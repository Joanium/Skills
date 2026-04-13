---
name: Gemma 3 (Google) Prompting
trigger: gemma prompting, gemma3 tips, google gemma, gemma instructions, gemma local, gemma27b
description: Best practices for prompting Google's Gemma 3 open models (1B, 4B, 12B, 27B). Use when running Gemma locally, deploying on-device, or building privacy-first AI features without sending data to external APIs.
---

# ROLE
You are a Gemma 3 prompt engineer. Your goal is to use the correct chat template, leverage Gemma's strong instruction following, and optimize for on-device or self-hosted deployment.

# MODEL PERSONALITY
```
Gemma 3 is:
- Google's open-weight model (Apache 2.0 for 1B-9B, Gemma license for 27B)
- Gemma 3 27B rivals Gemini 1.5 Pro on many benchmarks
- Strong at: instruction following, multilingual, code, vision (27B)
- Designed for: on-premise, privacy-first, edge deployment
- Efficient architecture — runs well on consumer hardware
- No external API required — your data stays local
- Chat template is REQUIRED for instruction-tuned variants
```

# CHAT TEMPLATE (CRITICAL)
```
Gemma 3 IT (Instruction Tuned) uses this template:

<start_of_turn>user
{user_message}<end_of_turn>
<start_of_turn>model

// With system prompt (Gemma 3):
<start_of_turn>user
{system_instruction}

{user_message}<end_of_turn>
<start_of_turn>model

// Multi-turn:
<start_of_turn>user
{user_1}<end_of_turn>
<start_of_turn>model
{assistant_1}<end_of_turn>
<start_of_turn>user
{user_2}<end_of_turn>
<start_of_turn>model

// NOTE: Gemma 3 does NOT have a dedicated system role.
// Inject system instructions at the top of the first user turn.
```

## Ollama (Simplest Local Setup)
```bash
ollama run gemma3:27b
ollama run gemma3:12b
ollama run gemma3:4b  # fits in 4GB VRAM
ollama run gemma3:1b  # mobile / edge
```

## Python via Transformers
```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_id = "google/gemma-3-27b-it"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    torch_dtype=torch.bfloat16
)

chat = [
    {"role": "user", "content": "Explain transformer architecture in 5 bullet points."}
]

inputs = tokenizer.apply_chat_template(chat, return_tensors="pt", add_generation_prompt=True)
```

# SYSTEM INSTRUCTION PATTERN
```
Since Gemma has no system role, prepend instructions to user turn:

EFFECTIVE PATTERN:
<start_of_turn>user
[Instructions]
You are a senior backend engineer. Always write Python with type hints.
Output complete, runnable code with no placeholders.
[/Instructions]

Task: Write a FastAPI endpoint that validates JWT tokens.
<end_of_turn>
<start_of_turn>model

Keep instructions inside a clear wrapper like [Instructions]...[/Instructions]
to separate them visually from the task.
```

# VISION TASKS (Gemma 3 27B)
```python
# Gemma 3 27B supports image inputs:
chat = [
    {
        "role": "user",
        "content": [
            {"type": "image", "image": pil_image},
            {"type": "text", "text": "Extract all text and data from this UI screenshot as JSON."}
        ]
    }
]

# Vision-language tasks:
# - UI/screenshot analysis
# - Document OCR
# - Chart data extraction
# - Image description
```

# SIZE GUIDE
```
model         → use case / hardware requirement
Gemma 3 27B   → best quality, needs 16GB+ VRAM or 32GB RAM
Gemma 3 12B   → good balance, 8GB VRAM / 16GB RAM
Gemma 3 4B    → fast local, 4GB VRAM / 8GB RAM
Gemma 3 1B    → mobile/edge, runs on phone or Pi
```

# GENERATION PARAMETERS
```python
{
    "max_new_tokens": 1024,
    "temperature": 0.5,
    "top_p": 0.9,
    "top_k": 50,
    "repetition_penalty": 1.1,    # Helps with loops
    "do_sample": True,             # False for greedy (deterministic)
    "eos_token_id": tokenizer.eos_token_id  # Critical stop token
}
```

# STRUCTURED OUTPUT
```
Gemma follows JSON instructions well:

User turn:
"[Instructions]
Respond ONLY with valid JSON. No markdown. No explanation.
Schema: { name: string, score: number, flags: string[] }
[/Instructions]

Input: {raw_text}"

For reliable JSON: add "Think carefully before outputting" 
— Gemma tends to produce better-formed JSON when told to be careful.
```

# ANTI-PATTERNS
```
AVOID:
- Using base (non-IT) model for instruction tasks — it's for fine-tuning
- Skipping the chat template — produces incoherent outputs
- Long system instructions for small models (1B, 4B) — overwhelms them
- Expecting Gemma 4B to reason like 27B — calibrate expectations

FIX:
- Always use -it (instruction tuned) variants
- Use tokenizer.apply_chat_template() — handles template automatically
- Scale instructions to model size
- Use 27B for complex tasks, smaller models for simple tasks
```

# PRIVACY / SELF-HOSTED USE CASES
```
Gemma's key advantage: runs 100% locally.

Use for:
- Processing sensitive documents (medical, legal, financial)
- Air-gapped environments (no internet required)
- GDPR-compliant AI features (data never leaves your server)
- Cost-sensitive high-volume inference
- Custom fine-tuning on proprietary data

Quantization for lower memory:
pip install llama-cpp-python
# Use GGUF 4-bit quantized models from HuggingFace
# 27B-Q4: ~15GB, 12B-Q4: ~7GB, 4B-Q4: ~2.5GB
```

# REVIEW CHECKLIST
```
[ ] -it (instruction tuned) variant selected
[ ] Chat template applied (manually or via apply_chat_template)
[ ] System instructions injected in first user turn
[ ] repetition_penalty set to prevent loops
[ ] Model size matched to hardware and task complexity
[ ] Vision model (27B) selected for image tasks
[ ] JSON output: "Think carefully" added before schema
[ ] GGUF quantization considered for memory constraints
```
