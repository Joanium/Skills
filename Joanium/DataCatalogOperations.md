---
name: Data Catalog Operations
trigger: data catalog operations, help with data catalog operations, plan data catalog operations, improve data catalog operations
description: Practical guidance for planning and executing data catalog operations with clear scope, tradeoffs, and validation steps.
---

Data Catalog Operations turns analytics work into a governed system where definitions, lineage, and data quality are explicit.

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
