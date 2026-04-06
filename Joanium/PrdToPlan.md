---
name: PRD to Plan
trigger: prd to plan, implementation plan, break down prd, plan phases, tracer bullets, phase plan from prd
description: Turn a PRD into a multi-phase implementation plan using tracer-bullet vertical slices, saved as a local Markdown file.
---

A great implementation plan cuts vertically, not horizontally. Each phase should deliver something demoable end-to-end — not a layer of the stack. This is the tracer-bullet approach: fire a thin round through every layer first, then flesh out each layer in subsequent passes.

## Process

### Step 1: Confirm the PRD is in context

The PRD should already be in the conversation. If it isn't, ask the user to paste it or point you to the file. Do not proceed without it.

### Step 2: Explore the codebase

Understand the current architecture, existing patterns, and integration layers before slicing. You can't plan vertical slices without knowing the layers.

### Step 3: Identify durable architectural decisions

Before slicing, surface high-level decisions that are unlikely to change:

- Route structures / URL patterns
- Database schema shape
- Key data models
- Authentication / authorization approach
- Third-party service boundaries

These go in the plan header so every phase can reference them.

### Step 4: Draft vertical slices

**Vertical (correct):**

```
Phase 1: User can log in → creates session → lands on dashboard (empty)
Phase 2: Dashboard shows list of items
Phase 3: User can create an item
```

**Horizontal (wrong):**

```
Phase 1: Database schema
Phase 2: API layer
Phase 3: UI layer
```

Rules for slices:

- Each slice delivers a narrow but COMPLETE path through every layer (schema, API, UI, tests)
- A completed slice is demoable or verifiable on its own
- Prefer many thin slices over few thick ones
- NO specific file names, function names, or implementation details that will change
- DO include durable decisions: route paths, schema shapes, data model names

### Step 5: Quiz the user

Present the proposed breakdown as a numbered list. For each phase show:

- **Title**: short descriptive name
- **User stories covered**: which user stories from the PRD this addresses

Ask: Does the granularity feel right? Should any phases be merged or split?

Iterate until the user approves.

### Step 6: Write the plan file

Create `./plans/` if it doesn't exist. Name the file after the feature (e.g. `./plans/user-onboarding.md`).

---

## Plan Template

```markdown
# Plan: <Feature Name>

> Source PRD: <brief identifier or link>

## Architectural decisions

- **Routes**: ...
- **Schema**: ...
- **Key models**: ...

---

## Phase 1: <Title>

**User stories**: <list from PRD>

### What to build

End-to-end behavior description. Not layer-by-layer.

### Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2

---

## Phase 2: <Title>

...
```

---

## Common Mistakes

**[CRITICAL]** Slicing horizontally — "Phase 1: Database" is not a slice, it's a layer. Users can't demo a database.

**[IMPORTANT]** Including file paths or function names — these go stale within days. Describe behavior and contracts instead.

**[SUGGESTION]** Too few phases — if a phase takes more than a week, split it. Thin slices reduce integration risk.
