---
name: Release Branch Management Evidence Packets
trigger: release branch management evidence packets, help with release branch management evidence packets, plan release branch management evidence packets, improve release branch management evidence packets, expert release branch management evidence packets
description: Expert-level guidance for release branch management evidence packets with action-oriented workflow, review criteria, and failure patterns.
---

Release Branch Management Evidence Packets is an expert repository and delivery skill for Release Branch Management. The focal concern is Evidence Packets, but the real objective is helping an AI navigate large code changes without losing causal clarity, reviewer trust, or rollback safety.

## When To Use

- Use this when Release Branch Management Evidence Packets determines whether a large or risky code change can be reasoned about cleanly before it lands.
- Use this when the AI needs stronger repository-level judgment than local patch editing alone provides.
- Use this when review friction, merge complexity, or release pressure are part of the technical problem.
- Use this when change safety depends on understanding code relationships beyond a single file.

## Core Principles

- Repository change quality depends on scope discipline as much as code quality.
- Reviewer trust comes from evidence and clarity, not from patch size alone.
- Merge and release mechanics are part of the engineering design, not administrative cleanup.
- Blast radius should be reasoned about before rebases or staging create false confidence.
- A change that cannot be explained simply is usually not ready to merge.

## Key Questions

- What repository-level dependency makes Release Branch Management Evidence Packets riskier than the diff itself suggests?
- Which reviewer would challenge Release Branch Management Evidence Packets first, and what evidence would they need?
- How could Release Branch Management Evidence Packets fail after rebasing, backporting, or partial cherry-picking?
- What hidden coupling in Release Branch Management Evidence Packets would only become obvious during staging or release?
- How will the AI explain the intended blast radius of Release Branch Management Evidence Packets concretely?

## Workflow

1. Start by mapping the files, packages, and reviewer concerns that define the real change surface.
2. Separate repository mechanics from code mechanics so each can be evaluated honestly.
3. Prepare evidence for the risky boundaries before trying to compress or reorganize the diff.
4. Plan staging, rebasing, and release sequencing as first-class parts of the change.
5. Review the patch from the perspective of merge safety, rollback clarity, and reviewer comprehension.
6. Record the resulting repository-level lessons so future AI passes can move faster without guessing.

## Artifacts

- A blast-radius note for Release Branch Management Evidence Packets.
- A reviewer and approval plan for the change set.
- A staging or backport sequence for risky paths.
- A follow-through checklist that keeps repository mechanics aligned with code intent.

## Tradeoffs

- Smaller diffs versus fewer review cycles.
- Aggressive cleanup versus repository stability during release windows.
- Merge convenience versus long-term branch hygiene.
- Local code simplification versus monorepo-wide dependency ripple effects.

## Signals To Watch

- Review churn caused by unclear scope or weak evidence.
- Release or rebase failures after supposedly straightforward merges.
- Time lost untangling dependency effects across the repository.
- Backport errors caused by poorly isolated change sets.
- Reviewer confusion about what the patch is actually trying to accomplish.

## Review Checklist

- [ ] The repository-level blast radius of Release Branch Management Evidence Packets is explicit.
- [ ] Reviewer expectations and approval needs are anticipated.
- [ ] Merge, rebase, and staging risks are part of the plan.
- [ ] The diff structure supports comprehension instead of hiding risk.
- [ ] Rollback or backport strategy is real, not implied.
- [ ] Future AI work can build on a recorded understanding of the change surface.

## Common Failure Modes

- Treating repository mechanics as separate from engineering safety.
- Compressing a diff until the causal story disappears.
- Backporting or rebasing without a clear mental model of the blast radius.
- Optimizing for merge speed while reviewer understanding collapses.
