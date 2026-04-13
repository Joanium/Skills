---
name: Groq (LPU Inference) Prompting
trigger: groq prompting, groq api, groq tips, groq lpu, groq fast inference, llama on groq, mixtral on groq
description: Best practices for using Groq's LPU inference platform for ultra-fast AI inference. Use when latency is critical, streaming responses are needed in real-time, or when running Llama/Mixtral/Gemma at maximum speed.
---

# ROLE
You are a Groq platform engineer. Your goal is to optimize prompts and requests for Groq's LPU hardware to achieve maximum throughput, minimum latency, and reliable high-speed streaming.

# WHAT GROQ IS
```
Groq is NOT a model — it's an inference platform using custom LPU chips.

Key facts:
- 10-100x faster than GPU inference for the same models
- Runs: Llama 3.3/3.1, Mixtral, Gemma 2, Whisper, and others
- Best-in-class for: real-time chat, streaming, voice pipelines
- OpenAI-compatible API — drop-in replacement
- Rate limits exist — optimize request size to stay within them
- Free tier available with generous limits for dev/testing
```

# API SETUP
```javascript
import Groq from "groq-sdk"

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY })

const response = await groq.chat.completions.create({
  model: "llama-3.3-70b-versatile",
  messages: [
    { role: "system", content: "You are a fast response assistant. Be concise." },
    { role: "user", content: "Explain Redis caching in 3 bullet points." }
  ],
  temperature: 0.5,
  max_tokens: 1024,
  stream: true  // Groq's streaming is FAST — use it
})

// Handle stream:
for await (const chunk of response) {
  process.stdout.write(chunk.choices[0]?.delta?.content || "")
}
```

# STREAMING OPTIMIZATION
```javascript
// Groq's primary advantage is streaming speed.
// Use streaming for all user-facing interfaces:

async function streamToUI(prompt, onChunk) {
  const stream = await groq.chat.completions.create({
    model: "llama-3.3-70b-versatile",
    messages: [{ role: "user", content: prompt }],
    stream: true,
    max_tokens: 2048
  })

  for await (const chunk of stream) {
    const text = chunk.choices[0]?.delta?.content
    if (text) onChunk(text)
  }
}

// Typical streaming speed on Groq: 700-900 tokens/second
// vs GPU cloud: 50-100 tokens/second
```

# MODEL SELECTION ON GROQ
```
model                           → best use
llama-3.3-70b-versatile         → best quality general tasks
llama-3.1-70b-versatile         → same tier, slightly older
llama-3.1-8b-instant            → max speed, simple tasks
mixtral-8x7b-32768              → long context (32k), balanced
gemma2-9b-it                    → lightweight, efficient
llama3-groq-70b-8192-tool-use   → function calling optimized
llama3-groq-8b-8192-tool-use    → fast function calling
whisper-large-v3                → speech-to-text (fastest on planet)
distil-whisper-large-v3-en      → English-only, even faster STT
```

# FUNCTION CALLING ON GROQ
```javascript
// Use tool-use optimized models:
const response = await groq.chat.completions.create({
  model: "llama3-groq-70b-8192-tool-use",
  messages: [{ role: "user", content: "Get the weather in Mumbai" }],
  tools: [
    {
      type: "function",
      function: {
        name: "get_weather",
        description: "Get current weather for a location",
        parameters: {
          type: "object",
          properties: {
            location: { type: "string" },
            unit: { type: "string", enum: ["celsius", "fahrenheit"] }
          },
          required: ["location"]
        }
      }
    }
  ],
  tool_choice: "auto"
})
```

# REAL-TIME VOICE PIPELINE
```javascript
// Groq Whisper + Llama = fastest voice AI pipeline:

// 1. Transcribe audio (Groq Whisper):
const transcription = await groq.audio.transcriptions.create({
  file: audioBuffer,
  model: "whisper-large-v3",
  language: "en"
})

// 2. Generate response (Groq Llama, streaming):
const stream = await groq.chat.completions.create({
  model: "llama-3.3-70b-versatile",
  messages: [
    { role: "system", content: "You are a voice assistant. Respond conversationally in 1-2 sentences." },
    { role: "user", content: transcription.text }
  ],
  stream: true,
  max_tokens: 150  // Keep short for voice
})

// Total pipeline latency: ~200-400ms (vs 2-5s on GPU cloud)
```

# RATE LIMIT MANAGEMENT
```
Groq rate limits (free tier):
- 6,000 req/min (RPM) — usually not hit
- 500,000 tokens/min (TPM) — watch this
- 30 req/min for large models (70B)

Optimization strategies:
1. Keep prompts concise — don't waste tokens
2. Set max_tokens appropriately — don't request 4096 for short answers
3. Use 8B models for high-frequency tasks
4. Batch non-urgent requests with delays

Rate limit error handling:
try {
  const response = await groq.chat.completions.create(...)
} catch (e) {
  if (e.status === 429) {
    await delay(60000)  // Wait 1 min, retry
    // Or implement exponential backoff
  }
}
```

# PROMPT OPTIMIZATION FOR SPEED
```
Groq's speed scales with TOKEN EFFICIENCY.
Fewer tokens in/out = faster responses even on LPU.

Concise system prompts:
SLOW: "You are an expert software engineer with 20 years of experience..."
FAST: "You are a senior dev. Be concise and direct."

Output constraints:
"Max 3 sentences." / "Under 100 words." / "List format only."

Prefill responses:
// Start the assistant's response to force format:
messages: [
  { role: "user", content: "List 5 JavaScript frameworks." },
  { role: "assistant", content: "1." }  // Model continues from here
]
```

# ANTI-PATTERNS
```
AVOID:
- Not using streaming — defeats Groq's primary advantage
- Sending large prompts for simple tasks — token-inefficient
- Using 70B model when 8B suffices — wastes rate limit quota
- Ignoring rate limits — exponential backoff is essential
- Long max_tokens for short answers — Groq still has to generate them

FIX:
- Enable streaming for all user-facing outputs
- Match model size to task complexity
- Set max_tokens based on expected output length
- Implement retry with backoff for 429 errors
```

# REVIEW CHECKLIST
```
[ ] stream: true enabled for user-facing responses
[ ] Model size matched to task complexity
[ ] max_tokens set to realistic expected output length
[ ] Tool-use model selected for function calling tasks
[ ] Whisper model selected for audio transcription
[ ] Rate limit retry with backoff implemented
[ ] System prompt is concise (under 100 tokens)
[ ] Token count estimated to avoid TPM limit
```
