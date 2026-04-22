---
name: Onboarding Friction Analysis Reliability
trigger: onboarding friction analysis reliability, help with onboarding friction analysis reliability, plan onboarding friction analysis reliability, improve onboarding friction analysis reliability, expert onboarding friction analysis reliability
description: Expert-level guidance for onboarding friction analysis reliability, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Onboarding Friction Analysis Reliability is an expert-level product skill for making high-leverage decisions with sharper tradeoffs, stronger evidence, and cleaner follow-through. The emphasis here is designing graceful degradation, recovery paths, and explicit reliability targets before the system is stressed.

## When To Use

- Use this when Onboarding Friction Analysis Reliability affects roadmap choices, customer outcomes, or cross-functional alignment.
- Use this when teams are busy but the decision model is still fuzzy.
- Use this when metrics exist but do not yet explain whether the product bet is working.
- Use this when you need a repeatable operating rhythm rather than another one-off discussion.

## Core Principles

- A good decision starts with a clearly framed problem.
- Tradeoffs create alignment only when they are written and ranked.
- Qualitative signals and quantitative signals should challenge each other.
- Ownership, timing, and review loops matter as much as the decision itself.
- A product process that cannot survive disagreement is not mature enough.

## Decision Questions

- What are the most likely and most damaging failure modes in Onboarding Friction Analysis Reliability?
- Which failures can be masked, and which require explicit user or operator visibility?
- What is the recovery objective for time, data loss, and trust impact?
- How will the team know the system is leaving its safe operating envelope?
- Which dependencies make reliability contingent on someone elses behavior?

## Workflow

1. Define the reliability targets, assumptions, and allowed degradation behavior.
2. Enumerate failure modes across dependencies, operators, data, and environment.
3. Design fallback paths, recovery procedures, and state repair options.
4. Instrument early detection and clear escalation criteria.
5. Test failure handling with drills, chaos cases, or targeted simulation.
6. Review incidents and near misses to update the reliability model.

## Deliverables

- A failure mode catalog for Onboarding Friction Analysis Reliability.
- A target matrix for availability, recovery, and data durability.
- A documented fallback and repair procedure.
- A drill or fault-injection plan for the critical risks.

## Tradeoffs

- Higher reliability versus delivery speed and cost.
- Automatic recovery versus operator control.
- Strict consistency versus availability during failures.
- Redundancy versus complexity and drift risk.

## Signals To Watch

- Outcome movement on the primary user and business metrics.
- Decision latency, rework rate, and unresolved dependency count.
- Experiment throughput versus learning quality.
- Customer pain recurrence after the intervention ships.
- Stakeholder confidence measured through clarity of ownership and review cadence.

## Review Checklist

- [ ] Reliability targets are explicit.
- [ ] Failure modes cover dependencies and operator error.
- [ ] Degraded behavior is designed and communicated.
- [ ] Detection and escalation paths are defined.
- [ ] Recovery procedures are tested, not hypothetical.
- [ ] Near misses feed the reliability model.

## Common Failure Modes

- Reliability work that only adds redundancy without recovery clarity.
- No degraded mode, forcing binary success or total failure.
- Targets stated without instrumentation to measure them.
- Assuming dependencies will be reliable enough by default.
