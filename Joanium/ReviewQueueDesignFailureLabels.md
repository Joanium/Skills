---
name: Review Queue Design Failure Labels
trigger: review queue design failure labels, help with review queue design failure labels, plan review queue design failure labels, improve review queue design failure labels, expert review queue design failure labels
description: Expert-level guidance for review queue design failure labels with action-oriented workflow, review criteria, and failure patterns.
---

Review Queue Design Failure Labels is an expert agent and tooling skill for Review Queue Design. The focal concern is Failure Labels, but the real objective is helping an AI system use tools, prompts, memory, and review loops without drifting into fragile automation.

## When To Use

- Use this when Review Queue Design Failure Labels affects whether an AI system remains useful once prompts, tools, and real operational noise are involved.
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

- What part of Review Queue Design Failure Labels is still governed by intuition instead of a contract or label set?
- Which failure in Review Queue Design Failure Labels would be hardest to detect before it compounds?
- How would Review Queue Design Failure Labels behave if the tool was slow, retrieval was weak, or the prompt version drifted?
- What should escalate to a human because the system is structurally unreliable there?
- Which comparison run would actually falsify the current design confidence in Review Queue Design Failure Labels?

## Workflow

1. Define the agent task, the acceptable output, and the cost of being wrong or slow.
2. Map the tool, prompt, retrieval, memory, and review components that shape outcomes.
3. Label failure types and connect them to routing, escalation, or guardrail behavior.
4. Use comparison runs and trace review to isolate the real cause of behavior changes.
5. Establish quality and safety gates before increasing automation or autonomy.
6. Version prompts, thresholds, and tool assumptions so future AI work can debug drift cleanly.

## Artifacts

- A contract and failure-label set for Review Queue Design Failure Labels.
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

- [ ] The system behind Review Queue Design Failure Labels is described more clearly than the prompt surface.
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
