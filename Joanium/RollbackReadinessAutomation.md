---
name: Rollback Readiness Automation
trigger: rollback readiness automation, help with rollback readiness automation, plan rollback readiness automation, improve rollback readiness automation
description: Practical guidance for planning and executing rollback readiness automation with clear scope, tradeoffs, and validation steps.
---

Rollback Readiness Automation focuses on infrastructure decisions that reduce rollout risk while keeping ownership, recovery, and change control explicit.

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
