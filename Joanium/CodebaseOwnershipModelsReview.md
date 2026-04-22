---
name: Codebase Ownership Models Review
trigger: codebase ownership models review, help with codebase ownership models review, plan codebase ownership models review, improve codebase ownership models review, expert codebase ownership models review
description: Expert-level guidance for codebase ownership models review, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Codebase Ownership Models Review is an expert-level engineering systems skill for making architecture, standards, and change management explicit enough to scale beyond individual memory. The emphasis here is challenging assumptions, proving readiness, and deciding whether the work is actually safe to adopt.

## When To Use

- Use this when Codebase Ownership Models Review affects codebase shape, team interfaces, or long-term delivery speed.
- Use this when unspoken standards or ownership gaps are causing repeated waste.
- Use this when migrations need structure so they can finish without destabilizing the platform.
- Use this when local optimizations are starting to damage cross-team coherence.

## Core Principles

- Incremental evolution usually beats dramatic rewrites under uncertainty.
- Standards only work when exceptions are explicit and reviewable.
- Ownership should be visible in the code, tooling, and review paths.
- Compatibility rules need to be designed before change volume rises.
- Architecture quality is measured by how teams change the system, not only by diagrams.

## Decision Questions

- What claims about Codebase Ownership Models Review are supported by evidence, and which are still assertions?
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

- A review summary for Codebase Ownership Models Review with clear approval status.
- A blocker list separate from optional improvements.
- A record of dissent, risk acceptance, or deferred questions.
- An action tracker tied to the review decision.

## Tradeoffs

- Review depth versus decision speed.
- Strict gating versus throughput and experimentation.
- Broad reviewer input versus accountability clarity.
- Theoretical completeness versus actionable decision quality.

## Signals To Watch

- Lead time, change failure rate, and rollback frequency.
- Policy compliance drift and exception backlog size.
- Dependency graph health, ownership clarity, and orphaned modules.
- Test determinism, flake rate, and review rework caused by unclear standards.
- Migration throughput versus the amount of legacy surface retired.

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
