---
name: Modular Monoliths Migration Seams
trigger: modular monoliths migration seams, help with modular monoliths migration seams, plan modular monoliths migration seams, improve modular monoliths migration seams, expert modular monoliths migration seams
description: Expert-level guidance for modular monoliths migration seams with action-oriented workflow, review criteria, and failure patterns.
---

Modular Monoliths Migration Seams is an expert architecture and systems skill for Modular Monoliths. The focal concern is Migration Seams, but the real objective is helping an AI reason about boundaries, failure paths, and evolution before the system gets too expensive to change.

## When To Use

- Use this when Modular Monoliths Migration Seams needs stronger reasoning about boundaries, contracts, and failure before implementation momentum hides the real tradeoffs.
- Use this when the AI is proposing structural change rather than a local patch.
- Use this when the hardest question is how the system evolves, not how a single component works today.
- Use this when operators, downstream teams, or long-lived data make architectural mistakes expensive.

## Core Principles

- A clean boundary is a cost-control mechanism, not just an aesthetic preference.
- Failure paths need architectural status equal to success paths.
- Migration seams should be designed before the migration is urgent.
- Ownership has to be visible in interfaces, data, and operations.
- A good architecture can explain how it will change without collapsing.

## Key Questions

- What part of Modular Monoliths Migration Seams becomes ambiguous when the system is stressed, scaled, or reorganized?
- Which dependency in Modular Monoliths Migration Seams is currently cheap only because the bill has not arrived yet?
- How would Modular Monoliths Migration Seams be migrated if the current assumption proved wrong in six months?
- Where is ownership inside Modular Monoliths Migration Seams too fuzzy for operators or adjacent teams?
- What failure mode would reveal the weakest architectural tradeoff first?

## Workflow

1. Clarify the problem, non-goals, and the long-term change pressure acting on the system.
2. Map boundaries, contracts, state transitions, and ownership explicitly.
3. Pressure-test the design against scale, failure, migration, and partial rollout scenarios.
4. Make the tradeoffs legible enough that a reviewer can disagree precisely.
5. Add operability hooks and failure budgets before the design is considered complete.
6. Capture the resulting model so future AI work can extend rather than undo it.

## Artifacts

- A boundary and ownership diagram for Modular Monoliths Migration Seams.
- A contract note covering failure semantics and migration concerns.
- A tradeoff record that names rejected alternatives honestly.
- An operability checklist tied to the design???s risky paths.

## Tradeoffs

- Local simplicity versus global flexibility.
- Immediate delivery speed versus future migration cost.
- Tighter contracts versus easier short-term iteration.
- Redundancy and resilience versus system complexity.

## Signals To Watch

- Frequency of architectural changes that break downstream assumptions.
- Operational confusion caused by unclear ownership or weak hooks.
- Migration difficulty when contracts or data boundaries shift.
- Hot spots or bottlenecks concentrated at poorly chosen boundaries.
- Reviewer disagreement caused by implicit rather than explicit tradeoffs.

## Review Checklist

- [ ] The key boundaries inside Modular Monoliths Migration Seams are explicit and justified.
- [ ] Failure and migration behavior are designed, not deferred.
- [ ] Ownership is visible in interfaces, data, and operations.
- [ ] Reviewers can evaluate the real tradeoffs rather than guess them.
- [ ] Operability exists for the failure paths that matter.
- [ ] The design can evolve without rewriting its core assumptions immediately.

## Common Failure Modes

- Creating boundaries that look clean in diagrams but dissolve in operations.
- Deferring migration concerns until the system is too entangled to move safely.
- Treating contract ambiguity as flexibility.
- Designing for average load while ignoring average failure.
