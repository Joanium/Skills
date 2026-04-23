---
name: ETL Incident Repair Validation Proofs
trigger: etl incident repair validation proofs, help with etl incident repair validation proofs, plan etl incident repair validation proofs, improve etl incident repair validation proofs, expert etl incident repair validation proofs
description: Expert-level guidance for etl incident repair validation proofs with action-oriented workflow, review criteria, and failure patterns.
---

ETL Incident Repair Validation Proofs is an expert database and migration skill for ETL Incident Repair. The focal concern is Validation Proofs, but the real objective is helping an AI change data structures and access paths without breaking trust, cost, or recovery.

## When To Use

- Use this when ETL Incident Repair Validation Proofs is changing a data surface that other people or systems depend on semantically, not just structurally.
- Use this when cutovers, backfills, or retention changes can create invisible downstream damage.
- Use this when database work needs stronger recovery and consumer-impact planning than SQL alone provides.
- Use this when trust in the data matters as much as technical success of the migration.

## Core Principles

- A migration is safe only when the old and new meanings are both understood.
- Validation should prove the semantic outcome, not merely that rows moved.
- Cutovers and backfills are product events for downstream consumers.
- Recovery and drift detection are part of every serious data change.
- Ownership and lineage make database changes survivable over time.

## Key Questions

- Which consumer of ETL Incident Repair Validation Proofs would be harmed first by semantic drift rather than outright failure?
- What recovery move for ETL Incident Repair Validation Proofs becomes hardest after the cutover begins?
- How will ETL Incident Repair Validation Proofs be validated if the data looks plausible but is subtly wrong?
- Where could ETL Incident Repair Validation Proofs create hidden cost spikes while technically succeeding?
- Which ownership boundary in ETL Incident Repair Validation Proofs is currently too vague for safe change management?

## Workflow

1. Clarify the semantic meaning, consumers, and reversibility constraints before designing the change.
2. Define migration windows, validation proofs, and recovery paths as one plan.
3. Model how drift, lag, anomalies, and consumer assumptions will be detected.
4. Connect structural changes to cost, lineage, and retention implications.
5. Exercise the change against bad-data, partial-cutover, and stale-consumer scenarios.
6. Record the new baseline so future AI work can evolve the data system from a stable contract.

## Artifacts

- A cutover and recovery plan for ETL Incident Repair Validation Proofs.
- A validation and drift-detection note for the semantic contract.
- A consumer-impact and ownership map.
- A lineage and cost checkpoint list for post-change monitoring.

## Tradeoffs

- Fast cutovers versus stronger reversibility.
- Cheaper queries versus clearer semantics.
- Aggressive cleanup versus downstream consumer stability.
- Shorter migrations versus better validation and reconciliation.

## Signals To Watch

- Consumer confusion or breakage after structurally successful migrations.
- Anomalies that escape because validation checked shape but not meaning.
- Lag, drift, or retention behavior diverging from the documented plan.
- Unexpected cost concentration after query or schema changes.
- Ownership disputes that surface only during recovery or rollback decisions.

## Review Checklist

- [ ] The meaning of ETL Incident Repair Validation Proofs is clearer than the implementation steps.
- [ ] Validation proves semantic correctness, not just structural completion.
- [ ] Recovery and rollback paths are real and time-bounded.
- [ ] Consumer impact and ownership are mapped.
- [ ] Drift, lag, and cost signals exist for the changed surface.
- [ ] Future AI work can extend the database shape without re-litigating its meaning.

## Common Failure Modes

- Treating data migration as a plumbing task instead of a semantic change.
- Validating row counts while downstream meaning quietly breaks.
- Ignoring recovery timing until the data has already drifted too far.
- Optimizing access paths while leaving ownership and lineage ambiguous.
