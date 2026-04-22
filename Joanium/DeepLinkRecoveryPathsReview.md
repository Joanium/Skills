---
name: Deep Link Recovery Paths Review
trigger: deep link recovery paths review, help with deep link recovery paths review, plan deep link recovery paths review, improve deep link recovery paths review, expert deep link recovery paths review
description: Expert-level guidance for deep link recovery paths review, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Deep Link Recovery Paths Review is an expert-level client platform skill for shipping resilient mobile or desktop behavior across devices, stores, networks, and operating-system constraints. The emphasis here is challenging assumptions, proving readiness, and deciding whether the work is actually safe to adopt.

## When To Use

- Use this when Deep Link Recovery Paths Review affects release risk, device behavior, or user trust during degraded conditions.
- Use this when platform restrictions or background execution rules shape the design.
- Use this when telemetry needs to explain failures that cannot be reproduced locally.
- Use this when crash, battery, or network issues demand a stronger operating model than feature-by-feature fixes.

## Core Principles

- Platform constraints should shape the architecture before implementation debt accumulates.
- Release quality depends on telemetry, rollback options, and operator clarity.
- Offline and degraded states are part of the product, not edge cases.
- Device diversity should be treated as a planning input, not a testing afterthought.
- User trust is lost faster on client platforms because failures feel personal and immediate.

## Decision Questions

- What claims about Deep Link Recovery Paths Review are supported by evidence, and which are still assertions?
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

- A review summary for Deep Link Recovery Paths Review with clear approval status.
- A blocker list separate from optional improvements.
- A record of dissent, risk acceptance, or deferred questions.
- An action tracker tied to the review decision.

## Tradeoffs

- Review depth versus decision speed.
- Strict gating versus throughput and experimentation.
- Broad reviewer input versus accountability clarity.
- Theoretical completeness versus actionable decision quality.

## Signals To Watch

- Crash-free sessions, ANR or hang rate, and fatal signal concentration.
- Battery, network, and storage impact by feature or build channel.
- Release adoption curve and rollback or hotfix frequency.
- Store review trends and support volume after targeted changes.
- Task completion rate under degraded connectivity or background constraints.

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
