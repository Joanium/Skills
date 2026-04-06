---
name: WebSockets & Realtime
trigger: websocket, realtime, socket.io, SSE, server-sent events, live updates, real-time communication, ws, long polling, pub/sub realtime, chat app, live notifications, streaming response, bidirectional
description: Build real-time features using WebSockets, Socket.IO, and Server-Sent Events. Covers connection management, rooms, broadcasting, reconnection, authentication, scaling with Redis pub/sub, and choosing the right technology.
---

# ROLE
You are a real-time systems engineer. Your job is to build reliable, scalable bidirectional communication between clients and servers. Real-time features feel magical when they work and catastrophic when they don't — resilience is as important as functionality.

# TECHNOLOGY DECISION
```
WebSocket (ws / Socket.IO):
  ✓ Bidirectional — client AND server can push messages
  ✓ Low latency — persistent connection, no HTTP overhead per message
  ✓ Use for: chat, multiplayer games, collaborative editing, live dashboards
  ✗ More complex to scale (sticky sessions or pub/sub needed)
  ✗ Some proxies/firewalls block WebSocket upgrades

Server-Sent Events (SSE):
  ✓ Server → Client only (one-directional push)
  ✓ Works over regular HTTP — no upgrade, proxy-friendly
  ✓ Auto-reconnects built in
  ✓ Use for: notifications, live feeds, progress updates, AI streaming
  ✗ Client → Server still uses regular HTTP requests

Long Polling (fallback):
  ✓ Works everywhere, zero special infrastructure
  ✗ Higher latency, more server load
  ✗ Use only as fallback when WebSocket/SSE unavailable
```

# NATIVE WEBSOCKET (No Library)

## Server (Node.js with 'ws')
```typescript
import { WebSocketServer, WebSocket } from 'ws'
import { IncomingMessage } from 'http'
import { verifyAccessToken } from './auth'

interface AuthenticatedClient extends WebSocket {
  userId?: string
  isAlive: boolean
}

const wss = new WebSocketServer({ port: 8080 })

// Track all clients
const clients = new Map<string, AuthenticatedClient>()

wss.on('connection', (ws: AuthenticatedClient, req: IncomingMessage) => {
  // Authenticate on connection (via query param or first message)
  const url = new URL(req.url!, `http://${req.headers.host}`)
  const token = url.searchParams.get('token')

  try {
    const payload = verifyAccessToken(token!)
    ws.userId = payload.userId
    clients.set(payload.userId, ws)
    console.log(`Client connected: ${payload.userId}`)
  } catch {
    ws.close(4001, 'Unauthorized')
    return
  }

  ws.isAlive = true

  // Handle incoming messages
  ws.on('message', (raw) => {
    try {
      const message = JSON.parse(raw.toString())
      handleMessage(ws, message)
    } catch {
      ws.send(JSON.stringify({ type: 'error', message: 'Invalid JSON' }))
    }
  })

  ws.on('pong', () => { ws.isAlive = true })

  ws.on('close', () => {
    if (ws.userId) clients.delete(ws.userId)
    console.log(`Client disconnected: ${ws.userId}`)
  })

  ws.on('error', (err) => {
    console.error(`WebSocket error for ${ws.userId}:`, err)
  })

  // Send initial state
  ws.send(JSON.stringify({ type: 'connected', userId: ws.userId }))
})

// Message router
function handleMessage(ws: AuthenticatedClient, message: any) {
  switch (message.type) {
    case 'ping':
      ws.send(JSON.stringify({ type: 'pong' }))
      break
    case 'chat':
      broadcast({ type: 'chat', from: ws.userId, text: message.text })
      break
    default:
      ws.send(JSON.stringify({ type: 'error', message: `Unknown type: ${message.type}` }))
  }
}

// Broadcast to all connected clients
function broadcast(message: object, excludeUserId?: string) {
  const payload = JSON.stringify(message)
  clients.forEach((client, userId) => {
    if (userId !== excludeUserId && client.readyState === WebSocket.OPEN) {
      client.send(payload)
    }
  })
}

// Send to specific user
function sendToUser(userId: string, message: object): boolean {
  const client = clients.get(userId)
  if (client?.readyState === WebSocket.OPEN) {
    client.send(JSON.stringify(message))
    return true
  }
  return false
}

// Heartbeat — detect dead connections
const heartbeatInterval = setInterval(() => {
  wss.clients.forEach((ws: AuthenticatedClient) => {
    if (!ws.isAlive) return ws.terminate()
    ws.isAlive = false
    ws.ping()
  })
}, 30_000)

wss.on('close', () => clearInterval(heartbeatInterval))
```

## Client (Browser)
```typescript
class RealtimeClient {
  private ws: WebSocket | null = null
  private reconnectDelay = 1000
  private maxDelay = 30_000
  private listeners = new Map<string, Set<(data: any) => void>>()

  constructor(private url: string, private getToken: () => string) {}

  connect() {
    const token = this.getToken()
    this.ws = new WebSocket(`${this.url}?token=${token}`)

    this.ws.onopen = () => {
      console.log('Connected')
      this.reconnectDelay = 1000  // reset backoff
    }

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      this.listeners.get(message.type)?.forEach(handler => handler(message))
    }

    this.ws.onclose = (event) => {
      if (event.code !== 4001) {  // 4001 = unauthorized, don't retry
        this.scheduleReconnect()
      }
    }

    this.ws.onerror = (err) => {
      console.error('WebSocket error:', err)
    }
  }

  private scheduleReconnect() {
    setTimeout(() => {
      console.log(`Reconnecting in ${this.reconnectDelay}ms...`)
      this.connect()
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxDelay)  // exponential backoff
    }, this.reconnectDelay)
  }

  on(type: string, handler: (data: any) => void) {
    if (!this.listeners.has(type)) this.listeners.set(type, new Set())
    this.listeners.get(type)!.add(handler)
    return () => this.listeners.get(type)?.delete(handler)  // return unsubscribe
  }

  send(message: object) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  disconnect() {
    this.ws?.close(1000, 'Client disconnecting')
  }
}

// Usage
const client = new RealtimeClient('ws://localhost:8080', () => localStorage.getItem('token')!)
client.connect()
client.on('chat', (msg) => console.log(`${msg.from}: ${msg.text}`))
client.send({ type: 'chat', text: 'Hello!' })
```

# SOCKET.IO (Higher-Level)
```typescript
// Server
import { Server } from 'socket.io'
import { createServer } from 'http'

const httpServer = createServer(app)
const io = new Server(httpServer, {
  cors: { origin: 'http://localhost:3000', credentials: true },
})

// Auth middleware
io.use((socket, next) => {
  const token = socket.handshake.auth.token
  try {
    socket.data.user = verifyAccessToken(token)
    next()
  } catch {
    next(new Error('Unauthorized'))
  }
})

io.on('connection', (socket) => {
  const { userId, role } = socket.data.user
  console.log(`${userId} connected`)

  // Join rooms (namespaced groups)
  socket.join(`user:${userId}`)        // personal room
  if (role === 'admin') socket.join('admins')

  socket.on('join-room', (roomId: string) => {
    socket.join(roomId)
    socket.to(roomId).emit('user-joined', { userId })  // notify others in room
  })

  socket.on('chat-message', ({ roomId, text }) => {
    io.to(roomId).emit('chat-message', {   // send to everyone in room (including sender)
      from: userId,
      text,
      timestamp: Date.now(),
    })
  })

  socket.on('disconnect', () => {
    console.log(`${userId} disconnected`)
  })
})

// Emit from anywhere (e.g., in an HTTP handler after DB write)
function notifyUser(userId: string, event: string, data: any) {
  io.to(`user:${userId}`).emit(event, data)
}

function broadcastToRoom(roomId: string, event: string, data: any) {
  io.to(roomId).emit(event, data)
}
```

# SERVER-SENT EVENTS (SSE)

## Server (Express)
```typescript
// SSE endpoint
app.get('/events', requireAuth, (req, res) => {
  // Set SSE headers
  res.setHeader('Content-Type', 'text/event-stream')
  res.setHeader('Cache-Control', 'no-cache')
  res.setHeader('Connection', 'keep-alive')
  res.setHeader('X-Accel-Buffering', 'no')  // disable nginx buffering
  res.flushHeaders()

  const userId = req.user!.userId

  // Register this client
  sseClients.set(userId, res)

  // Send initial connection event
  res.write(`event: connected\ndata: ${JSON.stringify({ userId })}\n\n`)

  // Heartbeat — keep connection alive through proxies
  const heartbeat = setInterval(() => {
    res.write(': heartbeat\n\n')  // comment line — no event dispatched, just keepalive
  }, 25_000)

  // Cleanup on disconnect
  req.on('close', () => {
    clearInterval(heartbeat)
    sseClients.delete(userId)
  })
})

const sseClients = new Map<string, Response>()

// Send event to specific user
function sendSSEEvent(userId: string, event: string, data: any) {
  const client = sseClients.get(userId)
  if (client) {
    client.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`)
  }
}

// SSE message format:
// event: <event-name>    (optional, defaults to 'message')
// data: <string>         (required)
// id: <event-id>         (optional, for reconnection)
// retry: 3000            (optional, reconnect delay in ms)
//                        (blank line terminates the event)
```

## Client (Browser)
```typescript
const es = new EventSource('/events', { withCredentials: true })

es.onopen = () => console.log('SSE connected')

es.addEventListener('connected', (e) => {
  const data = JSON.parse(e.data)
  console.log('Authenticated as', data.userId)
})

es.addEventListener('notification', (e) => {
  const notification = JSON.parse(e.data)
  showToast(notification.message)
})

es.onerror = (e) => {
  // Browser auto-reconnects — no manual handling needed
  console.error('SSE error:', e)
}

// Close when no longer needed
es.close()
```

# SCALING WITH REDIS PUB/SUB
```typescript
// Problem: multiple server instances each have their own connected clients
// Solution: use Redis pub/sub as a message bus between instances

import { createClient } from 'redis'

const publisher  = createClient({ url: process.env.REDIS_URL })
const subscriber = createClient({ url: process.env.REDIS_URL })

await publisher.connect()
await subscriber.connect()

// Subscribe to channels
await subscriber.subscribe('notifications', (message) => {
  const { userId, event, data } = JSON.parse(message)
  // Send to local client if connected on this instance
  sendToLocalClient(userId, event, data)
})

// Publish from any instance
async function notifyUser(userId: string, event: string, data: any) {
  await publisher.publish('notifications', JSON.stringify({ userId, event, data }))
}

// For Socket.IO: use socket.io-redis adapter
import { createAdapter } from '@socket.io/redis-adapter'
io.adapter(createAdapter(publisher, subscriber))
// Now io.to('room').emit() works across all instances automatically
```

# REACT HOOKS FOR REALTIME
```typescript
// useWebSocket hook
function useWebSocket(url: string) {
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen  = () => setConnected(true)
    ws.onclose = () => setConnected(false)

    return () => ws.close()
  }, [url])

  const send = useCallback((data: object) => {
    wsRef.current?.send(JSON.stringify(data))
  }, [])

  return { connected, send, ws: wsRef.current }
}

// useSSE hook
function useSSE<T>(url: string, eventName: string) {
  const [data, setData] = useState<T | null>(null)

  useEffect(() => {
    const es = new EventSource(url, { withCredentials: true })
    es.addEventListener(eventName, (e) => setData(JSON.parse(e.data)))
    return () => es.close()
  }, [url, eventName])

  return data
}
```
