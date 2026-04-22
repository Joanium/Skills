---
name: Legacy Boundary Extraction Strategy
trigger: legacy boundary extraction strategy, help with legacy boundary extraction strategy, plan legacy boundary extraction strategy, improve legacy boundary extraction strategy, expert legacy boundary extraction strategy
description: Expert-level guidance for legacy boundary extraction strategy, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Legacy Boundary Extraction Strategy is an expert-level engineering systems skill for making architecture, standards, and change management explicit enough to scale beyond individual memory. The emphasis here is on choosing the operating model, decision boundaries, and success criteria before local optimizations become policy by accident.

## When To Use

- Use this when Legacy Boundary Extraction Strategy affects codebase shape, team interfaces, or long-term delivery speed.
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

- What decision is Legacy Boundary Extraction Strategy supposed to improve over the next planning horizon?
- Which constraints are fixed, and which are merely habits that can be challenged?
- Where does failure in Legacy Boundary Extraction Strategy create the largest technical, business, or trust cost?
- Which teams must own inputs, decisions, and follow-through?
- What evidence would prove that the current direction is wrong?

## Workflow

1. Frame the objective, decision horizon, and non-negotiable constraints.
2. Map stakeholders, dependencies, and the highest-cost failure boundaries.
3. Compare realistic operating models and choose the default path deliberately.
4. Define guardrails, decision rights, and the metrics that will govern tradeoffs.
5. Record rejected alternatives and the reasons they lost.
6. Publish the strategy with a review cadence and conditions for revision.

## Deliverables

- A written decision statement for Legacy Boundary Extraction Strategy.
- A ranked constraint register with explicit owners.
- A risk register tied to the chosen operating model.
- A review cadence with triggers for strategy revision.

## Tradeoffs

- Flexibility versus standardization across teams or products.
- Short-term delivery speed versus long-term operating cost.
- Centralized control versus local autonomy.
- Preventive investment now versus reactive cost later.

## Signals To Watch

- Lead time, change failure rate, and rollback frequency.
- Policy compliance drift and exception backlog size.
- Dependency graph health, ownership clarity, and orphaned modules.
- Test determinism, flake rate, and review rework caused by unclear standards.
- Migration throughput versus the amount of legacy surface retired.

## Review Checklist

- [ ] The problem, horizon, and constraints are explicit.
- [ ] Alternatives were compared rather than hand-waved.
- [ ] Decision rights and owners are named.
- [ ] Success and failure signals are measurable.
- [ ] Review timing is scheduled, not implied.
- [ ] The chosen strategy can be explained to a skeptical peer.

## Common Failure Modes

- Strategy written as slogans instead of decisions.
- Objectives that cannot be measured or challenged.
- No owner for enforcing tradeoffs.
- No review date, causing silent drift.
