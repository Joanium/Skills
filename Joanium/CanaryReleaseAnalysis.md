---
name: Canary Release Analysis
trigger: canary release analysis, help with canary release analysis, plan canary release analysis, improve canary release analysis
description: Practical guidance for planning and executing canary release analysis with clear scope, tradeoffs, and validation steps.
---

Canary Release Analysis focuses on reducing operational risk while improving delivery speed through clear rollout controls, ownership, and recovery paths.

## Core Principles

- Rollouts need explicit blast-radius control.
- Recovery plans are part of the design, not an appendix.
- Ownership and communication paths must be unambiguous.

## Workflow

1. Identify failure modes, dependencies, and recovery objectives.
2. Design rollout stages, checks, and rollback criteria.
3. Automate monitoring and communication for every stage.
4. Run a limited release before broader adoption.

## Common Mistakes

- Treating rollout strategy as an afterthought.
- Expanding scope before proving operational readiness.
- Missing clear handoffs during incidents.
