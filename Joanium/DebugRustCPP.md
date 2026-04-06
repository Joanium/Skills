---
name: Debug — Rust / C++
trigger: rust error, c++ bug, segfault, borrow checker, lifetime error, cannot borrow, use after free, memory leak, undefined behavior, segmentation fault, stack overflow, rust compile error, c++ crash, asan, valgrind
description: Hyper-specific debugging guide for Rust and C++. Covers Rust borrow checker errors, lifetime issues, ownership, unsafe bugs, C++ memory errors, UB, segfaults, ASAN/Valgrind, and performance profiling.
---

# Debug — Rust / C++

---

# RUST

## First Move

```bash
# Full error output — Rust errors are detailed, read them fully
cargo build 2>&1 | less

# Run with backtrace on panic
RUST_BACKTRACE=1 cargo run
RUST_BACKTRACE=full cargo run   # full stack with all frames

# All clippy lints — catches real bugs beyond the compiler
cargo clippy -- -W clippy::all -W clippy::pedantic

# Run tests with output
cargo test -- --nocapture   # show println! output in tests
cargo test test_name        # run specific test

# Check without building (faster for type checking)
cargo check
```

---

## Borrow Checker Errors

### `cannot borrow X as mutable because it is also borrowed as immutable`

```rust
// Error: you hold an immutable reference while trying to mutate
let mut v = vec![1, 2, 3];
let first = &v[0];   // immutable borrow begins here
v.push(4);           // Error: mutable borrow — could reallocate, invalidating first
println!("{}", first);

// Fix 1: end the immutable borrow before mutating
let mut v = vec![1, 2, 3];
let first_val = v[0];   // copy the value, not a reference
v.push(4);
println!("{}", first_val);  // uses the copied value

// Fix 2: clone if you need the data and mutation
let first = v[0].clone();
v.push(4);

// Fix 3: restructure to not hold refs across mutations
// Use indices instead of references when you'll mutate the collection
let first_idx = 0;
v.push(4);
println!("{}", v[first_idx]);
```

### `cannot borrow X as mutable more than once at a time`

```rust
// Two mutable borrows of the same thing simultaneously
let mut v = vec![1, 2, 3];
let a = &mut v[0];
let b = &mut v[1];   // Error — two &mut borrows of v
*a += 1;
*b += 1;

// Fix: use split_at_mut
let (left, right) = v.split_at_mut(1);
let a = &mut left[0];
let b = &mut right[0];

// Fix 2: use indices and mutate sequentially
v[0] += 1;
v[1] += 1;

// Fix 3: interior mutability with RefCell (single-threaded)
use std::cell::RefCell;
let v: Vec<RefCell<i32>> = vec![RefCell::new(1), RefCell::new(2)];
*v[0].borrow_mut() += 1;
*v[1].borrow_mut() += 1;
```

---

## Lifetime Errors

### `lifetime may not live long enough` / `missing lifetime specifier`

```rust
// Error: returned reference might outlive the data it points to
fn longest(x: &str, y: &str) -> &str {  // Error — which lifetime?
    if x.len() > y.len() { x } else { y }
}

// Fix: add lifetime annotation — tells the compiler output lives as long as both inputs
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

// Error: struct holding a reference needs lifetime annotation
struct Parser {
    input: &str,  // Error — what's the lifetime of this reference?
}

// Fix:
struct Parser<'a> {
    input: &'a str,
}
impl<'a> Parser<'a> {
    fn new(input: &'a str) -> Self {
        Parser { input }
    }
}
```

### `does not live long enough`

```rust
// Error: creating a reference to a value that will be dropped
fn get_data() -> &str {  // Error
    let s = String::from("hello");
    &s   // s is dropped at end of function — reference would dangle
}

// Fix 1: return owned data
fn get_data() -> String {
    String::from("hello")
}

// Fix 2: return &'static str for string literals
fn get_data() -> &'static str {
    "hello"   // static lifetime — lives for the whole program
}

// Fix 3: take a buffer as parameter
fn get_data(buf: &mut String) -> &str {
    buf.push_str("hello");
    buf.as_str()
}
```

---

## Ownership Errors

### `use of moved value`

```rust
// Error: value moved into a function, then used again
let s = String::from("hello");
takes_ownership(s);   // s moved here
println!("{}", s);    // Error: s was moved

// Fix 1: clone (if you need both the original and to pass it)
takes_ownership(s.clone());
println!("{}", s);  // original still valid

// Fix 2: borrow instead of move
takes_reference(&s);   // function takes &String
println!("{}", s);     // s still valid

// Fix 3: restructure so move happens last
println!("{}", s);
takes_ownership(s);  // moved after last use — no problem
```

---

## Trait Errors

### `the trait bound X is not satisfied`

```rust
// You're passing a type to something that requires a trait it doesn't implement

// Debug: what trait is required?
fn print_all<T: Display>(items: Vec<T>) { ... }
print_all(vec![MyStruct {}]);  // Error if MyStruct doesn't implement Display

// Fix: implement the trait
use std::fmt;
impl fmt::Display for MyStruct {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "MyStruct({})", self.value)
    }
}

// Or derive if the trait supports it
#[derive(Debug, Clone, PartialEq)]
struct MyStruct { value: i32 }
```

---

## Panic Debugging

```rust
// RUST_BACKTRACE=1 — always set this when debugging panics

// Common panics:
// 1. Index out of bounds
v[100]  // panics if len <= 100
v.get(100)  // returns Option<&T> — no panic

// 2. Unwrap on None/Err
option.unwrap()          // panics if None
option.expect("message") // panics with better message — prefer over unwrap
option?                  // propagates None/Err up — best in functions returning Result/Option

// 3. Integer overflow (debug mode panics, release mode wraps silently)
let x: u8 = 255;
let y = x + 1;  // panics in debug

// Fix: use checked arithmetic
let y = x.checked_add(1).expect("overflow");
// Or: wrapping_add, saturating_add

// 4. Slice out of range
&s[0..100]  // panics if s.len() < 100
s.get(0..100)  // returns Option<&str> — safe

// Find the exact panic location
std::panic::set_hook(Box::new(|info| {
    println!("Panic: {:?}", info);
    println!("{:?}", std::backtrace::Backtrace::capture());
}));
```

---

## Async Rust (Tokio)

```rust
// Error: async block must be awaited
let result = async_function();  // result is a Future — not yet run
let result = async_function().await;  // correct

// Blocking in async context — blocks the entire thread
async fn bad() {
    std::thread::sleep(Duration::from_secs(1));  // blocks tokio thread
}

// Fix: use tokio::time::sleep
async fn good() {
    tokio::time::sleep(Duration::from_secs(1)).await;
}

// Or run blocking code in a blocking thread pool
async fn with_blocking() {
    let result = tokio::task::spawn_blocking(|| {
        heavy_synchronous_computation()
    }).await.unwrap();
}

// Send bound errors in async
// Error: future cannot be sent between threads safely because X is not Send
// Cause: holding a non-Send type (Rc, RefCell, raw pointer) across an await

// Fix 1: switch to Arc<Mutex<T>> instead of Rc<RefCell<T>>
// Fix 2: drop the non-Send value before the await point
let value = non_send_computation();
let result = value.into_result();  // drop non_send value
some_await().await;                // now it's safe to await
```

---

# C++

## Segfault Debugging

```bash
# Compile with debug symbols and sanitizers (USE THESE, always)
g++ -g -fsanitize=address,undefined -o prog main.cpp
clang++ -g -fsanitize=address,undefined -o prog main.cpp

# AddressSanitizer (ASAN) output is detailed — read it fully:
# ERROR: AddressSanitizer: heap-use-after-free on address 0x...
# READ of size 4 at 0x... thread T0
#     #0 0x... in main /path/main.cpp:42  ← the line that crashed
#     #1 0x... ... (allocated here, freed here)

# Valgrind — memory errors, leaks (slower but no recompile needed)
valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes ./prog

# GDB — interactive debugger
g++ -g -o prog main.cpp  # must have -g
gdb ./prog
(gdb) run          # run the program
(gdb) bt           # backtrace when it crashes
(gdb) frame 3      # switch to frame 3
(gdb) print var    # print variable value
(gdb) list         # show source code around current line
(gdb) break main.cpp:42  # set breakpoint at line 42
(gdb) watch var    # break when var changes
```

---

## Use After Free / Dangling Pointer

```cpp
// Classic UAF
int* p = new int(42);
delete p;
std::cout << *p;   // Undefined Behavior — p points to freed memory

// Fix: set to nullptr after delete
delete p;
p = nullptr;
if (p) *p;   // now safe

// Better fix: use smart pointers — never call delete manually
std::unique_ptr<int> p = std::make_unique<int>(42);
// p freed automatically when it goes out of scope

// Dangling reference
int& getRef() {
    int local = 42;
    return local;   // Undefined Behavior — local destroyed on return
}

// Fix: return by value
int getValue() { return 42; }
// Or ensure the object outlives the reference
```

---

## Undefined Behavior (UB)

```cpp
// These don't crash immediately — they cause silent corruption or random behavior
// ASAN + UBSan catch most of these at runtime

// 1. Signed integer overflow
int x = INT_MAX;
x + 1;   // UB — signed overflow is undefined (unlike unsigned which wraps)
// Fix: use unsigned, or check before adding, or __builtin_add_overflow

// 2. Out of bounds array access
int arr[5];
arr[5] = 1;  // UB — one past the end
// Fix: std::array with .at() throws, or use bounds checking builds

// 3. Dereferencing null
int* p = nullptr;
*p = 5;  // UB — immediate crash on most systems but technically UB

// 4. Strict aliasing violation
int i = 5;
float* fp = reinterpret_cast<float*>(&i);
*fp;   // UB — accessing int through float pointer

// 5. Reading uninitialized memory
int x;
std::cout << x;  // UB — could be anything
// Fix: always initialize: int x = 0;

// Enable all UB sanitizers:
clang++ -fsanitize=undefined,address,leak -fno-omit-frame-pointer -g main.cpp
```

---

## Memory Leaks

```cpp
// Valgrind output:
// LEAK SUMMARY: definitely lost: 40 bytes in 1 blocks
// at 0x...: operator new(unsigned long) ...
//   by 0x...: main /path/main.cpp:10

// Common source: raw new without delete
void bad() {
    int* p = new int[100];
    // return without delete[] p — leak!
}

// Fix 1: RAII — unique_ptr
void good() {
    auto p = std::make_unique<int[]>(100);
    // automatically freed when p goes out of scope
}

// Fix 2: stack allocation when size is known/small
void good2() {
    int arr[100];  // no heap allocation, no leak
}

// Fix 3: std::vector
void good3() {
    std::vector<int> v(100);  // RAII managed
}

// Rule: if you write new, you must write delete. Better: never write new.
// Use make_unique, make_shared, vector, string — the stdlib manages memory.
```

---

## Stack Overflow (C++)

```bash
# Symptom: segfault with very deep call stack, or stack overflow message
# ASAN shows: stack-overflow on address ...

ulimit -s unlimited  # temporary: increase stack size for debugging

# Find it in gdb:
(gdb) bt  # if you see the same function hundreds of times → infinite recursion
```

```cpp
// Common cause: infinite recursion without base case
int factorial(int n) {
    return n * factorial(n - 1);  // missing: if (n == 0) return 1;
}

// Large stack allocations
void bad() {
    int arr[1000000];  // 4MB on stack — likely overflow
}
// Fix: heap allocate
void good() {
    auto arr = std::make_unique<int[]>(1000000);
}
```

---

## Compilation Errors

```bash
# Verbose output
g++ -v main.cpp

# Most common errors:

# 'X' was not declared in this scope
# → missing #include, or wrong namespace
# Fix: add the right header, or use std:: prefix

# no matching function for call to 'X'
# → argument types don't match any overload
# Add -fdiagnostics-show-template-tree for template errors:
clang++ -fdiagnostics-show-template-tree main.cpp

# undefined reference to 'X'  (linker error, not compiler)
# → function declared but not defined, or missing library
g++ main.cpp -o prog -lmylibrary  # add -l flag

# multiple definition of 'X'
# → definition in header included in multiple translation units
// Fix: use 'inline' for definitions in headers
inline int helper() { return 42; }
// Or move definition to .cpp file
```
