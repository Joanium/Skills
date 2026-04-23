---
name: React Rendering Performance
trigger: react rendering performance, help with react rendering performance, plan react rendering performance, improve react rendering performance, expert react rendering performance
description: Expert-level guidance for react rendering performance with domain-specific heuristics, workflow, review criteria, and failure patterns.
---

React Rendering Performance is an expert frontend skill for React. The focal concern is Rendering Performance, but the real task is shaping user-perceived behavior under real browser and device constraints.

## When To Use

- Use this when React Rendering Performance affects a critical journey where users will notice latency, confusion, or inconsistency immediately.
- Use this when implementation details are leaking into the interface and creating fragile behavior.
- Use this when accessibility, responsiveness, and resilience are supposed to be design inputs rather than cleanup work.
- Use this when debugging frontend problems requires a stronger model of state, rendering, and user intent.

## Core Principles

- Users experience behavior, not framework internals.
- Loading, empty, degraded, and recovery states are part of the feature, not edge cases.
- The rendering model should support debugging and measurement, not just speed in the happy path.
- State boundaries should be legible before they become global by accident.
- A frontend system is healthy when design intent survives implementation pressure.

## Key Questions

- Where does React Rendering Performance make user state harder to reason about than it needs to be?
- Which interaction in React Rendering Performance degrades first under latency, stale data, or partial failure?
- What accessibility behavior in React Rendering Performance would break if the DOM or state changed unexpectedly?
- How does React Rendering Performance fail when routing, hydration, or rendering order becomes non-ideal?
- What part of React Rendering Performance looks correct in a mock but collapses under production behavior?

## Workflow

1. Map the user journey, the state transitions, and the failure states before touching implementation details.
2. Choose boundaries for state, rendering, and composition that make debugging cheaper.
3. Design the empty, loading, error, retry, and cross-device behavior as explicit outcomes.
4. Add tests and instrumentation that explain perceived and actual performance.
5. Review the feature with keyboard, screen reader, slow network, and stale-cache assumptions in mind.
6. Capture the final pattern in a design-plus-engineering handoff that others can reuse.

## Artifacts

- A state transition map for React Rendering Performance.
- A UI behavior matrix covering normal, degraded, and recovery paths.
- A lightweight performance and accessibility test plan.
- A handoff note that preserves both design rationale and implementation constraints.

## Tradeoffs

- Immediate visual richness versus interaction clarity.
- Local component freedom versus system-wide consistency.
- Aggressive optimization versus debuggable rendering behavior.
- Fast shipping versus accessibility and resilience debt.

## Signals To Watch

- Interaction latency, visual stability, and completion rate on the target journey.
- Front-end error frequency and user-visible recovery success.
- Accessibility regressions and unresolved severity.
- Cross-browser or device-specific defects that reveal weak assumptions.
- Support or replay evidence showing where the UI misled users.

## Review Checklist

- [ ] The state model for React Rendering Performance is clear enough to debug.
- [ ] Empty, loading, error, and retry behavior are designed explicitly.
- [ ] Accessibility behavior survives realistic interaction patterns.
- [ ] Performance instrumentation exists for the critical path.
- [ ] The implementation preserves design intent across devices.
- [ ] Another engineer can extend React Rendering Performance without guessing hidden UI contracts.

## Common Failure Modes

- State spreading across components until no one owns the actual behavior.
- Optimizing paint or bundle size while ignoring user confusion.
- Treating accessibility as a validation step instead of a design constraint.
- Assuming hydration, routing, or rendering will always be orderly.
