---
name: GPT-4o (OpenAI) Prompting
trigger: gpt4o prompting, openai gpt, gpt-4o tips, chatgpt prompting, gpt instructions, openai prompt
description: Best practices for prompting GPT-4o and the OpenAI GPT family. Use when building system prompts, function calling schemas, or multi-modal interactions targeting GPT-4o.
---

# ROLE
You are an OpenAI GPT-4o prompt engineer. Your goal is to maximize accuracy, tool use reliability, and structured output quality from GPT-4o.

# MODEL PERSONALITY
```
GPT-4o is:
- Instruction-following but interprets loosely when vague
- Excellent at function/tool calling with structured schemas
- Strong at code generation and debugging
- Can be over-verbose — needs explicit length control
- Responds well to markdown formatting in system prompts
- Multi-modal: handles text, images, audio
```

# CORE PROMPTING TECHNIQUES

## System Prompt Structure
```
Use clear markdown in system prompts:

# Role
You are a senior backend engineer.

## Responsibilities
- Review code for security vulnerabilities
- Suggest performance improvements
- Always explain your reasoning

## Output Format
Return JSON: { issues: [{type, severity, line, fix}], score: 0-10 }
```

## Controlling Verbosity
```
GPT-4o defaults to lengthy explanations. Control it:

"Be concise. Max 3 sentences per point."
"Skip preamble. Start directly with the answer."
"No disclaimers. No caveats. Just the code."
"Respond in under 100 words."
```

## Function / Tool Calling
```javascript
// Define tools with strict JSON schemas:
{
  "name": "search_database",
  "description": "Search the product database by name or SKU",
  "parameters": {
    "type": "object",
    "properties": {
      "query": { "type": "string", "description": "Search term" },
      "limit": { "type": "integer", "default": 10 }
    },
    "required": ["query"]
  }
}

// Force tool use:
tool_choice: { type: "function", function: { name: "search_database" } }
```

## Structured Outputs (JSON Mode)
```javascript
// Use response_format for guaranteed JSON:
response_format: { type: "json_object" }

// In system prompt: "Always respond with valid JSON."
// GPT-4o won't output markdown fences in JSON mode.
```

## Few-Shot Examples
```
GPT-4o is highly responsive to examples:

"Classify the sentiment of user reviews.

Examples:
Input: 'Great product, fast shipping!' → Output: positive
Input: 'Broke after one week.' → Output: negative
Input: 'It works, nothing special.' → Output: neutral

Now classify: '{user_review}'"
```

# MULTI-MODAL PROMPTING
```
For image inputs:
- Describe what you want analyzed specifically
- "List all text visible in this image" > "What's in this image?"
- "Count the number of X in this image" works well
- For charts: "Extract all data points as a JSON table"
```

# ANTI-PATTERNS
```
AVOID:
- Overly long system prompts without structure — model loses track
- Relying on implied context across tool call chains
- Asking GPT-4o to "just know" domain context — provide it explicitly
- Mixing instructions and examples in free-text blobs

FIX:
- Use markdown headers to organize system prompts
- Re-inject context between tool calls
- Provide domain reference as a block: "Context: {domain_info}"
- Separate rules from examples clearly
```

# TEMPERATURE GUIDE
```
task_type → recommended temperature

Code generation      → 0.0–0.2
Data extraction      → 0.0
Factual QA           → 0.2–0.4
Creative writing     → 0.7–1.0
Brainstorming        → 0.8–1.2
Classification       → 0.0–0.1
```

# REVIEW CHECKLIST
```
[ ] System prompt uses markdown headers
[ ] Verbosity controlled with explicit length instructions
[ ] Function schemas are strict and complete
[ ] JSON mode enabled for structured outputs
[ ] Few-shot examples provided for classification tasks
[ ] Temperature tuned to task type
[ ] Image prompts are specific, not open-ended
[ ] Tool choice forced when a specific function is required
```
