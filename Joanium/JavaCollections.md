---
name: Java Collections
trigger: java collections, list vs arraylist, hashmap, linkedlist, treemap, set, queue, deque, collections framework, java data structures, choose collection, collection performance
description: Master the Java Collections Framework — picking the right data structure, understanding time complexity, and avoiding common pitfalls with List, Map, Set, and Queue types.
---

# ROLE
You are a senior Java engineer. Your job is to guide correct, performant use of the Java Collections Framework. The wrong collection choice causes silent bugs, memory bloat, and slow code at scale.

# CORE PRINCIPLES
```
RIGHT TOOL:     Every collection has a purpose — don't default to ArrayList for everything
INTERFACE FIRST: Code to List/Map/Set interfaces, not ArrayList/HashMap implementations
NULL AWARENESS: Know which collections allow null keys/values and which blow up
THREAD SAFETY:  Standard collections are NOT thread-safe — know when to use concurrent variants
IMMUTABILITY:   Prefer unmodifiable views or immutable collections when mutation isn't needed
```

# COLLECTION HIERARCHY
```
Iterable
  └── Collection
        ├── List       → ordered, index-based, allows duplicates
        │     ├── ArrayList
        │     ├── LinkedList
        │     └── Vector (legacy — avoid)
        ├── Set        → no duplicates
        │     ├── HashSet
        │     ├── LinkedHashSet
        │     └── TreeSet
        └── Queue      → FIFO / priority order
              ├── LinkedList
              ├── PriorityQueue
              └── ArrayDeque (preferred Deque impl)

Map (not Collection)
  ├── HashMap
  ├── LinkedHashMap
  ├── TreeMap
  └── Hashtable (legacy — avoid)
```

# CHOOSING THE RIGHT COLLECTION

## List
```
ArrayList     → random access by index, fast reads, slow mid-insert (O(n) shift)
LinkedList    → fast insert/delete at head/tail, slow random access (O(n) traverse)
CopyOnWriteArrayList → thread-safe reads, expensive writes (snapshot on write)

RULE: Default to ArrayList. Use LinkedList only when you have many insertions
      at known positions and rare random access.

ArrayList<String> list = new ArrayList<>();     ✓ default
List<String> list = new ArrayList<>();          ✓ prefer interface type
LinkedList<String> q = new LinkedList<>();      ✓ as queue/deque only
```

## Map
```
HashMap        → O(1) get/put avg, no order guarantee, one null key allowed
LinkedHashMap  → insertion-order iteration, slight memory overhead
TreeMap        → sorted by key (natural/Comparator), O(log n) ops
EnumMap        → fastest map when keys are enum constants

RULE: Default to HashMap. Use LinkedHashMap when iteration order matters.
      Use TreeMap when sorted keys are needed.

Map<String, Integer> scores = new HashMap<>();
Map<String, Integer> ordered = new LinkedHashMap<>();
Map<String, Integer> sorted  = new TreeMap<>();
```

## Set
```
HashSet        → O(1) contains, no order, allows one null
LinkedHashSet  → insertion-order, slightly slower than HashSet
TreeSet        → sorted, O(log n), no null allowed (compareTo would NPE)

RULE: Default to HashSet. Use TreeSet only when sorted iteration is required.
```

## Queue / Deque
```
ArrayDeque     → fastest general-purpose queue/stack (no null allowed)
PriorityQueue  → heap-backed, elements dequeued by priority (not FIFO)
LinkedList     → also implements Deque, allows null

RULE: Use ArrayDeque for both stack (push/pop) and queue (offer/poll).
      Replace Stack class entirely — it's synchronized and slow.

Deque<String> stack = new ArrayDeque<>();    ✓
Stack<String> stack = new Stack<>();         ✗ (legacy, synchronized)
```

# TIME COMPLEXITY CHEAT SHEET
```
Operation       ArrayList   LinkedList   HashMap    TreeMap    HashSet    TreeSet
──────────────────────────────────────────────────────────────────────────────────
get(index)        O(1)        O(n)         —          —          —          —
add(end)          O(1)*       O(1)         —          —          —          —
add(middle)       O(n)        O(1)**       —          —          —          —
remove(index)     O(n)        O(1)**       —          —          —          —
contains(val)     O(n)        O(n)         O(1)*      O(log n)   O(1)*      O(log n)
put/get (key)       —           —          O(1)*      O(log n)   —          —

* = amortized average   ** = after traversal to position
```

# COMMON PITFALLS

## Modifying a Collection While Iterating
```java
// BAD — ConcurrentModificationException
for (String item : list) {
    if (item.startsWith("X")) list.remove(item);  // ✗
}

// GOOD — use iterator's remove
Iterator<String> it = list.iterator();
while (it.hasNext()) {
    if (it.next().startsWith("X")) it.remove();   // ✓
}

// BEST — use removeIf (Java 8+)
list.removeIf(item -> item.startsWith("X"));       // ✓
```

## HashMap and equals/hashCode
```java
// Objects used as Map keys MUST implement both equals() and hashCode()
// If hashCode() changes after insertion, you can never find the key again

// BAD — mutable key
Map<List<Integer>, String> map = new HashMap<>();
List<Integer> key = new ArrayList<>(List.of(1, 2));
map.put(key, "value");
key.add(3);                 // ✗ key changed — map.get(key) returns null now

// GOOD — use immutable keys (String, Integer, record, etc.)
Map<String, String> map = new HashMap<>();
```

## Arrays.asList() Trap
```java
List<String> fixed = Arrays.asList("a", "b", "c");
fixed.add("d");   // ✗ UnsupportedOperationException — fixed size!

// GOOD — mutable copy
List<String> mutable = new ArrayList<>(Arrays.asList("a", "b", "c"));

// BETTER (Java 9+) — truly immutable
List<String> immutable = List.of("a", "b", "c");
```

# IMMUTABLE & UNMODIFIABLE COLLECTIONS

## Java 9+ Factory Methods (Preferred)
```java
List<String>        immutable = List.of("a", "b", "c");       // no nulls
Set<Integer>        immutable = Set.of(1, 2, 3);               // no nulls, no duplicates
Map<String, Integer> immutable = Map.of("a", 1, "b", 2);       // no nulls

// Copyof — immutable snapshot of existing collection
List<String> copy = List.copyOf(existingList);
```

## Unmodifiable Wrappers (allow nulls, allow modification of original)
```java
List<String> view = Collections.unmodifiableList(originalList);
// changing originalList still changes view — this is NOT a copy
```

# SORTING
```java
// Natural order
Collections.sort(list);
list.sort(null);
list.sort(Comparator.naturalOrder());

// Custom order
list.sort(Comparator.comparing(Person::getAge));
list.sort(Comparator.comparing(Person::getLastName).thenComparing(Person::getFirstName));
list.sort(Comparator.comparing(Person::getAge).reversed());

// Sort by multiple fields
list.sort(Comparator.comparingInt(Person::getAge)
                    .thenComparing(Person::getName));
```

# THREAD-SAFE ALTERNATIVES
```
ConcurrentHashMap       → high-throughput concurrent map (never use Hashtable)
CopyOnWriteArrayList    → safe iteration, expensive writes
ConcurrentLinkedQueue   → non-blocking queue
BlockingQueue impls     → ArrayBlockingQueue, LinkedBlockingQueue (producer-consumer)
Collections.synchronizedList(list)  → coarse lock — prefer concurrent alternatives

RULE: ConcurrentHashMap > synchronizedMap() >> Hashtable (never)
```

# UTILITY METHODS — Collections class
```java
Collections.sort(list);                         // sort in-place
Collections.shuffle(list);                      // random shuffle
Collections.reverse(list);                      // reverse in-place
Collections.frequency(list, element);           // count occurrences
Collections.disjoint(list1, list2);             // true if no common elements
Collections.min(list) / Collections.max(list);  // min/max with Comparable
Collections.nCopies(5, "x");                    // ["x","x","x","x","x"]
Collections.singletonList("only");              // immutable single-element list
Collections.emptyList();                        // immutable empty list (reusable)
```

# BEST PRACTICES CHECKLIST
```
[ ] Declare variables with interface type (List, Map, Set — not ArrayList, HashMap)
[ ] Override equals() AND hashCode() for any class used as a Map key or Set element
[ ] Use List.of() / Map.of() for constants and return values that must not be mutated
[ ] Never expose mutable collections in public API — return unmodifiable views or copies
[ ] Specify initial capacity for large known-size collections: new ArrayList<>(1000)
[ ] Use EnumMap / EnumSet when keys/elements are enums — fastest implementations
[ ] Prefer removeIf / replaceAll over manual index-based loops for mutations
[ ] Never use raw types: List list = ... is a compiler warning and runtime hazard
```
