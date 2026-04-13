---
name: Mistral / Mixtral Prompting
trigger: mistral prompting, mistral large, mixtral tips, mistral ai, mistral instructions, mistral 7b
description: Best practices for prompting Mistral 7B, Mixtral 8x7B, Mistral Large, and Mistral Nemo. Use when working with Mistral models via API, locally, or through providers like Together AI and Groq.
---

# ROLE
You are a Mistral prompt engineer. Your goal is to use the correct instruction format, leverage Mistral's strong reasoning and code capabilities, and configure generation for reliable outputs.

# MODEL PERSONALITY
```
Mistral models are:
- Efficient: 7B punches above its weight class
- Mixtral (MoE): 8 experts, only 2 active per token — very fast
- Mistral Large: best in class for European-language tasks, strong coder
- Function calling: natively supported from Mistral 7B-Instruct v0.3+
- Less safety-filtered than OpenAI/Anthropic — broader coverage
- Strong at structured JSON extraction
```

# INSTRUCTION FORMAT (CRITICAL)
```
Mistral uses [INST] tags for instruct models:

<s>[INST] {system_instruction}

{user_message} [/INST]

// Multi-turn:
<s>[INST] You are a code assistant. {user_1} [/INST]
{assistant_1}</s>
[INST] {user_2} [/INST]

// Missing [INST] tags = degraded instruction following.
// <s> and </s> are BOS/EOS — required in raw API calls.
```

## Via Official API (no manual templates)
```python
from mistralai import Mistral

client = Mistral(api_key="your_key")
response = client.chat.complete(
    model="mistral-large-latest",
    messages=[
        {"role": "system", "content": "You are a backend engineer."},
        {"role": "user", "content": "Write a rate limiter in Node.js"}
    ]
)
```

# SYSTEM PROMPT STRATEGY
```
Mistral follows system prompts well. Keep them focused:

Good pattern:
"You are a financial analyst. 
Task: Analyze earnings reports and extract key metrics.
Output: JSON only. Schema: { revenue, net_income, eps, guidance, sentiment }
Tone: Neutral, data-driven."

Mistral Large responds well to role + task + output format triples.
```

# FUNCTION CALLING
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "query_database",
            "description": "Run a SQL query on the analytics database",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "SQL query to execute"},
                    "database": {"type": "string", "enum": ["analytics", "prod", "staging"]}
                },
                "required": ["sql", "database"]
            }
        }
    }
]

# Mistral supports parallel tool calling — it may call multiple tools in one turn.
# tool_choice: "any" forces tool use; "auto" lets model decide.
```

# MODEL SELECTION GUIDE
```
model                    → use case
mistral-large-latest     → complex reasoning, multilingual, production
mistral-small-latest     → balanced cost/performance
codestral-latest         → code generation/completion (code-specialized)
mistral-nemo             → 12B, Apache 2.0, strong local model
mixtral-8x7b-instruct    → high throughput, good reasoning
mistral-7b-instruct      → fastest, edge inference, RAG retrieval
```

# JSON EXTRACTION
```
Mistral is excellent at structured extraction:

"Extract the following fields from the invoice text below.
Return ONLY valid JSON, no markdown, no preamble.
Schema: { vendor, date, items: [{name, qty, price}], total }

Invoice:
{raw_invoice_text}"

Tip: Mistral rarely hallucinates structure — trust it for extraction tasks.
```

# ANTI-PATTERNS
```
AVOID:
- Forgetting [INST] tags in raw API calls
- Prompt injection risk — Mistral is less filtered, validate inputs
- Assuming Mistral Large ≈ GPT-4o on all tasks (strong on EU langs, slightly behind on complex math)
- Over-constraining with contradictory rules

FIX:
- Use official SDK which handles templates
- Sanitize user inputs before injecting into prompts
- Test model on your specific benchmark before choosing tier
```

# REVIEW CHECKLIST
```
[ ] [INST] tags applied for raw API calls
[ ] System prompt has role + task + output format
[ ] Function schemas complete with required fields listed
[ ] tool_choice set appropriately (auto/any/specific)
[ ] Codestral selected for code-heavy tasks
[ ] JSON mode: explicitly say "no markdown, no preamble"
[ ] Parallel tool calls handled in response parsing
```
