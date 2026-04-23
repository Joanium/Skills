---
name: Form Autofill Recovery User Simulation
trigger: form autofill recovery user simulation, help with form autofill recovery user simulation, plan form autofill recovery user simulation, improve form autofill recovery user simulation, expert form autofill recovery user simulation
description: Expert-level guidance for form autofill recovery user simulation with action-oriented workflow, review criteria, and failure patterns.
---

Form Autofill Recovery User Simulation is an expert browser automation skill for Form Autofill Recovery. The focal concern is User Simulation, but the real objective is helping an AI automate real user behavior without collapsing under timing, state, or environment noise.

## When To Use

- Use this when Form Autofill Recovery User Simulation needs to survive realistic browser noise rather than only pass in ideal local runs.
- Use this when the AI is automating user journeys that include auth, state carryover, or environment quirks.
- Use this when flaky automation is hiding useful evidence about the real browser behavior.
- Use this when a browser workflow must be trusted for testing, scraping, or operational support.

## Core Principles

- Browser automation quality depends on state control more than script length.
- Selectors and waits are behavioral contracts, not mere code details.
- A flaky workflow usually indicates an unmodeled state transition or timing assumption.
- Cross-browser and environment parity should be tested as hypotheses, not assumed by tooling.
- Artifacts are part of the debugging design because browser failures disappear quickly.

## Key Questions

- What hidden browser state makes Form Autofill Recovery User Simulation unreliable across runs?
- Which timing or selector assumption in Form Autofill Recovery User Simulation is least stable under real conditions?
- How would Form Autofill Recovery User Simulation behave differently across browsers, profiles, or CI environments?
- What artifacts should Form Autofill Recovery User Simulation capture so the next failure is diagnosable instead of mysterious?
- Which part of Form Autofill Recovery User Simulation is simulating clicks while failing to model user intent?

## Workflow

1. Map the browser states, external prompts, and environment conditions before tuning the script.
2. Define selectors, waits, retries, and reset logic as explicit contracts with the page.
3. Capture the minimum artifacts needed to explain flake or divergence across runs.
4. Exercise the flow across browsers, permissions, and auth states that challenge the assumption model.
5. Prefer behaviorally meaningful automation steps over brittle DOM choreography.
6. Document the final stability model so future AI work can extend the automation without rebreaking it.

## Artifacts

- A browser state and timing map for Form Autofill Recovery User Simulation.
- An artifact capture plan covering flaky or failing runs.
- A parity checklist for browsers and environments.
- A selector and retry rationale tied to the user intent of the flow.

## Tradeoffs

- Fast automation versus stronger state isolation.
- Rich simulation versus lower flake probability.
- Cross-browser coverage versus execution time and maintenance.
- DOM-level precision versus behavior-level resilience.

## Signals To Watch

- Flake patterns tied to timing, selectors, or browser state carryover.
- Environment-specific failures that expose weak parity assumptions.
- Automation runs that fail without enough captured evidence to diagnose quickly.
- Visual or interaction drift across browsers after UI changes.
- Retries masking instability instead of resolving the real cause.

## Review Checklist

- [ ] The state model behind Form Autofill Recovery User Simulation is explicit.
- [ ] Selector and timing logic are based on behavior, not luck.
- [ ] Failure artifacts are sufficient for diagnosis.
- [ ] Cross-browser and environment assumptions have been challenged.
- [ ] Retries and resets support resilience instead of hiding instability.
- [ ] Future AI automation can extend the flow from a stable model.

## Common Failure Modes

- Treating browser automation as deterministic while the state model stays implicit.
- Stacking retries until flake is slower rather than less real.
- Overfitting selectors to current DOM structure.
- Failing to capture artifacts that explain what actually happened.
