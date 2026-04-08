---
name: AI Chat Context Management
trigger: context window management, AI chat history, token budget, conversation history pruning, LLM memory, chat context, token limit, summarize conversation, context overflow, long conversation AI, AI memory strategies, context window full, conversation state AI
description: Manage conversation history, token budgets, and memory strategies for AI chat applications. Covers history pruning, summarization, rolling windows, and smart context construction to stay within model limits.
---

# ROLE
You are an AI application engineer building chat interfaces on top of LLM APIs. You know that every message you send costs tokens, models have hard limits, and sending 50 messages of history for every new reply will bankrupt you and hit context limits. Your job is to send exactly the right context — not too much, not too little.

# UNDERSTANDING TOKEN BUDGETS

## Model Context Limits (As of 2025)
```
Claude Opus/Sonnet 4.5:   200,000 tokens (input + output combined)
Claude Haiku 4.5:          200,000 tokens
GPT-4o:                    128,000 tokens
GPT-4o-mini:               128,000 tokens
Gemini 1.5 Pro:          1,000,000 tokens

PRACTICAL BUDGET (allocate these from total):
  System prompt:    1,000 - 5,000 tokens  (your instructions, persona, tools)
  Conversation:     varies — this is what you manage
  Output reserve:   2,000 - 8,000 tokens  (leave room for response)
  Safety margin:    ~10%

RULE: Never send more than 80% of max context — models degrade near the limit
```

## Estimate Token Count Without API Call
```typescript
// Rough estimate: 1 token ≈ 4 characters (English), 3 chars (code/JSON)
function estimateTokens(text: string): number {
  return Math.ceil(text.length / 4);
}

function estimateMessageTokens(message: { role: string; content: string }): number {
  // Add ~4 tokens per message for role/formatting overhead
  return estimateTokens(message.content) + 4;
}

function estimateHistoryTokens(messages: Message[]): number {
  return messages.reduce((total, m) => total + estimateMessageTokens(m), 0);
}

// For accuracy, use tiktoken (works for OpenAI models)
import { encoding_for_model } from 'tiktoken';
const enc = encoding_for_model('gpt-4o');
function countTokens(text: string): number {
  return enc.encode(text).length;
}
```

# CONTEXT MANAGEMENT STRATEGIES

## Strategy 1: Rolling Window (Simplest)
```typescript
// Keep only the last N messages
class RollingWindowContext {
  private messages: Message[] = [];
  private maxMessages: number;

  constructor(maxMessages = 20) {
    this.maxMessages = maxMessages;
  }

  add(message: Message) {
    this.messages.push(message);
  }

  getContext(): Message[] {
    // Always keep the first message if it is user context setup
    if (this.messages.length <= this.maxMessages) return this.messages;

    return this.messages.slice(-this.maxMessages);
    // Cuts off oldest messages — simple, loses early context
  }
}
```

## Strategy 2: Token-Budget Window (Better)
```typescript
class TokenBudgetContext {
  private messages: Message[] = [];
  private tokenBudget: number;

  constructor(tokenBudget = 50_000) {
    this.tokenBudget = tokenBudget;
  }

  add(message: Message) {
    this.messages.push(message);
  }

  getContext(): Message[] {
    const result: Message[] = [];
    let tokenCount = 0;

    // Walk backwards from newest, include messages until budget hit
    for (let i = this.messages.length - 1; i >= 0; i--) {
      const msg = this.messages[i];
      const tokens = estimateMessageTokens(msg);

      if (tokenCount + tokens > this.tokenBudget) break;

      result.unshift(msg);
      tokenCount += tokens;
    }

    return result;
  }
}
```

## Strategy 3: Summarize + Recents (Best for Long Conversations)
```typescript
class SummarizingContext {
  private recentMessages: Message[] = [];
  private summary: string | null = null;
  private summaryTokens = 0;

  private readonly maxRecentMessages = 10;
  private readonly maxTotalTokens = 60_000;

  async add(message: Message, aiClient: AIProvider) {
    this.recentMessages.push(message);

    // When recent messages exceed threshold, summarize oldest half
    if (this.recentMessages.length > this.maxRecentMessages * 2) {
      await this.compressOldMessages(aiClient);
    }
  }

  private async compressOldMessages(aiClient: AIProvider) {
    const toSummarize = this.recentMessages.splice(0, this.maxRecentMessages);
    const conversationText = toSummarize
      .map(m => `${m.role}: ${m.content}`)
      .join('\n');

    const summaryResponse = await aiClient.complete({
      messages: [{
        role: 'user',
        content: `Summarize this conversation segment concisely, preserving key facts, decisions, and context that would be needed to continue the conversation:\n\n${conversationText}`
      }],
      maxTokens: 500,
      temperature: 0
    });

    const newSummary = summaryResponse.content;

    // Append to existing summary
    if (this.summary) {
      this.summary = `${this.summary}\n\nLater in the conversation:\n${newSummary}`;
    } else {
      this.summary = newSummary;
    }
    this.summaryTokens = estimateTokens(this.summary);
  }

  buildContextMessages(systemPrompt: string): Message[] {
    const messages: Message[] = [];

    // Inject summary as context if exists
    if (this.summary) {
      messages.push({
        role: 'user',
        content: `[Previous conversation summary: ${this.summary}]`
      });
      messages.push({
        role: 'assistant',
        content: 'I understand. I have that context from our earlier conversation.'
      });
    }

    // Add recent messages
    messages.push(...this.recentMessages);
    return messages;
  }
}
```

## Strategy 4: Semantic Memory (Retrieval-Based)
```typescript
// For very long sessions — store messages as embeddings, retrieve relevant ones
class SemanticContext {
  private allMessages: Array<{ message: Message; embedding: number[] }> = [];
  private recentMessages: Message[] = [];
  private readonly recentWindow = 5;

  async add(message: Message, embedFn: (text: string) => Promise<number[]>) {
    const embedding = await embedFn(message.content);
    this.allMessages.push({ message, embedding });
    this.recentMessages.push(message);
    if (this.recentMessages.length > this.recentWindow) {
      this.recentMessages.shift();
    }
  }

  async getContext(
    query: string,
    embedFn: (text: string) => Promise<number[]>,
    topK = 5
  ): Promise<Message[]> {
    const queryEmbedding = await embedFn(query);

    // Cosine similarity
    const cosineSim = (a: number[], b: number[]) => {
      const dot = a.reduce((sum, ai, i) => sum + ai * b[i], 0);
      const magA = Math.sqrt(a.reduce((s, ai) => s + ai * ai, 0));
      const magB = Math.sqrt(b.reduce((s, bi) => s + bi * bi, 0));
      return dot / (magA * magB);
    };

    // Find most relevant past messages
    const recent = new Set(this.recentMessages.map(m => m.content));
    const relevant = this.allMessages
      .filter(m => !recent.has(m.message.content))  // exclude already-included recents
      .map(m => ({ message: m.message, score: cosineSim(queryEmbedding, m.embedding) }))
      .sort((a, b) => b.score - a.score)
      .slice(0, topK)
      .map(m => m.message);

    // Return: relevant historical + recent
    return [...relevant, ...this.recentMessages];
  }
}
```

# SYSTEM PROMPT MANAGEMENT

## Tiered System Prompt
```typescript
// Build system prompt dynamically — include only what matters for this request
function buildSystemPrompt(opts: {
  persona?: string;
  tools?: string[];
  userContext?: string;
  taskContext?: string;
}): string {
  const parts: string[] = [];

  // Core persona — always included
  parts.push(`You are ${opts.persona ?? 'a helpful assistant'}.`);

  // User context — only if available
  if (opts.userContext) {
    parts.push(`\nUser context:\n${opts.userContext}`);
  }

  // Task context — relevant to this conversation
  if (opts.taskContext) {
    parts.push(`\nCurrent task:\n${opts.taskContext}`);
  }

  // Tool descriptions — only include tools enabled for this session
  if (opts.tools?.length) {
    parts.push(`\nAvailable tools:\n${opts.tools.join('\n')}`);
  }

  return parts.join('\n');
}
```

# CONTEXT CONSTRUCTION PIPELINE

## Complete Pipeline
```typescript
class ConversationManager {
  private contextStrategy: SummarizingContext;
  private systemPrompt: string;
  private aiClient: AIProvider;

  private readonly MODEL = 'claude-sonnet-4-5';
  private readonly MAX_INPUT_TOKENS = 100_000;
  private readonly OUTPUT_RESERVE = 4_000;
  private readonly BUDGET = this.MAX_INPUT_TOKENS - this.OUTPUT_RESERVE;

  constructor(aiClient: AIProvider, systemPrompt: string) {
    this.aiClient = aiClient;
    this.systemPrompt = systemPrompt;
    this.contextStrategy = new SummarizingContext();
  }

  async sendMessage(userMessage: string): Promise<string> {
    // 1. Add user message to history
    await this.contextStrategy.add(
      { role: 'user', content: userMessage },
      this.aiClient
    );

    // 2. Build context messages
    const contextMessages = this.contextStrategy.buildContextMessages(this.systemPrompt);

    // 3. Check token budget
    const totalTokens = estimateTokens(this.systemPrompt) +
                        estimateHistoryTokens(contextMessages);

    if (totalTokens > this.BUDGET) {
      // Emergency trim — should not happen with good strategy
      console.warn(`Context ${totalTokens} tokens exceeds budget ${this.BUDGET}`);
    }

    // 4. Send to AI
    const response = await this.aiClient.complete({
      messages: contextMessages,
      systemPrompt: this.systemPrompt,
      model: this.MODEL,
      maxTokens: this.OUTPUT_RESERVE
    });

    // 5. Add assistant response to history
    await this.contextStrategy.add(
      { role: 'assistant', content: response.content },
      this.aiClient
    );

    return response.content;
  }

  getTokenStats() {
    const contextMessages = this.contextStrategy.buildContextMessages(this.systemPrompt);
    return {
      systemTokens: estimateTokens(this.systemPrompt),
      historyTokens: estimateHistoryTokens(contextMessages),
      totalTokens: estimateTokens(this.systemPrompt) + estimateHistoryTokens(contextMessages),
      budgetUsedPct: Math.round(
        (estimateTokens(this.systemPrompt) + estimateHistoryTokens(contextMessages))
        / this.BUDGET * 100
      )
    };
  }
}
```

# STRATEGIES COMPARISON
```
Strategy            | Pros                          | Cons
--------------------|-------------------------------|------------------------------
Rolling Window      | Simple, no API cost           | Loses early context abruptly
Token Budget Window | Respects limits precisely     | Still drops early context
Summarize + Recents | Preserves key info long-term  | Costs tokens to summarize
Semantic Retrieval  | Scales to infinite history    | Requires embedding infra

WHEN TO USE EACH:
  Short sessions (< 20 messages):  Rolling window — no overhead needed
  Medium sessions (20-100):        Token budget window — simple and correct
  Long sessions (100+):            Summarize + Recents
  Domain-specific knowledge base:  Semantic retrieval
  Real-time chat apps:             Token budget + periodic summarization
```

# CHECKLIST
```
[ ] Context budget defined and enforced before every API call
[ ] System prompt token cost accounted in budget
[ ] Output reserve tokens held back (do not fill 100% of context)
[ ] History pruning strategy chosen for expected session length
[ ] Token counting implemented — do not guess
[ ] Summarization triggered before hitting hard limit, not at it
[ ] Summary stored between sessions if long-running (persist to DB)
[ ] Token usage logged per message for cost analysis
[ ] Graceful degradation when context limit approached (warn user, offer summary)