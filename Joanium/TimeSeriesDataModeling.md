---
name: Time-Series Data Modeling
trigger: time-series data modeling, help with time-series data modeling, plan time-series data modeling, improve time-series data modeling
description: Practical guidance for planning and executing time-series data modeling with clear scope, tradeoffs, and validation steps.
---

Time-Series Data Modeling helps teams reason about technical domains that have sharp constraints, specialized tooling, and non-obvious failure modes.

## Core Principles

- Respect the physical, computational, or protocol limits of the system.
- Model the failure modes before optimizing performance.
- Specialized systems need test harnesses and observability early.

## Workflow

1. Define the domain constraints and operating envelope.
2. Choose the architecture, tooling, and validation approach.
3. Prototype critical paths before full integration.
4. Measure correctness, performance, and maintainability together.

## Common Mistakes

- Porting generic software assumptions into specialized systems.
- Optimizing before validating correctness.
- Underestimating integration and operations overhead.
