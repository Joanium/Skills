---
name: V (Vlang)
trigger: vlang, v language, .v file programming, vlang programming, v programming language, vweb, vpm
description: Write fast, safe V code. Covers syntax, immutability by default, option/result types, concurrency, vweb, ORM, and the V package manager.
---

# ROLE
You are a V language expert. V is a statically typed compiled language designed for performance, safety, and fast compilation. Inspired by Go, it compiles in under a second and produces small binaries. Zero-cost C interop, no null, no undefined behavior by default.

# CORE PHILOSOPHY
```
IMMUTABLE BY DEFAULT — variables require mut keyword to mutate
NO NULL — Option and Result types replace nil/null
FAST COMPILATION — entire compiler is under 1MB
C INTEROP ZERO COST — translate C headers automatically
SIMPLE AND EXPLICIT — no operator overloading, no implicit conversions
```

# SYNTAX ESSENTIALS

## Variables
```v
fn main() {
    // Immutable by default
    name := 'Joel'
    age  := 22

    // Mutable requires mut
    mut counter := 0
    counter++

    // Multiple assignment
    a, b := 10, 20
    println('$name is $age')   // string interpolation
}
```

## Functions
```v
fn add(a int, b int) int {
    return a + b
}

// Multiple return values
fn min_max(a int, b int) (int, int) {
    if a < b { return a, b }
    return b, a
}

lo, hi := min_max(5, 3)

// Optional return
fn find(items []string, target string) ?string {
    for item in items {
        if item == target { return item }
    }
    return none
}

// Result return
fn divide(a f64, b f64) !f64 {
    if b == 0 { return error('division by zero') }
    return a / b
}
```

## Structs
```v
struct User {
    name  string
    email string
mut:
    age   int       // mutable field
    score f64
pub:
    id    int       // public immutable
pub mut:
    active bool     // public mutable
}

fn new_user(name string, email string) User {
    return User{
        name: name
        email: email
        age: 0
        active: true
    }
}

// Method
fn (u User) greet() string {
    return 'Hello, I am $u.name'
}

// Mutable method
fn (mut u User) birthday() {
    u.age++
}

user := new_user('Joel', 'joeljollyhere@gmail.com')
println(user.greet())
```

# OPTION AND RESULT

## Option Type
```v
fn get_config(key string) ?string {
    config := {'host': 'localhost', 'port': '8080'}
    return config[key] or { return none }
}

// or{} to provide default
host := get_config('host') or { 'default.com' }

// if guard
if val := get_config('host') {
    println('host is $val')
} else {
    println('no host configured')
}
```

## Result Type
```v
fn read_file(path string) !string {
    content := os.read_file(path) or {
        return error('cannot read $path: $err')
    }
    return content
}

// Propagate with ?
fn process(path string) !string {
    data := read_file(path)!   // ! propagates error (like try in other langs)
    return data.to_upper()
}

// Catch at call site
result := process('data.txt') or {
    eprintln('Error: $err')
    ''
}
```

# ARRAYS AND MAPS
```v
// Arrays
mut nums := [1, 2, 3, 4, 5]
nums << 6                          // append
first := nums[0]
slice := nums[1..3]                // [2, 3]
doubled := nums.map(it * 2)        // [2,4,6,8,10,12]
evens   := nums.filter(it % 2 == 0)
total   := nums.reduce(fn(a b int) int { return a + b }, 0)

// Fixed-size array
fixed := [3]int{init: 0}           // [0, 0, 0]

// Maps
mut ages := map[string]int{}
ages['Joel'] = 22
ages['Alice'] = 30
if val := ages['Joel'] {
    println('Joel is $val')
}
```

# ENUMS
```v
enum Direction {
    north
    south
    east
    west
}

enum Color {
    red = 1
    green
    blue
    custom(r int, g int, b int)   // enum with data
}

fn describe(d Direction) string {
    return match d {
        .north { 'heading north' }
        .south { 'heading south' }
        .east  { 'heading east' }
        .west  { 'heading west' }
    }
}
```

# INTERFACES
```v
interface Shape {
    area() f64
    perimeter() f64
}

struct Circle {
    radius f64
}

fn (c Circle) area() f64      { return math.pi * c.radius * c.radius }
fn (c Circle) perimeter() f64 { return 2 * math.pi * c.radius }

struct Rect {
    width f64
    height f64
}

fn (r Rect) area() f64      { return r.width * r.height }
fn (r Rect) perimeter() f64 { return 2 * (r.width + r.height) }

fn print_shape(s Shape) {
    println('area: ${s.area():.2f}')
}

print_shape(Circle{ radius: 5.0 })
print_shape(Rect{ width: 3.0, height: 4.0 })
```

# CONCURRENCY
```v
import sync

fn worker(id int, wg &sync.WaitGroup) {
    defer wg.done()
    println('Worker $id started')
    // do work...
    println('Worker $id done')
}

fn main() {
    mut wg := sync.new_wait_group()
    for i in 0..5 {
        wg.add(1)
        go worker(i, &wg)
    }
    wg.wait()
    println('All workers done')
}

// Channels
ch := chan int{cap: 10}

go fn() {
    for i in 0..5 { ch <- i }
    ch.close()
}()

for val in ch {
    println(val)
}
```

# VWEB (WEB FRAMEWORK)
```v
import vweb

struct App {
    vweb.Context
}

pub fn (mut app App) index() vweb.Result {
    return app.json('{"message": "Hello, V!"}')
}

pub fn (mut app App) user(id int) vweb.Result {
    return app.text('User: $id')
}

fn main() {
    vweb.run(&App{}, 8080)
}
```

# C INTEROP
```v
#include <math.h>

fn C.sqrt(x f64) f64
fn C.pow(x f64, y f64) f64

fn hypotenuse(a f64, b f64) f64 {
    return C.sqrt(C.pow(a, 2) + C.pow(b, 2))
}
```

# V PACKAGE MANAGER
```bash
v new myproject         # scaffold project
v install username.pkg  # install package from VPM
v run main.v            # run
v build main.v          # compile
v test .                # run all tests
v fmt .                 # format code
v doc .                 # generate docs
```

# QUICK WINS CHECKLIST
```
[ ] Use mut only when mutation is actually needed
[ ] Use ? (Option) for absence, ! (Result) for failure
[ ] Use or {} to handle Option/Result at the call site
[ ] Prefer it shorthand in .map() and .filter() for single-arg lambdas
[ ] Use defer for cleanup — runs at end of scope
[ ] Use $if os == 'windows' {} for conditional compilation
[ ] Run v fmt . before committing — idiomatic style enforced
[ ] Use -prod flag for release builds (v -prod build main.v)
[ ] Use shared keyword sparingly — prefer channels for concurrent state
[ ] Translate C headers automatically: v translate header.h
```
