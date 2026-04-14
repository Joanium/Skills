---
name: Io
trigger: io language, io-lang, iolanguage, io programming, .io language, io prototype, iolang
description: Write expressive Io code — a pure prototype-based OO language with a minimal syntax, message passing, coroutines, and powerful metaprogramming via slots.
---

# ROLE
You are an Io language expert. Io is a pure prototype-based language inspired by Smalltalk, Self, and Lisp. Everything is a message send; everything is an object; there are no classes — only objects that clone from other objects. Its simplicity makes it ideal for teaching and metaprogramming.

# CORE PHILOSOPHY
```
EVERYTHING IS A MESSAGE — a + b is "send + to a with argument b"
PURE PROTOTYPE OOP — clone objects, not instantiate classes
MINIMAL SYNTAX — only message sends; everything else is library
SLOTS ARE EVERYTHING — objects are bags of named slots (methods + data)
METACIRCULAR — Io can reprogram itself at runtime
```

# SYNTAX ESSENTIALS

## Basics — It's All Messages
```io
# Print
"Hello, World!" println

# Variables — slots on the current object
name := "Joel"        # := creates a new slot
age  := 22

# Update existing slot
name = "Joel Jolly"   # = updates (fails if slot doesn't exist)

# Arithmetic — all message sends
3 + 4                 # → 7
10 * (2 + 3)          # → 50
2 ** 8                # → 256

# String operations
"hello" asUppercase   # "HELLO"
"hello" size          # 5
"hello" .. " world"   # "hello world" (concatenation)
```

## Method Definitions
```io
# Method is an object — assigned to a slot
greet := method(name,
    "Hello, " .. name .. "!" println
)

greet("Joel")

# With multiple args
add := method(a, b, a + b)
add(3, 4)   # 7

# No-arg method
sayHi := method(
    "Hi!" println
)
sayHi

# Method returns last evaluated expression
double := method(x, x * 2)
double(5)   # 10
```

# PROTOTYPE-BASED OOP
```io
# All objects clone from Object (or other objects)
# No "class" keyword — just clone and add slots

Animal := Object clone
Animal name := "Unknown"
Animal age  := 0

Animal speak := method(
    "..." println
)

Animal describe := method(
    (name .. " (age " .. age .. ")") println
)

# Create an instance by cloning
dog := Animal clone
dog name = "Rex"
dog age  = 3

dog speak        # ...
dog describe     # Rex (age 3)

# Override a slot in the clone
dog speak = method(
    (name .. " says: Woof!") println
)

dog speak   # Rex says: Woof!

# Multi-level inheritance via prototype chain
GuideDog := dog clone
GuideDog owner := "Alice"
GuideDog speak = method(
    (name .. " guides " .. owner) println
)
```

# SLOTS AND INTROSPECTION
```io
# Get all slot names
Object slotNames println

# Check if slot exists
dog hasSlot("name") println    # true
dog hasSlot("fly") println     # false

# Get slot value
dog getSlot("name") println    # Rex

# Remove a slot
dog removeSlot("age")

# Set a slot dynamically
dog setSlot("breed", "Husky")

# Get proto chain
dog proto println    # Animal
```

# COLLECTIONS

## Lists
```io
nums := list(1, 2, 3, 4, 5)
nums size           # 5
nums first          # 1
nums last           # 5
nums at(2)          # 3 (0-indexed)

nums append(6)      # adds 6
nums prepend(0)     # adds 0 at front

# Functional operations
doubled := nums map(x, x * 2)
evens   := nums select(x, x % 2 == 0)
total   := nums reduce(acc, x, acc + x, 0)

# foreach
nums foreach(i, v,
    writeln(i, ": ", v)
)
```

## Maps (Dictionaries)
```io
config := Map clone
config atPut("host", "localhost")
config atPut("port", 8080)

config at("host")            # "localhost"
config hasKey("port")        # true

config keys println
config values println

config foreach(k, v,
    writeln(k, " = ", v)
)
```

# CONTROL FLOW
```io
# if/then/else
(age >= 18) ifTrue(
    "adult" println
) ifFalse(
    "minor" println
)

# Ternary-like
result := (x > 0) ifTrue("positive") ifFalse("non-positive")

# while loop
i := 0
while(i < 5,
    i println
    i = i + 1
)

# for loop
for(i, 1, 10, 1,
    i println
)

# loop with break
loop(
    n := Random value(1, 10) floor
    if(n == 7, break)
    n println
)
```

# COROUTINES
```io
producer := Object clone
producer run := method(
    1 to(5) foreach(i, v,
        v println
        yield
    )
)

# Start as coroutine
coro := producer coroutine
coro resume
coro resume
# Each resume runs until the next yield
```

# METAPROGRAMMING
```io
# Override message forward for method_missing behavior
Dog := Object clone

Dog forward := method(
    writeln("Unknown message: ", thisMessage name)
)

dog := Dog clone
dog flyToTheMoon   # Unknown message: flyToTheMoon

# Override operators
Vector := Object clone
Vector x := 0
Vector y := 0

Vector + := method(other,
    v := Vector clone
    v x = x + other x
    v y = y + other y
    v
)
```

# CONCURRENCY (ACTORS)
```io
# Io has actor-based concurrency — objects become actors with @
Worker := Object clone

Worker doWork := method(n,
    writeln("Working on: ", n)
    System sleep(1)
    n * n
)

w := Worker clone

# Non-blocking call — returns a Future
future := w @doWork(5)
# ... do other work ...
result := future result   # blocks until done
writeln("Result: ", result)
```

# QUICK WINS CHECKLIST
```
[ ] Use := to create new slots, = to update existing ones
[ ] Clone objects for "instantiation" — no class keyword
[ ] Use hasSlot before accessing uncertain slots to avoid errors
[ ] Override forward for dynamic method dispatch (method_missing)
[ ] Use @ prefix for async non-blocking message sends
[ ] Use yield inside coroutines with resume to step through
[ ] All collections have select/map/reduce — prefer them over manual loops
[ ] Use method(arg, body) — no separator between args and body needed
[ ] Parentheses in message sends are optional for no-arg methods
[ ] writeln is cleaner than println for concatenated output
```
