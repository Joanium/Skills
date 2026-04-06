---
name: EdgeComputing
description: Design and build applications that run at the edge — Cloudflare Workers, Vercel Edge Functions, Deno Deploy, Lambda@Edge, and IoT edge nodes. Use when the user asks about edge runtimes, edge caching, geolocation logic, latency optimization, edge middleware, or deploying compute closer to users.
---

You are an expert in edge computing, specializing in designing and deploying low-latency compute workloads to edge runtimes including Cloudflare Workers, Vercel Edge Runtime, Deno Deploy, AWS Lambda@Edge, and Fastly Compute.

The user provides an edge computing task: migrating a server function to the edge, building edge middleware, implementing geolocation-based routing, optimizing for cold starts, or designing a globally distributed compute architecture.

## Edge Computing Mental Model

Edge compute runs your code in data centers distributed worldwide, physically close to users. The key constraints that distinguish edge from traditional serverless:

- **No Node.js APIs**: Edge runtimes use the WinterCG Web Standard APIs — `fetch`, `Request`, `Response`, `URL`, `crypto`, `ReadableStream`. No `fs`, `path`, `process`, `net`, etc.
- **Limited execution time**: Typically 5–50ms CPU time (not wall time); long-running tasks don't belong at the edge
- **Small bundle sizes**: Workers have limits (1–10MB compressed); no heavy native modules
- **No persistent in-process state**: Each request gets a fresh isolate (or a V8 isolate that may be reused — don't rely on global state persisting)
- **Cold starts are nearly zero**: V8 isolates start in microseconds vs Lambda's milliseconds

What belongs at the edge:

- Request routing and rewriting
- Authentication / JWT validation
- A/B testing and feature flag evaluation
- Geolocation-based personalization
- Response transformation (headers, HTML injection)
- Edge caching and cache invalidation logic
- Bot detection and rate limiting
- API proxying and response aggregation

## Cloudflare Workers

**Basic Worker Structure**

```js
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Routing
    if (url.pathname.startsWith('/api/')) {
      return handleAPI(request, env);
    }

    // Pass through to origin
    return fetch(request);
  },
};
```

**KV Storage** (eventually consistent, global, great for config/flags)

```js
// Read
const value = await env.MY_KV.get('config:featureFlags', { type: 'json' });

// Write (from a Worker with write access)
await env.MY_KV.put('config:featureFlags', JSON.stringify(flags), {
  expirationTtl: 3600, // seconds
});
```

**Durable Objects** (strongly consistent, single-location, great for coordination)

```js
// Get a stub for a specific object by name
const id = env.ROOM.idFromName(roomId);
const room = env.ROOM.get(id);
return room.fetch(request); // Forward to the Durable Object

// Inside the Durable Object class
export class Room {
  constructor(state, env) {
    this.state = state;
  }
  async fetch(request) {
    // this.state.storage is persistent SQLite
    const count = (await this.state.storage.get('count')) || 0;
    await this.state.storage.put('count', count + 1);
    return new Response(`Count: ${count + 1}`);
  }
}
```

**R2 (S3-compatible object storage)**

```js
// Upload
await env.BUCKET.put('uploads/image.png', request.body, {
  httpMetadata: { contentType: 'image/png' },
});

// Download
const object = await env.BUCKET.get('uploads/image.png');
if (!object) return new Response('Not found', { status: 404 });
return new Response(object.body, { headers: object.httpMetadata });
```

**Queues**

```js
// Producer: send a message
await env.MY_QUEUE.send({ type: 'email', to: 'user@example.com' });

// Consumer: handle messages in a batch
export default {
  async queue(batch, env) {
    for (const message of batch.messages) {
      await processMessage(message.body, env);
      message.ack();
    }
  },
};
```

**wrangler.toml**

```toml
name = "my-worker"
main = "src/index.js"
compatibility_date = "2024-09-23"

[[kv_namespaces]]
binding = "MY_KV"
id = "xxxx"

[[r2_buckets]]
binding = "BUCKET"
bucket_name = "my-bucket"

[vars]
ENVIRONMENT = "production"
```

## Vercel Edge Middleware & Edge Functions

**Middleware** (runs before every request on the matched path)

```ts
// middleware.ts — at project root
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const country = request.geo?.country || 'US';
  const url = request.nextUrl.clone();

  // Geo-redirect example
  if (country === 'IN' && !url.pathname.startsWith('/in')) {
    url.pathname = `/in${url.pathname}`;
    return NextResponse.redirect(url);
  }

  // Add custom headers to the response
  const response = NextResponse.next();
  response.headers.set('x-country', country);
  return response;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
```

**Edge API Routes (Next.js App Router)**

```ts
// app/api/geo/route.ts
export const runtime = 'edge';

export async function GET(request: Request) {
  // Vercel injects geo data via headers in production
  const country = request.headers.get('x-vercel-ip-country') || 'unknown';
  const city = request.headers.get('x-vercel-ip-city') || 'unknown';

  return Response.json({ country, city });
}
```

## Geolocation Patterns

**A/B Testing at the Edge**

```js
function getVariant(userId) {
  // Deterministic assignment based on user ID
  const hash = simpleHash(userId);
  return hash % 100 < 50 ? 'control' : 'treatment';
}

async function fetch(request, env) {
  const userId = getCookie(request, 'userId') || crypto.randomUUID();
  const variant = getVariant(userId);

  const response = await fetch(request);
  const newResponse = new Response(response.body, response);
  newResponse.headers.set('x-ab-variant', variant);
  setCookie(newResponse, 'userId', userId);
  return newResponse;
}
```

**Country-Based Content**

```js
// Cloudflare provides cf.country on every request
const country = request.cf?.country;

const pricingByCountry = {
  IN: { currency: 'INR', symbol: '₹', price: 999 },
  US: { currency: 'USD', symbol: '$', price: 12 },
  GB: { currency: 'GBP', symbol: '£', price: 10 },
};

const pricing = pricingByCountry[country] || pricingByCountry['US'];
```

## Edge Caching Strategies

**Cache API (Cloudflare Workers)**

```js
const cache = caches.default;

async function fetchWithCache(request) {
  // Try cache first
  const cached = await cache.match(request);
  if (cached) return cached;

  // Fetch from origin
  const response = await fetch(request);

  // Clone and cache (response body can only be consumed once)
  const responseToCache = response.clone();
  const cacheControl = responseToCache.headers.get('cache-control');

  if (!cacheControl?.includes('no-store')) {
    ctx.waitUntil(cache.put(request, responseToCache));
  }

  return response;
}
```

**Cache Keys**

- Vary cache by country: append `?country=IN` to cache key for geo-personalized content
- Vary by auth state: use separate cache namespaces for authed vs anon content
- Never cache responses with `Set-Cookie` headers unless you've stripped them first

**Surrogate Keys / Cache Tags** (Cloudflare)

```js
response.headers.set('Cache-Tag', `product-${id},category-electronics`);
// Purge all product pages when product data changes:
// POST api.cloudflare.com/zones/{zone}/purge_cache with { tags: ['product-42'] }
```

## Authentication at the Edge

**JWT Validation**

```js
import { jwtVerify, importSPKI } from 'jose'; // jose works in edge runtimes

async function validateJWT(token, env) {
  try {
    const publicKey = await importSPKI(env.JWT_PUBLIC_KEY, 'RS256');
    const { payload } = await jwtVerify(token, publicKey, {
      issuer: 'https://auth.example.com',
      audience: 'api.example.com',
    });
    return payload;
  } catch {
    return null;
  }
}

async function fetch(request, env) {
  const token = request.headers.get('authorization')?.replace('Bearer ', '');
  const payload = token ? await validateJWT(token, env) : null;

  if (!payload) {
    return new Response('Unauthorized', { status: 401 });
  }

  // Forward to origin with user context in header
  const newRequest = new Request(request, {
    headers: { ...Object.fromEntries(request.headers), 'x-user-id': payload.sub },
  });
  return fetch(newRequest);
}
```

## Performance & Limits

| Platform           | CPU Time Limit             | Memory | Bundle Size     | Persistent Storage  |
| ------------------ | -------------------------- | ------ | --------------- | ------------------- |
| Cloudflare Workers | 10–50ms (paid)             | 128MB  | 10MB compressed | KV, R2, D1, DO      |
| Vercel Edge        | 25ms                       | 128MB  | 4MB             | None (use external) |
| Deno Deploy        | No hard limit              | 512MB  | No limit        | Deno KV             |
| Lambda@Edge        | 5s (viewer) / 30s (origin) | 128MB  | 1MB zipped      | None                |

**Performance Tips**

- Use `ctx.waitUntil()` for non-critical async work (analytics, cache writes) — don't block the response
- Minimize imported libraries — every byte counts on edge bundles
- Cache expensive computations in KV or Durable Objects
- Use streaming responses (`ReadableStream`) for large payloads
- Prefer `fetch()` with `cf: { cacheEverything: true }` for cacheable subrequests

## Local Development

```bash
# Cloudflare Workers
npx wrangler dev             # local dev server with KV/R2 emulation
npx wrangler deploy          # deploy to production

# Vercel Edge (Next.js)
vercel dev                   # local dev with edge runtime emulation
vercel --prod                # deploy to production

# Deno Deploy
deployctl run --no-check main.ts   # local run
deployctl deploy --project=myapp main.ts
```
