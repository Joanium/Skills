---
name: Failure Domain Isolation Operations
trigger: failure domain isolation operations, help with failure domain isolation operations, plan failure domain isolation operations, improve failure domain isolation operations, expert failure domain isolation operations
description: Expert-level guidance for failure domain isolation operations, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Failure Domain Isolation Operations is an expert-level infrastructure skill for reducing operational risk while keeping rollout control, recovery, and ownership explicit. The emphasis here is repeatable day-two execution under real load, incomplete information, and ordinary human error.

## When To Use

- Use this when Failure Domain Isolation Operations changes service availability, deployment safety, or recovery behavior.
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

- What are the recurring operational decisions inside Failure Domain Isolation Operations?
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

- A runbook for Failure Domain Isolation Operations covering routine and degraded modes.
- An alert map with severity, owner, and first action.
- A handoff template for cross-team or on-call transitions.
- A toil reduction backlog driven by repeated operator pain.

## Tradeoffs

- Operator flexibility versus procedural safety.
- Automation speed versus recoverability when automation fails.
- Local expertise versus portable runbooks.
- Rich dashboards versus cognitive overload during incidents.

## Signals To Watch

- Change failure rate and mean time to recovery after rollout issues.
- Rollback success rate and the time needed to restore steady state.
- Error budget burn and saturation during deployments or failovers.
- Alert quality: noise rate, missing coverage, and acknowledgement delays.
- Configuration drift, dependency skew, and recovery drill pass rate.

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
