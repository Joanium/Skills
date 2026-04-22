---
name: Reverse ETL Activation
trigger: reverse etl activation, help with reverse etl activation, plan reverse etl activation, improve reverse etl activation
description: Practical guidance for planning and executing reverse etl activation with clear scope, tradeoffs, and validation steps.
---

Reverse ETL Activation turns analytics work into a governed system where definitions, lineage, and data quality are explicit.

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
