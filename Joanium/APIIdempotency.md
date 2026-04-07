---
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
const acquired = await redis.set(`idempotency:lock:${key}`, 1, NX, EX, 30);
if (!acquired) return res.status(409).json({ error: "Request in progress" });

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
