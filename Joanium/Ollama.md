---
name: Ollama (Local Model Runner) Prompting
trigger: ollama prompting, ollama tips, ollama setup, local llm, ollama api, run llm locally, ollama configuration
description: Best practices for running and prompting AI models locally with Ollama. Use when deploying local LLMs for privacy, offline use, or development — covering model selection, API usage, Modelfiles, and optimization.
---

# ROLE
You are an Ollama deployment engineer. Your goal is to run, configure, and prompt local LLMs efficiently using Ollama — from setup to production-quality inference pipelines.

# WHAT OLLAMA DOES
```
Ollama is a local model runner that:
- Handles model downloads, chat templates, and hardware acceleration
- Exposes an OpenAI-compatible REST API at localhost:11434
- Supports: Llama, Mistral, Gemma, Phi, Qwen, DeepSeek, and 100+ models
- GPU acceleration: NVIDIA CUDA, Apple Metal (M-series), AMD ROCm
- No API keys, no internet required after model download
- Models stored in ~/.ollama/models
```

# QUICK START
```bash
# Install:
curl -fsSL https://ollama.com/install.sh | sh  # Linux/Mac
# Windows: download installer from ollama.com

# Pull and run a model:
ollama pull llama3.3
ollama run llama3.3

# One-liner with prompt:
ollama run llama3.3 "Explain async/await in JavaScript in 3 sentences"

# Run in background (API mode):
ollama serve  # Starts on http://localhost:11434
```

# OPENAI-COMPATIBLE API
```javascript
// Drop-in replacement for OpenAI SDK:
import OpenAI from "openai"

const client = new OpenAI({
  baseURL: "http://localhost:11434/v1",
  apiKey: "ollama"  // Required by SDK but ignored by Ollama
})

const response = await client.chat.completions.create({
  model: "llama3.3",  // Must be pulled first
  messages: [
    { role: "system", content: "You are a code reviewer." },
    { role: "user", content: "Review this function: ..." }
  ],
  stream: true
})

for await (const chunk of response) {
  process.stdout.write(chunk.choices[0]?.delta?.content || "")
}
```

## Python with LangChain
```python
from langchain_ollama import ChatOllama

llm = ChatOllama(model="llama3.3", temperature=0.3)
response = llm.invoke("Write a Python decorator for rate limiting")
```

# MODELFILE — CUSTOM MODELS
```dockerfile
# Create a custom model with system prompt baked in:
# File: Modelfile

FROM llama3.3

SYSTEM """
You are Aria, a senior backend engineer at TechCorp.
You write Python and Node.js. Be direct and concise.
Never add unnecessary explanations. Output complete code only.
"""

PARAMETER temperature 0.2
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 8192

# Build and run:
# ollama create aria -f Modelfile
# ollama run aria
```

# MODEL SELECTION FOR HARDWARE
```
RAM / VRAM → recommended model

4GB RAM     → phi3.5:mini, llama3.2:3b, gemma3:1b
8GB RAM     → llama3.2:8b, mistral:7b, gemma3:4b, phi4:14b-Q4
16GB RAM    → llama3.3:70b-Q4, qwen2.5:14b, gemma3:12b
32GB RAM    → llama3.3:70b, qwen2.5:32b, mixtral:8x7b
64GB+ RAM   → qwen2.5:72b, llama3.1:70b (full precision)

GPU (NVIDIA):
6GB VRAM    → 7B models (4-bit)
12GB VRAM   → 13B models (4-bit) or 7B (full)
24GB VRAM   → 33B models (4-bit) or 13B (full)
80GB VRAM   → 70B models (full precision)

Check model size before pulling:
ollama show llama3.3 --modelinfo | grep size
```

# PERFORMANCE TUNING
```bash
# Set number of GPU layers to offload:
OLLAMA_NUM_GPU=999 ollama serve  # All layers on GPU

# CPU thread count:
OLLAMA_NUM_THREAD=8 ollama serve

# Context length (tradeoff: more context = more VRAM):
# Set in Modelfile: PARAMETER num_ctx 4096

# Keep model loaded in RAM (avoid cold start):
OLLAMA_KEEP_ALIVE=24h ollama serve

# Batch size for throughput:
OLLAMA_NUM_BATCH=512 ollama serve
```

# MULTIMODAL (VISION) MODELS
```bash
ollama pull llava:13b        # LLaVA vision model
ollama pull llama3.2-vision  # Meta's vision model

# API with image:
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2-vision",
  "messages": [{
    "role": "user",
    "content": "What UI elements are in this screenshot?",
    "images": ["base64_encoded_image_here"]
  }]
}'
```

# EMBEDDING MODELS
```bash
ollama pull nomic-embed-text   # Best general embeddings
ollama pull mxbai-embed-large  # High accuracy
ollama pull all-minilm          # Smallest, fastest

# API call:
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "The quick brown fox"
}'

# Use case: local RAG without sending data to external APIs
```

# PROMPT TIPS FOR OLLAMA
```
Since Ollama handles chat templates automatically:
1. Use standard role messages (system/user/assistant)
2. Bake recurring system prompts into Modelfiles
3. Set PARAMETER temperature in Modelfile for consistent behavior
4. Use num_ctx to control context (default is 2048 — often too small)

Critical: Default context is 2048 tokens.
Increase it: PARAMETER num_ctx 8192 in Modelfile
Or per-request: options: { num_ctx: 8192 } in API call
```

# ANTI-PATTERNS
```
AVOID:
- Pulling 70B models without checking available RAM
- Using default num_ctx (2048) for code tasks — too small
- Running Ollama models cold (no keep-alive) in production
- Not quantizing large models — use Q4_K_M for best quality/size

FIX:
- Check model size with: ollama show {model} --modelinfo
- Set num_ctx to 8192+ in Modelfile or request options
- Set OLLAMA_KEEP_ALIVE=24h for production
- Use Q4_K_M quantization: ollama pull llama3.3:70b-q4_K_M
```

# REVIEW CHECKLIST
```
[ ] Hardware checked before pulling model (RAM/VRAM requirement)
[ ] num_ctx increased from default 2048 (use 8192+ for code)
[ ] Modelfile created for custom system prompts
[ ] OLLAMA_KEEP_ALIVE set to prevent cold starts
[ ] GPU offload configured (OLLAMA_NUM_GPU)
[ ] Vision model pulled for image tasks
[ ] Embedding model selected for local RAG
[ ] Quantization level matched to hardware (Q4_K_M recommended)
```
