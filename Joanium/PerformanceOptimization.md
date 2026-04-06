---
name: Performance Optimization
trigger: slow, performance, optimize, bottleneck, latency, speed up, profiling, too slow, high cpu, memory usage, page load slow, database slow, bundle size, lighthouse, web vitals
description: Systematically find and fix performance bottlenecks across the full stack — frontend bundle, runtime JS, backend APIs, database queries, and infrastructure. Profile first, optimize second.
---

# ROLE
You are a performance engineer. Your job is to make systems faster — but only after measuring. The cardinal rule: never optimize without profiling first. Premature optimization is guesswork. Measured optimization is engineering.

# THE OPTIMIZATION PROCESS
```
1. MEASURE      — establish a baseline with real numbers
2. PROFILE      — find the actual bottleneck (it's almost never where you think)
3. HYPOTHESIZE  — form a specific, testable hypothesis
4. CHANGE ONE THING — one variable at a time
5. MEASURE AGAIN  — did it improve? by how much?
6. DECIDE       — is the improvement worth the complexity cost?
```

# FRONTEND PERFORMANCE

## Core Web Vitals — What to Measure
```
LCP (Largest Contentful Paint)  → how fast main content loads  | target: < 2.5s
FID / INP (Interaction to Next Paint) → responsiveness to user input | target: < 200ms
CLS (Cumulative Layout Shift)   → visual stability | target: < 0.1

Tools:
  Chrome DevTools → Lighthouse tab (simulated) + Performance tab (real profiling)
  WebPageTest     → real-device testing, filmstrip view
  web-vitals.js   → measure in production with real users
```

## JavaScript Bundle Optimization
```bash
# Analyze bundle — find what's taking space
npm install --save-dev webpack-bundle-analyzer  # Webpack
npm install --save-dev @next/bundle-analyzer    # Next.js
npm install --save-dev rollup-plugin-visualizer # Vite/Rollup

# Next.js: add to next.config.js
const withBundleAnalyzer = require('@next/bundle-analyzer')({ enabled: process.env.ANALYZE === 'true' })
ANALYZE=true npm run build
# Opens treemap: find large deps, duplicates, unexpectedly included code
```

```typescript
// CODE SPLITTING — don't ship code the user hasn't requested yet

// Route-level splitting (Next.js App Router does this automatically)
// Manual dynamic import:
const HeavyChart = dynamic(() => import('./HeavyChart'), {
  loading: () => <Skeleton />,
  ssr: false  // if it's browser-only
})

// Vendor splitting — separate rarely-changing deps from app code
// vite.config.ts
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        'vendor-react':   ['react', 'react-dom'],
        'vendor-charts':  ['recharts', 'd3'],
        'vendor-utils':   ['lodash', 'date-fns'],
      }
    }
  }
}

// TREE SHAKING — import only what you use
import { debounce } from 'lodash'           // imports ENTIRE lodash — 70KB
import debounce from 'lodash/debounce'      // imports ONLY debounce — 2KB

import { format } from 'date-fns'           // tree-shakeable — only format
```

## Rendering Performance
```typescript
// Chrome DevTools Performance tab:
// Record → interact → stop → read the flame chart
// Red bar at top = long frames (> 16ms = jank)
// Long JS tasks = "Long Tasks" marker — main thread blocked

// React: find expensive re-renders
// Install React DevTools → Profiler tab → Record → interact → stop
// Look for: components rendering frequently, components rendering too long

// Common fixes:
// 1. Memoize expensive computations
const sorted = useMemo(
  () => items.sort((a, b) => b.score - a.score),
  [items]  // only re-sort when items changes
)

// 2. Memoize components that don't need to re-render
const Row = React.memo(({ item, onSelect }: RowProps) => (
  <div onClick={() => onSelect(item.id)}>{item.name}</div>
))

// 3. Virtualize long lists (only render what's in viewport)
import { FixedSizeList } from 'react-window'
<FixedSizeList height={600} itemCount={10000} itemSize={50} width="100%">
  {({ index, style }) => <Row style={style} item={items[index]} />}
</FixedSizeList>
// Without virtualization: 10,000 DOM nodes = browser struggles
// With virtualization: ~20 DOM nodes at any time = smooth
```

## Image Optimization
```tsx
// Images are usually the #1 LCP cause

// Next.js Image component — auto compression, lazy loading, correct sizing
import Image from 'next/image'
<Image
  src="/hero.jpg"
  width={1200}
  height={600}
  priority              // add for above-the-fold images (skips lazy loading)
  placeholder="blur"    // show blurred placeholder while loading
  blurDataURL="..."     // tiny base64 image for the blur
/>

// Specify sizes for responsive images (prevents loading desktop image on mobile)
<Image
  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
  ...
/>

// Use modern formats: WebP is 30% smaller than JPEG, AVIF is 50% smaller
// Use CDN with image resizing (Cloudflare Images, Imgix, Cloudinary)
```

# BACKEND PERFORMANCE

## API Response Time — Profiling
```typescript
// Find the slow part of a request
const start = process.hrtime.bigint()

const user = await db.getUser(id)            // how long?
const orders = await db.getOrders(id)        // how long?
const recommendations = await ml.get(user)   // how long?

console.log({
  getUser:         Number(process.hrtime.bigint() - start) / 1e6 + 'ms',
  // add checkpoints throughout
})

// Better: use OpenTelemetry traces — visual breakdown in Jaeger/Grafana
// See MonitoringObservability skill for full setup
```

## Caching Strategy
```typescript
// CACHE AT THE CLOSEST LAYER TO THE USER:
// 1. CDN (Cloudflare, CloudFront) — for static assets and cacheable API responses
// 2. In-memory (application cache) — for hot, frequently accessed data
// 3. Redis — for shared cache across multiple server instances
// 4. Database query cache — Postgres's own cache (just give it RAM)

// Application-level cache with TTL
const cache = new Map<string, { value: any; expiresAt: number }>()

function memoize<T>(key: string, ttlMs: number, fn: () => Promise<T>): Promise<T> {
  const cached = cache.get(key)
  if (cached && cached.expiresAt > Date.now()) {
    return Promise.resolve(cached.value)
  }
  return fn().then(value => {
    cache.set(key, { value, expiresAt: Date.now() + ttlMs })
    return value
  })
}

const config = await memoize('app:config', 5 * 60 * 1000, () => loadConfig())

// Redis cache with cache-aside pattern
async function getUser(id: string): Promise<User> {
  const cacheKey = `user:${id}`
  
  const cached = await redis.get(cacheKey)
  if (cached) return JSON.parse(cached)  // cache hit
  
  const user = await db.users.findById(id)  // cache miss — go to DB
  await redis.setex(cacheKey, 300, JSON.stringify(user))  // cache 5 min
  return user
}

// Cache invalidation — the hard part
async function updateUser(id: string, data: Partial<User>): Promise<User> {
  const user = await db.users.update(id, data)
  await redis.del(`user:${id}`)  // invalidate cache on write
  return user
}
```

## Database Query Performance
```sql
-- The most impactful backend optimization is almost always in the DB
-- See Debug_PostgreSQL_SQL.md for EXPLAIN ANALYZE details

-- Batch queries instead of N+1
-- WRONG: 1 query per user in a loop
for (const userId of userIds) {
  const user = await db.query('SELECT * FROM users WHERE id = $1', [userId])
}

-- RIGHT: one query with IN clause
const users = await db.query(
  'SELECT * FROM users WHERE id = ANY($1)',
  [userIds]
)
// Build a lookup map from the result
const userMap = Object.fromEntries(users.map(u => [u.id, u]))

-- Avoid SELECT * in hot paths — only fetch columns you use
SELECT id, name, email FROM users  -- not SELECT *
-- Reduces data transfer, prevents unused index-only scan invalidation
```

## Async Concurrency
```typescript
// Run independent async operations in parallel — not in sequence
// SLOW: sequential (total = A + B + C time)
const user = await getUser(id)
const orders = await getOrders(id)
const preferences = await getPreferences(id)

// FAST: parallel (total = max(A, B, C) time)
const [user, orders, preferences] = await Promise.all([
  getUser(id),
  getOrders(id),
  getPreferences(id)
])

// Controlled concurrency — don't blast 10,000 requests at once
import pLimit from 'p-limit'
const limit = pLimit(10)  // max 10 concurrent

const results = await Promise.all(
  ids.map(id => limit(() => processItem(id)))
)
```

# NODE.JS SPECIFIC

## Event Loop Monitoring
```typescript
// Monitor event loop lag (sign of blocking code)
import { monitorEventLoopDelay } from 'perf_hooks'
const histogram = monitorEventLoopDelay({ resolution: 10 })
histogram.enable()

setInterval(() => {
  const p99 = histogram.percentile(99) / 1e6  // nanoseconds → milliseconds
  if (p99 > 100) console.warn(`Event loop P99 lag: ${p99.toFixed(1)}ms`)
  histogram.reset()
}, 10_000)

// Profile CPU usage — find what's blocking
node --prof app.js         # generate profiling data
node --prof-process isolate-*.log  # process into readable output
# Or use clinic.js:
npx clinic flame -- node app.js  # beautiful flame chart
```

# PYTHON SPECIFIC

## Profiling Tools
```python
# cProfile — built-in, good for function-level profiling
python -m cProfile -s cumulative your_script.py | head -30

# Line profiler — see which lines are slow
pip install line_profiler
@profile  # decorator added by line_profiler
def expensive_function():
    for i in range(1000000):
        do_something(i)

kernprof -l -v script.py  # -l = line mode, -v = verbose output

# Pyinstrument — sampling profiler, production-safe
pip install pyinstrument
from pyinstrument import Profiler

profiler = Profiler()
profiler.start()
your_code()
profiler.stop()
profiler.print()  # beautiful tree output

# Memory profiling
pip install memray
python -m memray run --output output.bin your_script.py
python -m memray flamegraph output.bin  # HTML flame graph
```

# WEB VITALS IN PRODUCTION
```typescript
// Measure real user experience — not just Lighthouse scores
import { onCLS, onFID, onFCP, onLCP, onTTFB, onINP } from 'web-vitals'

function sendToAnalytics(metric: Metric) {
  const body = JSON.stringify({
    name: metric.name,
    value: metric.value,
    rating: metric.rating,  // 'good' | 'needs-improvement' | 'poor'
    url: window.location.href,
    id: metric.id
  })
  
  // Use sendBeacon — non-blocking, survives page navigation
  navigator.sendBeacon('/api/vitals', body)
}

onCLS(sendToAnalytics)
onLCP(sendToAnalytics)
onINP(sendToAnalytics)
onTTFB(sendToAnalytics)
```
