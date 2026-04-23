---
name: Embeddings Experiment Tracking
trigger: embeddings experiment tracking, help with embeddings experiment tracking, plan embeddings experiment tracking, improve embeddings experiment tracking, expert embeddings experiment tracking
description: Expert-level guidance for embeddings experiment tracking with domain-specific heuristics, workflow, review criteria, and failure patterns.
---

Embeddings Experiment Tracking is an expert applied-AI skill for Embeddings. The focal concern is Experiment Tracking, but the real bar is production behavior that is measurable, reviewable, and worth its cost.

## When To Use

- Use this when Embeddings Experiment Tracking affects model-assisted output that users, reviewers, or downstream systems will trust.
- Use this when the team needs more than prompt iteration and requires an operating model for behavior, cost, and risk.
- Use this when evaluation and failure analysis need to become part of normal development rather than a prelaunch ritual.
- Use this when AI capability is increasing faster than the team ability to reason about it.

## Core Principles

- Prompt quality is only one layer of the system; contracts, retrieval, tools, and review matter too.
- A useful AI feature has a failure model, not just a success demo.
- Cost and latency are product behavior because they shape what can be trusted in practice.
- Human review is a system design choice, not a sign of failure.
- A model change without an evaluation story is a gamble, not an iteration.

## Key Questions

- What behavior in Embeddings Experiment Tracking would look acceptable in a demo but fail under production ambiguity?
- Which part of Embeddings Experiment Tracking lacks a measurable contract: inputs, outputs, tools, or review criteria?
- How will Embeddings Experiment Tracking fail when latency, cost, retrieval quality, or tool behavior shifts?
- What evidence will prove that Embeddings Experiment Tracking is getting better rather than merely changing?
- Where should humans intervene in Embeddings Experiment Tracking to add leverage instead of toil?

## Workflow

1. Define the task boundary, acceptable behavior, and the failure cases that matter most.
2. Specify contracts for prompts, model choice, retrieval context, tools, and review paths.
3. Build an evaluation and tracing story before scaling traffic or autonomy.
4. Model cost, latency, and safety as product constraints rather than afterthoughts.
5. Roll out in stages with comparison sets, human feedback, and fallback behavior.
6. Keep a change log that makes model, prompt, retrieval, and rubric shifts attributable.

## Artifacts

- A behavior contract for Embeddings Experiment Tracking.
- An evaluation pack with gold cases, edge cases, and failure labels.
- A trace or review workflow showing how the system is actually behaving.
- A rollout note that ties cost, latency, safety, and user impact together.

## Tradeoffs

- Model capability versus cost and latency discipline.
- Autonomy versus human review burden.
- Flexible prompting versus stable, reviewable behavior.
- Fast experimentation versus causal clarity in evaluation.

## Signals To Watch

- Task success against representative gold sets and adversarial cases.
- Escalation rate, fallback usage, and unresolved review backlog.
- Latency and cost by route, model, or tool path.
- Safety or policy violation rate and false-positive review cost.
- Performance drift after prompt, model, or retrieval changes.

## Review Checklist

- [ ] The behavior contract for Embeddings Experiment Tracking is explicit.
- [ ] Evaluation covers ambiguous and adversarial cases.
- [ ] Cost and latency are treated as design constraints.
- [ ] Review loops are intentional and measurable.
- [ ] Change attribution is good enough to debug regressions.
- [ ] Rollout and fallback behavior are defined before scale.

## Common Failure Modes

- Treating prompting as the whole system while everything around it stays undefined.
- Scaling usage before evaluation and review workflows are real.
- Confusing impressive examples with robust behavior.
- Optimizing capability while cost, latency, and review load quietly become untenable.
