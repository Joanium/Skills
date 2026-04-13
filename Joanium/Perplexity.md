---
name: Perplexity AI Prompting
trigger: perplexity prompting, perplexity ai, perplexity tips, sonar prompting, perplexity api, perplexity search
description: Best practices for prompting Perplexity AI's Sonar models via API. Use when you need real-time web search integrated with LLM generation, cited answers, or current event research in automated pipelines.
---

# ROLE
You are a Perplexity Sonar prompt engineer. Your goal is to leverage Perplexity's real-time web search + generation pipeline to produce current, cited, and accurate responses.

# MODEL PERSONALITY
```
Perplexity Sonar is:
- A search-augmented LLM — every response is grounded in live web results
- Returns citations automatically (URLs + source snippets)
- Best for: current events, research, fact-checking, market data
- Not ideal for: pure creative tasks, complex multi-step reasoning
- OpenAI-compatible API — drop-in for GPT-4o with live search
- Sonar Pro: deeper research, more sources, costlier
- Sonar: fast, good for most search tasks
```

# API SETUP
```javascript
const response = await fetch("https://api.perplexity.ai/chat/completions", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${process.env.PERPLEXITY_API_KEY}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    model: "sonar-pro",
    messages: [
      {
        role: "system",
        content: "You are a market research analyst. Be concise and always cite sources."
      },
      {
        role: "user",
        content: "What are the latest funding rounds in AI infrastructure this month?"
      }
    ],
    return_citations: true,
    return_images: false,
    search_recency_filter: "month"  // week, month, year
  })
})
```

# SEARCH RECENCY CONTROL
```
search_recency_filter options:
"day"   → last 24 hours (breaking news, live events)
"week"  → last 7 days (recent developments)
"month" → last 30 days (recent trends, product releases)
"year"  → last year (general research)

Use recency filters aggressively — they focus search and reduce noise:
- Stock news, earnings → "day" or "week"
- Tech releases, product updates → "month"
- Research, background info → "year" or no filter
```

# QUERY CRAFTING FOR SEARCH
```
Perplexity searches the web based on your message.
Write prompts that are SEARCH-OPTIMIZED, not conversational:

WEAK:  "Tell me about what's happening with AI chips"
STRONG: "Latest news on AI chip supply constraints and NVIDIA/AMD production updates 2025"

WEAK:  "Is React still popular?"
STRONG: "React vs Vue vs Svelte adoption trends 2025 developer surveys"

Include:
- Specific entities (company names, product names)
- Date/year context when relevant
- The type of information you want (news, data, comparison)
```

# CITATION PARSING
```javascript
// Response includes citations array:
const data = await response.json()

const answer = data.choices[0].message.content
const citations = data.citations  // Array of URLs

// Inline citation markers appear in text as [1], [2], etc.
// Map to citations array by index (1-based):

function formatWithCitations(text, citations) {
  return text.replace(/\[(\d+)\]/g, (match, num) => {
    const url = citations[parseInt(num) - 1]
    return `[${num}](${url})`
  })
}
```

# DOMAIN FILTERING
```javascript
// Focus search on specific domains:
search_domain_filter: [
  "reuters.com",
  "bloomberg.com",
  "techcrunch.com"
]

// Exclude domains:
search_domain_filter: ["-reddit.com", "-quora.com"]

// Use for:
// - Restricting to authoritative sources
// - Avoiding user-generated content noise
// - Domain-specific research (only .gov, only .edu)
```

# SYSTEM PROMPT STRATEGIES
```
Since Perplexity always searches, system prompts should:
1. Define the analytical lens: "You are a financial analyst..."
2. Set output format: "Respond in bullet points with key numbers"
3. Set citation behavior: "Always cite sources with [n] markers"
4. Set scope: "Focus on publicly traded companies only"

DO NOT instruct Perplexity how to search — it handles that.
DO instruct it how to PRESENT and FILTER search results.
```

# MODEL SELECTION
```
model              → use case
sonar-pro          → deep research, complex multi-source synthesis
sonar              → fast searches, simple factual queries
sonar-reasoning    → search + reasoning (like o1 + web search)
sonar-reasoning-pro → hardest research + deep reasoning combined
```

# ANTI-PATTERNS
```
AVOID:
- Using Perplexity for tasks not needing live data (wasteful)
- Vague queries that lead to broad, noisy search
- Ignoring citations — they're the model's primary value
- Setting recency too tight for evergreen topics

FIX:
- Use for explicitly time-sensitive or factual tasks
- Make queries specific: entities, dates, topic type
- Parse and surface citations in your UI
- Match recency filter to topic freshness requirements
```

# REVIEW CHECKLIST
```
[ ] search_recency_filter matches topic freshness needs
[ ] Query is search-optimized (specific entities, dates)
[ ] return_citations: true enabled
[ ] Citations parsed and mapped to [n] markers
[ ] domain_filter set for authoritative-only searches
[ ] System prompt defines analytical lens and output format
[ ] Model tier matches depth of research needed
[ ] Not using Perplexity for tasks that don't need live search
```
