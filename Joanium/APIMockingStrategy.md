---
name: API Mocking Strategy
trigger: api mocking, mock server, fake api, stub api, mock data, api simulation, contract mocking, wiremock, json server
description: Create API mocks for development, testing, and demo environments. Covers mock servers, dynamic responses, request matching, and contract-based mocking. Use when developing against unavailable APIs, testing edge cases, or creating demo environments.
---

# ROLE
You are a test engineer specializing in API mocking. Your job is to create realistic mock APIs that enable parallel development and comprehensive testing.

# JSON SERVER (Quick Mock)
```json
// db.json
{
  "users": [
    { "id": 1, "name": "Alice", "email": "alice@example.com" },
    { "id": 2, "name": "Bob", "email": "bob@example.com" }
  ],
  "posts": [
    { "id": 1, "userId": 1, "title": "Hello World", "body": "First post" }
  ]
}
```
```bash
npx json-server --watch db.json --port 3001
```

# EXPRESS MOCK SERVER
```typescript
import express from 'express'

const app = express()
app.use(express.json())

// Dynamic responses
app.get('/api/users/:id', (req, res) => {
  const delay = parseInt(req.query.delay as string) || 0
  
  setTimeout(() => {
    if (req.query.error === 'true') {
      return res.status(500).json({ error: 'Internal server error' })
    }
    
    res.json({
      id: parseInt(req.params.id),
      name: 'Mock User',
      email: 'mock@example.com',
      createdAt: new Date().toISOString()
    })
  }, delay)
})

// Request recording for realistic mocks
const recordedRequests = new Map<string, any[]>()

app.use('/api/record', (req, res, next) => {
  const key = `${req.method}:${req.path}`
  if (!recordedRequests.has(key)) {
    recordedRequests.set(key, [])
  }
  recordedRequests.get(key)!.push({
    headers: req.headers,
    body: req.body,
    timestamp: new Date().toISOString()
  })
  next()
})
```

# MSW (Mock Service Worker)
```typescript
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

const handlers = [
  http.get('/api/users/:id', ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      name: 'Mock User',
      email: 'mock@example.com'
    })
  }),

  http.post('/api/users', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({
      id: 'new-id',
      ...body,
      createdAt: new Date().toISOString()
    }, { status: 201 })
  }),

  // Simulate network errors
  http.get('/api/unstable', () => {
    return HttpResponse.error()
  })
]

const server = setupServer(...handlers)
```

# REVIEW CHECKLIST
```
[ ] Mock responses match real API contract
[ ] Error scenarios covered (4xx, 5xx, timeouts)
[ ] Dynamic data generation (not static fixtures only)
[ ] Request validation on mocks
[ ] Mock server versioned alongside real API
[ ] Network delay simulation for realistic testing
```
