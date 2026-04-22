---
name: Fact Modeling Grain Design
trigger: fact modeling grain design, help with fact modeling grain design, plan fact modeling grain design, improve fact modeling grain design, expert fact modeling grain design
description: Expert-level guidance for fact modeling grain design, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Fact Modeling Grain Design is an expert-level data systems skill for turning analysis and pipelines into governed, trusted, and operationally stable assets. The emphasis here is on interfaces, invariants, failure handling, and why one structure is safer than its alternatives.

## When To Use

- Use this when Fact Modeling Grain Design affects downstream metrics, decisions, or customer-facing data products.
- Use this when schemas, lineage, or quality expectations need to survive team and tool changes.
- Use this when backfills, migrations, or new data products risk breaking shared definitions.
- Use this when trust in the data is low and consumers need a stronger operating contract.

## Core Principles

- Shared definitions are more valuable than local convenience.
- Every important metric needs lineage, ownership, and a validation story.
- Model data around decisions and entities, not only source-system tables.
- Backfills and migrations are product changes, not mere pipeline chores.
- Trust is built by reconciling deltas, freshness, and semantic intent together.

## Decision Questions

- What are the core boundaries, contracts, and invariants in Fact Modeling Grain Design?
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

- An architecture or boundary diagram for Fact Modeling Grain Design.
- A contract or state model that captures invariants explicitly.
- A migration and compatibility sketch for affected consumers.
- A tradeoff record describing why this design beat the alternatives.

## Tradeoffs

- Modularity versus coordination overhead.
- Strict contracts versus flexibility of change.
- Simplicity now versus extensibility later.
- Immediate performance versus debuggability and safety.

## Signals To Watch

- Freshness, completeness, and reconciliation pass rate for critical datasets.
- Metric drift versus source-of-truth calculations.
- Schema change failure rate and downstream breakage count.
- Adoption of certified definitions versus ad hoc forks.
- Warehouse cost by workload, consumer, and retention tier.

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
