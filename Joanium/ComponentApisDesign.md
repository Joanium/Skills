---
name: Component APIs Design
trigger: component apis design, help with component apis design, plan component apis design, improve component apis design
description: Practical guidance for planning and executing component apis design with clear scope, tradeoffs, and validation steps.
---

Component APIs Design improves frontend delivery by making behavior, accessibility, and handoff expectations concrete.

## Core Principles

- The interface needs to explain itself under normal and failure states.
- Accessibility and responsiveness are design inputs, not polish work.
- Handoffs get better when acceptance criteria are observable.

## Workflow

1. Define the user states, transitions, and edge cases.
2. Specify the intended visuals, interactions, and accessibility behavior.
3. Implement and QA across devices, input modes, and failure conditions.
4. Use telemetry and user feedback to refine the experience.

## Common Mistakes

- Designing only the happy path.
- Leaving implementation details implied in the handoff.
- Treating accessibility regressions as secondary issues.
