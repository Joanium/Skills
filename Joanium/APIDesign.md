---
name: API Design
trigger: API design, REST API, GraphQL, endpoints, routes, HTTP methods, API contract, OpenAPI, swagger, request response, versioning, API spec, route planning, CRUD endpoints
description: Fourth skill in the build pipeline. Read after Database Design. Covers RESTful API design principles, endpoint naming, HTTP semantics, request/response shapes, versioning, and producing an OpenAPI spec before implementation.
prev_skill: 03-DatabaseDesign.md
next_skill: 05-FrontendArchitecture.md
---

# ROLE
You are an API designer who understands that your API is a public contract — once consumed, breaking it is expensive. You design APIs that are intuitive, consistent, and evolvable. Your goal is that a developer can look at your URL and method and immediately know what it does.

# CORE PRINCIPLES
```
YOUR API IS A CONTRACT — breaking it breaks your consumers
RESOURCE-ORIENTED URLS — nouns, not verbs (/videos not /getVideos)
HTTP METHODS CARRY MEANING — GET=read, POST=create, PUT=replace, PATCH=update, DELETE=remove
RETURN CONSISTENT SHAPES — success and error envelopes look the same everywhere
VERSION FROM DAY ONE — /api/v1/ is easier than retrofitting versioning later
PAGINATION IS NOT OPTIONAL — never return unbounded lists
DESIGN THE HAPPY PATH, THEN EVERY ERROR — errors are half your API surface
```

# STEP 1 — REST RESOURCE MAPPING

```
RULE: Map each database entity to a REST resource.
      Nested resources for owned sub-resources (max 2 levels deep).

RESOURCE TABLE:
  Resource        Base URL                    Notes
  ─────────────   ─────────────────────────   ───────────────────────────
  Users           /api/v1/users               Registration, profile
  Auth            /api/v1/auth                Sessions, tokens
  Channels        /api/v1/channels            Public channel pages
  Videos          /api/v1/videos              Video CRUD and discovery
  Comments        /api/v1/videos/:id/comments Owned by video
  Subscriptions   /api/v1/subscriptions       Current user's subscriptions
  Likes           /api/v1/videos/:id/like     Toggle like (POST/DELETE)
  Tags            /api/v1/tags                Tag lookup
  Search          /api/v1/search              Cross-resource search
  Upload          /api/v1/upload              Multipart / presigned URL flow
  Me              /api/v1/me                  Shorthand for current user

NESTING RULE:
  ✅ /api/v1/videos/:videoId/comments     — comments belong to a video
  ✅ /api/v1/channels/:channelId/videos   — videos belong to a channel
  ❌ /api/v1/users/:userId/channels/:channelId/videos/:videoId/comments
     → Too deep. Flatten after 2 levels: /api/v1/comments/:commentId
```

# STEP 2 — ENDPOINT DEFINITIONS

```
FORMAT FOR EACH ENDPOINT:
  METHOD  /path
  Auth:   required | optional | none
  Params: query params, path params, body fields
  Returns: response shape
  Errors:  list of expected error codes

EXAMPLE — Videos API:

GET /api/v1/videos
  Auth: optional (affects personalization)
  Query params:
    page         integer, default 1
    limit        integer, default 20, max 100
    channel_id   UUID, optional filter
    tag          string, optional filter
    sort         enum: latest|trending|oldest, default: latest
  Returns:
    { data: Video[], pagination: { page, limit, total, has_next } }
  Errors:
    400 Bad Request — invalid sort value
    422 Unprocessable Entity — invalid UUID format

POST /api/v1/videos
  Auth: required (creator)
  Body: { title, description, visibility, tags[] }
  Returns: 201 Created, { data: Video }
  Errors:
    400 — missing required fields
    401 — not authenticated
    403 — account suspended
    422 — validation errors (field-level)

GET /api/v1/videos/:id
  Auth: optional
  Returns: { data: Video } (includes channel, tags)
  Errors:
    404 — video not found or not visible to caller

PATCH /api/v1/videos/:id
  Auth: required (must be video owner)
  Body: partial { title?, description?, visibility?, tags[]? }
  Returns: { data: Video }
  Errors:
    401 — not authenticated
    403 — not the owner
    404 — video not found

DELETE /api/v1/videos/:id
  Auth: required (owner or admin)
  Returns: 204 No Content
  Errors:
    401, 403, 404

POST /api/v1/videos/:id/like
  Auth: required
  Returns: 200, { liked: true, like_count: 1042 }

DELETE /api/v1/videos/:id/like
  Auth: required
  Returns: 200, { liked: false, like_count: 1041 }

POST /api/v1/auth/register
  Auth: none
  Body: { email, username, password }
  Returns: 201, { data: User, token: string }
  Errors:
    409 — email or username already taken
    422 — password too weak, invalid email

POST /api/v1/auth/login
  Auth: none
  Body: { email, password }
  Returns: 200, { data: User, token: string }
  Errors:
    401 — invalid credentials
    403 — account banned

POST /api/v1/upload/presigned
  Auth: required
  Body: { filename, content_type, size_bytes }
  Returns: { upload_url: string, storage_key: string, expires_in: 3600 }
  Notes: Client uploads directly to S3 using the presigned URL.
         After upload, client calls PATCH /videos/:id to set storage_key.
```

# STEP 3 — RESPONSE ENVELOPE STANDARD

```javascript
// ALL responses use this envelope — consistent parsing in every client

// SUCCESS:
{
  "data": <object or array>,      // the payload
  "meta": {                        // optional metadata
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 348,
      "has_next": true
    }
  }
}

// ERROR:
{
  "error": {
    "code": "VALIDATION_ERROR",    // machine-readable, stable string
    "message": "Validation failed", // human-readable, can change
    "details": [                    // optional field-level errors
      { "field": "email", "message": "Invalid email format" },
      { "field": "password", "message": "Must be at least 8 characters" }
    ]
  }
}

// ERROR CODE REGISTRY (define before implementation):
  UNAUTHORIZED          → 401 — no token or token expired
  FORBIDDEN             → 403 — authenticated but lacks permission
  NOT_FOUND             → 404 — resource doesn't exist
  CONFLICT              → 409 — duplicate (email taken, already liked)
  VALIDATION_ERROR      → 422 — input failed validation
  RATE_LIMITED          → 429 — too many requests
  INTERNAL_ERROR        → 500 — unexpected server error (don't leak details)
```

# STEP 4 — AUTHENTICATION PATTERN

```
JWT FLOW (stateless, recommended for APIs):

  Login:
    1. Client: POST /auth/login { email, password }
    2. Server: validates, returns { token, refresh_token }
    3. Client: stores token in memory, refresh_token in httpOnly cookie
    4. Client: sends Authorization: Bearer <token> with every request

  Token structure:
    { sub: userId, role: "user"|"creator"|"admin", exp: timestamp }
    Sign with HS256 (symmetric) or RS256 (asymmetric — better for microservices)

  Refresh flow:
    When access token expires (401) → send refresh_token → get new access token
    If refresh_token expired → redirect to login

  ACCESS TOKEN EXPIRY: 15 minutes (short — reduces damage if stolen)
  REFRESH TOKEN EXPIRY: 30 days (longer — invalidate on logout via DB)

MIDDLEWARE ORDER (apply in this order):
  1. cors()            — allow cross-origin from known domains
  2. helmet()          — security headers
  3. rateLimit()       — global rate limit (100 req/min per IP)
  4. authenticate()    — verify JWT, attach user to req.user
  5. authorize(role)   — check req.user.role matches required role
  6. validate(schema)  — Zod/Joi schema validation on body/params
  7. routeHandler()    — actual business logic
```

# STEP 5 — VERSIONING AND EVOLUTION

```
VERSIONING STRATEGY:
  URL versioning:    /api/v1/videos  (visible, simple, recommended)
  Header versioning: Accept: application/vnd.app.v1+json (invisible, complex)
  → Use URL versioning. It's easier to test and document.

BREAKING vs NON-BREAKING CHANGES:
  Non-breaking (OK in same version):
    ✅ Adding new optional fields to response
    ✅ Adding new optional query params
    ✅ Adding new endpoints
    ✅ Adding new enum values to fields nobody filters on

  Breaking (requires new version):
    ❌ Removing or renaming fields
    ❌ Changing field types
    ❌ Changing endpoint URL or method
    ❌ Changing required fields
    ❌ Changing error codes or envelope shape

DEPRECATION PROCESS:
  1. Add Deprecation header to old endpoint responses
  2. Document migration path to new version
  3. Keep v1 running for minimum 6 months after v2 launch
  4. Log usage of deprecated endpoints to know when it's safe to remove
```

# STEP 6 — OPENAPI SPEC SKELETON

```yaml
openapi: 3.1.0
info:
  title: VideoApp API
  version: 1.0.0
  description: API for the VideoApp platform

servers:
  - url: https://api.videoapp.com/api/v1
  - url: http://localhost:3000/api/v1

security:
  - BearerAuth: []

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    Video:
      type: object
      properties:
        id:          { type: string, format: uuid }
        title:       { type: string }
        description: { type: string, nullable: true }
        status:      { type: string, enum: [processing, ready, failed] }
        view_count:  { type: integer }
        created_at:  { type: string, format: date-time }

    Error:
      type: object
      required: [error]
      properties:
        error:
          type: object
          required: [code, message]
          properties:
            code:    { type: string }
            message: { type: string }

paths:
  /videos:
    get:
      summary: List videos
      parameters:
        - name: page
          in: query
          schema: { type: integer, default: 1 }
        - name: limit
          in: query
          schema: { type: integer, default: 20, maximum: 100 }
      responses:
        "200":
          description: Success
        "400":
          description: Bad request
```

# CHECKLIST — Before Moving to Frontend Architecture

```
✅ All MVP endpoints defined (method, URL, auth, body, response, errors)
✅ Response envelope standardized and documented
✅ Error code registry written
✅ Auth flow designed (JWT tokens, refresh, expiry)
✅ Middleware order defined
✅ Versioning strategy decided
✅ OpenAPI spec skeleton created
✅ No business logic in URL names (no /getVideosByUser — use query params)
→ NEXT: 05-FrontendArchitecture.md
```
