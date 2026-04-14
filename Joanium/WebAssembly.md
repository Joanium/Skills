---
name: WebAssembly
trigger: WebAssembly, WASM, WAT, Emscripten, wasm-pack, wasi, wasm module, wasm memory, wasm imports, wasm exports, AssemblyScript, Rust to WASM, C to WASM, linear memory, wasm-bindgen, wasmtime, WASI, component model
description: Compile and run WebAssembly modules from Rust, C/C++, and other languages. Covers WAT syntax, linear memory, JS↔WASM interop, wasm-pack, Emscripten, WASI for server-side WASM, performance optimization, and the component model.
---

# ROLE
You are a WebAssembly engineer. You compile high-performance code from native languages to WASM, bridge it with JavaScript, and deploy it in browsers and on servers. You know that WASM is not always faster — you profile, you don't assume.

# CORE PRINCIPLES
```
WASM IS NOT MAGIC SPEED — it's predictable performance; profile against your JS baseline
MEMORY IS EXPLICIT — no GC; linear memory with manual layout; shared with JS
INTEROP HAS COST — every JS↔WASM call has overhead; batch your calls
WASM IS SANDBOXED — no DOM, no I/O; everything comes through imports
WASI IS WASM FOR SERVERS — standardized system interface; portable binaries
COMPONENT MODEL IS THE FUTURE — typed, composable WASM modules with interface types
```

# WEBASSEMBLY TEXT FORMAT (WAT)

## Module Anatomy
```wat
(module
  ;; Import from JavaScript
  (import "env" "log_int" (func $log_int (param i32)))
  (import "env" "memory" (memory 1))  ;; or declare own memory

  ;; Declare linear memory (grows in 64KB pages)
  (memory (export "memory") 1)  ;; 1 page = 64KB minimum

  ;; Global variable
  (global $counter (mut i32) (i32.const 0))

  ;; Function: add two i32s
  (func $add (export "add") (param $a i32) (param $b i32) (result i32)
    local.get $a
    local.get $b
    i32.add         ;; stack-based: pops a and b, pushes a+b
  )

  ;; Function: fibonacci
  (func $fib (export "fib") (param $n i32) (result i32)
    (if (result i32) (i32.le_s (local.get $n) (i32.const 1))
      (then (local.get $n))
      (else
        (i32.add
          (call $fib (i32.sub (local.get $n) (i32.const 1)))
          (call $fib (i32.sub (local.get $n) (i32.const 2)))
        )
      )
    )
  )

  ;; Memory write: store bytes at offset 0
  (func $write_hello (export "write_hello")
    (i32.store8 (i32.const 0) (i32.const 72))  ;; 'H'
    (i32.store8 (i32.const 1) (i32.const 101)) ;; 'e'
    (i32.store8 (i32.const 2) (i32.const 108)) ;; 'l'
    (i32.store8 (i32.const 3) (i32.const 108)) ;; 'l'
    (i32.store8 (i32.const 4) (i32.const 111)) ;; 'o'
  )
)
```

## WAT Data Types
```wat
;; WASM has exactly 4 numeric types:
;; i32 — 32-bit integer (most common; also used for booleans and pointers)
;; i64 — 64-bit integer
;; f32 — 32-bit float
;; f64 — 64-bit float
;; v128 — SIMD vector (128-bit)

;; Integers: no sign distinction in type — operations are signed or unsigned
i32.add         ;; unsigned/signed same result (two's complement)
i32.div_s       ;; signed division
i32.div_u       ;; unsigned division
i32.lt_s        ;; signed less-than
i32.lt_u        ;; unsigned less-than

;; Memory operations use byte offsets:
(i32.load  (i32.const 100))        ;; load 4 bytes from address 100
(i32.store (i32.const 100) (i32.const 42)) ;; store 42 at address 100
(i32.load8_u (i32.const 0))        ;; load 1 byte, zero-extend to i32
```

# RUST → WASM

## Setup
```bash
# Install target
rustup target add wasm32-unknown-unknown

# Install wasm-pack (for JS integration)
cargo install wasm-pack

# Create library crate
cargo new --lib mylib
```

## Rust WASM Library
```rust
// src/lib.rs
use wasm_bindgen::prelude::*;

// Export function to JavaScript
#[wasm_bindgen]
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

// Import function from JavaScript
#[wasm_bindgen]
extern "C" {
    #[wasm_bindgen(js_namespace = console)]
    fn log(s: &str);
}

// Use JS types (strings, objects)
#[wasm_bindgen]
pub fn greet(name: &str) -> String {
    log(&format!("Hello from Rust, {}!", name));
    format!("Hello, {}!", name)
}

// Work with complex types via serde
use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize)]
pub struct Point { pub x: f64, pub y: f64 }

#[wasm_bindgen]
pub fn transform_points(points_json: &str) -> String {
    let points: Vec<Point> = serde_json::from_str(points_json).unwrap();
    let transformed: Vec<Point> = points.iter()
        .map(|p| Point { x: p.x * 2.0, y: p.y * 2.0 })
        .collect();
    serde_json::to_string(&transformed).unwrap()
}
```

## Cargo.toml
```toml
[package]
name = "mylib"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]  # required for wasm

[dependencies]
wasm-bindgen = "0.2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"

[profile.release]
opt-level = 3     # maximum optimization
lto = true        # link-time optimization (significant size reduction)
```

## Build and Use
```bash
# Build for web (outputs pkg/ directory with JS bindings)
wasm-pack build --target web

# Or for bundlers (webpack/vite/rollup)
wasm-pack build --target bundler
```

```javascript
// Import WASM module (ES module)
import init, { add, greet } from './pkg/mylib.js';

async function main() {
  await init();  // initialize WASM (fetches and compiles .wasm file)
  
  console.log(add(2, 3));        // 5
  console.log(greet("World"));   // "Hello, World!"
}
main();
```

# C/C++ → WASM WITH EMSCRIPTEN

## Compile C to WASM
```bash
# Install Emscripten SDK
git clone https://github.com/emscripten-core/emsdk.git
./emsdk install latest && ./emsdk activate latest
source ./emsdk_env.sh

# Compile C file
emcc compute.c -O3 \
  -s WASM=1 \
  -s EXPORTED_FUNCTIONS='["_compute", "_malloc", "_free"]' \
  -s EXPORTED_RUNTIME_METHODS='["ccall", "cwrap"]' \
  -o compute.js      # generates compute.js + compute.wasm
```

```javascript
// Use Emscripten-compiled module
const Module = await createModule();  // loads compute.js

// Call exported C function: int compute(int a, int b)
const compute = Module.cwrap('compute', 'number', ['number', 'number']);
console.log(compute(10, 20));

// Pass arrays to C (via WASM linear memory)
const n = 1000;
const ptr = Module._malloc(n * 4);   // allocate n * sizeof(float)
const arr = new Float32Array(Module.HEAPF32.buffer, ptr, n);
arr.set([1.0, 2.0, 3.0]);            // write data
Module._process_array(ptr, n);       // C processes it in-place
console.log(arr[0]);                 // read result
Module._free(ptr);
```

# JS ↔ WASM MEMORY INTEROP

## Reading/Writing WASM Linear Memory
```javascript
// After loading a WASM module manually (not via wasm-pack):
const memory = instance.exports.memory;  // WebAssembly.Memory

// Views into memory — these are LIVE views (no copying)
const bytes   = new Uint8Array(memory.buffer);
const int32s  = new Int32Array(memory.buffer);
const float64 = new Float64Array(memory.buffer);

// Write a string into WASM memory at offset 100
const encoder = new TextEncoder();
const encoded = encoder.encode("Hello\0");
bytes.set(encoded, 100);  // write at address 100

// Read a string from WASM memory (null-terminated)
function readString(memory, ptr) {
  const bytes = new Uint8Array(memory.buffer);
  let end = ptr;
  while (bytes[end] !== 0) end++;
  return new TextDecoder().decode(bytes.slice(ptr, end));
}

// IMPORTANT: memory.buffer becomes detached if WASM grows memory
// Always re-derive views after any call that might grow memory
function getView(memory) {
  return new Uint8Array(memory.buffer);  // always fresh
}
```

# WASI — SERVER-SIDE WASM

## Running WASM on the Server
```rust
// WASI program: file I/O, stdout, env vars — portable binary
use std::fs;
use std::io::Write;

fn main() {
    let content = fs::read_to_string("/data/input.txt").unwrap();
    let processed = content.to_uppercase();
    
    let mut out = fs::File::create("/data/output.txt").unwrap();
    out.write_all(processed.as_bytes()).unwrap();
    
    println!("Processed {} bytes", processed.len());
}
```

```bash
# Compile for WASI
rustup target add wasm32-wasip1
cargo build --target wasm32-wasip1 --release

# Run with wasmtime (outside browser)
wasmtime --dir /data ./target/wasm32-wasip1/release/myapp.wasm

# Or with Deno (supports WASI)
deno run --allow-read --allow-write run_wasm.ts
```

# PERFORMANCE GUIDE
```
WASM FASTER THAN JS FOR:
  ✓ Tight numeric loops (no JIT warm-up variability)
  ✓ Predictable memory layout (no GC pauses)
  ✓ Porting existing C/Rust libraries (no rewrite)
  ✓ CPU-intensive algorithms > 100ms of computation

WASM NOT NECESSARILY FASTER FOR:
  ✗ DOM manipulation (must go through JS anyway)
  ✗ Simple functions called once (load overhead)
  ✗ Anything I/O bound
  ✗ Code that's already fast in JIT-optimized JS

OPTIMIZATION TIPS:
  1. Minimize JS↔WASM calls; batch operations
  2. Use shared ArrayBuffer for large data (avoid copying)
  3. Enable SIMD: rustc flag -C target-feature=+simd128
  4. Optimize binary size: wasm-opt -O3 (Binaryen)
  5. Use streaming compilation: WebAssembly.instantiateStreaming()
     not WebAssembly.instantiate() (avoids buffering entire .wasm)
  6. Compress .wasm files: gzip or brotli (typically 50–60% smaller)

PROFILING:
  Chrome DevTools → Performance → enable WASM debugging
  Firefox has WebAssembly profiler in DevTools
  wasmer-profiler for server-side
```
