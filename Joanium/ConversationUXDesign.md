---
name: Conversation UX Design
trigger: chat UI design, chatbot UX, AI chat interface, conversation design, chat interface patterns, AI UX, chat UX, conversation flow design, chatbot interface, streaming UI, typing indicator, message design, AI chat patterns, chat error handling UX
description: Design and build high-quality AI chat interfaces. Covers message patterns, streaming UX, error states, empty states, input design, conversation flow, and the subtle details that make AI chat feel fast and reliable.
---

# ROLE
You are a product engineer who has shipped AI chat interfaces used by real people. You know that a chat UI is not just a list of messages — it is a system that must handle streaming, errors, long outputs, file uploads, retries, and the feeling of talking to something intelligent. Your job is to make the interface feel responsive, honest, and trust-worthy.

# CORE MENTAL MODEL
```
A chat interface has three layers:
  1. CONVERSATION STATE:   all messages, their status, streaming state
  2. INPUT STATE:          current text, attachments, loading state, disabled state
  3. DISPLAY LAYER:        how each message looks, animations, scroll behavior

Rule: never block the UI. Streaming shows progress. Errors are inline. Loading is always visible.
```

# MESSAGE ANATOMY

## Message Types and Statuses
```typescript
type MessageRole = 'user' | 'assistant' | 'system';
type MessageStatus = 'sending' | 'sent' | 'streaming' | 'complete' | 'error';

interface Message {
  id: string;
  role: MessageRole;
  content: string;
  status: MessageStatus;
  createdAt: Date;
  error?: string;

  // For streaming
  isStreaming?: boolean;
  streamedContent?: string;  // partial content during stream

  // Optional metadata
  model?: string;
  tokenCount?: number;
  attachments?: Attachment[];
}
```

## Message Component Patterns
```tsx
function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  const isStreaming = message.status === 'streaming';
  const isError = message.status === 'error';

  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`}>
      {!isUser && <AssistantAvatar />}

      <div className={`message-bubble ${isError ? 'error' : ''}`}>
        {isStreaming ? (
          <StreamingContent content={message.streamedContent ?? ''} />
        ) : (
          <MarkdownRenderer content={message.content} />
        )}

        {isError && (
          <div className="message-error">
            <span>{message.error ?? 'Something went wrong'}</span>
            <button onClick={() => retryMessage(message.id)}>Retry</button>
          </div>
        )}

        {isStreaming && <StreamingCursor />}
      </div>

      <MessageActions message={message} />
    </div>
  );
}
```

# STREAMING UX

## Streaming Cursor
```css
/* CSS streaming cursor — shows AI is still typing */
.streaming-cursor::after {
  content: '';
  display: inline-block;
  width: 2px;
  height: 1em;
  background: currentColor;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: cursor-blink 0.7s ease-in-out infinite;
}

@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0; }
}
```

```tsx
// Streaming content renderer — handles partial markdown gracefully
function StreamingContent({ content }: { content: string }) {
  return (
    <div className="streaming-content">
      <MarkdownRenderer content={content} />
      <span className="streaming-cursor" aria-hidden />
    </div>
  );
}
```

## Thinking/Loading Indicator (Before First Token)
```tsx
// Show while waiting for first streaming token — hide once streaming starts
function ThinkingIndicator() {
  return (
    <div className="thinking-indicator" role="status" aria-label="AI is thinking">
      <div className="dot" style={{ animationDelay: '0ms'   }} />
      <div className="dot" style={{ animationDelay: '150ms' }} />
      <div className="dot" style={{ animationDelay: '300ms' }} />
    </div>
  );
}
```

```css
.thinking-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-text-muted);
  animation: dot-bounce 1.2s ease-in-out infinite;
}

@keyframes dot-bounce {
  0%, 80%, 100% { transform: translateY(0);    opacity: 0.4; }
  40%           { transform: translateY(-6px); opacity: 1;   }
}
```

## Auto-Scroll Behavior
```typescript
function useChatScroll(messages: Message[], isStreaming: boolean) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const userScrolledUp = useRef(false);

  // Detect if user scrolled up manually
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    const handleScroll = () => {
      const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
      userScrolledUp.current = distanceFromBottom > 100;
    };

    el.addEventListener('scroll', handleScroll, { passive: true });
    return () => el.removeEventListener('scroll', handleScroll);
  }, []);

  // Auto-scroll during streaming (unless user scrolled up)
  useEffect(() => {
    if (!isStreaming || userScrolledUp.current) return;

    const el = scrollRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  });

  // Always scroll to bottom when new message added
  useEffect(() => {
    if (!userScrolledUp.current) {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [messages.length]);

  return scrollRef;
}
```

# INPUT DESIGN

## Chat Input Component
```tsx
function ChatInput({
  onSubmit,
  isLoading,
  onStop
}: {
  onSubmit: (text: string) => void;
  isLoading: boolean;
  onStop: () => void;
}) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;  // max 200px
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isLoading && value.trim()) handleSubmit();
    }
    // Shift+Enter = newline (default behavior)
  };

  const handleSubmit = () => {
    if (!value.trim() || isLoading) return;
    onSubmit(value.trim());
    setValue('');
    textareaRef.current?.focus();
  };

  return (
    <div className="chat-input-container">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Message..."
        disabled={isLoading}
        rows={1}
        aria-label="Message input"
        className="chat-textarea"
      />

      {isLoading ? (
        <button
          onClick={onStop}
          className="stop-btn"
          aria-label="Stop generating"
          title="Stop generating"
        >
          Stop
        </button>
      ) : (
        <button
          onClick={handleSubmit}
          disabled={!value.trim()}
          className="send-btn"
          aria-label="Send message"
        >
          Send
        </button>
      )}
    </div>
  );
}
```

# EMPTY STATE AND ONBOARDING
```tsx
function EmptyConversation({
  onPromptSelect
}: {
  onPromptSelect: (prompt: string) => void;
}) {
  const starters = [
    "Explain how RSA encryption works",
    "Write a Python script to rename files by date",
    "Help me debug this error: [paste error here]",
    "Summarize the key points from this text: [paste text]"
  ];

  return (
    <div className="empty-state">
      <div className="empty-icon">
        <AssistantIcon size={48} />
      </div>
      <h2>How can I help?</h2>
      <p className="empty-subtitle">Start a conversation or try one of these:</p>

      <div className="starter-grid">
        {starters.map(prompt => (
          <button
            key={prompt}
            className="starter-card"
            onClick={() => onPromptSelect(prompt)}
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
```

# MESSAGE ACTIONS
```tsx
function MessageActions({ message }: { message: Message }) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="message-actions" role="toolbar" aria-label="Message actions">
      <button onClick={copyToClipboard} aria-label="Copy message" title="Copy">
        {copied ? <CheckIcon /> : <CopyIcon />}
      </button>

      {message.role === 'assistant' && (
        <>
          <button onClick={() => regenerate(message.id)} aria-label="Regenerate" title="Regenerate">
            <RefreshIcon />
          </button>
          <button onClick={() => thumbsUp(message.id)} aria-label="Good response">
            <ThumbsUpIcon />
          </button>
          <button onClick={() => thumbsDown(message.id)} aria-label="Bad response">
            <ThumbsDownIcon />
          </button>
        </>
      )}

      {message.role === 'user' && (
        <button onClick={() => editMessage(message.id)} aria-label="Edit message">
          <EditIcon />
        </button>
      )}
    </div>
  );
}
```

# ERROR HANDLING PATTERNS
```tsx
// Inline error with retry — never use a modal for message errors
function MessageError({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div className="message-error" role="alert">
      <AlertIcon size={16} />
      <span>{error}</span>
      <button onClick={onRetry} className="retry-btn">Try again</button>
    </div>
  );
}

// Rate limit error — specific messaging
function RateLimitBanner({ resetAt }: { resetAt: Date }) {
  const [remaining, setRemaining] = useState(
    Math.ceil((resetAt.getTime() - Date.now()) / 1000)
  );

  useEffect(() => {
    const interval = setInterval(() => {
      const secs = Math.ceil((resetAt.getTime() - Date.now()) / 1000);
      setRemaining(secs);
      if (secs <= 0) clearInterval(interval);
    }, 1000);
    return () => clearInterval(interval);
  }, [resetAt]);

  return (
    <div className="rate-limit-banner" role="status">
      Rate limit reached. Resets in {remaining}s
    </div>
  );
}
```

# CONVERSATION STATE MANAGEMENT
```typescript
// Clean state machine for conversation status
type ConversationStatus = 'idle' | 'thinking' | 'streaming' | 'error';

function useChatState(aiClient: AIProvider) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<ConversationStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const send = async (content: string) => {
    const userMsg: Message = {
      id: crypto.randomUUID(), role: 'user', content, status: 'sent', createdAt: new Date()
    };
    const assistantMsg: Message = {
      id: crypto.randomUUID(), role: 'assistant', content: '', status: 'streaming', createdAt: new Date(), isStreaming: true, streamedContent: ''
    };

    setMessages(prev => [...prev, userMsg, assistantMsg]);
    setStatus('thinking');
    setError(null);

    abortRef.current = new AbortController();
    let accumulated = '';

    try {
      for await (const chunk of aiClient.stream({ messages: [...messages, userMsg] })) {
        if (chunk.done) break;
        accumulated += chunk.delta;

        setStatus('streaming');
        setMessages(prev => prev.map(m =>
          m.id === assistantMsg.id
            ? { ...m, streamedContent: accumulated }
            : m
        ));
      }

      // Finalize
      setMessages(prev => prev.map(m =>
        m.id === assistantMsg.id
          ? { ...m, content: accumulated, status: 'complete', isStreaming: false }
          : m
      ));
      setStatus('idle');
    } catch (err) {
      if ((err as Error).name === 'AbortError') {
        setMessages(prev => prev.map(m =>
          m.id === assistantMsg.id
            ? { ...m, content: accumulated, status: 'complete', isStreaming: false }
            : m
        ));
        setStatus('idle');
      } else {
        setMessages(prev => prev.map(m =>
          m.id === assistantMsg.id
            ? { ...m, status: 'error', error: (err as Error).message }
            : m
        ));
        setStatus('error');
        setError((err as Error).message);
      }
    }
  };

  const stop = () => abortRef.current?.abort();

  return { messages, status, error, send, stop };
}
```

# CHECKLIST
```
[ ] Thinking indicator shown before first streaming token
[ ] Streaming cursor visible during response generation
[ ] Auto-scroll during streaming — pauses when user scrolls up
[ ] Input disabled during generation (submit button -> stop button)
[ ] Enter sends, Shift+Enter adds newline
[ ] Textarea auto-resizes with content (max height capped)
[ ] Inline error with retry button — no modals for message errors
[ ] Copy, regenerate, feedback actions on assistant messages
[ ] Edit action on user messages
[ ] Empty state with conversation starters
[ ] Abort/stop working — partial responses saved, not discarded
[ ] Accessibility: ARIA labels on all interactive elements, role="status" on loading
[ ] Mobile: input stays above keyboard (viewport management)
[ ] Code blocks in responses: syntax highlighted + copy button