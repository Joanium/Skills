---
name: Background Execution Limits Planning
trigger: background execution limits planning, help with background execution limits planning, plan background execution limits planning, improve background execution limits planning, expert background execution limits planning
description: Expert-level guidance for background execution limits planning, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Background Execution Limits Planning is an expert-level client platform skill for shipping resilient mobile or desktop behavior across devices, stores, networks, and operating-system constraints. The emphasis here is sequencing work, dependencies, and proof points so execution moves quickly without creating blind risk.

## When To Use

- Use this when Background Execution Limits Planning affects release risk, device behavior, or user trust during degraded conditions.
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

- What must be true before Background Execution Limits Planning can start safely?
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

- A milestone plan for Background Execution Limits Planning with explicit gating criteria.
- A dependency map showing blockers, handoffs, and critical path items.
- A contingency and rollback map for the most likely plan failures.
- A status model that distinguishes risk, delay, and readiness clearly.

## Tradeoffs

- Aggressive deadlines versus quality of risk reduction.
- Parallel execution versus coordination overhead.
- Detailed planning upfront versus adaptive replanning.
- Local team efficiency versus cross-team synchronization.

## Signals To Watch

- Crash-free sessions, ANR or hang rate, and fatal signal concentration.
- Battery, network, and storage impact by feature or build channel.
- Release adoption curve and rollback or hotfix frequency.
- Store review trends and support volume after targeted changes.
- Task completion rate under degraded connectivity or background constraints.

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
