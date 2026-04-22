---
name: Architecture Fitness Functions Operations
trigger: architecture fitness functions operations, help with architecture fitness functions operations, plan architecture fitness functions operations, improve architecture fitness functions operations, expert architecture fitness functions operations
description: Expert-level guidance for architecture fitness functions operations, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Architecture Fitness Functions Operations is an expert-level engineering systems skill for making architecture, standards, and change management explicit enough to scale beyond individual memory. The emphasis here is repeatable day-two execution under real load, incomplete information, and ordinary human error.

## When To Use

- Use this when Architecture Fitness Functions Operations affects codebase shape, team interfaces, or long-term delivery speed.
- Use this when unspoken standards or ownership gaps are causing repeated waste.
- Use this when migrations need structure so they can finish without destabilizing the platform.
- Use this when local optimizations are starting to damage cross-team coherence.

## Core Principles

- Incremental evolution usually beats dramatic rewrites under uncertainty.
- Standards only work when exceptions are explicit and reviewable.
- Ownership should be visible in the code, tooling, and review paths.
- Compatibility rules need to be designed before change volume rises.
- Architecture quality is measured by how teams change the system, not only by diagrams.

## Decision Questions

- What are the recurring operational decisions inside Architecture Fitness Functions Operations?
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

- A runbook for Architecture Fitness Functions Operations covering routine and degraded modes.
- An alert map with severity, owner, and first action.
- A handoff template for cross-team or on-call transitions.
- A toil reduction backlog driven by repeated operator pain.

## Tradeoffs

- Operator flexibility versus procedural safety.
- Automation speed versus recoverability when automation fails.
- Local expertise versus portable runbooks.
- Rich dashboards versus cognitive overload during incidents.

## Signals To Watch

- Lead time, change failure rate, and rollback frequency.
- Policy compliance drift and exception backlog size.
- Dependency graph health, ownership clarity, and orphaned modules.
- Test determinism, flake rate, and review rework caused by unclear standards.
- Migration throughput versus the amount of legacy surface retired.

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
