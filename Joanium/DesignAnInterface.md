---
name: Design an Interface
trigger: design an interface, design it twice, api design, module interface, explore interface options, compare module shapes
description: Generate multiple radically different interface designs for a module using parallel sub-agents, then compare trade-offs. Use when designing APIs, exploring interface options, or stress-testing a module shape.
---

Your first interface idea is unlikely to be the best. Generating multiple radically different designs forces you to understand the problem deeply before committing to a shape. The value is in the contrast — designs that look similar at a glance often have very different implications at scale.

## Process

### Step 1: Gather requirements

Before designing anything, answer:

```
- What problem does this module solve?
- Who are the callers? (other modules, external users, tests)
- What are the key operations?
- Any constraints? (performance, compatibility, existing patterns)
- What should be hidden inside vs exposed?
```

Ask: "What does this module need to do? Who will use it?"

### Step 2: Generate designs (parallel sub-agents)

Spawn 3+ sub-agents simultaneously. Each must produce a **radically different** approach — not stylistic variations on the same idea.

Give each agent a different constraint to force genuine divergence:

| Agent   | Constraint                                                   |
| ------- | ------------------------------------------------------------ |
| Agent 1 | Minimize method count — aim for 1–3 methods max              |
| Agent 2 | Maximize flexibility — support many use cases and extension  |
| Agent 3 | Optimize for the most common case — make the default trivial |
| Agent 4 | Take inspiration from [specific paradigm/library]            |

Each sub-agent must output:

1. Interface signature (types/methods/params)
2. Usage example showing how a caller actually uses it
3. What complexity it hides internally
4. Trade-offs of this approach

### Step 3: Present designs

Show each design sequentially with prose context. Don't just dump signatures — explain what each design is doing and why.

Let the user absorb each approach before moving to comparison.

### Step 4: Compare designs

After presenting all designs, compare on these dimensions:

**Interface simplicity:** Fewer methods, simpler params = easier to learn and use correctly. A method count is not a score — ask whether the interface matches the caller's mental model.

**General-purpose vs specialized:** Can it handle future use cases without changes? Or is it so focused that extension requires API changes?

**Implementation efficiency:** Does the interface shape allow efficient internals, or does it force awkward data transformations?

**Depth:** Small interface hiding significant complexity = deep module (good). Large interface with thin implementation = shallow module (bad). Ask: is the complexity above or below the interface?

**Ease of correct use vs ease of misuse:** Can a caller use this wrong in a way that's hard to notice?

Discuss trade-offs in **prose**, not tables. Highlight where designs diverge most and what that divergence reveals about the problem.

### Step 5: Synthesize

Often the best design combines insights from multiple options. Make an explicit recommendation — be opinionated. Then ask:

- "Which design best fits your primary use case?"
- "Any elements from other designs worth incorporating?"

---

## Evaluation Criteria (from "A Philosophy of Software Design")

**Deep module:** Small interface hiding significant complexity.

```
┌─────────────────────┐
│   Small Interface   │  ← Few methods, simple params
├─────────────────────┤
│  Deep Implementation│  ← Complex logic hidden
└─────────────────────┘
```

**Shallow module (avoid):** Large interface with thin implementation.

```
┌─────────────────────────────────┐
│       Large Interface           │  ← Many methods, complex params
├─────────────────────────────────┤
│  Thin Implementation            │  ← Just passes through
└─────────────────────────────────┘
```

---

## Anti-Patterns

**[CRITICAL]** Letting sub-agents produce similar designs — if all three look like variations on the same idea, explicitly instruct agents to be more radical.

**[CRITICAL]** Skipping the comparison — generating designs without comparing them defeats the entire purpose.

**[IMPORTANT]** Evaluating based on implementation effort — a design isn't worse because it's harder to build.

**[SUGGESTION]** Don't implement during this step — this is purely about interface shape.
