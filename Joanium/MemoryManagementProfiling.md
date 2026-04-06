---
name: Memory Management & Profiling
trigger: memory leak, memory usage, heap, profiling memory, out of memory, high memory, memory grows, node memory, python memory, garbage collection, heap snapshot, memory profile, ram usage, gc pressure, oom, process memory
description: Diagnose and fix memory leaks, reduce memory usage, and profile memory allocation in Node.js and Python applications. Use when a process memory grows without bound, OOM errors appear, or you need to reduce the memory footprint of a service.
---

Memory leaks don't announce themselves. They show up as a process that needs a restart every few days, a p99 latency spike that correlates with memory pressure, or an OOM kill from Kubernetes. Learn to find the leak before it finds you in production.

## Recognizing a Memory Leak vs. Expected Growth

Not all memory growth is a leak. Distinguish:

```
Expected growth → Stabilizes after warmup:
  - JIT compilation caches
  - Module/require caches at startup
  - Connection pool allocation
  - LRU caches that fill to their limit

Memory leak → Grows without bound:
  - Unbounded caches (key-value stores you never evict from)
  - Event listeners added but never removed
  - Closures holding references longer than needed
  - Circular references in manual memory management (C/C++)
  - Streams/buffers not consumed or destroyed
  - Global arrays/maps that grow with every request

Test: Restart the process. Memory should return to baseline.
Then drive traffic. Watch the memory over time.
If it grows continuously with no plateau → leak.
```

## Node.js Memory Profiling

### Step 1: Measure current usage
```javascript
// Log memory usage periodically
setInterval(() => {
  const mem = process.memoryUsage();
  console.log({
    rss: `${Math.round(mem.rss / 1024 / 1024)}MB`,        // Total process memory
    heapUsed: `${Math.round(mem.heapUsed / 1024 / 1024)}MB`, // JS heap in use
    heapTotal: `${Math.round(mem.heapTotal / 1024 / 1024)}MB`, // JS heap allocated
    external: `${Math.round(mem.external / 1024 / 1024)}MB`,   // C++ objects (Buffers)
  });
}, 10_000);

// For metrics/Datadog:
gauge('process.memory.rss', process.memoryUsage().rss);
gauge('process.memory.heap_used', process.memoryUsage().heapUsed);
```

```
Key metric to watch: heapUsed
- heapUsed growing → JS objects accumulating
- external growing → Buffer/C++ object leak (streams, native addons)
- rss growing, heap stable → OS memory fragmentation or native code
```

### Step 2: Take heap snapshots (Chrome DevTools)
```javascript
// Expose heap snapshot endpoint (only in dev/staging!)
const v8 = require('v8');
const fs = require('fs');

app.get('/__internal/heap-snapshot', (req, res) => {
  const filename = `heap-${Date.now()}.heapsnapshot`;
  const stream = v8.writeHeapSnapshot(filename);
  res.json({ file: stream });
});
```

```bash
# Or trigger via signal
kill -USR2 <pid>  # With --expose-gc and heapdump package

# Or use clinic.js (recommended)
npm install -g clinic
clinic heapprofiler -- node server.js
```

Open `.heapsnapshot` in Chrome DevTools → Memory tab → Load snapshot.

**The workflow:**
1. Snapshot at baseline (after warmup)
2. Drive traffic for 10 minutes
3. Force GC (`global.gc()` with `--expose-gc` flag)
4. Snapshot again
5. Compare: "Objects allocated between snapshots" — look for unexpected growth

### Step 3: Identify the leak with `--inspect`
```bash
# Start with inspector
node --inspect server.js

# Navigate to: chrome://inspect
# Open DevTools → Memory tab
# Take heap snapshot, drive traffic, take another
# Filter: "Objects allocated between snapshots"
```

### Common Node.js Leak Patterns

#### Leak 1: Event listeners not removed
```javascript
// BAD: Every call to setupConnection adds a listener — never removed
function setupConnection(socket) {
  eventEmitter.on('data', (data) => {
    socket.write(data); // Closure holds reference to `socket`
  });
}
// After 1000 connections: 1000 listeners accumulate

// GOOD: Remove listener when socket closes
function setupConnection(socket) {
  const handler = (data) => socket.write(data);
  eventEmitter.on('data', handler);
  
  socket.on('close', () => {
    eventEmitter.off('data', handler); // Clean up!
  });
}

// React equivalent
useEffect(() => {
  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize); // cleanup
}, []);
```

#### Leak 2: Unbounded caches
```javascript
// BAD: Cache grows forever
const cache = new Map();

function getUser(id) {
  if (cache.has(id)) return cache.get(id);
  const user = db.findUser(id);
  cache.set(id, user); // Never evicted
  return user;
}

// GOOD: Bounded cache with LRU eviction
import LRU from 'lru-cache';

const cache = new LRU({
  max: 1000,       // Maximum 1000 entries
  ttl: 1000 * 60 * 5, // 5 minute TTL
});

// Or use a simple bounded map:
class BoundedMap<K, V> extends Map<K, V> {
  constructor(private maxSize: number) { super(); }
  set(key: K, value: V) {
    if (this.size >= this.maxSize) {
      this.delete(this.keys().next().value); // Evict oldest
    }
    return super.set(key, value);
  }
}
```

#### Leak 3: Closures holding large objects
```javascript
// BAD: The closure captures the entire largeArray
function processLargeData(largeArray) {
  const summary = computeSummary(largeArray); // 100KB object
  
  // This closure holds a reference to largeArray (10MB!) 
  // even though it only needs `summary`
  setTimeout(() => {
    console.log(summary.total); // Uses summary, but largeArray stays in memory
  }, 5000);
}

// GOOD: Don't capture what you don't need
function processLargeData(largeArray) {
  const summary = computeSummary(largeArray);
  largeArray = null; // Release reference before the async operation
  
  setTimeout(() => {
    console.log(summary.total);
  }, 5000);
}
```

#### Leak 4: Streams not consumed or destroyed
```javascript
// BAD: Response stream not consumed → memory held open
const response = await fetch(url);
// Never reading response.body → underlying resources held

// BAD: Stream with error that's never cleaned up
const readable = fs.createReadStream(file);
readable.on('data', process);
// No 'error' handler → unhandled rejection can leave stream open

// GOOD: Always consume and handle errors
const response = await fetch(url);
const data = await response.json(); // Consume

// GOOD: Use pipeline for automatic cleanup
const { pipeline } = require('stream/promises');
await pipeline(
  fs.createReadStream(input),
  transform,
  fs.createWriteStream(output)
); // Destroys all streams on completion or error
```

## Python Memory Profiling

### Step 1: Measure usage
```python
import tracemalloc
import linecache

# Start tracing
tracemalloc.start()

# ... run your code ...

# Take snapshot
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("Top 10 memory consumers:")
for stat in top_stats[:10]:
    print(stat)
```

### Step 2: memory_profiler (line-by-line)
```bash
pip install memory-profiler
```

```python
from memory_profiler import profile

@profile  # Decorator for line-by-line analysis
def process_data(data):
    result = []
    for item in data:           # Line 5
        result.append(item * 2) # Line 6 — see memory per line
    return result               # Line 7
```

```bash
python -m memory_profiler my_script.py
# Output shows MB usage at each decorated line
```

### Step 3: objgraph (find leaks)
```python
import objgraph

# Before:
objgraph.show_growth()  # No output (baseline)

# ... drive traffic / run operations ...

# After:
objgraph.show_growth()  # Shows what grew
# MyClass        500   +500  ← 500 new instances not GC'd

# Find what's holding a reference
objgraph.show_backrefs(
  objgraph.by_type('MyClass')[0],  # An instance of the leaking class
  max_depth=3
)
```

### Common Python Leak Patterns

```python
# LEAK: Class-level mutable default (shared across all instances)
class RequestHandler:
    cache = {}  # Shared! Grows across all requests

# FIX: Instance-level
class RequestHandler:
    def __init__(self):
        self.cache = {}

# LEAK: Circular references (prevented by GC usually, but can delay collection)
class Node:
    def __init__(self):
        self.parent = None
        self.children = []

# LEAK: Generator not fully consumed (holds frame)
def read_large_file(path):
    with open(path) as f:
        for line in f:
            yield process(line)

gen = read_large_file('big.txt')
first = next(gen)  # File stays open! Generator frame not released.
# FIX: Always exhaust generators or use gen.close()

# LEAK: __del__ methods can prevent garbage collection
# Avoid __del__ — use context managers instead
class Resource:
    def __enter__(self): return self
    def __exit__(self, *args): self.cleanup()
```

## Kubernetes OOM Debugging

```bash
# Find OOMKilled pods
kubectl get pods -A | grep OOMKilled

# See memory limit that was hit
kubectl describe pod <pod-name> -n <namespace>
# Look for: Last State: Terminated, Reason: OOMKilled

# Current memory usage
kubectl top pods -n production --sort-by=memory

# Resource limits in the deployment
kubectl get deployment <name> -n production -o yaml | grep -A5 resources:
```

```yaml
# Right-size your limits (don't guess — measure first)
resources:
  requests:
    memory: "256Mi"   # Scheduler uses this for placement
  limits:
    memory: "512Mi"   # OOM kill threshold
    
# Set limit to ~2x your p99 observed usage
# If the process legitimately needs more, increase the limit
# If memory grows without bound → it's a leak
```

## Memory Debugging Checklist

```
Initial diagnosis:
☐ Is heapUsed growing continuously or stabilizing?
☐ Does memory return to baseline after restart?
☐ Does memory correlate with traffic (request-scoped leak) or time (global leak)?

Node.js leaks — check in order:
☐ EventEmitter listeners not cleaned up?
☐ Unbounded Map/Set/Array that accumulates entries?
☐ Closures capturing large objects unnecessarily?
☐ Streams not consumed/destroyed/error-handled?
☐ Timers (setInterval) not cleared on shutdown?
☐ Third-party library with known memory leak? (check their issues)

Python leaks:
☐ Class-level mutable attributes shared across instances?
☐ Circular references preventing GC?
☐ Large DataFrames not explicitly deleted?
☐ Generators not exhausted or closed?

Production:
☐ Memory limit set to ~2x p99 observed usage?
☐ Memory alert configured at 80% of limit?
☐ Graceful restart if memory exceeds threshold (PM2 max_memory_restart)?
☐ Heap snapshot mechanism available in staging?
```
