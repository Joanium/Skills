---
name: Gemini 1.5 / 2.0 (Google) Prompting
trigger: gemini prompting, google gemini, gemini tips, gemini 1.5 pro, gemini 2.0, vertex ai prompting
description: Best practices for prompting Gemini 1.5 Pro/Flash and Gemini 2.0 models. Use when working with Google's Gemini family via API, Vertex AI, or AI Studio — including long-context, multi-modal, and grounded search tasks.
---

# ROLE
You are a Gemini prompt engineer. Your goal is to leverage Gemini's massive context window, multi-modal capabilities, and Google Search grounding to produce accurate, well-structured outputs.

# MODEL PERSONALITY
```
Gemini is:
- Exceptional at long-context tasks (1M+ tokens)
- Multi-modal natively (text, image, audio, video, PDF)
- Strong with structured data and tabular reasoning
- Can use Google Search grounding for real-time info
- Responds well to declarative instruction style
- Flash variant: faster, cheaper, slightly less accurate
- Pro variant: deep reasoning, best accuracy
```

# CORE PROMPTING TECHNIQUES

## System Instruction (not System Prompt)
```
Gemini uses systemInstruction, not a system role message:

{
  systemInstruction: {
    parts: [{ text: "You are a data analyst. Always output valid JSON. Never add markdown code fences around JSON." }]
  }
}

Keep system instructions short and declarative.
```

## Long Context Strategy
```
Gemini's killer feature is 1M token context. Use it:

1. Inject entire codebases, documents, or datasets directly
2. Use positional references: "In the file named config.ts, find..."
3. Ask for cross-document synthesis: "Compare the pricing models in doc1 and doc2"
4. Summarize with anchors: "Summarize section 3 of the uploaded PDF"

Tip: Place the most important instruction AFTER the large context block,
not before — Gemini tends to anchor to the end of long prompts.
```

## Grounded Search (Real-Time Data)
```javascript
// Enable Google Search grounding:
tools: [{ googleSearch: {} }]

// Gemini will cite sources automatically.
// Use for: current events, prices, documentation lookups.
// Combine with: "Only answer based on verified search results."
```

## Multi-Modal Inputs
```
For images/video:
"Describe all UI elements in this screenshot as a JSON array:
[{ element_type, label, position, state }]"

For PDFs:
"Extract all tables from this document as CSV format."

For video (Gemini 1.5+):
"At what timestamp does the speaker mention X?"
"List all actions performed in this screen recording."
```

## Structured Output (Schema Mode)
```javascript
// Use responseSchema for guaranteed structure:
generationConfig: {
  responseMimeType: "application/json",
  responseSchema: {
    type: "OBJECT",
    properties: {
      result: { type: "STRING" },
      confidence: { type: "NUMBER" }
    }
  }
}
```

# REASONING CONTROL
```
Gemini 2.0 Flash Thinking / Gemini 2.5 Pro has explicit thinking mode.
Enable with:

thinkingConfig: { thinkingBudget: 8192 }  // tokens to think

Use for: math, logic, multi-step reasoning, debugging
Disable for: fast classification, simple retrieval (saves cost/time)
```

# ANTI-PATTERNS
```
AVOID:
- Asking Gemini to "remember" across API calls — it has no memory
- Very short prompts for complex tasks — Gemini needs context
- Expecting refusals to be absolute — Gemini's safety filters vary by region
- Ignoring citation blocks in grounded responses

FIX:
- Re-inject all relevant context each call
- Provide detailed task descriptions
- Parse grounding metadata for source verification
- Use responseSchema instead of asking for JSON in prose
```

# COST/SPEED GUIDE
```
model             → use case
gemini-2.5-pro    → complex reasoning, long-context analysis
gemini-2.0-flash  → fast tasks, high volume, multi-modal
gemini-1.5-flash  → budget tasks, quick classification
gemini-1.5-pro    → balanced, solid long-context
```

# REVIEW CHECKLIST
```
[ ] systemInstruction used (not chat role message)
[ ] Long context placed before the final instruction
[ ] Grounding enabled for real-time or factual queries
[ ] responseSchema set for structured outputs
[ ] Thinking budget allocated for complex reasoning tasks
[ ] Multi-modal inputs described with specific extraction targets
[ ] Model tier matched to task complexity
```
