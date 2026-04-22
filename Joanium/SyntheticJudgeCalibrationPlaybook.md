---
name: Synthetic Judge Calibration Playbook
trigger: synthetic judge calibration playbook, help with synthetic judge calibration playbook, plan synthetic judge calibration playbook, improve synthetic judge calibration playbook, expert synthetic judge calibration playbook
description: Expert-level guidance for synthetic judge calibration playbook, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Synthetic Judge Calibration Playbook is an expert-level AI systems skill for making model-assisted behavior reliable, auditable, and economically sane in production. The emphasis here is response execution: who does what, in what order, with what evidence, when conditions are degraded.

## When To Use

- Use this when Synthetic Judge Calibration Playbook influences user-visible output, automation, or safety-sensitive decisions.
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

- What threshold or trigger causes Synthetic Judge Calibration Playbook to move from monitoring to active response?
- Who is the incident or response lead for the first fifteen minutes?
- What containment steps are safe before the full diagnosis is complete?
- How will stakeholders, users, or regulators be informed if needed?
- What condition allows the team to stand down or transition to follow-up work?

## Workflow

1. Classify the event, severity, and triggering evidence.
2. Assign command, owners, and communication responsibilities immediately.
3. Execute containment actions that reduce blast radius without destroying evidence.
4. Restore critical functionality through the safest viable path.
5. Communicate status, uncertainty, and next actions at a fixed cadence.
6. Close with a post-event review that updates the playbook itself.

## Deliverables

- A trigger table for Synthetic Judge Calibration Playbook.
- An action sequence for the first response window.
- A communication template for internal and external updates.
- A post-event capture template for decisions, evidence, and follow-ups.

## Tradeoffs

- Fast containment versus evidence preservation.
- Centralized command versus local decision speed.
- Broad communication versus noise and confusion.
- Immediate restoration versus fully clean remediation.

## Signals To Watch

- Task success rate against a human-reviewed gold set.
- Fallback frequency, escalation rate, and unresolved exception count.
- Latency and token cost by path, prompt family, and customer tier.
- Tool call failure rate and recovery success percentage.
- Unsafe output rate, policy violation rate, and false-positive review burden.

## Review Checklist

- [ ] Trigger thresholds are explicit.
- [ ] Command roles and backups are named.
- [ ] Containment steps preserve critical evidence where possible.
- [ ] Communication cadence and audience are predefined.
- [ ] Stand-down conditions are clear.
- [ ] The playbook is updated after every meaningful use.

## Common Failure Modes

- No one owns command in the first response window.
- Containment destroys the evidence needed for follow-up.
- Communication is improvised and inconsistent.
- The same playbook mistakes repeat because updates never happen.
