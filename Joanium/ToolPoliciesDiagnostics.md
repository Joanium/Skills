---
name: Tool Policies Diagnostics
trigger: tool policies diagnostics, help with tool policies diagnostics, plan tool policies diagnostics, improve tool policies diagnostics
description: Practical guidance for planning and executing tool policies diagnostics with clear scope, tradeoffs, and validation steps.
---

Tool Policies Diagnostics helps structure AI systems so prompts, tool use, evaluation, and fallback behavior stay understandable as the product grows.

## Core Principles

- Reliability comes from explicit boundaries, not optimistic prompting.
- Evaluation data should reflect real failure modes, not only demos.
- Operational feedback loops matter as much as model quality.

## Workflow

1. Define the user task, acceptable output, and failure conditions.
2. Choose prompts, models, routing rules, and review paths deliberately.
3. Add logging, evaluation, and fallback behavior before scaling traffic.
4. Refine the system using observed edge cases and measured outcomes.

## Common Mistakes

- Treating prompt quality as a substitute for system design.
- Skipping evaluation datasets for ambiguous or risky tasks.
- Changing several variables at once and losing causal clarity.
