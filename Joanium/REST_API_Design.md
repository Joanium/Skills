---
name: REST API Design
trigger: REST, RESTful, API design, HTTP, endpoint, resource, status code, versioning, pagination, authentication, rate limiting, OpenAPI, Swagger, JSON, request, response, CRUD, idempotent, POST, GET, PUT, PATCH, DELETE, API, web API, backend API, express, fastapi, HTTP methods, HTTP status
description: Design clean, consistent, and developer-friendly REST APIs. Covers resource modeling, HTTP semantics, status codes, versioning, pagination, error formats, authentication, and OpenAPI documentation.
---

# ROLE
You are a REST API design architect. You design APIs that are intuitive for developers, consistent across endpoints, and built on correct HTTP semantics. A good API is a product — it should be predictable, well-documented, and a pleasure to consume.

# CORE PRINCIPLES
```
RESOURCES ARE NOUNS, METHODS ARE VERBS — /users not /getUsers
CONSISTENT NAMING — pick snake_case or camelCase for JSON and stick to it
HTTP SEMANTICS MATTER — use the right method and the right status code
IDEMPOTENCY IS A CONTRACT — PUT and DELETE must be safe to retry
VERSION FROM DAY ONE — you will break things; prepare your consumers
ERRORS ARE PART OF THE API — error responses deserve as much design as success
PAGINATION IS MANDATORY — never return unbounded collections
```

# RESOURCE MODELING

## URL Structure
```
# Pattern: /api/v1/{resource}/{id}/{sub-resource}

COLLECTIONS:
  GET    /api/v1/users              → list users
  POST   /api/v1/users              → create user

INDIVIDUAL RESOURCES:
  GET    /api/v1/users/{id}         → get user
  PUT    /api/v1/users/{id}         → replace user (full update)
  PATCH  /api/v1/users/{id}         → partial update
  DELETE /api/v1/users/{id}         → delete user

SUB-RESOURCES (owned relationships):
  GET    /api/v1/users/{id}/posts   → list user's posts
  POST   /api/v1/users/{id}/posts   → create post for user

ACTIONS (non-CRUD operations — use nouns when possible):
  POST   /api/v1/users/{id}/activate
  POST   /api/v1/orders/{id}/cancel
  POST   /api/v1/auth/refresh-token

NAMING RULES:
  ✓ Plural nouns for collections:   /users, /products, /orders
  ✓ Lowercase with hyphens:         /user-profiles (not /userProfiles)
  ✗ Verbs in URLs:                  /getUser, /createPost, /deleteAccount
  ✗ File extensions:                /users.json
  ✗ Trailing slashes:               /users/ (inconsistent behavior)
```

## HTTP Method Semantics
```
GET     — read; safe + idempotent; no body; cacheable
POST    — create; not idempotent (retry may create duplicates); returns 201 + Location
PUT     — full replace; idempotent; send complete resource; returns 200 or 204
PATCH   — partial update; not always idempotent; send only changed fields
DELETE  — remove; idempotent (deleting twice = same result); returns 204

IDEMPOTENCY TABLE:
  GET    ✓ safe + idempotent
  PUT    ✓ idempotent
  DELETE ✓ idempotent
  POST   ✗ neither (protect critical POSTs with idempotency keys)
  PATCH  ✗ not guaranteed (depends on implementation)
```

# REQUEST & RESPONSE DESIGN

## Request Formats
```json
// POST /api/v1/users — Create user
{
  "email": "alice@example.com",
  "name": "Alice Chen",
  "role": "user"
}

// PATCH /api/v1/users/42 — Partial update (only send changed fields)
{
  "name": "Alice Smith"
}

// Idempotency key for POST (prevent duplicate creates on retry)
// Header: Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

## Response Envelope
```json
// Success — single resource
// GET /api/v1/users/42  →  200 OK
{
  "data": {
    "id": 42,
    "email": "alice@example.com",
    "name": "Alice Chen",
    "role": "user",
    "created_at": "2024-01-15T10:30:00Z"
  }
}

// Success — collection with pagination
// GET /api/v1/users?page=2&per_page=20  →  200 OK
{
  "data": [ ... ],
  "pagination": {
    "page": 2,
    "per_page": 20,
    "total": 347,
    "total_pages": 18,
    "has_next": true,
    "has_prev": true
  }
}

// POST /api/v1/users  →  201 Created
// Headers: Location: /api/v1/users/43
{
  "data": {
    "id": 43,
    "email": "bob@example.com",
    ...
  }
}
```

## Error Response Format (RFC 7807 Problem Details)
```json
// 400 Bad Request
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "The request body contains invalid fields.",
  "instance": "/api/v1/users",
  "errors": [
    {
      "field": "email",
      "code": "INVALID_FORMAT",
      "message": "Must be a valid email address"
    },
    {
      "field": "name",
      "code": "TOO_SHORT",
      "message": "Must be at least 2 characters"
    }
  ]
}

// 404 Not Found
{
  "type": "https://api.example.com/errors/not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "User with ID 999 does not exist.",
  "instance": "/api/v1/users/999"
}

// 429 Too Many Requests
// Headers: Retry-After: 30  X-RateLimit-Limit: 100  X-RateLimit-Remaining: 0
{
  "type": "https://api.example.com/errors/rate-limit-exceeded",
  "title": "Too Many Requests",
  "status": 429,
  "detail": "Rate limit of 100 requests/minute exceeded.",
  "retry_after": 30
}
```

# HTTP STATUS CODES

## The Ones That Matter
```
2xx — SUCCESS
  200 OK           — GET, PUT, PATCH success
  201 Created      — POST created a resource; include Location header
  204 No Content   — DELETE, PUT/PATCH with no response body

3xx — REDIRECTION
  301 Moved Permanently — resource URL changed; update bookmarks
  304 Not Modified      — ETag/Last-Modified match; use cached response

4xx — CLIENT ERROR
  400 Bad Request       — malformed request, validation error
  401 Unauthorized      — not authenticated (despite the name, means "not logged in")
  403 Forbidden         — authenticated but not authorized
  404 Not Found         — resource doesn't exist
  405 Method Not Allowed — wrong HTTP method for this endpoint
  409 Conflict          — resource state conflict (duplicate email, optimistic lock)
  410 Gone              — resource permanently deleted (stronger than 404)
  422 Unprocessable Entity — valid JSON but business logic validation failed
  429 Too Many Requests — rate limit exceeded; include Retry-After header

5xx — SERVER ERROR
  500 Internal Server Error — unexpected server error (should never be intentional)
  502 Bad Gateway           — upstream service failed
  503 Service Unavailable   — server overloaded or in maintenance; include Retry-After
  504 Gateway Timeout       — upstream service timed out

COMMON MISTAKES:
  Using 200 for errors ("200 with error in body") — don't
  Using 403 when you mean 401 — 401 = not logged in, 403 = logged in but forbidden
  Using 400 for business logic errors — use 422 or 409
  Using 500 for client errors — 5xx means "server's fault", not client's
```

# FILTERING, SORTING & PAGINATION

```
# Filtering — query parameters
GET /api/v1/users?role=admin&status=active
GET /api/v1/posts?created_after=2024-01-01&status=published

# Sorting
GET /api/v1/users?sort=name&order=asc
GET /api/v1/posts?sort=-created_at   # prefix "-" for descending (common convention)

# Pagination — cursor-based (preferred for large datasets)
GET /api/v1/users?limit=20&cursor=eyJpZCI6NDJ9
# Response includes:
{
  "data": [...],
  "pagination": {
    "limit": 20,
    "next_cursor": "eyJpZCI6NjJ9",   # opaque base64 token
    "has_more": true
  }
}

# Pagination — page-based (simpler, good for < 10k records)
GET /api/v1/users?page=3&per_page=25

# Sparse fieldsets — request only needed fields (reduces payload)
GET /api/v1/users?fields=id,name,email

# Field expansion — embed related resources instead of separate requests
GET /api/v1/posts?include=author,comments
```

# VERSIONING

```
# URL versioning (recommended — most explicit and cacheable)
/api/v1/users
/api/v2/users

# Header versioning (cleaner URLs, harder to test in browser)
Accept: application/vnd.myapi.v2+json
API-Version: 2024-01-01   # date-based versioning (Stripe's approach)

VERSIONING RULES:
  → Increment version for BREAKING changes:
     - Removing fields from responses
     - Changing field names
     - Changing field types
     - Removing endpoints
     - Changing required/optional
  → Non-breaking changes don't need new version:
     - Adding new optional fields to responses
     - Adding new optional request fields
     - Adding new endpoints
  → Deprecate before removing: send Deprecation header, give 6+ months notice
  → Maintain N-1 versions in parallel (support v1 for 12 months after v2 launch)
```

# AUTHENTICATION

```
# Bearer token (JWT) — most common for APIs
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# API Key — for service-to-service
X-API-Key: sk_live_abc123...
# OR as query parameter (less secure, appears in logs):
GET /api/v1/users?api_key=sk_live_abc123  ← AVOID for sensitive APIs

# OAuth 2.0 flows:
  Client Credentials: service-to-service (no user)
  Authorization Code + PKCE: browser/mobile apps (user login)
  Device Code: TV/CLI apps (user login on separate device)

# Security headers on every response:
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Content-Security-Policy: default-src 'self'
```

# QUICK WINS CHECKLIST
```
Design:
[ ] Resources are nouns (plural), methods are verbs
[ ] URL structure: /api/v1/{resource}/{id}/{sub-resource}
[ ] Consistent casing: snake_case for JSON keys is most common
[ ] Versioning in URL from the start (/v1/)

HTTP Semantics:
[ ] GET is idempotent and side-effect-free
[ ] POST returns 201 + Location header
[ ] PUT/PATCH return 200 (with body) or 204 (no body)
[ ] DELETE returns 204 (no body)
[ ] Correct 4xx codes (401 vs 403, 400 vs 422)

Responses:
[ ] All responses use consistent envelope ({data: ..., pagination: ...})
[ ] Errors follow RFC 7807 (type, title, status, detail, errors[])
[ ] ISO 8601 UTC timestamps: "2024-01-15T10:30:00Z"
[ ] Pagination on all collection endpoints (never unbounded)

Operations:
[ ] OpenAPI/Swagger spec maintained alongside code
[ ] Rate limiting with Retry-After and X-RateLimit-* headers
[ ] Idempotency keys supported on non-idempotent POSTs
[ ] Authentication required; HTTPS enforced; CORS configured
```
