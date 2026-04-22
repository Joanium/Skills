---
name: Config Promotion Flows Review
trigger: config promotion flows review, help with config promotion flows review, plan config promotion flows review, improve config promotion flows review, expert config promotion flows review
description: Expert-level guidance for config promotion flows review, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Config Promotion Flows Review is an expert-level infrastructure skill for reducing operational risk while keeping rollout control, recovery, and ownership explicit. The emphasis here is challenging assumptions, proving readiness, and deciding whether the work is actually safe to adopt.

## When To Use

- Use this when Config Promotion Flows Review changes service availability, deployment safety, or recovery behavior.
- Use this when multiple services, regions, or operators need a shared operating model.
- Use this when hidden dependencies or high blast radius make informal rollout decisions unsafe.
- Use this when production incidents show that the current control plane is too implicit.

## Core Principles

- Blast radius should be designed and limited before the first rollout step.
- Recovery is part of the design, not an appendix after launch.
- Operational ownership must be obvious under time pressure.
- Automate the checks humans are most likely to skip when stressed.
- Prefer progressive exposure over all-at-once change when the system is not yet proven.

## Decision Questions

- What claims about Config Promotion Flows Review are supported by evidence, and which are still assertions?
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

- A review summary for Config Promotion Flows Review with clear approval status.
- A blocker list separate from optional improvements.
- A record of dissent, risk acceptance, or deferred questions.
- An action tracker tied to the review decision.

## Tradeoffs

- Review depth versus decision speed.
- Strict gating versus throughput and experimentation.
- Broad reviewer input versus accountability clarity.
- Theoretical completeness versus actionable decision quality.

## Signals To Watch

- Change failure rate and mean time to recovery after rollout issues.
- Rollback success rate and the time needed to restore steady state.
- Error budget burn and saturation during deployments or failovers.
- Alert quality: noise rate, missing coverage, and acknowledgement delays.
- Configuration drift, dependency skew, and recovery drill pass rate.

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
