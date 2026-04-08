---
name: Multi-Provider AI Integration
trigger: multi-provider AI, AI provider abstraction, AI failover, switch AI provider, openai anthropic google together, AI provider routing, LLM provider fallback, multiple LLM providers, AI cost routing, provider agnostic LLM, unified AI client, model routing
description: Build a provider-agnostic AI integration layer that abstracts OpenAI, Anthropic, Google, and other LLMs behind a unified interface with failover, cost routing, and model selection logic.
---

# ROLE
You are an AI systems engineer building production applications that call LLM APIs. You know that tying your app to a single provider is a single point of failure — rate limits, outages, price hikes, and model deprecations are when you regret not abstracting. Your job is to build a clean provider layer that lets the rest of the app not care which LLM it is talking to.

# CORE ARCHITECTURE

## Provider Interface (The Contract)
```typescript
// types/ai.ts
export interface Message {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface CompletionRequest {
  messages: Message[];
  model?: string;
  maxTokens?: number;
  temperature?: number;
  stream?: boolean;
  systemPrompt?: string;
}

export interface CompletionResponse {
  content: string;
  model: string;
  provider: string;
  usage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
    estimatedCostUsd: number;
  };
}

export interface StreamChunk {
  delta: string;
  done: boolean;
}

export interface AIProvider {
  name: string;
  models: string[];
  complete(request: CompletionRequest): Promise<CompletionResponse>;
  stream(request: CompletionRequest): AsyncIterable<StreamChunk>;
  isAvailable(): Promise<boolean>;
}
```

## Anthropic Provider
```typescript
// providers/anthropic.ts
import Anthropic from '@anthropic-ai/sdk';

export class AnthropicProvider implements AIProvider {
  name = 'anthropic';
  models = ['claude-opus-4-5', 'claude-sonnet-4-5', 'claude-haiku-4-5'];

  private client: Anthropic;
  private pricing: Record<string, { input: number; output: number }> = {
    'claude-opus-4-5':    { input: 15,   output: 75 },   // per million tokens
    'claude-sonnet-4-5':  { input: 3,    output: 15 },
    'claude-haiku-4-5':   { input: 0.25, output: 1.25 }
  };

  constructor(apiKey: string) {
    this.client = new Anthropic({ apiKey });
  }

  async complete(req: CompletionRequest): Promise<CompletionResponse> {
    const model = req.model ?? 'claude-sonnet-4-5';
    const response = await this.client.messages.create({
      model,
      max_tokens: req.maxTokens ?? 2048,
      temperature: req.temperature ?? 0.7,
      system: req.systemPrompt,
      messages: req.messages.filter(m => m.role !== 'system').map(m => ({
        role: m.role as 'user' | 'assistant',
        content: m.content
      }))
    });

    const content = response.content.find(b => b.type === 'text')?.text ?? '';
    const usage = response.usage;
    const p = this.pricing[model] ?? { input: 3, output: 15 };

    return {
      content,
      model,
      provider: this.name,
      usage: {
        promptTokens: usage.input_tokens,
        completionTokens: usage.output_tokens,
        totalTokens: usage.input_tokens + usage.output_tokens,
        estimatedCostUsd: (usage.input_tokens * p.input + usage.output_tokens * p.output) / 1_000_000
      }
    };
  }

  async *stream(req: CompletionRequest): AsyncIterable<StreamChunk> {
    const model = req.model ?? 'claude-sonnet-4-5';
    const stream = this.client.messages.stream({
      model,
      max_tokens: req.maxTokens ?? 2048,
      system: req.systemPrompt,
      messages: req.messages.filter(m => m.role !== 'system').map(m => ({
        role: m.role as 'user' | 'assistant',
        content: m.content
      }))
    });

    for await (const chunk of stream) {
      if (chunk.type === 'content_block_delta' && chunk.delta.type === 'text_delta') {
        yield { delta: chunk.delta.text, done: false };
      }
    }
    yield { delta: '', done: true };
  }

  async isAvailable(): Promise<boolean> {
    try {
      await this.client.messages.create({
        model: 'claude-haiku-4-5',
        max_tokens: 5,
        messages: [{ role: 'user', content: 'hi' }]
      });
      return true;
    } catch { return false; }
  }
}
```

## OpenAI Provider
```typescript
// providers/openai.ts
import OpenAI from 'openai';

export class OpenAIProvider implements AIProvider {
  name = 'openai';
  models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'];

  private client: OpenAI;
  private pricing: Record<string, { input: number; output: number }> = {
    'gpt-4o':       { input: 5,    output: 15 },
    'gpt-4o-mini':  { input: 0.15, output: 0.6 },
    'gpt-4-turbo':  { input: 10,   output: 30 },
    'gpt-3.5-turbo':{ input: 0.5,  output: 1.5 }
  };

  constructor(apiKey: string) {
    this.client = new OpenAI({ apiKey });
  }

  async complete(req: CompletionRequest): Promise<CompletionResponse> {
    const model = req.model ?? 'gpt-4o-mini';
    const messages: OpenAI.ChatCompletionMessageParam[] = [];

    if (req.systemPrompt) {
      messages.push({ role: 'system', content: req.systemPrompt });
    }
    messages.push(...req.messages.map(m => ({ role: m.role, content: m.content })));

    const response = await this.client.chat.completions.create({
      model,
      messages,
      max_tokens: req.maxTokens ?? 2048,
      temperature: req.temperature ?? 0.7
    });

    const usage = response.usage!;
    const p = this.pricing[model] ?? { input: 5, output: 15 };

    return {
      content: response.choices[0].message.content ?? '',
      model,
      provider: this.name,
      usage: {
        promptTokens: usage.prompt_tokens,
        completionTokens: usage.completion_tokens,
        totalTokens: usage.total_tokens,
        estimatedCostUsd: (usage.prompt_tokens * p.input + usage.completion_tokens * p.output) / 1_000_000
      }
    };
  }

  async *stream(req: CompletionRequest): AsyncIterable<StreamChunk> {
    const model = req.model ?? 'gpt-4o-mini';
    const messages: OpenAI.ChatCompletionMessageParam[] = [];

    if (req.systemPrompt) messages.push({ role: 'system', content: req.systemPrompt });
    messages.push(...req.messages.map(m => ({ role: m.role, content: m.content })));

    const stream = await this.client.chat.completions.create({
      model, messages, stream: true,
      max_tokens: req.maxTokens ?? 2048
    });

    for await (const chunk of stream) {
      const delta = chunk.choices[0]?.delta?.content ?? '';
      if (delta) yield { delta, done: false };
    }
    yield { delta: '', done: true };
  }

  async isAvailable(): Promise<boolean> {
    try {
      await this.client.chat.completions.create({
        model: 'gpt-3.5-turbo',
        max_tokens: 5,
        messages: [{ role: 'user', content: 'hi' }]
      });
      return true;
    } catch { return false; }
  }
}
```

# AI ROUTER — FAILOVER AND ROUTING STRATEGIES

## Router with Failover
```typescript
// AIRouter.ts
export class AIRouter {
  private providers: Map<string, AIProvider> = new Map();
  private failoverOrder: string[] = [];
  private circuitBreaker: Map<string, { failures: number; openUntil: number }> = new Map();

  registerProvider(provider: AIProvider, priority: number = 0) {
    this.providers.set(provider.name, provider);
    this.failoverOrder.push(provider.name);
    this.failoverOrder.sort((a, b) => {
      const pa = this.providers.get(a)!;
      const pb = this.providers.get(b)!;
      return 0; // sort by your priority map
    });
    this.circuitBreaker.set(provider.name, { failures: 0, openUntil: 0 });
  }

  private isCircuitOpen(providerName: string): boolean {
    const cb = this.circuitBreaker.get(providerName)!;
    return cb.failures >= 3 && Date.now() < cb.openUntil;
  }

  private recordFailure(providerName: string) {
    const cb = this.circuitBreaker.get(providerName)!;
    cb.failures++;
    if (cb.failures >= 3) {
      cb.openUntil = Date.now() + 60_000;  // open circuit for 60 seconds
    }
  }

  private recordSuccess(providerName: string) {
    const cb = this.circuitBreaker.get(providerName)!;
    cb.failures = 0;
    cb.openUntil = 0;
  }

  // Route based on strategy
  async complete(
    req: CompletionRequest,
    strategy: 'failover' | 'cheapest' | 'specific' = 'failover',
    preferredProvider?: string
  ): Promise<CompletionResponse> {
    const order = this.getProviderOrder(strategy, preferredProvider);

    for (const providerName of order) {
      if (this.isCircuitOpen(providerName)) continue;

      const provider = this.providers.get(providerName)!;
      try {
        const result = await provider.complete(req);
        this.recordSuccess(providerName);
        return result;
      } catch (err) {
        this.recordFailure(providerName);
        console.warn(`Provider ${providerName} failed:`, err);
        // continue to next provider
      }
    }

    throw new Error('All AI providers failed or circuit breakers open');
  }

  private getProviderOrder(
    strategy: string,
    preferred?: string
  ): string[] {
    if (strategy === 'specific' && preferred) {
      return [preferred, ...this.failoverOrder.filter(n => n !== preferred)];
    }
    if (strategy === 'cheapest') {
      // Sort by estimated cost — would need model pricing comparison
      return [...this.failoverOrder].reverse(); // placeholder
    }
    return [...this.failoverOrder]; // failover: priority order
  }
}
```

## Model Routing by Task Type
```typescript
// Route different tasks to most appropriate/cost-effective model
type TaskType = 'chat' | 'analysis' | 'code' | 'summary' | 'classify';

const MODEL_ROUTING: Record<TaskType, { provider: string; model: string }> = {
  chat:     { provider: 'anthropic', model: 'claude-haiku-4-5' },     // fast, cheap
  analysis: { provider: 'anthropic', model: 'claude-opus-4-5' },      // best reasoning
  code:     { provider: 'openai',    model: 'gpt-4o' },               // best for code
  summary:  { provider: 'openai',    model: 'gpt-4o-mini' },          // cheap, fast
  classify: { provider: 'anthropic', model: 'claude-haiku-4-5' }      // fast, simple task
};

async function routedComplete(
  task: TaskType,
  messages: Message[],
  router: AIRouter
): Promise<CompletionResponse> {
  const { provider, model } = MODEL_ROUTING[task];
  return router.complete({ messages, model }, 'specific', provider);
}
```

# USAGE TRACKING
```typescript
// Track usage and cost per provider/model
interface UsageRecord {
  timestamp: Date;
  provider: string;
  model: string;
  promptTokens: number;
  completionTokens: number;
  costUsd: number;
  taskType?: string;
  latencyMs: number;
}

class UsageTracker {
  private records: UsageRecord[] = [];

  record(response: CompletionResponse, latencyMs: number, taskType?: string) {
    this.records.push({
      timestamp: new Date(),
      provider: response.provider,
      model: response.model,
      promptTokens: response.usage.promptTokens,
      completionTokens: response.usage.completionTokens,
      costUsd: response.usage.estimatedCostUsd,
      taskType,
      latencyMs
    });
  }

  summary() {
    const byProvider = this.records.reduce((acc, r) => {
      if (!acc[r.provider]) acc[r.provider] = { calls: 0, tokens: 0, costUsd: 0 };
      acc[r.provider].calls++;
      acc[r.provider].tokens += r.promptTokens + r.completionTokens;
      acc[r.provider].costUsd += r.costUsd;
      return acc;
    }, {} as Record<string, { calls: number; tokens: number; costUsd: number }>);

    return {
      totalCalls: this.records.length,
      totalCostUsd: this.records.reduce((s, r) => s + r.costUsd, 0),
      avgLatencyMs: this.records.reduce((s, r) => s + r.latencyMs, 0) / this.records.length,
      byProvider
    };
  }
}
```

# UNIFIED SETUP EXAMPLE
```typescript
// ai.ts — single import for rest of app
const router = new AIRouter();
const tracker = new UsageTracker();

router.registerProvider(new AnthropicProvider(process.env.ANTHROPIC_API_KEY!));
router.registerProvider(new OpenAIProvider(process.env.OPENAI_API_KEY!));

export async function chat(messages: Message[], opts?: Partial<CompletionRequest>) {
  const start = Date.now();
  const response = await router.complete({ messages, ...opts });
  tracker.record(response, Date.now() - start);
  return response;
}

export function streamChat(messages: Message[], opts?: Partial<CompletionRequest>) {
  const provider = router['providers'].get('anthropic')!;
  return provider.stream({ messages, ...opts });
}

export { tracker };

// Usage anywhere in app:
import { chat, streamChat } from './ai';
const response = await chat([{ role: 'user', content: 'Hello' }]);
```

# CHECKLIST
```
[ ] Provider interface defined — swap providers without changing call sites
[ ] Failover order configured — at least 2 providers available
[ ] Circuit breaker prevents hammering a failing provider
[ ] Cost tracking per provider/model — know where your money goes
[ ] Model routing by task type — do not use opus for classify tasks
[ ] API keys in env vars, never hardcoded
[ ] Retry with exponential backoff on 429 rate limit errors
[ ] Streaming implemented for long responses
[ ] Latency tracked per provider — drop slow providers from hot paths
[ ] Tests use mock provider — no real API calls in tests