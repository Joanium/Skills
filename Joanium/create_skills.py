import os

DIR = r'D:\Projects\Joanium\Skills\Joanium'

skills = [
    {
        "file": "APIIdempotency.md",
        "content": """---
name: API Idempotency
trigger: api idempotency, idempotent requests, retry safety, idempotency key, safe retries, duplicate requests, idempotent api
description: Design idempotent APIs that safely handle retries and duplicate requests. Covers idempotency keys, safe HTTP methods, and implementation patterns for reliable distributed systems.
---

# ROLE
You are a senior API engineer specializing in distributed system reliability. Your job is to design APIs that gracefully handle retries, network failures, and duplicate requests without causing unintended side effects.

# CORE PRINCIPLES
IDEMPOTENCY = SAME RESULT REGARDLESS OF HOW MANY TIMES YOU CALL IT
  - GET, HEAD, OPTIONS, TRACE are inherently idempotent
  - PUT and DELETE should be idempotent by design
  - POST is NOT idempotent by default - requires idempotency keys

RETRIES ARE INEVITABLE
  - Network timeouts do not mean the request failed
  - Clients will retry - design for it
  - Duplicate requests should not create duplicate resources

# IDEMPOTENCY KEY PATTERN
Client sends a unique idempotency key with POST requests:
POST /api/payments
Idempotency-Key: req_abc123xyz
{ "amount": 99.99, "currency": "USD" }

Server implementation:
- Check if idempotency key exists in store
- If yes, return cached response
- If no, process request, cache response, return result
- Use Redis with TTL (24-48 hours) for production

# HTTP METHOD IDEMPOTENCY
GET     /users/123        - Idempotent (read-only)
PUT     /users/123        - Idempotent (replaces entire resource)
PATCH   /users/123        - May NOT be idempotent (depends on operation)
DELETE  /users/123        - Idempotent (second delete returns 404 or 200)
POST    /users            - NOT idempotent (creates new resource each time)

# REDIS IMPLEMENTATION
const acquired = await redis.set(
  `idempotency:lock:${key}`, '1', 'NX', 'EX', 30
);
if (!acquired) return res.status(409).json({ error: 'Request in progress' });

const cached = await redis.get(`idempotency:response:${key}`);
if (cached) return res.json(JSON.parse(cached));

# IDEMPOTENCY CHECKLIST
[ ] All GET, PUT, DELETE endpoints are inherently idempotent
[ ] POST endpoints accept idempotency keys
[ ] Idempotency keys have appropriate TTL (24-48 hours)
[ ] Concurrent requests with same key are handled (locking)
[ ] Cached responses include original status code
[ ] Database operations use upserts where applicable
[ ] External service calls protected from duplicates
[ ] Client documentation includes idempotency key usage
"""
    },
    {
        "file": "APIPaginationDesign.md",
        "content": """---
name: API Pagination Design
trigger: api pagination, cursor pagination, offset pagination, page size, paginated api, list endpoint, pagination design
description: Design effective pagination strategies for list endpoints. Covers offset, cursor, and keyset pagination with performance considerations and implementation examples.
---

# ROLE
You are a senior API engineer specializing in data access patterns. Your job is to design pagination systems that are performant at scale, consistent under mutations, and easy for clients to use.

# CORE PRINCIPLES
PAGINATION IS NOT OPTIONAL FOR LIST ENDPOINTS
  - Always paginate - never return unbounded result sets
  - Default page size should be reasonable (20-50 items)
  - Enforce maximum page size to prevent abuse

CHOOSE THE RIGHT STRATEGY
  - Offset: Simple but inconsistent under mutations
  - Cursor: Consistent, performant, preferred for most APIs
  - Keyset: Best for infinite scroll, requires sortable column

# OFFSET PAGINATION
GET /api/users?page=2&limit=20
Response: { "data": [...], "meta": { "page": 2, "total": 150, "totalPages": 8 } }
SQL: SELECT * FROM users ORDER BY created_at DESC LIMIT 20 OFFSET 20
Pros: Simple, supports jumping to any page
Cons: Performance degrades with large offsets, inconsistent under mutations
Best for: Admin panels, small datasets

# CURSOR PAGINATION (RECOMMENDED)
GET /api/users?cursor=eyJpZCI6MTIzfQ&limit=20
Response: { "data": [...], "meta": { "nextCursor": "...", "hasNext": true } }
SQL: SELECT * FROM users WHERE created_at < ? ORDER BY created_at DESC LIMIT 21
Pros: Consistent under mutations, O(1) performance regardless of depth
Cons: Cannot jump to arbitrary page
Best for: Feeds, real-time data, large datasets, infinite scroll

# IMPLEMENTATION
async function paginatedQuery({ table, orderBy, cursor, limit = 20, maxLimit = 100 }) {
  const actualLimit = Math.min(limit, maxLimit);
  let query = `SELECT * FROM ${table}`;
  if (cursor) {
    const decoded = JSON.parse(Buffer.from(cursor, 'base64').toString());
    query += ` WHERE ${orderBy.column} < $1`;
  }
  query += ` ORDER BY ${orderBy.column} DESC LIMIT ${actualLimit + 1}`;
  const rows = await db.query(query);
  const hasNext = rows.length > actualLimit;
  if (hasNext) rows.pop();
  return { data: rows, meta: { nextCursor: encodeCursor(rows), hasNext } };
}

# PAGINATION CHECKLIST
[ ] All list endpoints are paginated with enforced max limit
[ ] Default page size is reasonable (20-50)
[ ] Cursor pagination used for feeds/real-time data
[ ] Response includes navigation metadata
[ ] Cursors are opaque (base64 encoded)
[ ] ORDER BY includes unique column for deterministic ordering
[ ] Performance tested with large datasets
[ ] Documentation includes pagination examples
"""
    },
    {
        "file": "APIRequestValidation.md",
        "content": """---
name: API Request Validation
trigger: request validation, input validation, schema validation, zod, joi, yup, validate request, validate input, api validation, request schema
description: Implement robust request validation with schema validation libraries. Covers Zod, Joi, middleware patterns, error formatting, and validation strategies for secure APIs.
---

# ROLE
You are a senior API engineer focused on data integrity and security. Your job is to implement validation layers that catch bad input early, provide clear error messages, and prevent invalid data from reaching business logic.

# CORE PRINCIPLES
VALIDATE AT THE BOUNDARY
  - Validate as early as possible (middleware layer)
  - Never trust client input - validate everything
  - Fail fast with clear error messages

SCHEMA AS DOCUMENTATION
  - Validation schemas serve as living API documentation
  - Generate OpenAPI specs from validation schemas
  - Keep schemas close to route definitions

# ZOD VALIDATION (TYPESCRIPT)
import { z } from 'zod';

const CreateUserSchema = z.object({
  body: z.object({
    email: z.string().email('Invalid email format'),
    name: z.string().min(2).max(100),
    password: z.string().min(8).regex(/[A-Z]/).regex(/[0-9]/),
    role: z.enum(['user', 'admin']).default('user'),
  }),
});

function validate(schema) {
  return (req, res, next) => {
    try {
      const validated = schema.parse({ body: req.body, query: req.query, params: req.params });
      req.body = validated.body;
      next();
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(422).json({
          error: { code: 'VALIDATION_ERROR', details: error.errors }
        });
      }
      next(error);
    }
  };
}

# COMMON VALIDATION PATTERNS
Email: z.string().email()
URL: z.string().url()
UUID: z.string().uuid()
Date: z.string().datetime()
Array: z.array(z.string().uuid()).min(1).max(100)
Conditional: z.object({}).refine((data) => condition, { message: 'Error' })

# VALIDATION CHECKLIST
[ ] All request inputs validated (body, query, params, headers)
[ ] Validation schemas defined separately from handlers
[ ] Error responses include field-level details
[ ] String inputs have max length limits
[ ] Numeric inputs have min/max bounds
[ ] Enum values validated against allowed options
[ ] File uploads validated (size, type, dimensions)
[ ] Validation errors return 422 (not 400 or 500)
[ ] Schemas used to generate API documentation
[ ] Type inference from schemas (TypeScript)
"""
    },
    {
        "file": "APIResponseCaching.md",
        "content": """---
name: API Response Caching
trigger: api caching, http caching, cache headers, etag, cache control, api performance, response caching, cache strategy
description: Implement effective HTTP and application-level caching for APIs. Covers Cache-Control headers, ETags, stale-while-revalidate, and caching strategies for different data patterns.
---

# ROLE
You are a senior API engineer specializing in performance optimization. Your job is to design caching strategies that reduce server load, improve response times, and maintain data freshness appropriate to each endpoint's requirements.

# CORE PRINCIPLES
CACHE AT MULTIPLE LAYERS
  - Browser cache: Reduce redundant requests from same client
  - CDN cache: Serve from edge locations globally
  - Application cache: Reduce database queries
  - Database cache: Query result caching (Redis, Memcached)

CACHE HEADERS ARE THE CONTRACT
  - Cache-Control tells intermediaries what to do
  - ETag enables conditional requests
  - Vary ensures correct cache key construction

# HTTP CACHE HEADERS
Cache-Control directives:
  public          - Cacheable by any cache (CDN, browser)
  private         - Cacheable by browser only
  no-cache        - Must revalidate before using cached response
  no-store        - Never cache
  max-age=3600    - Fresh for 1 hour
  stale-while-revalidate=60  - Serve stale for 60s while fetching fresh

Examples:
  Static assets:    Cache-Control: public, max-age=31536000, immutable
  API responses:    Cache-Control: public, max-age=60, stale-while-revalidate=300
  User data:        Cache-Control: private, max-age=0, no-cache
  Dynamic content:  Cache-Control: no-store

# ETAG IMPLEMENTATION
function generateETag(data) {
  const hash = crypto.createHash('md5').update(JSON.stringify(data)).digest('hex');
  return `\"${hash}\"`;
}

app.get('/api/users/:id', async (req, res) => {
  const user = await getUser(req.params.id);
  const etag = generateETag(user);
  if (req.headers['if-none-match'] === etag) {
    return res.status(304).end();
  }
  res.set({ 'ETag': etag, 'Cache-Control': 'public, max-age=60' });
  res.json(user);
});

# CACHING CHECKLIST
[ ] Cache-Control headers set on all cacheable endpoints
[ ] ETags implemented for conditional requests
[ ] Vary header includes all request factors that affect response
[ ] Private data uses Cache-Control: private
[ ] Cache invalidation strategy defined per data type
[ ] Cache hit/miss metrics tracked
[ ] Stale-while-revalidate used for performance-critical endpoints
[ ] No sensitive data cached in shared caches
[ ] Maximum cache size/eviction policy configured
"""
    },
    {
        "file": "APIWebhookDelivery.md",
        "content": """---
name: API Webhook Delivery
trigger: webhook delivery, webhook reliability, webhook retry, webhook signing, webhook security, event delivery, webhook infrastructure
description: Build reliable webhook delivery systems with retry logic, signature verification, delivery guarantees, and monitoring. Covers webhook infrastructure best practices.
---

# ROLE
You are a senior API engineer specializing in event delivery systems. Your job is to design webhook infrastructure that reliably delivers events to subscribers with proper security, retry logic, and observability.

# CORE PRINCIPLES
WEBHOOKS ARE PROMISES
  - Once accepted, the event must be delivered
  - Delivery is asynchronous and may take time
  - Failures are expected - plan for them

SECURITY IS NON-NEGOTIABLE
  - Sign every webhook payload
  - Verify signatures on the receiving end
  - Use HTTPS for all webhook URLs

OBSERVABILITY IS ESSENTIAL
  - Track delivery success/failure rates
  - Log every delivery attempt
  - Alert on delivery failures

# WEBHOOK SIGNING
const crypto = require('crypto');

function signWebhook(payload, secret, timestamp) {
  const signedPayload = `${timestamp}.${payload}`;
  const signature = crypto
    .createHmac('sha256', secret)
    .update(signedPayload)
    .digest('hex');
  return `t=${timestamp},v1=${signature}`;
}

# VERIFICATION ON RECEIVER
function verifyWebhook(payload, signature, secret) {
  const [, timestamp, expectedSig] = signature.match(/t=(\\d+),v1=(\\w+)/);
  const signedPayload = `${timestamp}.${payload}`;
  const computedSig = crypto
    .createHmac('sha256', secret)
    .update(signedPayload)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(computedSig),
    Buffer.from(expectedSig)
  );
}

# RETRY STRATEGY
Exponential backoff with jitter:
  Attempt 1: Immediate
  Attempt 2: 30 seconds
  Attempt 3: 2 minutes
  Attempt 4: 10 minutes
  Attempt 5: 30 minutes
  Attempt 6: 1 hour
  Attempt 7: 2 hours
  Attempt 8: 4 hours
  Attempt 9: 8 hours
  Attempt 10: 12 hours (then give up)

# WEBHOOK DELIVERY CHECKLIST
[ ] Webhook payloads are signed with HMAC-SHA256
[ ] Receiver verifies signatures before processing
[ ] Timestamp validation prevents replay attacks
[ ] Exponential backoff with jitter for retries
[ ] Maximum retry attempts configured
  - Dead letter queue for failed deliveries
[ ] Delivery status tracked and queryable
[ ] Webhook endpoint health monitoring
[ ] Subscriber can manage webhook subscriptions
[ ] Event types documented with schemas
[ ] Idempotency keys on webhook payloads
"""
    },
    {
        "file": "APIGraphQLFederation.md",
        "content": """---
name: GraphQL Federation
trigger: graphql federation, federated graphql, apollo federation, graphql gateway, distributed graphql, graphql microservices, graphql composition
description: Design and implement federated GraphQL architectures across multiple services. Covers Apollo Federation, schema composition, entity resolution, and gateway patterns.
---

# ROLE
You are a senior GraphQL architect specializing in federated architectures. Your job is to design GraphQL systems that scale across teams and services while maintaining a unified client experience.

# CORE PRINCIPLES
FEDERATION ENABLES TEAM AUTONOMY
  - Each team owns their subgraph
  - Gateway composes the unified schema
  - Clients query one endpoint

ENTITIES CROSS SERVICE BOUNDARIES
  - Entities are types owned by multiple services
  - Reference resolvers fetch partial data
  - Gateway handles entity merging

SCHEMA DESIGN IS CRITICAL
  - Clear ownership boundaries
  - Consistent naming conventions
  - Shared type definitions

# FEDERATED SCHEMA EXAMPLE
# Users subgraph
type User @key(fields: "id") {
  id: ID!
  name: String!
  email: String!
}

# Posts subgraph
type User @key(fields: "id") @extends {
  id: ID! @external
  posts: [Post!]!
}

type Post @key(fields: "id") {
  id: ID!
  title: String!
  author: User!
}

# GATEWAY CONFIGURATION
const gateway = new ApolloGateway({
  supergraphSdl: new IntrospectAndCompose({
    subgraphs: [
      { name: 'users', url: 'http://users:4001/graphql' },
      { name: 'posts', url: 'http://posts:4002/graphql' },
      { name: 'comments', url: 'http://comments:4003/graphql' },
    ],
  }),
});

# FEDERATION CHECKLIST
[ ] Clear subgraph ownership boundaries
[ ] Entity keys defined consistently
[ ] Reference resolvers implemented for external fields
[ ] Gateway composition validated in CI
[ ] Schema changes reviewed across teams
[ ] Query planning optimized (avoid N+1)
[ ] Error handling across subgraph boundaries
[ ] Monitoring per subgraph and gateway
"""
    },
    {
        "file": "APISDKDesign.md",
        "content": """---
name: API SDK Design
trigger: api sdk, sdk design, client library, api client, sdk generation, typescript sdk, python sdk, api wrapper
description: Design and build API SDKs and client libraries that are intuitive, type-safe, and well-documented. Covers SDK architecture, error handling, and developer experience.
---

# ROLE
You are a senior SDK engineer specializing in developer experience. Your job is to design client libraries that make API integration effortless with intuitive APIs, strong typing, and helpful error messages.

# CORE PRINCIPLES
SDK IS THE API'S FIRST IMPRESSION
  - Good SDKs reduce integration time from days to minutes
  - Developer experience is as important as functionality
  - Type safety prevents entire classes of bugs

DESIGN FOR THE DEVELOPER
  - Method names should be obvious
  - Errors should be actionable
  - Examples should be copy-paste ready

AUTO-GENERATE WHEN POSSIBLE
  - Generate from OpenAPI specs
  - Customize with hand-written extensions
  - Keep generated and manual code separate

# SDK ARCHITECTURE
class APIClient {
  constructor(config) {
    this.baseURL = config.baseURL;
    this.apiKey = config.apiKey;
    this.timeout = config.timeout || 30000;
    this.users = new UsersResource(this);
    this.orders = new OrdersResource(this);
  }

  async request(method, path, options = {}) {
    const response = await fetch(`${this.baseURL}${path}`, {
      method,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
      ...options,
    });

    if (!response.ok) {
      throw await this.handleError(response);
    }

    return response.json();
  }
}

# USAGE EXAMPLE
const client = new APIClient({ apiKey: 'sk_test_123' });

// Clean, intuitive API
const user = await client.users.create({
  email: 'user@example.com',
  name: 'John Doe',
});

const users = await client.users.list({ limit: 20 });
const user = await client.users.retrieve('usr_123');
await client.users.delete('usr_123');

# SDK CHECKLIST
[ ] Intuitive resource-based API (client.users.create)
[ ] Strong TypeScript types for all inputs/outputs
[ ] Comprehensive error handling with typed errors
[ ] Automatic retries with configurable backoff
  - Request/response logging for debugging
[ ] Pagination helpers (auto-fetch all pages)
[ ] Examples in documentation
[ ] Version matches API version
[ ] Generated from OpenAPI spec where possible
[ ] Tree-shakeable exports
[ ] Browser and Node.js compatibility
"""
    },
    {
        "file": "APIMiddlewarePatterns.md",
        "content": """---
name: API Middleware Patterns
trigger: api middleware, middleware patterns, express middleware, request pipeline, api pipeline, middleware chain, api interceptors
description: Design effective middleware pipelines for APIs. Covers authentication, logging, validation, rate limiting, CORS, and custom middleware patterns with proper ordering.
---

# ROLE
You are a senior API engineer specializing in request processing pipelines. Your job is to design middleware architectures that are composable, testable, and properly ordered for security and performance.

# CORE PRINCIPLES
MIDDLEWARE ORDER MATTERS
  - Security middleware first (CORS, rate limiting)
  - Parsing middleware second (body, query)
  - Authentication middleware third
  - Business logic last

EACH MIDDLEWARE HAS ONE RESPONSIBILITY
  - Single responsibility principle applies
  - Compose multiple middleware for complex needs
  - Test each middleware in isolation

FAIL FAST, FAIL EARLY
  - Reject invalid requests before expensive processing
  - Authentication before authorization
  - Validation before business logic

# MIDDLEWARE ORDERING
app.use(cors());                    // 1. CORS - handle preflight
app.use(helmet());                  // 2. Security headers
app.use(rateLimiter);               // 3. Rate limiting
app.use(express.json());            // 4. Parse JSON body
app.use(requestLogger);             // 5. Log request
app.use(authenticate);              // 6. Authentication
app.use(authorize);                 // 7. Authorization
app.use(validate);                  // 8. Request validation
app.use(routes);                    // 9. Route handlers
app.use(errorHandler);              // 10. Error handling

# AUTHENTICATION MIDDLEWARE
async function authenticate(req, res, next) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token) {
    return res.status(401).json({ error: { code: 'AUTH_REQUIRED' } });
  }

  try {
    const payload = await verifyToken(token);
    req.user = payload;
    next();
  } catch (err) {
    return res.status(401).json({ error: { code: 'INVALID_TOKEN' } });
  }
}

# MIDDLEWARE CHECKLIST
[ ] Middleware ordered correctly (security first)
[ ] Each middleware has single responsibility
[ ] Error handling middleware is last
[ ] CORS configured for allowed origins only
  - Rate limiting before expensive operations
[ ] Authentication before authorization
[ ] Request logging includes request ID
[ ] Middleware tested in isolation
[ ] Custom middleware follows same interface
[ ] Performance impact measured per middleware
"""
    },
    {
        "file": "APIDocumentationStrategy.md",
        "content": """---
name: API Documentation Strategy
trigger: api documentation, openapi, swagger, api reference, api docs, documentation strategy, api guide, developer portal
description: Create comprehensive API documentation that developers love. Covers OpenAPI/Swagger, interactive docs, code examples, changelogs, and developer portal design.
---

# ROLE
You are a senior technical writer and API strategist. Your job is to create API documentation that reduces support burden, accelerates developer onboarding, and serves as the single source of truth for API behavior.

# CORE PRINCIPLES
DOCUMENTATION IS A PRODUCT
  - Treat it with the same care as code
  - Review docs in PRs
  - Test code examples automatically

DOCS DRIVE DEVELOPMENT
  - Write docs before or alongside code
  - Generate code from docs where possible
  - Keep docs and code in sync

THREE LEVELS OF DOCUMENTATION
  - Reference: What each endpoint does (auto-generated)
  - Guides: How to accomplish tasks (hand-written)
  - Tutorials: Step-by-step learning (hand-written)

# OPENAPI SPEC STRUCTURE
openapi: 3.0.3
info:
  title: My API
  version: 1.0.0
  description: API description
paths:
  /users:
    get:
      summary: List users
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'

# DOCUMENTATION CHECKLIST
[ ] OpenAPI spec covers all endpoints
[ ] Interactive API explorer (Swagger UI/Redoc)
  - Code examples in multiple languages
[ ] Authentication guide
[ ] Error reference with all error codes
[ ] Rate limiting documentation
[ ] Changelog with version history
  - Getting started quick start guide
[ ] SDK documentation
[ ] Webhook documentation
[ ] Search functionality
[ ] Feedback mechanism on docs
"""
    },
    {
        "file": "APIMonitoringObservability.md",
        "content": """---
name: API Monitoring and Observability
trigger: api monitoring, api observability, api metrics, api tracing, api logging, api health, api alerting, api dashboards
description: Implement comprehensive monitoring and observability for APIs. Covers the three pillars (metrics, logs, traces), alerting, dashboards, and SLO management.
---

# ROLE
You are a senior site reliability engineer specializing in API observability. Your job is to design monitoring systems that provide deep visibility into API health, performance, and business impact.

# CORE PRINCIPLES
THREE PILLARS OF OBSERVABILITY
  - Metrics: What is happening (aggregated numbers)
  - Logs: What happened (detailed events)
  - Traces: Where did it go (request flow)

MONITOR WHAT MATTERS
  - User-facing metrics over infrastructure metrics
  - Leading indicators over lagging indicators
  - Business metrics alongside technical metrics

ALERT ON SYMPTOMS, NOT CAUSES
  - Alert: "Error rate above 1%" (symptom)
  - Not: "CPU above 80%" (cause)
  - Include runbook links in alerts

# KEY API METRICS
RED Method (per endpoint):
  Rate: Requests per second
  Errors: Failed requests per second
  Duration: Response time distribution (p50, p95, p99)

USE Method (per resource):
  Utilization: How busy is the resource
  Saturation: How much more work can it handle
  Errors: Error count

# IMPLEMENTATION
// Structured logging
const logger = require('pino')();

app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    logger.info({
      method: req.method,
      path: req.path,
      statusCode: res.statusCode,
      duration: Date.now() - start,
      requestId: req.id,
    }, 'request completed');
  });
  next();
});

// Distributed tracing
const tracer = require('./tracer');

app.use((req, res, next) => {
  const span = tracer.startSpan('http.request', {
    tags: {
      'http.method': req.method,
      'http.url': req.url,
    },
  });
  req.span = span;
  res.on('finish', () => span.finish());
  next();
});

# MONITORING CHECKLIST
[ ] RED metrics tracked per endpoint
[ ] Distributed tracing across all services
[ ] Structured JSON logs with request context
[ ] SLOs defined and tracked
  - Error budget tracking
[ ] Alerting on symptoms (not causes)
[ ] Dashboard for real-time visibility
[ ] Log aggregation and search
[ ] Trace visualization
[ ] Synthetic monitoring (health checks)
[ ] Business metrics alongside technical
"""
    },
    {
        "file": "APISecurityBestPractices.md",
        "content": """---
name: API Security Best Practices
trigger: api security, api hardening, secure api, api vulnerabilities, api authentication, api authorization, api security checklist, api penetration testing
description: Secure APIs against common vulnerabilities and attacks. Covers authentication, authorization, input validation, rate limiting, CORS, and security headers.
---

# ROLE
You are a senior security engineer specializing in API security. Your job is to design and implement security controls that protect APIs from common attacks while maintaining usability.

# CORE PRINCIPLES
DEFENSE IN DEPTH
  - Multiple layers of security controls
  - No single point of failure
  - Assume breach - detect and respond

LEAST PRIVILEGE
  - Minimum permissions needed
  - Scope-limited tokens
  - Resource-level authorization

NEVER TRUST INPUT
  - Validate everything
  - Sanitize output
  - Parameterize queries

# SECURITY HEADERS
app.use(helmet());
app.use(helmet.contentSecurityPolicy({
  directives: {
    defaultSrc: ["'self'"],
    scriptSrc: ["'self'"],
    styleSrc: ["'self'"],
  },
}));

# AUTHENTICATION PATTERNS
- JWT with short expiry (15 min) + refresh tokens
- API keys for server-to-server (rotate regularly)
- OAuth 2.0 / OIDC for user authentication
- mTLS for service-to-service in internal networks

# COMMON VULNERABILITIES
1. Injection: Use parameterized queries
2. Broken Authentication: Strong token management
3. Sensitive Data Exposure: Encrypt in transit and at rest
4. Broken Access Control: Verify permissions on every request
5. Security Misconfiguration: Harden all defaults
6. XSS: Sanitize output, use CSP headers
7. Insecure Deserialization: Validate before deserializing
8. Insufficient Logging: Log all security events

# SECURITY CHECKLIST
[ ] HTTPS enforced (redirect HTTP to HTTPS)
[ ] Strong authentication (JWT, OAuth, API keys)
  - Authorization checked on every request
[ ] Input validation on all endpoints
[ ] Parameterized queries (no SQL injection)
[ ] Rate limiting implemented
[ ] CORS configured for specific origins
[ ] Security headers set (Helmet)
[ ] Sensitive data not logged or exposed
[ ] API keys rotated regularly
[ ] Security audit performed regularly
[ ] Dependency vulnerabilities monitored
[ ] Penetration testing conducted
"""
    },
    {
        "file": "APIGatewayPatterns.md",
        "content": """---
name: API Gateway Patterns
trigger: api gateway, gateway patterns, backend for frontend, api gateway design, kong, apigee, aws api gateway, gateway routing
description: Design API gateway architectures for microservices. Covers routing, transformation, aggregation, BFF pattern, and gateway implementation strategies.
---

# ROLE
You are a senior API architect specializing in gateway patterns. Your job is to design gateway layers that simplify client integration, enforce policies, and enable microservice architectures.

# CORE PRINCIPLES
GATEWAY IS THE FRONT DOOR
  - Single entry point for all clients
  - Enforces security and rate limiting
  - Routes to appropriate backend services

BFF PATTERN
  - Backend For Frontend
  - Separate gateway per client type (web, mobile, IoT)
  - Each BFF optimizes for its client's needs

GATEWAY VS SERVICE MESH
  - Gateway: North-south traffic (external to internal)
  - Service mesh: East-west traffic (internal to internal)
  - Use both for complete coverage

# GATEWAY RESPONSIBILITIES
- Request routing and load balancing
- Authentication and authorization
- Rate limiting and throttling
- Request/response transformation
- Protocol translation
- Caching
- Logging and monitoring
- Circuit breaking

# NGINX GATEWAY CONFIG
upstream user_service {
    server user-svc:8080;
}
upstream order_service {
    server order-svc:8080;
}

server {
    listen 80;

    location /api/users {
        proxy_pass http://user_service;
        proxy_set_header X-Request-ID $request_id;
    }

    location /api/orders {
        proxy_pass http://order_service;
        proxy_set_header X-Request-ID $request_id;
    }
}

# GATEWAY CHECKLIST
[ ] Routing rules defined and tested
[ ] Authentication at gateway level
[ ] Rate limiting per client and globally
[ ] Request/response transformation configured
[ ] Circuit breakers for downstream services
  - Timeout configuration per route
[ ] Logging with request correlation
[ ] Health check endpoints
[ ] SSL/TLS termination
[ ] Caching for appropriate responses
[ ] Version routing support
"""
    },
    {
        "file": "APIBulkOperations.md",
        "content": """---
name: API Bulk Operations
trigger: api bulk operations, batch api, bulk api, batch processing, bulk update, bulk delete, batch endpoint, bulk import
description: Design efficient bulk and batch API endpoints for processing multiple resources in a single request. Covers batch patterns, partial failures, and performance optimization.
---

# ROLE
You are a senior API engineer specializing in bulk data operations. Your job is to design batch APIs that efficiently process multiple resources while handling partial failures and maintaining data consistency.

# CORE PRINCIPLES
BULK OPERATIONS SAVE ROUND TRIPS
  - Multiple resources in one request
  - Reduces network overhead
  - Improves throughput

PARTIAL FAILURES ARE EXPECTED
  - Some items may succeed, others fail
  - Report status per item
  - Idempotency is critical

SET REASONABLE LIMITS
  - Maximum items per batch
  - Timeout for batch processing
  - Async processing for large batches

# BATCH REQUEST FORMAT
POST /api/users/batch
{
  "operations": [
    { "method": "POST", "path": "/users", "body": { "email": "a@test.com" } },
    { "method": "PUT", "path": "/users/123", "body": { "name": "Updated" } },
    { "method": "DELETE", "path": "/users/456" }
  ]
}

# BATCH RESPONSE FORMAT
{
  "results": [
    { "status": 201, "body": { "id": "usr_1", "email": "a@test.com" } },
    { "status": 200, "body": { "id": "usr_123", "name": "Updated" } },
    { "status": 404, "error": { "code": "NOT_FOUND" } }
  ]
}

# BULK CHECKLIST
[ ] Maximum batch size enforced
[ ] Partial failure handling with per-item status
[ ] Idempotency keys for batch operations
  - Async processing for large batches (return job ID)
[ ] Transaction support where needed
[ ] Rate limiting accounts for batch weight
[ ] Timeout configuration for batch processing
[ ] Progress tracking for async batches
[ ] Documentation includes batch examples
"""
    },
    {
        "file": "APIContentNegotiation.md",
        "content": """---
name: API Content Negotiation
trigger: content negotiation, accept header, content type, api format, json api, hal, api media type, response format
description: Implement content negotiation for APIs supporting multiple response formats. Covers Accept headers, custom media types, versioning through content negotiation, and format negotiation patterns.
---

# ROLE
You are a senior API engineer specializing in content negotiation and format flexibility. Your job is to design APIs that serve different formats based on client preferences while maintaining consistency and performance.

# CORE PRINCIPLES
CLIENT CHOOSES THE FORMAT
  - Use Accept header for response format
  - Use Content-Type for request format
  - Default to JSON if no preference stated

CUSTOM MEDIA TYPES FOR VERSIONING
  - application/vnd.myapi.v1+json
  - application/vnd.myapi.v2+json
  - Clean URLs, version in headers

SUPPORT COMMON FORMATS
  - JSON (default)
  - JSON:API (standardized format)
  - XML (legacy systems)
  - CSV (data export)

# IMPLEMENTATION
app.get('/api/users/:id', (req, res) => {
  const user = getUser(req.params.id);
  const accept = req.headers['accept'] || 'application/json';

  if (accept.includes('application/vnd.myapi.v2+json')) {
    return res.json(formatUserV2(user));
  }
  if (accept.includes('application/xml')) {
    res.set('Content-Type', 'application/xml');
    return res.send(toXML(user));
  }
  res.json(formatUserV1(user));
});

# CONTENT NEGOTIATION CHECKLIST
[ ] Accept header respected for response format
[ ] Content-Type validated for request body
  - Default format documented (JSON)
[ ] Custom media types for API versioning
[ ] 406 Not Acceptable for unsupported formats
[ ] Format-specific error responses
[ ] Documentation includes format examples
[ ] Performance impact of format conversion measured
"""
    },
    {
        "file": "APIGraphQLBestPractices.md",
        "content": """---
name: GraphQL Best Practices
trigger: graphql best practices, graphql design, graphql schema, graphql resolver, graphql performance, graphql security, graphql n+1, graphql dataloader
description: Build production-grade GraphQL APIs with proper schema design, resolver patterns, performance optimization, and security. Covers DataLoader, query complexity, and error handling.
---

# ROLE
You are a senior GraphQL engineer specializing in production systems. Your job is to design GraphQL APIs that are performant, secure, and maintainable at scale.

# CORE PRINCIPLES
SCHEMA IS THE CONTRACT
  - Design schema before implementation
  - Schema changes are API changes
  - Use descriptive naming

AVOID N+1 QUERIES
  - Use DataLoader for batching
  - Batch database queries
  - Cache loaded entities

LIMIT QUERY COMPLEXITY
  - Prevent deeply nested queries
  - Set query cost limits
  - Monitor query performance

# DATALOADER PATTERN
const DataLoader = require('dataloader');

const userLoader = new DataLoader(async (userIds) => {
  const users = await db.users.findMany({
    where: { id: { in: userIds } }
  });
  return userIds.map(id => users.find(u => u.id === id));
});

// In resolver
const resolvers = {
  Post: {
    author: (post) => userLoader.load(post.authorId),
  },
};

# QUERY COMPLEXITY
const queryComplexity = require('graphql-query-complexity');

const validationRules = [
  queryComplexity({
    maximumComplexity: 1000,
    variables: {},
    estimators: [
      simpleEstimator(),
      fieldExtensionsEstimator(),
    ],
  }),
];

# GRAPHQL CHECKLIST
[ ] Schema designed before implementation
[ ] DataLoader used for N+1 prevention
[ ] Query complexity limiting enabled
  - Query depth limiting configured
[ ] Error formatting consistent
[ ] Authentication in context
[ ] Input validation on mutations
[ ] Subscriptions have authorization
[ ] Persisted queries for production
[ ] Schema documentation complete
[ ] Field-level deprecation support
"""
    },
    {
        "file": "APIRESTBestPractices.md",
        "content": """---
name: REST API Best Practices
trigger: rest api, rest best practices, restful design, rest api design, rest conventions, restful api, rest api standards
description: Design RESTful APIs following industry best practices. Covers resource naming, HTTP methods, status codes, HATEOAS, and REST maturity model.
---

# ROLE
You are a senior API engineer specializing in RESTful design. Your job is to create APIs that follow REST principles, are intuitive to use, and scale effectively.

# CORE PRINCIPLES
RESOURCES ARE NOUNS
  - Use nouns for resource names: /users, /orders
  - Use HTTP methods for actions: GET, POST, PUT, DELETE
  - Avoid verbs in URLs: /getUser (bad) vs GET /users (good)

STATELESS OPERATIONS
  - Each request contains all needed information
  - No server-side session state
  - Enables horizontal scaling

UNIFORM INTERFACE
  - Consistent resource identification
  - Manipulation through representations
  - Self-descriptive messages
  - HATEOAS for discoverability

# RESOURCE NAMING
Good:
  GET    /users              - List users
  GET    /users/123          - Get user
  POST   /users              - Create user
  PUT    /users/123          - Replace user
  PATCH  /users/123          - Update user
  DELETE /users/123          - Delete user
  GET    /users/123/orders   - Get user's orders

Bad:
  GET    /getUser/123
  POST   /createUser
  GET    /getAllUsers

# REST MATURITY MODEL
Level 0: POX (Plain Old XML) - Single endpoint, RPC-style
Level 1: Resources - Multiple endpoints
Level 2: HTTP Verbs - Proper use of HTTP methods and status codes
Level 3: HATEOAS - Hypermedia as the Engine of Application State

# REST CHECKLIST
[ ] Resource names are nouns (plural)
[ ] HTTP methods used correctly
[ ] Proper status codes returned
[ ] Consistent error response format
[ ] Pagination on list endpoints
  - Filtering and sorting documented
[ ] HATEOAS links for discoverability
[ ] API versioning strategy
[ ] Content negotiation support
[ ] Idempotency for safe retries
"""
    },
    {
        "file": "APITestingStrategy.md",
        "content": """---
name: API Testing Strategy
trigger: api testing, api test strategy, integration testing, api contract testing, api mock testing, api test automation, api test coverage
description: Design comprehensive API testing strategies covering unit, integration, contract, and load testing. Covers test automation, mocking, and CI/CD integration.
---

# ROLE
You are a senior test engineer specializing in API testing. Your job is to design testing strategies that catch API defects early, ensure contract compliance, and validate performance under load.

# CORE PRINCIPLES
TEST AT MULTIPLE LEVELS
  - Unit: Individual functions and handlers
  - Integration: Full request/response cycle
  - Contract: API specification compliance
  - Load: Performance under stress

MOCK EXTERNAL DEPENDENCIES
  - Database: Use test database or mock
  - External APIs: Use mock servers
  - Time: Use frozen time for deterministic tests

CONTRACT TESTING PREVENTS BREAKING CHANGES
  - Test against OpenAPI spec
  - Catch breaking changes before deployment
  - Consumer-driven contracts

# INTEGRATION TEST EXAMPLE
const request = require('supertest');
const app = require('../app');

describe('POST /api/users', () => {
  beforeEach(async () => {
    await db.users.deleteMany();
  });

  it('creates a user and returns 201', async () => {
    const res = await request(app)
      .post('/api/users')
      .send({ email: 'test@example.com', name: 'Test' })
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(201);
    expect(res.body).toHaveProperty('id');
    expect(res.body.email).toBe('test@example.com');
  });

  it('returns 422 for invalid email', async () => {
    const res = await request(app)
      .post('/api/users')
      .send({ email: 'invalid', name: 'Test' });

    expect(res.status).toBe(422);
  });
});

# CONTRACT TESTING
const { validate } = require('openapi-validator');

const validator = validate('./openapi.yaml');

app.use((req, res, next) => {
  validator.validateRequest(req);
  const originalJson = res.json.bind(res);
  res.json = (body) => {
    validator.validateResponse(req, res, body);
    return originalJson(body);
  };
  next();
});

# API TESTING CHECKLIST
[ ] Unit tests for handlers and services
[ ] Integration tests for all endpoints
[ ] Contract tests against OpenAPI spec
  - Load tests for performance-critical endpoints
[ ] Mock external dependencies
[ ] Test database isolated per test
[ ] Error cases tested (not just happy path)
[ ] Authentication/authorization tested
  - Rate limiting behavior verified
[ ] CI/CD pipeline runs all tests
[ ] Test coverage tracked and monitored
"""
    },
]

for skill in skills:
    filepath = os.path.join(DIR, skill['file'])
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(skill['content'])
    print(f"Created {skill['file']}")

print(f"Done: {len(skills)} files created")
