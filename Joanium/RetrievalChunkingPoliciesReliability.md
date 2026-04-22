---
name: Retrieval Chunking Policies Reliability
trigger: retrieval chunking policies reliability, help with retrieval chunking policies reliability, plan retrieval chunking policies reliability, improve retrieval chunking policies reliability, expert retrieval chunking policies reliability
description: Expert-level guidance for retrieval chunking policies reliability, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Retrieval Chunking Policies Reliability is an expert-level AI systems skill for making model-assisted behavior reliable, auditable, and economically sane in production. The emphasis here is designing graceful degradation, recovery paths, and explicit reliability targets before the system is stressed.

## When To Use

- Use this when Retrieval Chunking Policies Reliability influences user-visible output, automation, or safety-sensitive decisions.
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

- What are the most likely and most damaging failure modes in Retrieval Chunking Policies Reliability?
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

- A failure mode catalog for Retrieval Chunking Policies Reliability.
- A target matrix for availability, recovery, and data durability.
- A documented fallback and repair procedure.
- A drill or fault-injection plan for the critical risks.

## Tradeoffs

- Higher reliability versus delivery speed and cost.
- Automatic recovery versus operator control.
- Strict consistency versus availability during failures.
- Redundancy versus complexity and drift risk.

## Signals To Watch

- Task success rate against a human-reviewed gold set.
- Fallback frequency, escalation rate, and unresolved exception count.
- Latency and token cost by path, prompt family, and customer tier.
- Tool call failure rate and recovery success percentage.
- Unsafe output rate, policy violation rate, and false-positive review burden.

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
