---
name: MySQL Query Profiling
trigger: mysql query profiling, help with mysql query profiling, plan mysql query profiling, improve mysql query profiling, expert mysql query profiling
description: Expert-level guidance for mysql query profiling with domain-specific heuristics, workflow, review criteria, and failure patterns.
---

MySQL Query Profiling is an expert data-systems skill for MySQL. The focal concern is Query Profiling, but the real bar is trustworthy data that survives scale, handoffs, and semantic drift.

## When To Use

- Use this when MySQL Query Profiling affects a shared data surface where semantics, freshness, or cost matter as much as raw correctness.
- Use this when the system is accumulating tables, topics, or workflows faster than the data contract is keeping up.
- Use this when migrations and backfills are likely to surprise downstream consumers.
- Use this when the team needs stronger reasoning about lineage, trust, and recovery.

## Core Principles

- The hardest data problem is usually semantic, not syntactic.
- Schema changes are product changes for every downstream consumer.
- Cost, freshness, and correctness should be reviewed together.
- Recovery is part of the data design because bad data is harder to undo than bad code.
- A good model reduces analysis ambiguity before it speeds up querying.

## Key Questions

- What semantic confusion would MySQL Query Profiling create if two teams interpreted it differently?
- Which recovery path for MySQL Query Profiling is the least understood today?
- How will MySQL Query Profiling behave under backfills, reprocessing, or delayed sources?
- What cost pattern in MySQL Query Profiling is growing silently because no one owns the boundary?
- Which consumer would fail first if the data contract inside MySQL Query Profiling drifted subtly?

## Workflow

1. Define the business meaning, owners, and downstream consumers before touching implementation.
2. Model the grain, lineage, and freshness expectations explicitly.
3. Stress the design with backfills, delayed sources, partial migrations, and repair operations.
4. Review security, access, and retention decisions together with cost and performance.
5. Instrument trust signals that reveal bad data before dashboards quietly adapt.
6. Capture the final contract so future work does not re-litigate the meaning of {0}.

## Artifacts

- A semantic contract note for MySQL Query Profiling.
- A lineage and failure-recovery sketch for the critical paths.
- A migration or backfill plan with validation steps.
- A cost and trust dashboard definition tied to the chosen pattern.

## Tradeoffs

- Model clarity versus storage or compute efficiency.
- Freshness versus recovery safety and cost.
- Flexibility of schema versus durability of shared meaning.
- Fast migrations versus confidence in reconciliation.

## Signals To Watch

- Freshness, completeness, and reconciliation pass rate.
- Consumer breakage or semantic drift after changes.
- Query cost, storage growth, and workload concentration.
- Recovery success after delayed, duplicated, or bad upstream data.
- Security or access exceptions that bypass the intended model.

## Review Checklist

- [ ] The meaning of MySQL Query Profiling is written in language consumers will actually use.
- [ ] Schema, lineage, and grain are explicit.
- [ ] Migration and recovery paths are designed, not implied.
- [ ] Cost and trust signals exist for the critical path.
- [ ] Consumer impact was considered before implementation.
- [ ] Future changes can be reviewed against a stable semantic baseline.

## Common Failure Modes

- Treating schema shape as the data contract while meaning drifts underneath.
- Shipping backfills or migrations without a reconciliation story.
- Optimizing queries while ignoring cost concentration and access risk.
- Assuming consumers will notice subtle semantic drift before it spreads.
