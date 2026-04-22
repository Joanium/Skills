---
name: Accessibility Risk Scoring Operations
trigger: accessibility risk scoring operations, help with accessibility risk scoring operations, plan accessibility risk scoring operations, improve accessibility risk scoring operations, expert accessibility risk scoring operations
description: Expert-level guidance for accessibility risk scoring operations, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Accessibility Risk Scoring Operations is an expert-level frontend skill for making client behavior understandable, resilient, and consistent across design and engineering. The emphasis here is repeatable day-two execution under real load, incomplete information, and ordinary human error.

## When To Use

- Use this when Accessibility Risk Scoring Operations shapes user trust through responsiveness, clarity, or failure handling.
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

- What are the recurring operational decisions inside Accessibility Risk Scoring Operations?
- Which alerts or dashboards should trigger human action, and which should not?
- What information does the operator need in the first five minutes?
- Where are handoffs likely to fail during rotation changes or incidents?
- Which manual steps are risky enough to automate or heavily constrain?

## Workflow

1. Map the steady-state workflows, alert sources, and operator decision tree.
2. Define the minimum context, dashboards, and commands needed to act safely.
3. Write the runbook for common cases, degraded cases, and escalation triggers.
4. Test the handoff path across roles, rotations, and time zones.
5. Run drills to validate the operational model under time pressure.
6. Use incident and toil data to remove fragile manual paths.

## Deliverables

- A runbook for Accessibility Risk Scoring Operations covering routine and degraded modes.
- An alert map with severity, owner, and first action.
- A handoff template for cross-team or on-call transitions.
- A toil reduction backlog driven by repeated operator pain.

## Tradeoffs

- Operator flexibility versus procedural safety.
- Automation speed versus recoverability when automation fails.
- Local expertise versus portable runbooks.
- Rich dashboards versus cognitive overload during incidents.

## Signals To Watch

- Interaction latency, visual stability, and completion rate for key journeys.
- Client-side error rate and recovery success without hard refresh.
- Accessibility regression count and unresolved severity.
- Cross-browser defect rate and device-class skew.
- Support tickets or session replays linked to the targeted journey.

## Review Checklist

- [ ] Operators can identify first actions quickly.
- [ ] Alerts map to decisions, not mere observations.
- [ ] Runbooks cover degraded and ambiguous cases.
- [ ] Handoffs are documented and practiced.
- [ ] Manual steps with high blast radius are constrained.
- [ ] Toil data feeds improvement work.

## Common Failure Modes

- Runbooks that assume the original author is online.
- Alerts with no clear next action.
- Operational steps that rely on tribal memory.
- Too much automation without a recovery path when automation fails.
