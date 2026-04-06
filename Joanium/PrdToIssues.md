---
name: PRD to Issues
trigger: prd to issues, break down prd into tickets, create issues from prd, implementation tickets, github issues from prd
description: Break a PRD into independently-grabbable GitHub issues using tracer-bullet vertical slices.
---

A great issue breakdown means any issue can be picked up by any developer (or agent) without needing context from the others. Each issue is a thin vertical slice — complete end-to-end, independently demoable.

## Process

### Step 1: Locate the PRD

Ask the user for the PRD GitHub issue number or URL.

If it's not already in context, fetch it:

```bash
gh issue view <number> --comments
```

### Step 2: Explore the codebase (optional)

If you haven't already explored the codebase, do so to understand the current state — this informs realistic scope boundaries per issue.

### Step 3: Draft vertical slices

Each issue is a **tracer bullet** — a thin vertical slice that cuts through ALL integration layers end-to-end.

```
VERTICAL (correct):          HORIZONTAL (wrong):
Issue: User can log in  →    Issue: Add users table
  schema change               Issue: Add /login endpoint
  API endpoint                Issue: Build login form
  UI form
  tests
```

Slices may be:

- **AFK** — can be implemented and merged without human interaction (prefer these)
- **HITL** — require human judgment (architectural decisions, design reviews, external approvals)

Rules:

- Each slice delivers a narrow but COMPLETE path through every layer
- A completed slice is demoable or verifiable on its own
- Prefer many thin issues over few thick ones

### Step 4: Quiz the user

Present the proposed breakdown as a numbered list. For each issue show:

| Field                    | Content                                |
| ------------------------ | -------------------------------------- |
| **Title**                | Short descriptive name                 |
| **Type**                 | HITL / AFK                             |
| **Blocked by**           | Which other issues must complete first |
| **User stories covered** | Which user stories from the PRD        |

Ask:

- Does the granularity feel right?
- Are blocking relationships correct?
- Should any issues be merged or split?
- Are HITL/AFK designations right?

### Step 5: Create GitHub issues

Create issues in **dependency order** (blockers first) so you can reference real issue numbers in "Blocked by" fields.

```bash
gh issue create --title "..." --body "..."
```

---

## Issue Template

```markdown
## Parent PRD

#<prd-issue-number>

## What to build

A concise description of this vertical slice. Describe end-to-end behavior,
not layer-by-layer implementation. Reference the parent PRD rather than
duplicating content.

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Blocked by

- Blocked by #<issue-number>

(Or "None — can start immediately")

## User stories addressed

- User story 3
- User story 7
```

---

## Common Mistakes

**[CRITICAL]** Do NOT close or modify the parent PRD issue.

**[CRITICAL]** Create issues in dependency order — you need real issue numbers for "Blocked by" references.

**[IMPORTANT]** Don't include file paths or line numbers in issue bodies — these go stale and make issues brittle.

**[SUGGESTION]** If you can't determine blockers, default to "None — can start immediately" and let the team sort it out.
