---
name: Legacy Boundary Extraction Diagnostics
trigger: legacy boundary extraction diagnostics, help with legacy boundary extraction diagnostics, plan legacy boundary extraction diagnostics, improve legacy boundary extraction diagnostics, expert legacy boundary extraction diagnostics
description: Expert-level guidance for legacy boundary extraction diagnostics, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Legacy Boundary Extraction Diagnostics is an expert-level engineering systems skill for making architecture, standards, and change management explicit enough to scale beyond individual memory. The emphasis here is turning vague symptoms into testable hypotheses fast enough to reduce mean time to clarity.

## When To Use

- Use this when Legacy Boundary Extraction Diagnostics affects codebase shape, team interfaces, or long-term delivery speed.
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

- What changed most recently in or around Legacy Boundary Extraction Diagnostics?
- What is the blast radius: user segment, workload, environment, or dependency?
- Which signals are primary evidence, and which are misleading side effects?
- How can the issue be isolated or reproduced safely?
- What evidence would eliminate the top hypothesis?

## Workflow

1. Stabilize the system enough to preserve evidence and reduce further harm.
2. Build a timeline of symptoms, changes, and relevant environmental context.
3. Generate a hypothesis tree and rank it by likelihood and impact.
4. Isolate variables with the smallest safe experiments first.
5. Confirm root cause with evidence, not narrative convenience.
6. Record remediation, missing telemetry, and prevention follow-ups.

## Deliverables

- An evidence-backed timeline for Legacy Boundary Extraction Diagnostics.
- A ranked hypothesis tree.
- A remediation log with confirmed and rejected paths.
- A telemetry gap list discovered during investigation.

## Tradeoffs

- Speed of mitigation versus quality of evidence preservation.
- Broad changes versus narrow experiments.
- Confidence in a likely root cause versus proof of causality.
- Immediate operator action versus waiting for stronger signals.

## Signals To Watch

- Lead time, change failure rate, and rollback frequency.
- Policy compliance drift and exception backlog size.
- Dependency graph health, ownership clarity, and orphaned modules.
- Test determinism, flake rate, and review rework caused by unclear standards.
- Migration throughput versus the amount of legacy surface retired.

## Review Checklist

- [ ] The blast radius is defined.
- [ ] A timeline exists before strong conclusions are made.
- [ ] Hypotheses are ranked and explicitly falsifiable.
- [ ] Evidence is preserved before major resets or rollbacks.
- [ ] Rejected hypotheses are recorded to avoid loops.
- [ ] Prevention work is captured after confirmation.

## Common Failure Modes

- Jumping to a familiar cause without evidence.
- Destroying evidence during the first response.
- Changing multiple variables at once and losing causality.
- Stopping after mitigation without understanding the trigger.
