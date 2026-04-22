---
name: Agent State Machines Operations
trigger: agent state machines operations, help with agent state machines operations, plan agent state machines operations, improve agent state machines operations, expert agent state machines operations
description: Expert-level guidance for agent state machines operations, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Agent State Machines Operations is an expert-level AI systems skill for making model-assisted behavior reliable, auditable, and economically sane in production. The emphasis here is repeatable day-two execution under real load, incomplete information, and ordinary human error.

## When To Use

- Use this when Agent State Machines Operations influences user-visible output, automation, or safety-sensitive decisions.
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

- What are the recurring operational decisions inside Agent State Machines Operations?
- Which alerts or dashboards should trigger human action, and which should not?
- What information does the operator need in the first five minutes?
- Where are handoffs likely to fail during rotation changes or incidents?
- Which manual steps are risky enough to automate or heavily constrain?

## Workflow

1. Map the steady-state workflows, alert sources, and operator decision tree.
2. Define the minimum context, dashboards, and commands needed to act safely.
3. Write the runbook for common cases, degraded cases, and escalation triggers.
4. Test the handoff path across roles, rotations, and time zones.
5. Run drills to validate the operational model under time pressure.
6. Use incident and toil data to remove fragile manual paths.

## Deliverables

- A runbook for Agent State Machines Operations covering routine and degraded modes.
- An alert map with severity, owner, and first action.
- A handoff template for cross-team or on-call transitions.
- A toil reduction backlog driven by repeated operator pain.

## Tradeoffs

- Operator flexibility versus procedural safety.
- Automation speed versus recoverability when automation fails.
- Local expertise versus portable runbooks.
- Rich dashboards versus cognitive overload during incidents.

## Signals To Watch

- Task success rate against a human-reviewed gold set.
- Fallback frequency, escalation rate, and unresolved exception count.
- Latency and token cost by path, prompt family, and customer tier.
- Tool call failure rate and recovery success percentage.
- Unsafe output rate, policy violation rate, and false-positive review burden.

## Review Checklist

- [ ] Operators can identify first actions quickly.
- [ ] Alerts map to decisions, not mere observations.
- [ ] Runbooks cover degraded and ambiguous cases.
- [ ] Handoffs are documented and practiced.
- [ ] Manual steps with high blast radius are constrained.
- [ ] Toil data feeds improvement work.

## Common Failure Modes

- Runbooks that assume the original author is online.
- Alerts with no clear next action.
- Operational steps that rely on tribal memory.
- Too much automation without a recovery path when automation fails.
