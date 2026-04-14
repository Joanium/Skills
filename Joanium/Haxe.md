---
name: Haxe
trigger: haxe, haxelang, .hx, haxe programming, haxe language, haxelib, openfl, heaps, haxe cross-platform
description: Write cross-platform Haxe code that compiles to JS, C++, Python, C#, Java, PHP, and more. Covers type system, macros, abstracts, targets, and major frameworks.
---

# ROLE
You are a Haxe language expert. Haxe is a high-level, strictly typed programming language with its own compiler that targets multiple platforms: JavaScript, C++, C#, Java, Python, PHP, Lua, and HashLink VM. One codebase, every platform.

# CORE PHILOSOPHY
```
WRITE ONCE, TARGET EVERYWHERE — one typed codebase for all platforms
POWERFUL TYPE SYSTEM — generics, abstracts, typedefs, structural typing
COMPILE-TIME MACROS — AST manipulation, code generation, type introspection
ZERO-COST ABSTRACTS — new types over existing ones with no runtime overhead
CONDITIONAL COMPILATION — #if target to manage platform specifics
```

# SYNTAX ESSENTIALS

## Variables and Types
```haxe
class Main {
    static function main() {
        // Type inference
        var name = "Joel";           // String
        var age  = 22;               // Int
        var pi   = 3.14;             // Float
        var flag = true;             // Bool

        // Explicit
        var score:Float = 0.0;

        // Final — immutable after assignment
        final MAX = 100;

        // Null safety (Haxe 4+)
        var nullable:Null<String> = null;
        var safe:String = "hello";   // non-nullable
    }
}
```

## Functions
```haxe
// Static method
static function add(a:Int, b:Int):Int {
    return a + b;
}

// Optional arguments
static function connect(host:String, ?port:Int, ?secure:Bool):String {
    var p = port ?? 8080;
    var s = secure ?? false;
    return (s ? "https" : "http") + "://" + host + ":" + p;
}

// Arrow functions
var double = (x:Int) -> x * 2;
var nums = [1,2,3].map(x -> x * 2);   // [2,4,6]

// Rest args
static function sum(nums:haxe.Rest<Int>):Int {
    var total = 0;
    for (n in nums) total += n;
    return total;
}
```

## Classes
```haxe
class Animal {
    public var name:String;
    public var age:Int;
    private var _sound:String;

    public function new(name:String, age:Int, sound:String) {
        this.name = name;
        this.age = age;
        _sound = sound;
    }

    public function speak():String {
        return '$name says: $_sound';
    }
}

class Dog extends Animal {
    public var breed:String;

    public function new(name:String, age:Int, breed:String) {
        super(name, age, "Woof!");
        this.breed = breed;
    }

    override public function speak():String {
        return '${super.speak()} (${breed})';
    }
}
```

# TYPE SYSTEM

## Enums (Algebraic Data Types)
```haxe
enum Shape {
    Circle(radius:Float);
    Rectangle(width:Float, height:Float);
    Point;
}

function area(s:Shape):Float {
    return switch s {
        case Circle(r):          Math.PI * r * r;
        case Rectangle(w, h):   w * h;
        case Point:              0;
    }
}
```

## Abstracts — Zero-Cost Type Wrappers
```haxe
// Wrap Int as a type-safe ID
abstract UserId(Int) {
    public function new(v:Int) this = v;
    public function toInt():Int return this;

    // Implicit conversion from Int
    @:from static function fromInt(v:Int):UserId return new UserId(v);
    // Implicit conversion to String
    @:to public function toString():String return 'UserId($this)';
}

var id:UserId = 42;   // fromInt called automatically
trace(id);            // "UserId(42)"

// Enum abstract — type-safe string constants
enum abstract Status(String) to String {
    var Active   = "active";
    var Inactive = "inactive";
    var Pending  = "pending";
}

var s:Status = Active;
```

## Typedefs — Structural Types
```haxe
typedef Point = {
    var x:Float;
    var y:Float;
}

typedef Named = {
    var name:String;
}

// Extending typedef (structural intersection)
typedef NamedPoint = Point & Named;

function distance(a:Point, b:Point):Float {
    var dx = a.x - b.x;
    var dy = a.y - b.y;
    return Math.sqrt(dx*dx + dy*dy);
}

// Any object with x and y fields satisfies Point
distance({x: 0, y: 0}, {x: 3, y: 4});
```

## Generics
```haxe
class Stack<T> {
    private var items:Array<T> = [];

    public function push(item:T):Void items.push(item);
    public function pop():Null<T>    return items.pop();
    public function get size():Int   return items.length;
}

var stack = new Stack<Int>();
stack.push(1);
stack.push(2);
trace(stack.pop());   // 2
```

# MACROS
```haxe
import haxe.macro.Context;
import haxe.macro.Expr;

// Compile-time assertion
macro static function assert(cond:Expr):Expr {
    return macro {
        if (!$cond) throw "Assertion failed: " + $v{Std.string(cond)};
    };
}

// Build macro — generate fields at compile time
class Builder {
    public static macro function build():Array<Field> {
        var fields = Context.getBuildFields();
        // add or transform fields here
        return fields;
    }
}
```

# CONDITIONAL COMPILATION
```haxe
class Platform {
    public static function info():String {
        #if js
            return "Running in browser/Node.js";
        #elseif cpp
            return "Native C++ binary";
        #elseif cs
            return "C# / .NET";
        #elseif python
            return "Python";
        #else
            return "Other target";
        #end
    }
}

// Check for specific features
#if (haxe >= "4.0.0")
    // use Haxe 4 features
#end
```

# JAVASCRIPT TARGET
```haxe
// Main entry for JS target
class Main {
    static function main() {
        js.Browser.document.getElementById("app").innerHTML = "Hello!";
    }
}
// haxe -main Main -js output.js

// Using JS externs (type definitions for JS libs)
@:jsRequire("axios")
extern class Axios {
    static function get(url:String):js.lib.Promise<Dynamic>;
}
```

# HAXELIB (PACKAGE MANAGER)
```bash
haxelib install format          # install package
haxelib run formatter           # run a library tool
haxelib list                    # list installed libs
```

```xml
<!-- build.hxml — build config file -->
-main Main
-js www/app.js
-lib heaps
-lib hxassets
-D debug
```

# QUICK WINS CHECKLIST
```
[ ] Use final for values that won't change
[ ] Use enum with data (ADTs) over class hierarchies for variants
[ ] Use abstract to create type-safe wrappers over primitives
[ ] Use typedef for structural typing — duck-typed interfaces
[ ] Prefer ? (optional params) over overloads for simple defaults
[ ] Use @:enum abstract for type-safe string/int constants
[ ] Use #if target for platform-specific code — keep it minimal
[ ] Use haxe.macro.Context at compile time, never runtime
[ ] Define JS externs with extern class to type JS libraries
[ ] Use trace() for debug output — auto-stripped in release builds
```
