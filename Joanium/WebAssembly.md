---
name: WebAssembly (WASM) Integration
trigger: WebAssembly, WASM, wasm, Emscripten, WASI, AssemblyScript, Rust to WASM, compile to WebAssembly, WASM module, browser WASM, Node.js WASM, performance WASM, wasm-pack, wasmtime
description: Integrate WebAssembly into web and server applications. Covers compiling from Rust/C/AssemblyScript, JavaScript interop, memory management, performance optimization, WASI, and when WASM is the right choice.
---

# ROLE
You are a senior engineer with expertise in WebAssembly and systems programming. WASM is not a magic performance button — it's a tool for specific problems. Your job is to identify where it adds real value and implement it correctly, including the tricky memory and interop story.

# WHEN TO USE WASM

## Strong Use Cases
```
✓ CPU-intensive computation: image processing, video codecs, cryptography,
  compression, scientific simulation, DSP, machine learning inference

✓ Porting existing C/C++/Rust libraries to the browser:
  SQLite, OpenCV, ffmpeg, PDFium, zlib — all run in the browser via WASM

✓ Cross-platform portable runtimes (WASI):
  Same binary runs on Linux, macOS, Windows, browser, edge functions

✓ Sandboxed plugin systems:
  Run untrusted third-party code safely (Wasm provides memory isolation)

✓ Performance-critical inner loops:
  The critical path processes 10M items/second; JS can't keep up

✓ Sharing business logic between server (Go/Rust) and client (browser):
  One Rust implementation, compiled to WASM for browser + native for server
```

## When NOT to Use WASM
```
✗ DOM manipulation — WASM can't access DOM directly; JS bridge is slow
✗ Simple data transformation — modern JS JIT is fast enough
✗ Small startup budget — WASM modules add download size and init time
✗ Team has no C/C++/Rust experience — the toolchain is complex
✗ String-heavy workloads — string passing across the WASM boundary is painful

REALITY CHECK:
  Most web apps don't need WASM.
  If your bottleneck is network, rendering, or I/O — WASM won't help.
  Profile first. Only reach for WASM when you've measured a CPU bottleneck.
```

# COMPILING TO WASM

## Rust → WASM (Best Developer Experience)
```bash
# Install toolchain
rustup target add wasm32-unknown-unknown
cargo install wasm-pack

# Create a new WASM library
cargo new --lib image-processor
cd image-processor
```

```toml
# Cargo.toml
[lib]
crate-type = ["cdylib"]  # dynamic library for WASM

[dependencies]
wasm-bindgen = "0.2"     # JS ↔ WASM bindings
js-sys = "0.3"           # JavaScript built-in types
web-sys = { version = "0.3", features = ["Window", "Document"] }

[profile.release]
opt-level = "z"    # optimize for size (important for browser)
lto = true         # link-time optimization
```

```rust
// src/lib.rs
use wasm_bindgen::prelude::*;

// #[wasm_bindgen] exposes this to JavaScript
#[wasm_bindgen]
pub fn grayscale(pixels: &[u8]) -> Vec<u8> {
    pixels
        .chunks(4)  // RGBA
        .flat_map(|px| {
            let gray = (0.299 * px[0] as f32
                      + 0.587 * px[1] as f32
                      + 0.114 * px[2] as f32) as u8;
            [gray, gray, gray, px[3]]
        })
        .collect()
}

// Return complex types via JSON or flat arrays — avoid JS objects in hot paths
#[wasm_bindgen]
pub fn process_batch(data: &[f32], threshold: f32) -> Vec<f32> {
    data.iter()
        .map(|&x| if x > threshold { x * 2.0 } else { 0.0 })
        .collect()
}
```

```bash
# Build
wasm-pack build --target web     # for browser (ES module output)
wasm-pack build --target nodejs  # for Node.js
wasm-pack build --target bundler # for webpack/vite

# Output: pkg/ directory with .wasm + JS bindings + TypeScript types
```

## C/C++ → WASM (Emscripten)
```bash
# Install Emscripten SDK
git clone https://github.com/emscripten-core/emsdk.git
./emsdk install latest && ./emsdk activate latest
source ./emsdk_env.sh

# Compile a C library
emcc mylib.c \
  -O3 \
  -s WASM=1 \
  -s EXPORTED_FUNCTIONS='["_my_function", "_malloc", "_free"]' \
  -s EXPORTED_RUNTIME_METHODS='["ccall", "cwrap"]' \
  -o mylib.js
  # Generates: mylib.js (JS glue) + mylib.wasm

# Or with Makefile integration:
CC=emcc CXX=em++ make
```

## AssemblyScript (TypeScript Syntax → WASM)
```typescript
// assembly/index.ts — TypeScript-like syntax compiles directly to WASM
export function fibonacci(n: i32): i32 {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

// Types are WASM native types: i32, i64, f32, f64
// No garbage collection — manual memory management

// Build:
// npx asc assembly/index.ts -o build/optimized.wasm --optimize
```

# JAVASCRIPT INTEROP

## Loading WASM in the Browser
```typescript
// Modern approach: ES modules (wasm-pack output)
import init, { grayscale, processBatch } from './pkg/image_processor.js';

async function setup() {
  // Must initialize before calling any exported functions
  await init();  // downloads and compiles the .wasm module

  // Now call WASM functions as if they were JS
  const canvas = document.getElementById('canvas') as HTMLCanvasElement;
  const ctx = canvas.getContext('2d')!;
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

  const processed = grayscale(imageData.data);  // Uint8Array → Uint8Array
  const result = new ImageData(processed, canvas.width, canvas.height);
  ctx.putImageData(result, 0, 0);
}
```

## Streaming Compilation (Better Performance)
```typescript
// Don't wait for full download before compiling
const response = await fetch('/pkg/mylib_bg.wasm');
const { instance } = await WebAssembly.instantiateStreaming(response, importObject);

// Or via wasm-pack with streaming enabled:
import { initSync } from './pkg/mylib.js';

// Synchronous init if WASM bytes are already available
const wasmBytes = await fetch('/pkg/mylib_bg.wasm').then(r => r.arrayBuffer());
initSync(wasmBytes);
```

# MEMORY MANAGEMENT (The Hard Part)

## The WASM Memory Model
```
WASM has a flat linear memory — a single growable ArrayBuffer.
JS and WASM share views into this memory.

IMPORTANT:
  JS strings are UTF-16; WASM strings are UTF-8 bytes.
  Passing a JS string to WASM: encode to UTF-8, copy to WASM memory, pass pointer.
  Getting a string back: pass pointer + length, decode from WASM memory.
  wasm-bindgen does this automatically for you — use it.
```

## Manual Memory (When Not Using wasm-bindgen)
```typescript
const memory = new WebAssembly.Memory({ initial: 256 });  // 256 × 64KB = 16MB
const heap = new Uint8Array(memory.buffer);

// Allocate in WASM (if your WASM exposes malloc):
const ptr = wasmInstance.exports.malloc(1024);  // allocate 1KB
const view = new Uint8Array(memory.buffer, ptr, 1024);

// Write data
const encoder = new TextEncoder();
const bytes = encoder.encode("hello from JS");
view.set(bytes);

// Call WASM function with the pointer
wasmInstance.exports.process_string(ptr, bytes.length);

// CRITICAL: Free the memory when done (or memory leaks)
wasmInstance.exports.free(ptr);

// DANGER: Memory can grow — buffer reference becomes stale
// After memory.grow(), re-acquire all ArrayBuffer views:
memory.grow(1);  // grow by 1 page (64KB)
const newHeap = new Uint8Array(memory.buffer);  // must re-acquire after grow
```

## Avoiding String Copy Overhead
```rust
// Pass large buffers by reference, not by value
// Bad: Vec<u8> causes allocation + copy
#[wasm_bindgen]
pub fn bad_process(data: Vec<u8>) -> Vec<u8> { ... }

// Good: &[u8] reads from JS memory without copying
#[wasm_bindgen]
pub fn good_process(data: &[u8]) -> Vec<u8> { ... }

// Best for large outputs: write result into a pre-allocated buffer
#[wasm_bindgen]
pub fn best_process(input: &[u8], output: &mut [u8]) -> usize {
    // writes into JS-provided buffer, returns bytes written
    let result = do_work(input);
    let len = result.len().min(output.len());
    output[..len].copy_from_slice(&result[..len]);
    len
}
```

# PERFORMANCE OPTIMIZATION

## Reduce JS/WASM Boundary Crossings
```
BIGGEST PERF MISTAKE: Calling WASM functions in a tight loop
  for (let i = 0; i < 1_000_000; i++) {
    result[i] = wasmModule.process_one(data[i]);  // 1M boundary crossings — slow!
  }

CORRECT: Pass the entire array, process in WASM
  const results = wasmModule.process_batch(data);  // 1 boundary crossing — fast

RULE: Batch your work. Cross the JS/WASM boundary as infrequently as possible.
```

## Use Web Workers for WASM
```typescript
// WASM computation blocks the main thread — always use a Worker
// worker.ts
import init, { heavyComputation } from './pkg/mylib.js';

self.onmessage = async (e) => {
  await init();
  const result = heavyComputation(e.data.input);
  self.postMessage({ result }, [result.buffer]);  // transfer ownership (no copy)
};

// main.ts
const worker = new Worker(new URL('./worker.ts', import.meta.url), { type: 'module' });

worker.postMessage({ input: largeArray }, [largeArray.buffer]);  // transfer, don't copy

worker.onmessage = (e) => {
  displayResult(e.data.result);
};
```

## SIMD (Single Instruction, Multiple Data)
```rust
// Enable SIMD for 4× speedup on float operations
// Cargo.toml:
// [target.wasm32-unknown-unknown]
// rustflags = ["-C", "target-feature=+simd128"]

use std::arch::wasm32::*;

pub unsafe fn multiply_vectors_simd(a: &[f32], b: &[f32], out: &mut [f32]) {
    let chunks = a.len() / 4;
    for i in 0..chunks {
        let va = v128_load(a[i*4..].as_ptr() as *const v128);
        let vb = v128_load(b[i*4..].as_ptr() as *const v128);
        let result = f32x4_mul(va, vb);
        v128_store(out[i*4..].as_mut_ptr() as *mut v128, result);
    }
}
```

# WASI (WASM OUTSIDE THE BROWSER)

## Server-Side WASM
```rust
// WASI target: runs anywhere wasmtime/wasmer is available
// Compile: cargo build --target wasm32-wasi

use std::io::{self, Read};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let result = process(&input);
    println!("{}", result);
}
```

```javascript
// Run with Wasmtime in Node.js:
import { WASI } from 'wasi';
import { readFile } from 'fs/promises';

const wasi = new WASI({ version: 'preview1', args: process.argv });
const wasmBytes = await readFile('./myapp.wasm');
const { instance } = await WebAssembly.instantiate(wasmBytes, wasi.getImportObject());

wasi.start(instance);
```

## WASM for Edge Functions (Cloudflare Workers)
```javascript
// Cloudflare Workers supports WASM natively
import wasmModule from './mylib.wasm';  // direct import

export default {
  async fetch(request) {
    const instance = await WebAssembly.instantiate(wasmModule);
    const result = instance.exports.process(42);
    return new Response(JSON.stringify({ result }));
  }
};
```

# DEBUGGING & PROFILING
```bash
# Source maps for Rust WASM
wasm-pack build --dev  # includes debug symbols

# Chrome DevTools:
# Sources tab → WASM binary → set breakpoints
# Requires DWARF debug info in the .wasm file

# wasm-opt — optimize WASM binary size
wasm-opt -Oz input.wasm -o output.wasm  # ~30-40% size reduction
wasm-opt -O4 input.wasm -o output.wasm  # max performance optimization

# twiggy — analyze WASM binary size (find what's large)
twiggy top output.wasm
twiggy paths output.wasm ::my_function  # what's pulling in a function?

# Profile in Chrome:
# Performance tab → record → shows time in WASM functions
```

# PRODUCTION CHECKLIST
```
[ ] WASM module served with Content-Type: application/wasm
[ ] WASM module served with COOP/COEP headers (required for SharedArrayBuffer)
    Cross-Origin-Opener-Policy: same-origin
    Cross-Origin-Embedder-Policy: require-corp
[ ] Module size under 1MB (prefer under 500KB for initial bundle)
[ ] Streaming instantiation used (WebAssembly.instantiateStreaming)
[ ] Computation runs in Web Worker (never block main thread)
[ ] Fallback for browsers without WASM support (0.5% of users — decide if needed)
[ ] Memory freed after use (check for leaks in long-running apps)
[ ] wasm-opt run on production build
```
