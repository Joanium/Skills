---
name: Prompt Attack Resilience Review
trigger: prompt attack resilience review, help with prompt attack resilience review, plan prompt attack resilience review, improve prompt attack resilience review, expert prompt attack resilience review
description: Expert-level guidance for prompt attack resilience review, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Prompt Attack Resilience Review is an expert-level AI systems skill for making model-assisted behavior reliable, auditable, and economically sane in production. The emphasis here is challenging assumptions, proving readiness, and deciding whether the work is actually safe to adopt.

## When To Use

- Use this when Prompt Attack Resilience Review influences user-visible output, automation, or safety-sensitive decisions.
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

- What claims about Prompt Attack Resilience Review are supported by evidence, and which are still assertions?
- Which risks are acknowledged but underweighted?
- What readiness gates should block approval or expansion?
- What burden will this place on operators, users, or adjacent teams?
- What unresolved question would make the current proposal unsafe?

## Workflow

1. Collect the proposal, data, incidents, and prior decisions relevant to the review.
2. Inspect assumptions, tradeoffs, and missing alternatives with a skeptical lens.
3. Run explicit readiness gates for correctness, operability, and ownership.
4. Separate blockers from suggestions so decisions can converge cleanly.
5. Record the decision, dissent, and conditions for approval or rejection.
6. Follow up on promised actions until the review outcome is actually satisfied.

## Deliverables

- A review summary for Prompt Attack Resilience Review with clear approval status.
- A blocker list separate from optional improvements.
- A record of dissent, risk acceptance, or deferred questions.
- An action tracker tied to the review decision.

## Tradeoffs

- Review depth versus decision speed.
- Strict gating versus throughput and experimentation.
- Broad reviewer input versus accountability clarity.
- Theoretical completeness versus actionable decision quality.

## Signals To Watch

- Task success rate against a human-reviewed gold set.
- Fallback frequency, escalation rate, and unresolved exception count.
- Latency and token cost by path, prompt family, and customer tier.
- Tool call failure rate and recovery success percentage.
- Unsafe output rate, policy violation rate, and false-positive review burden.

## Review Checklist

- [ ] Evidence backs the key claims.
- [ ] Blockers and suggestions are clearly separated.
- [ ] Ownership exists for follow-up actions.
- [ ] Approval conditions are explicit.
- [ ] Risk acceptance is documented where needed.
- [ ] The decision can be revisited on defined triggers.

## Common Failure Modes

- Reviews that generate comments but no decision.
- Rubber-stamping because the right people were not engaged.
- Blocking issues mixed with minor suggestions until nothing is clear.
- Approval granted without ownership for follow-through.
