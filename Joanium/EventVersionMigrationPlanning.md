---
name: Event Version Migration Planning
trigger: event version migration planning, help with event version migration planning, plan event version migration planning, improve event version migration planning, expert event version migration planning
description: Expert-level guidance for event version migration planning, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Event Version Migration Planning is an expert-level data systems skill for turning analysis and pipelines into governed, trusted, and operationally stable assets. The emphasis here is sequencing work, dependencies, and proof points so execution moves quickly without creating blind risk.

## When To Use

- Use this when Event Version Migration Planning affects downstream metrics, decisions, or customer-facing data products.
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

- What must be true before Event Version Migration Planning can start safely?
- Which dependency has the highest chance of slipping or changing?
- What is the smallest milestone that proves the plan is still viable?
- Which tasks can proceed in parallel without creating integration debt?
- What contingency path exists if the primary plan stalls?

## Workflow

1. Define scope, exclusions, and the readiness threshold for starting.
2. Break the work into milestones that each reduce a specific risk.
3. Map dependencies, handoffs, and decision points that can block flow.
4. Assign owners, due dates, and readiness criteria for every milestone.
5. Add contingency options for likely slips, blocked work, or invalidated assumptions.
6. Run a standing replanning loop based on evidence, not calendar optimism.

## Deliverables

- A milestone plan for Event Version Migration Planning with explicit gating criteria.
- A dependency map showing blockers, handoffs, and critical path items.
- A contingency and rollback map for the most likely plan failures.
- A status model that distinguishes risk, delay, and readiness clearly.

## Tradeoffs

- Aggressive deadlines versus quality of risk reduction.
- Parallel execution versus coordination overhead.
- Detailed planning upfront versus adaptive replanning.
- Local team efficiency versus cross-team synchronization.

## Signals To Watch

- Freshness, completeness, and reconciliation pass rate for critical datasets.
- Metric drift versus source-of-truth calculations.
- Schema change failure rate and downstream breakage count.
- Adoption of certified definitions versus ad hoc forks.
- Warehouse cost by workload, consumer, and retention tier.

## Review Checklist

- [ ] Scope and exclusions are documented.
- [ ] Critical path items are visible and owned.
- [ ] Every milestone has a proof point, not just a date.
- [ ] Contingencies exist for the top risks.
- [ ] Status reporting distinguishes signal from optimism.
- [ ] The plan can survive one major assumption being wrong.

## Common Failure Modes

- Plans that track tasks but not risk reduction.
- Dependencies hidden until the week they block delivery.
- Milestones defined by effort spent rather than proof gained.
- No contingency path when assumptions fail.
