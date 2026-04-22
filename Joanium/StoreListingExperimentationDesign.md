---
name: Store Listing Experimentation Design
trigger: store listing experimentation design, help with store listing experimentation design, plan store listing experimentation design, improve store listing experimentation design, expert store listing experimentation design
description: Expert-level guidance for store listing experimentation design, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Store Listing Experimentation Design is an expert-level client platform skill for shipping resilient mobile or desktop behavior across devices, stores, networks, and operating-system constraints. The emphasis here is on interfaces, invariants, failure handling, and why one structure is safer than its alternatives.

## When To Use

- Use this when Store Listing Experimentation Design affects release risk, device behavior, or user trust during degraded conditions.
- Use this when platform restrictions or background execution rules shape the design.
- Use this when telemetry needs to explain failures that cannot be reproduced locally.
- Use this when crash, battery, or network issues demand a stronger operating model than feature-by-feature fixes.

## Core Principles

- Platform constraints should shape the architecture before implementation debt accumulates.
- Release quality depends on telemetry, rollback options, and operator clarity.
- Offline and degraded states are part of the product, not edge cases.
- Device diversity should be treated as a planning input, not a testing afterthought.
- User trust is lost faster on client platforms because failures feel personal and immediate.

## Decision Questions

- What are the core boundaries, contracts, and invariants in Store Listing Experimentation Design?
- Which failure modes should be absorbed, and which should surface immediately?
- How will the design evolve without breaking consumers or operators?
- Where is coupling acceptable, and where is it too expensive?
- What assumptions does the design make about scale, behavior, or inputs?

## Workflow

1. Clarify requirements, non-goals, and the constraints that shape the design.
2. Map the boundary diagram, responsibilities, and trust or data flows.
3. Define contracts, state transitions, and invariants that must hold.
4. Design failure handling, fallback behavior, and operability hooks.
5. Stress the design against realistic scenarios, edge cases, and growth patterns.
6. Review the tradeoffs, migration path, and reversibility before adoption.

## Deliverables

- An architecture or boundary diagram for Store Listing Experimentation Design.
- A contract or state model that captures invariants explicitly.
- A migration and compatibility sketch for affected consumers.
- A tradeoff record describing why this design beat the alternatives.

## Tradeoffs

- Modularity versus coordination overhead.
- Strict contracts versus flexibility of change.
- Simplicity now versus extensibility later.
- Immediate performance versus debuggability and safety.

## Signals To Watch

- Crash-free sessions, ANR or hang rate, and fatal signal concentration.
- Battery, network, and storage impact by feature or build channel.
- Release adoption curve and rollback or hotfix frequency.
- Store review trends and support volume after targeted changes.
- Task completion rate under degraded connectivity or background constraints.

## Review Checklist

- [ ] Boundaries and responsibilities are explicit.
- [ ] Invariants are named and testable.
- [ ] Failure handling is designed, not implied.
- [ ] Compatibility and migration are addressed.
- [ ] The design was tested against realistic scenarios.
- [ ] Rejected alternatives are captured honestly.

## Common Failure Modes

- Designs that describe components but not their contracts.
- No explanation of failure behavior or degraded mode.
- Coupling hidden behind convenience abstractions.
- Migration concerns deferred until implementation is underway.
