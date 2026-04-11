---
name: Java Streams & Lambdas
trigger: java streams, stream api, lambda, functional interface, map filter reduce, collectors, flatmap, optional, method reference, java functional programming, stream pipeline, groupingby
description: Write expressive, efficient Java code using the Stream API and lambdas. Covers pipeline construction, terminal operations, collectors, flatMap, Optional, and common performance traps.
---

# ROLE
You are a senior Java engineer. Your job is to help developers write readable, correct, and performant code using Java's functional features — Streams, Lambdas, and Optional. Misused streams cause silent bugs and poor performance.

# CORE PRINCIPLES
```
PIPELINES:     Streams are lazy — nothing runs until a terminal operation is called
IMMUTABLE:     Streams don't modify the source — they produce new values
SINGLE-USE:    A Stream can only be consumed once — reuse the source, not the stream
AVOID SIDE EFFECTS: Don't mutate external state inside stream operations
READABILITY:   Streams should make code shorter AND clearer — if they don't, use a loop
```

# LAMBDA SYNTAX
```java
// No params
Runnable r = () -> System.out.println("hello");

// One param (parentheses optional)
Consumer<String> print = s -> System.out.println(s);

// Multiple params
BiFunction<Integer, Integer, Integer> add = (a, b) -> a + b;

// Block body (use when logic > 1 expression)
Function<String, Integer> parse = s -> {
    if (s == null) return 0;
    return Integer.parseInt(s.trim());
};

// Method references (cleaner than equivalent lambda)
list.forEach(System.out::println);          // instance method of arg
list.stream().map(String::toUpperCase);     // instance method
list.stream().map(Integer::parseInt);       // static method
list.stream().map(Person::new);             // constructor ref
```

# FUNCTIONAL INTERFACES
```java
Supplier<T>          ()  → T            get()       produce a value
Consumer<T>          T   → void         accept()    consume a value
BiConsumer<T,U>      T,U → void         accept()
Function<T,R>        T   → R            apply()     transform a value
BiFunction<T,U,R>    T,U → R            apply()
UnaryOperator<T>     T   → T            apply()     transform same type
BinaryOperator<T>    T,T → T            apply()
Predicate<T>         T   → boolean      test()      filter condition
BiPredicate<T,U>     T,U → boolean      test()

// Composition
Predicate<String> notEmpty = s -> !s.isEmpty();
Predicate<String> notNull  = Objects::nonNull;
Predicate<String> valid    = notNull.and(notEmpty);

Function<String, String> trim  = String::trim;
Function<String, String> upper = String::toUpperCase;
Function<String, String> clean = trim.andThen(upper);
```

# STREAM PIPELINE ANATOMY
```java
source                          // Collection, array, Stream.of(), Stream.generate()
  .intermediateOp()             // lazy — builds pipeline only
  .intermediateOp()
  .terminalOp();                // triggers execution, produces result

// Example
List<String> result = employees.stream()          // source
    .filter(e -> e.getSalary() > 50_000)          // intermediate — lazy
    .map(Employee::getName)                        // intermediate — lazy
    .sorted()                                      // intermediate — lazy
    .collect(Collectors.toList());                 // terminal — runs pipeline
```

# INTERMEDIATE OPERATIONS
```java
// filter — keep elements matching predicate
stream.filter(s -> s.length() > 3)

// map — transform each element
stream.map(String::toUpperCase)
stream.mapToInt(String::length)     // → IntStream (avoids boxing)

// flatMap — flatten nested collections
List<List<Integer>> nested = List.of(List.of(1,2), List.of(3,4));
nested.stream()
      .flatMap(Collection::stream)   // → Stream<Integer>: 1,2,3,4

// distinct, sorted, limit, skip
stream.distinct()
stream.sorted(Comparator.comparing(Person::getAge))
stream.limit(10)
stream.skip(5)

// peek — debug only, don't use for side effects
stream.peek(e -> System.out.println("Processing: " + e))
```

# TERMINAL OPERATIONS
```java
// collect
List<String>       list  = stream.collect(Collectors.toList());
Set<String>        set   = stream.collect(Collectors.toSet());
String             joined = stream.collect(Collectors.joining(", ", "[", "]"));
Map<Boolean, List<Person>> split = stream.collect(Collectors.partitioningBy(p -> p.getAge() >= 18));
Map<String, List<Person>>  groups = stream.collect(Collectors.groupingBy(Person::getDepartment));
Map<String, Long>  counts = stream.collect(Collectors.groupingBy(Person::getDept, Collectors.counting()));

// reduce
int sum = IntStream.rangeClosed(1, 10).reduce(0, Integer::sum);
Optional<String> longest = stream.reduce((a, b) -> a.length() >= b.length() ? a : b);

// forEach / forEachOrdered
stream.forEach(System.out::println);
parallelStream.forEachOrdered(System.out::println);  // preserves order in parallel

// find / match
Optional<String> first  = stream.filter(s -> s.startsWith("A")).findFirst();
boolean anyMatch        = stream.anyMatch(s -> s.isEmpty());
boolean allMatch        = stream.allMatch(s -> s.length() > 0);
boolean noneMatch       = stream.noneMatch(Objects::isNull);

// count / min / max
long count       = stream.count();
Optional<T> min  = stream.min(Comparator.naturalOrder());
Optional<T> max  = stream.max(Comparator.comparingInt(String::length));

// toArray
Object[]   arr  = stream.toArray();
String[]   sarr = stream.toArray(String[]::new);
```

# COLLECTORS — ADVANCED
```java
// groupingBy with downstream collector
Map<String, Double> avgSalaryByDept =
    employees.stream()
             .collect(Collectors.groupingBy(
                 Employee::getDepartment,
                 Collectors.averagingDouble(Employee::getSalary)));

// toMap — beware duplicate key exception
Map<Integer, String> idToName =
    employees.stream()
             .collect(Collectors.toMap(
                 Employee::getId,
                 Employee::getName,
                 (existing, replacement) -> existing));  // merge fn for duplicates

// counting, summarizing
Map<String, Long> countByDept =
    employees.stream()
             .collect(Collectors.groupingBy(Employee::getDept, Collectors.counting()));

IntSummaryStatistics stats =
    employees.stream()
             .collect(Collectors.summarizingInt(Employee::getAge));
// stats.getAverage(), getMin(), getMax(), getSum(), getCount()

// Collectors.toUnmodifiableList() (Java 10+)
List<String> safe = stream.collect(Collectors.toUnmodifiableList());
```

# OPTIONAL — USE CORRECTLY
```java
// Create
Optional<String> opt  = Optional.of("value");       // NPE if value is null
Optional<String> safe = Optional.ofNullable(value); // OK for null
Optional<String> empty = Optional.empty();

// Consume
opt.isPresent()                           // check presence
opt.ifPresent(System.out::println)        // action if present
opt.get()                                 // ✗ throws if empty — never call without isPresent check
opt.orElse("default")                     // value or default (default always evaluated)
opt.orElseGet(() -> computeDefault())     // value or lazy default (preferred)
opt.orElseThrow(() -> new RuntimeException("missing"))

// Transform
opt.map(String::toUpperCase)              // Optional<String>
opt.flatMap(s -> Optional.ofNullable(s.getUser())) // avoid Optional<Optional<T>>
opt.filter(s -> s.length() > 3)

// BAD PATTERNS
if (opt.isPresent()) { return opt.get(); }   // ✗ — verbose, use orElse/map
Optional<String> field;                       // ✗ don't use as field type
void method(Optional<String> param)          // ✗ don't use as method param

// GOOD PATTERN — chain it
String name = findUser(id)
    .map(User::getName)
    .map(String::trim)
    .orElse("Unknown");
```

# PRIMITIVE STREAMS — AVOID BOXING
```java
// Use IntStream, LongStream, DoubleStream for primitives
IntStream.range(0, 10)              // 0..9
IntStream.rangeClosed(1, 10)        // 1..10
IntStream.of(1, 2, 3)

// mapToInt avoids Integer boxing overhead
int total = employees.stream()
                     .mapToInt(Employee::getSalary)
                     .sum();

// sum, average, min, max, count available directly
OptionalDouble avg = IntStream.of(1,2,3).average();
```

# PARALLEL STREAMS — HANDLE WITH CARE
```java
list.parallelStream()
    .filter(...)
    .map(...)
    .collect(Collectors.toList());  // safe — Collectors are thread-safe

// GOOD candidates for parallel:
// - Large collections (>10k elements)
// - CPU-bound, stateless operations
// - Operations with no shared mutable state

// BAD candidates:
// - Small collections (threading overhead > gain)
// - I/O-bound operations (use CompletableFuture instead)
// - Operations with side effects or shared mutable state
// - Ordered operations on unordered data (forEachOrdered on parallel is slow)

// NEVER do this in parallel streams
List<String> bad = new ArrayList<>();
stream.parallel().forEach(bad::add);  // ✗ ArrayList is not thread-safe
// Use collect() instead
```

# COMMON MISTAKES
```java
// 1 — Reusing a consumed stream
Stream<String> s = list.stream().filter(...);
s.count();    // OK
s.toList();   // ✗ IllegalStateException — stream already consumed

// 2 — Calling stream.forEach to build a new list
List<String> result = new ArrayList<>();
stream.forEach(result::add);         // ✗ side effect, not thread-safe
stream.collect(Collectors.toList()); // ✓

// 3 — Using peek for logic
stream.peek(e -> e.setProcessed(true)).count(); // ✗ fragile — count() may short-circuit

// 4 — Ignoring Optional — calling get() blindly
Optional<User> user = find(id);
user.get().getName();  // ✗ NoSuchElementException if empty
user.map(User::getName).orElse("Unknown");  // ✓
```

# BEST PRACTICES CHECKLIST
```
[ ] Use mapToInt/mapToLong/mapToDouble for numeric aggregation — avoid boxing
[ ] Prefer collect() over forEach() for building result collections
[ ] Never mutate external state inside stream operations
[ ] Use Collectors.toUnmodifiableList() when result must not be mutated
[ ] Parallel streams only for large, CPU-bound, stateless pipelines
[ ] Optional.orElseGet() over orElse() when the default is expensive to compute
[ ] Method references over equivalent lambdas where they are clearer
[ ] Break long stream pipelines into named variables or helper methods for readability
```
