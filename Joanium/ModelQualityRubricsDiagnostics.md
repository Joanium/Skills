---
name: Model Quality Rubrics Diagnostics
trigger: model quality rubrics diagnostics, help with model quality rubrics diagnostics, plan model quality rubrics diagnostics, improve model quality rubrics diagnostics, expert model quality rubrics diagnostics
description: Expert-level guidance for model quality rubrics diagnostics, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Model Quality Rubrics Diagnostics is an expert-level AI systems skill for making model-assisted behavior reliable, auditable, and economically sane in production. The emphasis here is turning vague symptoms into testable hypotheses fast enough to reduce mean time to clarity.

## When To Use

- Use this when Model Quality Rubrics Diagnostics influences user-visible output, automation, or safety-sensitive decisions.
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

- What changed most recently in or around Model Quality Rubrics Diagnostics?
- What is the blast radius: user segment, workload, environment, or dependency?
- Which signals are primary evidence, and which are misleading side effects?
- How can the issue be isolated or reproduced safely?
- What evidence would eliminate the top hypothesis?

## Workflow

1. Stabilize the system enough to preserve evidence and reduce further harm.
2. Build a timeline of symptoms, changes, and relevant environmental context.
3. Generate a hypothesis tree and rank it by likelihood and impact.
4. Isolate variables with the smallest safe experiments first.
5. Confirm root cause with evidence, not narrative convenience.
6. Record remediation, missing telemetry, and prevention follow-ups.

## Deliverables

- An evidence-backed timeline for Model Quality Rubrics Diagnostics.
- A ranked hypothesis tree.
- A remediation log with confirmed and rejected paths.
- A telemetry gap list discovered during investigation.

## Tradeoffs

- Speed of mitigation versus quality of evidence preservation.
- Broad changes versus narrow experiments.
- Confidence in a likely root cause versus proof of causality.
- Immediate operator action versus waiting for stronger signals.

## Signals To Watch

- Task success rate against a human-reviewed gold set.
- Fallback frequency, escalation rate, and unresolved exception count.
- Latency and token cost by path, prompt family, and customer tier.
- Tool call failure rate and recovery success percentage.
- Unsafe output rate, policy violation rate, and false-positive review burden.

## Review Checklist

- [ ] The blast radius is defined.
- [ ] A timeline exists before strong conclusions are made.
- [ ] Hypotheses are ranked and explicitly falsifiable.
- [ ] Evidence is preserved before major resets or rollbacks.
- [ ] Rejected hypotheses are recorded to avoid loops.
- [ ] Prevention work is captured after confirmation.

## Common Failure Modes

- Jumping to a familiar cause without evidence.
- Destroying evidence during the first response.
- Changing multiple variables at once and losing causality.
- Stopping after mitigation without understanding the trigger.
