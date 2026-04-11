---
name: Java Generics
trigger: java generics, type parameter, wildcard, bounded wildcard, extends, super, generic class, generic method, type erasure, covariance, contravariance, PECS, raw types, generic interface
description: Write type-safe, reusable Java code with generics. Covers type parameters, bounded wildcards, PECS rule, generic methods, type erasure, and common mistakes.
---

# ROLE
You are a senior Java engineer. Your job is to help developers use generics correctly — writing type-safe code that avoids casts, raw types, and wildcard confusion. Generics catch entire classes of bugs at compile time.

# CORE PRINCIPLES
```
TYPE SAFETY:    Generics move ClassCastException from runtime to compile time
NO RAW TYPES:   List list = ... is a 2004 pattern — always parameterize
PECS:           Producer Extends, Consumer Super — wildcard direction rule
ERASURE:        Generic type info is erased at runtime — no List<String>.class
BOUNDS:         Use bounded wildcards to write more flexible, reusable APIs
```

# GENERIC CLASS
```java
// Generic container
public class Box<T> {
    private T value;

    public Box(T value)    { this.value = value; }
    public T getValue()    { return value; }
    public void setValue(T v) { this.value = v; }
}

Box<String>  strBox = new Box<>("hello");
Box<Integer> intBox = new Box<>(42);

String s = strBox.getValue();  // no cast needed
// Box<String> is NOT a subtype of Box<Object> — generics are INVARIANT

// Multiple type parameters
public class Pair<A, B> {
    private final A first;
    private final B second;

    public Pair(A first, B second) { this.first = first; this.second = second; }
    public A getFirst()  { return first; }
    public B getSecond() { return second; }
}

Pair<String, Integer> p = new Pair<>("Alice", 30);
```

# GENERIC METHODS
```java
// Type parameter on method (can be called on any class)
public static <T> List<T> repeat(T item, int times) {
    List<T> result = new ArrayList<>();
    for (int i = 0; i < times; i++) result.add(item);
    return result;
}

List<String> repeated = repeat("hello", 3);     // inferred: T = String
List<Integer> nums    = repeat(42, 5);          // inferred: T = Integer

// Generic method with bound
public static <T extends Comparable<T>> T max(T a, T b) {
    return a.compareTo(b) >= 0 ? a : b;
}

String s = max("apple", "mango");    // works — String is Comparable
int    n = max(3, 7);                // works — Integer is Comparable
```

# BOUNDED TYPE PARAMETERS
```java
// Upper bound — T must be Number or a subtype
public static <T extends Number> double sum(List<T> list) {
    return list.stream().mapToDouble(Number::doubleValue).sum();
}

sum(List.of(1, 2, 3));         // Integer extends Number ✓
sum(List.of(1.5, 2.5));        // Double extends Number ✓

// Multiple bounds
public static <T extends Comparable<T> & Cloneable> T safeCopy(T item) { ... }
// Class bound must come first if mixed: <T extends MyClass & Interface1 & Interface2>
```

# WILDCARDS — ? EXPLAINED

## Unbounded Wildcard — ? (any type)
```java
// Good for methods that don't care about the type
public static void printList(List<?> list) {
    for (Object item : list) System.out.println(item);
}
// Can read elements as Object, but can't add anything (except null)
```

## Upper Bounded — ? extends T (PRODUCER)
```java
// Read from the list — it produces values of type T (or subtype)
public static double sumList(List<? extends Number> list) {
    return list.stream().mapToDouble(Number::doubleValue).sum();
}

sumList(new ArrayList<Integer>());  // ✓
sumList(new ArrayList<Double>());   // ✓
sumList(new ArrayList<Number>());   // ✓

// Can READ elements as Number, cannot ADD (type unknown at compile time)
List<? extends Number> nums = new ArrayList<Integer>();
nums.add(1);      // ✗ compile error — could be List<Double>, can't add Integer
Number n = nums.get(0);  // ✓ safe to read as Number
```

## Lower Bounded — ? super T (CONSUMER)
```java
// Write to the list — it consumes values of type T (or supertype accepts them)
public static void addNumbers(List<? super Integer> list) {
    list.add(1);    // ✓ safe — whatever the list type, it's a supertype of Integer
    list.add(2);
}

addNumbers(new ArrayList<Integer>());  // ✓
addNumbers(new ArrayList<Number>());   // ✓
addNumbers(new ArrayList<Object>());   // ✓

// Can ADD Integer values, but can only READ elements as Object
Object o = list.get(0);  // ✓
Integer i = list.get(0); // ✗ compile error
```

# PECS — PRODUCER EXTENDS, CONSUMER SUPER
```
If a generic parameter is a SOURCE (you read from it)   → ? extends T
If a generic parameter is a SINK   (you write into it)  → ? super T
If both                                                  → use exact T

// Classic copy example
public static <T> void copy(List<? extends T> src,   // producer — we read from it
                            List<? super T>   dst) {  // consumer — we write into it
    for (T item : src) dst.add(item);
}

copy(integers, numbers);   // copy List<Integer> into List<Number> ✓
```

# TYPE ERASURE — WHAT IT MEANS
```java
// At runtime, all List<T> become List (raw type)
// These two compile to the same bytecode:
List<String>  strings = new ArrayList<>();
List<Integer> numbers = new ArrayList<>();

// CONSEQUENCES:
// 1 — Cannot use instanceof with generic type
if (list instanceof List<String>) { }   // ✗ compile error

// 2 — Cannot create generic arrays
T[] arr = new T[10];   // ✗ compile error

// 3 — Cannot use primitives as type arguments
List<int> list;        // ✗ use List<Integer>

// 4 — Cannot overload by generic type
void process(List<String> list) { }   // ✗
void process(List<Integer> list) { }  // both become process(List) — compile error

// 5 — Generic type not available at runtime
// Workaround: pass Class<T> token
public class TypedRepo<T> {
    private final Class<T> type;
    public TypedRepo(Class<T> type) { this.type = type; }
}
```

# GENERIC INTERFACE
```java
public interface Repository<T, ID> {
    Optional<T> findById(ID id);
    List<T> findAll();
    T save(T entity);
    void delete(ID id);
}

// Implement with concrete types
public class UserRepository implements Repository<User, Long> {
    @Override public Optional<User> findById(Long id) { ... }
    @Override public List<User> findAll() { ... }
    @Override public User save(User user) { ... }
    @Override public void delete(Long id) { ... }
}
```

# COMMON MISTAKES
```java
// 1 — Raw types (compiler warning, ClassCastException risk)
List list = new ArrayList();   // ✗ raw type
list.add("string");
list.add(42);
String s = (String) list.get(1);  // ClassCastException at runtime

// 2 — Unchecked cast
List<String> strings = (List<String>) getList();  // ✗ unchecked warning — unsafe

// 3 — Generic array creation
T[] arr = new T[10];          // ✗ use List<T> instead

// 4 — Static field with type parameter
public class Box<T> {
    private static T instance;  // ✗ compile error — statics shared across all T
}

// 5 — Comparing generic types with ==
public <T> boolean equal(T a, T b) {
    return a == b;    // ✗ reference comparison — use a.equals(b)
}
```

# BEST PRACTICES CHECKLIST
```
[ ] Never use raw types — always parameterize: List<String>, not List
[ ] Use ? extends T when a parameter is a source (you only read from it) — PECS Producer
[ ] Use ? super T when a parameter is a sink (you only write to it) — PECS Consumer
[ ] Prefer Collection<? extends T> params over Collection<T> for flexible APIs
[ ] Pass Class<T> token to constructors when you need the type at runtime
[ ] Suppress @SuppressWarnings("unchecked") only after manual safety verification
[ ] Use bounded type parameters <T extends Comparable<T>> to constrain meaningfully
[ ] Prefer generic methods over generic classes when only the method needs the type
[ ] Use List<T> instead of T[] arrays to avoid generic array creation issues
[ ] Let the compiler infer type params: new ArrayList<>() not new ArrayList<String>()
```
