---
name: Reliability Review Boards Design
trigger: reliability review boards design, help with reliability review boards design, plan reliability review boards design, improve reliability review boards design, expert reliability review boards design
description: Expert-level guidance for reliability review boards design, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Reliability Review Boards Design is an expert-level engineering systems skill for making architecture, standards, and change management explicit enough to scale beyond individual memory. The emphasis here is on interfaces, invariants, failure handling, and why one structure is safer than its alternatives.

## When To Use

- Use this when Reliability Review Boards Design affects codebase shape, team interfaces, or long-term delivery speed.
- Use this when unspoken standards or ownership gaps are causing repeated waste.
- Use this when migrations need structure so they can finish without destabilizing the platform.
- Use this when local optimizations are starting to damage cross-team coherence.

## Core Principles

- Incremental evolution usually beats dramatic rewrites under uncertainty.
- Standards only work when exceptions are explicit and reviewable.
- Ownership should be visible in the code, tooling, and review paths.
- Compatibility rules need to be designed before change volume rises.
- Architecture quality is measured by how teams change the system, not only by diagrams.

## Decision Questions

- What are the core boundaries, contracts, and invariants in Reliability Review Boards Design?
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

- An architecture or boundary diagram for Reliability Review Boards Design.
- A contract or state model that captures invariants explicitly.
- A migration and compatibility sketch for affected consumers.
- A tradeoff record describing why this design beat the alternatives.

## Tradeoffs

- Modularity versus coordination overhead.
- Strict contracts versus flexibility of change.
- Simplicity now versus extensibility later.
- Immediate performance versus debuggability and safety.

## Signals To Watch

- Lead time, change failure rate, and rollback frequency.
- Policy compliance drift and exception backlog size.
- Dependency graph health, ownership clarity, and orphaned modules.
- Test determinism, flake rate, and review rework caused by unclear standards.
- Migration throughput versus the amount of legacy surface retired.

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
