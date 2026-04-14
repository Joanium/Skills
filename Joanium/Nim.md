---
name: Nim
trigger: nim, nimble, .nim, nimlang, nim programming, nim language, nim compiler, nim script, nimscript
description: Write idiomatic, high-performance Nim code. Covers syntax, type system, macros, metaprogramming, memory management, async, FFI, and the Nimble package manager.
---

# ROLE
You are a Nim language expert. Nim is a statically typed, compiled systems programming language that combines the performance of C, the expressiveness of Python, and powerful metaprogramming via macros. You write clean, idiomatic Nim that compiles to efficient C/C++/JS backends.

# CORE PHILOSOPHY
```
EFFICIENT BY DEFAULT — Nim compiles to C and inherits its speed
EXPRESSIVE SYNTAX — Python-like indentation, no boilerplate
METAPROGRAMMING FIRST — macros are hygienic, typed, and compile-time
MEMORY FLEXIBLE — GC by default, manual or ARC/ORC available
MULTI-BACKEND — compile to C, C++, JavaScript, or WASM
```

# SYNTAX ESSENTIALS

## Variables and Types
```nim
# Immutable by default — use let
let name = "Joel"
let age: int = 22

# Mutable — use var
var counter = 0
counter += 1

# Constants — compile-time evaluated
const MAX_SIZE = 1024
const PI = 3.14159

# Type inference is strong — rarely need explicit types
let items = @[1, 2, 3]       # seq[int]
let table = {"a": 1, "b": 2} # array of tuples → use toTable for Table
```

## Functions (Procs)
```nim
# Basic proc
proc greet(name: string): string =
  "Hello, " & name  # last expression is return value

# Multiple return via tuple
proc minMax(a, b: int): (int, int) =
  if a < b: (a, b) else (b, a)

let (lo, hi) = minMax(5, 3)

# Default arguments
proc connect(host: string, port: int = 8080, secure: bool = false): string =
  (if secure: "https" else: "http") & "://" & host & ":" & $port

# Variadic args
proc sum(nums: varargs[int]): int =
  for n in nums: result += n

# result is auto-initialized return variable
proc factorial(n: int): int =
  result = 1
  for i in 2..n: result *= i
```

## Object Types
```nim
type
  Animal = object of RootObj   # base type
    name: string
    age: int

  Dog = object of Animal       # inheritance
    breed: string

  Shape = ref object           # heap-allocated (reference type)
    x, y: float

# Constructor pattern
proc newDog(name, breed: string, age: int): Dog =
  Dog(name: name, age: age, breed: breed)

# Methods via proc on type
proc speak(d: Dog): string =
  d.name & " says: Woof!"

# Uniform Function Call Syntax (UFCS) — call as method
let rex = newDog("Rex", "Husky", 3)
echo rex.speak()
```

## Variants (Sum Types)
```nim
type
  TokenKind = enum
    tkInt, tkFloat, tkString, tkIdent

  Token = object
    case kind: TokenKind
    of tkInt:    intVal: int
    of tkFloat:  floatVal: float
    of tkString, tkIdent: strVal: string

# Pattern match with case
proc describe(tok: Token): string =
  case tok.kind
  of tkInt:    "int: " & $tok.intVal
  of tkFloat:  "float: " & $tok.floatVal
  of tkString: "string: " & tok.strVal
  of tkIdent:  "ident: " & tok.strVal
```

# METAPROGRAMMING

## Templates (Hygienic Inline Substitution)
```nim
# Template — zero-cost abstraction, no runtime overhead
template withOpen(path: string, mode: FileMode, body: untyped) =
  let f = open(path, mode)
  try:
    body
  finally:
    close(f)

withOpen("data.txt", fmRead):
  echo f.readAll()

# defer-style template
template defer(body: untyped) =
  try: discard
  finally: body
```

## Macros (Full AST Manipulation)
```nim
import macros

# Macro that generates getters for object fields
macro makeGetters(T: typedesc): untyped =
  result = newStmtList()
  let impl = T.getImpl
  for field in impl[2][2]:
    let fname = field[0]
    let ftype = field[1]
    result.add quote do:
      proc `fname`*(self: `T`): `ftype` = self.`fname`

type Point = object
  x, y: float

makeGetters(Point)
```

# MEMORY MANAGEMENT
```nim
# Default: refc (reference counting + cycle detection)
# Fast alternative: --mm:arc (deterministic, no GC pauses)
# Best for systems: --mm:none (manual only)

# Compile with ARC:
# nim c --mm:arc myapp.nim

# Move semantics with sink
proc consume(data: sink seq[int]) =
  # data is moved in, caller's copy is invalidated
  echo data.len

# Owned ref
let owned = new(int)   # ref int — GC managed
owned[] = 42
```

# ASYNC / AWAIT
```nim
import asyncdispatch, asyncnet

proc fetchPage(url: string): Future[string] {.async.} =
  let client = newAsyncHttpClient()
  result = await client.getContent(url)

proc main() {.async.} =
  let html = await fetchPage("http://example.com")
  echo html[0..100]

waitFor main()
```

# FFI — CALLING C
```nim
# Inline C declaration
proc printf(fmt: cstring): cint
  {.importc, varargs, header: "<stdio.h>".}

printf("Hello from C, %s!\n", "Nim")

# Link to a C library
{.passL: "-lm".}
proc sqrt(x: cdouble): cdouble {.importc: "sqrt", header: "<math.h>".}

echo sqrt(2.0)  # 1.4142...
```

# NIMBLE (PACKAGE MANAGER)
```
nimble init myproject       # scaffold new project
nimble install packagename  # install dependency
nimble build                # compile project
nimble test                 # run tests
nimble run                  # build and execute

# myproject.nimble
requires "nim >= 2.0.0"
requires "httpbeast >= 0.4.0"
task build, "Build the project":
  exec "nim c -d:release src/main.nim"
```

# COMPILATION FLAGS
```bash
nim c myapp.nim                         # debug build → C backend
nim c -d:release myapp.nim              # optimized release
nim c -d:release --opt:speed myapp.nim  # max speed
nim c --mm:arc -d:release myapp.nim     # ARC memory model
nim js myapp.nim                        # compile to JavaScript
nim c -r myapp.nim                      # compile and run immediately
```

# IDIOMS AND BEST PRACTICES
```nim
# Prefer result over explicit return
proc double(n: int): int =
  result = n * 2   # cleaner than return n * 2

# Use iterators for lazy sequences
iterator fibonacci(): int =
  var a, b = 0, 1
  while true:
    yield a
    (a, b) = (b, a + b)

for n in fibonacci():
  if n > 100: break
  echo n

# String formatting with &
import strformat
let msg = &"Hello {name}, you are {age} years old"

# Nil safety: use Option[T]
import options
proc findUser(id: int): Option[string] =
  if id == 1: some("Joel") else: none(string)

let user = findUser(1)
if user.isSome: echo user.get()
```

# QUICK WINS CHECKLIST
```
[ ] Use let over var whenever value won't change
[ ] Prefer ARC (--mm:arc) for low-latency or systems code
[ ] Use strformat (&"...") for string interpolation
[ ] Use result variable instead of explicit return
[ ] Mark side-effect-free procs with {.noSideEffect.} or func keyword
[ ] Use Option[T] instead of nil for optional values
[ ] Run nim check before nim c to catch type errors fast
[ ] Use nimble tasks for build automation
[ ] Prefer iterator over proc returning seq for large datasets
[ ] Use {.inline.} on hot small procs
```
