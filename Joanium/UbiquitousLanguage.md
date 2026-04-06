---
name: Ubiquitous Language
trigger: ubiquitous language, domain model, ddd, glossary, define domain terms, domain terminology, build a glossary, shared vocabulary
description: Extract a DDD-style ubiquitous language glossary from the current conversation, flagging ambiguities and proposing canonical terms. Saves to UBIQUITOUS_LANGUAGE.md.
---

A great ubiquitous language glossary ends the "what do you mean by X?" conversations. When every person on the team — devs, designers, domain experts — uses the same word for the same concept, miscommunication costs drop dramatically. The glossary is the dictionary of your domain.

## Process

### Step 1: Scan the conversation

Read the entire conversation for domain-relevant:

- **Nouns**: entities, concepts, things in the system
- **Verbs**: actions, events, processes
- **Adjectives**: states, statuses, modes

### Step 2: Identify problems

Look for:

- **Ambiguity**: same word used for different concepts
- **Synonyms**: different words used for the same concept
- **Vague terms**: overloaded words that mean different things in different contexts
- **Missing terms**: concepts that were discussed but never named

### Step 3: Propose a canonical glossary

Be opinionated:

- When multiple words exist for the same concept, pick the best one
- List others as "aliases to avoid"
- If a term is ambiguous, call it out explicitly in "Flagged ambiguities"

### Step 4: Write UBIQUITOUS_LANGUAGE.md

Save to `UBIQUITOUS_LANGUAGE.md` in the working directory.

### Step 5: Output a summary

Present the key terms and any flagged ambiguities inline in the conversation.

---

## File Format

```markdown
# Ubiquitous Language

## [Domain Area / Subdomain]

| Term        | Definition                                         | Aliases to avoid      |
| ----------- | -------------------------------------------------- | --------------------- |
| **Order**   | A customer's request to purchase one or more items | Purchase, transaction |
| **Invoice** | A request for payment sent after delivery          | Bill, payment request |

## [Another Domain Area]

| Term         | Definition                                  | Aliases to avoid       |
| ------------ | ------------------------------------------- | ---------------------- |
| **Customer** | A person or organization that places orders | Client, buyer, account |
| **User**     | An authentication identity in the system    | Login, account         |

## Relationships

- An **Invoice** belongs to exactly one **Customer**
- An **Order** produces one or more **Invoices**

## Example dialogue

> **Dev:** "When a **Customer** places an **Order**, do we create the **Invoice** immediately?"
> **Domain expert:** "No — an **Invoice** is only generated once a **Fulfillment** is confirmed."
> **Dev:** "So a single **Order** can produce multiple **Invoices**?"
> **Domain expert:** "Exactly — one per **Shipment**."

## Flagged ambiguities

- "account" was used to mean both **Customer** and **User** — these are distinct:
  a **Customer** places orders, a **User** is an authentication identity.
```

---

## Glossary Writing Rules

**Be opinionated.** Pick the best term and list alternatives as aliases to avoid.

**Flag conflicts explicitly.** Don't smooth over ambiguities — they cause bugs.

**Keep definitions tight.** One sentence max. Define what it IS, not what it does.

**Show relationships.** Use bold term names and express cardinality where obvious.

**Group into multiple tables.** When natural clusters emerge (subdomain, lifecycle, actor). One table is fine if terms are cohesive.

**Write an example dialogue.** 3–5 exchanges between a dev and domain expert that show the terms being used precisely. The dialogue should clarify the hardest distinctions.

**Domain terms only.** Skip generic programming concepts (array, function, endpoint) unless they have domain-specific meaning.

---

## Re-running

When invoked again in the same conversation:

1. Read the existing `UBIQUITOUS_LANGUAGE.md`
2. Incorporate new terms from subsequent discussion
3. Update definitions if understanding has evolved
4. Re-flag any new ambiguities
5. Rewrite the example dialogue to incorporate new terms

---

## Common Mistakes

**[CRITICAL]** Defining what a term _does_ instead of what it _is_ — definitions should be noun phrases, not function descriptions.

**[IMPORTANT]** Smoothing over ambiguities — they're the most valuable part. Surfacing a term that means two things is worth more than 10 clean definitions.

**[SUGGESTION]** Including technical jargon (REST endpoint, database table, React component) — unless these appear in domain conversations, they don't belong in the glossary.
