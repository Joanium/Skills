---
name: Grok (xAI) Prompting
trigger: grok prompting, xai grok, grok tips, grok instructions, grok2, grok3
description: Best practices for prompting Grok 2 and Grok 3 from xAI. Use when working with Grok via the xAI API or X platform — including real-time web access, image generation, and live X/Twitter data tasks.
---

# ROLE
You are a Grok prompt engineer. Your goal is to leverage Grok's real-time data access, X platform integration, and strong reasoning to produce accurate, up-to-date outputs.

# MODEL PERSONALITY
```
Grok is:
- Opinionated and direct — more personality than most models
- Has real-time access to X (Twitter) data and web search
- Elon Musk-influenced tone: concise, anti-bureaucratic, technically precise
- Grok 3 matches frontier models (GPT-4o, Claude Sonnet) on benchmarks
- Less safety-filtered than OpenAI — handles edgier topics more openly
- Strong at current events, market data, and social media analysis
- OpenAI-compatible API (easy integration)
```

# SYSTEM PROMPT STRUCTURE
```javascript
// xAI API (OpenAI-compatible):
const client = new OpenAI({
  baseURL: "https://api.x.ai/v1",
  apiKey: process.env.XAI_API_KEY
})

const response = await client.chat.completions.create({
  model: "grok-3",
  messages: [
    {
      role: "system",
      content: "You are a financial analyst focused on tech stocks. Be direct. No disclaimers."
    },
    {
      role: "user",
      content: "Analyze $NVDA's recent performance and sentiment on X."
    }
  ]
})
```

# REAL-TIME DATA ACCESS
```
Grok's unique strength: live X data + web search.

For real-time tasks:
- "What is the current sentiment on X about {topic}?"
- "Find the latest news about {company} from the past 24 hours"
- "What are top posts about {trending_topic} on X right now?"
- "Summarize what {public_figure} has posted about {topic} this week"

For live web search:
- "Search for the current price of {asset}"
- "Find the latest documentation for {library} version {X}"
- "What happened in {event} today?"
```

# GROK'S TONE — MATCHING IT
```
Grok is direct and slightly irreverent. Prompts that work well:

EFFECTIVE:
- "No fluff. Just the answer."
- "Be blunt. What's wrong with this approach?"
- "Skip the caveats. Give me your actual opinion."
- "What does the data actually say, not what people want to hear?"

LESS EFFECTIVE:
- Overly polite, hedged prompting
- Asking for "balanced perspectives" on clear factual matters
- Long-winded multi-paragraph instructions
```

# IMAGE UNDERSTANDING (Grok Vision)
```
Grok supports image inputs:

{
  role: "user",
  content: [
    {
      type: "image_url",
      image_url: { url: "https://..." }
    },
    {
      type: "text",
      text: "Extract all data from this chart as JSON."
    }
  ]
}

Strong at: chart reading, screenshot analysis, document OCR.
```

# X PLATFORM ANALYSIS PATTERNS
```
Specialized prompts for X data tasks:

Sentiment analysis:
"Analyze X sentiment for {ticker/topic} over the past week.
Classify overall sentiment and identify the top 3 talking points."

Influencer tracking:
"Find key opinion leaders discussing {topic} on X. 
List them with approximate reach and their stance."

Trend detection:
"What are the emerging narratives around {topic} on X?
Identify any coordinated messaging or unusual activity."
```

# FUNCTION CALLING
```javascript
// Grok supports OpenAI-compatible tool calling:
tools: [
  {
    type: "function",
    function: {
      name: "get_x_sentiment",
      description: "Get real-time sentiment from X for a given ticker or keyword",
      parameters: {
        type: "object",
        properties: {
          keyword: { type: "string" },
          timeframe: { type: "string", enum: ["1h", "24h", "7d"] }
        },
        required: ["keyword"]
      }
    }
  }
]
```

# ANTI-PATTERNS
```
AVOID:
- Over-hedged prompts — Grok responds better to directness
- Assuming Grok has personal memory between sessions
- Using it for tasks needing extreme precision (it's strong but not infallible)
- Ignoring that X data has noise — ask Grok to filter signal from noise

FIX:
- Be direct and specific
- Ask for confidence levels: "How confident are you in this?"
- Request source attribution: "Cite the X posts or sources"
- For critical data, cross-reference with other sources
```

# REVIEW CHECKLIST
```
[ ] xAI base URL configured correctly
[ ] Real-time/live data tasks routed to Grok (not cached models)
[ ] Prompt is direct and concise (matches Grok's style)
[ ] X sentiment tasks include timeframe specification
[ ] Image inputs use image_url format
[ ] Tool schemas match OpenAI format
[ ] Output requested with source attribution for factual claims
```
