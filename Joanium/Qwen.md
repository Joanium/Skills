---
name: Qwen 2.5 / QwQ (Alibaba) Prompting
trigger: qwen prompting, qwen2.5, qwq prompting, alibaba qwen, qwen tips, qwen instructions, qwen coder
description: Best practices for prompting Alibaba's Qwen 2.5 family (Qwen2.5, QwQ-32B, Qwen2.5-Coder). Use when working with Qwen models locally or via API for code, multilingual tasks, math reasoning, or cost-effective inference.
---

# ROLE
You are a Qwen prompt engineer. Your goal is to leverage Qwen's strong multilingual support, exceptional coding ability (Qwen2.5-Coder), and QwQ's deep reasoning to produce high-quality outputs.

# MODEL PERSONALITY
```
Qwen 2.5 family:
- Best open-source multilingual model (English + Chinese + 29 languages)
- Qwen2.5-72B rivals GPT-4o on many benchmarks
- Qwen2.5-Coder-32B: best open-source code model (rivals GPT-4o for code)
- QwQ-32B: reasoning model that rivals o1-mini for math/logic
- Very instruction-adherent — follows format instructions tightly
- Available on Hugging Face, Ollama, DashScope API (Alibaba Cloud)
```

# API ACCESS

## DashScope (Alibaba Cloud API)
```python
import openai

client = openai.OpenAI(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

response = client.chat.completions.create(
    model="qwen-plus",        # or qwen-max, qwen-turbo
    messages=[
        {"role": "system", "content": "You are a senior Python developer."},
        {"role": "user", "content": "Write a Redis-backed job queue in Python."}
    ]
)
```

## Ollama (Local)
```bash
ollama run qwen2.5:72b
ollama run qwen2.5-coder:32b
ollama run qwq  # reasoning model
```

# SYSTEM PROMPT STRUCTURE
```
Qwen follows system prompts with high precision. Use this pattern:

"# Role
You are {role}.

## Task
{specific_task_description}

## Output Format
{exact_format_required}

## Constraints
- {constraint_1}
- {constraint_2}"

Qwen respects markdown structure in system prompts — use headers.
```

# QwQ-32B — REASONING MODEL
```
QwQ is Qwen's chain-of-thought model. Similar to DeepSeek R1.

Outputs: <think>...</think> then final answer.

Best for:
- Math problems and proofs
- Algorithm design challenges
- Code debugging (multi-step reasoning)
- Logical deduction tasks

Prompting pattern:
"[Problem with all constraints stated clearly]
Reason through this step by step.
Output the final answer after your reasoning."

QwQ will think in <think> blocks automatically.
Parse the same way as R1:
const thinking = text.match(/<think>([\s\S]*?)<\/think>/)?.[1]
const answer = text.replace(/<think>[\s\S]*?<\/think>/, '').trim()
```

# QWEN2.5-CODER TIPS
```
Qwen2.5-Coder-32B is purpose-built for code.

Effective patterns:
1. Specify language + version: "Python 3.12, async/await style"
2. Specify style guide: "Follow PEP 8", "ESLint Airbnb"
3. Request complete files: "Full file, no truncation, no TODOs"
4. Give project context: "This is a FastAPI microservice with SQLAlchemy"

Code task template:
"Language: {lang}
Style: {style_guide}
Task: {what_to_build}
Constraints: {constraints}
Output: Complete, runnable {file_type} file."
```

# MULTILINGUAL TASKS
```
Qwen's multilingual strength: Chinese-English bilingual tasks.

Cross-lingual extraction:
"Extract key information from this Chinese document and output in English JSON.
Schema: { company, revenue, date, key_metrics: [] }

Document:
{chinese_text}"

Translation with tone preservation:
"Translate the following from Chinese to English.
Preserve: formal business tone, all numbers/dates, technical terms.
Do not: add explanations, change structure, paraphrase.

Text: {text}"
```

# MODEL SELECTION GUIDE
```
model                   → use case
qwen-max                → best quality, complex tasks
qwen-plus               → balanced cost/performance
qwen-turbo              → fast, cheap, simple tasks
qwen2.5-72b             → best open-source general purpose
qwen2.5-coder-32b       → best open-source code model
qwq-32b                 → math, reasoning, logic (o1-class)
qwen2.5-7b              → edge inference, fast local tasks
```

# ANTI-PATTERNS
```
AVOID:
- Using base (non-instruct) models for chat — use instruct variants
- Skipping language context for multilingual tasks
- Assuming QwQ is fast — it's slow (thinking model), plan accordingly
- Generic prompts for Coder — it performs much better with specifics

FIX:
- Always use -Instruct model variants for instruction tasks
- Specify source + target language explicitly
- Cache QwQ responses, don't call for time-sensitive paths
- Provide full project context for Coder tasks
```

# REVIEW CHECKLIST
```
[ ] Correct model variant selected (instruct vs base)
[ ] System prompt uses markdown headers
[ ] Qwen2.5-Coder used for code tasks
[ ] QwQ think blocks parsed and stripped from output
[ ] Language explicitly specified for multilingual tasks
[ ] Code prompts include: language, style, complete file instruction
[ ] DashScope or Ollama endpoint configured correctly
[ ] Temperature ≤ 0.5 for code/structured tasks
```
