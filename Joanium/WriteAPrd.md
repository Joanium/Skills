---
name: Write a PRD
trigger: write a prd, create a prd, product requirements, plan a feature, new feature spec, feature document
description: Create a PRD through user interview, codebase exploration, and module design, then submit as a GitHub issue.
---

A great PRD is not a wishlist — it's a shared contract between the person who wants something built and the people who will build it. The goal is to surface assumptions, resolve ambiguities, and give future implementors everything they need to make good decisions without you in the room.

## Process

### Step 1: Deep problem interview

Ask the user for a long, detailed description of:

- The problem they want to solve (from the user's perspective, not technical)
- Any ideas they already have for solutions
- What "done" looks like to them

Let them ramble. You're listening for the real problem beneath their proposed solution.

### Step 2: Explore the codebase

Before interviewing further, explore the repo to:

- Verify the user's assertions about current behavior
- Understand the existing architecture and patterns
- Find relevant modules that will need to change
- Identify constraints they may not have mentioned

### Step 3: Relentless interview

Interview the user about every aspect of the plan until you reach shared understanding. Walk down each branch of the decision tree one question at a time. Provide your recommended answer for each question.

Never ask more than one question at a time.

### Step 4: Design the modules

Sketch out the major modules you will need to build or modify. Actively look for opportunities to extract **deep modules** — small interfaces hiding large implementations.

Check with the user:

- Do these modules match their expectations?
- Which modules should have tests written for them?

### Step 5: Write and submit the PRD

Use the template below. Submit as a GitHub issue with `gh issue create`.

---

## PRD Template

```markdown
## Problem Statement

The problem the user is facing, from the user's perspective.

## Solution

The solution, from the user's perspective.

## User Stories

A numbered list. Cover all aspects — be extensive.

1. As a [actor], I want [feature], so that [benefit]
2. ...

## Implementation Decisions

- Modules to build/modify and their interfaces
- Architectural decisions
- Schema changes
- API contracts
- Technical clarifications

(No file paths or code snippets — these go stale.)

## Testing Decisions

- What makes a good test for this feature
- Which modules will be tested
- Prior art in the codebase for similar tests

## Out of Scope

What is explicitly NOT being built in this PRD.

## Further Notes

Anything else relevant.
```

---

## Review Summary

**Overall:** PRD should be a durable contract, not a list of tasks.

**Must include before filing:**

- A clear problem statement from the user's perspective
- Extensive user stories covering edge cases
- Module design reviewed with the user

**Well done when:**

- Future implementors can make decisions without asking follow-up questions
- Out-of-scope is explicit, not implied
