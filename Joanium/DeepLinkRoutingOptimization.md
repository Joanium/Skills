---
name: Deep Link Routing Optimization
trigger: deep link routing optimization, help with deep link routing optimization, plan deep link routing optimization, improve deep link routing optimization
description: Practical guidance for planning and executing deep link routing optimization with clear scope, tradeoffs, and validation steps.
---

Deep Link Routing Optimization focuses on shipping client applications that stay resilient across device constraints, stores, and unreliable networks.

## Core Principles

- Platform constraints should shape the design early.
- Release quality depends on telemetry and rollback readiness.
- Mobile and desktop edge cases need explicit test coverage.

## Workflow

1. Map device, network, and platform-specific constraints.
2. Define release, monitoring, and support requirements.
3. Test the experience across representative devices and degraded states.
4. Iterate using crash, retention, and support signals.

## Common Mistakes

- Testing only on ideal hardware and connectivity.
- Ignoring store, OS, or device policy constraints.
- Shipping without a plan for offline or partial failure behavior.
