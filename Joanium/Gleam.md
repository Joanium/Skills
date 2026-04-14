---
name: Gleam
trigger: gleam, gleam-lang, .gleam, gleam programming, gleam language, gleam on erlang, gleam beam
description: Write type-safe, functional Gleam code for the BEAM VM. Covers syntax, types, pattern matching, pipelines, OTP integration, error handling, and the Gleam package ecosystem.
---

# ROLE
You are a Gleam language expert. Gleam is a statically typed functional language that compiles to Erlang and runs on the BEAM VM — the same runtime as Erlang and Elixir. It brings ML-family type safety to the most battle-tested distributed systems runtime in existence.

# CORE PHILOSOPHY
```
TYPE SAFE ON BEAM — full type inference, zero runtime type errors
NO NULL, NO EXCEPTIONS — Result and Option types encode failure
PIPELINES EVERYWHERE — |> operator makes data flow readable
ERLANG INTEROP — call any Erlang/Elixir library directly
SMALL SURFACE AREA — fewer concepts, fewer surprises
```

# SYNTAX ESSENTIALS

## Variables and Functions
```gleam
// Let bindings are immutable
let name = "Joel"
let age = 22
let pi = 3.14159

// Functions
pub fn greet(name: String) -> String {
  "Hello, " <> name <> "!"
}

// Multiple arguments
pub fn add(a: Int, b: Int) -> Int {
  a + b
}

// Anonymous functions (closures)
let double = fn(x) { x * 2 }
let doubled = double(5)   // 10

// Shorthand with use (similar to do-notation)
```

## Types
```gleam
// Custom types — the core of Gleam data modeling
pub type Color {
  Red
  Green
  Blue
  Rgb(Int, Int, Int)       // with fields
}

pub type User {
  User(name: String, age: Int, email: String)
}

// Alias
pub type UserId = Int

// Generic type
pub type Maybe(a) {
  Just(a)
  Nothing
}
```

## Pattern Matching
```gleam
pub fn describe_color(c: Color) -> String {
  case c {
    Red        -> "pure red"
    Green      -> "pure green"
    Blue       -> "pure blue"
    Rgb(r, g, b) -> "rgb(" <> int.to_string(r) <> "," <> int.to_string(g) <> "," <> int.to_string(b) <> ")"
  }
}

// Pattern match on tuples
pub fn classify(pair: #(Int, Int)) -> String {
  case pair {
    #(0, 0)     -> "origin"
    #(x, 0)     -> "x-axis at " <> int.to_string(x)
    #(0, y)     -> "y-axis at " <> int.to_string(y)
    #(x, y)     -> "point"
  }
}

// Guards
pub fn grade(score: Int) -> String {
  case score {
    s if s >= 90 -> "A"
    s if s >= 80 -> "B"
    s if s >= 70 -> "C"
    _            -> "F"
  }
}
```

# ERROR HANDLING

## Result Type
```gleam
import gleam/result

// Result(ok_type, error_type)
pub type ParseError {
  InvalidFormat
  OutOfRange(Int)
}

pub fn parse_age(s: String) -> Result(Int, ParseError) {
  case int.parse(s) {
    Ok(n) if n >= 0 && n <= 150 -> Ok(n)
    Ok(n)  -> Error(OutOfRange(n))
    Error(_) -> Error(InvalidFormat)
  }
}

// Chaining with result.try
pub fn process(input: String) -> Result(String, ParseError) {
  use age <- result.try(parse_age(input))
  Ok("Age is: " <> int.to_string(age))
}

// map and map_error
let doubled = result.map(Ok(5), fn(x) { x * 2 })     // Ok(10)
let fallback = result.unwrap(Error("oops"), 0)         // 0
```

## Option via stdlib
```gleam
import gleam/option.{Option, Some, None}

pub fn find_user(id: Int) -> Option(String) {
  case id {
    1 -> Some("Joel")
    _ -> None
  }
}

let name = option.unwrap(find_user(1), "Unknown")   // "Joel"
let upper = option.map(find_user(1), string.uppercase)  // Some("JOEL")
```

# PIPELINES
```gleam
import gleam/list
import gleam/string

// |> pipes the left value as the first argument of the right function
pub fn process_names(names: List(String)) -> List(String) {
  names
  |> list.filter(fn(n) { string.length(n) > 3 })
  |> list.map(string.uppercase)
  |> list.sort(string.compare)
}

// Before/after comparison
// Without pipes:
list.sort(list.map(list.filter(names, fn(n) { string.length(n) > 3 }), string.uppercase), string.compare)

// With pipes: much more readable ↑
```

# RECORDS AND UPDATES
```gleam
pub type Config {
  Config(
    host: String,
    port: Int,
    debug: Bool,
  )
}

let default_config = Config(host: "localhost", port: 8080, debug: False)

// Record update syntax — immutable, creates new record
let prod_config = Config(..default_config, host: "example.com", debug: False)
let dev_config  = Config(..default_config, debug: True)
```

# LISTS AND STDLIB
```gleam
import gleam/list
import gleam/int
import gleam/string

// List operations
let nums = [1, 2, 3, 4, 5]
let doubled   = list.map(nums, fn(x) { x * 2 })          // [2,4,6,8,10]
let evens     = list.filter(nums, fn(x) { x % 2 == 0 })  // [2,4]
let total     = list.fold(nums, 0, int.add)               // 15
let first     = list.first(nums)                          // Ok(1)
let flattened = list.flatten([[1,2], [3,4]])              // [1,2,3,4]

// Pattern matching on list
pub fn sum(nums: List(Int)) -> Int {
  case nums {
    []           -> 0
    [head, ..tail] -> head + sum(tail)
  }
}
```

# OTP / ERLANG INTEROP
```gleam
// Call Erlang functions directly
@external(erlang, "erlang", "system_time")
pub fn system_time(unit: atom) -> Int

// Use Erlang processes via gleam_erlang
import gleam/erlang/process

pub fn spawn_worker(msg: String) {
  process.start(fn() {
    // this runs in a separate BEAM process
    io.println("Worker got: " <> msg)
  }, True)
}
```

# GLEAM PACKAGE MANAGER
```bash
gleam new myproject         # scaffold new project
gleam add gleam_http        # add dependency
gleam build                 # compile
gleam run                   # compile and run
gleam test                  # run tests
gleam format                # auto-format
gleam docs build            # generate docs
```

```toml
# gleam.toml
name = "myapp"
version = "1.0.0"

[dependencies]
gleam_stdlib    = ">= 0.34.0 and < 2.0.0"
gleam_http      = ">= 3.6.0 and < 4.0.0"
gleam_json      = ">= 1.0.0 and < 2.0.0"
wisp            = ">= 0.13.0 and < 1.0.0"    # web framework
```

# TESTING
```gleam
import gleeunit
import gleeunit/should

pub fn main() {
  gleeunit.main()
}

pub fn add_test() {
  add(1, 2)
  |> should.equal(3)
}

pub fn pipeline_test() {
  [1, 2, 3]
  |> list.map(fn(x) { x * 2 })
  |> should.equal([2, 4, 6])
}
```

# QUICK WINS CHECKLIST
```
[ ] Use Result(ok, err) for ALL fallible operations — no exceptions
[ ] Use |> pipelines to keep data transformation readable
[ ] Pattern match exhaustively — compiler errors on missing cases
[ ] Prefer let with use for chaining Results (avoid nested case)
[ ] Name custom error types descriptively (e.g. UserNotFound, InvalidEmail)
[ ] Use record update syntax (Config(..base, field: value)) for config variants
[ ] gleam format in CI — enforce consistent style
[ ] Use the gleam_stdlib list/string/result modules before writing your own
[ ] Mark public API with pub — unexported = internal by default
[ ] Target JavaScript with gleam build --target javascript for frontend use
```
