---
name: Battery Performance Tuning
trigger: battery performance tuning, help with battery performance tuning, plan battery performance tuning, improve battery performance tuning
description: Practical guidance for planning and executing battery performance tuning with clear scope, tradeoffs, and validation steps.
---

Battery Performance Tuning focuses on shipping client applications that remain reliable across devices, networks, stores, and operating-system behavior.

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
