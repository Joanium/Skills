---
name: DeepSeek V3 / R1 Prompting
trigger: deepseek prompting, deepseek v3, deepseek r1, deepseek tips, deepseek coder, deepseek instructions
description: Best practices for prompting DeepSeek V3 and DeepSeek R1 (reasoning model). Use when targeting DeepSeek for code generation, mathematical reasoning, or cost-effective GPT-4-class completions.
---

# ROLE
You are a DeepSeek prompt engineer. Your goal is to leverage DeepSeek's exceptional coding ability, math reasoning (R1), and cost efficiency to produce reliable, production-quality outputs.

# MODEL PERSONALITY
```
DeepSeek V3:
- Rivals GPT-4o at a fraction of the cost
- Exceptional at code generation and debugging
- Strong multilingual (English + Chinese primary)
- Follows instructions precisely when clearly stated
- OpenAI-compatible API — easy to swap from GPT-4

DeepSeek R1:
- Reasoning model (like o1) with visible thinking chain
- Best open-source model for math and logic
- Slower — uses thinking tokens before answering
- Exposes <think>...</think> block in output
```

# SYSTEM PROMPT STRUCTURE
```
DeepSeek uses OpenAI-compatible chat format:

{
  "model": "deepseek-chat",  // V3
  "messages": [
    {
      "role": "system",
      "content": "You are an expert Python developer. Always write production-ready code with type hints, docstrings, and error handling."
    },
    {
      "role": "user",
      "content": "Write a FastAPI endpoint that accepts a CSV upload and returns summary statistics."
    }
  ]
}
```

## Base URL for DeepSeek API
```javascript
const client = new OpenAI({
  baseURL: "https://api.deepseek.com",
  apiKey: process.env.DEEPSEEK_API_KEY
})
```

# DEEPSEEK R1 — REASONING MODEL
```
R1 exposes its thinking process. Use it for:
- Complex math problems
- Algorithm design
- Multi-step logical deductions
- Code architecture decisions

Response contains:
<think>
  ... model's internal reasoning ...
</think>
Final answer here.

Parse thinking separately:
const thinking = response.match(/<think>([\s\S]*?)<\/think>/)?.[1]
const answer = response.replace(/<think>[\s\S]*?<\/think>/, '').trim()

Do NOT interrupt the thinking block — let it complete fully.
```

# CODE GENERATION TIPS
```
DeepSeek Coder / V3 code prompting:

Be specific about:
1. Language + version: "Python 3.11", "TypeScript 5.3", "Node.js 20"
2. Libraries to use/avoid: "Use only stdlib", "Use axios not fetch"
3. Style: "PEP8", "ESLint airbnb rules"
4. Output: "Complete file, no placeholders, no TODO comments"

Strong prompt pattern:
"Write a complete, production-ready {language} {component_type}.
Requirements:
- {requirement_1}
- {requirement_2}
Constraints:
- No external dependencies except {allowed_libs}
- Handle all edge cases
- Include error handling"
```

# STRUCTURED OUTPUT
```
DeepSeek follows JSON instructions reliably:

System: "You are a data extractor. Respond ONLY with valid JSON matching this schema exactly: {schema}. No markdown. No explanation."

For R1, add: "After your thinking, output ONLY the JSON object."

DeepSeek will follow schema tightly — good for pipelines.
```

# TEMPERATURE GUIDE
```
task                  → temperature
Code generation       → 0.0–0.1
Bug fixing            → 0.0
Structured extraction → 0.0
Creative/brainstorm   → 0.7–1.0
R1 reasoning tasks    → 0.6 (default, don't go high)
```

# ANTI-PATTERNS
```
AVOID:
- Vague code requests ("write a web scraper") without specifics
- High temperature on R1 — degrades reasoning quality
- Parsing R1 output before <think> block completes
- Assuming DeepSeek knows your private codebase context

FIX:
- Be explicit about tech stack, version, style guide
- Keep R1 temperature at 0.6 or below
- Always strip <think> block before processing R1 output
- Inject relevant code context in the user message
```

# CONTEXT WINDOW
```
deepseek-chat (V3): 64k context window
deepseek-reasoner (R1): 64k input, 32k thinking + output

For large codebases:
- Inject only the relevant files
- Use file path headers: "// File: src/utils/auth.ts"
- Ask for focused changes: "Only modify the validateToken function"
```

# REVIEW CHECKLIST
```
[ ] OpenAI-compatible base URL configured
[ ] System prompt includes language version and style guide
[ ] Temperature set to 0.0–0.1 for code tasks
[ ] R1 thinking block parsed and stripped before processing
[ ] JSON schema provided inline for structured outputs
[ ] Code requests specify: no placeholders, complete files
[ ] Context window usage estimated before sending large payloads
```
