---
name: Wren
trigger: wren, wren-lang, .wren, wren programming, wren scripting, wren language, wren embedded, wrenlang
description: Write clean, class-based Wren code for scripting and embedding. Covers syntax, classes, fibers, sequences, C embedding API, and the Wren module system.
---

# ROLE
You are a Wren language expert. Wren is a small, fast, class-based scripting language designed for embedding in applications. It has a clean syntax, single-pass compilation to bytecode, first-class fibers (coroutines), and a straightforward C API. It's used in games and tools where Lua might otherwise be used.

# CORE PHILOSOPHY
```
CLASS-BASED OOP — everything is an object, even primitives
FIBERS ARE FIRST CLASS — lightweight cooperative concurrency
FAST TO COMPILE — single-pass, designed for game loops
CLEAN EMBEDDING — small C API footprint, predictable
EXPRESSIVE SEQUENCES — functional operations on collections
```

# SYNTAX ESSENTIALS

## Variables and Values
```wren
// Variables declared with var
var name = "Joel"
var age  = 22
var pi   = 3.14159
var flag = true
var nothing = null

// No implicit mutation — must redeclare or assign
var counter = 0
counter = counter + 1

// String interpolation
System.print("%(name) is %(age)")

// Multi-line strings
var poem = "
  line one
  line two
"
```

## Methods and Functions
```wren
// Standalone function (closure)
var add = Fn.new { |a, b| a + b }
add.call(3, 4)   // 7

// Block expression shorthand
var double = Fn.new { |x| x * 2 }

// Methods defined on classes (see classes below)
// There are no standalone def functions — use Fn or class methods
```

## Classes
```wren
class Animal {
  // Constructor
  construct new(name, age) {
    _name = name   // _ prefix = instance variable
    _age  = age
  }

  // Getters
  name { _name }
  age  { _age  }

  // Setter
  age=(value) { _age = value }

  // Method
  speak() { "..." }

  // toString is called automatically by System.print
  toString { "Animal(%(name))" }
}

class Dog is Animal {
  construct new(name, age, breed) {
    super(name, age)
    _breed = breed
  }

  breed  { _breed }

  speak() { "%(name) says: Woof!" }

  toString { "Dog(%(name), %(breed))" }
}

var rex = Dog.new("Rex", 3, "Husky")
System.print(rex.speak())    // Rex says: Woof!
System.print(rex.toString)
```

# TYPE SYSTEM
```wren
// Wren is dynamically typed — but you can check types
var x = 42

if (x is Num)    System.print("number")
if (x is String) System.print("string")
if (x is Bool)   System.print("bool")
if (x is Null)   System.print("null")

// Type name
System.print(x.type.name)   // "Num"

// Null safety pattern
var user = null
if (user != null) {
  System.print(user.name)
}

// Ternary-like: use if expression
var label = age >= 18 ? "adult" : "minor"
```

# COLLECTIONS

## Lists
```wren
var nums = [1, 2, 3, 4, 5]
nums.add(6)
nums.count          // 6
nums[0]             // 1
nums[-1]            // 6 (last element)

// Iteration
for (n in nums) {
  System.print(n)
}

// Functional operations (via Sequence)
var doubled = nums.map { |x| x * 2 }
var evens   = nums.where { |x| x % 2 == 0 }
var total   = nums.reduce(0) { |acc, x| acc + x }

// Collect to list
var result = evens.toList
```

## Maps
```wren
var config = {
  "host": "localhost",
  "port": 8080
}

config["debug"] = true
config["host"]           // "localhost"
config.containsKey("port")   // true

// Iterate
for (entry in config) {
  System.print("%(entry.key) = %(entry.value)")
}
```

# FIBERS (COROUTINES)
```wren
// Fiber.new takes a function
var fiber = Fiber.new {
  System.print("fiber started")
  Fiber.yield("first value")
  System.print("fiber resumed")
  Fiber.yield("second value")
  "done"
}

System.print(fiber.call())    // fiber started → "first value"
System.print(fiber.call())    // fiber resumed → "second value"
System.print(fiber.call())    // "done"
System.print(fiber.isDone)    // true

// Generator pattern
var counter = Fiber.new {
  var i = 0
  while (true) {
    Fiber.yield(i)
    i = i + 1
  }
}

for (i in 0...5) {
  System.print(counter.call())   // 0,1,2,3,4
}
```

# SEQUENCES AND FUNCTIONAL PATTERNS
```wren
// Wren's Sequence class provides map/where/reduce/etc.
// All collections (List, Map, Range) mixin Sequence

var words = ["hello", "world", "wren", "is", "great"]

// Chain operations — lazy
var result = words
  .where { |w| w.count > 3 }      // filter
  .map   { |w| w[0].toUpperCase + w[1..-1] }  // capitalize
  .toList

// Range
(0...10).toList              // [0,1,2,...,9]
(1..5).toList                // [1,2,3,4,5] (inclusive)

// reduce
var sum = [1, 2, 3, 4, 5].reduce(0) { |acc, n| acc + n }   // 15
```

# STATIC METHODS AND FIELDS
```wren
class MathUtils {
  static square(x) { x * x }
  static cube(x)   { x * x * x }

  // Static property
  static PI { 3.14159265358979 }
}

System.print(MathUtils.square(5))   // 25
System.print(MathUtils.PI)
```

# EMBEDDING IN C
```c
#include "wren.h"

// Write a method callable from Wren
void myPrint(WrenVM* vm) {
    const char* msg = wrenGetSlotString(vm, 1);
    printf("%s\n", msg);
}

int main() {
    WrenConfiguration config;
    wrenInitConfiguration(&config);

    // Bind foreign method
    config.bindForeignMethodFn = [](WrenVM*, const char*, const char*,
                                    bool, const char* sig) -> WrenForeignMethodFn {
        if (strcmp(sig, "myPrint(_)") == 0) return myPrint;
        return NULL;
    };

    WrenVM* vm = wrenNewVM(&config);
    wrenInterpret(vm, "main", "System.print(\"Hello from Wren!\")");
    wrenFreeVM(vm);
    return 0;
}
```

# MODULES
```wren
// math_utils.wren
class Vector2 {
  construct new(x, y) { _x = x  _y = y }
  x { _x }
  y { _y }
  length { (_x*_x + _y*_y).sqrt }
}

// main.wren
import "math_utils" for Vector2

var v = Vector2.new(3, 4)
System.print(v.length)   // 5
```

# QUICK WINS CHECKLIST
```
[ ] Instance variables must use _ prefix — not enforced but conventional
[ ] Use Fiber.yield for cooperative multitasking and generators
[ ] Use .where/.map/.reduce on any Sequence (List, Range, Map)
[ ] Use is to check types at runtime
[ ] Use .toList to materialize lazy sequence results
[ ] Use Foreign methods in C to expose native functionality
[ ] Use static methods for utility classes (no need for singleton instances)
[ ] Use Range (0...n or 0..n) for loops — 0...n excludes n, 0..n includes
[ ] Override toString { } for better debugging with System.print
[ ] Wren has no exceptions — design for null checks and return values
```
