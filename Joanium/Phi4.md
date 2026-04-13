---
name: Phi-4 (Microsoft) Prompting
trigger: phi-4 prompting, microsoft phi, phi4 tips, phi-3 prompting, phi small model, phi edge ai
description: Best practices for prompting Microsoft's Phi-4 (and Phi-3) small language models. Use when deploying AI on-device, in resource-constrained environments, or building fast/cheap inference pipelines where model size matters.
---

# ROLE
You are a Phi-4 prompt engineer. Your goal is to get maximum quality from Microsoft's compact Phi models by understanding their strengths in reasoning and their constraints as small models.

# MODEL PERSONALITY
```
Phi-4 (14B) is:
- Punches far above its size class — beats many 70B models on reasoning
- Training focused on textbook-quality synthetic data (quality > quantity)
- Exceptional at: math, science, logical reasoning, coding
- Weak at: obscure factual knowledge, creative writing, long-form generation
- Designed for edge deployment (laptop, mobile, IoT, browser)
- Very fast — great for latency-sensitive applications
- MIT License — fully commercial, no restrictions
```

# API ACCESS

## Azure AI Foundry / GitHub Models
```python
import openai

client = openai.OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.environ["GITHUB_TOKEN"]  # GitHub Models (free tier)
)

response = client.chat.completions.create(
    model="Phi-4",
    messages=[
        {"role": "system", "content": "You are a math tutor. Show all steps."},
        {"role": "user", "content": "Solve: find all real x where x^3 - 6x^2 + 11x - 6 = 0"}
    ],
    temperature=0.1,
    max_tokens=1024
)
```

## Local via Ollama
```bash
ollama run phi4
ollama run phi3.5  # lighter, faster
```

## Local via Transformers
```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    "microsoft/phi-4",
    torch_dtype="auto",
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained("microsoft/phi-4")
```

# SYSTEM PROMPT STRUCTURE
```
Phi-4 responds well to clean, concise system prompts:

"You are a {role}. {one-line task description}.
Always {output_requirement}."

Keep system prompts SHORT — Phi-4 is a small model and long
system prompts eat into the context budget meaningfully.

Good example:
"You are a code reviewer. Find bugs and suggest fixes.
Always respond as JSON: {bugs: [{line, issue, fix}]}"
```

# REASONING TASKS (Phi-4's STRENGTH)
```
Phi-4 is exceptional at structured logical reasoning.
Leverage it with:

Math: "Solve step by step. Show each step on a new line."
Logic: "Evaluate this argument for validity. List premises, identify the conclusion, assess validity."
Code debugging: "Trace execution step by step. Identify where the bug occurs and why."

Chain of thought emerges naturally — just ask for it explicitly.
"Reason through this step by step before giving the final answer."
```

# EDGE DEPLOYMENT PATTERNS
```
Phi-4 is built for edge inference:

On-device with ONNX:
pip install onnxruntime-genai
# Use Microsoft's Phi-4 ONNX builds from HuggingFace

In browser (WebGPU):
// Use transformers.js — Phi-3 mini has browser-optimized builds
import { pipeline } from '@xenova/transformers'
const pipe = await pipeline('text-generation', 'Xenova/Phi-3-mini-4k-instruct')

Memory footprint:
Phi-4 (14B) 4-bit quantized → ~8GB RAM
Phi-3.5-mini (3.8B) 4-bit  → ~2GB RAM
```

# CONTEXT WINDOW & LENGTH
```
Phi-4: 16k token context
Phi-3-mini: 4k or 128k (long context variant)

For Phi-4 (16k):
- Keep system prompt < 200 tokens
- Leave 1000+ tokens for generation
- For code tasks: inject only relevant functions, not entire files

Phi-4 quality degrades on VERY long inputs relative to larger models.
Keep inputs focused and concise.
```

# WHAT PHI-4 DOES WELL VS POORLY
```
STRONG:
✓ Grade-school to university math
✓ Logical puzzles and deductive reasoning
✓ Python, JavaScript, SQL code generation
✓ Structured JSON extraction from clean text
✓ Short document summarization
✓ On-device inference (low latency)

WEAK:
✗ Obscure factual knowledge (limited training data breadth)
✗ Long creative writing (>1000 tokens)
✗ Complex multi-document synthesis
✗ Latest events (training cutoff)
✗ Tasks requiring very long context chains
```

# ANTI-PATTERNS
```
AVOID:
- Long system prompts — they eat context on a small model
- Expecting GPT-4-class factual breadth — Phi-4 is reasoning-strong, knowledge-narrow
- Using Phi-4 for long-form generation — quality drops past ~800 tokens
- High temperature — small models are more chaotic at high temps

FIX:
- Keep system prompts < 200 tokens
- Supplement with RAG for factual tasks
- Generate in chunks for long outputs
- Keep temperature ≤ 0.4 for structured tasks
```

# REVIEW CHECKLIST
```
[ ] System prompt is short and declarative
[ ] Task plays to Phi-4 strengths (reasoning, math, code)
[ ] Context window usage estimated (stay under 12k for safety)
[ ] Temperature ≤ 0.4 for structured tasks
[ ] Edge/ONNX build selected for on-device deployment
[ ] RAG supplement planned if factual breadth is needed
[ ] Generation length ≤ 800 tokens for best quality
```
