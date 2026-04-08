---
name: Redis Advanced Patterns
trigger: redis, cache invalidation, redis pub/sub, redis streams, redis sorted sets, redis lua, redis cluster, redis sentinel, rate limiting redis, session store redis, leaderboard redis, distributed lock redis, ioredis, redis caching strategy
description: Use Redis beyond simple caching — covering data structures for real problems, pub/sub, streams, distributed locks, rate limiting, leaderboards, session management, and cluster architecture.
---

# ROLE
You are a senior backend engineer with deep Redis expertise. You know which data structure solves which problem, when Redis is the right tool, and how to operate it safely in production.

# DATA STRUCTURES — PICK THE RIGHT ONE
```
STRING:      Counters, simple cache, atomic values, JSON blobs
HASH:        Object fields — user profile, session, config (more memory-efficient than string-per-field)
LIST:        Queue, stack, activity feed, recent items
SET:         Unique memberships, tags, intersections (who's online, common followers)
SORTED SET:  Leaderboard, rate limit windows, priority queue, time-series index
STREAM:      Event log, message queue with consumer groups (Kafka-lite)
HyperLogLog: Approximate unique count (page views, unique users) — 12KB regardless of cardinality
Bitmap:      Bitwise ops — daily active users, feature flags per user ID
```

# CACHING PATTERNS

## Cache-Aside (Most Common)
```typescript
// Node.js with ioredis
async function getUser(userId: string): Promise<User> {
  const cacheKey = `user:${userId}`

  // 1. Check cache
  const cached = await redis.get(cacheKey)
  if (cached) return JSON.parse(cached)

  // 2. Miss — fetch from DB
  const user = await db.users.findById(userId)
  if (!user) throw new NotFoundError('User', userId)

  // 3. Populate cache with TTL
  await redis.setex(cacheKey, 3600, JSON.stringify(user))  // 1 hour TTL

  return user
}

// Invalidate on update
async function updateUser(userId: string, data: UserUpdate) {
  const user = await db.users.update(userId, data)
  await redis.del(`user:${userId}`)   // bust cache
  return user
}
```

## Write-Through Cache
```typescript
// Write to DB and cache atomically using pipeline
async function setUserProfile(userId: string, profile: Profile) {
  const pipeline = redis.pipeline()
  pipeline.setex(`profile:${userId}`, 86400, JSON.stringify(profile))
  pipeline.setex(`profile:updated:${userId}`, 86400, Date.now().toString())

  await Promise.all([
    db.profiles.upsert(userId, profile),
    pipeline.exec()
  ])
}
```

## Cache Stampede Prevention — Mutex Lock
```typescript
// Problem: 100 requests miss cache simultaneously, all hit DB
// Solution: only first request rebuilds, others wait

async function getCachedWithLock<T>(
  key: string,
  rebuild: () => Promise<T>,
  ttl: number
): Promise<T> {
  const cached = await redis.get(key)
  if (cached) return JSON.parse(cached)

  const lockKey = `lock:${key}`
  const lockAcquired = await redis.set(lockKey, '1', 'EX', 10, 'NX')  // NX = only if not exists

  if (lockAcquired) {
    try {
      const data = await rebuild()
      await redis.setex(key, ttl, JSON.stringify(data))
      return data
    } finally {
      await redis.del(lockKey)
    }
  } else {
    // Another process is rebuilding — wait and retry
    await new Promise(r => setTimeout(r, 100))
    return getCachedWithLock(key, rebuild, ttl)
  }
}
```

# DISTRIBUTED LOCK (Redlock)
```typescript
import Redlock from 'redlock'

const redlock = new Redlock([redis], {
  driftFactor: 0.01,
  retryCount: 3,
  retryDelay: 200,
  retryJitter: 100
})

async function processOrder(orderId: string) {
  const lock = await redlock.acquire([`lock:order:${orderId}`], 5000)  // 5s TTL
  try {
    // Only one instance processes this order at a time
    await doProcessOrder(orderId)
  } finally {
    await lock.release()  // always release even on error
  }
}
```

# RATE LIMITING WITH SORTED SETS
```typescript
// Sliding window rate limiter — precise, no edge-case spikes
async function isAllowed(userId: string, limit: number, windowMs: number): Promise<boolean> {
  const key = `ratelimit:${userId}`
  const now = Date.now()
  const windowStart = now - windowMs

  const pipeline = redis.pipeline()
  pipeline.zremrangebyscore(key, 0, windowStart)   // remove old entries
  pipeline.zadd(key, now, `${now}-${Math.random()}`)  // add current request
  pipeline.zcard(key)                               // count requests in window
  pipeline.expire(key, Math.ceil(windowMs / 1000))  // auto-cleanup

  const results = await pipeline.exec()
  const count = results![2][1] as number

  return count <= limit
}

// Usage
const allowed = await isAllowed(userId, 100, 60_000)  // 100 req/min
if (!allowed) throw new RateLimitError()
```

# LEADERBOARD WITH SORTED SETS
```typescript
// ZADD — O(log N) insert
// ZREVRANK — O(log N) rank lookup
// ZREVRANGE — O(log N + M) range query

// Add/update score
await redis.zadd('leaderboard:weekly', score, userId)

// Increment score
await redis.zincrby('leaderboard:weekly', pointsEarned, userId)

// Top 10
const top10 = await redis.zrevrange('leaderboard:weekly', 0, 9, 'WITHSCORES')

// Player rank (0-indexed)
const rank = await redis.zrevrank('leaderboard:weekly', userId)

// Player's score
const score = await redis.zscore('leaderboard:weekly', userId)

// Players around a given user (rank ± 2)
const rank = await redis.zrevrank('leaderboard:weekly', userId)
const nearby = await redis.zrevrange('leaderboard:weekly', rank - 2, rank + 2, 'WITHSCORES')
```

# PUB/SUB — REAL-TIME EVENTS
```typescript
// Publisher
async function publishUserEvent(event: UserEvent) {
  await redis.publish('user-events', JSON.stringify(event))
}

// Subscriber — needs a dedicated connection (subscribed connection can't do other commands)
const subscriber = redis.duplicate()  // separate connection

await subscriber.subscribe('user-events', 'order-events')

subscriber.on('message', (channel: string, message: string) => {
  const event = JSON.parse(message)
  switch(channel) {
    case 'user-events': handleUserEvent(event); break
    case 'order-events': handleOrderEvent(event); break
  }
})

// Pattern subscribe
await subscriber.psubscribe('user:*')
subscriber.on('pmessage', (pattern, channel, message) => {
  console.log(`Pattern ${pattern} matched ${channel}`)
})
```

# REDIS STREAMS — DURABLE MESSAGE QUEUE
```typescript
// Producer — append to stream
await redis.xadd('orders', '*', {  // * = auto-generate ID
  orderId: order.id,
  userId: order.userId,
  total: order.total.toString()
})

// Consumer group — each message processed by exactly one consumer
await redis.xgroup('CREATE', 'orders', 'processors', '$', 'MKSTREAM')

// Consumer — read and process
async function processMessages() {
  while (true) {
    const messages = await redis.xreadgroup(
      'GROUP', 'processors', 'worker-1',
      'COUNT', 10,
      'BLOCK', 1000,     // block 1s waiting for messages
      'STREAMS', 'orders', '>'  // > = only new/undelivered
    )

    for (const [stream, entries] of messages ?? []) {
      for (const [id, fields] of entries) {
        try {
          await handleOrder(Object.fromEntries(fields))
          await redis.xack('orders', 'processors', id)  // ack on success
        } catch (e) {
          // Message stays unacked — will be redelivered
          console.error(`Failed to process ${id}`, e)
        }
      }
    }
  }
}
```

# SESSION MANAGEMENT
```typescript
// Store session as Redis Hash (granular field access)
async function createSession(userId: string, metadata: SessionMeta): Promise<string> {
  const sessionId = crypto.randomUUID()
  const key = `session:${sessionId}`

  await redis.hset(key, {
    userId,
    ip: metadata.ip,
    userAgent: metadata.userAgent,
    createdAt: Date.now()
  })
  await redis.expire(key, 86400 * 7)  // 7-day TTL

  return sessionId
}

async function getSession(sessionId: string) {
  const session = await redis.hgetall(`session:${sessionId}`)
  if (!Object.keys(session).length) throw new Error('Session expired')
  return session
}

// Track all sessions per user (for "logout everywhere")
await redis.sadd(`sessions:user:${userId}`, sessionId)

async function logoutAll(userId: string) {
  const sessions = await redis.smembers(`sessions:user:${userId}`)
  const pipeline = redis.pipeline()
  sessions.forEach(id => pipeline.del(`session:${id}`))
  pipeline.del(`sessions:user:${userId}`)
  await pipeline.exec()
}
```

# PIPELINE + MULTI/EXEC
```typescript
// Pipeline — batch commands, single round trip (not atomic)
const pipeline = redis.pipeline()
pipeline.get('key1')
pipeline.get('key2')
pipeline.incr('counter')
const results = await pipeline.exec()  // [[null, val1], [null, val2], [null, 4]]

// MULTI/EXEC — atomic transaction
const result = await redis
  .multi()
  .decrby('stock:item-123', 1)
  .incr('sold:item-123')
  .exec()

if (result === null) {
  // Transaction aborted (WATCH key was modified)
}
```

# PRODUCTION CONFIG
```
maxmemory-policy allkeys-lru    # evict LRU keys when memory full (for cache)
# OR: volatile-lru              # only evict keys with TTL (preserve permanent keys)
maxmemory 2gb

save ""                          # disable RDB snapshots for pure cache
appendonly yes                   # enable AOF for durability

bind 127.0.0.1                   # never bind to 0.0.0.0 in production
requirepass your-strong-password
rename-command FLUSHALL ""       # disable dangerous commands
rename-command DEBUG ""
```

# COMMON MISTAKES TO AVOID
```
✗ No TTL on cached keys — memory fills up, never evicts stale data
✗ Using KEYS * in production — O(N), blocks server while scanning
  → Use SCAN with cursor instead: redis.scan(cursor, 'MATCH', 'user:*', 'COUNT', 100)
✗ Storing huge values (>1MB) in Redis — use blob storage + Redis for metadata
✗ Using a single Redis connection for pub/sub AND commands — they need separate connections
✗ JSON.parse without try/catch — corrupted cache hits will crash
✗ Not setting maxmemory-policy — Redis will crash when OOM if unconfigured
✗ Using MULTI/EXEC for high-contention counters — INCR is already atomic, use that
✗ Ignoring Redis slowlog — run SLOWLOG GET 25 regularly to catch O(N) ops
```
