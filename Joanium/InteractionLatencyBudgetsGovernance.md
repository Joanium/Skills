---
name: Interaction Latency Budgets Governance
trigger: interaction latency budgets governance, help with interaction latency budgets governance, plan interaction latency budgets governance, improve interaction latency budgets governance, expert interaction latency budgets governance
description: Expert-level guidance for interaction latency budgets governance, including decision criteria, workflow, tradeoffs, signals, review checkpoints, and failure modes.
---

Interaction Latency Budgets Governance is an expert-level frontend skill for making client behavior understandable, resilient, and consistent across design and engineering. The emphasis here is on ownership, policy, exception handling, and auditability so the domain does not decay into ad hoc decisions.

## When To Use

- Use this when Interaction Latency Budgets Governance shapes user trust through responsiveness, clarity, or failure handling.
- Use this when behavior needs to hold across browsers, devices, accessibility tools, or partial outages.
- Use this when design intent is repeatedly lost between mocks, implementation, and QA.
- Use this when interface regressions are costly because users discover them before the team does.

## Core Principles

- Users experience system behavior, not implementation details.
- Loading, empty, error, and recovery states deserve first-class design.
- Accessibility constraints belong in the design model from the start.
- Client observability should explain both perceived and actual performance.
- Handoffs get stronger when acceptance criteria are visible and testable.

## Decision Questions

- Who sets the policy for Interaction Latency Budgets Governance, and who is allowed to grant exceptions?
- Which behaviors are required, forbidden, or conditionally allowed?
- What evidence proves compliance or justified non-compliance?
- How often should the policy be reviewed against operational reality?
- What enforcement mechanism is credible for this team and toolchain?

## Workflow

1. Define the governed surface area and why it needs formal policy.
2. Assign policy ownership, approvers, and escalation paths for disagreement.
3. Specify baseline rules, approved exceptions, and evidence requirements.
4. Implement enforcement through tooling, review, and reporting loops.
5. Track exceptions with expiry, renewal rules, and risk acceptance.
6. Run periodic governance reviews to retire bad rules and close bypass paths.

## Deliverables

- A policy document for Interaction Latency Budgets Governance with explicit scope.
- An ownership and approver matrix.
- An exception workflow with expiry and review rules.
- A compliance report or dashboard definition.

## Tradeoffs

- Strict enforcement versus developer or operator throughput.
- Central consistency versus local adaptability.
- Formal evidence versus administrative burden.
- Wide policy scope versus clarity and enforceability.

## Signals To Watch

- Interaction latency, visual stability, and completion rate for key journeys.
- Client-side error rate and recovery success without hard refresh.
- Accessibility regression count and unresolved severity.
- Cross-browser defect rate and device-class skew.
- Support tickets or session replays linked to the targeted journey.

## Review Checklist

- [ ] Policy scope and ownership are unambiguous.
- [ ] Rules distinguish required behavior from guidance.
- [ ] Exceptions have expiry, owner, and rationale.
- [ ] Enforcement is realistic for the current tooling.
- [ ] Review cadence exists to remove stale policy.
- [ ] Reporting can show whether the policy is working.

## Common Failure Modes

- Policies that nobody can actually enforce.
- Permanent exceptions that quietly become the norm.
- No evidence trail for risky decisions.
- Governance reviews that only add rules and never retire them.
