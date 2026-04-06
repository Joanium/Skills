---
name: Request Refactor Plan
trigger: refactor plan, plan a refactor, refactoring rfc, refactor request, incremental refactor, safe refactor steps
description: Create a detailed refactor plan with tiny incremental commits via user interview, then file it as a GitHub issue RFC.
---

A great refactor plan is one where every commit leaves the codebase in a working state. The goal is to make change feel boring — small, safe, reversible steps that collectively get you somewhere meaningful.

_"Make each refactoring step as small as possible, so that you can always see the program working."_ — Martin Fowler

## Process

### Step 1: Deep problem description

Ask for a long, detailed description of:

- The problem they want to solve
- Any ideas they already have for solutions

Don't cut this short — the more context, the better the plan.

### Step 2: Explore the codebase

Verify the user's assertions about the current state. Understand:

- What the code actually looks like today
- What test coverage exists in this area
- What patterns are being used and why

### Step 3: Challenge the approach

Ask whether they've considered other options. Present alternatives if you see them.

Don't just execute — make sure this is the right refactor to do.

### Step 4: Detailed implementation interview

Interview the user thoroughly about the implementation. One question at a time. Provide your recommended answer for each.

Cover:

- What exactly will change
- What will NOT change (explicit scope boundary)
- What the intermediate states will look like
- How the API/interface changes (if any)

### Step 5: Hammer out exact scope

Work out precisely:

- What you plan to change
- What you explicitly plan not to change

Scope creep kills refactors. Be surgical.

### Step 6: Check test coverage

Look at the test coverage for the area being refactored.

If coverage is insufficient:

- Ask the user what their plan is for testing
- Consider adding tests before refactoring (make the existing behavior explicit first)

### Step 7: Break into tiny commits

Create a plan of commits that are as small as possible. Each commit must:

- Leave the codebase in a working state
- Pass all existing tests
- Be independently describable

**Good commit granularity:**

- Extract a function (no behavior change)
- Rename a variable throughout (no behavior change)
- Move logic from A to B while keeping A as a wrapper
- Add the new interface alongside the old one
- Switch callers one at a time
- Remove the old interface once all callers have moved

### Step 8: File the GitHub issue

```bash
gh issue create --title "Refactor: ..." --body "..."
```

---

## Issue Template

```markdown
## Problem Statement

The problem from the developer's perspective.

## Solution

The solution from the developer's perspective.

## Commits

A detailed, ordered list of the smallest possible commits.
Each commit leaves the codebase working.

1. [commit description]
2. [commit description]
   ...

## Decision Document

- Modules to be built/modified and their interfaces
- Architectural decisions made
- Schema changes
- API contracts
- Technical clarifications

(No file paths or code snippets.)

## Testing Decisions

- What makes a good test for this refactor
- Which modules will be tested
- Prior art for similar tests in the codebase

## Out of Scope

What is explicitly NOT changing in this refactor.

## Further Notes (optional)
```

---

## Common Mistakes

**[CRITICAL]** Commits that leave the codebase broken — every commit must be green.

**[CRITICAL]** Scope that grows during the plan — nail down what's NOT changing before planning what is.

**[IMPORTANT]** Refactoring without sufficient test coverage — you won't know if you broke something.

**[SUGGESTION]** Starting with the biggest change — start with the smallest safe step and build confidence.
