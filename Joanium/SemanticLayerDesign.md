---
name: Semantic Layer Design
trigger: semantic layer design, help with semantic layer design, plan semantic layer design, improve semantic layer design
description: Practical guidance for planning and executing semantic layer design with clear scope, tradeoffs, and validation steps.
---

Semantic Layer Design turns analytics work into a governed system where definitions, lineage, and data quality are explicit.

## Core Principles

- Shared definitions matter more than local convenience.
- Data changes need lineage, validation, and ownership.
- Models should reflect downstream decisions, not raw tables alone.

## Workflow

1. Clarify the business question and the consuming teams.
2. Define entities, metrics, and quality checks before modeling.
3. Model transformations with lineage and ownership.
4. Review backfills and downstream impact before release.

## Common Mistakes

- Reusing vague metric names across teams.
- Backfilling without reconciliation checks.
- Ignoring data consumers during schema changes.
