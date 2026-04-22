---
name: Monolith Decomposition Diagnostics
trigger: monolith decomposition diagnostics, help with monolith decomposition diagnostics, plan monolith decomposition diagnostics, improve monolith decomposition diagnostics
description: Practical guidance for planning and executing monolith decomposition diagnostics with clear scope, tradeoffs, and validation steps.
---

Monolith Decomposition Diagnostics improves engineering execution by making standards, migration steps, and review boundaries easier to apply consistently.

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
