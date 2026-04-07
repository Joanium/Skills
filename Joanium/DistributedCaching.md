---
name: Distributed Caching
trigger: distributed cache, redis cache, memcached, cache invalidation, cache strategy, cache warming, cache stampede, cache consistency
description: Design distributed caching strategies using Redis, Memcached, or similar. Covers cache invalidation patterns, cache stampede prevention, consistency, and cache warming. Use when implementing caching layers, optimizing read performance, or managing distributed caches.
---

# ROLE
You are a performance engineer specializing in distributed caching. Your job is to design caching strategies that dramatically reduce latency and database load while maintaining data consistency.

# CACHE PATTERNS

## Cache-Aside (Lazy Loading)
```typescript
async function getUser(id: string): Promise<User> {
  // 1. Check cache
  const cached = await redis.get(`user:${id}`)
  if (cached) return JSON.parse(cached)
  
  // 2. Cache miss — load from database
  const user = await db.user.findUnique({ where: { id } })
  if (!user) throw new NotFoundError()
  
  // 3. Populate cache
  await redis.setex(`user:${id}`, 3600, JSON.stringify(user))
  
  return user
}
```

## Write-Through
```typescript
async function updateUser(id: string, data: UpdateUserInput): Promise<User> {
  // Write to both cache and database simultaneously
  const user = await db.user.update({ where: { id }, data })
  await redis.setex(`user:${id}`, 3600, JSON.stringify(user))
  return user
}
```

## Write-Behind (Write-Back)
```typescript
// Write to cache immediately, async flush to database
const writeQueue = new Map<string, any>()
let flushTimer: NodeJS.Timeout

async function updateUser(id: string, data: UpdateUserInput) {
  const user = { id, ...data, updatedAt: new Date() }
  
  // Update cache immediately
  await redis.setex(`user:${id}`, 3600, JSON.stringify(user))
  
  // Queue for async database write
  writeQueue.set(id, user)
  
  // Batch flush every 5 seconds
  if (!flushTimer) {
    flushTimer = setTimeout(flushToDatabase, 5000)
  }
}

async function flushToDatabase() {
  const updates = Array.from(writeQueue.entries())
  writeQueue.clear()
  flushTimer = undefined
  
  for (const [id, user] of updates) {
    await db.user.update({ where: { id }, data: user })
  }
}
```

# CACHE INVALIDATION
```
There are only two hard things in Computer Science:
cache invalidation and naming things. — Phil Karlton

Strategies:
1. TTL (Time-To-Live) → Expire after fixed duration
2. Explicit delete  → Invalidate on write
3. Versioned keys    → Change key version on invalidation
4. Tag-based         → Invalidate by tag/group
```

```typescript
// TTL-based
await redis.setex(`user:${id}`, 3600, JSON.stringify(user))

// Explicit invalidation on write
async function updateUser(id: string, data: UpdateUserInput) {
  const user = await db.user.update({ where: { id }, data })
  await redis.setex(`user:${id}`, 3600, JSON.stringify(user))
  // Also invalidate related caches
  await redis.del(`user:${id}:orders`)
  await redis.del(`user:${id}:preferences`)
}

// Versioned keys
async function getUser(id: string): Promise<User> {
  const version = await redis.get(`user:${id}:version`) || '1'
  const cached = await redis.get(`user:${id}:v${version}`)
  if (cached) return JSON.parse(cached)
  
  const user = await db.user.findUnique({ where: { id } })
  await redis.setex(`user:${id}:v${version}`, 3600, JSON.stringify(user))
  return user
}

async function invalidateUser(id: string) {
  const version = await redis.get(`user:${id}:version`) || '1'
  await redis.del(`user:${id}:v${version}`)
  await redis.set(`user:${id}:version`, String(parseInt(version) + 1))
}
```

# CACHE STAMPEDE PREVENTION
```typescript
// Problem: Cache expires, 1000 requests hit DB simultaneously

// Solution 1: Locking (single request rebuilds cache)
async function getUserWithLock(id: string): Promise<User> {
  const cached = await redis.get(`user:${id}`)
  if (cached) return JSON.parse(cached)
  
  const lock = await redis.set(`lock:user:${id}`, '1', 'EX', 10, 'NX')
  if (!lock) {
    // Another request is rebuilding — wait and retry
    await sleep(100)
    return getUserWithLock(id)
  }
  
  try {
    const user = await db.user.findUnique({ where: { id } })
    await redis.setex(`user:${id}`, 3600, JSON.stringify(user))
    return user
  } finally {
    await redis.del(`lock:user:${id}`)
  }
}

// Solution 2: Probabilistic early expiration
async function getUserProbabilistic(id: string): Promise<User> {
  const cached = await redis.get(`user:${id}`)
  if (!cached) return await fetchAndCache(id)
  
  const user = JSON.parse(cached)
  const ttl = await redis.ttl(`user:${id}`)
  
  // If less than 10% TTL remaining, refresh in background
  if (ttl < 360) {
    refreshCacheInBackground(id) // Don't await
  }
  
  return user
}
```

# CACHE WARMING
```typescript
// Pre-populate cache after deployment
async function warmCache() {
  const popularUsers = await db.user.findMany({
    orderBy: { lastActive: 'desc' },
    take: 1000
  })
  
  const pipeline = redis.pipeline()
  for (const user of popularUsers) {
    pipeline.setex(`user:${user.id}`, 3600, JSON.stringify(user))
  }
  await pipeline.exec()
}
```

# REVIEW CHECKLIST
```
[ ] Cache strategy chosen per use case (aside, through, behind)
[ ] TTL values appropriate for data freshness needs
[ ] Cache stampede prevention implemented
[ ] Invalidation strategy defined for each cache entry
[ ] Cache warming configured for critical data
[ ] Cache miss fallback to database
[ ] Monitoring for hit/miss ratio
[ ] Memory limits and eviction policy set
```
