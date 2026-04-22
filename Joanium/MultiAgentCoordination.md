---
name: Multi-Agent Coordination
trigger: multi-agent coordination, help with multi-agent coordination, plan multi-agent coordination, improve multi-agent coordination
description: Practical guidance for planning and executing multi-agent coordination with clear scope, tradeoffs, and validation steps.
---

Multi-Agent Coordination is about making AI features reliable in production by defining evaluation criteria, failure handling, and operational guardrails before scaling usage.

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
