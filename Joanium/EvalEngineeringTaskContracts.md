---
name: Evaluation Engineering Task Contracts
trigger: evaluation engineering task contracts, help with evaluation engineering task contracts, plan evaluation engineering task contracts, improve evaluation engineering task contracts, expert evaluation engineering task contracts
description: Expert-level guidance for evaluation engineering task contracts with action-oriented workflow, review criteria, and failure patterns.
---

Evaluation Engineering Task Contracts is an expert applied AI skill for Evaluation Engineering. The focal concern is Task Contracts, but the real objective is helping an AI system behave usefully in production where cost, latency, ambiguity, and safety all matter at once.

## When To Use

- Use this when Evaluation Engineering Task Contracts affects how model-assisted behavior will actually work once users, tools, and ambiguity are involved.
- Use this when prompt iteration is no longer enough and the AI system needs explicit contracts and operating rules.
- Use this when evaluation, human review, or routing logic need to become first-class parts of the system.
- Use this when a model feature could succeed in demos while failing under production constraints.

## Core Principles

- A strong AI feature has a failure model, not just an impressive example.
- Prompting, routing, retrieval, and tool use are one system and should be judged together.
- Human review is an architectural decision, not merely a fallback.
- Latency and cost are user-facing behavior when they shape trust or usability.
- A model change without comparable evaluation evidence is mostly storytelling.

## Key Questions

- What part of Evaluation Engineering Task Contracts is currently measured by vibes rather than a real contract?
- Which failure in Evaluation Engineering Task Contracts would be hardest to notice before it harms users or operators?
- How will Evaluation Engineering Task Contracts behave if tools are slow, retrieval is weak, or prompts drift over time?
- What should escalate to humans because the AI is structurally weak there, not just temporarily uncertain?
- How will the next model or prompt change be attributed cleanly inside Evaluation Engineering Task Contracts?

## Workflow

1. Define the task boundary, acceptable behavior, and the cost of being wrong.
2. Map the non-model components that shape outcomes: routing, retrieval, tools, policy, and review.
3. Build an evaluation set that includes ambiguity, adversarial behavior, and operational noise.
4. Design escalation, fallback, and rollout rules before traffic increases.
5. Measure cost, latency, safety, and quality together rather than in separate conversations.
6. Record changes so regressions can be traced to the right layer of the system.

## Artifacts

- A behavior contract for Evaluation Engineering Task Contracts.
- An evaluation pack with normal, edge, and adversarial examples.
- A rollout note that ties quality, latency, cost, and safety together.
- A trace and review workflow for diagnosing production behavior.

## Tradeoffs

- Model power versus predictable behavior.
- Automation breadth versus human review load.
- Fast experimentation versus causal clarity.
- Higher quality thresholds versus throughput or cost.

## Signals To Watch

- Task success across representative gold sets and ambiguous real-world cases.
- Escalation rate, fallback frequency, and unresolved review queue growth.
- Cost and latency by route, tool path, or review state.
- Policy violation rate and false-positive enforcement burden.
- Behavior drift after prompt, model, routing, or retrieval changes.

## Review Checklist

- [ ] The contract behind Evaluation Engineering Task Contracts is explicit enough to evaluate.
- [ ] Failure cases are labeled and represented, not hand-waved.
- [ ] Human review exists where the system is structurally weak.
- [ ] Cost and latency are treated as product constraints.
- [ ] Rollout and fallback rules are defined before scale.
- [ ] Future changes can be compared to a stable evidence baseline.

## Common Failure Modes

- Treating the model output as the whole system while the surrounding behavior remains undefined.
- Scaling traffic before evaluation and escalation are operationally real.
- Optimizing cost or latency until quality silently crosses the trust threshold.
- Confusing one impressive example with production readiness.
