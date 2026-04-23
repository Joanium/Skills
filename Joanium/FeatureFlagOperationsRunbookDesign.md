---
name: Feature Flag Operations Runbook Design
trigger: feature flag operations runbook design, help with feature flag operations runbook design, plan feature flag operations runbook design, improve feature flag operations runbook design, expert feature flag operations runbook design
description: Expert-level guidance for feature flag operations runbook design with action-oriented workflow, review criteria, and failure patterns.
---

Feature Flag Operations Runbook Design is an expert platform and automation skill for Feature Flag Operations. The focal concern is Runbook Design, but the real objective is helping an AI make infrastructure and operational change without creating invisible blast radius.

## When To Use

- Use this when Feature Flag Operations Runbook Design can affect deployment safety, service recovery, or operator trust in automation.
- Use this when the AI is changing systems that continue running after the command completes.
- Use this when rollback, observability, and access control need to be designed together.
- Use this when platform automation is faster than the team???s current ability to reason about it.

## Core Principles

- Automation should reduce uncertainty, not simply accelerate action.
- If rollback is fragile, the forward path is not truly safe.
- Operators need decision-ready signals, not just more dashboards.
- Access and change boundaries are part of operational design.
- Drills are the only honest test of whether an operational model really works.

## Key Questions

- What part of Feature Flag Operations Runbook Design could fail silently while the automation still reports success?
- Which rollback or recovery step inside Feature Flag Operations Runbook Design depends too much on tribal memory?
- How will operators know when Feature Flag Operations Runbook Design should stop, wait, or reverse course?
- Where does Feature Flag Operations Runbook Design blur access, policy, and execution boundaries dangerously?
- What signal is missing that would turn a future incident from chaos into diagnosis?

## Workflow

1. Map the control surface, operator decisions, and rollback dependencies before changing automation.
2. Define the safety rails that constrain risky behavior even when humans are rushed.
3. Instrument the operational path so the right evidence is captured during change and recovery.
4. Exercise the automation under degraded and partial-success scenarios, not only the happy path.
5. Tighten access and change boundaries so powerful tools stay reviewable.
6. Update the runbook and drill model so the system remains operable without the original author.

## Artifacts

- A change-and-recovery map for Feature Flag Operations Runbook Design.
- A runbook segment that names stop conditions and rollback triggers.
- An alert and evidence plan tied to the operational path.
- A drill note proving whether the automation can be trusted under stress.

## Tradeoffs

- More automation versus less human reversibility.
- Strict guardrails versus operator flexibility.
- Broader observability versus cognitive overload.
- Faster change throughput versus stronger access controls.

## Signals To Watch

- Change failure rate and mean time to recover after automation-driven incidents.
- Frequency of rollbacks that expose weak safety rails.
- Alert usefulness during deployment or incident windows.
- Drift between intended infrastructure state and actual state.
- Operational confusion caused by unclear access or recovery responsibilities.

## Review Checklist

- [ ] The rollback model for Feature Flag Operations Runbook Design is as real as the forward path.
- [ ] Operators have decision-ready signals and clear stop conditions.
- [ ] Access and automation boundaries are intentionally designed.
- [ ] The system was exercised under partial failure, not only success.
- [ ] Evidence capture is adequate for future diagnosis.
- [ ] The runbook remains useful without the original automation author online.

## Common Failure Modes

- Treating automation speed as proof of operational maturity.
- Building rollback paths that fail under the exact stress when they are needed.
- Separating access control from change safety.
- Assuming alerts are helpful because they are numerous.
