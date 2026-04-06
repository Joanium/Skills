---
name: Functional Programming Patterns
trigger: functional programming, pure functions, immutability, function composition, map filter reduce, fp patterns, side effects, referential transparency, monad, functor, currying, partial application, functional approach, fp in javascript, fp in python, higher order functions, point-free
description: Apply functional programming principles — pure functions, immutability, composition, and higher-order functions — to write more predictable, testable, and maintainable code. Use when refactoring imperative code, designing data transformation pipelines, or introducing FP concepts to a codebase.
---

Functional programming isn't an ideology — it's a set of constraints that make code easier to reason about. Pure functions always return the same output for the same input. Immutable data doesn't surprise you with mutations across call frames. Composed pipelines are readable in the order data flows. These are practical benefits, not abstract ideals.

## The Three Core Properties

```
1. PURE FUNCTIONS — no side effects, same input → same output
   Benefits: trivially testable, parallelizable, cacheable

2. IMMUTABILITY — don't mutate; return new values
   Benefits: no surprise mutations, safe sharing, easy undo/redo

3. COMPOSITION — build complex behavior from simple functions
   Benefits: reusable parts, readable pipelines, single responsibility

You don't have to adopt all three at once. Even adding one improves code.
```

---

## Pure Functions

A function is pure if:
1. It always returns the same output for the same input
2. It has no side effects (no I/O, no mutations, no global state)

```typescript
// IMPURE: depends on external state, has side effect
let taxRate = 0.1;
let log = [];

function calculateTotal(price: number): number {
  const total = price * (1 + taxRate); // depends on external state
  log.push(total);                     // side effect
  return total;
}

// PURE: self-contained, no side effects
function calculateTotal(price: number, taxRate: number): number {
  return price * (1 + taxRate);
}

// PURE: trivially testable
expect(calculateTotal(100, 0.1)).toBe(110);
expect(calculateTotal(100, 0.1)).toBe(110); // Always. No setup needed.
```

### Push side effects to the edges
The functional approach doesn't ban side effects — it isolates them:

```typescript
// The core logic is pure — all the smart stuff is here
function processOrders(orders: Order[]): ProcessedOrder[] {
  return orders
    .filter(order => order.status === 'pending')
    .map(order => applyDiscount(order))
    .map(order => calculateTax(order))
    .filter(order => order.total > 0);
}

// Side effects live at the edges — easy to find, easy to mock in tests
async function main() {
  const orders = await db.fetchPendingOrders();    // side effect: I/O
  const processed = processOrders(orders);          // pure — testable
  await db.saveBatch(processed);                    // side effect: I/O
  await emailService.notifyBatch(processed);        // side effect: I/O
}
```

---

## Immutability

### Object and array operations
```typescript
// MUTATION — dangerous across call frames
function addDiscount(order: Order, discount: number) {
  order.total = order.total - discount; // mutates the original!
  return order;
}

// IMMUTABLE — return new values
function addDiscount(order: Order, discount: number): Order {
  return { ...order, total: order.total - discount };
}

// Array mutations to avoid → immutable alternatives
const arr = [1, 2, 3];

// push / pop / splice → spread + concat
const withItem = [...arr, 4];
const withoutLast = arr.slice(0, -1);
const withInsert = [...arr.slice(0, 1), 99, ...arr.slice(1)];

// sort mutates! → copy first
const sorted = [...arr].sort((a, b) => a - b);

// Object delete → spread with omit
const { removeMe, ...rest } = obj;

// Nested immutable updates
const state = { user: { name: 'Alice', address: { city: 'NYC' } } };

// Deep update without mutation
const newState = {
  ...state,
  user: {
    ...state.user,
    address: {
      ...state.user.address,
      city: 'LA'
    }
  }
};

// For complex nested updates, use Immer:
import { produce } from 'immer';

const newState = produce(state, draft => {
  draft.user.address.city = 'LA'; // Looks like mutation, creates new object
});
```

### Immutable data structures for performance
```typescript
// For large datasets, spread creates copies (O(n) per update)
// Use a library for structural sharing:

import { Map, List } from 'immutable'; // Persistent data structures

const map = Map({ a: 1, b: 2 });
const updated = map.set('a', 99); // New map, shares unchanged structure
map.get('a');     // 1 — original unchanged
updated.get('a'); // 99
```

---

## Higher-Order Functions

Functions that take or return functions are the building blocks of FP.

### map, filter, reduce — the holy trinity
```typescript
const orders = [
  { id: 1, total: 50,  status: 'paid',    items: 2 },
  { id: 2, total: 200, status: 'pending', items: 5 },
  { id: 3, total: 75,  status: 'paid',    items: 1 },
];

// Imperative (harder to scan)
let revenue = 0;
const paidOrders = [];
for (const order of orders) {
  if (order.status === 'paid') {
    paidOrders.push(order);
    revenue += order.total;
  }
}

// Functional (reads like a description)
const paidOrders = orders.filter(order => order.status === 'paid');
const revenue = paidOrders.reduce((sum, order) => sum + order.total, 0);

// Pipeline: transform data step by step
const result = orders
  .filter(o => o.status === 'paid')
  .map(o => ({ ...o, totalWithTax: o.total * 1.1 }))
  .sort((a, b) => b.total - a.total)
  .slice(0, 10); // Top 10 paid orders by value
```

### Currying and partial application
```typescript
// Currying: transform a multi-argument function into a chain of single-argument functions
const multiply = (a: number) => (b: number) => a * b;

const double = multiply(2);   // Partially applied
const triple = multiply(3);

double(5); // 10
triple(5); // 15

// Practical currying with Ramda
import * as R from 'ramda';

const getByStatus = R.curry((status: string, orders: Order[]) =>
  orders.filter(o => o.status === status)
);

const getPaidOrders = getByStatus('paid');
const getPendingOrders = getByStatus('pending');

// Now these are reusable, composable filters
getPaidOrders(allOrders);
getPendingOrders(allOrders);
```

### Function composition
```typescript
// Compose: apply functions right-to-left
const compose = (...fns: Function[]) => (x: any) =>
  fns.reduceRight((acc, fn) => fn(acc), x);

// Pipe: apply functions left-to-right (more readable)
const pipe = (...fns: Function[]) => (x: any) =>
  fns.reduce((acc, fn) => fn(acc), x);

// Build processing pipelines from small, reusable functions
const normalize = (s: string) => s.toLowerCase().trim();
const removeSpecialChars = (s: string) => s.replace(/[^a-z0-9\s]/g, '');
const toSlug = (s: string) => s.replace(/\s+/g, '-');

const slugify = pipe(normalize, removeSpecialChars, toSlug);

slugify('Hello, World!'); // "hello-world"
slugify('  TypeScript Rocks!!  '); // "typescript-rocks"

// Real-world data pipeline
const processUserInput = pipe(
  sanitizeInput,
  validateFields,
  normalizePhoneNumber,
  enrichWithGeoLocation,
  formatForDatabase
);

const result = processUserInput(formData);
```

---

## Functional Patterns for Common Problems

### Option/Maybe — handling null safely
```typescript
// Instead of null checks everywhere
type Option<T> = { kind: 'some'; value: T } | { kind: 'none' };

const some = <T>(value: T): Option<T> => ({ kind: 'some', value });
const none: Option<never> = { kind: 'none' };

function findUser(id: string): Option<User> {
  const user = users.get(id);
  return user ? some(user) : none;
}

function mapOption<T, U>(option: Option<T>, fn: (v: T) => U): Option<U> {
  return option.kind === 'some' ? some(fn(option.value)) : none;
}

// Chain nullable operations safely
const emailDomain = mapOption(
  findUser(userId),
  user => user.email.split('@')[1]
);

// ts-pattern or fp-ts for production use:
import { pipe } from 'fp-ts/function';
import * as O from 'fp-ts/Option';

const emailDomain = pipe(
  O.fromNullable(users.get(userId)),
  O.map(user => user.email.split('@')[1])
);
```

### Result type — explicit error handling
```typescript
// Replace throw/catch with explicit Result type
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

const ok = <T>(value: T): Result<T, never> => ({ ok: true, value });
const err = <E>(error: E): Result<never, E> => ({ ok: false, error });

async function parseConfig(path: string): Promise<Result<Config, string>> {
  try {
    const content = await fs.readFile(path, 'utf-8');
    return ok(JSON.parse(content));
  } catch (e) {
    return err(`Failed to parse config: ${e.message}`);
  }
}

// No surprises — caller must handle both cases
const result = await parseConfig('./config.json');
if (!result.ok) {
  logger.error(result.error);
  process.exit(1);
}
const config = result.value; // TypeScript knows this is Config
```

### Transducer pattern — efficient data pipelines
```typescript
// Problem: chained map/filter creates intermediate arrays
const result = bigArray
  .filter(pred1)  // creates array #1
  .map(transform) // creates array #2
  .filter(pred2); // creates array #3

// Transducer: compose transforms without intermediates
const filterMap = <T, U>(pred: (x: T) => boolean, fn: (x: T) => U) =>
  (arr: T[]): U[] => {
    const result: U[] = [];
    for (const x of arr) {
      if (pred(x)) result.push(fn(x));
    }
    return result;
  };

const processOrders = filterMap(
  (o: Order) => o.status === 'paid',
  (o: Order) => ({ id: o.id, total: o.total * 1.1 })
);

// One pass, no intermediates
const result = processOrders(bigArray);
```

---

## Python Functional Patterns

```python
from functools import reduce, partial
from itertools import chain, islice
from typing import Callable, TypeVar, Iterable

T = TypeVar('T')
U = TypeVar('U')

# Pure function with type hints
def calculate_tax(price: float, rate: float) -> float:
    return price * (1 + rate)

# Partial application
calculate_uk_tax = partial(calculate_tax, rate=0.20)
calculate_us_tax = partial(calculate_tax, rate=0.08)

# Pipeline with functools.reduce
def pipe(*fns: Callable) -> Callable:
    return lambda x: reduce(lambda v, f: f(v), fns, x)

process = pipe(
    str.strip,
    str.lower,
    lambda s: s.replace(' ', '_')
)

process('  Hello World  ')  # 'hello_world'

# Lazy evaluation with generators (memory-efficient pipelines)
def filter_map(pred, transform, iterable):
    return (transform(x) for x in iterable if pred(x))

# Processes one item at a time — no large intermediate lists
results = filter_map(
    lambda o: o['status'] == 'paid',
    lambda o: {**o, 'total_with_tax': o['total'] * 1.1},
    all_orders  # Could be a DB cursor with millions of rows
)
```

---

## When to Use (and Not Use) FP

```
FP SHINES for:
✓ Data transformation pipelines (ETL, report generation)
✓ Business rule calculation (pricing, tax, discounts)
✓ Event processing and stream manipulation
✓ Anywhere testability is paramount
✓ Concurrent / parallel processing (pure functions are safe to parallelize)

FP IS AWKWARD for:
✗ I/O-heavy sequential workflows (use async/await + side effects honestly)
✗ State machines with complex transitions (OOP or explicit state works better)
✗ Performance-critical loops (imperative with mutation is often faster)
✗ Teams unfamiliar with FP (readability drops if the team isn't on board)

The pragmatic approach:
→ Keep pure functions at the core of your business logic
→ Keep side effects at the edges (DB, I/O, external APIs)
→ Use immutability by default for data flowing through the system
→ Reach for composition when you see repeated transformation patterns
→ Don't adopt Haskell-style monads in a JavaScript codebase unless the whole 
  team is fluent — readability matters more than purity
```
