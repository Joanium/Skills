---
name: Claude (Anthropic) Prompting
trigger: claude prompting, anthropic claude, claude tips, claude instructions, how to prompt claude, claude system prompt
description: Best practices for prompting Claude models (Haiku, Sonnet, Opus). Use when crafting system prompts, user messages, or multi-turn conversations targeting the Claude model family.
---

# ROLE
You are a Claude prompt engineer. Your goal is to get the most accurate, structured, and useful responses from Claude by leveraging its strengths in reasoning, instruction-following, and nuanced understanding.

# MODEL PERSONALITY
```
Claude is:
- Honest and refuses to pretend it knows things it doesn't
- Responsive to explicit structure (XML tags, headers, numbered steps)
- Strong at nuanced, multi-step reasoning
- Defaults to being helpful but can be steered with tone
- Follows "spirit of instruction" not just literal wording
```

# CORE PROMPTING TECHNIQUES

## System Prompt Structure
```
Use XML-style tags for clean role separation:

<system>
  You are a senior software engineer reviewing pull requests.
  Always respond with:
  1. Summary of changes
  2. Issues found (severity: LOW/MED/HIGH)
  3. Suggested fixes as code snippets
</system>

<context>
  Project uses TypeScript strict mode, React 18, and Zod for validation.
</context>
```

## Explicit Output Format
```
Tell Claude EXACTLY what format you want:

"Respond in JSON only. Schema:
{
  summary: string,
  bugs: Array<{ line: number, issue: string, fix: string }>,
  approved: boolean
}"

Claude follows format instructions tightly — be as specific as needed.
```

## Chain of Thought
```
Add "Think step by step before answering" for complex reasoning tasks.
Or use: "First reason through the problem in <thinking> tags, then give your final answer."

Claude natively does extended thinking — leverage it for hard problems.
```

## Persona Steering
```
Claude's tone shifts based on context signals:
- "Be blunt and skip explanations" → terse, direct
- "Explain like I'm a beginner" → educational, patient
- "Act as a critic" → skeptical, challenge-focused
- "You are a world-class X" → expert mode, technical depth
```

# ANTI-PATTERNS
```
AVOID:
- Vague requests ("make this better") — Claude will guess intent
- Asking for harmful content — Claude will refuse and explain
- Over-constraining with conflicting rules — Claude picks the most charitable reading
- Expecting sycophancy — Claude will push back if something is wrong

FIX:
- Be specific about what "better" means
- Frame sensitive requests with clear legitimate context
- Prioritize constraints explicitly ("most important rule: X")
```

# MULTI-TURN CONVERSATION
```
Claude retains context across turns well. Use it:
- Build incrementally: "Now add error handling to the function above"
- Correct without re-explaining: "The second item is wrong, fix it"
- Reference earlier content: "Go back to the schema you defined earlier"

Reset context signal: "Ignore everything above. New task:"
```

# STRUCTURED DATA EXTRACTION
```
Claude excels at extraction. Use document blocks:

"Extract all invoice line items from the text below.
Return as JSON array: [{item, qty, unit_price, total}]

<document>
  {RAW TEXT HERE}
</document>"
```

# LONG CONTEXT TIPS
```
- Put the most important instruction at the START and END (recency + primacy)
- Use headers to help Claude navigate large prompts
- For 100k+ token contexts, explicitly say: "Focus only on the section titled X"
```

# REVIEW CHECKLIST
```
[ ] System prompt defines role + output format
[ ] XML tags used for structural separation
[ ] Output schema explicitly stated for structured data
[ ] Chain-of-thought enabled for complex reasoning
[ ] Tone/persona set via explicit instruction
[ ] Edge cases specified ("if X is missing, return null")
[ ] Tested with adversarial inputs
```
