---
name: Entity Resolution Diagnostics
trigger: entity resolution diagnostics, help with entity resolution diagnostics, plan entity resolution diagnostics, improve entity resolution diagnostics
description: Practical guidance for planning and executing entity resolution diagnostics with clear scope, tradeoffs, and validation steps.
---

Entity Resolution Diagnostics helps teams treat data work as a governed product with explicit definitions, lineage, and validation.

## Core Principles

- Shared definitions are more important than local shortcuts.
- Lineage and quality checks should exist before downstream adoption.
- Data models should reflect the decisions they support.

## Workflow

1. Clarify the business question, consumers, and success metric.
2. Define entities, events, metrics, and validation rules.
3. Model transformations with ownership and downstream impact in mind.
4. Review quality, freshness, and trust signals after release.

## Common Mistakes

- Publishing metrics before defining the source of truth.
- Backfilling data without reconciliation checks.
- Changing schemas without accounting for downstream consumers.
