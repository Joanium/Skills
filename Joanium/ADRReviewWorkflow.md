---
name: ADR Review Workflow
trigger: adr review workflow, help with adr review workflow, plan adr review workflow, improve adr review workflow
description: Practical guidance for planning and executing adr review workflow with clear scope, tradeoffs, and validation steps.
---

ADR Review Workflow is about improving engineering systems by making architecture and delivery rules explicit, reviewable, and repeatable.

## Core Principles

- Evolution beats rewrite when risk is high.
- Standards need clear exceptions and review paths.
- Compatibility and ownership must be designed intentionally.

## Workflow

1. Audit the current constraints and technical debt.
2. Define the target pattern and migration boundary.
3. Roll changes out incrementally with review checkpoints.
4. Capture decisions in docs, tooling, and team habits.

## Common Mistakes

- Changing too many layers at once.
- Skipping backward-compatibility checks.
- Leaving governance unwritten.
