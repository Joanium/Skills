---
name: Deep Link Routing Diagnostics
trigger: deep link routing diagnostics, help with deep link routing diagnostics, plan deep link routing diagnostics, improve deep link routing diagnostics
description: Practical guidance for planning and executing deep link routing diagnostics with clear scope, tradeoffs, and validation steps.
---

Deep Link Routing Diagnostics focuses on shipping client applications that stay resilient across device constraints, stores, and unreliable networks.

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
