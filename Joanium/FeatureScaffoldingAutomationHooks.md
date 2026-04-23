---
name: Feature Scaffolding Automation Hooks
trigger: feature scaffolding automation hooks, help with feature scaffolding automation hooks, plan feature scaffolding automation hooks, improve feature scaffolding automation hooks, expert feature scaffolding automation hooks
description: Expert-level guidance for feature scaffolding automation hooks with action-oriented workflow, review criteria, and failure patterns.
---

Feature Scaffolding Automation Hooks is an expert coding workflow skill for Feature Scaffolding. The focal concern is Automation Hooks, but the real objective is helping an AI move from messy code context to a safe, reviewable, high-leverage change.

## When To Use

- Use this when Feature Scaffolding Automation Hooks is the difference between a plausible code edit and a change that can survive review, testing, and rollback.
- Use this when the AI has partial context and needs a stronger method for separating evidence from guesswork.
- Use this when a code problem spans files, runtime behavior, and team conventions at the same time.
- Use this when the safest path is not obvious and the change needs tighter scoping before execution.

## Core Principles

- A code change is only good if its blast radius is understood before editing starts.
- The shortest patch is not automatically the safest patch.
- Evidence beats intuition when debugging, reviewing, or refactoring unfamiliar code.
- Verification should be designed at the same time as the change, not appended afterward.
- If rollback is unclear, the change is not ready.

## Key Questions

- What part of Feature Scaffolding Automation Hooks is known from evidence versus inferred from incomplete context?
- Which file, boundary, or runtime path inside Feature Scaffolding Automation Hooks would hurt most if misunderstood?
- What is the smallest proof that the chosen change direction is correct?
- Where could Feature Scaffolding Automation Hooks create a silent regression that tests may miss?
- How would the AI explain the safety of Feature Scaffolding Automation Hooks to a skeptical reviewer?

## Workflow

1. Build a narrow evidence set before deciding on the patch shape.
2. Map the call path, ownership boundary, or data flow that actually controls the behavior.
3. Choose the smallest change that resolves the problem without hiding future work.
4. Design verification, rollback, and reviewer-facing rationale before editing extensively.
5. Execute the patch with instrumentation or tests that prove the claim, not just compile the code.
6. Close the loop by documenting what was learned so future AI passes start from a stronger baseline.

## Artifacts

- A concise evidence note for Feature Scaffolding Automation Hooks.
- A scoped patch plan with rollback assumptions.
- A verification checklist that covers the risky paths.
- A reviewer summary explaining why the change is safe enough to merge.

## Tradeoffs

- Narrow changes versus fixing adjacent design debt.
- Fast patch delivery versus stronger causal proof.
- Local simplification versus consistency with broader codebase patterns.
- Extra instrumentation now versus weaker debugging later.

## Signals To Watch

- Time to isolate root cause after the first symptom is seen.
- Regression rate after small or medium code changes.
- Reviewer friction caused by unclear scope or weak evidence.
- Rollback frequency after supposedly safe patches.
- Debugging loops caused by missing traces, logs, or minimal reproductions.

## Review Checklist

- [ ] The evidence supporting Feature Scaffolding Automation Hooks is stronger than the assumptions.
- [ ] The change scope is smaller than the unexplained blast radius.
- [ ] Verification proves the intended behavior on the risky path.
- [ ] Rollback or recovery is straightforward if the change misbehaves.
- [ ] The reviewer-facing rationale is concrete and defensible.
- [ ] Future AI passes can build on the recorded evidence instead of rediscovering it.

## Common Failure Modes

- Letting the patch size grow faster than the confidence in the diagnosis.
- Mistaking compilation or passing tests for causal proof.
- Fixing symptoms in several places without identifying the controlling boundary.
- Shipping changes whose rollback path exists only in theory.
