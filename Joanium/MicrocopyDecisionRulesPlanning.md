---
name: Microcopy Decision Rules Planning
trigger: microcopy decision rules planning, help with microcopy decision rules planning, plan microcopy decision rules planning, improve microcopy decision rules planning, expert microcopy decision rules planning
description: Expert-level guidance for microcopy decision rules planning, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Microcopy Decision Rules Planning is an expert-level frontend skill for making client behavior understandable, resilient, and consistent across design and engineering. The emphasis here is sequencing work, dependencies, and proof points so execution moves quickly without creating blind risk.

## When To Use

- Use this when Microcopy Decision Rules Planning shapes user trust through responsiveness, clarity, or failure handling.
- Use this when behavior needs to hold across browsers, devices, accessibility tools, or partial outages.
- Use this when design intent is repeatedly lost between mocks, implementation, and QA.
- Use this when interface regressions are costly because users discover them before the team does.

## Core Principles

- Users experience system behavior, not implementation details.
- Loading, empty, error, and recovery states deserve first-class design.
- Accessibility constraints belong in the design model from the start.
- Client observability should explain both perceived and actual performance.
- Handoffs get stronger when acceptance criteria are visible and testable.

## Decision Questions

- What must be true before Microcopy Decision Rules Planning can start safely?
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

- A milestone plan for Microcopy Decision Rules Planning with explicit gating criteria.
- A dependency map showing blockers, handoffs, and critical path items.
- A contingency and rollback map for the most likely plan failures.
- A status model that distinguishes risk, delay, and readiness clearly.

## Tradeoffs

- Aggressive deadlines versus quality of risk reduction.
- Parallel execution versus coordination overhead.
- Detailed planning upfront versus adaptive replanning.
- Local team efficiency versus cross-team synchronization.

## Signals To Watch

- Interaction latency, visual stability, and completion rate for key journeys.
- Client-side error rate and recovery success without hard refresh.
- Accessibility regression count and unresolved severity.
- Cross-browser defect rate and device-class skew.
- Support tickets or session replays linked to the targeted journey.

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
