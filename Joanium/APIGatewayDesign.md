---
name: API Gateway Design
trigger: api gateway, design an api gateway, gateway pattern, rate limiting gateway, routing gateway, api gateway architecture
description: Design and implement API gateway patterns including routing, rate limiting, authentication, caching, and request transformation. Use when building an API gateway or when user mentions gateway, routing, or API management.
---

# ROLE
You are a senior platform engineer specializing in API gateway design. Your job is to help architect, configure, and deploy API gateways that handle routing, authentication, rate limiting, and observability.

# CORE PATTERNS

## Gateway Responsibilities
```
Routing        → Forward requests to appropriate backend services
Authentication → Validate tokens, API keys, OAuth before reaching services
Rate Limiting  → Protect backends from abuse and overload
Caching        → Cache responses for frequently requested data
Transformation → Modify request/response formats between client and backend
Logging        → Centralized request/response logging for observability
Load Balancing → Distribute traffic across service instances
Circuit Breaker → Prevent cascading failures when backends are unhealthy
```

## Gateway Architecture
```
Client → API Gateway → [Auth] → [Rate Limit] → [Cache] → [Route] → Backend Services
                                                    ↓
                                              [Transform]
                                                    ↓
                                              [Log/Metrics]
```

## Common Gateway Implementations

### Kong Gateway
```yaml
# kong.yml - declarative configuration
_format_version: "3.0"
services:
  - name: user-service
    url: http://user-service:8080
    routes:
      - name: users-route
        paths:
          - /api/users
    plugins:
      - name: rate-limiting
        config:
          minute: 100
          policy: local
      - name: jwt
        config:
          key_claim_name: iss
      - name: cors
        config:
          origins:
            - https://example.com
```

### NGINX as API Gateway
```nginx
upstream user_service {
    server user-service-1:8080;
    server user-service-2:8080;
}

upstream order_service {
    server order-service-1:8080;
    server order-service-2:8080;
}

server {
    listen 80;
    server_name api.example.com;

    # Rate limiting zone
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    location /api/users {
        limit_req zone=api_limit burst=20;
        proxy_pass http://user_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/orders {
        limit_req zone=api_limit burst=20;
        proxy_pass http://order_service;
    }
}
```

### Express.js API Gateway
```typescript
import express from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import rateLimit from 'express-rate-limit'

const app = express()

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP'
})

app.use(limiter)

// Authentication middleware
const authenticate = async (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1]
  if (!token) return res.status(401).json({ error: 'Unauthorized' })
  
  try {
    req.user = await verifyToken(token)
    next()
  } catch {
    res.status(401).json({ error: 'Invalid token' })
  }
}

// Routing
app.use('/api/users', authenticate, createProxyMiddleware({
  target: 'http://user-service:8080',
  changeOrigin: true,
  pathRewrite: { '^/api/users': '/users' }
}))

app.use('/api/orders', authenticate, createProxyMiddleware({
  target: 'http://order-service:8080',
  changeOrigin: true
}))
```

## Circuit Breaker Pattern
```typescript
class CircuitBreaker {
  private state: 'closed' | 'open' | 'half-open' = 'closed'
  private failureCount = 0
  private lastFailureTime: number | null = null
  
  constructor(
    private threshold: number = 5,
    private timeout: number = 30000
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - (this.lastFailureTime || 0) > this.timeout) {
        this.state = 'half-open'
      } else {
        throw new Error('Circuit breaker is open')
      }
    }

    try {
      const result = await fn()
      this.onSuccess()
      return result
    } catch (error) {
      this.onFailure()
      throw error
    }
  }

  private onSuccess() {
    this.failureCount = 0
    this.state = 'closed'
  }

  private onFailure() {
    this.failureCount++
    this.lastFailureTime = Date.now()
    if (this.failureCount >= this.threshold) {
      this.state = 'open'
    }
  }
}
```

## Request Transformation
```typescript
// Transform incoming requests before forwarding
function transformRequest(req: Request): TransformedRequest {
  return {
    ...req,
    headers: {
      ...req.headers,
      'X-Request-ID': generateRequestId(),
      'X-Forwarded-For': req.ip,
      'X-Gateway-Version': '1.0.0'
    },
    body: sanitizeInput(req.body)
  }
}

// Transform responses before returning to client
function transformResponse(res: Response, backendResponse: any): ApiResponse {
  return {
    success: res.status < 400,
    data: backendResponse.data,
    meta: {
      requestId: res.headers['x-request-id'],
      timestamp: new Date().toISOString(),
      version: 'v1'
    }
  }
}
```

## Health Check Aggregation
```typescript
async function aggregateHealthChecks(services: ServiceConfig[]): Promise<HealthStatus> {
  const results = await Promise.allSettled(
    services.map(async (service) => {
      const start = Date.now()
      const response = await fetch(`${service.url}/health`)
      return {
        name: service.name,
        status: response.ok ? 'healthy' : 'unhealthy',
        latency: Date.now() - start,
        details: await response.json()
      }
    })
  )

  return {
    overall: results.every(r => r.status === 'fulfilled' && r.value.status === 'healthy')
      ? 'healthy'
      : 'degraded',
    services: results.map(r => r.status === 'fulfilled' ? r.value : { status: 'unreachable' })
  }
}
```

# DESIGN DECISIONS

## When to Use an API Gateway
```
USE when:
- Multiple microservices need unified entry point
- Cross-cutting concerns (auth, rate limiting, logging) are duplicated
- Clients need request/response transformation
- You need centralized observability and monitoring

DON'T USE when:
- Single monolithic application (overkill)
- Simple CRUD app with one backend
- Low-latency requirements (adds hop)
```

## Gateway vs Service Mesh
```
API Gateway: North-South traffic (client to services)
Service Mesh: East-West traffic (service to service)

Use both for complete coverage:
Client → API Gateway → Service Mesh → Backend Services
```

# REVIEW CHECKLIST
```
[ ] Authentication and authorization configured
[ ] Rate limiting appropriate for each endpoint
[ ] Circuit breakers prevent cascading failures
[ ] Request/response transformation handles edge cases
[ ] Health checks monitor all backend services
[ ] Logging includes correlation IDs for tracing
[ ] CORS configured correctly for frontend clients
[ ] Timeout and retry policies set appropriately
```
