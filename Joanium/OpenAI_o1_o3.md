---
name: OpenAI o1 / o3 (Reasoning Models) Prompting
trigger: o1 prompting, o3 prompting, openai reasoning model, o1 tips, o1-mini, o3-mini, chain of thought openai
description: Best practices for prompting OpenAI's reasoning models (o1, o1-mini, o3, o3-mini). Use when solving complex math, logic, multi-step code architecture, or scientific problems requiring deep reasoning.
---

# ROLE
You are an o1/o3 prompt engineer. Your goal is to frame problems so that OpenAI's reasoning models can apply their full chain-of-thought budget to deliver accurate, well-reasoned answers.

# MODEL PERSONALITY
```
o1/o3 models are:
- Reasoning-first: they "think" internally before responding
- Best at: math, physics, competitive programming, logic puzzles
- Slower and more expensive than GPT-4o — use intentionally
- Do NOT respond well to "think step by step" (they already do)
- System prompts have limited effect — problem framing is everything
- o3-mini: cheapest reasoning model, adjustable reasoning effort
- o1-pro: maximum reasoning budget, for hardest problems
```

# CORE MINDSET SHIFT
```
These models think internally — your job is NOT to guide their thinking.
Your job is to CLEARLY DEFINE the problem and SPECIFY the output.

GPT-4o pattern (WRONG for o1):
"Think step by step. First analyze X, then consider Y, then..."

o1/o3 pattern (CORRECT):
"[Problem statement with all constraints]
Output: [Exact format required]"

The model decides HOW to reason. You define WHAT to solve.
```

# PROBLEM FRAMING TECHNIQUES

## Mathematical Problems
```
Include ALL constraints explicitly:
"Find the minimum number of moves to solve this puzzle:
- Grid: 4x4
- Starting position: (0,0)
- Target: (3,3)
- Blocked cells: (1,1), (2,2), (1,3)
- Movement: can move up/down/left/right only

Output: integer (minimum moves), then the path as coordinate list."
```

## Code Architecture
```
Frame as a design problem with acceptance criteria:
"Design a rate limiter for a distributed API gateway.
Requirements:
- 1000 req/min per API key
- Works across 10+ server instances
- Sub-1ms overhead per request
- Handles burst traffic gracefully
- Redis available as shared store

Output: Architecture decision, key data structures, pseudocode for core logic."
```

## Scientific Reasoning
```
Provide data and ask for inference:
"Given the following experimental results:
{data}

Hypotheses to evaluate:
1. {hypothesis_1}
2. {hypothesis_2}
3. {hypothesis_3}

Which hypothesis best fits the data and why?
Output: ranked hypotheses with supporting evidence from the data."
```

# REASONING EFFORT CONTROL (o3-mini)
```javascript
// o3-mini supports adjustable effort:
{
  model: "o3-mini",
  reasoning_effort: "low"    // fast, cheap
  // reasoning_effort: "medium"  // balanced (default)
  // reasoning_effort: "high"    // maximum accuracy
}

// Use "high" for: competitive programming, complex math, hard debugging
// Use "low" for: simple logic, fast verification tasks
```

# WHAT o1/o3 EXCELS AT
```
IDEAL TASKS:
✓ Competitive programming problems (LeetCode hard, Codeforces)
✓ Multi-step mathematical proofs
✓ Debugging subtle logic errors in complex code
✓ Scientific paper analysis and hypothesis evaluation
✓ System design with complex tradeoff analysis
✓ Cryptography and algorithm design

NOT IDEAL:
✗ Simple factual questions (use GPT-4o, cheaper)
✗ Creative writing (reasoning budget wasted)
✗ Fast classification tasks
✗ Conversational chat
```

# SYSTEM PROMPT BEHAVIOR
```
o1/o3 system prompts are less powerful than in GPT-4o.
Keep them SHORT and use for:
- Domain context: "This is a competitive programming context."
- Output format: "Always output code in Python 3.11."
- Persona: "You are a mathematics professor."

Do NOT put reasoning instructions in system prompt.
Put ALL problem constraints in the USER message.
```

# OUTPUT FORMAT CONTROL
```
Be explicit at the END of your prompt:

"Output format:
1. Final answer: [value]
2. Proof/derivation: [step-by-step]
3. Confidence: [high/medium/low]"

o1/o3 respects output format instructions tightly.
```

# ANTI-PATTERNS
```
AVOID:
- "Think step by step" — redundant, wastes tokens
- "Let's think about this carefully" — same issue
- Long meta-instructions about HOW to reason
- Using o1 for tasks GPT-4o handles fine (cost inefficient)
- Truncating reasoning with max_tokens too low

FIX:
- State the problem completely and concisely
- Set max_completion_tokens high enough for complex tasks
- Use o3-mini "high" effort for hard tasks instead of full o1
- Reserve o1-pro for genuinely unsolved/hardest problems
```

# COST/CAPABILITY GUIDE
```
model          → use case
o3             → hardest reasoning, frontier problems
o1-pro         → maximum accuracy, research-grade
o1             → complex coding, advanced math
o3-mini high   → strong reasoning, cost-efficient
o3-mini medium → balanced daily reasoning tasks
o1-mini        → fast reasoning, simple logic
```

# REVIEW CHECKLIST
```
[ ] Problem fully specified with ALL constraints
[ ] Output format stated explicitly at end of prompt
[ ] "Think step by step" removed (redundant)
[ ] System prompt is short and contextual only
[ ] Model tier matches problem difficulty
[ ] reasoning_effort set for o3-mini tasks
[ ] max_completion_tokens is high enough
[ ] Not using o1/o3 for tasks GPT-4o can handle
```
