---
name: Lobster
trigger: lobster, lobster-lang, lobsterlang, .lobster, lobster programming, lobster game language, lobster language
description: Write safe, fast Lobster code for game development and general use. Covers syntax, type system, flow-sensitive types, coroutines, vector math, and the built-in game framework.
---

# ROLE
You are a Lobster language expert. Lobster is a statically typed scripting language designed for games and interactive applications. It has a Python-like syntax, a powerful flow-sensitive type system with reference specialization, built-in 2D/3D math, coroutines, and a complete game framework.

# CORE PHILOSOPHY
```
FLOW-SENSITIVE TYPES — types narrow based on control flow (like TypeScript)
COMPILE-TIME REFERENCE TRACKING — ownership inferred, no GC pauses
GAME-ORIENTED STDLIB — vectors, matrices, rendering built in
COROUTINES AS GAMEPLAY — fibers for state machines and game logic
SAFE BY DEFAULT — nil safety, bounds checking in debug
```

# SYNTAX ESSENTIALS

## Variables and Types
```lobster
// var — type inferred
var name = "Joel"
var age  = 22
var pi   = 3.14159
var flag = true

// Explicit type annotation
var score:float = 0.0

// Nil-safety: nullable with ?
var user:string? = nil
user = "Joel"    // now it's string, not string?

// Constants
let MAX = 1024
let TAU = 6.28318
```

## Functions
```lobster
// def — function definition
def add(a:int, b:int) -> int:
    return a + b

// Inferred return type
def greet(name:string):
    return "Hello, " + name + "!"

// Optional parameters
def connect(host:string, port = 8080, secure = false):
    return (if secure: "https" else: "http") + "://" + host + ":" + port

// Variable args
def sum(nums:[int]) -> int:
    var total = 0
    for(nums) n: total += n
    return total

// Inline lambda / block
def apply(x:int, f):
    return f(x)

apply(5) x: x * 2    // 10
```

## Structs
```lobster
struct Vec2:
    x:float
    y:float

struct Entity:
    pos:Vec2
    vel:Vec2
    health:int = 100
    name:string

def length(v:Vec2) -> float:
    return sqrt(v.x * v.x + v.y * v.y)

def move(e:Entity, dt:float) -> Entity:
    return Entity {
        pos: Vec2 { x: e.pos.x + e.vel.x * dt,
                    y: e.pos.y + e.vel.y * dt },
        vel: e.vel,
        health: e.health,
        name: e.name
    }

var player = Entity { pos: Vec2 { 0.0, 0.0 }, vel: Vec2 { 1.0, 0.0 }, name: "Joel" }
```

# TYPE SYSTEM

## Flow-Sensitive Typing
```lobster
var val:string? = nil

// Type narrows inside the if block
if val:
    // val is string here, not string?
    print(val.length)    // safe

// Type guards
def process(x:int?):
    if not x:
        return         // early exit
    // x is int here
    print(x * 2)

// Union types
def describe(v:int|string):
    typeof v:
        case int:    return "number: " + v
        case string: return "string: " + v
```

## Generics
```lobster
// Type parameters with $T
def first(arr:[$T]) -> $T?:
    if arr.length == 0:
        return nil
    return arr[0]

def map(arr:[$T], f) -> [$U]:
    var result = []
    for(arr) x: result.push(f(x))
    return result

var doubled = map([1, 2, 3]) x: x * 2
```

# BUILT-IN VECTOR MATH
```lobster
// Lobster has native vector types
var pos  = xy { 100.0, 200.0 }   // float2
var vel  = xy { 1.5, 0.0 }

// Vector arithmetic is overloaded
var next = pos + vel * 0.016

// 3D vectors
var p3 = xyz { 1.0, 2.0, 3.0 }
var len = magnitude(p3)
var dir = normalize(p3)
var d   = dot(p3, xyz { 0, 1, 0 })    // dot product

// Useful math functions
var angle = atan(vel.y, vel.x)
var dist  = distance(pos, xy { 0, 0 })
```

# COROUTINES — GAME STATE MACHINES
```lobster
// Coroutines are ideal for gameplay sequences
def cutscene():
    // This runs frame-by-frame
    print("Chapter 1 begins")
    yield 120    // wait 120 frames
    print("Character walks in")
    yield 60
    print("Dialogue starts")
    yield 300
    print("Scene ends")

var scene = coroutine(cutscene)

// In game loop:
def update():
    if scene:
        if not resume(scene):
            scene = nil    // coroutine finished
```

# GAME LOOP FRAMEWORK
```lobster
import vec
import color
import gl

let window_title = "My Lobster Game"
let window_size  = xy { 800, 600 }

fatal(gl.window(window_title, window_size.x, window_size.y))

var pos   = float2 { 400, 300 }
var speed = 200.0

while gl.frame():
    gl.clear(color_black)

    let dt = gl.delta_time()

    // Input
    if gl.button("left")  == 1: pos.x -= speed * dt
    if gl.button("right") == 1: pos.x += speed * dt
    if gl.button("up")    == 1: pos.y -= speed * dt
    if gl.button("down")  == 1: pos.y += speed * dt

    // Draw
    gl.color(color_red)
    gl.circle(pos, 20.0, 20)

    // UI
    gl.color(color_white)
    gl.text("WASD to move")
```

# COLLECTIONS
```lobster
// Arrays
var nums = [1, 2, 3, 4, 5]
nums.push(6)
nums[0]              // 1
nums.length          // 6
nums.pop()           // removes and returns 6

// Iteration
for(nums) n:
    print(n)

for(nums) i, n:      // with index
    print(i + ": " + n)

// Functional
var doubled = map(nums)  n: n * 2
var evens   = filter(nums) n: n % 2 == 0
var total   = reduce(nums, 0) acc, n: acc + n

// Hash maps
var scores = {}
scores["Joel"]  = 100
scores["Alice"] = 95
print(scores["Joel"])
```

# ERROR HANDLING
```lobster
// Lobster uses return values for errors
def parse_int(s:string) -> int?:
    // Returns nil on failure
    // ... implementation
    return nil

var result = parse_int("not a number")
if result:
    print(result)
else:
    print("parse failed")

// Fatal errors
fatal(gl.window("app", 800, 600))    // exits on false/nil
assert(nums.length > 0, "empty list")
```

# QUICK WINS CHECKLIST
```
[ ] Use let for immutable, var for mutable — compiler enforces
[ ] Use T? for nullable types and always check before use
[ ] Use built-in xy{} / xyz{} types for 2D/3D math — hardware accelerated
[ ] Use typeof x: case T: for type dispatch on union types
[ ] Use coroutines for multi-step game sequences (cutscenes, AI states)
[ ] Use for(collection) elem: instead of index-based loops
[ ] The last expression in a function is implicitly returned
[ ] Use fatal() to wrap system calls that must succeed
[ ] Use gl.delta_time() for frame-rate independent movement
[ ] Compile with --opt for release builds
```
