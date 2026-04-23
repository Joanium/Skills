---
name: GCP Cost Governance
trigger: gcp cost governance, help with gcp cost governance, plan gcp cost governance, improve gcp cost governance, expert gcp cost governance
description: Expert-level guidance for gcp cost governance with domain-specific heuristics, workflow, review criteria, and failure patterns.
---

GCP Cost Governance is an expert cloud and platform skill for GCP. The focal concern is Cost Governance, but the real bar is safe change under pressure, with operators who can still recover when automation gets it wrong.

## When To Use

- Use this when GCP Cost Governance changes the risk profile of deploying, operating, or recovering infrastructure.
- Use this when automation is powerful enough to cause platform-wide damage if modeled badly.
- Use this when operators need stronger contracts than ???the pipeline usually works.???
- Use this when cost, reliability, and policy are colliding in the same platform surface.

## Core Principles

- A platform is healthy when operators can understand and reverse its changes.
- Automation should reduce risk concentration, not merely accelerate blast radius.
- Recovery steps need the same engineering discipline as deployment steps.
- Observability must support decisions, not just dashboards.
- Policy is only real if the platform can enforce it under stress.

## Key Questions

- What platform assumption inside GCP Cost Governance would fail first during a rushed rollout or incident?
- Which control in GCP Cost Governance is automated but not truly reversible?
- How will operators know whether GCP Cost Governance is helping or harming recovery in the first ten minutes?
- What cost or policy behavior in GCP Cost Governance is invisible until it becomes expensive?
- Which dependency makes GCP Cost Governance less deterministic than the team assumes?

## Workflow

1. Map the control surface, the rollback path, and the operator decision points.
2. Design the change and recovery sequence together before running the automation.
3. Instrument signals that reveal whether the platform is inside or outside safe operating bounds.
4. Exercise the system with rollback, promotion, and policy-violation scenarios.
5. Review cost, reliability, and security outcomes together because the platform couples them.
6. Document the operational model so the next person can recover without the original author.

## Artifacts

- A rollout-and-recovery diagram for GCP Cost Governance.
- An operator decision matrix for common and degraded scenarios.
- A cost, policy, and reliability checkpoint list tied to the platform surface.
- A runbook note explaining where automation should stop and humans should decide.

## Tradeoffs

- Automation speed versus operator reversibility.
- Standardization versus local service flexibility.
- Stronger policy enforcement versus developer throughput.
- Higher resilience versus platform complexity and cost.

## Signals To Watch

- Change failure rate and mean time to recovery after platform-driven incidents.
- Rollback reliability and operator clarity during degraded rollouts.
- Cost drift and saturation signals that escape routine dashboards.
- Policy violation rate and exception growth.
- Time lost to platform confusion during incidents or promotions.

## Review Checklist

- [ ] The rollback path for GCP Cost Governance is explicit and tested.
- [ ] Operators can tell whether automation is safe to continue.
- [ ] Cost, reliability, and policy consequences are visible.
- [ ] Recovery steps are documented at the same fidelity as deployment steps.
- [ ] Human decision points are intentional, not accidental.
- [ ] The platform behavior survives stressed or degraded conditions.

## Common Failure Modes

- Automating dangerous behavior faster than the team can understand it.
- Treating rollback as a theoretical feature rather than an exercised path.
- Separating cost, policy, and reliability decisions that are actually coupled.
- Building a platform only its authors can operate confidently.
