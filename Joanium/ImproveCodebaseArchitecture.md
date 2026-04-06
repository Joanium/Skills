---
name: Improve Codebase Architecture
trigger: improve architecture, find refactoring opportunities, architectural review, codebase structure, make codebase more testable, consolidate modules, ai navigable
description: Explore a codebase to surface architectural friction, find shallow modules, and propose module-deepening refactors as GitHub issue RFCs.
---

A great architectural review surfaces the places where the codebase fights you — where understanding one thing requires bouncing across five files, where tests mock everything because nothing can be tested directly, where two modules are secretly the same module split by accident. The friction you encounter while exploring IS the signal.

## Core Concept: Deep vs Shallow Modules

**Deep module (good):** Small interface hiding large implementation.

```
┌─────────────────────┐
│   Small Interface   │  ← Few methods, simple params
├─────────────────────┤
│  Deep Implementation│  ← Complex logic hidden
└─────────────────────┘
```

**Shallow module (bad):** Large interface with thin implementation.

```
┌─────────────────────────────────┐
│       Large Interface           │  ← Many methods, complex params
├─────────────────────────────────┤
│  Thin Implementation            │  ← Just passes through
└─────────────────────────────────┘
```

The goal: merge shallow modules, deepen their combined interface, and test at the boundary.

---

## Process

### Step 1: Explore the codebase

Navigate organically — don't follow rigid heuristics. Note where you experience friction:

- Where does understanding one concept require bouncing between many small files?
- Where are modules so shallow that the interface is nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, hiding the real bugs in how they're called?
- Where do tightly-coupled modules create integration risk in the seams between them?
- Which parts are untested, or hard to test?

The friction you experience is the signal.

### Step 2: Present candidates

Present a numbered list of deepening opportunities. For each:

- **Cluster**: Which modules/concepts are involved
- **Why they're coupled**: Shared types, call patterns, co-ownership of a concept
- **Dependency category**: In-process / Local-substitutable / Ports & Adapters / External mock
- **Test impact**: What existing tests would be replaced by boundary tests

Do NOT propose interfaces yet. Ask: "Which of these would you like to explore?"

### Step 3: User picks a candidate

### Step 4: Frame the problem space

Write a user-facing explanation of the problem space:

- The constraints any new interface must satisfy
- The dependencies it would need to handle
- A rough illustrative code sketch to make constraints concrete (not a proposal)

Show this to the user, then immediately proceed to Step 5 in parallel.

### Step 5: Design multiple interfaces (parallel sub-agents)

Spawn 3+ sub-agents simultaneously. Each gets a different design constraint:

| Agent   | Constraint                                                     |
| ------- | -------------------------------------------------------------- |
| Agent 1 | Minimize interface — aim for 1–3 entry points max              |
| Agent 2 | Maximize flexibility — support many use cases and extension    |
| Agent 3 | Optimize for most common caller — make default case trivial    |
| Agent 4 | Design around ports & adapters for cross-boundary dependencies |

Each sub-agent outputs:

1. Interface signature
2. Usage example
3. What complexity it hides
4. Dependency strategy
5. Trade-offs

Present designs sequentially, then compare in prose. Give your own recommendation — be opinionated.

### Step 6: User picks an interface

### Step 7: Create GitHub issue

```bash
gh issue create --title "Refactor: ..." --body "..."
```

Create immediately — don't ask for review first. Share the URL.

---

## Dependency Categories

| Category                | Description                                 | Testing Approach                             |
| ----------------------- | ------------------------------------------- | -------------------------------------------- |
| **In-process**          | Pure computation, no I/O                    | Test directly, no mocking needed             |
| **Local-substitutable** | Has local stand-ins (PGLite, in-memory FS)  | Use local stand-in in test suite             |
| **Remote but owned**    | Your own services across a network boundary | Port + HTTP adapter + in-memory test adapter |
| **True external**       | Third-party services (Stripe, Twilio, etc.) | Mock at the boundary via injected port       |

---

## GitHub Issue Template

```markdown
## Problem

- Which modules are shallow and tightly coupled
- What integration risk exists in the seams between them
- Why this makes the codebase harder to navigate and maintain

## Proposed Interface

- Interface signature (types, methods, params)
- Usage example showing how callers use it
- What complexity it hides internally

## Dependency Strategy

Which category applies and how dependencies are handled.

## Testing Strategy

- New boundary tests to write
- Old shallow-module tests to delete
- Test environment needs

## Implementation Recommendations

- What the module should own (responsibilities)
- What it should hide (implementation details)
- What it should expose (the interface contract)
- How callers should migrate to the new interface
```

---

## Common Mistakes

**[CRITICAL]** Referencing file paths in the GitHub issue — describe behaviors and contracts, not locations.

**[IMPORTANT]** Proposing similar designs across sub-agents — force genuine divergence or the comparison is useless.

**[SUGGESTION]** Don't let the test strategy be "we'll figure it out later" — resolving the dependency category is half the work.
