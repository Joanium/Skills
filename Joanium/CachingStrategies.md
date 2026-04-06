---
name: Caching Strategies
trigger: caching, redis cache, cache invalidation, cache aside, write through, TTL, cache eviction, in-memory cache, cache strategy, memoize, CDN cache, HTTP caching, cache busting, distributed cache, cache warming
description: Implement effective caching at every layer of the stack. Covers Redis patterns (cache-aside, write-through, write-behind), in-memory caching, HTTP cache headers, CDN, cache invalidation strategies, TTL design, and avoiding cache stampedes.
---

# ROLE
You are a performance engineer focused on caching. Your job is to make applications faster by reducing redundant computation and I/O. Caching has two hard problems: knowing what to cache and knowing when to invalidate it. Get both right.

# CACHING LAYERS — CHOOSE THE RIGHT ONE
```
Browser Cache      → HTTP headers (Cache-Control) — free, no backend needed
CDN Cache          → static assets, API responses at edge — global latency reduction
Application Cache  → in-process memory (Map/LRU) — nanoseconds, limited size
Distributed Cache  → Redis/Memcached — milliseconds, shared across instances
Database Cache     → query result cache — reduces DB load
```

# REDIS CACHING PATTERNS

## Cache-Aside (Lazy Loading) — Most Common Pattern
```typescript
import { createClient } from 'redis'

const redis = createClient({ url: process.env.REDIS_URL })
await redis.connect()

// Pattern:
// 1. Check cache
// 2. Cache miss? → Query DB, store in cache
// 3. Return result

async function getUser(userId: string): Promise<User> {
  const cacheKey = `user:${userId}`

  // 1. Try cache
  const cached = await redis.get(cacheKey)
  if (cached) {
    return JSON.parse(cached)   // cache hit
  }

  // 2. Cache miss — query DB
  const user = await db.users.findById(userId)
  if (!user) throw new Error('User not found')

  // 3. Store in cache with TTL
  await redis.set(cacheKey, JSON.stringify(user), { EX: 3600 })  // 1 hour TTL

  return user
}

// Invalidate on update
async function updateUser(userId: string, data: Partial<User>): Promise<User> {
  const updated = await db.users.update(userId, data)

  // Delete cache — next read will repopulate it
  await redis.del(`user:${userId}`)

  return updated
}

// Generic cache wrapper
async function withCache<T>(
  key: string,
  ttlSeconds: number,
  fetcher: () => Promise<T>
): Promise<T> {
  const cached = await redis.get(key)
  if (cached) return JSON.parse(cached) as T

  const data = await fetcher()
  await redis.set(key, JSON.stringify(data), { EX: ttlSeconds })
  return data
}

// Usage
const posts = await withCache('posts:recent', 300, () => db.posts.findRecent(20))
```

## Write-Through — Keep Cache and DB in Sync
```typescript
// Write to cache AND DB simultaneously on every write
// Pro: cache always has fresh data
// Con: higher write latency, caches things that may never be read

async function saveUserWriteThrough(userId: string, data: User): Promise<User> {
  const [saved] = await Promise.all([
    db.users.save(userId, data),
    redis.set(`user:${userId}`, JSON.stringify(data), { EX: 3600 })
  ])
  return saved
}
```

## Write-Behind (Write-Back) — Async Persistence
```typescript
// Write to cache immediately, persist to DB asynchronously
// Pro: lowest write latency
// Con: data loss risk if cache dies before persisting

const pendingWrites = new Map<string, { data: any; scheduledAt: number }>()

async function saveUserWriteBehind(userId: string, data: User): Promise<void> {
  // Update cache immediately — reads are instant
  await redis.set(`user:${userId}`, JSON.stringify(data), { EX: 3600 })

  // Schedule async write to DB
  pendingWrites.set(userId, { data, scheduledAt: Date.now() })
}

// Background flush job
setInterval(async () => {
  const now = Date.now()
  for (const [userId, { data, scheduledAt }] of pendingWrites) {
    if (now - scheduledAt > 1000) {   // flush after 1 second of no updates
      await db.users.save(userId, data)
      pendingWrites.delete(userId)
    }
  }
}, 500)
```

## Cache Invalidation Strategies
```typescript
// Strategy 1: TTL-based expiry (simplest)
await redis.set(key, value, { EX: 300 })   // auto-expires in 5 min

// Strategy 2: Event-based invalidation (most correct)
// After any mutation, explicitly delete affected keys
async function deletePost(postId: string): Promise<void> {
  await db.posts.delete(postId)

  await Promise.all([
    redis.del(`post:${postId}`),           // the post itself
    redis.del('posts:featured'),           // featured posts list
    redis.del(`posts:tag:javascript`),     // tag lists (if this post had tags)
    redis.del(`user:${authorId}:posts`),   // author's posts list
  ])
}

// Strategy 3: Cache tags (group-based invalidation)
// Store metadata about which keys belong to which group
async function cacheWithTag(key: string, tag: string, value: any, ttl: number) {
  const pipeline = redis.multi()
  pipeline.set(key, JSON.stringify(value), { EX: ttl })
  pipeline.sAdd(`tag:${tag}`, key)          // track key under this tag
  pipeline.expire(`tag:${tag}`, ttl)
  await pipeline.exec()
}

async function invalidateByTag(tag: string) {
  const keys = await redis.sMembers(`tag:${tag}`)
  if (keys.length) {
    await Promise.all([
      redis.del(keys),
      redis.del(`tag:${tag}`)
    ])
  }
}

// Usage
await cacheWithTag('user:123', 'users', user, 3600)
await cacheWithTag('posts:by-user:123', 'users', posts, 300)
// When user data changes:
await invalidateByTag('users')   // deletes both user:123 and posts:by-user:123
```

## Cache Stampede Prevention
```typescript
// Problem: cache expires, 100 requests all hit DB simultaneously
// Solution 1: Lock (mutex)
import Redlock from 'redlock'
const redlock = new Redlock([redis])

async function getPopularPostsWithLock(): Promise<Post[]> {
  const key = 'posts:popular'
  const cached = await redis.get(key)
  if (cached) return JSON.parse(cached)

  // Try to acquire lock — only one instance fetches
  const lock = await redlock.acquire([`lock:${key}`], 5000)
  try {
    // Double-check after acquiring lock
    const recheck = await redis.get(key)
    if (recheck) return JSON.parse(recheck)

    const posts = await db.posts.findPopular()
    await redis.set(key, JSON.stringify(posts), { EX: 300 })
    return posts
  } finally {
    await lock.release()
  }
}

// Solution 2: Probabilistic early expiration
// Start refreshing before cache actually expires
async function getWithEarlyRefresh<T>(key: string, ttl: number, fetcher: () => Promise<T>): Promise<T> {
  const raw = await redis.get(key)
  if (raw) {
    const { data, expiresAt } = JSON.parse(raw)
    const remaining = expiresAt - Date.now()

    // If 10% of TTL remains, refresh in background (only ~10% of requests trigger this)
    if (remaining < ttl * 100 && Math.random() < 0.1) {
      fetcher().then(async fresh => {
        await redis.set(key, JSON.stringify({
          data: fresh,
          expiresAt: Date.now() + ttl * 1000
        }), { EX: ttl })
      })
    }
    return data
  }

  const data = await fetcher()
  await redis.set(key, JSON.stringify({ data, expiresAt: Date.now() + ttl * 1000 }), { EX: ttl })
  return data
}
```

## Redis Data Structures Beyond Strings
```typescript
// Hash — for objects (avoids parsing JSON, can update fields individually)
await redis.hSet('user:123', { name: 'Alice', email: 'a@b.com', role: 'admin' })
await redis.hGet('user:123', 'name')           // 'Alice'
await redis.hGetAll('user:123')                // { name, email, role }
await redis.hSet('user:123', 'name', 'Alice B') // update single field

// Sorted Set — leaderboards, rate limiting, priority queues
await redis.zAdd('leaderboard', [{ score: 1500, value: 'user:123' }])
await redis.zRangeWithScores('leaderboard', 0, 9, { REV: true })  // top 10

// Set — unique membership, tags
await redis.sAdd('online-users', userId)
await redis.sRem('online-users', userId)
await redis.sCard('online-users')              // count
await redis.sIsMember('online-users', userId)  // boolean check

// List — activity feeds, recent items
await redis.lPush('activity:user:123', JSON.stringify(event))
await redis.lTrim('activity:user:123', 0, 49)  // keep last 50 items
await redis.lRange('activity:user:123', 0, 19) // get first 20
```

# IN-PROCESS CACHING (LRU)
```typescript
import LRU from 'lru-cache'

// Good for: frequently-read, rarely-changed data (config, feature flags)
// Limitation: not shared between server instances
const cache = new LRU<string, any>({
  max: 500,              // max 500 items
  ttl: 1000 * 60 * 5,   // 5 minutes TTL
  updateAgeOnGet: true,  // refresh TTL on access
})

function getFeatureFlag(key: string): boolean {
  if (cache.has(key)) return cache.get(key)
  const value = fetchFlagFromDB(key)
  cache.set(key, value)
  return value
}
```

# HTTP CACHING HEADERS
```typescript
// Express middleware for cache headers

// Public cacheable resources (CDN + browser)
app.get('/api/config', (req, res) => {
  res.set('Cache-Control', 'public, max-age=300, s-maxage=600')
  // browser caches for 5min, CDN for 10min
  res.json(config)
})

// Private user data — browser only, not CDN
app.get('/api/profile', requireAuth, (req, res) => {
  res.set('Cache-Control', 'private, max-age=60')
  res.json(req.user)
})

// Never cache
app.get('/api/live-price', (req, res) => {
  res.set('Cache-Control', 'no-store')
  res.json(getLivePrice())
})

// Conditional caching — ETag
app.get('/api/posts/:id', async (req, res) => {
  const post = await db.posts.findById(req.params.id)
  const etag = `"${post.updatedAt.getTime()}"`

  if (req.headers['if-none-match'] === etag) {
    return res.status(304).end()   // Not Modified — client uses cached version
  }

  res.set({
    'ETag': etag,
    'Cache-Control': 'public, max-age=0, must-revalidate'
  })
  res.json(post)
})
```

# TTL DESIGN GUIDE
```
Data type                    Recommended TTL
──────────────────────────────────────────
User session                 24h – 7 days
User profile                 1h – 4h
Product catalog              15min – 1h
Search results               5min – 15min
Live pricing/inventory       30s – 2min
Leaderboards/rankings        1min – 5min
Aggregated stats             5min – 1h
Feature flags                5min (poll)
Config/settings              15min – 1h
API rate limit windows       1min (sliding)

Rules:
- Shorter TTL = fresher data, more DB load
- Longer TTL = stale data risk, less load
- Popular + stable = longer TTL
- Personalized = shorter TTL or tag-based invalidation
- Financial/inventory = very short TTL or event-based
```
