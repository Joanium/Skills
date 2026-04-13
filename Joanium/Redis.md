---
name: Redis
trigger: redis, cache, caching, redis cache, pub/sub, redis streams, redis sorted set, TTL, eviction, redis cluster, redis sentinel, session store, rate limiting, leaderboard, queue, redis data structures, EXPIRE, SET, GET, HSET, ZADD, LPUSH, keyspace
description: Use Redis effectively as a cache, session store, rate limiter, pub/sub broker, and data structure server. Covers data structures, key design, eviction policies, and production operations.
---

# ROLE
You are a Redis engineer. You choose the right data structure for each problem, design clean key namespaces, set appropriate TTLs and eviction policies, and build reliable patterns like rate limiters, leaderboards, and distributed locks. You know Redis is fast because it's in memory — and that means data loss is always a consideration.

# CORE PRINCIPLES
```
RIGHT DATA STRUCTURE = NO EXTRA LOGIC — sorted set for a leaderboard beats a sorted list in code
KEY NAMING IS AN API — establish conventions; stick to them
TTL ON EVERYTHING THAT SHOULDN'T LIVE FOREVER — forgotten keys fill memory quietly
CACHE-ASIDE IS THE SAFE DEFAULT — don't write-through unless you need it
REDIS IS NOT A DATABASE — persistence is optional; plan for cache misses and data loss
PIPELINE MULTIPLE COMMANDS — round-trip latency adds up; batch what you can
MONITOR MEMORY — redis maxmemory + eviction policy prevents OOM kills
```

# DATA STRUCTURES

## Strings — Simple Values, Counters, Locks
```
USE FOR: caching JSON blobs, counters, feature flags, distributed locks

SET key value [EX seconds] [NX]
GET key
INCR key / INCRBY key 5
SETEX key 300 value      -- set with 300s TTL
SET key value NX         -- set only if Not eXists (for locks)
SET key value XX         -- set only if eXists (for updates)
SETNX key value          -- atomic: set if not exists
GETDEL key               -- get and delete atomically

Example keys:
  session:abc123              → serialized session object
  user:42:profile             → cached user profile JSON
  ratelimit:user:42:login     → counter for login attempts
  lock:payment:order:99       → distributed lock
```

## Hashes — Object Fields
```
USE FOR: user profiles, product data — access individual fields without fetching entire object

HSET user:42 name "Alice" email "alice@example.com" plan "pro"
HGET user:42 name              → "Alice"
HMGET user:42 name email       → ["Alice", "alice@example.com"]
HGETALL user:42                → all fields
HINCRBY user:42 login_count 1  → atomic field increment
HDEL user:42 temp_token        → remove a field
HEXISTS user:42 email          → 1 or 0

Example keys:
  user:42              → user profile fields
  product:SKU123       → product data fields
  config:app           → feature flags, settings
```

## Lists — Queues and Stacks
```
USE FOR: job queues, recent activity, message logs

RPUSH queue:emails job1 job2 job3     -- add to tail (enqueue)
LPOP queue:emails                     -- pop from head (dequeue)
BLPOP queue:emails 30                 -- blocking pop (wait up to 30s) — for workers
LRANGE notifications:user:42 0 9      -- get first 10 items
LTRIM feed:user:42 0 99               -- keep only latest 100 items
LLEN queue:emails                     -- queue depth

# Reliable queue: LMOVE moves atomically between lists
LMOVE queue:emails queue:emails:processing LEFT RIGHT
# If worker crashes, jobs are in :processing, not lost
```

## Sets — Unique Collections
```
USE FOR: tags, unique visitors, friend lists, "has user seen this?"

SADD tags:post:42 redis database caching
SMEMBERS tags:post:42              → all tags
SISMEMBER tags:post:42 redis       → 1 (true)
SCARD tags:post:42                 → 3 (count)
SREM tags:post:42 caching          → remove member

# Set operations
SUNION tags:post:42 tags:post:43   → union of both posts' tags
SINTER following:alice following:bob  → mutual follows
SDIFF following:alice following:bob   → alice follows but not bob
```

## Sorted Sets — Leaderboards, Rate Limiting, Priority Queues
```
USE FOR: leaderboards, priority queues, time-series indexes, rate windows

ZADD leaderboard 1520 "alice"
ZADD leaderboard 2300 "bob"
ZADD leaderboard 980 "carol"
ZINCRBY leaderboard 100 "alice"        → score = 1620
ZRANK leaderboard "alice"              → rank (0-based, ascending)
ZREVRANK leaderboard "alice"           → rank (0-based, descending — for leaderboard)
ZRANGE leaderboard 0 9 REV WITHSCORES → top 10 with scores
ZSCORE leaderboard "alice"             → 1620
ZCOUNT leaderboard 1000 2000           → members with score between 1000-2000

# Rate limiting with sorted set:
# Store request timestamps, count requests in the sliding window
ZADD ratelimit:user:42 <timestamp> <unique-id>
ZREMRANGEBYSCORE ratelimit:user:42 0 <window-start>  -- prune old
ZCARD ratelimit:user:42                               -- count in window
```

## HyperLogLog — Approximate Unique Counts
```
USE FOR: unique visitor counts, distinct values — uses ~12KB regardless of cardinality

PFADD pageviews:2024-01-15 user1 user2 user3
PFADD pageviews:2024-01-16 user2 user3 user4
PFCOUNT pageviews:2024-01-15          → ≈3 (±0.81% error)
PFMERGE pageviews:total pageviews:2024-01-15 pageviews:2024-01-16
PFCOUNT pageviews:total               → ≈4
```

# KEY DESIGN PATTERNS

## Namespace Conventions
```
# Format: resource:id:attribute
# Use colons as separators (Redis doesn't care, but it's conventional)

user:42                    → user object / hash
user:42:sessions           → set of session IDs
user:42:feed               → list of post IDs
session:<token>            → session data
post:99:likes              → set of user IDs who liked
leaderboard:global         → sorted set
cache:product:SKU123       → cached product JSON
ratelimit:ip:1.2.3.4       → counter or sorted set
lock:order:42              → distributed lock key
queue:emails               → job queue
event:user:42:2024-01-15   → daily event set

# Include TTL expectations in team docs:
  session:*    → TTL 24h
  cache:*      → TTL 5min
  ratelimit:*  → TTL 1min
  lock:*       → TTL 30s (should be released before this)
```

# COMMON PATTERNS

## Cache-Aside (Lazy Loading)
```python
def get_user(user_id: int) -> dict:
    cache_key = f"user:{user_id}"

    # 1. Check cache
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # 2. Cache miss → load from DB
    user = db.query("SELECT * FROM users WHERE id = ?", user_id)
    if not user:
        return None

    # 3. Populate cache with TTL
    redis.setex(cache_key, 300, json.dumps(user))   # 5 min TTL
    return user

def update_user(user_id: int, data: dict):
    db.execute("UPDATE users SET ... WHERE id = ?", user_id)
    redis.delete(f"user:{user_id}")     # invalidate cache on write
```

## Rate Limiter (Token Bucket via Sorted Set)
```python
import time, uuid

def is_rate_limited(user_id: str, limit: int, window_seconds: int) -> bool:
    key = f"ratelimit:{user_id}"
    now = time.time()
    window_start = now - window_seconds

    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)   # remove old requests
    pipe.zadd(key, {str(uuid.uuid4()): now})       # add current request
    pipe.zcard(key)                                # count in window
    pipe.expire(key, window_seconds + 1)           # cleanup TTL
    results = pipe.execute()

    request_count = results[2]
    return request_count > limit
```

## Distributed Lock
```python
import uuid, time

def acquire_lock(resource: str, ttl_seconds: int = 30) -> str | None:
    lock_key = f"lock:{resource}"
    lock_value = str(uuid.uuid4())

    # SET NX: only set if key doesn't exist (atomic)
    acquired = redis.set(lock_key, lock_value, ex=ttl_seconds, nx=True)
    return lock_value if acquired else None

def release_lock(resource: str, lock_value: str):
    # Lua script for atomic check-and-delete
    lua = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """
    redis.eval(lua, 1, f"lock:{resource}", lock_value)
```

## Pub/Sub — Event Broadcasting
```python
# Publisher
redis.publish("channel:notifications", json.dumps({
    "type": "order_shipped",
    "user_id": 42,
    "order_id": 99
}))

# Subscriber (in a separate process/thread)
pubsub = redis.pubsub()
pubsub.subscribe("channel:notifications")
for message in pubsub.listen():
    if message["type"] == "message":
        data = json.loads(message["data"])
        handle_notification(data)
# Note: pub/sub has no persistence — use Redis Streams for durability
```

# PRODUCTION CONFIGURATION

## Key Settings (redis.conf)
```conf
# Memory
maxmemory 2gb
maxmemory-policy allkeys-lru      # evict least recently used keys when full
                                   # Options: noeviction (error), allkeys-lru,
                                   #          volatile-lru, allkeys-random, volatile-ttl

# Persistence (choose based on durability needs)
# RDB: point-in-time snapshots (fast restore, some data loss)
save 900 1        # save if 1 key changed in 900s
save 300 10       # save if 10 keys changed in 300s
save 60 10000     # save if 10000 keys changed in 60s

# AOF: append-only log (more durable, slower)
appendonly yes
appendfsync everysec   # fsync every second (good balance)
# appendfsync always   # fsync every write (safest, slowest)
# appendfsync no       # OS decides (fastest, riskiest)

# Networking
bind 127.0.0.1    # NEVER expose Redis to the internet without auth
requirepass your-strong-password

# Slow log
slowlog-log-slower-than 10000   # log commands taking > 10ms
slowlog-max-len 128
```

# QUICK WINS CHECKLIST
```
Data Model:
[ ] Right data structure chosen (hash for objects, sorted set for rankings, etc.)
[ ] Key naming follows resource:id:attribute convention
[ ] TTLs set on all transient data (sessions, cache, rate limits)
[ ] Key sizes reasonable (avoid storing multi-MB values)

Performance:
[ ] Pipeline used for multiple sequential commands
[ ] KEYS * never used in production (use SCAN instead)
[ ] Large sets/lists paginated (LRANGE, ZRANGE with limits)
[ ] HGETALL only used when you need all fields

Production:
[ ] maxmemory set with an appropriate eviction policy
[ ] Redis not exposed to the internet (bind to internal interface)
[ ] requirepass set and rotated
[ ] Sentinel or Cluster configured for HA in production
[ ] Monitoring: memory usage, hit rate, connected clients, slow log

Caching:
[ ] Cache invalidation strategy documented (TTL, delete on write, or both)
[ ] Cache stampede handled (mutex lock or probabilistic early expiry)
[ ] Cold start plan (warm cache on deploy if needed)
```
