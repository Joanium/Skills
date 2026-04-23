---
name: Rust Test Harness Design
trigger: rust test harness design, help with rust test harness design, plan rust test harness design, improve rust test harness design, expert rust test harness design
description: Expert-level guidance for rust test harness design with domain-specific heuristics, workflow, review criteria, and failure patterns.
---

Rust Test Harness Design is an expert programming-language skill for Rust. The focal concern is Test Harness Design, but the real bar is production code that survives refactors, scale, and peer review.

## When To Use

- Use this when Rust Test Harness Design affects correctness, readability, and long-term maintainability in the same code path.
- Use this when language features are being used as style choices instead of deliberate design tools.
- Use this when the team needs sharper rules for debugging, testing, and evolving a language-specific codebase.
- Use this when performance or safety issues keep tracing back to avoidable language-level decisions.

## Core Principles

- Treat the language as a design constraint, not a syntax preference.
- The safest abstraction is the one the next engineer can still reason about under pressure.
- Typing, error flow, and concurrency choices should reduce ambiguity, not hide it.
- Debuggability and testability are first-class outcomes of good language design.
- Refactoring is cheaper when boundaries are explicit before the codebase gets busy.

## Key Questions

- What language feature is carrying the real complexity inside Rust Test Harness Design?
- Which abstraction in Rust Test Harness Design becomes harder to debug as the codebase grows?
- What runtime failure would reveal a weak design choice in Rust Test Harness Design first?
- How will Rust Test Harness Design behave when multiple contributors evolve it independently?
- Which part of Rust Test Harness Design is optimized for elegance instead of team comprehension?

## Workflow

1. Identify the language-level decision that most strongly shapes maintainability or runtime behavior.
2. Map the boundary where types, errors, state, or concurrency stop being obvious.
3. Write the smallest example that proves the desired behavior and the most dangerous counterexample.
4. Choose conventions that make debugging and refactoring cheaper, not merely shorter to write.
5. Review the code under change pressure: extension, rollback, instrumentation, and testing.
6. Document the resulting pattern so the next engineer can apply it without folklore.

## Artifacts

- A minimal before-and-after code sample for Rust Test Harness Design.
- A failure-mode note that explains the sharp edges inside Rust Test Harness Design.
- A test or benchmark scaffold that keeps the pattern honest.
- A review note explaining why the chosen language-level tradeoff is worth it.

## Tradeoffs

- Expressiveness versus readability under mixed experience levels.
- Strictness versus iteration speed during early implementation.
- Runtime efficiency versus instrumentation and debuggability.
- Language idioms versus portability across teams and toolchains.

## Signals To Watch

- Defect patterns traceable to typing, mutation, concurrency, or packaging choices.
- Time to isolate language-specific bugs in normal debugging sessions.
- Refactor success rate without collateral breakage.
- Benchmark drift after supposedly local changes.
- Review churn caused by unclear idioms or unsafe shortcuts.

## Review Checklist

- [ ] The main language-level risk in Rust Test Harness Design is named explicitly.
- [ ] The code path is understandable without relying on cleverness.
- [ ] Failure behavior can be reproduced and tested.
- [ ] Tooling, tests, and debugging support the chosen pattern.
- [ ] Future contributors can extend Rust Test Harness Design without reverse-engineering hidden contracts.
- [ ] The pattern is documented well enough to survive team turnover.

## Common Failure Modes

- Using advanced language features to compress code while expanding ambiguity.
- Treating refactor safety as something tests might cover later.
- Debugging workflows that depend on personal intuition instead of structure.
- Optimizing micro-performance before fixing semantic confusion.
