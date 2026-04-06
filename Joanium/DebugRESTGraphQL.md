---
name: Debug — REST APIs / GraphQL
trigger: api not working, rest api error, graphql error, 401, 403, 404, 429, 500, cors api, api timeout, graphql query failing, resolver error, n+1 graphql, api slow, bad request, authentication failing, jwt error, graphql mutation error
description: Hyper-specific debugging guide for REST APIs and GraphQL. Real HTTP status codes, real error patterns, real fixes. Covers auth, CORS, rate limiting, GraphQL resolvers, N+1, introspection, and API performance.
---

# Debug — REST APIs / GraphQL

---

# REST APIs

## First Move — Inspect the Full Request/Response

```bash
# curl is your best friend — shows EVERYTHING
curl -v https://api.example.com/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}'
# -v = verbose (shows request + response headers)
# Add -s to silence progress bar

# Send JSON and pretty-print response
curl -s https://api.example.com/users | jq .

# Test POST with body
curl -s -X POST https://api.example.com/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"email": "user@example.com", "name": "Alice"}' | jq .

# Follow redirects and show final URL
curl -L -v https://api.example.com/resource

# Save response headers to file for inspection
curl -D headers.txt https://api.example.com/users

# Check response time
curl -o /dev/null -s -w "total: %{time_total}s\n" https://api.example.com/users

# Test with specific TLS version (debugging TLS issues)
curl --tls-max 1.2 https://api.example.com/
```

---

## HTTP Status Code Debugging

### 400 Bad Request

```bash
# The request is malformed — read the response body for details
curl -v -X POST https://api/resource \
  -H "Content-Type: application/json" \
  -d '{"data": "value"}' 2>&1 | jq .

# Common causes:
# 1. Missing required field — check API docs for required fields
# 2. Wrong Content-Type header
curl -H "Content-Type: application/json" ...  # JSON body
curl -H "Content-Type: application/x-www-form-urlencoded" ...  # form body
curl -F "file=@path/to/file" ...  # multipart/form-data

# 3. Validation error — field type or format wrong
# 400: {"error": "email must be a valid email address"}
# Fix the value being sent, not the request structure

# 4. Body not being parsed — check Content-Type is set
# If you send JSON without Content-Type: application/json, the server won't parse it
```

### 401 Unauthorized vs 403 Forbidden

```bash
# 401 = not authenticated (no valid credentials)
# 403 = authenticated but not allowed (wrong permissions)

# Debug 401:
# 1. Check the Authorization header format
curl -v -H "Authorization: Bearer eyJ..." https://api/resource
# Common mistake: "Bearer" missing, or "Token" instead of "Bearer"

# 2. Check token expiry
# Decode a JWT (without verifying signature — just inspect)
echo "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMiLCJleHAiOjE3MDB9.sig" | \
  cut -d. -f2 | base64 -d 2>/dev/null | jq .
# Check "exp" field — is it in the past?

# 3. Check the WWW-Authenticate header in the 401 response — it tells you why
curl -v https://api/resource 2>&1 | grep "WWW-Authenticate"

# Debug 403:
# User is authenticated but lacks permission for this specific resource
# Check: is the user's role/scope correct?
# Check: is the resource owned by a different user?
# Check: has the permission been granted in your system?
```

### 404 Not Found

```bash
# Is it really "resource doesn't exist" or "route doesn't exist"?

# 1. Check the URL is correct — trailing slash matters in some frameworks
curl https://api/users     # might be different from
curl https://api/users/    # these two

# 2. Check route is registered — add a debug log or check routing table
# Express:
app._router.stack.forEach(r => r.route && console.log(r.route.path))

# 3. Check if the resource actually exists in the database
# Add a log: console.log('Looking up user:', id, '→ result:', user)

# 4. Base URL might be wrong
curl https://api.example.com/api/v1/users  # is /api/v1 the prefix?
curl https://api.example.com/v1/users      # or just /v1?
# Check your API documentation or OpenAPI spec
```

### 429 Too Many Requests

```bash
# Rate limited — check response headers for limits and reset time
curl -v https://api/resource 2>&1 | grep -i "ratelimit\|retry-after\|x-rate"
# X-RateLimit-Limit: 100
# X-RateLimit-Remaining: 0
# X-RateLimit-Reset: 1703000060  (unix timestamp when limit resets)
# Retry-After: 60  (seconds until you can retry)

# Fix in your code:
async function callWithRateLimit(fn, retries = 3) {
  for (let attempt = 0; attempt < retries; attempt++) {
    const res = await fn()
    if (res.status !== 429) return res
    const retryAfter = parseInt(res.headers.get('Retry-After') || '60')
    console.log(`Rate limited, waiting ${retryAfter}s...`)
    await new Promise(r => setTimeout(r, retryAfter * 1000))
  }
  throw new Error('Rate limit retries exhausted')
}
```

### 500 Internal Server Error

```bash
# The server crashed — check SERVER logs, not the response body
# The response body rarely has useful details in production (security)

# If you control the server — check the logs
# If you're calling a third-party API — check their status page

# Add request IDs to correlate logs
curl -H "X-Request-ID: $(uuidgen)" https://api/resource
# Server should log the request ID — makes finding the specific error trivial

# Reproduce the exact failing request
# Save the request to a file:
curl -v https://api/resource \
  -H "Content-Type: application/json" \
  -d @request.json 2>&1 | tee response.txt
```

---

## Authentication / JWT Debugging

```javascript
// Debug JWT token — decode without verification
function debugJwt(token) {
  const parts = token.split('.')
  const header = JSON.parse(Buffer.from(parts[0], 'base64url').toString())
  const payload = JSON.parse(Buffer.from(parts[1], 'base64url').toString())
  
  console.log('Header:', header)
  console.log('Payload:', payload)
  console.log('Expires:', new Date(payload.exp * 1000))
  console.log('Is expired:', Date.now() / 1000 > payload.exp)
  console.log('Issued at:', new Date(payload.iat * 1000))
}

// Common JWT errors:
// "invalid signature" → wrong secret, or token was generated with different key
// "jwt expired"       → token expired — re-issue or refresh
// "jwt malformed"     → token was corrupted or is the wrong format
// "jwt audience invalid" → aud claim doesn't match your API

// Verify JWT with correct algorithm — algorithm confusion is a security bug
import jwt from 'jsonwebtoken'
// Wrong: accepts any algorithm — RS256 JWT signed with "none" would pass
jwt.verify(token, secret)
// Right: specify allowed algorithms explicitly
jwt.verify(token, secret, { algorithms: ['HS256'] })
```

---

## API Performance Debugging

```bash
# Find where time is spent in a request
curl -o /dev/null -s -w "
  namelookup: %{time_namelookup}s
  connect:    %{time_connect}s
  appconnect: %{time_appconnect}s
  pretransfer: %{time_pretransfer}s
  redirect:   %{time_redirect}s
  starttransfer: %{time_starttransfer}s  ← time to first byte (server processing)
  total:      %{time_total}s
" https://api/resource

# High starttransfer = server is slow processing the request
# High connect = network/DNS problem
# High appconnect = TLS handshake slow (check certificate chain)
```

---

# GRAPHQL

## First Move

```bash
# Always enable introspection in development
# Check if schema is accessible
curl -X POST https://api/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { types { name } } }"}' | jq .

# Test a query directly with curl
curl -X POST https://api/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "query GetUser($id: ID!) { user(id: $id) { id name email } }",
    "variables": { "id": "123" }
  }' | jq .

# GraphQL always returns 200 OK — errors are in the response body
# Response with errors:
# {
#   "data": null,
#   "errors": [{ "message": "User not found", "locations": [...], "path": [...] }]
# }
```

---

## GraphQL Error Patterns

### `Cannot query field 'X' on type 'Y'`

```graphql
# The field doesn't exist in the schema
# Fix: check the schema definition
# In Apollo Server — view schema at /graphql with introspection
# Or: print the schema
# graphql-codegen or Apollo Studio shows the full schema

# Typo in field name — check exact spelling and case
query {
  user {
    userName  # wrong — check if it's 'username' or 'name'
    name      # correct
  }
}
```

### `Variable '$X' of required type 'Y' was not provided`

```graphql
# Variables defined in the query must be passed in the variables object
query GetUser($id: ID!) {  # $id is required (non-nullable)
  user(id: $id) { name }
}
# Fix: pass the variable
variables: { "id": "123" }

# Nullable variable — use ? to make optional
query GetUser($id: ID) {   # $id is optional
  user(id: $id) { name }
}
```

### Resolver Returns `null` Unexpectedly

```javascript
// Debug: add logging to resolvers to trace what's returned
const resolvers = {
  Query: {
    user: async (_, { id }, context) => {
      console.log('Resolver: user called with id:', id)
      console.log('Context user:', context.user)
      
      const user = await db.findUser(id)
      console.log('DB returned:', user)
      
      return user  // if this is null, GraphQL field returns null
    }
  }
}

// Common cause: context.user is null (auth middleware not running)
// Check: is auth middleware applied to the GraphQL route?
// Check: is the Authorization header being sent?

// Common cause: wrong field name in resolver vs schema
const resolvers = {
  User: {
    fullName: (user) => `${user.first_name} ${user.last_name}`
    // Schema might define it as 'fullname' not 'fullName'
  }
}
```

---

## N+1 Query Problem in GraphQL

```javascript
// Symptom: 1 query to get 100 users, then 100 queries to get each user's profile
// Log your DB queries to detect it:
// "SELECT * FROM profiles WHERE user_id = 1"
// "SELECT * FROM profiles WHERE user_id = 2"
// ... 100 times

const resolvers = {
  User: {
    profile: async (user) => {
      return await db.query(`SELECT * FROM profiles WHERE user_id = ${user.id}`)
      // Called once per user — N+1!
    }
  }
}

// Fix: DataLoader — batches all requests in a single tick, then fetches once
const DataLoader = require('dataloader')

// Create loaders (once per request, in context)
const createContext = () => ({
  loaders: {
    profile: new DataLoader(async (userIds) => {
      // Called ONCE with all userIds at once
      const profiles = await db.query(
        `SELECT * FROM profiles WHERE user_id = ANY($1)`, [userIds]
      )
      // Must return array in same order as userIds
      return userIds.map(id => profiles.find(p => p.user_id === id) || null)
    })
  }
})

// Use in resolver
const resolvers = {
  User: {
    profile: (user, _, context) => context.loaders.profile.load(user.id)
    // load() queues the ID — DataLoader batches all queued IDs together
  }
}
```

---

## GraphQL Authorization

```javascript
// Common mistake: only checking auth at the query level, not field level
const resolvers = {
  Query: {
    user: authenticate(async (_, { id }, context) => {  // auth checked here
      return await db.getUser(id)
    })
  },
  User: {
    privateData: (user, _, context) => {
      // No auth check here — any authenticated user can access any user's private data!
      return user.sensitiveInfo
    }
  }
}

// Fix: field-level authorization
const resolvers = {
  User: {
    privateData: (user, _, context) => {
      if (context.currentUser.id !== user.id && !context.currentUser.isAdmin) {
        throw new ForbiddenError('Cannot access other users private data')
      }
      return user.sensitiveInfo
    }
  }
}

// Better: use graphql-shield for declarative permission rules
const permissions = shield({
  Query: { user: isAuthenticated },
  User: {
    privateData: and(isAuthenticated, isOwner),
    publicName: allow,
  }
})
```

---

## GraphQL Performance

```javascript
// Query complexity limiting — prevent expensive queries
const { createComplexityLimitRule } = require('graphql-validation-complexity')

const server = new ApolloServer({
  schema,
  validationRules: [
    createComplexityLimitRule(1000, {  // max complexity score of 1000
      onCost: (cost) => console.log('Query cost:', cost),
    })
  ]
})

// Depth limiting — prevent deeply nested queries
const depthLimit = require('graphql-depth-limit')
validationRules: [depthLimit(7)]  // max 7 levels deep

// Persisted queries — hash → query, prevents arbitrary query execution
// Apollo Client + Apollo Server support this out of the box

// Disable introspection in production
const server = new ApolloServer({
  introspection: process.env.NODE_ENV !== 'production'
})

// Query tracing — see resolver timing
const server = new ApolloServer({
  plugins: [
    ApolloServerPluginInlineTrace()  // adds tracing to response extensions
  ]
})
// Or use Apollo Studio for persistent traces
```

---

## Useful API Debugging Tools

```bash
# HTTPie — more readable than curl
pip install httpie
http GET https://api/users Authorization:"Bearer $TOKEN"
http POST https://api/users name=Alice email=alice@example.com

# jq — parse and filter JSON responses
curl -s https://api/users | jq '.data[] | {id, name}'  # extract specific fields
curl -s https://api/users | jq '[.data[] | select(.active == true)]'  # filter

# Postman collections as code — export/share test suites
# Newman — run Postman collections from CLI
npx newman run collection.json --environment production.json

# mitmproxy — intercept and inspect HTTPS traffic from any app
pip install mitmproxy
mitmproxy --mode transparent  # intercept all traffic
```
