---
name: Triage Issue
trigger: triage this issue, triage a bug, investigate this bug, find root cause, file an issue, report a bug, debug and file
description: Investigate a reported problem by exploring the codebase to find its root cause, then create a GitHub issue with a TDD-based fix plan.
---

A great triage takes the burden off the reporter. You investigate, you find the root cause, you write the issue. The developer who picks it up should be able to start coding without any follow-up questions.

## Process

### Step 1: Capture the problem

Get a brief description of the issue from the user.

Ask ONE question: "What's the problem you're seeing?"

Do NOT ask follow-up questions yet. Start investigating immediately.

### Step 2: Explore and diagnose

Deeply investigate the codebase. Your goal:

- **Where** the bug manifests (entry points, UI, API responses)
- **What** code path is involved (trace the flow)
- **Why** it fails (root cause, not just symptom)
- **What** related code exists (similar patterns, tests, adjacent modules)

Look at:

- Related source files and their dependencies
- Existing tests (what's covered, what's missing)
- Recent changes to affected files (`git log`)
- Error handling in the code path
- Similar patterns elsewhere that work correctly

### Step 3: Identify the fix approach

Determine:

- The minimal change needed to fix the root cause
- Which modules/interfaces are affected
- What behaviors need to be verified via tests
- Whether this is a regression, missing feature, or design flaw

### Step 4: Design TDD fix plan

Create a concrete, ordered list of RED-GREEN cycles. One cycle = one vertical slice.

Rules for the plan:

- Tests verify behavior through public interfaces, not implementation details
- One test at a time (vertical) — NOT all tests first, then all code
- Each test survives internal refactors
- Include a final REFACTOR step if needed
- **Durability**: describe behaviors and contracts, not internal structure

### Step 5: Create the GitHub issue

Create the issue immediately — don't ask for review first:

```bash
gh issue create --title "..." --body "..."
```

Share the URL with the user plus a one-line summary of the root cause.

---

## Issue Template

```markdown
## Problem

What happens (actual behavior), what should happen (expected behavior),
and how to reproduce.

## Root Cause Analysis

- The code path involved
- Why the current code fails
- Contributing factors

(No file paths, line numbers, or implementation details — describe
modules, behaviors, and contracts instead. The issue should survive refactors.)

## TDD Fix Plan

1. **RED**: Write a test that [describes expected behavior]
   **GREEN**: [Minimal change to make it pass]

2. **RED**: Write a test that [describes next behavior]
   **GREEN**: [Minimal change to make it pass]

...

**REFACTOR**: [Any cleanup after all tests pass]

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] All new tests pass
- [ ] Existing tests still pass
```

---

## Common Mistakes

**[CRITICAL]** Including file paths or line numbers in issues — these go stale within days. Describe behaviors, not locations.

**[CRITICAL]** Writing the fix plan horizontally (all RED, then all GREEN) — this produces bad tests that test imagined behavior.

**[IMPORTANT]** Asking too many clarifying questions before investigating — explore first, ask only if you're genuinely blocked.

**[SUGGESTION]** If you can't reproduce the bug, say so in the issue. That's still valuable signal.
