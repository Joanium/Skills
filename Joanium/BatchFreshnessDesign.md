---
name: Batch Freshness Design
trigger: batch freshness design, help with batch freshness design, plan batch freshness design, improve batch freshness design
description: Practical guidance for planning and executing batch freshness design with clear scope, tradeoffs, and validation steps.
---

Batch Freshness Design helps teams treat data work as a governed product with explicit definitions, lineage, and validation.

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
