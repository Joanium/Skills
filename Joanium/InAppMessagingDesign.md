---
name: In-App Messaging Design
trigger: in-app messaging design, help with in-app messaging design, plan in-app messaging design, improve in-app messaging design
description: Practical guidance for planning and executing in-app messaging design with clear scope, tradeoffs, and validation steps.
---

In-App Messaging Design focuses on shipping client applications that remain reliable across devices, networks, stores, and operating-system behavior.

## Core Principles

- Device constraints shape the design.
- Release quality depends on telemetry and rollback options.
- Platform-specific edge cases need explicit coverage.

## Workflow

1. Map platform constraints, user flows, and failure states.
2. Define release, monitoring, and support requirements.
3. Test on representative devices and network conditions.
4. Iterate using crash, retention, and review signals.

## Common Mistakes

- Testing on one ideal device only.
- Ignoring store or platform policy constraints.
- Shipping without a plan for degraded connectivity.
