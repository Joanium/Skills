---
name: Kimi / Moonshot AI Prompting
trigger: kimi prompting, moonshot ai, kimi k2, kimi tips, moonshot api, kimi instructions
description: Best practices for prompting Moonshot AI's Kimi models (Kimi K2, Kimi 1.5). Use when working with Kimi's ultra-long context window, agentic tasks, or when accessing via Moonshot API or NVIDIA NIM.
---

# ROLE
You are a Kimi/Moonshot prompt engineer. Your goal is to leverage Kimi's massive context window, strong reasoning, and agentic tool use to build reliable, context-heavy AI workflows.

# MODEL PERSONALITY
```
Kimi models are:
- Kimi K2: Mixture-of-Experts model (~1T total params, 32B active)
  - Strong frontier-level reasoning, rivals Claude/GPT-4o
  - Excellent agentic tool use and multi-step planning
  - OpenAI-compatible API
- Kimi 1.5: specialized for ultra-long context (128k+)
- Both: strong Chinese + English bilingual
- Less filtered than OpenAI — broader topic coverage
- Best at: complex agent tasks, long document analysis, code
```

# API ACCESS

## Moonshot API
```javascript
const client = new OpenAI({
  baseURL: "https://api.moonshot.cn/v1",
  apiKey: process.env.MOONSHOT_API_KEY
})

const response = await client.chat.completions.create({
  model: "kimi-k2",
  messages: [
    {
      role: "system",
      content: "You are a senior software architect. Design scalable systems."
    },
    {
      role: "user",
      content: "Design a real-time notification system for 10M users."
    }
  ]
})
```

## NVIDIA NIM (Kimi K2 Thinking)
```javascript
const client = new OpenAI({
  baseURL: "https://integrate.api.nvidia.com/v1",
  apiKey: process.env.NVIDIA_NIM_API_KEY
})

// Model: moonshotai/kimi-k2-thinking
// This is the reasoning/thinking variant
```

# LONG CONTEXT USAGE
```
Kimi's strength is handling massive documents.

128k context strategy:
1. Inject full documents without chunking
2. Reference by section: "In the section titled X, find..."
3. Cross-reference: "Compare the approach in Part 1 vs Part 3"
4. Ask for synthesis: "What are the 5 most critical inconsistencies across all sections?"

For code repositories:
- Inject entire relevant modules directly
- "In the file auth.js lines 45-120, explain the token refresh logic"
- "How does the data flow from UserController to the database across all files?"

Tip: Put your QUESTION or TASK at the END of a long context prompt.
Kimi (like Gemini) anchors to recency.
```

# AGENTIC TOOL USE
```javascript
// Kimi K2 has strong native tool use:
tools: [
  {
    type: "function",
    function: {
      name: "execute_code",
      description: "Run Python code in a sandboxed environment",
      parameters: {
        type: "object",
        properties: {
          code: { type: "string", description: "Python code to execute" },
          timeout: { type: "integer", default: 30 }
        },
        required: ["code"]
      }
    }
  }
]

// Kimi K2 is good at multi-step tool chaining:
// It will plan, call tool → analyze result → call next tool
// Works well for: data analysis pipelines, research agents, code execution loops
```

# THINKING VARIANT (Kimi K2 Thinking)
```
The thinking variant on NVIDIA NIM exposes reasoning:

Usage pattern:
- Give it hard problems that need multi-step reasoning
- Let it think without interrupting
- Parse final answer after </think> block

Same parsing pattern as DeepSeek R1:
const thinkMatch = response.match(/<think>([\s\S]*?)<\/think>/)
const thinking = thinkMatch?.[1] || ""
const answer = response.replace(/<think>[\s\S]*?<\/think>/, '').trim()

Best for: algorithm design, debugging, architectural decisions
```

# DOCUMENT ANALYSIS PATTERNS
```
Kimi excels at long document workflows:

Contract review:
"I'm uploading a 200-page contract. Tasks:
1. List all obligations of Party A (chronologically)
2. Find all termination clauses and their conditions
3. Identify any unusual or non-standard provisions
4. Flag any missing standard clauses

Contract text:
{full_contract_text}"

Codebase analysis:
"Here is the full codebase for {project_name}.
{all_files_content}

Question: Trace the complete data flow for a user login request,
from HTTP request to database query to response."
```

# SYSTEM PROMPT TIPS
```
Kimi responds well to:
- Clear role definition
- Explicit output structure
- Direct instructions (no excessive hedging)

Pattern:
"You are {role}. 
Your task: {task}
Rules:
- {rule_1}
- {rule_2}
Output format: {format}"

For agentic tasks, include:
"Plan before acting. List your steps before executing tool calls."
This improves multi-step tool use quality significantly.
```

# ANTI-PATTERNS
```
AVOID:
- Underusing the context window — Kimi is built for long inputs
- Skipping "plan before acting" for agentic tasks
- Treating Kimi like a search engine — it has no live web access by default
- Very high temperature for reasoning tasks

FIX:
- Inject full documents rather than summarizing before sending
- Add "List your plan before executing" for tool use workflows
- Combine with Perplexity/Tavily for web-augmented tasks
- Keep temperature ≤ 0.7 for structured work
```

# REVIEW CHECKLIST
```
[ ] Task placed at END of long context prompts
[ ] Full documents injected (no pre-summarization needed)
[ ] Tool schemas defined for agentic workflows
[ ] "Plan before acting" added to agentic system prompts
[ ] Thinking variant selected for hard reasoning tasks
[ ] Think block parsed and stripped from output
[ ] Correct API base URL (Moonshot vs NVIDIA NIM)
[ ] Temperature ≤ 0.7 for structured or agentic tasks
```
