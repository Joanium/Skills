---
name: Crystal
trigger: crystal, crystal-lang, .cr, crystal programming, crystal language, shards, crystal compiler
description: Write idiomatic, type-safe Crystal code. Covers Ruby-like syntax, static typing, macros, fibers, channels, HTTP servers, and the Shards package manager.
---

# ROLE
You are a Crystal language expert. Crystal is a statically typed, compiled language with Ruby-like syntax that achieves near-C performance. It has type inference so strong that code often looks dynamic but is fully type-checked at compile time.

# CORE PHILOSOPHY
```
RUBY SYNTAX — familiar, expressive, readable
STATIC TYPES — zero runtime type errors; caught at compile time
FAST AS C — compiles to native via LLVM
CONCURRENCY VIA CSP — fibers + channels, not threads
NILABLE BY DEFAULT — Nil is a first-class type, not a hidden bug
```

# SYNTAX ESSENTIALS

## Variables and Types
```crystal
# Type inference — rarely need annotations
name = "Joel"           # String
age  = 22               # Int32
pi   = 3.14             # Float64

# Explicit type annotation
score : Float64 = 0.0

# Nilable types — T? is shorthand for T | Nil
user : String? = nil
user = "Joel"

# Constants
MAX = 100
```

## Methods
```crystal
def greet(name : String) : String
  "Hello, #{name}!"
end

# Optional parameter
def connect(host : String, port : Int32 = 8080)
  "#{host}:#{port}"
end

# Splat / variadic
def sum(*nums : Int32) : Int32
  nums.sum
end

# Block parameter (yield)
def repeat(n : Int32, &block)
  n.times { block.call }
end

repeat(3) { puts "hi" }
```

## Classes and Modules
```crystal
class Animal
  getter name : String
  getter age  : Int32

  def initialize(@name : String, @age : Int32)
  end

  def speak : String
    "..."
  end
end

class Dog < Animal
  getter breed : String

  def initialize(name : String, age : Int32, @breed : String)
    super(name, age)
  end

  def speak : String
    "#{name} says: Woof!"
  end
end

# Module for mixins
module Serializable
  def to_json_string : String
    # ... implement
    "{}"
  end
end

class Dog < Animal
  include Serializable
end
```

## Structs (Value Types)
```crystal
struct Point
  getter x : Float64
  getter y : Float64

  def initialize(@x : Float64, @y : Float64)
  end

  def distance_to(other : Point) : Float64
    Math.sqrt((x - other.x) ** 2 + (y - other.y) ** 2)
  end
end

# Structs are stack-allocated, copied on assignment
p1 = Point.new(0.0, 0.0)
p2 = Point.new(3.0, 4.0)
puts p1.distance_to(p2)  # 5.0
```

# TYPE SYSTEM

## Union Types
```crystal
# A variable can hold multiple types
value : Int32 | String = 42
value = "hello"     # valid

# Type narrowing
case value
when Int32  then puts "number: #{value}"
when String then puts "string: #{value}"
end

# Nil safety
def process(name : String?)
  if name
    puts name.upcase  # name is String here, not String?
  else
    puts "no name"
  end
end
```

## Generics
```crystal
class Stack(T)
  def initialize
    @data = Array(T).new
  end

  def push(item : T)
    @data << item
  end

  def pop : T?
    @data.pop?
  end

  def size : Int32
    @data.size
  end
end

stack = Stack(Int32).new
stack.push(1)
stack.push(2)
puts stack.pop  # 2
```

# MACROS
```crystal
# Macros run at compile time and generate code
macro define_getters(*names)
  {% for name in names %}
    def {{name.id}}
      @{{name.id}}
    end
  {% end %}
end

class Person
  define_getters :name, :email, :age

  def initialize(@name : String, @email : String, @age : Int32)
  end
end

# Built-in macros
puts {{ __FILE__ }}     # current file path
puts {{ __LINE__ }}     # current line number
puts {{ @type }}        # current type name
```

# CONCURRENCY — FIBERS AND CHANNELS
```crystal
require "fiber"

# Fibers are lightweight coroutines
fiber = Fiber.new do
  puts "Fiber start"
  Fiber.yield
  puts "Fiber resumed"
end

fiber.resume
fiber.resume

# Channels — CSP style concurrency
channel = Channel(String).new

spawn do
  # runs in a fiber
  sleep 1.second
  channel.send "hello from fiber"
end

msg = channel.receive
puts msg   # hello from fiber

# Select on multiple channels
ch1 = Channel(Int32).new
ch2 = Channel(String).new

spawn { ch1.send 42 }
spawn { ch2.send "hi" }

select
when n = ch1.receive
  puts "got int: #{n}"
when s = ch2.receive
  puts "got string: #{s}"
end
```

# HTTP SERVER
```crystal
require "http/server"

server = HTTP::Server.new do |ctx|
  case {ctx.request.method, ctx.request.path}
  when {"GET", "/"}
    ctx.response.content_type = "application/json"
    ctx.response.print %({"message": "Hello, Crystal!"})
  when {"GET", %r{^/user/(\w+)}}
    name = $~[1]
    ctx.response.print "User: #{name}"
  else
    ctx.response.status = HTTP::Status::NOT_FOUND
    ctx.response.print "Not Found"
  end
end

address = server.bind_tcp("0.0.0.0", 8080)
puts "Listening on http://#{address}"
server.listen
```

# SHARDS (PACKAGE MANAGER)
```yaml
# shard.yml
name: myapp
version: 0.1.0

dependencies:
  kemal:
    github: kemalcr/kemal
    version: "~> 1.5"
  jennifer:
    github: imdrasil/jennifer.cr
```

```bash
shards install          # install dependencies
shards build            # build project
shards build --release  # optimized release build
crystal run src/app.cr  # run directly
crystal spec            # run tests
```

# TESTING
```crystal
require "spec"

describe "String" do
  describe "#upcase" do
    it "converts to uppercase" do
      "hello".upcase.should eq "HELLO"
    end

    it "handles empty string" do
      "".upcase.should eq ""
    end
  end
end

describe Array do
  it "supports generics" do
    arr = [1, 2, 3]
    arr.sum.should eq 6
    arr.size.should eq 3
  end
end
```

# QUICK WINS CHECKLIST
```
[ ] Use T? for nilable types — Crystal forces you to handle nil
[ ] Use getter/setter/property macros instead of manual accessor methods
[ ] Prefer structs over classes for small, immutable value objects
[ ] Use spawn + Channel for concurrent work — avoid shared mutable state
[ ] Use case/when for type narrowing — compiler tracks types in each branch
[ ] Compile with --release for production builds
[ ] Use crystal tool format to auto-format code
[ ] crystal spec runs all files in spec/ directory
[ ] Use @[AlwaysInline] annotation on hot small methods
[ ] Use Array(T), Hash(K, V) syntax for typed collections
```
