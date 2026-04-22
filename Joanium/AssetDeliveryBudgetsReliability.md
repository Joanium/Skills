---
name: Asset Delivery Budgets Reliability
trigger: asset delivery budgets reliability, help with asset delivery budgets reliability, plan asset delivery budgets reliability, improve asset delivery budgets reliability, expert asset delivery budgets reliability
description: Expert-level guidance for asset delivery budgets reliability, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Asset Delivery Budgets Reliability is an expert-level frontend skill for making client behavior understandable, resilient, and consistent across design and engineering. The emphasis here is designing graceful degradation, recovery paths, and explicit reliability targets before the system is stressed.

## When To Use

- Use this when Asset Delivery Budgets Reliability shapes user trust through responsiveness, clarity, or failure handling.
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

- What are the most likely and most damaging failure modes in Asset Delivery Budgets Reliability?
- Which failures can be masked, and which require explicit user or operator visibility?
- What is the recovery objective for time, data loss, and trust impact?
- How will the team know the system is leaving its safe operating envelope?
- Which dependencies make reliability contingent on someone elses behavior?

## Workflow

1. Define the reliability targets, assumptions, and allowed degradation behavior.
2. Enumerate failure modes across dependencies, operators, data, and environment.
3. Design fallback paths, recovery procedures, and state repair options.
4. Instrument early detection and clear escalation criteria.
5. Test failure handling with drills, chaos cases, or targeted simulation.
6. Review incidents and near misses to update the reliability model.

## Deliverables

- A failure mode catalog for Asset Delivery Budgets Reliability.
- A target matrix for availability, recovery, and data durability.
- A documented fallback and repair procedure.
- A drill or fault-injection plan for the critical risks.

## Tradeoffs

- Higher reliability versus delivery speed and cost.
- Automatic recovery versus operator control.
- Strict consistency versus availability during failures.
- Redundancy versus complexity and drift risk.

## Signals To Watch

- Interaction latency, visual stability, and completion rate for key journeys.
- Client-side error rate and recovery success without hard refresh.
- Accessibility regression count and unresolved severity.
- Cross-browser defect rate and device-class skew.
- Support tickets or session replays linked to the targeted journey.

## Review Checklist

- [ ] Reliability targets are explicit.
- [ ] Failure modes cover dependencies and operator error.
- [ ] Degraded behavior is designed and communicated.
- [ ] Detection and escalation paths are defined.
- [ ] Recovery procedures are tested, not hypothetical.
- [ ] Near misses feed the reliability model.

## Common Failure Modes

- Reliability work that only adds redundancy without recovery clarity.
- No degraded mode, forcing binary success or total failure.
- Targets stated without instrumentation to measure them.
- Assuming dependencies will be reliable enough by default.
