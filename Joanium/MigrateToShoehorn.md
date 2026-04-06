---
name: Migrate to Shoehorn
trigger: shoehorn, migrate type assertions, replace as in tests, partial test data, as unknown as, fix type assertions in tests
description: Migrate test files from `as` type assertions to @total-typescript/shoehorn for type-safe partial test data.
---

`as` assertions in tests are a smell: they hide incomplete test data, require you to manually specify target types, and force double-casting for intentionally wrong data. Shoehorn replaces all three patterns with type-safe alternatives that keep autocomplete working.

**Test code only.** Never use shoehorn in production code.

---

## Why `as` Is a Problem in Tests

```typescript
// Problems with `as`:
// 1. Must fake all 20+ fields to satisfy the type
// 2. Easy to forget a field and not notice
// 3. `as unknown as Type` is ugly and loses autocomplete
getUser({ body: { id: "123" }, headers: {}, cookies: {}, ...20more } as Request);
```

---

## Install

```bash
npm i @total-typescript/shoehorn
```

---

## Migration Patterns

### Large objects where you only care about a few fields

Before:

```typescript
it('gets user by id', () => {
  getUser({
    body: { id: '123' },
    headers: {},
    cookies: {},
    // ... 20 more fake fields
  });
});
```

After:

```typescript
import { fromPartial } from '@total-typescript/shoehorn';

it('gets user by id', () => {
  getUser(fromPartial({ body: { id: '123' } }));
});
```

### `as Type` → `fromPartial()`

Before:

```typescript
getUser({ body: { id: '123' } } as Request);
```

After:

```typescript
getUser(fromPartial({ body: { id: '123' } }));
```

### `as unknown as Type` → `fromAny()`

Before:

```typescript
getUser({ body: { id: 123 } } as unknown as Request); // intentionally wrong type
```

After:

```typescript
import { fromAny } from '@total-typescript/shoehorn';
getUser(fromAny({ body: { id: 123 } }));
```

---

## When to Use Each

| Function        | Use case                                                                    |
| --------------- | --------------------------------------------------------------------------- |
| `fromPartial()` | Pass partial data that still type-checks (right shape, incomplete)          |
| `fromAny()`     | Pass intentionally wrong data — keeps autocomplete, bypasses checks         |
| `fromExact()`   | Force full object (useful to swap back from fromPartial for specific tests) |

---

## Workflow

### Step 1: Understand the scope

Ask the user:

- Which test files have `as` assertions causing problems?
- Are they dealing with large objects where only some properties matter?
- Do they need to pass intentionally wrong data for error testing?

### Step 2: Find affected files

```bash
# Find as Type assertions in test files
grep -r " as [A-Z]" --include="*.test.ts" --include="*.spec.ts"

# Find double-cast assertions
grep -r "as unknown as" --include="*.test.ts" --include="*.spec.ts"
```

### Step 3: Install and migrate

```
[ ] Install: npm i @total-typescript/shoehorn
[ ] Replace `as Type` with fromPartial()
[ ] Replace `as unknown as Type` with fromAny()
[ ] Add imports from @total-typescript/shoehorn
[ ] Run type check to verify: npx tsc --noEmit
[ ] Run tests to confirm nothing broke
```

---

## Common Mistakes

**[CRITICAL]** Using shoehorn in production code — it's a test utility only. Production code should have complete, valid types.

**[IMPORTANT]** Using `fromAny()` where `fromPartial()` would work — prefer `fromPartial()` because it keeps type-checking for the fields you do provide.

**[SUGGESTION]** Migrating incrementally — you don't have to do all files at once. Start with the files that are most painful.
