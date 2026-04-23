---
name: Accessibility Remediation State Boundaries
trigger: accessibility remediation state boundaries, help with accessibility remediation state boundaries, plan accessibility remediation state boundaries, improve accessibility remediation state boundaries, expert accessibility remediation state boundaries
description: Expert-level guidance for accessibility remediation state boundaries with action-oriented workflow, review criteria, and failure patterns.
---

Accessibility Remediation State Boundaries is an expert frontend implementation skill for Accessibility Remediation. The focal concern is State Boundaries, but the real objective is helping an AI create UI behavior that stays understandable when state, rendering, latency, and devices stop cooperating.

## When To Use

- Use this when Accessibility Remediation State Boundaries affects whether a frontend change will remain coherent outside the happy path.
- Use this when the AI needs sharper UI engineering judgment than translating a mock into components.
- Use this when state, rendering, and user feedback loops are interacting in non-obvious ways.
- Use this when implementation choices can quietly undo design intent across devices or conditions.

## Core Principles

- Frontend correctness includes what users perceive, not only what code executes.
- State boundaries should explain behavior before they optimize it.
- Latency, retries, and stale data are part of the UI contract.
- A design-to-code translation is incomplete until degraded and edge states survive it.
- Observability is a UI feature when it helps teams understand what users actually experienced.

## Key Questions

- What part of Accessibility Remediation State Boundaries becomes hardest to reason about when the UI is slow or inconsistent?
- Which state transition inside Accessibility Remediation State Boundaries would fail silently without stronger instrumentation?
- How does Accessibility Remediation State Boundaries behave when the browser, network, or input method stops being ideal?
- What implementation choice in Accessibility Remediation State Boundaries most threatens the original design intent?
- Which regression in Accessibility Remediation State Boundaries would users notice long before the team does?

## Workflow

1. Map the user journey, state transitions, and degraded conditions before choosing a code structure.
2. Define the component, style, and telemetry boundaries that best explain behavior.
3. Design recovery, fallback, and accessibility behavior as explicit implementation requirements.
4. Use test and visual evidence to protect the risky interaction surfaces.
5. Review device classes, input methods, and latency conditions as part of the implementation design.
6. Capture the reasoning so later UI work can extend the behavior without rediscovering its constraints.

## Artifacts

- A state and edge-case map for Accessibility Remediation State Boundaries.
- A handoff or implementation note preserving the visual and behavioral contract.
- A regression evidence set for risky UI paths.
- A telemetry plan that reveals what users experienced when things go wrong.

## Tradeoffs

- Visual richness versus interaction clarity.
- Local component autonomy versus system-wide consistency.
- Aggressive optimization versus debuggable rendering behavior.
- Fast handoff execution versus resilient edge-state behavior.

## Signals To Watch

- UI regressions that only appear under latency, stale data, or unusual devices.
- Time spent diagnosing state or rendering confusion after a release.
- Support evidence showing users got lost during failure or retry states.
- Accessibility gaps that survived implementation review.
- Mismatch between intended design behavior and shipped interaction behavior.

## Review Checklist

- [ ] The behavioral contract behind Accessibility Remediation State Boundaries is clearer than the implementation shortcuts.
- [ ] State, recovery, and accessibility paths are explicitly handled.
- [ ] Device and latency assumptions have been challenged.
- [ ] Regression evidence exists for the risky visual or interaction paths.
- [ ] Telemetry can explain what users experienced.
- [ ] Future AI work can extend the UI without flattening the original interaction model.

## Common Failure Modes

- Treating the frontend as if rendering speed alone defines quality.
- Letting component convenience blur the actual state model.
- Shipping polished happy paths with weak recovery and retry behavior.
- Assuming design fidelity survives implementation without explicit guardrails.
