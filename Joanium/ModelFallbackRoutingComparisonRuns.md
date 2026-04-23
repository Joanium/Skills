---
name: Model Fallback Routing Comparison Runs
trigger: model fallback routing comparison runs, help with model fallback routing comparison runs, plan model fallback routing comparison runs, improve model fallback routing comparison runs, expert model fallback routing comparison runs
description: Expert-level guidance for model fallback routing comparison runs with action-oriented workflow, review criteria, and failure patterns.
---

Model Fallback Routing Comparison Runs is an expert agent and tooling skill for Model Fallback Routing. The focal concern is Comparison Runs, but the real objective is helping an AI system use tools, prompts, memory, and review loops without drifting into fragile automation.

## When To Use

- Use this when Model Fallback Routing Comparison Runs affects whether an AI system remains useful once prompts, tools, and real operational noise are involved.
- Use this when the AI needs an explicit system model rather than more ad hoc prompt edits.
- Use this when failure analysis, human review, or tool reliability are becoming the real constraints.
- Use this when the system can produce impressive outputs but cannot yet defend or sustain them.

## Core Principles

- An AI agent is a workflow system, not just a model call with extra steps.
- Failure labeling is what turns anecdotes into engineering evidence.
- Human review should target structural weaknesses, not mop up random uncertainty.
- Tool choice and prompt choice are both interface design decisions.
- Routing, memory, and safety need versioning because drift is inevitable.

## Key Questions

- What part of Model Fallback Routing Comparison Runs is still governed by intuition instead of a contract or label set?
- Which failure in Model Fallback Routing Comparison Runs would be hardest to detect before it compounds?
- How would Model Fallback Routing Comparison Runs behave if the tool was slow, retrieval was weak, or the prompt version drifted?
- What should escalate to a human because the system is structurally unreliable there?
- Which comparison run would actually falsify the current design confidence in Model Fallback Routing Comparison Runs?

## Workflow

1. Define the agent task, the acceptable output, and the cost of being wrong or slow.
2. Map the tool, prompt, retrieval, memory, and review components that shape outcomes.
3. Label failure types and connect them to routing, escalation, or guardrail behavior.
4. Use comparison runs and trace review to isolate the real cause of behavior changes.
5. Establish quality and safety gates before increasing automation or autonomy.
6. Version prompts, thresholds, and tool assumptions so future AI work can debug drift cleanly.

## Artifacts

- A contract and failure-label set for Model Fallback Routing Comparison Runs.
- A trace-review workflow that isolates model versus system behavior.
- A human-override and escalation plan.
- A comparison-run note showing what evidence changes trust in the current design.

## Tradeoffs

- More autonomy versus more review burden.
- Cheaper tool paths versus stronger reliability.
- Prompt flexibility versus stable evaluation.
- Fast rollout versus versioned causal understanding.

## Signals To Watch

- Labeled failure rates by prompt, tool, or routing path.
- Human override volume and unresolved review queue growth.
- Behavior drift after prompt or threshold changes.
- Cost and latency concentration across the agent path.
- Tool outages or retrieval degradation that the agent hides poorly.

## Review Checklist

- [ ] The system behind Model Fallback Routing Comparison Runs is described more clearly than the prompt surface.
- [ ] Failure labels are explicit and actionable.
- [ ] Human escalation exists where structural weakness is known.
- [ ] Comparison runs and trace review can challenge the current design honestly.
- [ ] Safety, quality, and cost thresholds are explicit.
- [ ] Future AI work can reason about versioned changes without guessing the cause.

## Common Failure Modes

- Treating agent complexity as if it were still a single-prompt problem.
- Escalating randomly instead of where the system is predictably weak.
- Changing prompts and routing simultaneously until causality disappears.
- Optimizing cost or latency while the failure taxonomy remains vague.
