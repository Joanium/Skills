---
name: Prompt Attack Resilience Optimization
trigger: prompt attack resilience optimization, help with prompt attack resilience optimization, plan prompt attack resilience optimization, improve prompt attack resilience optimization, expert prompt attack resilience optimization
description: Expert-level guidance for prompt attack resilience optimization, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Prompt Attack Resilience Optimization is an expert-level AI systems skill for making model-assisted behavior reliable, auditable, and economically sane in production. The emphasis here is improving the limiting resource without merely moving cost, fragility, or risk somewhere else.

## When To Use

- Use this when Prompt Attack Resilience Optimization influences user-visible output, automation, or safety-sensitive decisions.
- Use this when prompts, retrieval, tools, and policies interact in ways that are hard to reason about informally.
- Use this when you need explicit acceptance criteria before increasing traffic, autonomy, or model authority.
- Use this when regressions, unsafe behavior, or cost spikes require a more disciplined operating model.

## Core Principles

- Separate model behavior from system behavior; both need design.
- Assume variance and clamp it with contracts, validation, and fallback paths.
- Evaluate against adversarial, ambiguous, and low-context cases, not only happy-path prompts.
- Make prompt, model, retrieval, and tool changes attributable so debugging stays causal.
- Human escalation should be deliberate, fast, and observable.

## Decision Questions

- What is the actual bottleneck in Prompt Attack Resilience Optimization: CPU, memory, latency, network, human time, or policy friction?
- What objective function matters most: throughput, latency, cost, quality, or predictability?
- Which workload slice or user segment dominates the current pain?
- How will regressions be detected once a change lands?
- What optimization would be impressive but strategically irrelevant?

## Workflow

1. Baseline the current performance, cost, or throughput with stable measurement.
2. Identify the true bottleneck and the conditions that trigger it.
3. Generate multiple intervention options and rank them by expected leverage.
4. Test one variable at a time with clear before-and-after criteria.
5. Roll out the winning change gradually while watching adjacent regressions.
6. Capture the new baseline and retire stale assumptions about the old one.

## Deliverables

- A baseline report for Prompt Attack Resilience Optimization with representative workloads.
- An optimization experiment plan with explicit success thresholds.
- Before-and-after results with regression notes.
- Guardrails that keep the optimization from silently backsliding.

## Tradeoffs

- Peak performance versus system simplicity.
- Lower cost versus operational slack and headroom.
- Short benchmarks versus representative production behavior.
- Optimizing one bottleneck versus creating a new one elsewhere.

## Signals To Watch

- Task success rate against a human-reviewed gold set.
- Fallback frequency, escalation rate, and unresolved exception count.
- Latency and token cost by path, prompt family, and customer tier.
- Tool call failure rate and recovery success percentage.
- Unsafe output rate, policy violation rate, and false-positive review burden.

## Review Checklist

- [ ] A stable baseline exists before changes start.
- [ ] The bottleneck is demonstrated rather than assumed.
- [ ] Success metrics and regression metrics are both defined.
- [ ] Experiments change one major variable at a time.
- [ ] Rollout is gradual enough to observe side effects.
- [ ] The new baseline is documented after the optimization.

## Common Failure Modes

- Optimizing the easiest metric instead of the limiting one.
- Comparing benchmarks that do not resemble real workloads.
- Declaring victory without regression monitoring.
- Pushing complexity into operations to gain a small local win.
