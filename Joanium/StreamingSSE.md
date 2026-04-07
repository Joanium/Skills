---
name: Streaming & Server-Sent Events
trigger: streaming response, server-sent events, sse, stream api response, stream llm output, text streaming, event stream, real-time streaming, stream fetch, ReadableStream, stream chunks, stream tokens
description: Implement real-time streaming of data from server to client using Server-Sent Events (SSE) and Fetch ReadableStream. Covers LLM token streaming, SSE protocol, backpressure, reconnection, and client-side consumption.
---

# ROLE
You are a senior fullstack engineer. Your job is to implement streaming that feels instant, handles interruptions gracefully, and never leaks connections. Streaming is about perceived performance — users see output appear immediately instead of waiting for the full response.

# CORE PRINCIPLES
```
START FAST:        Send first token/chunk as soon as possible — don't buffer unnecessarily
NEVER BLOCK:       Streaming endpoints must be async and non-blocking end-to-end
ALWAYS CLEANUP:    Close connections, abort controllers, and streams on client disconnect
HANDLE ERRORS:     Errors mid-stream must be communicated in-band as error events
RECONNECT SAFELY:  Clients must be able to resume interrupted streams with last-event-id
```

# SERVER-SENT EVENTS (SSE) PROTOCOL

## Wire Format
```
SSE is plain text over HTTP. Each event is:

  data: your payload here\n\n           ← single-line data
  
  data: line 1\n
  data: line 2\n\n                      ← multi-line data
  
  event: custom_type\n
  data: {"key": "value"}\n\n            ← typed event with JSON
  
  id: 42\n
  data: hello\n\n                       ← event with ID (enables resume)
  
  : this is a comment\n\n               ← comment (heartbeat / keep-alive)
  
  retry: 3000\n\n                       ← tell client to retry after 3s on disconnect

Rules:
  - Each field ends with \n
  - Each EVENT ends with \n\n (double newline)
  - Required headers: Content-Type: text/event-stream, Cache-Control: no-cache
```

# SERVER IMPLEMENTATIONS

## Node.js + Express SSE
```javascript
app.get('/stream', (req, res) => {
  // Required headers
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');  // disable nginx buffering
  res.flushHeaders();

  let counter = 0;
  const interval = setInterval(() => {
    counter++;
    // Send typed event with JSON data
    res.write(`event: update\n`);
    res.write(`data: ${JSON.stringify({ count: counter, time: Date.now() })}\n\n`);
    
    if (counter >= 10) {
      res.write(`event: done\ndata: stream complete\n\n`);
      clearInterval(interval);
      res.end();
    }
  }, 500);

  // Cleanup on client disconnect
  req.on('close', () => {
    clearInterval(interval);
    res.end();
  });
});
```

## LLM Token Streaming (Anthropic/OpenAI)
```javascript
app.post('/chat/stream', async (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  const { messages } = req.body;

  try {
    const stream = await anthropic.messages.stream({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 1024,
      messages,
    });

    for await (const event of stream) {
      if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
        res.write(`event: token\ndata: ${JSON.stringify({ token: event.delta.text })}\n\n`);
      }
      if (event.type === 'message_stop') {
        res.write(`event: done\ndata: {}\n\n`);
      }
    }
  } catch (error) {
    res.write(`event: error\ndata: ${JSON.stringify({ message: error.message })}\n\n`);
  } finally {
    res.end();
  }

  req.on('close', () => stream.abort?.());
});
```

## Next.js / Edge Runtime Streaming
```javascript
// app/api/stream/route.ts
export async function POST(req: Request) {
  const { prompt } = await req.json();
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      try {
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model: 'gpt-4o-mini',
            stream: true,
            messages: [{ role: 'user', content: prompt }],
          }),
        });

        const reader = response.body!.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const text = decoder.decode(value);

          // Parse SSE lines from OpenAI
          for (const line of text.split('\n')) {
            if (!line.startsWith('data: ') || line === 'data: [DONE]') continue;
            const json = JSON.parse(line.slice(6));
            const token = json.choices[0]?.delta?.content;
            if (token) controller.enqueue(encoder.encode(`data: ${JSON.stringify({ token })}\n\n`));
          }
        }
        controller.enqueue(encoder.encode('event: done\ndata: {}\n\n'));
      } catch (e) {
        controller.enqueue(encoder.encode(`event: error\ndata: ${JSON.stringify({ error: e.message })}\n\n`));
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
    },
  });
}
```

# CLIENT IMPLEMENTATIONS

## EventSource API (Browser Native)
```javascript
// Only supports GET, no custom headers — use for simple cases
const evtSource = new EventSource('/stream');

evtSource.onmessage = (e) => {
  console.log('data:', e.data);  // default 'message' event
};

evtSource.addEventListener('token', (e) => {
  const { token } = JSON.parse(e.data);
  appendToUI(token);
});

evtSource.addEventListener('done', () => {
  evtSource.close();
});

evtSource.addEventListener('error', (e) => {
  console.error('SSE error', e);
  evtSource.close();
});

// Auto-reconnects by default — to disable:
evtSource.close();
```

## Fetch Streaming (POST, custom headers — preferred)
```javascript
async function streamChat(messages, onToken, onDone, onError) {
  const controller = new AbortController();

  try {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ messages }),
      signal: controller.signal,
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();  // keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.token) onToken(data.token);
          } catch {}
        }
        if (line.startsWith('event: done')) {
          onDone();
        }
        if (line.startsWith('event: error')) {
          const errLine = lines[lines.indexOf(line) + 1];
          onError(JSON.parse(errLine?.slice(6) || '{}'));
        }
      }
    }
  } catch (err) {
    if (err.name !== 'AbortError') onError(err);
  }

  // Return abort function so caller can cancel
  return () => controller.abort();
}

// Usage
const abort = await streamChat(
  messages,
  (token) => setOutput(prev => prev + token),
  () => setIsStreaming(false),
  (err) => setError(err.message)
);

// To cancel:
stopButton.onclick = () => abort();
```

## React Hook for Streaming
```javascript
function useStream(url) {
  const [output, setOutput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef(null);

  const start = useCallback(async (body) => {
    setOutput('');
    setIsStreaming(true);

    const abort = await streamChat(
      body,
      (token) => setOutput(prev => prev + token),
      () => setIsStreaming(false),
      (err) => { console.error(err); setIsStreaming(false); }
    );

    abortRef.current = abort;
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.();
    setIsStreaming(false);
  }, []);

  useEffect(() => () => abortRef.current?.(), []);  // cleanup on unmount

  return { output, isStreaming, start, stop };
}
```

# RECONNECTION & RESUMABILITY
```javascript
// Server: send event IDs so client can resume
let lastId = 0;
res.write(`id: ${++lastId}\nevent: token\ndata: ${JSON.stringify({ token })}\n\n`);

// Client: EventSource sends Last-Event-ID header on reconnect
// Server: read it and replay missed events
app.get('/stream', (req, res) => {
  const lastId = parseInt(req.headers['last-event-id'] || '0');
  // Replay events after lastId from your event log
  replayEventsAfter(lastId, res);
  // Then continue streaming new events
});
```

# NGINX / PROXY CONFIG
```nginx
# Disable buffering for SSE routes
location /stream {
  proxy_pass http://localhost:3000;
  proxy_buffering off;
  proxy_cache off;
  proxy_set_header Connection '';
  proxy_http_version 1.1;
  chunked_transfer_encoding on;
}
```

# COMMON PITFALLS
```
Nginx/proxy buffering responses:
  → Add X-Accel-Buffering: no header on responses
  → Or configure proxy_buffering off in nginx

EventSource only supports GET:
  → Use Fetch ReadableStream for POST requests with body/auth headers

Not cleaning up on client disconnect:
  → Always listen to req.on('close') and clear intervals/abort streams

Partial JSON in buffer:
  → Buffer incomplete lines, only parse complete \n-terminated lines

CORS issues with EventSource:
  → Add CORS headers: Access-Control-Allow-Origin, Access-Control-Allow-Credentials
```
