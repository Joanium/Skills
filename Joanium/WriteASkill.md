---
name: Write a Skill
trigger: write a skill, create a skill, new skill, build a skill, skill template, add a skill
description: Create new agent skills with proper structure, concise descriptions, and bundled resources. Use when creating, writing, or structuring a new skill.
---

A great skill is the right size — detailed enough to produce high-quality output, concise enough that the agent uses it correctly without getting lost. The description is your skill's only advertisement: if it's vague, the agent won't load the skill at the right time.

## Skill Structure

```
skill-name/
├── SKILL.md           # Main instructions (required)
├── REFERENCE.md       # Detailed docs (if SKILL.md would exceed ~100 lines)
├── EXAMPLES.md        # Usage examples (if needed)
└── scripts/           # Utility scripts (if needed)
    └── helper.js
```

Keep everything in SKILL.md until it exceeds ~100 lines. Then split into REFERENCE.md.

---

## Process

### Step 1: Gather requirements

Ask:

- What task/domain does the skill cover?
- What specific use cases should it handle?
- Are there executable scripts needed, or just instructions?
- Any reference materials to bundle?

### Step 2: Draft the skill

Create:

- `SKILL.md` with concise instructions
- Additional reference files if content exceeds 100 lines
- Utility scripts for deterministic operations (validation, formatting, etc.)

### Step 3: Review with user

Present the draft and ask:

- Does this cover your use cases?
- Anything missing or unclear?
- Should any section be more or less detailed?

---

## SKILL.md Template

```markdown
---
name: Skill Name
trigger: trigger phrase, another trigger, use case keyword
description: One sentence on what it does. Use when [specific triggers].
---

# Skill Name

## Quick start

[Minimal working example]

## Workflows

[Step-by-step processes with checklists for complex tasks]

## Common Mistakes

[What goes wrong and how to avoid it]
```

---

## Writing the Description

The description is **the only thing the agent sees** when deciding which skill to load. It surfaces in the system prompt alongside all other installed skills. Your agent reads these and picks the right skill based on the user's request.

**Give your agent just enough info to know:**

1. What capability this skill provides
2. When/why to trigger it (specific keywords, contexts, file types)

**Format:**

- Max 1024 characters
- First sentence: what it does
- Second sentence: "Use when [specific triggers]"

**Good:**

```
Extract text and tables from PDF files, fill forms, merge documents. Use when
working with PDF files or when user mentions PDFs, forms, or document extraction.
```

**Bad:**

```
Helps with documents.
```

---

## When to Add Scripts

Add utility scripts when:

- The operation is deterministic (validation, formatting, scaffolding)
- The same code would be generated repeatedly across uses
- Errors need explicit handling

Scripts save tokens and improve reliability vs. code generated on the fly.

## When to Split Files

Split into separate files when:

- `SKILL.md` exceeds ~100 lines
- Content covers distinct domains (e.g. finance schema vs. sales schema)
- Advanced features are rarely needed but take significant space

---

## Review Checklist

```
[ ] Description includes "Use when..." with specific triggers
[ ] SKILL.md is under ~100 lines
[ ] No time-sensitive information (dates, versions, URLs that rot)
[ ] Consistent terminology throughout
[ ] Concrete examples included for key workflows
[ ] References stay one level deep (no reference to a reference)
```

---

## Common Mistakes

**[CRITICAL]** A vague description — if the agent can't distinguish this skill from others by the description alone, it will pick the wrong one.

**[IMPORTANT]** SKILL.md over 100 lines — split content into REFERENCE.md so the main file stays scannable.

**[SUGGESTION]** Over-engineering with scripts — don't add scripts unless the same code would need to be re-generated repeatedly.
