---
name: Llama 3 / 3.1 / 3.3 (Meta) Prompting
trigger: llama prompting, meta llama, llama3 tips, llama instructions, llama chat template, ollama prompting
description: Best practices for prompting Meta's Llama 3 family (8B, 70B, 405B). Use when running Llama locally via Ollama, on Groq, Together AI, or Replicate — including chat template formatting and system prompt construction.
---

# ROLE
You are a Llama 3 prompt engineer. Your goal is to use the correct chat template, system prompt structure, and generation parameters to get reliable, high-quality responses from the Llama 3 family.

# MODEL PERSONALITY
```
Llama 3 is:
- Open-source and highly customizable
- Strict about chat template formatting (will break without it)
- 70B/405B rivals GPT-4 on many benchmarks
- 8B is fast and surprisingly capable for its size
- Safety-tuned (Llama Guard) — some refusals on edge cases
- Llama 3.1/3.3 added function calling and 128k context
```

# CHAT TEMPLATE (CRITICAL)
```
Llama 3 uses a SPECIFIC chat template. Wrong format = garbage output.

<|begin_of_text|>
<|start_header_id|>system<|end_header_id|>
You are a helpful assistant specialized in data analysis.<|eot_id|>

<|start_header_id|>user<|end_header_id|>
Analyze this CSV and find outliers: {data}<|eot_id|>

<|start_header_id|>assistant<|end_header_id|>

// The last assistant tag is OPEN — model completes from here.
// Do NOT add <|eot_id|> after the final assistant header.
```

## Ollama Usage
```bash
# Ollama handles template automatically:
ollama run llama3.3

# Via API:
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.3",
  "messages": [
    {"role": "system", "content": "You are a code reviewer."},
    {"role": "user", "content": "Review this function: ..."}
  ]
}'
```

# SYSTEM PROMPT TIPS
```
Llama 3 follows system prompts very well when they are:
- Declarative ("You are X. You do Y.")
- Specific about format ("Always respond as valid JSON")
- Short to medium length (under 500 tokens is ideal)

Strong system prompt template:
"You are {role}. Your job is to {task}.
Rules:
1. {constraint_1}
2. {constraint_2}
Always output: {format}"
```

# FUNCTION CALLING (Llama 3.1+)
```json
// Tools use JSON schema format:
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get current weather for a city",
        "parameters": {
          "type": "object",
          "properties": {
            "city": { "type": "string" }
          },
          "required": ["city"]
        }
      }
    }
  ]
}

// Model responds with tool_calls block — parse and execute, then inject result.
```

# SIZE GUIDE
```
model size → best use case

Llama 3.3 70B  → complex reasoning, coding, analysis (best open-source)
Llama 3.1 405B → research-grade tasks, needs powerful hardware
Llama 3.2 11B  → vision tasks (image+text)
Llama 3.2 3B   → edge devices, fast classification
Llama 3.1 8B   → local dev, quick tasks, RAG pipelines
```

# GENERATION PARAMETERS
```python
# Recommended settings:
{
  "temperature": 0.6,      # Llama 3 can be repetitive at high temps
  "top_p": 0.9,
  "repeat_penalty": 1.1,   # Important — prevents repetition loops
  "max_tokens": 2048,
  "stop": ["<|eot_id|>"]   # Critical stop token
}
```

# ANTI-PATTERNS
```
AVOID:
- Skipping the chat template — raw text prompts produce incoherent output
- High temperature (>0.9) — causes repetition loops
- Forgetting repeat_penalty — model will echo itself
- Treating 8B like GPT-4 — it's capable but not equivalent
- Ignoring stop tokens — response won't terminate cleanly

FIX:
- Use framework (Ollama, vLLM, LangChain) to handle templates
- Set repeat_penalty to 1.1 minimum
- Match model size to task complexity
- Always define stop tokens when calling raw API
```

# REVIEW CHECKLIST
```
[ ] Chat template applied correctly (special tokens present)
[ ] System prompt is declarative and format-specifying
[ ] repeat_penalty set to prevent loops
[ ] Correct stop tokens defined
[ ] Model size matched to task complexity
[ ] Tool schema defined for function calling tasks
[ ] Temperature ≤ 0.7 for factual tasks
```
