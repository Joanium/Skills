---
name: Zig
trigger: zig, ziglang, .zig, zig programming, zig language, zig build, zig compiler, comptime
description: Write idiomatic, safe, low-level Zig code. Covers syntax, comptime, error handling, allocators, build system, C interop, and memory safety without GC.
---

# ROLE
You are a Zig language expert. Zig is a general-purpose systems programming language and toolchain designed for robustness, optimality, and maintainability. No hidden control flow, no hidden allocations, no macros — just explicit, auditable code.

# CORE PHILOSOPHY
```
NO HIDDEN CONTROL FLOW — no exceptions; errors are values
NO HIDDEN ALLOCATIONS — every allocation is explicit with an allocator
COMPTIME IS METAPROGRAMMING — compile-time execution replaces macros
C INTEROP IS FIRST CLASS — import and use C headers directly
ONE CANONICAL WAY — the language is small; idioms are consistent
```

# SYNTAX ESSENTIALS

## Variables
```zig
const std = @import("std");

pub fn main() void {
    const x: i32 = 42;        // immutable, must be known at comptime or runtime
    var y: i32 = 10;          // mutable
    y += x;

    const name = "Joel";      // string literal — type is *const [4:0]u8
    _ = name;                 // prefix unused vars with _ to silence compiler
}
```

## Functions
```zig
// Basic function
fn add(a: i32, b: i32) i32 {
    return a + b;
}

// Void return
fn log(msg: []const u8) void {
    std.debug.print("{s}\n", .{msg});
}

// Optional return
fn findIndex(haystack: []const u8, needle: u8) ?usize {
    for (haystack, 0..) |c, i| {
        if (c == needle) return i;
    }
    return null;
}
```

# ERROR HANDLING — THE ZIG WAY
```zig
// Errors are values, not exceptions
const FileError = error{
    NotFound,
    PermissionDenied,
    OutOfMemory,
};

fn readFile(path: []const u8) FileError![]u8 {
    // ! means: returns FileError or []u8
    _ = path;
    return FileError.NotFound;
}

// try — propagates error up (like ? in Rust)
fn process(path: []const u8) !void {
    const data = try readFile(path);  // returns error to caller if err
    _ = data;
}

// catch — handle at call site
fn safeRead(path: []const u8) []u8 {
    return readFile(path) catch |err| {
        std.debug.print("Error: {}\n", .{err});
        return "";
    };
}

// errdefer — cleanup on error path only
fn openAndProcess(path: []const u8) !void {
    const file = try std.fs.cwd().openFile(path, .{});
    errdefer file.close();    // runs ONLY if function returns error
    defer file.close();       // runs always — prefer defer for normal cleanup
    // ...
}
```

# COMPTIME — COMPILE-TIME EXECUTION
```zig
// Comptime replaces generics, macros, and templates

// Generic function via comptime type
fn max(comptime T: type, a: T, b: T) T {
    return if (a > b) a else b;
}

const result = max(i32, 10, 20);   // T resolved at compile time
const fmax  = max(f64, 1.5, 2.5);

// Comptime block — evaluated at compile time
const BUFFER_SIZE = comptime blk: {
    const base = 1024;
    break :blk base * 4;
};

// Type introspection at comptime
fn printTypeInfo(comptime T: type) void {
    const info = @typeInfo(T);
    switch (info) {
        .Int => |i| std.debug.print("int: bits={}, signed={}\n", .{i.bits, i.signedness == .signed}),
        .Float => |f| std.debug.print("float: bits={}\n", .{f.bits}),
        else => std.debug.print("other type\n", .{}),
    }
}
```

# ALLOCATORS — EXPLICIT MEMORY
```zig
const std = @import("std");

pub fn main() !void {
    // General purpose allocator — detects leaks in debug mode
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    // Allocate a slice
    const buf = try allocator.alloc(u8, 256);
    defer allocator.free(buf);

    // Arena allocator — free everything at once
    var arena = std.heap.ArenaAllocator.init(allocator);
    defer arena.deinit();    // frees all arena allocations at once
    const aalloc = arena.allocator();

    const arr = try aalloc.alloc(i32, 100);
    _ = arr;   // freed when arena.deinit() is called

    // Stack allocator for small, fixed-size buffers
    var buf2: [1024]u8 = undefined;
    var fba = std.heap.FixedBufferAllocator.init(&buf2);
    const stack_alloc = fba.allocator();
    _ = stack_alloc;
}
```

# STRUCTS AND METHODS
```zig
const Vec2 = struct {
    x: f32,
    y: f32,

    // Method — first param is self
    pub fn length(self: Vec2) f32 {
        return @sqrt(self.x * self.x + self.y * self.y);
    }

    pub fn add(self: Vec2, other: Vec2) Vec2 {
        return .{ .x = self.x + other.x, .y = self.y + other.y };
    }
};

const v1 = Vec2{ .x = 3.0, .y = 4.0 };
const v2 = Vec2{ .x = 1.0, .y = 2.0 };
const v3 = v1.add(v2);
std.debug.print("length={d}\n", .{v3.length()});
```

# TAGGED UNIONS (SUM TYPES)
```zig
const Shape = union(enum) {
    circle: f32,            // radius
    rectangle: struct { w: f32, h: f32 },
    point,

    pub fn area(self: Shape) f32 {
        return switch (self) {
            .circle  => |r| std.math.pi * r * r,
            .rectangle => |s| s.w * s.h,
            .point   => 0,
        };
    }
};

const s = Shape{ .circle = 5.0 };
std.debug.print("area={d}\n", .{s.area()});
```

# C INTEROP
```zig
// Direct C header import — no bindings needed
const c = @cImport({
    @cInclude("stdio.h");
    @cInclude("stdlib.h");
});

pub fn main() void {
    _ = c.printf("Hello from C!\n");
    const ptr = c.malloc(256);
    defer c.free(ptr);
}

// build.zig — link C library
// exe.linkSystemLibrary("z");  // links libz
// exe.linkLibC();
```

# BUILD SYSTEM (build.zig)
```zig
const std = @import("std");

pub fn build(b: *std.Build) void {
    const target   = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const exe = b.addExecutable(.{
        .name = "myapp",
        .root_source_file = b.path("src/main.zig"),
        .target = target,
        .optimize = optimize,
    });
    b.installArtifact(exe);

    const run_cmd = b.addRunArtifact(exe);
    const run_step = b.step("run", "Run the app");
    run_step.dependOn(&run_cmd.step);

    const unit_tests = b.addTest(.{
        .root_source_file = b.path("src/main.zig"),
        .target = target,
        .optimize = optimize,
    });
    const test_step = b.step("test", "Run tests");
    test_step.dependOn(&b.addRunArtifact(unit_tests).step);
}
```

# TESTING
```zig
const testing = std.testing;

fn fibonacci(n: u32) u32 {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

test "fibonacci" {
    try testing.expectEqual(@as(u32, 0), fibonacci(0));
    try testing.expectEqual(@as(u32, 1), fibonacci(1));
    try testing.expectEqual(@as(u32, 8), fibonacci(6));
}

// run: zig test src/main.zig
```

# QUICK WINS CHECKLIST
```
[ ] Always use defer for cleanup — never forget to free/close
[ ] Use errdefer for error-path-only cleanup
[ ] Start with GeneralPurposeAllocator in debug to catch leaks
[ ] Use ArenaAllocator for request-scoped allocations (web handlers, parsers)
[ ] Prefer comptime parameters over runtime polymorphism where possible
[ ] Mark unused variables with _ = varname to satisfy compiler
[ ] Use @import("std").testing for unit tests inside source files
[ ] Use zig build instead of zig run for multi-file projects
[ ] Use ?T for nullable values — never raw null pointers
[ ] Cross-compile: zig build -Dtarget=x86_64-windows-gnu
```
