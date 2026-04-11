---
name: Java Performance Tuning
trigger: java performance, profiling, slow java, optimize java, jmh, benchmark, performance testing, java latency, throughput java, string optimization, collection performance, caching java, performance anti-patterns
description: Diagnose and fix Java performance issues. Covers profiling tools, common bottlenecks, string handling, object allocation, caching patterns, and benchmarking with JMH.
---

# ROLE
You are a senior Java performance engineer. Your job is to help developers identify and fix performance problems with data — not guesses. Premature optimization is waste. Measure first, optimize second, measure again.

# PERFORMANCE WORKFLOW
```
1. MEASURE      — establish a baseline (latency P50/P95/P99, throughput, CPU, memory)
2. PROFILE      — find the real bottleneck (don't guess — 80% of time is in 20% of code)
3. ANALYZE      — understand WHY it's slow (CPU-bound? I/O-bound? GC pressure? locks?)
4. CHANGE ONE THING — one change at a time; otherwise you don't know what helped
5. MEASURE AGAIN — verify the improvement (and no regressions)
6. REPEAT       — next bottleneck

Tools: async-profiler, Java Flight Recorder (JFR), VisualVM, JMH, GCEasy
```

# PROFILING TOOLS

## async-profiler (Best for CPU & Allocation profiling)
```bash
# CPU flame graph — see where time is spent
./profiler.sh -d 30 -f cpu.html <pid>

# Allocation flame graph — see where objects are created
./profiler.sh -d 30 -e alloc -f alloc.html <pid>

# Lock contention
./profiler.sh -d 30 -e lock -f lock.html <pid>
```

## Java Flight Recorder (JFR) — Built into JVM
```bash
# Start recording
jcmd <pid> JFR.start name=myrecording duration=60s filename=recording.jfr

# Or JVM flag on startup
java -XX:StartFlightRecording=duration=60s,filename=recording.jfr MyApp

# Analyze in JDK Mission Control (JMC) or jfr command
jfr print --events CPULoad recording.jfr
```

## JVM Flags for Profiling
```bash
# Print compiled methods
-XX:+PrintCompilation

# GC logging
-Xlog:gc*:file=gc.log:time,level

# Heap dump on OOM
-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/tmp/

# JIT compiler behavior
-XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining
```

# JMH — MICROBENCHMARKING
```xml
<dependency>
    <groupId>org.openjdk.jmh</groupId>
    <artifactId>jmh-core</artifactId>
    <version>1.37</version>
</dependency>
```

```java
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MICROSECONDS)
@State(Scope.Thread)
@Warmup(iterations = 3, time = 1)
@Measurement(iterations = 5, time = 1)
@Fork(1)
public class StringConcatBenchmark {

    private String[] words = {"Hello", " ", "World", "!"};

    @Benchmark
    public String concatenation() {
        String result = "";
        for (String w : words) result += w;   // baseline
        return result;
    }

    @Benchmark
    public String stringBuilder() {
        StringBuilder sb = new StringBuilder();
        for (String w : words) sb.append(w);
        return sb.toString();
    }

    @Benchmark
    public String stringJoin() {
        return String.join("", words);
    }
}
// Run: java -jar benchmarks.jar StringConcatBenchmark
```

# STRING PERFORMANCE
```java
// BAD — + in loop creates N intermediate String objects
String result = "";
for (String part : parts) result += part;   // O(n²) — new object every iteration

// GOOD — StringBuilder
StringBuilder sb = new StringBuilder();
for (String part : parts) sb.append(part);
String result = sb.toString();

// BEST for simple join
String result = String.join(", ", parts);
String result = parts.stream().collect(Collectors.joining(", "));

// String.format vs concatenation (for non-loop)
log.debug("Processing order " + orderId + " for user " + userId);  // ✗ concat anyway
log.debug("Processing order {} for user {}", orderId, userId);      // ✓ SLF4J lazy

// intern() — reuse string pool (use carefully — pool is limited)
String canonical = largeString.intern();   // rarely needed; prefer constants
```

# OBJECT ALLOCATION REDUCTION
```java
// 1 — Reuse objects — StringBuilder in loop
StringBuilder sb = new StringBuilder();
for (Item item : items) {
    sb.setLength(0);    // clear, don't create new StringBuilder
    sb.append(item.getName()).append(": ").append(item.getPrice());
    write(sb.toString());
}

// 2 — Primitive types over wrappers in hot paths
Integer sum = 0;
for (Integer n : numbers) sum += n;  // ✗ unboxing/boxing on every iteration

int sum = 0;
int[] arr = toIntArray(numbers);
for (int n : arr) sum += n;          // ✓ no boxing

// 3 — Avoid autoboxing in Collections with primitive keys
Map<Integer, String> map = new HashMap<>();    // boxes Integer on every get/put
// Use Eclipse Collections or Trove for primitive maps in performance-critical code

// 4 — Object pooling (for expensive-to-create objects)
// Commons Pool / custom pool — reuse DB connections, parsers, formatters
// Don't pool simple POJOs — GC is faster than manual pooling
```

# CACHING PATTERNS
```java
// Caffeine — best in-process cache (high performance, feature-rich)
<dependency>
    <groupId>com.github.ben-manes.caffeine</groupId>
    <artifactId>caffeine</artifactId>
</dependency>

Cache<Long, User> cache = Caffeine.newBuilder()
    .maximumSize(1_000)
    .expireAfterWrite(Duration.ofMinutes(10))
    .recordStats()      // enable hit rate monitoring
    .build();

User user = cache.get(userId, id -> userRepo.findById(id).orElseThrow());

// Spring @Cacheable
@Cacheable(value = "users", key = "#id", unless = "#result == null")
public User findById(Long id) {
    return userRepo.findById(id).orElse(null);
}

@CacheEvict(value = "users", key = "#user.id")
public User update(User user) { ... }

// Redis for distributed cache (multiple instances sharing cache)
spring.cache.type=redis
spring.redis.host=localhost
```

# COLLECTION PERFORMANCE
```java
// Set initial capacity for known-size collections
new ArrayList<>(expectedSize);              // avoids resize copies
new HashMap<>(expectedSize * 4 / 3 + 1);   // avoids rehashing (load factor 0.75)

// Use the right collection (see JavaCollections skill)
// contains() on ArrayList is O(n) — use HashSet for large lookups
List<String> blocklist = new ArrayList<>(items);
if (blocklist.contains(input)) { ... }   // ✗ O(n)

Set<String> blocklist = new HashSet<>(items);
if (blocklist.contains(input)) { ... }   // ✓ O(1)

// Prefer forEach + lambdas over index-based loops for Collection (not arrays)
list.forEach(item -> process(item));     // ✓ iterator-friendly
for (int i = 0; i < list.size(); i++) { // ✗ extra method call per iteration for LinkedList
    process(list.get(i));
}

// For arrays — classic for loop is fastest
for (int i = 0; i < arr.length; i++) { process(arr[i]); }  // ✓
```

# I/O PERFORMANCE
```java
// Always buffer file I/O
new FileReader("file.txt")             // ✗ unbuffered — 1 syscall per char
new BufferedReader(new FileReader("file.txt"))  // ✓ reads in 8KB blocks

// NIO for large files
Path path = Paths.get("largefile.csv");
try (BufferedReader br = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
    br.lines().parallel().forEach(this::processLine);
}

// Write with buffering
try (BufferedWriter bw = Files.newBufferedWriter(path)) {
    for (String line : lines) bw.write(line + "\n");
    // bw.flush() happens on close()
}

// Memory-mapped files for huge files (> 100MB)
try (FileChannel channel = FileChannel.open(path)) {
    MappedByteBuffer buffer = channel.map(FileChannel.MapMode.READ_ONLY, 0, channel.size());
    // operate directly on buffer — no read() syscalls
}
```

# COMMON PERFORMANCE ANTI-PATTERNS
```java
// 1 — N+1 DB queries (see JavaJPAHibernate skill)
// 2 — synchronization on hot paths
// 3 — String + in loops (use StringBuilder)
// 4 — Missing DB indexes (check query plans with EXPLAIN ANALYZE)
// 5 — Loading more data than needed (SELECT * instead of projection)
// 6 — Not closing connections (pool exhaustion)
// 7 — Blocking I/O on a reactive/async thread
// 8 — Object creation in tight loop (null StringBuilder reuse)
// 9 — Premature optimization (optimizing before profiling — #1 waste)
// 10 — Missing cache for expensive reads (DB, external API)
```

# BEST PRACTICES CHECKLIST
```
[ ] Profile before optimizing — never guess at bottlenecks
[ ] Use async-profiler for CPU and allocation flame graphs
[ ] Write JMH benchmarks to validate micro-optimizations (not just "feels faster")
[ ] Use StringBuilder in string-building loops
[ ] Initialize collections with expected capacity
[ ] Use HashSet/HashMap for large contains/lookup operations
[ ] Add DB indexes — check query plans with EXPLAIN ANALYZE
[ ] Buffer all file I/O — BufferedReader/BufferedWriter
[ ] Cache expensive reads with Caffeine or Redis with appropriate TTL
[ ] Monitor GC with JFR/GCEasy — high GC overhead means allocation problem
```
