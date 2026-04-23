---
name: Contract Testing Operations Triage Heuristics
trigger: contract testing operations triage heuristics, help with contract testing operations triage heuristics, plan contract testing operations triage heuristics, improve contract testing operations triage heuristics, expert contract testing operations triage heuristics
description: Expert-level guidance for contract testing operations triage heuristics with action-oriented workflow, review criteria, and failure patterns.
---

Contract Testing Operations Triage Heuristics is an expert testing and quality skill for Contract Testing Operations. The focal concern is Triage Heuristics, but the real objective is helping an AI create evidence that code is correct under change, not merely green under ideal conditions.

## When To Use

- Use this when Contract Testing Operations Triage Heuristics needs to prove behavior under realistic change and failure conditions rather than just increase test count.
- Use this when the AI must decide what kind of evidence is persuasive for a risky code path.
- Use this when flakiness, shallow assertions, or unrealistic fixtures are hiding genuine uncertainty.
- Use this when quality work has to guide engineering decisions instead of trailing them.

## Core Principles

- A useful test explains behavior; it does not merely reenact implementation.
- Coverage without a good oracle creates false confidence.
- Determinism is part of test design, not a bonus attribute.
- The right fixture reveals system behavior instead of masking it with convenience.
- A failing test should teach the AI where to look next.

## Key Questions

- What uncertainty inside Contract Testing Operations Triage Heuristics is still untested even if coverage looks healthy?
- Which assertion in Contract Testing Operations Triage Heuristics would stay green while the user-visible behavior regressed?
- How much of Contract Testing Operations Triage Heuristics depends on mocks, fixtures, or timing assumptions that may be lying?
- What test failure pattern would be most actionable for a future AI debugging pass?
- Where does Contract Testing Operations Triage Heuristics need stronger negative cases rather than more positive cases?

## Workflow

1. Start from the behavior that must be protected and the failure that would matter most.
2. Choose the smallest test level that can still reveal the right kind of truth.
3. Design fixtures, mocks, and timing controls so they expose the system rather than sanitize it.
4. Add edge, boundary, and failure cases that challenge the main claim behind the code.
5. Make the output of the test suite useful for diagnosis, not just pass or fail.
6. Review the resulting coverage as an evidence map rather than a vanity metric.

## Artifacts

- A behavior protection map for Contract Testing Operations Triage Heuristics.
- A test design note covering fixtures, timing, and oracle choice.
- A failure matrix for the important negative scenarios.
- A triage guide for what failing signals in Contract Testing Operations Triage Heuristics should mean.

## Tradeoffs

- Fast feedback versus realism of system behavior.
- Deep integration coverage versus isolation of root causes.
- Heavy fixtures versus maintainable tests.
- Broad coverage counts versus high-signal assertions.

## Signals To Watch

- Rate of regressions escaping despite passing tests.
- Flake frequency and time lost to reruns or distrust.
- Diagnosis speed after a meaningful test failure.
- Maintenance churn caused by brittle or overcoupled tests.
- Coverage areas that remain blind to boundary or failure conditions.

## Review Checklist

- [ ] The key behavior protected by Contract Testing Operations Triage Heuristics is explicit.
- [ ] The test level matches the uncertainty being addressed.
- [ ] Fixtures, timing, and mocks are disciplined enough to stay trustworthy.
- [ ] Failure cases are represented, not implied.
- [ ] A future AI can tell what a failing result actually means.
- [ ] The suite increases confidence instead of merely increasing count.

## Common Failure Modes

- Writing tests that mirror implementation details and collapse during refactors.
- Using mocks so aggressively that system behavior is no longer visible.
- Chasing coverage numbers while boundary conditions remain untested.
- Ignoring flake patterns until the suite trains engineers to distrust it.
