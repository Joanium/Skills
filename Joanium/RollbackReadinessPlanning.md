---
name: Rollback Readiness Planning
trigger: rollback readiness planning, help with rollback readiness planning, plan rollback readiness planning, improve rollback readiness planning
description: Practical guidance for planning and executing rollback readiness planning with clear scope, tradeoffs, and validation steps.
---

Rollback Readiness Planning focuses on infrastructure decisions that reduce rollout risk while keeping ownership, recovery, and change control explicit.

## Core Principles

- Operational safety needs clear blast-radius control.
- Recovery steps must be designed before the change begins.
- Ownership, communication, and automation should reinforce each other.

## Workflow

1. Map the dependency chain, likely failure modes, and rollback path.
2. Define the rollout stages, checks, and escalation criteria.
3. Automate validation and communication for every critical stage.
4. Review production outcomes before widening the change scope.

## Common Mistakes

- Rolling forward without a tested recovery plan.
- Leaving critical ownership boundaries ambiguous.
- Expanding the rollout before the early signals are stable.
