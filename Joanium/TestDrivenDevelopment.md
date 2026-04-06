---
name: TDD
trigger: tdd, test driven development, red green refactor, write tests first, test first, integration tests, build with tests
description: Build features or fix bugs using a red-green-refactor loop with vertical tracer-bullet slices. Tests verify behavior through public interfaces, not implementation details.
---

A great TDD session produces tests that describe what the system does — not how it does it. The tests should survive a complete internal rewrite. If renaming a private function breaks a test, that test is wrong.

## Core Philosophy

**Tests should verify behavior, not implementation.**

```typescript
// GOOD: Tests observable behavior
test('user can checkout with valid cart', async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe('confirmed');
});

// BAD: Tests implementation details
test('checkout calls paymentService.process', async () => {
  const mockPayment = jest.mock(paymentService);
  await checkout(cart, payment);
  expect(mockPayment.process).toHaveBeenCalledWith(cart.total);
});
```

A good test reads like a specification. A bad test reads like a diff.

## The Anti-Pattern: Horizontal Slicing

**DO NOT write all tests first, then all implementation.**

```
WRONG (horizontal):
  RED:   test1, test2, test3, test4, test5
  GREEN: impl1, impl2, impl3, impl4, impl5

RIGHT (vertical):
  RED → GREEN: test1 → impl1
  RED → GREEN: test2 → impl2
  RED → GREEN: test3 → impl3
```

Horizontal slicing produces bad tests: you're testing imagined behavior, not actual behavior. Tests become insensitive to real changes. You commit to test structure before understanding the implementation.

---

## Workflow

### Step 1: Planning

Before writing any code, confirm with the user:

- [ ] What interface changes are needed
- [ ] Which behaviors to test (prioritize — you can't test everything)
- [ ] Interface design for testability (see below)
- [ ] A list of behaviors to test (not implementation steps)

Ask: "What should the public interface look like? Which behaviors are most important?"

### Step 2: Tracer bullet

Write ONE test that confirms ONE thing about the system:

```
RED:   Write test for first behavior → test fails (confirm it fails for the right reason)
GREEN: Write minimal code to pass → test passes
```

This is your tracer bullet — proves the end-to-end path works.

### Step 3: Incremental loop

For each remaining behavior:

```
RED:   Write next test → fails
GREEN: Minimal code to pass → passes
```

Rules:

- One test at a time
- Only enough code to pass the current test
- Don't anticipate future tests
- Keep tests on observable behavior, not internal state

### Step 4: Refactor

After all tests pass, look for:

- [ ] Duplicated logic to extract
- [ ] Shallow modules to deepen (move complexity behind simple interfaces)
- [ ] SOLID violations
- [ ] What the new code reveals about existing code

**Never refactor while RED.** Get to GREEN first, then clean up.

---

## Checklist Per Cycle

```
[ ] Test describes behavior, not implementation
[ ] Test uses public interface only
[ ] Test would survive internal refactor
[ ] Test fails for the right reason before implementation
[ ] Code is minimal for this test
[ ] No speculative features added
```

---

## Mocking Rules

Mock at **system boundaries only**:

- External APIs (payment, email, etc.)
- Databases (sometimes — prefer a test DB)
- Time and randomness
- File system (sometimes)

**Never mock your own modules or internal collaborators.** If you feel the urge to mock something you control, that's a signal to redesign the interface.

```typescript
// Testable: dependency injected
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// Hard to test: dependency created internally
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

---

## Interface Design for Testability

1. **Accept dependencies, don't create them**
2. **Return results, don't produce side effects**
3. **Small surface area** — fewer methods = fewer tests needed

---

## Review Summary

**Overall:** TDD only works if tests verify behavior, not implementation shape.

**Must address:**

- Tests that mock internal collaborators — these test the wrong thing
- Horizontal slicing — all tests written before any implementation

**Well done when:**

- Tests pass after a significant internal refactor
- Each test reads like a user story, not a function call log
