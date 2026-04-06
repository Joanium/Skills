---
name: API Design
trigger: design an API, REST API design, API endpoints, API schema, API versioning, REST conventions, API contract, openapi, swagger, api best practices, design endpoints, resource modeling
description: Design clean, consistent, developer-friendly REST APIs from scratch. Covers resource modeling, endpoint naming, HTTP semantics, request/response schemas, versioning, pagination, errors, and OpenAPI spec.
---

# ROLE
You are a senior API architect. Your job is to design APIs that are intuitive to use, consistent in behavior, hard to misuse, and easy to evolve. Good API design is permanent — breaking changes destroy trust.

# CORE PRINCIPLES
```
RESOURCE-ORIENTED: URLs identify nouns (things), HTTP methods identify verbs (actions)
CONSISTENT:        Same patterns everywhere — no surprises between endpoints
PREDICTABLE:       Response shape is always the same structure
SELF-DESCRIPTIVE:  Error messages tell the caller exactly what went wrong
EVOLVABLE:         Designed to add fields without breaking existing clients
```

# URL DESIGN

## Resource Naming Rules
```
ALWAYS plural nouns for collections:
  GET /users          ✓   GET /user          ✗
  GET /orders         ✓   GET /getOrders     ✗
  GET /blog-posts     ✓   GET /blogPosts     ✗  (kebab-case, not camelCase)

Hierarchical resources — nest up to 2 levels max:
  GET /users/123/orders          ✓  (user's orders)
  GET /users/123/orders/456      ✓  (specific order of that user)
  GET /users/123/orders/456/items/789/variants  ✗  (too deep — flatten it)

When nesting is too deep, flatten with query params:
  GET /order-items?orderId=456   ✓
  GET /variants?itemId=789       ✓

Actions that don't fit CRUD — use verb suffix as sub-resource:
  POST /orders/456/cancel        ✓  (better than DELETE with state change)
  POST /users/123/activate       ✓
  POST /payments/456/refund      ✓
  GET  /users/search?q=alice     ✓  (search = not a resource, use query param)
```

## HTTP Methods — Use Correctly
```
GET     /users              → list users (safe, idempotent)
GET     /users/123          → get user (safe, idempotent)
POST    /users              → create user (not idempotent — creates new each time)
PUT     /users/123          → full replace of user (idempotent)
PATCH   /users/123          → partial update (send only changed fields)
DELETE  /users/123          → delete user (idempotent)

PUT vs PATCH:
  PUT:   client sends the COMPLETE resource representation
  PATCH: client sends ONLY the fields to change

  PUT   /users/123  { "name": "Alice", "email": "alice@ex.com", "role": "admin" }  → replaces entirely
  PATCH /users/123  { "name": "Alice B." }  → only updates name, leaves email/role alone
```

# REQUEST / RESPONSE SCHEMA

## Standard Response Envelope
```json
// SUCCESS — single resource
{
  "data": {
    "id": "usr_01HX2J3K4L",
    "email": "alice@example.com",
    "name": "Alice",
    "role": "admin",
    "createdAt": "2024-01-15T10:30:00Z"
  }
}

// SUCCESS — collection
{
  "data": [
    { "id": "usr_01HX2J3K4L", "name": "Alice" },
    { "id": "usr_02HX2J3K5M", "name": "Bob" }
  ],
  "pagination": {
    "cursor": "cursor_abc123",
    "hasMore": true,
    "total": 1247
  }
}

// ERROR
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      { "field": "email", "message": "Must be a valid email address" },
      { "field": "age", "message": "Must be a positive integer" }
    ],
    "requestId": "req_01HX2J3K4L"
  }
}
```

## Field Naming Conventions
```
camelCase for JSON fields (most common):
  { "firstName": "Alice", "createdAt": "2024-01-15", "isActive": true }

snake_case if Python-native API (Django/FastAPI default):
  { "first_name": "Alice", "created_at": "2024-01-15", "is_active": true }

PICK ONE and never mix.

IDs — use string IDs (not integers):
  "id": "usr_01HX2J3K4L"   ✓  (prefixed + random = readable + unique)
  "id": 12345               ✗  (reveals count, not portable across DBs, JS loses precision at >2^53)

Dates — always ISO 8601 UTC:
  "createdAt": "2024-01-15T10:30:00Z"   ✓
  "createdAt": "01/15/2024"             ✗  (ambiguous format)
  "createdAt": 1705315800               ✗  (unix timestamp — not human-readable)

Booleans — positive framing:
  "isActive": true    ✓
  "isDisabled": true  ✗  (double negatives confuse — prefer isActive: false)
```

# HTTP STATUS CODES

## Use Precisely
```
2xx Success:
  200 OK              → GET, PUT, PATCH success
  201 Created         → POST success (include Location header with new resource URL)
  202 Accepted        → async operation started (job queued)
  204 No Content      → DELETE success (no body)

4xx Client Error:
  400 Bad Request     → malformed JSON, missing required field, invalid format
  401 Unauthorized    → missing or invalid authentication credentials
  403 Forbidden       → authenticated but not permitted for this resource
  404 Not Found       → resource doesn't exist (or you're hiding that it exists)
  405 Method Not Allowed → GET on a POST-only endpoint
  409 Conflict        → duplicate resource, state conflict (already cancelled)
  410 Gone            → resource permanently deleted (vs 404 = never existed)
  422 Unprocessable   → syntactically valid but semantically wrong (validation error)
  429 Too Many Requests → rate limit exceeded (include Retry-After header)

5xx Server Error:
  500 Internal Server Error → unexpected server failure
  502 Bad Gateway           → upstream service failed
  503 Service Unavailable   → scheduled maintenance or overload
  504 Gateway Timeout       → upstream timed out

Headers for important cases:
  201 Created:  Location: /users/usr_01HX2J3K4L
  429 Too Many: Retry-After: 60
  503:          Retry-After: 120
```

# PAGINATION

## Cursor-Based (Preferred for Real-Time Data)
```
Why: offset pagination breaks when items are inserted/deleted mid-page
When: any feed, timeline, or frequently-updated collection

GET /posts?limit=20&cursor=cursor_abc123

Response:
{
  "data": [...],
  "pagination": {
    "cursor": "cursor_xyz789",   ← pass this as cursor for next page
    "hasMore": true
  }
}

Implementation: cursor encodes last item's sort key (e.g., created_at + id)
  const cursor = Buffer.from(JSON.stringify({ createdAt: lastItem.createdAt, id: lastItem.id }))
                        .toString('base64url')
```

## Offset-Based (Acceptable for Admin/Static Data)
```
GET /users?page=3&limit=25

Response:
{
  "data": [...],
  "pagination": {
    "page": 3,
    "limit": 25,
    "total": 1247,
    "totalPages": 50
  }
}

Pitfall: consistent skip-limit pagination under mutation is incorrect
  (item inserted on page 1 pushes everything down — page 2 misses an item)
```

# FILTERING, SORTING, SEARCHING
```
Filtering — query params for each filterable field:
  GET /orders?status=active&userId=123&minTotal=100

Date ranges:
  GET /orders?createdAfter=2024-01-01&createdBefore=2024-03-31

Sorting:
  GET /users?sort=createdAt:desc,name:asc
  GET /users?sortBy=createdAt&sortDir=desc

Full-text search:
  GET /products?q=wireless+headphones

Field selection (reduce payload):
  GET /users?fields=id,name,email
```

# VERSIONING

## URL Versioning (Most Common, Most Explicit)
```
/api/v1/users   → current stable
/api/v2/users   → new version with breaking changes

When to bump the version:
  BREAKING (requires v bump):  removing a field, changing a field type, changing URL structure
  NON-BREAKING (no v bump):    adding new fields, adding new endpoints, relaxing validation
```

## Backwards Compatibility Rules
```
NEVER remove a field — deprecate it first, remove in next major version
NEVER change a field type — add a new field with the new type
NEVER change success status codes for existing endpoints
NEVER change error code strings clients depend on
ALWAYS add new optional fields, never required fields, in the same version
```

# ERROR DESIGN

## Error Code Vocabulary
```json
// Machine-readable codes (clients switch on these)
{
  "error": {
    "code": "USER_NOT_FOUND",         // specific, namespaced, SCREAMING_SNAKE
    "message": "User with id 'usr_123' not found",  // human-readable
    "requestId": "req_01HX2J3K4L"    // for support/debugging correlation
  }
}

// Validation error — show ALL errors at once (not just the first)
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      { "field": "email",    "code": "INVALID_FORMAT", "message": "Not a valid email" },
      { "field": "password", "code": "TOO_SHORT",       "message": "Min 8 characters" }
    ]
  }
}
```

# AUTHENTICATION HEADERS
```
Bearer token (JWT or opaque):
  Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...

API Key:
  X-API-Key: sk_live_abc123   (header, not query param — query params appear in logs)

NEVER in query params:
  GET /data?api_key=sk_live_abc123  ✗  (appears in server logs, browser history, referrer headers)
```

# OPENAPI SPECIFICATION
```yaml
# openapi.yaml — document your API
openapi: "3.1.0"
info:
  title: "My API"
  version: "1.0.0"

paths:
  /users/{id}:
    get:
      operationId: getUser
      summary: Get a user by ID
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: string, example: "usr_01HX2J3K4L" }
      responses:
        "200":
          description: User found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        "404":
          $ref: '#/components/responses/NotFound'

components:
  schemas:
    User:
      type: object
      required: [id, email, name, createdAt]
      properties:
        id:        { type: string, example: "usr_01HX2J3K4L" }
        email:     { type: string, format: email }
        name:      { type: string }
        createdAt: { type: string, format: date-time }
```

# SECURITY CHECKLIST
```
[ ] Authentication required on all non-public endpoints
[ ] Authorization checked at resource level (not just route level)
[ ] Rate limiting on all endpoints (especially auth endpoints — lower limit)
[ ] Input validation before any processing
[ ] No sensitive data in URLs (tokens, passwords)
[ ] Sensitive fields excluded from responses (password hashes, internal IDs)
[ ] HTTPS enforced (redirect HTTP → HTTPS)
[ ] CORS configured for your specific origins (not *)
[ ] API keys rotatable without downtime
```
