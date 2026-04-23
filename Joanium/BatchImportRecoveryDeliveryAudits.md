---
name: Batch Import Recovery Delivery Audits
trigger: batch import recovery delivery audits, help with batch import recovery delivery audits, plan batch import recovery delivery audits, improve batch import recovery delivery audits, expert batch import recovery delivery audits
description: Expert-level guidance for batch import recovery delivery audits with action-oriented workflow, review criteria, and failure patterns.
---

Batch Import Recovery Delivery Audits is an expert workflow and operations integration skill for Batch Import Recovery. The focal concern is Delivery Audits, but the real objective is helping an AI connect systems, schedules, and human actions without creating silent operational debt.

## When To Use

- Use this when Batch Import Recovery Delivery Audits spans systems and schedules that can fail long after the original trigger.
- Use this when the AI is working on pipelines that combine data movement, human timing, and retry semantics.
- Use this when silent drops, duplicates, or stale schedules are harder to detect than outright outages.
- Use this when operational correctness depends on more than one system behaving well at the same time.

## Core Principles

- Workflow integrations need explicit replay and idempotency models.
- Schedules and batch windows are part of correctness, not just convenience.
- Connector and mapping drift should be assumed until proven otherwise.
- Dead-letter paths are primary debugging surfaces, not trash bins.
- Human escalation is part of a workflow contract when automatic recovery has limits.

## Key Questions

- Which delay, duplicate, or mapping failure would be hardest to notice inside Batch Import Recovery Delivery Audits?
- How will Batch Import Recovery Delivery Audits recover if one step succeeds and the next step is replayed later?
- What connector, secret, or schedule assumption in Batch Import Recovery Delivery Audits is most likely to drift silently?
- Which dead-letter or alert path should exist before trusting Batch Import Recovery Delivery Audits in production?
- How will the AI prove that the integration is correct beyond one successful run?

## Workflow

1. Map the end-to-end workflow, the schedule boundaries, and the replay expectations.
2. Define schema, mapping, retry, and idempotency rules as part of the operational contract.
3. Exercise the flow under stale secrets, delayed delivery, duplicates, and partial completion.
4. Add dead-letter, audit, and escalation surfaces that reveal hidden degradation quickly.
5. Review throughput and batch assumptions against realistic operating windows.
6. Record the workflow model so future AI changes can preserve operational truth instead of only code shape.

## Artifacts

- A schedule and replay map for Batch Import Recovery Delivery Audits.
- A schema and mapping validation checklist.
- A dead-letter and escalation plan.
- A throughput and idempotency note for operational reviewers.

## Tradeoffs

- Simpler flows versus stronger replay and auditability.
- Higher throughput versus easier recovery and diagnosis.
- Flexible mappings versus stricter contract discipline.
- More automation versus clearer human intervention points.

## Signals To Watch

- Silent duplicates or drops discovered only after downstream damage.
- Dead-letter queues growing without clear ownership or replay rules.
- Schedule drift or stale secrets degrading the workflow gradually.
- Operational teams lacking enough evidence to explain batch failures.
- Mapping changes causing successful runs with incorrect outcomes.

## Review Checklist

- [ ] The schedule, replay, and idempotency model behind Batch Import Recovery Delivery Audits is explicit.
- [ ] Schema and mapping drift are guarded or detectable.
- [ ] Dead-letter and escalation paths are operationally useful.
- [ ] Throughput and batch assumptions were challenged.
- [ ] Partial completion and replay scenarios are handled intentionally.
- [ ] Future AI work can extend the workflow from a stable operational contract.

## Common Failure Modes

- Treating integration correctness as a one-run property.
- Ignoring schedule and replay behavior until data or actions duplicate silently.
- Building dead-letter paths nobody can actually use.
- Allowing mapping drift to remain invisible because the pipeline still runs.
