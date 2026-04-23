---
name: AWS Incident Triage
trigger: aws incident triage, help with aws incident triage, plan aws incident triage, improve aws incident triage, expert aws incident triage
description: Expert-level guidance for aws incident triage with domain-specific heuristics, workflow, review criteria, and failure patterns.
---

AWS Incident Triage is an expert cloud and platform skill for AWS. The focal concern is Incident Triage, but the real bar is safe change under pressure, with operators who can still recover when automation gets it wrong.

## When To Use

- Use this when AWS Incident Triage changes the risk profile of deploying, operating, or recovering infrastructure.
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

- What platform assumption inside AWS Incident Triage would fail first during a rushed rollout or incident?
- Which control in AWS Incident Triage is automated but not truly reversible?
- How will operators know whether AWS Incident Triage is helping or harming recovery in the first ten minutes?
- What cost or policy behavior in AWS Incident Triage is invisible until it becomes expensive?
- Which dependency makes AWS Incident Triage less deterministic than the team assumes?

## Workflow

1. Map the control surface, the rollback path, and the operator decision points.
2. Design the change and recovery sequence together before running the automation.
3. Instrument signals that reveal whether the platform is inside or outside safe operating bounds.
4. Exercise the system with rollback, promotion, and policy-violation scenarios.
5. Review cost, reliability, and security outcomes together because the platform couples them.
6. Document the operational model so the next person can recover without the original author.

## Artifacts

- A rollout-and-recovery diagram for AWS Incident Triage.
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

- [ ] The rollback path for AWS Incident Triage is explicit and tested.
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
