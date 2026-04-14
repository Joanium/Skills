---
name: Odin
trigger: odin, odin-lang, .odin, odin programming, odin language, odin systems, odinlang
description: Write safe, explicit, low-level Odin code. Covers syntax, types, allocators, context system, SOA, foreign imports, and build system.
---

# ROLE
You are an Odin language expert. Odin is a systems programming language built for high-performance, low-level programming with the simplicity and clarity of a scripting language. No hidden allocations, no undefined behavior, no macros — everything is explicit.

# CORE PHILOSOPHY
```
DATA-ORIENTED BY DEFAULT — SOA/AOS patterns are first class
EXPLICIT OVER IMPLICIT — no operator overloading, no implicit conversions
CONTEXT SYSTEM — thread-local context carries allocator, logger, user data
MULTIPLE RETURN VALUES — error handling without exceptions or Result monads
COMPILE-TIME PARAMETERS — parametric polymorphism without generics syntax
```

# SYNTAX ESSENTIALS

## Variables and Constants
```odin
package main

import "core:fmt"

main :: proc() {
    // Variable declaration (mutable)
    x : int = 10
    name : string = "Joel"

    // Type inference with :=
    y := 42
    message := "hello"

    // Constant
    MAX :: 1024
    PI :: 3.14159

    // Multiple assignment
    a, b := 1, 2
    a, b = b, a    // swap

    fmt.println(x, y, message)
}
```

## Procedures
```odin
// Basic procedure
add :: proc(a, b: int) -> int {
    return a + b
}

// Multiple return values
min_max :: proc(a, b: int) -> (int, int) {
    if a < b { return a, b }
    return b, a
}

lo, hi := min_max(5, 3)

// Named return values
divide :: proc(a, b: f64) -> (result: f64, ok: bool) {
    if b == 0 { return 0, false }
    return a / b, true
}

result, ok := divide(10.0, 3.0)

// Variadic
sum :: proc(nums: ..int) -> int {
    total := 0
    for n in nums { total += n }
    return total
}
```

## Structs
```odin
Vector2 :: struct {
    x, y: f32,
}

Entity :: struct {
    pos:      Vector2,
    velocity: Vector2,
    health:   int,
    name:     string,
}

// Initialization
e := Entity {
    pos      = {1.0, 2.0},
    velocity = {0.5, 0.0},
    health   = 100,
    name     = "Player",
}

// Struct methods — procedures with struct as first param
entity_move :: proc(e: ^Entity, dt: f32) {
    e.pos.x += e.velocity.x * dt
    e.pos.y += e.velocity.y * dt
}

entity_move(&e, 0.016)
```

# THE CONTEXT SYSTEM
```odin
// Every procedure call carries an implicit 'context'
// Contains: allocator, temp_allocator, logger, user_ptr

// Override allocator for a scope
{
    context.allocator = my_arena_allocator
    data := make([]int, 100)   // uses arena allocator
    // arena freed externally
}

// Custom context data
My_Context :: struct {
    request_id: string,
    user_id:    int,
}

ctx_data := My_Context{request_id: "abc-123", user_id: 42}
context.user_ptr = &ctx_data

// Retrieve in any called procedure
get_request_id :: proc() -> string {
    data := (^My_Context)(context.user_ptr)
    return data.request_id if data != nil else ""
}
```

# MEMORY AND ALLOCATORS
```odin
import "core:mem"

main :: proc() {
    // Default allocator is heap (libc malloc)
    arr := make([]int, 10)
    defer delete(arr)

    // Arena allocator — free all at once
    arena: mem.Arena
    mem.arena_init(&arena, make([]byte, 1024*1024))
    defer mem.arena_destroy(&arena)

    context.allocator = mem.arena_allocator(&arena)
    data := make([]Entity, 500)   // allocated from arena
    _ = data
    // freed when arena_destroy is called

    // Stack allocation
    buf: [256]byte
    fa := mem.Fixed_Buffer_Allocator{}
    mem.fixed_buffer_allocator_init(&fa, buf[:])
    context.allocator = mem.fixed_buffer_allocator_allocator(&fa)
}
```

# ENUMS AND UNIONS
```odin
Direction :: enum {
    North,
    South,
    East,
    West,
}

// Bit set from enum
Directions :: bit_set[Direction]
accessible := Directions{.North, .East}
can_go_north := .North in accessible

// Tagged union (sum type)
Shape :: union {
    Circle,
    Rectangle,
    Point,
}

Circle    :: struct { radius: f32 }
Rectangle :: struct { w, h: f32 }
Point     :: struct {}

area :: proc(s: Shape) -> f32 {
    switch v in s {
    case Circle:    return 3.14159 * v.radius * v.radius
    case Rectangle: return v.w * v.h
    case Point:     return 0
    }
    return 0
}
```

# DATA-ORIENTED: SOA
```odin
// Structure of Arrays — cache friendly
Particles_SOA :: struct {
    x, y, z:    []f32,
    vx, vy, vz: []f32,
    alive:      []bool,
    count:      int,
}

// Odin built-in #soa tag
Particle :: struct {
    pos:      [3]f32,
    velocity: [3]f32,
    alive:    bool,
}

particles: #soa[1000]Particle   // automatically SOA layout

// Access is same syntax as AOS
particles[0].pos = {1, 2, 3}
```

# COMPILE-TIME PARAMETERS
```odin
// Parametric polymorphism using $T
max :: proc(a, b: $T) -> T {
    return a if a > b else b
}

x := max(3, 5)          // T = int
y := max(1.5, 2.5)      // T = f64

// Type constraint
print_numeric :: proc(v: $T) where intrinsics.type_is_numeric(T) {
    fmt.println(v)
}
```

# FOREIGN IMPORT (C INTEROP)
```odin
foreign import libc "system:c"

@(default_calling_convention="c")
foreign libc {
    printf  :: proc(fmt: cstring, #c_vararg args: ..any) -> i32 ---
    malloc  :: proc(size: int) -> rawptr ---
    free    :: proc(ptr: rawptr) ---
}

main :: proc() {
    printf("Hello from C, %s!\n", "Odin")
}
```

# BUILD SYSTEM
```bash
odin build .                    # build current directory package
odin run .                      # build and run
odin run main.odin              # run single file
odin build . -o:speed           # optimized for speed
odin build . -o:size            # optimized for binary size
odin build . -debug             # with debug info
odin test .                     # run tests
odin check .                    # type check without building
```

# QUICK WINS CHECKLIST
```
[ ] Use defer for cleanup — runs at end of scope (LIFO order)
[ ] Always pass ^Struct (pointer) when mutating inside a procedure
[ ] Use context.allocator override for scope-local memory strategies
[ ] Use bit_set[Enum] instead of bit flags — type safe and readable
[ ] Use #soa for arrays of structs with hot update loops (ECS, particles)
[ ] Use or_return (Odin 0.12+) to propagate multiple-return errors
[ ] Use when clause for compile-time conditional code
[ ] Prefer tagged union over interface for performance-critical dispatch
[ ] Named proc parameters in calls: my_proc(x = 1, y = 2) for clarity
[ ] Use intrinsics package for CPU-level operations and SIMD
```
