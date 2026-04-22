---
name: Service Dependency Mapping Planning
trigger: service dependency mapping planning, help with service dependency mapping planning, plan service dependency mapping planning, improve service dependency mapping planning, expert service dependency mapping planning
description: Expert-level guidance for service dependency mapping planning, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Service Dependency Mapping Planning is an expert-level infrastructure skill for reducing operational risk while keeping rollout control, recovery, and ownership explicit. The emphasis here is sequencing work, dependencies, and proof points so execution moves quickly without creating blind risk.

## When To Use

- Use this when Service Dependency Mapping Planning changes service availability, deployment safety, or recovery behavior.
- Use this when multiple services, regions, or operators need a shared operating model.
- Use this when hidden dependencies or high blast radius make informal rollout decisions unsafe.
- Use this when production incidents show that the current control plane is too implicit.

## Core Principles

- Blast radius should be designed and limited before the first rollout step.
- Recovery is part of the design, not an appendix after launch.
- Operational ownership must be obvious under time pressure.
- Automate the checks humans are most likely to skip when stressed.
- Prefer progressive exposure over all-at-once change when the system is not yet proven.

## Decision Questions

- What must be true before Service Dependency Mapping Planning can start safely?
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

- A milestone plan for Service Dependency Mapping Planning with explicit gating criteria.
- A dependency map showing blockers, handoffs, and critical path items.
- A contingency and rollback map for the most likely plan failures.
- A status model that distinguishes risk, delay, and readiness clearly.

## Tradeoffs

- Aggressive deadlines versus quality of risk reduction.
- Parallel execution versus coordination overhead.
- Detailed planning upfront versus adaptive replanning.
- Local team efficiency versus cross-team synchronization.

## Signals To Watch

- Change failure rate and mean time to recovery after rollout issues.
- Rollback success rate and the time needed to restore steady state.
- Error budget burn and saturation during deployments or failovers.
- Alert quality: noise rate, missing coverage, and acknowledgement delays.
- Configuration drift, dependency skew, and recovery drill pass rate.

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
