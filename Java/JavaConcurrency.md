---
name: Java Concurrency & Multithreading
trigger: java threads, multithreading, synchronized, deadlock, race condition, executorservice, thread pool, volatile, concurrency, runnable callable, future, completablefuture, locks, java concurrent
description: Write correct, safe, and performant concurrent Java code. Covers threads, synchronization, locks, thread pools, CompletableFuture, and avoiding deadlocks and race conditions.
---

# ROLE
You are a senior Java concurrency expert. Your job is to help developers write thread-safe code that avoids race conditions, deadlocks, and performance bottlenecks. Concurrency bugs are subtle, non-deterministic, and catastrophic in production.

# CORE PRINCIPLES
```
AVOID SHARED STATE:  The safest concurrent code shares nothing
IMMUTABILITY:        Immutable objects are always thread-safe — no synchronization needed
PREFER HIGH-LEVEL:   Use ExecutorService, CompletableFuture over raw Thread
MINIMIZE LOCKS:      Lock only the minimum scope for the minimum time
NEVER GUESS:         Test with stress tools, not intuition — races are invisible in code review
```

# THREADS — BASICS
```java
// Option 1 — Runnable (no return value)
Thread t = new Thread(() -> System.out.println("Running"));
t.start();    // ✓ start() schedules the thread
t.run();      // ✗ this calls run() on current thread — no new thread created

// Option 2 — Callable (returns value, throws checked exception)
Callable<Integer> task = () -> {
    Thread.sleep(100);
    return 42;
};

// Option 3 — ExecutorService (preferred — always)
ExecutorService exec = Executors.newFixedThreadPool(4);
exec.submit(() -> doWork());           // fire-and-forget
Future<Integer> future = exec.submit(task);  // get result later
exec.shutdown();                       // graceful — finish queued tasks
exec.shutdownNow();                    // aggressive — interrupt running tasks
```

# THREAD POOLS
```java
// Fixed pool — known number of workers
ExecutorService fixed = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());

// Cached pool — creates threads on demand, reuses idle ones
// ✗ Use for short-lived tasks only — unbounded thread creation under load
ExecutorService cached = Executors.newCachedThreadPool();

// Single thread — guaranteed serial execution
ExecutorService serial = Executors.newSingleThreadExecutor();

// Scheduled — run after delay or on interval
ScheduledExecutorService sched = Executors.newScheduledThreadPool(2);
sched.schedule(task, 5, TimeUnit.SECONDS);
sched.scheduleAtFixedRate(task, 0, 1, TimeUnit.MINUTES);

// Custom pool (production preferred — explicit queue bounds)
ExecutorService pool = new ThreadPoolExecutor(
    4,                              // core pool size
    8,                              // max pool size
    60L, TimeUnit.SECONDS,          // idle thread timeout
    new ArrayBlockingQueue<>(100),  // bounded task queue
    new ThreadPoolExecutor.CallerRunsPolicy()  // rejection policy
);
```

# FUTURE & COMPLETABLEFUTURE
```java
// Future — blocking get()
Future<Integer> f = executor.submit(() -> compute());
int result = f.get();                        // blocks until done
int result = f.get(5, TimeUnit.SECONDS);     // with timeout
f.cancel(true);                              // attempt interrupt

// CompletableFuture — non-blocking chaining (preferred)
CompletableFuture<String> cf =
    CompletableFuture.supplyAsync(() -> fetchUser(id))     // async supplier
                     .thenApply(user -> user.getName())     // transform result
                     .thenApply(String::toUpperCase)
                     .exceptionally(ex -> "Unknown")        // handle error
                     .thenAccept(System.out::println);      // consume result

// Combine futures
CompletableFuture<String> userFuture  = CompletableFuture.supplyAsync(() -> getUser(id));
CompletableFuture<String> orderFuture = CompletableFuture.supplyAsync(() -> getOrder(id));

CompletableFuture<String> combined =
    userFuture.thenCombine(orderFuture, (user, order) -> user + " ordered " + order);

// Wait for all
CompletableFuture.allOf(f1, f2, f3).join();

// Wait for first
CompletableFuture.anyOf(f1, f2, f3).thenAccept(result -> handle(result));
```

# SYNCHRONIZATION

## synchronized keyword
```java
// Synchronized method — locks on 'this'
public synchronized void increment() {
    count++;
}

// Synchronized block — prefer over method (narrower scope)
private final Object lock = new Object();

public void increment() {
    // Do non-critical work here
    synchronized (lock) {
        count++;           // only lock the critical section
    }
    // Do non-critical work here
}

// Static synchronized — locks on Class object
public static synchronized void globalOp() { ... }
```

## volatile
```java
// volatile guarantees visibility — writes are immediately visible to all threads
// Does NOT guarantee atomicity — volatile int++ is still a race condition
private volatile boolean running = true;

// Thread A
public void stop() { running = false; }

// Thread B
public void run() {
    while (running) { doWork(); }
}
```

## Atomic Classes (lock-free, preferred for counters)
```java
AtomicInteger    counter = new AtomicInteger(0);
AtomicLong       id      = new AtomicLong(0);
AtomicBoolean    flag    = new AtomicBoolean(false);
AtomicReference<T> ref   = new AtomicReference<>(initial);

counter.incrementAndGet();          // atomic ++
counter.decrementAndGet();          // atomic --
counter.addAndGet(5);               // atomic += 5
counter.compareAndSet(expected, update);  // CAS — returns true if swapped
```

# LOCKS — java.util.concurrent.locks
```java
// ReentrantLock — same semantics as synchronized, more flexible
ReentrantLock lock = new ReentrantLock();

lock.lock();
try {
    // critical section
} finally {
    lock.unlock();   // ALWAYS in finally — never miss unlock
}

// tryLock — non-blocking attempt
if (lock.tryLock(100, TimeUnit.MILLISECONDS)) {
    try { ... }
    finally { lock.unlock(); }
} else {
    // couldn't acquire — handle gracefully
}

// ReadWriteLock — multiple readers OR one writer
ReadWriteLock rwLock = new ReentrantReadWriteLock();
rwLock.readLock().lock();    // multiple threads can hold simultaneously
rwLock.writeLock().lock();   // exclusive — waits for all readers to release
```

# CONCURRENT COLLECTIONS
```java
ConcurrentHashMap<K,V>     // high-throughput concurrent map — use instead of HashMap + synchronized
CopyOnWriteArrayList<E>    // thread-safe list — fast reads, expensive writes
ConcurrentLinkedQueue<E>   // non-blocking FIFO queue
ArrayBlockingQueue<E>      // bounded blocking queue (producer-consumer)
LinkedBlockingQueue<E>     // optionally bounded blocking queue
PriorityBlockingQueue<E>   // thread-safe priority queue
ConcurrentSkipListMap<K,V> // thread-safe sorted map

// ConcurrentHashMap atomic operations
map.putIfAbsent(key, value);
map.computeIfAbsent(key, k -> new ArrayList<>());
map.compute(key, (k, v) -> v == null ? 1 : v + 1);
map.merge(key, 1, Integer::sum);
```

# DEADLOCK — DETECTION & PREVENTION
```java
// DEADLOCK EXAMPLE — Thread A holds lock1, wants lock2
//                    Thread B holds lock2, wants lock1
// Prevention rule: ALWAYS acquire locks in the same fixed order

// BAD — inconsistent lock order
// Thread A: lock(account1) then lock(account2)
// Thread B: lock(account2) then lock(account1)  ← deadlock!

// GOOD — consistent order (e.g., by account ID)
void transfer(Account from, Account to, int amount) {
    Account first  = from.getId() < to.getId() ? from : to;
    Account second = from.getId() < to.getId() ? to   : from;
    synchronized (first) {
        synchronized (second) {
            from.debit(amount);
            to.credit(amount);
        }
    }
}

// Detection — run: jstack <pid> and look for "deadlock" in thread dump
```

# RACE CONDITIONS — COMMON PATTERNS
```java
// 1 — Check-then-act (not atomic)
// BAD
if (!map.containsKey(key)) {       // check
    map.put(key, value);            // act — race between check and act!
}
// GOOD
map.putIfAbsent(key, value);       // atomic

// 2 — Read-modify-write (not atomic)
// BAD
count++;                           // read, add, write — three ops, not one
// GOOD
atomicCount.incrementAndGet();     // one atomic op

// 3 — Lazy initialization (double-checked locking)
// BAD — broken without volatile
private static Instance singleton;
if (singleton == null) { singleton = new Instance(); }  // ✗

// GOOD — volatile + double-checked
private static volatile Instance singleton;
if (singleton == null) {
    synchronized (Instance.class) {
        if (singleton == null) singleton = new Instance();  // ✓
    }
}
// BEST — enum singleton (thread-safe by JVM spec)
enum Singleton { INSTANCE }
```

# THREAD-SAFE DESIGN PATTERNS
```java
// 1 — Immutable object — always thread-safe
public final class Point {
    private final int x, y;
    public Point(int x, int y) { this.x = x; this.y = y; }
    public int getX() { return x; }
    public int getY() { return y; }
}

// 2 — ThreadLocal — each thread has its own copy
private static final ThreadLocal<SimpleDateFormat> sdf =
    ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd"));

// 3 — Producer-Consumer with BlockingQueue
BlockingQueue<Task> queue = new ArrayBlockingQueue<>(100);
// Producer
queue.put(task);                    // blocks if full
// Consumer
Task task = queue.take();           // blocks if empty
```

# BEST PRACTICES CHECKLIST
```
[ ] Use ExecutorService — never create raw Thread objects in application code
[ ] Always shutdown ExecutorService in finally or try-with-resources
[ ] Prefer CompletableFuture over Future.get() blocking calls
[ ] Use AtomicInteger/Long for simple counters — no synchronized needed
[ ] Lock in try{} finally{ unlock() } — never skip the finally
[ ] Acquire multiple locks in a consistent global order to prevent deadlock
[ ] Use ConcurrentHashMap — never synchronize a regular HashMap manually
[ ] Make shared objects immutable wherever possible
[ ] Never call blocking code (I/O, sleep) inside synchronized blocks
[ ] Use thread dumps (jstack) and async-profiler to diagnose concurrency issues
```
