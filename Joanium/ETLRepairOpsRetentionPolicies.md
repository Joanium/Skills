---
name: ETL Repair Operations Retention Policies
trigger: etl repair operations retention policies, help with etl repair operations retention policies, plan etl repair operations retention policies, improve etl repair operations retention policies, expert etl repair operations retention policies
description: Expert-level guidance for etl repair operations retention policies with action-oriented workflow, review criteria, and failure patterns.
---

ETL Repair Operations Retention Policies is an expert data and analytics skill for ETL Repair Operations. The focal concern is Retention Policies, but the real objective is helping an AI produce data systems and analysis that remain trustworthy when definitions, sources, and consumers all evolve.

## When To Use

- Use this when ETL Repair Operations Retention Policies needs stronger semantics, validation, and consumer awareness than a working query or pipeline alone can provide.
- Use this when the AI is producing analyses or data changes that other teams will depend on.
- Use this when dashboards, metrics, or pipelines are vulnerable to silent semantic drift.
- Use this when cost, freshness, and trust have to be managed together.

## Core Principles

- A trusted metric is a social contract backed by technical discipline.
- Backfills, cutovers, and repairs are product events for downstream consumers.
- Freshness without reconciliation can still produce wrong confidence.
- The cost model of data work matters because expensive truth is often unactionable truth.
- The best analysis is one future analysts can reinterpret safely.

## Key Questions

- What part of ETL Repair Operations Retention Policies would two consumers interpret differently if nothing were documented?
- Which anomaly in ETL Repair Operations Retention Policies is most likely to be ignored until it becomes a business argument?
- How would ETL Repair Operations Retention Policies be repaired if the source data arrived late, duplicated, or wrong?
- What cost pattern in ETL Repair Operations Retention Policies is growing because nobody owns the semantic boundary?
- Which downstream decision is too fragile for ETL Repair Operations Retention Policies to remain loosely defined?

## Workflow

1. Clarify the business meaning, the consumers, and the decisions the data will influence.
2. Define semantic expectations, validation rules, and repair paths before making structural changes.
3. Stress the analysis or pipeline with late data, duplicated data, and cutover scenarios.
4. Connect query efficiency and warehouse cost back to the value of the output.
5. Review how consumers will detect and react to drift in freshness, meaning, or completeness.
6. Leave behind a contract strong enough that the next AI pass can extend the work safely.

## Artifacts

- A semantic contract for ETL Repair Operations Retention Policies.
- A reconciliation and repair note for risky data paths.
- A consumer impact summary for changes in meaning or structure.
- A freshness, validation, and cost monitoring sketch.

## Tradeoffs

- Fast analytical iteration versus semantic discipline.
- Cheaper storage or compute versus easier future interpretation.
- Fresher data versus stronger reconciliation guarantees.
- Flexible queries versus reusable governed definitions.

## Signals To Watch

- Metric disputes caused by unclear definitions or hidden transformations.
- Time to detect and repair bad or late data.
- Warehouse or query cost drifting away from analytical value.
- Consumer breakage after schema or meaning changes.
- Dashboard confidence that persists despite stale or inconsistent inputs.

## Review Checklist

- [ ] The meaning of ETL Repair Operations Retention Policies is explicit and consumer-facing.
- [ ] Validation and repair paths exist for realistic data failure modes.
- [ ] Consumer impact is part of the change design.
- [ ] Freshness, reconciliation, and cost are all observable.
- [ ] The analysis or pipeline can survive schema and source evolution.
- [ ] Future AI work can build on a stable semantic baseline.

## Common Failure Modes

- Publishing numbers before publishing their meaning.
- Repairing data pipelines without repairing consumer trust.
- Treating dashboard freshness as equivalent to data correctness.
- Optimizing query speed while leaving the semantic contract undefined.
