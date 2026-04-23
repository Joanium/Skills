---
name: Airflow Security Controls
trigger: airflow security controls, help with airflow security controls, plan airflow security controls, improve airflow security controls, expert airflow security controls
description: Expert-level guidance for airflow security controls with domain-specific heuristics, workflow, review criteria, and failure patterns.
---

Airflow Security Controls is an expert data-systems skill for Airflow. The focal concern is Security Controls, but the real bar is trustworthy data that survives scale, handoffs, and semantic drift.

## When To Use

- Use this when Airflow Security Controls affects a shared data surface where semantics, freshness, or cost matter as much as raw correctness.
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

- What semantic confusion would Airflow Security Controls create if two teams interpreted it differently?
- Which recovery path for Airflow Security Controls is the least understood today?
- How will Airflow Security Controls behave under backfills, reprocessing, or delayed sources?
- What cost pattern in Airflow Security Controls is growing silently because no one owns the boundary?
- Which consumer would fail first if the data contract inside Airflow Security Controls drifted subtly?

## Workflow

1. Define the business meaning, owners, and downstream consumers before touching implementation.
2. Model the grain, lineage, and freshness expectations explicitly.
3. Stress the design with backfills, delayed sources, partial migrations, and repair operations.
4. Review security, access, and retention decisions together with cost and performance.
5. Instrument trust signals that reveal bad data before dashboards quietly adapt.
6. Capture the final contract so future work does not re-litigate the meaning of {0}.

## Artifacts

- A semantic contract note for Airflow Security Controls.
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

- [ ] The meaning of Airflow Security Controls is written in language consumers will actually use.
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
