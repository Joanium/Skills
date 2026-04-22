---
name: Retrieval Augmentation Evaluation
trigger: retrieval augmentation evaluation, help with retrieval augmentation evaluation, plan retrieval augmentation evaluation, improve retrieval augmentation evaluation
description: Practical guidance for planning and executing retrieval augmentation evaluation with clear scope, tradeoffs, and validation steps.
---

Retrieval Augmentation Evaluation is about making AI features reliable in production by defining evaluation criteria, failure handling, and operational guardrails before scaling usage.

## Core Principles

- Optimize for traceable behavior, not one impressive demo.
- Make prompts, tools, and fallback paths explicit.
- Measure quality with repeatable datasets and review loops.

## Workflow

1. Define the task boundary, success metric, and failure conditions.
2. Choose prompts, models, tools, and evaluation data intentionally.
3. Add logging, guardrails, and fallback behavior before expansion.
4. Review outputs regularly and refine the system with real examples.

## Common Mistakes

- Optimizing for a single happy-path example.
- Shipping without observability or human review hooks.
- Mixing scope changes and model changes in one experiment.
