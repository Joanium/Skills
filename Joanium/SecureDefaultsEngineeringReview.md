---
name: Secure Defaults Engineering Review
trigger: secure defaults engineering review, help with secure defaults engineering review, plan secure defaults engineering review, improve secure defaults engineering review, expert secure defaults engineering review
description: Expert-level guidance for secure defaults engineering review, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Secure Defaults Engineering Review is an expert-level security skill for reducing exploitable gaps while keeping controls practical for the team that must operate them. The emphasis here is challenging assumptions, proving readiness, and deciding whether the work is actually safe to adopt.

## When To Use

- Use this when Secure Defaults Engineering Review affects trust boundaries, privileged actions, or evidence needed after an incident.
- Use this when attacker behavior is more relevant than nominal product flows.
- Use this when the team needs both preventive controls and a realistic response plan.
- Use this when exceptions, emergency paths, or legacy systems are creating quiet security debt.

## Core Principles

- Assume motivated attackers and imperfect operators.
- Design for prevention, detection, and response together.
- Controls should degrade safely and fail loudly.
- Evidence quality matters; you cannot investigate what you did not preserve.
- Security policy without ownership and exception handling does not hold in production.

## Decision Questions

- What claims about Secure Defaults Engineering Review are supported by evidence, and which are still assertions?
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

- A review summary for Secure Defaults Engineering Review with clear approval status.
- A blocker list separate from optional improvements.
- A record of dissent, risk acceptance, or deferred questions.
- An action tracker tied to the review decision.

## Tradeoffs

- Review depth versus decision speed.
- Strict gating versus throughput and experimentation.
- Broad reviewer input versus accountability clarity.
- Theoretical completeness versus actionable decision quality.

## Signals To Watch

- Detection coverage, signal quality, and false-positive burden.
- Time to contain, time to investigate, and time to recover after security events.
- Exception volume, age, and renewal discipline for risky waivers.
- Privilege drift, stale credentials, and key rotation completion rate.
- Control bypass attempts, abuse rate, and post-incident evidence gaps.

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
