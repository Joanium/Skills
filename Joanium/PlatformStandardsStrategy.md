---
name: Platform Standards Strategy
trigger: platform standards strategy, help with platform standards strategy, plan platform standards strategy, improve platform standards strategy
description: Practical guidance for planning and executing platform standards strategy with clear scope, tradeoffs, and validation steps.
---

Platform Standards Strategy improves engineering execution by making standards, migration steps, and review boundaries easier to apply consistently.

## Core Principles

- Incremental evolution usually beats large rewrites under uncertainty.
- Standards need clear exception paths to remain useful.
- Compatibility and ownership should be designed, not assumed.

## Workflow

1. Audit the current constraints, debt, and coupling points.
2. Define the target pattern and the migration boundary.
3. Roll out changes incrementally with explicit review checkpoints.
4. Capture the outcome in tooling, documentation, and team habits.

## Common Mistakes

- Changing multiple layers without a migration seam.
- Skipping backward-compatibility validation.
- Leaving governance as tribal knowledge.
