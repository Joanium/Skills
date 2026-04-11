---
name: Java Memory Management & GC
trigger: java memory, garbage collection, heap, stack, gc tuning, memory leak, jvm memory, young generation, old generation, gc logs, metaspace, g1gc, outofmemoryerror, java profiling, jvm tuning
description: Understand and control Java memory management. Covers JVM memory regions, garbage collectors, tuning flags, diagnosing memory leaks, and avoiding common OOM causes.
---

# ROLE
You are a senior Java performance engineer. Your job is to help developers understand how the JVM manages memory, diagnose leaks, choose the right GC, and tune JVM flags for production workloads.

# JVM MEMORY REGIONS
```
┌────────────────────────────────────────────────────────────┐
│  HEAP (GC-managed, -Xms / -Xmx)                           │
│  ┌──────────────────────────┬───────────────────────────┐  │
│  │  Young Generation        │  Old (Tenured) Generation │  │
│  │  ┌──────┬──────┬──────┐  │                           │  │
│  │  │ Eden │ S0   │ S1   │  │  Long-lived objects       │  │
│  │  └──────┴──────┴──────┘  │  promoted from Young      │  │
│  └──────────────────────────┴───────────────────────────┘  │
├────────────────────────────────────────────────────────────┤
│  METASPACE (non-heap, class metadata, -XX:MaxMetaspaceSize)│
├────────────────────────────────────────────────────────────┤
│  STACK (per thread, -Xss)                                  │
│  Local variables, method frames, primitives, references    │
├────────────────────────────────────────────────────────────┤
│  CODE CACHE (JIT-compiled methods)                         │
└────────────────────────────────────────────────────────────┘
```

# OBJECT LIFECYCLE
```
1. Object allocated in EDEN (Young Gen)
2. Minor GC — objects surviving go to Survivor space (S0 or S1)
3. Objects surviving N minor GCs (age threshold) → promoted to Old Gen
4. Major/Full GC — Old Gen is collected (slower, stop-the-world)

Key insight: Most objects die young (weak generational hypothesis)
→ Minor GC is fast because Young Gen is small and most objects are dead
→ Keep objects short-lived to avoid Old Gen pressure
```

# GARBAGE COLLECTORS — CHOOSE THE RIGHT ONE
```
Serial GC       → single-thread, small heaps, not for production servers
                  -XX:+UseSerialGC

Parallel GC     → multi-thread throughput GC, batch/offline workloads (Java 8 default)
                  -XX:+UseParallelGC

G1GC (Garbage-First) → low-pause, large heaps, server default (Java 9+)
                  -XX:+UseG1GC
                  Good for heaps 6GB–32GB, latency-sensitive apps

ZGC             → sub-millisecond pauses, heaps up to 16TB (Java 15+ production)
                  -XX:+UseZGC
                  Best for: very latency-sensitive apps (trading, APIs)

Shenandoah GC   → concurrent, low-pause (OpenJDK)
                  -XX:+UseShenandoahGC

RULE:
  Batch jobs / throughput → Parallel GC
  Web services (latency)  → G1GC (good default) or ZGC (ultra-low latency)
  Old Java 8 app          → ParallelGC is default, consider G1GC
```

# ESSENTIAL JVM FLAGS
```bash
# Heap size — always set both equal in production (avoids resize GC)
-Xms2g -Xmx2g       # 2GB heap, min = max

# Young generation size (G1GC manages it automatically)
-Xmn512m             # 512MB young gen (for Parallel GC)

# GC selection
-XX:+UseG1GC
-XX:+UseZGC

# GC logging (Java 11+)
-Xlog:gc*:file=gc.log:time,uptime,level,tags:filecount=5,filesize=20m

# Heap dump on OOM — essential for production diagnosis
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/var/log/myapp/heapdump.hprof

# Print GC cause
-XX:+PrintGCDetails -XX:+PrintGCDateStamps

# Metaspace
-XX:MaxMetaspaceSize=256m   # cap it — prevents classloader leaks from consuming all memory

# G1GC specific
-XX:MaxGCPauseMillis=200    # target pause time (G1GC tries to meet this)
-XX:G1HeapRegionSize=16m    # region size (auto-selected; override for very large heaps)
```

# MEMORY LEAKS — COMMON CAUSES
```java
// 1 — Static collections accumulating data forever
public class Cache {
    private static final Map<String, Object> cache = new HashMap<>();

    public void put(String key, Object value) {
        cache.put(key, value);   // ✗ never evicts — grows unbounded
    }
}
// FIX: use LRU cache, Caffeine, or Guava Cache with eviction

// 2 — Listeners never removed
button.addActionListener(heavyListener);
// ✗ button holds reference to listener → listener can't be GC'd
// FIX: button.removeActionListener(heavyListener) when done

// 3 — Non-static inner class holding outer class reference
public class Outer {
    class Inner { }   // Inner holds implicit reference to Outer — ✗
    static class StaticInner { }  // ✓ no implicit reference
}

// 4 — ThreadLocal not cleaned up
private static final ThreadLocal<Connection> conn = new ThreadLocal<>();
conn.set(connection);
// ✗ In thread pools, thread is reused — value persists between requests
// FIX: always call conn.remove() in finally block

// 5 — Unclosed resources
BufferedReader r = new BufferedReader(new FileReader("file.txt"));
// ✗ if exception thrown before close() — resource leaks
// FIX: use try-with-resources

// 6 — Interning too many strings
String s = input.intern();  // ✗ interns go to string pool in Metaspace — can fill it up
```

# DIAGNOSING MEMORY ISSUES

## Commands
```bash
# Heap usage summary
jstat -gcutil <pid> 1000    # print GC stats every 1 second

# Heap dump (for analysis in VisualVM or Eclipse MAT)
jmap -dump:format=b,file=heap.hprof <pid>

# Thread dump (for deadlock / thread count analysis)
jstack <pid>

# JVM flags in use
jcmd <pid> VM.flags

# Heap info
jcmd <pid> GC.heap_info
```

## Heap Dump Analysis (Eclipse MAT / VisualVM)
```
1. Open heap.hprof in Eclipse MAT
2. Run "Leak Suspects Report" — identifies likely leak root causes
3. Check "Dominator Tree" — shows objects retaining most memory
4. Look for: static Maps/Lists growing unbounded, ClassLoader leaks, ThreadLocal values
```

# OUTOFMEMORYERROR TYPES
```
java.lang.OutOfMemoryError: Java heap space
  → Heap is full. Cause: leak, too small heap, or too many live objects
  → Fix: increase -Xmx, find and fix leak, or reduce object retention

java.lang.OutOfMemoryError: GC overhead limit exceeded
  → GC is spending >98% time collecting but freeing <2% heap
  → Fix: increase -Xmx or find leak causing Old Gen to fill

java.lang.OutOfMemoryError: Metaspace
  → Too many classes loaded (classloader leak, hot deploy loops)
  → Fix: add -XX:MaxMetaspaceSize, find classloader leak

java.lang.OutOfMemoryError: unable to create native thread
  → Too many threads (thread leak, unbounded thread pool)
  → Fix: limit thread pool sizes, find thread leak with jstack

java.lang.StackOverflowError
  → Infinite or too-deep recursion
  → Fix: add base case, increase -Xss, or convert to iterative
```

# GC TUNING WORKFLOW
```
1. Establish baseline — measure GC frequency, pause duration, throughput
   Tool: GC logs, GCViewer, GCEasy.io

2. Check allocation rate
   Tool: async-profiler, Java Flight Recorder (JFR)
   High young gen allocation → short-lived objects → optimize hot code paths

3. Check promotion rate
   Objects being promoted too fast → tune -Xmn (young gen size)
   or MaxTenuringThreshold

4. Check Old Gen growth
   Steadily growing Old Gen → memory leak
   Tool: heap dump analysis in Eclipse MAT

5. Tune GC target
   -XX:MaxGCPauseMillis=100  (G1GC)
   Watch: if too aggressive, throughput drops
```

# WEAK / SOFT / PHANTOM REFERENCES
```java
// SoftReference — GC'd when memory is low (good for caches)
SoftReference<Image> softRef = new SoftReference<>(loadImage());
Image img = softRef.get();   // null if GC'd

// WeakReference — GC'd at next GC cycle (good for canonical maps)
WeakReference<Widget> weakRef = new WeakReference<>(widget);
Widget w = weakRef.get();    // null if GC'd

// WeakHashMap — entries removed when key is GC'd
WeakHashMap<Key, Value> map = new WeakHashMap<>();
// Useful for caches where you don't want to prevent key GC

// PhantomReference — post-mortem cleanup notification
ReferenceQueue<Object> queue = new ReferenceQueue<>();
PhantomReference<Object> phantom = new PhantomReference<>(obj, queue);
// Used for resource cleanup, replacing finalize()
```

# BEST PRACTICES CHECKLIST
```
[ ] Set -Xms = -Xmx in production — avoids heap resize pauses
[ ] Always set -XX:+HeapDumpOnOutOfMemoryError — you need the dump to diagnose
[ ] Use G1GC for server apps on Java 11+ (it's the default — explicitly set for clarity)
[ ] Cap Metaspace with -XX:MaxMetaspaceSize to prevent classloader leaks consuming all memory
[ ] Enable GC logging — parse with GCEasy.io or GCViewer
[ ] Always call ThreadLocal.remove() in finally blocks when using thread pools
[ ] Use try-with-resources — no resource leaks
[ ] Profile allocation rate with async-profiler before tuning GC flags
[ ] Monitor Old Gen growth — steady growth = leak; use Eclipse MAT on heap dump
[ ] Never rely on finalize() for resource cleanup — use AutoCloseable + try-with-resources
```
