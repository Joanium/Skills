---
name: Tool Calling & Function Use
trigger: tool calling, function calling, tool use, function use, llm tools, claude tools, openai function calling, define tools, tool schema, tool result, parallel tool use, structured output, tool invocation, model tools
description: Define, implement, and handle LLM tool calls with Anthropic and OpenAI APIs. Covers tool schema design, handling tool use responses, parallel tool calls, tool result injection, and building reliable tool loops.
---

# ROLE
You are a senior AI integrations engineer. Your job is to build tool-calling pipelines that handle all response types (text, tool use, mixed), execute tools correctly, and feed results back for multi-turn completion. Tool calling fails in production because of poor schema descriptions, missing error handling, and incomplete turn management.

# CORE PRINCIPLES
```
DESCRIPTIONS ARE EVERYTHING: The model picks tools based purely on your descriptions
HANDLE ALL RESPONSE TYPES:   Responses can be text-only, tool-only, or mixed
ALWAYS RETURN RESULTS:       Every tool_use block must be answered with tool_result
PARALLEL SUPPORT:            Multiple tools can be called in one response — handle all
LOOP UNTIL DONE:             Keep calling until response has no tool_use blocks
```

# TOOL SCHEMA DESIGN

## Anthropic Format
```javascript
const tools = [
  {
    name: 'web_search',
    description: `Search the web for current information. Use when you need facts that might be outdated in your training data, current events, prices, or anything time-sensitive. Do NOT use for general knowledge you already have.`,
    input_schema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'The search query. Be specific — "Python 3.12 release date" not "python"',
        },
        num_results: {
          type: 'integer',
          description: 'Number of results to return (1–10). Default 5.',
          default: 5,
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'read_file',
    description: `Read the contents of a file at the given path. Returns the file contents as a string. Use before editing a file. Fails for binary files.`,
    input_schema: {
      type: 'object',
      properties: {
        path: {
          type: 'string',
          description: 'Absolute path to the file',
        },
      },
      required: ['path'],
    },
  },
  {
    name: 'execute_code',
    description: `Execute Python code and return stdout/stderr. Use to perform calculations, data processing, or validate logic. Code runs in an isolated sandbox. No internet access inside.`,
    input_schema: {
      type: 'object',
      properties: {
        code: { type: 'string', description: 'Python code to execute' },
        timeout: { type: 'integer', description: 'Timeout in seconds (max 30)', default: 10 },
      },
      required: ['code'],
    },
  },
];
```

## OpenAI Format
```javascript
const openAITools = [
  {
    type: 'function',
    function: {
      name: 'get_weather',
      description: 'Get current weather for a city. Returns temperature, conditions, and humidity.',
      parameters: {
        type: 'object',
        properties: {
          city: { type: 'string', description: 'City name, e.g. "Tokyo" or "New York"' },
          units: { type: 'string', enum: ['celsius', 'fahrenheit'], default: 'celsius' },
        },
        required: ['city'],
      },
    },
  },
];
```

# TOOL EXECUTION LOOP

## Anthropic Complete Loop
```javascript
import Anthropic from '@anthropic-ai/sdk';

const anthropic = new Anthropic();

async function runWithTools(userMessage, tools, toolHandlers) {
  const messages = [{ role: 'user', content: userMessage }];

  while (true) {
    const response = await anthropic.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 4096,
      tools,
      messages,
    });

    // Add assistant's response to history
    messages.push({ role: 'assistant', content: response.content });

    // If no tool use — we're done
    if (response.stop_reason !== 'tool_use') {
      // Extract final text response
      const text = response.content
        .filter(block => block.type === 'text')
        .map(block => block.text)
        .join('');
      return text;
    }

    // Execute ALL tool calls (may be parallel)
    const toolUseBlocks = response.content.filter(b => b.type === 'tool_use');
    const toolResults = await Promise.all(
      toolUseBlocks.map(async (toolUse) => {
        let result;
        try {
          const handler = toolHandlers[toolUse.name];
          if (!handler) throw new Error(`Unknown tool: ${toolUse.name}`);
          result = await handler(toolUse.input);
        } catch (err) {
          result = { error: err.message };
        }

        return {
          type: 'tool_result',
          tool_use_id: toolUse.id,
          content: typeof result === 'string' ? result : JSON.stringify(result),
          // Mark as error so model knows to handle it:
          is_error: result?.error !== undefined,
        };
      })
    );

    // Add tool results as user turn
    messages.push({ role: 'user', content: toolResults });
  }
}

// Usage
const result = await runWithTools(
  'What is the weather in Tokyo and Paris right now?',
  tools,
  {
    get_weather: async ({ city, units }) => {
      const data = await weatherAPI.fetch(city);
      return { city, temp: data.temp, conditions: data.conditions, units };
    },
    web_search: async ({ query, num_results }) => {
      return await searchEngine.search(query, num_results);
    },
  }
);
```

## OpenAI Complete Loop
```javascript
import OpenAI from 'openai';

const openai = new OpenAI();

async function runWithToolsOpenAI(userMessage, tools, toolHandlers) {
  const messages = [{ role: 'user', content: userMessage }];

  while (true) {
    const response = await openai.chat.completions.create({
      model: 'gpt-4o',
      tools,
      tool_choice: 'auto',  // 'none' | 'auto' | { type: 'function', function: { name } }
      messages,
    });

    const choice = response.choices[0];
    messages.push(choice.message);

    if (choice.finish_reason !== 'tool_calls') {
      return choice.message.content;
    }

    // Execute all tool calls in parallel
    const results = await Promise.all(
      choice.message.tool_calls.map(async (toolCall) => {
        let result;
        try {
          const args = JSON.parse(toolCall.function.arguments);
          result = await toolHandlers[toolCall.function.name](args);
        } catch (err) {
          result = { error: err.message };
        }

        return {
          role: 'tool',
          tool_call_id: toolCall.id,
          content: typeof result === 'string' ? result : JSON.stringify(result),
        };
      })
    );

    messages.push(...results);
  }
}
```

# STREAMING WITH TOOL USE (Anthropic)
```javascript
async function streamWithTools(messages, tools, toolHandlers, onText) {
  while (true) {
    const stream = anthropic.messages.stream({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 4096,
      tools,
      messages,
    });

    let currentToolUse = null;
    let toolInputBuffer = '';
    const pendingToolCalls = [];
    let finalText = '';

    for await (const event of stream) {
      switch (event.type) {
        case 'content_block_start':
          if (event.content_block.type === 'tool_use') {
            currentToolUse = { id: event.content_block.id, name: event.content_block.name };
            toolInputBuffer = '';
          }
          break;

        case 'content_block_delta':
          if (event.delta.type === 'text_delta') {
            onText(event.delta.text);  // Stream text to UI
            finalText += event.delta.text;
          }
          if (event.delta.type === 'input_json_delta') {
            toolInputBuffer += event.delta.partial_json;
          }
          break;

        case 'content_block_stop':
          if (currentToolUse) {
            pendingToolCalls.push({ ...currentToolUse, input: JSON.parse(toolInputBuffer) });
            currentToolUse = null;
            toolInputBuffer = '';
          }
          break;
      }
    }

    const finalMessage = await stream.finalMessage();
    messages.push({ role: 'assistant', content: finalMessage.content });

    if (pendingToolCalls.length === 0) return finalText;

    // Execute tools and continue
    const toolResults = await Promise.all(
      pendingToolCalls.map(async (tc) => ({
        type: 'tool_result',
        tool_use_id: tc.id,
        content: JSON.stringify(await toolHandlers[tc.name](tc.input)),
      }))
    );

    messages.push({ role: 'user', content: toolResults });
  }
}
```

# FORCED TOOL USE
```javascript
// Force model to always call a specific tool (structured output)
const response = await anthropic.messages.create({
  model: 'claude-sonnet-4-20250514',
  max_tokens: 1024,
  tools: [extractionTool],
  tool_choice: { type: 'tool', name: 'extract_data' },  // force this tool
  messages: [{ role: 'user', content: 'Extract all dates from: "Meeting Jan 5, deadline Feb 14"' }],
});

// Response will always have a tool_use block — safe to access directly
const toolUse = response.content.find(b => b.type === 'tool_use');
const extracted = toolUse.input;
```

# TOOL RESULT BEST PRACTICES
```javascript
// Good tool results:
// 1. Return structured data the model can reason about
return {
  results: [
    { title: "...", url: "...", snippet: "..." }
  ],
  totalFound: 1240,
};

// 2. Return error in a way the model understands
return {
  error: 'FILE_NOT_FOUND',
  path: '/home/user/docs/missing.txt',
  suggestion: 'Check if the path is correct',
};

// 3. Return status for write operations
return {
  success: true,
  path: '/output/result.json',
  bytesWritten: 2048,
};

// Bad tool results:
return null;                    // ✗ model can't reason about null
return "done";                  // ✗ no useful info
throw new Error("failed");      // ✗ crashes the loop — catch and return error obj
```

# TOOL SCHEMA QUALITY CHECKLIST
```
[ ] Description says WHEN to use (and when NOT to)
[ ] Each parameter has a description with example values
[ ] Required vs optional clearly separated
[ ] Enum values listed when field has limited options
[ ] Description length: 1–3 sentences — not too short, not a paragraph
[ ] Tool name is a verb + noun: get_weather, read_file, send_email, create_task
[ ] No ambiguous overlap between tools (model gets confused)
[ ] Error handling: every tool handler has try/catch returning { error: string }
[ ] Tool loop has max iteration cap (prevent infinite loops)
```
