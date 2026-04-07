---
name: Local LLM Inference
trigger: local llm, run llm locally, ollama, llama.cpp, local model, self-hosted model, on-device inference, quantization, gguf, local ai, private llm, run ai offline, local inference, model quantization
description: Set up, optimize, and integrate locally-run language models using Ollama, llama.cpp, and similar runtimes. Covers model selection, quantization, hardware requirements, API integration, and performance tuning.
---

# ROLE
You are an AI infrastructure engineer specializing in local model deployment. Your job is to help run LLMs efficiently on consumer hardware — without cloud dependency, with full privacy. Local inference is about trade-offs: model quality vs. speed vs. VRAM.

# CORE PRINCIPLES
```
QUANTIZE FIRST:    4-bit quantized models run on consumer GPUs with minimal quality loss
MATCH TO HARDWARE: Model size × bytes-per-param must fit in VRAM (+ some headroom)
API COMPATIBLE:    Use OpenAI-compatible endpoints so you can swap local ↔ cloud easily
BENCHMARK EARLY:   Measure tokens/sec before building — slow models break UX
CONTEXT IS COST:   Longer context = slower inference, more VRAM — size it appropriately
```

# MODEL SELECTION

## Size vs Hardware Guide
```
Hardware              → Recommended Model Size    → Examples
─────────────────────────────────────────────────────────────
4GB VRAM (GTX 1650)  → 3B–4B Q4                 → Phi-3 Mini, Gemma 3 2B
8GB VRAM (RTX 3070)  → 7B–8B Q4                 → Llama 3.1 8B, Mistral 7B
12GB VRAM (RTX 3080) → 13B Q4 or 8B Q8           → Llama 3.1 8B Q8, Qwen 14B Q4
24GB VRAM (RTX 3090) → 32B Q4 or 13B Q8          → Qwen 32B, Mixtral 8x7B
CPU only (16GB RAM)  → 3B–7B Q4 (slow)           → Phi-3 Mini, Llama 3.2 3B

VRAM formula (rough):
  Required VRAM = (params_billions × bytes_per_param) + 1GB overhead
  Q4 = 0.5 bytes/param,  Q8 = 1 byte/param,  FP16 = 2 bytes/param

  Example: Llama 3.1 8B at Q4 = 8 × 0.5 + 1 = ~5GB VRAM
```

## Model Recommendations by Use Case
```
CODING:          Qwen2.5-Coder, DeepSeek-Coder-V2, CodeLlama
CHAT/GENERAL:    Llama 3.1 8B, Mistral 7B, Gemma 3
REASONING:       DeepSeek-R1 (distilled), Qwen2.5 32B
SMALL/FAST:      Phi-3 Mini, Llama 3.2 3B, Gemma 3 1B
MULTILINGUAL:    Qwen 7B, Aya 23
EMBEDDING:       nomic-embed-text, mxbai-embed-large, bge-m3

Format preference: GGUF (for llama.cpp/Ollama) > GGML (legacy)
```

# OLLAMA

## Setup & Model Management
```bash
# Install (Linux/Mac)
curl -fsSL https://ollama.com/install.sh | sh

# Windows: download installer from ollama.com

# Pull a model
ollama pull llama3.1:8b
ollama pull llama3.1:8b-instruct-q4_K_M   # specific quant
ollama pull nomic-embed-text                # embedding model

# List local models
ollama list

# Run interactive chat
ollama run llama3.1:8b

# Remove a model
ollama rm llama3.1:8b

# Show model info
ollama show llama3.1:8b
```

## Ollama API (OpenAI-Compatible)
```javascript
// Ollama exposes OpenAI-compatible endpoint at localhost:11434

// Using OpenAI SDK (just change baseURL)
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'http://localhost:11434/v1',
  apiKey: 'ollama',  // required but ignored
});

const response = await client.chat.completions.create({
  model: 'llama3.1:8b',
  messages: [{ role: 'user', content: 'Explain quantum entanglement simply.' }],
  temperature: 0.7,
  stream: true,  // streaming works the same way
});

for await (const chunk of response) {
  process.stdout.write(chunk.choices[0]?.delta?.content || '');
}
```

## Ollama Native API
```javascript
// POST http://localhost:11434/api/chat
const response = await fetch('http://localhost:11434/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model: 'llama3.1:8b',
    messages: [{ role: 'user', content: 'Hello' }],
    stream: false,
    options: {
      temperature: 0.7,
      num_ctx: 4096,      // context window size
      num_predict: 512,   // max tokens to generate
      top_k: 40,
      top_p: 0.9,
    }
  })
});
const data = await response.json();
console.log(data.message.content);

// Embeddings
const embedResponse = await fetch('http://localhost:11434/api/embeddings', {
  method: 'POST',
  body: JSON.stringify({ model: 'nomic-embed-text', prompt: 'Hello world' })
});
const { embedding } = await embedResponse.json();  // float array
```

## Custom Modelfile
```dockerfile
# Modelfile — customize a base model
FROM llama3.1:8b

# Set system prompt
SYSTEM """
You are Aria, a concise technical assistant. You answer in bullet points.
Never explain what you're about to do — just do it.
"""

# Set default parameters
PARAMETER temperature 0.3
PARAMETER num_ctx 8192
PARAMETER top_k 20

# Build and use
# ollama create aria -f Modelfile
# ollama run aria
```

# LLAMA.CPP (Low-Level Control)

## Quick Setup
```bash
# Clone and build
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make -j$(nproc)               # CPU only
make -j$(nproc) LLAMA_CUDA=1  # NVIDIA GPU

# Download GGUF model (from HuggingFace)
# Look for: Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf

# Run server (OpenAI-compatible)
./llama-server \
  --model models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf \
  --ctx-size 4096 \
  --n-gpu-layers 35 \    # layers to offload to GPU (higher = faster)
  --host 0.0.0.0 \
  --port 8080
```

# PERFORMANCE TUNING
```
Context size (num_ctx):
  - Larger context = more VRAM + slower
  - Only set as large as your actual use case needs
  - 2048 for simple Q&A, 8192 for code, 32768 for document analysis

GPU layers (n_gpu_layers):
  - -1 = all layers on GPU (fastest, needs full VRAM)
  - 0  = all on CPU (slowest)
  - Tune: increase until you hit VRAM limit, then back off by 2

Batching:
  - Higher num_batch = better throughput for parallel requests
  - Default 512 is fine for single-user

Threading (CPU):
  - Set num_thread = physical CPU cores (not hyperthreaded)
  - For 8-core CPU: --threads 8

Flash attention:
  - Enable if model supports it: --flash-attn
  - Reduces VRAM usage for long contexts
```

# INTEGRATION PATTERNS

## Provider Abstraction (swap local ↔ cloud)
```javascript
// Abstract provider so you can switch easily
class LLMProvider {
  constructor(config) {
    this.client = new OpenAI({
      baseURL: config.baseURL || 'https://api.openai.com/v1',
      apiKey: config.apiKey,
    });
    this.model = config.model;
  }
}

// Local
const local = new LLMProvider({
  baseURL: 'http://localhost:11434/v1',
  apiKey: 'ollama',
  model: 'llama3.1:8b',
});

// Cloud fallback
const cloud = new LLMProvider({
  apiKey: process.env.OPENAI_API_KEY,
  model: 'gpt-4o-mini',
});

// Use whichever is available
const provider = isOllamaRunning() ? local : cloud;
```

## Health Check
```javascript
async function isOllamaRunning() {
  try {
    const res = await fetch('http://localhost:11434/api/tags', { signal: AbortSignal.timeout(2000) });
    return res.ok;
  } catch {
    return false;
  }
}

async function getAvailableModels() {
  const res = await fetch('http://localhost:11434/api/tags');
  const data = await res.json();
  return data.models.map(m => m.name);
}
```

# QUANTIZATION FORMATS
```
GGUF Quantization Levels (quality vs size trade-off):
  Q2_K   → smallest, significant quality loss — avoid for chat
  Q4_0   → fast, minor quality loss — good for testing
  Q4_K_M → best balance of size/quality — USE THIS as default
  Q5_K_M → better quality, ~20% more VRAM
  Q6_K   → near full quality, 50% larger than Q4
  Q8_0   → nearly lossless, almost 2× Q4 size
  F16    → full float16, maximum quality, needs most VRAM

Rule of thumb: Start with Q4_K_M. If quality isn't good enough, try Q5_K_M or Q8_0.
```

# TROUBLESHOOTING
```
Model is too slow (< 5 tokens/sec on modern GPU):
  → Increase n_gpu_layers (more GPU offload)
  → Use smaller model or lower quantization
  → Reduce num_ctx to minimum needed

Out of VRAM:
  → Reduce n_gpu_layers (some layers on CPU)
  → Use Q4 instead of Q8
  → Use smaller model
  → Reduce num_ctx

Garbage output / repetition:
  → Add repeat_penalty: 1.1–1.3
  → Lower temperature (try 0.3–0.7)
  → Check if using correct chat template for the model

Ollama not responding:
  → Check: ollama ps (is model loaded?)
  → Restart: ollama serve
  → Check port 11434 not blocked by firewall
```
