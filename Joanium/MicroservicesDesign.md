---
name: Microservices Design
trigger: microservices, service architecture, microservice pattern, service mesh, API gateway, service communication, service discovery, distributed systems, event-driven architecture, domain-driven design, service boundary, inter-service communication, distributed tracing, saga pattern
description: Design and build microservice architectures. Covers service decomposition, synchronous (REST/gRPC) and asynchronous (events) communication, API gateway, service discovery, distributed tracing, the Saga pattern for distributed transactions, and common failure patterns.
---

# ROLE
You are a distributed systems architect. Your job is to decompose monoliths sensibly, design service boundaries that minimize coupling, and build systems that fail gracefully. Microservices solve real scaling problems — but they introduce complexity. Only go there when you need to.

# WHEN TO USE MICROSERVICES
```
CONSIDER MICROSERVICES WHEN:
  ✓ Teams are large enough that a monolith creates deploy bottlenecks
  ✓ Different services need different scaling characteristics
  ✓ Different parts of the system need different tech stacks
  ✓ Compliance requires data isolation (PCI, HIPAA)
  ✓ You've already built and understood the domain as a monolith

STAY WITH A MONOLITH WHEN:
  ✗ Small team (< 10 engineers)
  ✗ Domain is not yet well understood
  ✗ Early-stage product with rapidly changing requirements
  ✗ Network latency and operational complexity outweigh benefits

RULE: Start as a modular monolith. Extract services when you have clear scaling or team reasons.
```

# SERVICE DECOMPOSITION

## Boundaries — Domain-Driven Design
```
GOOD boundary signals:
  - Different data ownership (each service owns its DB — no shared DB)
  - Different change rates (payments changes rarely; user profiles frequently)
  - Different scaling needs (image processing vs. auth)
  - Different teams own them

BAD boundaries (too granular):
  - "UserService" + "UserProfileService" + "UserPreferencesService"
    → They share data, change together, deployed together anyway

Example decomposition for e-commerce:
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │ Order Service│  │Product Service│  │  User Service │
  │ - Orders DB  │  │ - Products DB │  │  - Users DB  │
  └──────┬───────┘  └──────┬────────┘  └──────┬───────┘
         │                 │                   │
  ┌──────▼───────┐  ┌──────▼────────┐  ┌──────▼───────┐
  │Payment Service│  │Inventory Svc  │  │  Auth Service│
  └──────────────┘  └───────────────┘  └──────────────┘
```

# SERVICE COMMUNICATION

## Synchronous — REST
```typescript
// Service A calling Service B via REST
// Use a shared HTTP client with timeout, retry, and circuit breaking

import axios from 'axios'
import axiosRetry from 'axios-retry'
import CircuitBreaker from 'opossum'

// Create service client with resilience
function createServiceClient(baseURL: string) {
  const client = axios.create({
    baseURL,
    timeout: 5000,    // fail fast — 5 second timeout
    headers: { 'X-Internal-Service': process.env.SERVICE_NAME! }
  })

  // Retry on network errors and 5xx (not 4xx — those are client errors)
  axiosRetry(client, {
    retries: 3,
    retryDelay: axiosRetry.exponentialDelay,
    retryCondition: (err) => axiosRetry.isNetworkError(err) ||
      (err.response?.status ?? 0) >= 500
  })

  return client
}

const userService = createServiceClient(process.env.USER_SERVICE_URL!)

// Circuit breaker — open after 50% failures, prevents cascading failures
const getUserCircuit = new CircuitBreaker(
  (userId: string) => userService.get(`/users/${userId}`),
  {
    errorThresholdPercentage: 50,
    resetTimeout: 10_000,   // retry after 10 seconds
    timeout: 5_000,
  }
)

getUserCircuit.fallback((userId: string) => {
  // Return cached/default data when circuit is open
  return { data: { id: userId, name: 'Unknown', role: 'user' } }
})

// Usage in Order Service
async function getOrderWithUser(orderId: string) {
  const order = await db.orders.findById(orderId)

  // Call User Service — falls back gracefully if it's down
  const { data: user } = await getUserCircuit.fire(order.userId)

  return { ...order, user }
}
```

## Synchronous — gRPC (High-Performance Internal)
```protobuf
// user.proto
syntax = "proto3";
package user;

service UserService {
  rpc GetUser(GetUserRequest) returns (User);
  rpc ListUsers(ListUsersRequest) returns (stream User);  // streaming
}

message GetUserRequest { string user_id = 1; }
message User {
  string id = 1;
  string name = 2;
  string email = 3;
  string role = 4;
}
```

```typescript
import * as grpc from '@grpc/grpc-js'
import * as protoLoader from '@grpc/proto-loader'

// Server
const packageDef = protoLoader.loadSync('user.proto')
const proto = grpc.loadPackageDefinition(packageDef) as any

const server = new grpc.Server()
server.addService(proto.user.UserService.service, {
  getUser: async (call, callback) => {
    const user = await db.users.findById(call.request.userId)
    if (!user) return callback({ code: grpc.status.NOT_FOUND })
    callback(null, user)
  }
})
server.bindAsync('0.0.0.0:50051', grpc.ServerCredentials.createInsecure(), () => server.start())

// Client
const client = new proto.user.UserService('user-service:50051', grpc.credentials.createInsecure())
// gRPC call: ~2x faster than REST for internal calls, strongly typed
```

## Asynchronous — Event-Driven
```typescript
// Services communicate via events — fully decoupled
// Publisher doesn't know or care who listens

// Event schema — define in a shared package
interface DomainEvent<T = any> {
  eventId: string
  eventType: string
  aggregateId: string    // e.g., userId, orderId
  aggregateType: string  // e.g., 'User', 'Order'
  payload: T
  occurredAt: string
  version: number
}

// Order Service publishes
async function placeOrder(customerId: string, items: OrderItem[]) {
  const order = await db.orders.create({ customerId, items, status: 'pending' })

  await eventBus.publish<OrderPlacedEvent>({
    eventId: crypto.randomUUID(),
    eventType: 'order.placed',
    aggregateId: order.id,
    aggregateType: 'Order',
    payload: { orderId: order.id, customerId, items, total: order.total },
    occurredAt: new Date().toISOString(),
    version: 1,
  })

  return order
}

// Inventory Service consumes — no coupling to Order Service
eventBus.subscribe('order.placed', async (event: DomainEvent<OrderPlacedEvent>) => {
  await reserveInventory(event.payload.items)
  await eventBus.publish({ eventType: 'inventory.reserved', /* ... */ })
})

// Email Service consumes — also no coupling
eventBus.subscribe('order.placed', async (event: DomainEvent<OrderPlacedEvent>) => {
  await sendOrderConfirmationEmail(event.payload.customerId, event.payload.orderId)
})
```

# SAGA PATTERN — DISTRIBUTED TRANSACTIONS

## Choreography Saga (Event-Driven)
```
Problem: How do you roll back a multi-service operation if one step fails?

Order Saga:
  OrderService → order.placed
    ↓
  PaymentService listens → charges card → payment.completed
    ↓
  InventoryService listens → reserves stock → inventory.reserved
    ↓
  ShippingService listens → creates shipment → shipment.created
    ↓
  OrderService listens → marks order as confirmed

COMPENSATION on failure:
  InventoryService fails → publishes inventory.failed
    → PaymentService listens → refunds card (compensation)
    → OrderService listens → marks order as failed
```

```typescript
// Payment Service — with compensation
eventBus.subscribe('order.placed', async (event) => {
  try {
    const charge = await stripe.charges.create({
      amount: event.payload.total,
      customer: event.payload.customerId,
    })

    await eventBus.publish({ eventType: 'payment.completed', payload: { chargeId: charge.id, ...event.payload } })
  } catch {
    await eventBus.publish({ eventType: 'payment.failed', payload: event.payload })
  }
})

// If inventory fails later — Payment Service compensates
eventBus.subscribe('inventory.failed', async (event) => {
  if (event.payload.chargeId) {
    await stripe.refunds.create({ charge: event.payload.chargeId })
    await eventBus.publish({ eventType: 'payment.refunded', payload: event.payload })
  }
})
```

# API GATEWAY
```typescript
// Gateway responsibilities:
// - Single entry point for clients
// - Auth verification (so each service doesn't implement it)
// - Rate limiting
// - Request routing
// - Response aggregation (BFF pattern)
// - SSL termination

// Using express-http-proxy as a simple gateway
import proxy from 'express-http-proxy'

const app = express()

// Auth middleware — verify JWT once at gateway, forward user info in headers
app.use(async (req, res, next) => {
  const token = req.headers.authorization?.slice(7)
  if (!token) return next()   // let services decide if auth is required

  try {
    const user = verifyAccessToken(token)
    req.headers['X-User-Id']   = user.userId
    req.headers['X-User-Role'] = user.role
    delete req.headers.authorization   // don't forward raw token to services
  } catch {
    // Token invalid — services can reject if they need auth
  }
  next()
})

// Route to services
app.use('/api/users',    proxy(process.env.USER_SERVICE_URL!))
app.use('/api/orders',   proxy(process.env.ORDER_SERVICE_URL!))
app.use('/api/products', proxy(process.env.PRODUCT_SERVICE_URL!))

// BFF: Aggregate response for mobile clients
app.get('/api/dashboard', requireAuth, async (req, res) => {
  const [user, orders, recommendations] = await Promise.allSettled([
    userClient.get(`/users/${req.headers['X-User-Id']}`),
    orderClient.get(`/orders?userId=${req.headers['X-User-Id']}&limit=5`),
    productClient.get(`/products/recommended?userId=${req.headers['X-User-Id']}`),
  ])

  res.json({
    user: user.status === 'fulfilled' ? user.value.data : null,
    recentOrders: orders.status === 'fulfilled' ? orders.value.data : [],
    recommendations: recommendations.status === 'fulfilled' ? recommendations.value.data : [],
  })
})
```

# DISTRIBUTED TRACING
```typescript
// Use OpenTelemetry — instrument once, send to Jaeger/Zipkin/Datadog
import { NodeSDK } from '@opentelemetry/sdk-node'
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http'

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({ url: process.env.OTEL_EXPORTER_URL }),
  serviceName: 'order-service',
})
sdk.start()

// Propagate trace context in HTTP headers (auto-done by OTel HTTP instrumentation)
// When Service A calls Service B, trace ID flows through:
// Order Service [trace: abc123, span: 001] → User Service [trace: abc123, span: 002]
// You can see the full request path in Jaeger

// Manual span for custom operations
import { trace } from '@opentelemetry/api'
const tracer = trace.getTracer('order-service')

async function processOrder(orderId: string) {
  const span = tracer.startSpan('processOrder', {
    attributes: { 'order.id': orderId }
  })

  try {
    const result = await doWork(orderId)
    span.setStatus({ code: SpanStatusCode.OK })
    return result
  } catch (err) {
    span.recordException(err as Error)
    span.setStatus({ code: SpanStatusCode.ERROR })
    throw err
  } finally {
    span.end()
  }
}
```

# HEALTH CHECKS AND READINESS
```typescript
// Each service must expose:
// /health/live  — is the process alive? (liveness)
// /health/ready — can it handle requests? (readiness — DB connected, etc.)

app.get('/health/live', (req, res) => {
  res.json({ status: 'ok', service: 'order-service', timestamp: Date.now() })
})

app.get('/health/ready', async (req, res) => {
  const checks = await Promise.allSettled([
    db.query('SELECT 1'),      // DB connection
    redis.ping(),              // Cache connection
    eventBus.healthCheck(),    // Queue connection
  ])

  const [db_, redis_, queue] = checks.map(c => c.status === 'fulfilled')
  const healthy = db_ && redis_ && queue

  res.status(healthy ? 200 : 503).json({
    status: healthy ? 'ready' : 'not-ready',
    checks: { database: db_, redis: redis_, queue }
  })
})
```
