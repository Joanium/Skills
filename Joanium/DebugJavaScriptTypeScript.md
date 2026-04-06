---
name: Debug — JavaScript / TypeScript
trigger: JS bug, TS error, typescript error, javascript not working, type error, undefined is not a function, cannot read properties, module not found, promise rejected, NaN, type mismatch
description: Hyper-specific debugging guide for JavaScript and TypeScript. Real error messages, real causes, real fixes. Covers runtime errors, TypeScript compiler errors, async bugs, module issues, and type system traps.
---

# Debug — JavaScript / TypeScript

## First Move: Get the Full Picture

```bash
# TypeScript — check ALL type errors at once (no emitting)
npx tsc --noEmit 2>&1

# See errors with full context
npx tsc --noEmit --pretty 2>&1 | less

# Runtime — always run with source maps enabled
node --enable-source-maps dist/index.js

# Check your Node version matches what the project expects
node -v
cat .nvmrc 2>/dev/null || cat package.json | grep '"node"'
```

---

## TypeScript Compiler Errors

### `Type 'X' is not assignable to type 'Y'`

**Cause 1: Optional field used as required**
```typescript
// Error
interface User { name?: string }
const u: User = {}
u.name.toUpperCase() // Object is possibly 'undefined'

// Fix — narrow before use
u.name?.toUpperCase()          // optional chain — returns undefined
u.name?.toUpperCase() ?? ''    // with fallback
if (u.name) u.name.toUpperCase() // type guard
```

**Cause 2: Union type not narrowed**
```typescript
function process(val: string | number) {
  val.toUpperCase() // Error — number has no toUpperCase

  // Fix — narrow with typeof
  if (typeof val === 'string') {
    val.toUpperCase() // TS now knows it's string
  }
}
```

**Cause 3: Return type mismatch**
```typescript
// TS infers return type as string | undefined but caller expects string
function getName(user: User): string {
  if (user.active) return user.name  // Error if name is string | undefined
  // Fix: add explicit return or handle undefined
  return user.name ?? 'Anonymous'
}
```

**Cause 4: Async function returning wrong type**
```typescript
// Async functions always return Promise<T> — not T
async function getUser(): Promise<User> { ... }
const user: User = getUser()  // Error — this is a Promise, not a User
const user: User = await getUser()  // Fix
```

---

### `Cannot find module 'X'` or `Module not found`

```bash
# 1. Confirm the file actually exists
ls src/utils/helpers.ts
ls src/utils/helpers/index.ts  # maybe it's an index file

# 2. Check tsconfig path aliases
cat tsconfig.json | grep -A 20 "paths"
# If using @/components — does the alias point to the right directory?

# 3. Node runtime doesn't understand tsconfig paths
# You need tsconfig-paths or a bundler at runtime
npm install tsconfig-paths
# Then run: node -r tsconfig-paths/register dist/index.js

# 4. ESM vs CJS conflict — check package type
cat package.json | grep '"type"'
# "type": "module" → use import/export, .mjs, or "moduleResolution": "bundler"
# "type": "commonjs" → use require() or configure TS to output CJS

# 5. Missing @types package
npm install --save-dev @types/node @types/express  # whatever is missing
```

---

### `Property 'X' does not exist on type 'Y'`

```typescript
// Cause: accessing a key that TS doesn't know about
const obj = JSON.parse(data)  // obj is 'any' — no type info

// Fix 1: Type assertion (use sparingly)
const obj = JSON.parse(data) as MyType

// Fix 2: Type guard with runtime check (safer)
function isMyType(obj: unknown): obj is MyType {
  return typeof obj === 'object' && obj !== null && 'id' in obj
}

// Fix 3: Zod for runtime-validated types (best for external data)
import { z } from 'zod'
const MySchema = z.object({ id: z.string(), name: z.string() })
const obj = MySchema.parse(JSON.parse(data))  // throws if invalid
```

---

### `Conversion of type 'X' to type 'Y' may be a mistake`

```typescript
// TS is blocking a dangerous cast
const el = document.getElementById('btn') as HTMLButtonElement
// If you're sure — use double assertion (smell — find out WHY)
const el = document.getElementById('btn') as unknown as HTMLButtonElement

// Better — narrow properly
const el = document.getElementById('btn')
if (!(el instanceof HTMLButtonElement)) throw new Error('Expected button')
el.click()  // TS now knows it's HTMLButtonElement
```

---

## Runtime Errors

### `TypeError: Cannot read properties of undefined (reading 'X')`

This is the #1 JS error. Means something you expected to exist is `undefined`.

```javascript
// Debug: find WHAT is undefined — log the full chain
console.log({ user, profile: user?.profile, name: user?.profile?.name })

// Common sources:
// 1. API response shape changed — log the raw response
fetch('/api/user').then(r => r.json()).then(data => console.log('RAW:', data))

// 2. Async data used before it loaded
const [user, setUser] = useState(null)
user.name  // Error — user is null on first render
user?.name  // Fix — optional chain

// 3. Array method returned undefined
const found = arr.find(x => x.id === id)
found.name  // Error if not found — find() returns undefined on no match
found?.name // Fix — or check first: if (!found) throw / return

// 4. Destructuring from undefined
const { name } = getUser()  // Error if getUser() returns undefined
const { name } = getUser() ?? {}  // Fix with fallback
```

---

### `Unhandled Promise Rejection` / Swallowed async errors

```javascript
// Common pattern that silently swallows errors:
async function loadData() {
  const data = await fetch('/api').then(r => r.json())  // if this throws, nothing happens
}
loadData()  // no await, no .catch() — error disappears

// Fix 1: always try/catch in async functions
async function loadData() {
  try {
    const res = await fetch('/api')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return await res.json()
  } catch (err) {
    console.error('loadData failed:', err)
    throw err  // re-throw so callers know
  }
}

// Fix 2: catch at the call site
loadData().catch(err => console.error(err))

// Fix 3: global handler to find all unhandled rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled rejection at:', promise, 'reason:', reason)
})
```

---

### `NaN` propagating silently

```javascript
// NaN === NaN is false — NaN is invisible
const price = parseFloat('abc')  // NaN
const total = price * 2          // NaN — no error thrown
console.log(total > 0)           // false — but silently wrong

// Debug: find where NaN enters
Number.isNaN(price)  // true

// Fix: validate before arithmetic
const price = parseFloat(input)
if (Number.isNaN(price)) throw new Error(`Invalid price: "${input}"`)

// Or use a safe parser
const safeFloat = (s) => {
  const n = parseFloat(s)
  return Number.isNaN(n) ? 0 : n
}
```

---

### Closure / Stale Variable in Loop

```javascript
// Classic bug — var is function-scoped, not block-scoped
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100)  // prints 3, 3, 3
}

// Fix 1: use let (block-scoped)
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100)  // prints 0, 1, 2
}

// Fix 2: capture via IIFE (legacy code)
for (var i = 0; i < 3; i++) {
  ((j) => setTimeout(() => console.log(j), 100))(i)
}
```

---

### `Maximum call stack size exceeded`

```javascript
// Infinite recursion — add a base case check
function walk(node) {
  console.log(node.value)
  walk(node.next)  // No base case — crashes when node.next is undefined
}

// Fix: guard the recursion
function walk(node) {
  if (!node) return          // base case
  console.log(node.value)
  walk(node.next)
}

// Also caused by: circular JSON — use safe serialize
JSON.stringify(obj, (key, val) => {
  if (key === 'parent') return undefined  // break the cycle
  return val
})
```

---

## Async / Event Loop Traps

### Promise chain not running in expected order

```javascript
// Bug: mixing await and .then() inconsistently
async function run() {
  fetch('/api')
    .then(r => r.json())
    .then(data => process(data))  // runs async, not awaited
  
  finish()  // runs BEFORE process() — wrong order
}

// Fix: be consistent — full await
async function run() {
  const res = await fetch('/api')
  const data = await res.json()
  await process(data)
  finish()  // now runs after process
}
```

### `Promise.all` fails on first rejection — others abandoned

```javascript
// If any promise rejects, ALL results are lost
const results = await Promise.all([fetchA(), fetchB(), fetchC()])
// If fetchB rejects, fetchA and fetchC results are gone

// Fix: use Promise.allSettled to get all results regardless
const results = await Promise.allSettled([fetchA(), fetchB(), fetchC()])
results.forEach(r => {
  if (r.status === 'fulfilled') console.log(r.value)
  else console.error('Failed:', r.reason)
})
```

---

## Type System Footguns

### `as any` / `as unknown as X` hiding real bugs

```typescript
// If you find yourself doing this — the types are wrong upstream
const data = response as any
data.user.name  // No type safety — runtime error possible

// Trace back to where the type is first wrong
// Fix at the source: response should be typed as ApiResponse
interface ApiResponse { user: { name: string } }
const data = response as ApiResponse
```

### `strictNullChecks` off — silent null bugs

```json
// tsconfig.json — always enable these
{
  "compilerOptions": {
    "strict": true,           // enables all strict checks
    "strictNullChecks": true, // null/undefined are not assignable to other types
    "noUncheckedIndexedAccess": true  // arr[0] is T | undefined, not T
  }
}
```

---

## Debugging Tools

```bash
# Node.js debugger — inspect protocol
node --inspect index.js
# Then open chrome://inspect in Chrome → click "inspect" under Remote Target

# Breakpoint in code
debugger  // pauses execution when devtools is open

# Pretty-print complex objects (avoids [Object])
console.log(JSON.stringify(obj, null, 2))
console.dir(obj, { depth: null })  // full depth, no truncation

# Trace where a value changes
Object.defineProperty(obj, 'key', {
  set(val) {
    console.trace('key was set to:', val)
    this._key = val
  },
  get() { return this._key }
})

# Performance profiling
console.time('label')
expensiveOperation()
console.timeEnd('label')
```

---

## Common `tsc` Config Mistakes

```json
// These settings cause the most confusion:
{
  "compilerOptions": {
    // Wrong: "module": "commonjs" with "type": "module" in package.json → conflicts
    // Fix: match module format to package.json type field

    // Wrong: "target": "es5" when using modern APIs → polyfill needed or missing
    // Fix: "target": "ES2020" or higher for Node 14+

    // Missing: "esModuleInterop": true → import React from 'react' fails
    // Missing: "resolveJsonModule": true → can't import .json files

    // Wrong: "outDir" not set → compiled files land next to source files
    "outDir": "./dist",
    "rootDir": "./src"
  }
}
```
