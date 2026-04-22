---
name: Crash Signal Triage Strategy
trigger: crash signal triage strategy, help with crash signal triage strategy, plan crash signal triage strategy, improve crash signal triage strategy, expert crash signal triage strategy
description: Expert-level guidance for crash signal triage strategy, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Crash Signal Triage Strategy is an expert-level client platform skill for shipping resilient mobile or desktop behavior across devices, stores, networks, and operating-system constraints. The emphasis here is on choosing the operating model, decision boundaries, and success criteria before local optimizations become policy by accident.

## When To Use

- Use this when Crash Signal Triage Strategy affects release risk, device behavior, or user trust during degraded conditions.
- Use this when platform restrictions or background execution rules shape the design.
- Use this when telemetry needs to explain failures that cannot be reproduced locally.
- Use this when crash, battery, or network issues demand a stronger operating model than feature-by-feature fixes.

## Core Principles

- Platform constraints should shape the architecture before implementation debt accumulates.
- Release quality depends on telemetry, rollback options, and operator clarity.
- Offline and degraded states are part of the product, not edge cases.
- Device diversity should be treated as a planning input, not a testing afterthought.
- User trust is lost faster on client platforms because failures feel personal and immediate.

## Decision Questions

- What decision is Crash Signal Triage Strategy supposed to improve over the next planning horizon?
- Which constraints are fixed, and which are merely habits that can be challenged?
- Where does failure in Crash Signal Triage Strategy create the largest technical, business, or trust cost?
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

- A written decision statement for Crash Signal Triage Strategy.
- A ranked constraint register with explicit owners.
- A risk register tied to the chosen operating model.
- A review cadence with triggers for strategy revision.

## Tradeoffs

- Flexibility versus standardization across teams or products.
- Short-term delivery speed versus long-term operating cost.
- Centralized control versus local autonomy.
- Preventive investment now versus reactive cost later.

## Signals To Watch

- Crash-free sessions, ANR or hang rate, and fatal signal concentration.
- Battery, network, and storage impact by feature or build channel.
- Release adoption curve and rollback or hotfix frequency.
- Store review trends and support volume after targeted changes.
- Task completion rate under degraded connectivity or background constraints.

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
