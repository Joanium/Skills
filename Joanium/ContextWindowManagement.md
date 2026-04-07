---
name: Context Window Management
trigger: context window, token limit, context overflow, manage context, truncate context, summarize history, long conversation, context too long, token count, context length, fit in context, conversation memory, context compression
description: Manage LLM context windows effectively — count tokens, truncate intelligently, compress history, and architect multi-turn conversations that don't overflow. Covers token budgeting, sliding windows, summarization, and retrieval-augmented context.
---

# ROLE
You are a senior AI systems engineer. Your job is to architect conversations and data pipelines so the right information fits in the context window — every time. Context overflow silently degrades quality before it hard-errors. You prevent both.

# CORE PRINCIPLES
```
BUDGET EARLY:     Know your token budget before you start, not after you overflow
COMPRESS HISTORY: Summarize old turns instead of dropping them blindly
PRIORITIZE:       Recent messages > old messages; system prompt > user chat history
CHUNK DOCUMENTS:  Never dump full documents — retrieve only relevant chunks
MEASURE ALWAYS:   Count tokens before sending — never guess
```

# TOKEN COUNTING

## Accurate Counting (tiktoken)
```javascript
import Tiktoken from 'js-tiktoken';

// For OpenAI models
const enc = Tiktoken.getEncoding('cl100k_base');  // GPT-4, GPT-3.5
// const enc = Tiktoken.getEncoding('o200k_base');  // GPT-4o

function countTokens(text) {
  return enc.encode(text).length;
}

function countMessageTokens(messages) {
  // Each message has 3 overhead tokens (role, content delimiters)
  const overhead = messages.length * 3 + 3;  // 3 for reply priming
  const contentTokens = messages.reduce((sum, msg) => {
    return sum + countTokens(msg.content) + countTokens(msg.role);
  }, 0);
  return overhead + contentTokens;
}

// For Anthropic (Claude) — approximate: 1 token ≈ 3.5–4 chars
function estimateTokensAnthropic(text) {
  return Math.ceil(text.length / 3.7);
}
```

## Budget Planning
```
Model context limits (as of 2025):
  GPT-4o:              128k tokens
  GPT-4o-mini:         128k tokens
  Claude Sonnet 4:     200k tokens
  Claude Haiku 4.5:    200k tokens
  Llama 3.1 8B:        128k tokens
  Gemini 1.5 Pro:      1M tokens (2M in some configs)

Recommended budget allocation:
  ┌──────────────────────────────────────────────┐
  │  System prompt          5–10%                │
  │  Retrieved context      20–30%               │
  │  Conversation history   30–40%               │
  │  Current user message   5–10%                │
  │  Output buffer          20–30% (max_tokens)  │
  └──────────────────────────────────────────────┘

Example for 128k model:
  System:    6,400 tokens  (5%)
  Context:   38,400 tokens (30%)
  History:   38,400 tokens (30%)
  User msg:  6,400 tokens  (5%)
  Output:    38,400 tokens (30% = max_tokens budget)
```

# CONVERSATION HISTORY MANAGEMENT

## Sliding Window (Simple)
```javascript
function buildMessagesWithWindow(history, newMessage, maxHistoryTokens = 8000) {
  const messages = [];
  let tokenCount = 0;

  // Walk backwards through history, add until budget exhausted
  for (let i = history.length - 1; i >= 0; i--) {
    const msgTokens = countTokens(history[i].content) + 4;
    if (tokenCount + msgTokens > maxHistoryTokens) break;
    messages.unshift(history[i]);
    tokenCount += msgTokens;
  }

  messages.push({ role: 'user', content: newMessage });
  return messages;
}
```

## Summarization (Better Quality)
```javascript
async function compressHistory(messages, targetTokens = 2000) {
  const currentTokens = countMessageTokens(messages);
  if (currentTokens <= targetTokens) return messages;

  // Keep last 4 turns fresh
  const recentMessages = messages.slice(-4);
  const oldMessages = messages.slice(0, -4);

  if (oldMessages.length === 0) return recentMessages;

  // Summarize old messages
  const historyText = oldMessages
    .map(m => `${m.role.toUpperCase()}: ${m.content}`)
    .join('\n');

  const summary = await llm.complete({
    messages: [{
      role: 'user',
      content: `Summarize this conversation concisely, preserving key facts, decisions, and context:\n\n${historyText}`
    }],
    max_tokens: 500,
  });

  // Replace old messages with summary
  return [
    { role: 'user', content: `[Previous conversation summary]: ${summary}` },
    { role: 'assistant', content: 'Understood, I have the context from before.' },
    ...recentMessages,
  ];
}
```

## Smart Truncation with Importance Scoring
```javascript
function scoreMessage(message, index, total) {
  let score = 0;

  // Recency — more recent = higher score
  score += (index / total) * 10;

  // Role importance
  if (message.role === 'system') score += 20;
  if (message.role === 'tool') score -= 3;  // tool results less important than summaries

  // Content signals
  if (message.content.includes('important') || message.content.includes('remember')) score += 5;
  if (message.content.includes('error') || message.content.includes('failed')) score += 3;

  // Length penalty — very long messages may be less important per token
  const tokens = countTokens(message.content);
  if (tokens > 1000) score -= 2;

  return score;
}

function selectMessagesForBudget(messages, budgetTokens) {
  const scored = messages.map((msg, i) => ({
    msg,
    score: scoreMessage(msg, i, messages.length),
    tokens: countTokens(msg.content) + 4,
  }));

  // Sort by score descending
  scored.sort((a, b) => b.score - a.score);

  let used = 0;
  const selected = [];

  for (const item of scored) {
    if (used + item.tokens > budgetTokens) continue;
    selected.push(item);
    used += item.tokens;
  }

  // Re-sort by original position to maintain chronological order
  selected.sort((a, b) => messages.indexOf(a.msg) - messages.indexOf(b.msg));
  return selected.map(item => item.msg);
}
```

# DOCUMENT CONTEXT MANAGEMENT

## Chunking Strategy
```javascript
function chunkDocument(text, chunkSize = 500, overlap = 50) {
  const words = text.split(/\s+/);
  const chunks = [];

  for (let i = 0; i < words.length; i += chunkSize - overlap) {
    const chunk = words.slice(i, i + chunkSize).join(' ');
    chunks.push({
      content: chunk,
      startIndex: i,
      endIndex: Math.min(i + chunkSize, words.length),
    });
  }
  return chunks;
}

// Semantic chunking (better) — split on paragraph boundaries
function semanticChunk(text, maxTokens = 400) {
  const paragraphs = text.split(/\n\n+/);
  const chunks = [];
  let current = '';

  for (const para of paragraphs) {
    const combined = current + '\n\n' + para;
    if (countTokens(combined) > maxTokens && current) {
      chunks.push(current.trim());
      current = para;
    } else {
      current = combined;
    }
  }
  if (current) chunks.push(current.trim());
  return chunks;
}
```

## Retrieval-Augmented Context (RAG)
```javascript
async function buildRAGContext(userQuery, vectorStore, maxContextTokens = 4000) {
  // Retrieve relevant chunks
  const results = await vectorStore.similaritySearch(userQuery, { topK: 10 });

  // Pack chunks until budget is full
  const selectedChunks = [];
  let usedTokens = 0;

  for (const result of results) {
    const tokens = countTokens(result.content);
    if (usedTokens + tokens > maxContextTokens) break;
    selectedChunks.push(result);
    usedTokens += tokens;
  }

  const contextText = selectedChunks
    .map((c, i) => `[Source ${i + 1}]: ${c.content}`)
    .join('\n\n---\n\n');

  return {
    context: contextText,
    tokens: usedTokens,
    sources: selectedChunks.map(c => c.metadata),
  };
}
```

# SYSTEM PROMPT OPTIMIZATION
```
Principles for compact system prompts:
  1. Use imperative commands ("Reply in JSON", not "You should reply in JSON format if possible")
  2. Use structured sections with headers, not prose paragraphs
  3. Put variable content (date, user info) in a separate section at the end
  4. Extract repeated instructions into a shared template
  5. Remove redundant phrases: "As an AI...", "I'll make sure to...", "Certainly!"

Token counts:
  Bad (47 tokens):   "You are a helpful AI assistant. You should always be polite and
                      professional. When the user asks questions, make sure to provide
                      complete and accurate answers."

  Good (14 tokens):  "Helpful, concise technical assistant. Answer directly."

Dynamic system prompt injection:
  const systemPrompt = [
    BASE_INSTRUCTIONS,           // static, cached
    `Today: ${today}`,           // small dynamic part
    `User: ${user.name}, ${user.role}`,
  ].join('\n');
```

# MONITORING & ALERTS
```javascript
function trackContextUsage(messages, modelLimit, label = '') {
  const used = countMessageTokens(messages);
  const pct = (used / modelLimit * 100).toFixed(1);
  
  console.log(`[Context] ${label} — ${used}/${modelLimit} tokens (${pct}%)`);

  if (used > modelLimit * 0.8) {
    console.warn(`[Context WARNING] Over 80% context used — consider compressing history`);
  }
  if (used > modelLimit * 0.95) {
    console.error(`[Context CRITICAL] Over 95% — next message may fail`);
  }

  return { used, limit: modelLimit, pct: parseFloat(pct) };
}
```

# PATTERNS BY USE CASE
```
CHATBOT (ongoing conversation):
  → Sliding window last 10–15 turns + periodic summarization
  → Summarize when history > 60% of budget

DOCUMENT Q&A:
  → Chunk documents, embed, retrieve top-k relevant chunks per query
  → Don't dump entire documents into context

CODING AGENT:
  → Keep recent file contents + error messages
  → Summarize tool call history (keep just final states, not all intermediate)

LONG-RUNNING AGENT:
  → Maintain structured state object (not raw conversation)
  → State includes: goal, plan, findings, completed steps
  → Regenerate context from state each step, not append conversation

MULTI-MODAL (images + text):
  → Images are expensive (typically 1,000–2,000 tokens each)
  → Resize images before sending: max 1024px on longest side
  → Only include images directly relevant to current question
```
