---
name: Browser Test Orchestration State Reset
trigger: browser test orchestration state reset, help with browser test orchestration state reset, plan browser test orchestration state reset, improve browser test orchestration state reset, expert browser test orchestration state reset
description: Expert-level guidance for browser test orchestration state reset with action-oriented workflow, review criteria, and failure patterns.
---

Browser Test Orchestration State Reset is an expert browser automation skill for Browser Test Orchestration. The focal concern is State Reset, but the real objective is helping an AI automate real user behavior without collapsing under timing, state, or environment noise.

## When To Use

- Use this when Browser Test Orchestration State Reset needs to survive realistic browser noise rather than only pass in ideal local runs.
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

- What hidden browser state makes Browser Test Orchestration State Reset unreliable across runs?
- Which timing or selector assumption in Browser Test Orchestration State Reset is least stable under real conditions?
- How would Browser Test Orchestration State Reset behave differently across browsers, profiles, or CI environments?
- What artifacts should Browser Test Orchestration State Reset capture so the next failure is diagnosable instead of mysterious?
- Which part of Browser Test Orchestration State Reset is simulating clicks while failing to model user intent?

## Workflow

1. Map the browser states, external prompts, and environment conditions before tuning the script.
2. Define selectors, waits, retries, and reset logic as explicit contracts with the page.
3. Capture the minimum artifacts needed to explain flake or divergence across runs.
4. Exercise the flow across browsers, permissions, and auth states that challenge the assumption model.
5. Prefer behaviorally meaningful automation steps over brittle DOM choreography.
6. Document the final stability model so future AI work can extend the automation without rebreaking it.

## Artifacts

- A browser state and timing map for Browser Test Orchestration State Reset.
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

- [ ] The state model behind Browser Test Orchestration State Reset is explicit.
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
