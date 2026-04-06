---
name: Debug — Go
trigger: go error, golang bug, panic, nil pointer dereference, goroutine leak, deadlock, race condition, go build failed, interface not implemented, go test failing, go slow, go memory
description: Hyper-specific debugging guide for Go. Real panics, real compiler errors, real fixes. Covers nil panics, goroutine leaks, race conditions, interface errors, context cancellation, and profiling.
---

# Debug — Go

## First Move: Get Complete Information

```bash
# Full build output with verbose
go build -v ./...

# All tests with race detector ON (always use this)
go test -race ./...

# Run with race detector
go run -race main.go

# Verbose test output — see every test
go test -v -race ./...

# Run specific test
go test -v -run TestFunctionName ./pkg/...

# Check for vet errors (catches real bugs)
go vet ./...

# Full static analysis
go install honnef.co/go/tools/cmd/staticcheck@latest
staticcheck ./...
```

---

## Nil Pointer Dereference (Panic)

The #1 Go panic. A nil pointer was dereferenced.

```go
// Panic: runtime error: invalid memory address or nil pointer dereference
// The stack trace shows EXACTLY where — read it

// goroutine 1 [running]:
// main.processUser(...)
//     /app/main.go:42 +0x58   ← line 42 is where the nil dereference happened

// Common causes:

// 1. Function returns nil on error but caller ignores the error
user, err := getUser(id)  // if err != nil, user IS nil
// Wrong:
fmt.Println(user.Name)  // panic if user is nil

// Right: ALWAYS check the error first
if err != nil {
    return fmt.Errorf("getUser: %w", err)
}
fmt.Println(user.Name)  // safe

// 2. Nil interface vs nil pointer — the subtlest Go trap
type Animal interface { Sound() string }
type Dog struct{}
func (d *Dog) Sound() string { return "woof" }

func getAnimal(want bool) Animal {
    var d *Dog  // d is a nil *Dog pointer
    if want {
        d = &Dog{}
    }
    return d  // NEVER do this — returns a non-nil interface wrapping a nil pointer
}

a := getAnimal(false)
fmt.Println(a == nil)  // FALSE — the interface is not nil even though *Dog inside is nil
a.Sound()              // PANIC

// Fix: return nil explicitly
func getAnimal(want bool) Animal {
    if want {
        return &Dog{}
    }
    return nil  // returns a truly nil interface
}

// 3. Uninitialized map — nil map reads return zero value, writes panic
var m map[string]int
fmt.Println(m["key"])  // 0 — no panic on read
m["key"] = 1           // panic: assignment to entry in nil map

// Fix: always initialize
m := make(map[string]int)
// Or: m := map[string]int{}
```

---

## Goroutine Leaks

Goroutines blocked forever, never garbage collected.

```go
// Detect: print goroutine count
import "runtime"
fmt.Println("goroutines:", runtime.NumGoroutine())

// Better: use goleak in tests
import "go.uber.org/goleak"
func TestMyFunc(t *testing.T) {
    defer goleak.VerifyNone(t)  // fails if any goroutines leak
    myFunc()
}

// Common cause 1: channel send/receive with no one on the other end
ch := make(chan int)
go func() {
    ch <- computeResult()  // blocks forever if nobody reads
}()
// Goroutine leaked if ch is never read

// Fix: use buffered channel or select with context
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

go func() {
    select {
    case ch <- computeResult():
    case <-ctx.Done():  // goroutine exits if context cancelled
    }
}()

// Common cause 2: http.Get without timeout — hangs forever
resp, err := http.Get(url)  // no timeout = goroutine leak if server hangs

// Fix: always set a timeout
client := &http.Client{Timeout: 10 * time.Second}
resp, err := client.Get(url)
```

---

## Data Race

```bash
# Run ALL tests and programs with -race
go test -race ./...
go run -race main.go

# Output looks like:
# WARNING: DATA RACE
# Write at 0x00c0000b6018 by goroutine 7:
#   main.increment()
#       /app/main.go:15
# Read at 0x00c0000b6018 by goroutine 6:
#   main.readValue()
#       /app/main.go:22
```

```go
// Fix 1: sync.Mutex
type Counter struct {
    mu    sync.Mutex
    value int
}

func (c *Counter) Increment() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.value++
}

// Fix 2: sync.RWMutex for read-heavy workloads
func (c *Counter) Read() int {
    c.mu.RLock()
    defer c.mu.RUnlock()
    return c.value
}

// Fix 3: sync/atomic for simple numeric operations
import "sync/atomic"
var counter int64
atomic.AddInt64(&counter, 1)
val := atomic.LoadInt64(&counter)

// Fix 4: channels — communicate ownership instead of sharing
// Instead of sharing state, send the data through a channel
updates := make(chan int, 100)
go func() {
    for val := range updates {
        process(val)
    }
}()
updates <- newValue
```

---

## Deadlock

```go
// Fatal error: all goroutines are asleep - deadlock!
// Go detects this and crashes with a full goroutine dump — read it carefully

// Cause 1: lock acquired twice in same goroutine
var mu sync.Mutex
mu.Lock()
mu.Lock()  // deadlock — same goroutine can't acquire twice (not reentrant)

// Cause 2: inconsistent lock ordering
// Goroutine A: locks mu1 then mu2
// Goroutine B: locks mu2 then mu1
// → circular wait

// Fix: always acquire locks in the same order everywhere

// Cause 3: sending to an unbuffered channel from the same goroutine that reads
ch := make(chan int)
ch <- 1      // blocks waiting for a reader
val := <-ch  // never reached — deadlock

// Fix: buffer the channel or use a separate goroutine
ch := make(chan int, 1)  // buffered — send doesn't block
ch <- 1
val := <-ch

// Debug: print goroutine stacks
import (
    "runtime"
    "os"
)
buf := make([]byte, 1<<20)
n := runtime.Stack(buf, true)  // all=true dumps ALL goroutines
os.Stderr.Write(buf[:n])
```

---

## Interface Not Implemented

```go
// Error: cannot use *MyType as type MyInterface (missing Method)
// or: *MyType does not implement MyInterface (wrong signature)

// 1. Pointer receiver vs value receiver mismatch
type Doer interface { Do() string }

type MyStruct struct{}
func (m MyStruct) Do() string { return "done" }  // value receiver

var _ Doer = MyStruct{}   // OK
var _ Doer = &MyStruct{}  // also OK — pointer satisfies value receiver interface

func (m *MyStruct) Do() string { return "done" }  // pointer receiver

var _ Doer = MyStruct{}   // ERROR — value doesn't satisfy pointer receiver interface
var _ Doer = &MyStruct{}  // OK

// Compile-time interface check (catch this early)
var _ Doer = (*MyStruct)(nil)  // fails to compile if *MyStruct doesn't implement Doer

// 2. Method signature mismatch
// Interface: Do(ctx context.Context) error
// Struct:    Do() error  ← wrong — missing ctx param
```

---

## Error Handling

```go
// Unwrapping errors — check the chain
var notFound *NotFoundError
if errors.As(err, &notFound) {
    fmt.Println("not found:", notFound.ID)
}

// Check for specific error value
if errors.Is(err, sql.ErrNoRows) {
    return nil, ErrUserNotFound
}

// Add context to errors (always wrap with %w to preserve chain)
if err != nil {
    return fmt.Errorf("processUser id=%d: %w", id, err)
}
// Not: fmt.Errorf("error: %s", err)  ← loses error type for errors.Is/As

// Log full error chain
fmt.Printf("%+v\n", err)  // with pkg/errors — prints stack trace
// Or:
fmt.Println(err)       // just the message chain
errors.Unwrap(err)     // get the wrapped error
```

---

## Context Cancellation

```go
// Always propagate context
func processRequest(ctx context.Context) error {
    // Check if already cancelled before starting expensive work
    select {
    case <-ctx.Done():
        return ctx.Err()
    default:
    }

    // Pass context to all downstream calls
    user, err := db.QueryContext(ctx, "SELECT ...")
    res, err := httpClient.Do(req.WithContext(ctx))
    result, err := processData(ctx, user)

    return nil
}

// Context timeout — always set one for external calls
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()  // ALWAYS defer cancel — prevents context leak even if timeout not reached

// Debug context cancellation cause
if ctx.Err() == context.Canceled {
    log.Println("request was cancelled by caller")
} else if ctx.Err() == context.DeadlineExceeded {
    log.Println("request timed out")
}
```

---

## Performance Profiling

```go
// CPU profiling
import "runtime/pprof"

f, _ := os.Create("cpu.prof")
pprof.StartCPUProfile(f)
defer pprof.StopCPUProfile()
// run your code
// then: go tool pprof cpu.prof → type "web" for flame graph

// Memory profiling
f, _ := os.Create("mem.prof")
runtime.GC()
pprof.WriteHeapProfile(f)
// then: go tool pprof mem.prof → type "top" or "web"

// HTTP endpoint (great for long-running services)
import _ "net/http/pprof"
go http.ListenAndServe(":6060", nil)
// Then: go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

// Benchmark in tests
func BenchmarkMyFunc(b *testing.B) {
    for i := 0; i < b.N; i++ {
        MyFunc()
    }
}
go test -bench=. -benchmem ./...
# -benchmem shows allocations per op — critical for finding GC pressure
```

---

## go test Failures

```bash
# Verbose — see all log output
go test -v ./...

# Run single test
go test -v -run "^TestMyFunc$" ./pkg/service/

# Run tests matching pattern
go test -v -run "TestUser" ./...

# Parallel test issues — add -count=1 to disable cache
go test -count=1 ./...

# Timeout (default 10m) — catch hanging tests
go test -timeout 30s ./...

# Coverage
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out  # opens browser with coverage map

# Build constraint issues — check tags
go test -tags integration ./...
```

---

## Common Compiler Errors

```go
// "declared and not used" — Go requires using all local variables
x := 5  // Error if x is never used
// Fix: use it, or use _ for intentional discard
_, err := doSomething()

// "imported and not used"
import "fmt"  // Error if fmt never called
// Fix: remove the import, or use goimports to auto-manage

// "undefined: X" — check package name and import path
// Is the function exported? (starts with uppercase)
// Is the package imported?

// Multiple return values not captured
result := functionReturningTwoValues()  // Error
result, err := functionReturningTwoValues()  // correct
```
