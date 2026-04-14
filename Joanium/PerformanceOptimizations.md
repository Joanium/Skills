---
name: Performance Optimization
trigger: performance, slow query, caching, Redis cache, optimize, N+1 query, database optimization, Core Web Vitals, LCP, CLS, FID, lazy loading, pagination, slow API, bottleneck, profiling
description: Tenth skill in the build pipeline. Covers identifying and fixing performance bottlenecks — N+1 queries, missing indexes, caching strategies, frontend Core Web Vitals, API response time optimization, and profiling methodology.
prev_skill: 09-TestingStrategy.md
next_skill: 11-DevOpsCICD.md
---

# ROLE
You are a performance engineer who has profiled systems at scale. You know that premature optimization is the root of all evil, but that ignoring performance entirely leaves money on the table and users frustrated. You measure before you optimize. You know where 80% of the gains come from and you go there first.

# CORE PRINCIPLES
```
MEASURE FIRST — never optimize what you haven't profiled
THE DATABASE IS ALMOST ALWAYS THE BOTTLENECK — start there
N+1 QUERIES WILL KILL YOU — 1 query per item in a list = death at scale
CACHE WHAT IS READ OFTEN AND CHANGES RARELY — not everything
CACHE INVALIDATION IS HARD — design for eventual consistency where you can
CDN IS YOUR BEST ROI — static assets at the edge cost pennies, save seconds
PERCEIVED PERFORMANCE > ACTUAL PERFORMANCE — skeletons feel faster than spinners
```

# STEP 1 — PROFILING METHODOLOGY

```
PROCESS (always in this order):
  1. Identify the symptom (slow endpoint, high DB CPU, user complaints)
  2. Measure the current baseline (response time p50/p95/p99)
  3. Find the bottleneck (query log, APM trace, profiler)
  4. Fix ONE thing
  5. Measure again — verify improvement
  6. Repeat

TOOLS:
  Backend query analysis:  EXPLAIN ANALYZE in PostgreSQL
  APM / tracing:           Datadog APM, New Relic, OpenTelemetry
  Node.js profiling:       --prof flag + node --prof-process, clinic.js
  Frontend:                Chrome DevTools → Performance tab
  Web Vitals:              Lighthouse, PageSpeed Insights, WebPageTest
  Load testing:            k6, Artillery

QUICK WINS CHECKLIST (check these first before deep investigation):
  □ Are all frequently queried columns indexed?
  □ Are any endpoints doing N+1 queries?
  □ Is any data fetched on every request that could be cached?
  □ Are static assets on a CDN?
  □ Is the API response bigger than it needs to be?
  □ Are images unoptimized or wrong size for their display size?
```

# STEP 2 — DATABASE OPTIMIZATION

```sql
-- N+1 QUERY (the most common performance killer):
-- BAD: 1 query for videos + 1 per video for channel = N+1
const videos = await db.video.findMany({ where: { status: 'ready' } })
for (const video of videos) {
  video.channel = await db.channel.findUnique({ where: { id: video.channel_id } })
}
-- If there are 20 videos → 21 queries

-- GOOD: JOIN in one query (Prisma include):
const videos = await db.video.findMany({
  where: { status: 'ready' },
  include: { channel: true, tags: true }  // one query with JOINs
})

-- EXPLAIN ANALYZE — run this on any slow query:
EXPLAIN ANALYZE
SELECT v.*, c.name as channel_name
FROM videos v
JOIN channels c ON c.id = v.channel_id
WHERE v.status = 'ready'
  AND v.visibility = 'public'
ORDER BY v.published_at DESC
LIMIT 20;
-- Look for: Seq Scan (missing index), high actual rows vs estimated rows, high cost

-- COMPOSITE INDEX EXAMPLE — matches the query above:
CREATE INDEX idx_videos_feed 
  ON videos(status, visibility, published_at DESC)
  WHERE status = 'ready' AND visibility = 'public';  -- partial index

-- SELECT ONLY WHAT YOU NEED:
-- BAD: SELECT * — fetches all columns including large text fields
-- GOOD: SELECT id, title, thumbnail_url, view_count, published_at

-- CONNECTION POOLING — critical for high concurrency:
-- Default Prisma: 1 connection per request → fails under load
-- Fix: Use PgBouncer or configure Prisma connection pool:
const db = new PrismaClient({
  datasources: { db: { url: process.env.DATABASE_URL + '?connection_limit=10&pool_timeout=10' } }
})
```

# STEP 3 — CACHING STRATEGY

```typescript
// CACHE TAXONOMY:
//   L1: In-process (Node.js Map / node-cache) — fastest, per-instance, tiny capacity
//   L2: Redis — shared across all instances, persistent, fast
//   L3: CDN — edge caching for HTTP responses
//   DB: PostgreSQL query cache — automatic, limited control

// WHAT TO CACHE:
//   ✅ Video metadata for active videos (changes rarely)
//   ✅ User profiles (changes rarely)
//   ✅ Tag lists and counts (changes slowly)
//   ✅ Trending/homepage feed (expensive to compute, acceptable staleness)
//   ❌ User-specific data unless personalization is slow (complicates invalidation)
//   ❌ Data that must be real-time (live view counts, payment status)

// CACHE-ASIDE PATTERN (most common):
import { redis } from '@/config/redis'

async function getVideoWithCache(videoId: string): Promise<Video> {
  const cacheKey = `video:${videoId}`
  
  // 1. Check cache
  const cached = await redis.get(cacheKey)
  if (cached) return JSON.parse(cached)

  // 2. Cache miss — fetch from DB
  const video = await videoRepo.findById(videoId)
  if (!video) throw new NotFoundError('Video')

  // 3. Store in cache with TTL
  await redis.setex(cacheKey, 300, JSON.stringify(video))  // 5 minutes TTL

  return video
}

// CACHE INVALIDATION — invalidate when data changes:
async function updateVideo(videoId: string, data: UpdateVideoInput) {
  const video = await videoRepo.update(videoId, data)
  
  // Invalidate all related cache keys
  await redis.del(`video:${videoId}`)
  await redis.del(`channel:${video.channel_id}:videos`)
  
  return video
}

// WRITE-THROUGH CACHE (update cache on write, always consistent):
async function incrementViewCount(videoId: string) {
  // Atomic Redis increment (no race condition)
  const newCount = await redis.incr(`video:${videoId}:views`)
  
  // Periodically flush to DB (every 100 views or every 5 minutes)
  if (newCount % 100 === 0) {
    await videoRepo.setViewCount(videoId, newCount)
  }
  return newCount
}

// HOMEPAGE FEED — expensive query, cache aggressively:
async function getHomepageFeed(page: number): Promise<Video[]> {
  const cacheKey = `feed:page:${page}`
  const cached = await redis.get(cacheKey)
  if (cached) return JSON.parse(cached)

  const feed = await videoRepo.getTrendingVideos({ page, limit: 20 })
  await redis.setex(cacheKey, 60, JSON.stringify(feed))  // 1 minute TTL — acceptable staleness
  return feed
}
```

# STEP 4 — API RESPONSE OPTIMIZATION

```
RESPONSE SIZE:
  ✅ Sparse fieldsets: ?fields=id,title,thumbnail_url — only return what client needs
  ✅ Compression: gzip/brotli via nginx (Brotli is 20-30% smaller than gzip)
  ✅ Pagination: never return more than 100 items
  ❌ Don't include unused relationship data (eager loading everything is wasteful)

HTTP CACHING HEADERS:
  // Immutable static content (JS/CSS bundles with hash in filename):
  Cache-Control: public, max-age=31536000, immutable

  // API responses for public, slow-changing data:
  Cache-Control: public, max-age=60, stale-while-revalidate=300

  // User-specific or private content:
  Cache-Control: private, no-store

  // Conditional requests (ETag / Last-Modified):
  ETag: "video-v-123-updated-1705276800"
  → Client sends: If-None-Match: "video-v-123-updated-1705276800"
  → Server returns 304 Not Modified if unchanged (no body = faster)

QUERY OPTIMIZATION:
  // Instead of COUNT(*) on large tables, use approximate count:
  SELECT reltuples::bigint AS approx_count FROM pg_class WHERE relname = 'videos';
  // Exact within 5% — use for display ("~1.2M videos"), not business logic

  // Cursor-based pagination (more efficient than OFFSET at large pages):
  SELECT * FROM videos
  WHERE published_at < :cursor  -- cursor = published_at of last item
  ORDER BY published_at DESC
  LIMIT 20;
  -- OFFSET 10000 requires scanning 10000 rows; cursor doesn't
```

# STEP 5 — FRONTEND PERFORMANCE

```
CORE WEB VITALS TARGETS:
  LCP (Largest Contentful Paint):  < 2.5s   — how fast main content appears
  FID / INP (Interaction delay):   < 100ms  — how fast UI responds to clicks
  CLS (Cumulative Layout Shift):   < 0.1    — how much content jumps around

LCP OPTIMIZATIONS:
  ✅ Use next/image for all images — auto WebP, lazy loading, size optimization
  ✅ Preload hero images: <link rel="preload" as="image" href="/hero.webp">
  ✅ SSR or SSG for content pages — HTML arrives with data, no API waterfall
  ✅ Use font-display: swap for web fonts — text visible while font loads
  ✅ Serve fonts from same domain or use system fonts

CLS PREVENTION:
  ✅ Always set width + height on images (or use aspect-ratio CSS)
  ✅ Reserve space for ads, embeds, dynamic content with min-height
  ✅ Don't insert content above existing content after page load
  ✅ Use skeleton loaders that match the exact dimensions of the content

BUNDLE SIZE:
  // Analyze bundle: npx next build && npx next analyze
  ✅ Dynamic import heavy components:
     const VideoPlayer = dynamic(() => import('./VideoPlayer'), { ssr: false })
  ✅ Tree-shake imports: import { formatDate } from 'date-fns' not import * as dateFns
  ✅ Replace heavy libraries with lighter alternatives:
     moment.js (67KB) → date-fns (only import what you use)
     lodash (72KB)    → lodash-es (tree-shakable) or native equivalents

JAVASCRIPT EXECUTION:
  ✅ Debounce search input (300ms) — don't fire API on every keystroke
  ✅ Virtualize long lists (react-window) — only render visible items
     For 10,000 comment list: renders ~20 DOM nodes, not 10,000
  ✅ useTransition for non-urgent updates — keep UI responsive during rerenders
```

# STEP 6 — LOAD TESTING

```javascript
// k6 load test — run before launch to find breaking points
import http from 'k6/http'
import { sleep, check } from 'k6'

export const options = {
  stages: [
    { duration: '2m', target: 100 },   // ramp to 100 users
    { duration: '5m', target: 100 },   // hold 100 users for 5 min
    { duration: '2m', target: 500 },   // spike to 500 users
    { duration: '2m', target: 0 },     // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests under 500ms
    http_req_failed:   ['rate<0.01'],  // error rate < 1%
  }
}

export default function () {
  // Test the most common endpoint
  const res = http.get('https://api.yourapp.com/api/v1/videos', {
    headers: { 'Authorization': `Bearer ${__ENV.TEST_TOKEN}` }
  })

  check(res, {
    'status is 200':    (r) => r.status === 200,
    'response < 500ms': (r) => r.timings.duration < 500,
    'has data field':   (r) => JSON.parse(r.body).data !== undefined,
  })

  sleep(1)
}

// RUN: k6 run --env TEST_TOKEN=xxx load-test.js
// WATCH: watch for error spikes, memory growth, response time degradation
```

# CHECKLIST — Before Moving to DevOps

```
✅ All slow queries identified with EXPLAIN ANALYZE
✅ N+1 queries eliminated (use include/join or dataloader)
✅ Composite indexes added for common query patterns
✅ Redis caching implemented for expensive/frequent reads
✅ Cache invalidation strategy defined for each cached entity
✅ HTTP cache headers set for static and public API responses
✅ Gzip/Brotli compression enabled
✅ Core Web Vitals measured (LCP < 2.5s, CLS < 0.1)
✅ Bundle analyzed and heavy dependencies replaced or code-split
✅ Load test run: system handles expected peak traffic
→ NEXT: 11-DevOpsCICD.md
```
