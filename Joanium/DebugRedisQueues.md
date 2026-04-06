---
name: Debug — Redis / Queues
trigger: redis error, redis not working, redis connection refused, redis memory, redis slow, bull queue, bullmq, celery redis, queue not processing, jobs stuck, redis cache wrong, pubsub not working, redis timeout, queue backlog
description: Hyper-specific debugging guide for Redis, BullMQ/Bull, and message queues. Real commands, real errors, real fixes. Covers connection issues, memory problems, cache bugs, queue stalls, and performance.
---

# Debug — Redis / Queues

---

# REDIS

## First Move

```bash
# Connect to Redis CLI
redis-cli                          # local default
redis-cli -h host -p 6379          # remote
redis-cli -h host -p 6379 -a password  # with auth
redis-cli -u redis://user:password@host:6379  # URL format

# Check Redis is alive and responding
redis-cli ping  # should return PONG

# Server info — version, memory, connections, stats
redis-cli info server
redis-cli info memory    # memory breakdown
redis-cli info clients   # connected clients
redis-cli info stats     # operations per second

# See all active client connections
redis-cli client list

# Monitor ALL commands in real-time (use carefully — heavy in production)
redis-cli monitor | head -50  # stop after 50 lines

# Slow log — find slow commands
redis-cli slowlog get 10           # last 10 slow commands
redis-cli slowlog reset            # reset
redis-cli config set slowlog-log-slower-than 10000  # log commands > 10ms
```

---

## Connection Issues

```bash
# "Connection refused" — Redis not running or wrong port
redis-cli ping
systemctl status redis
# Or if Docker:
docker ps | grep redis
docker logs redis-container

# "NOAUTH Authentication required"
redis-cli -a yourpassword ping
# In app config: add password to connection URL
REDIS_URL=redis://:password@localhost:6379

# "ERR max number of clients reached"
redis-cli info clients
# maxclients — Redis default is 10000
redis-cli config get maxclients
redis-cli config set maxclients 20000  # increase (temporary — also set in redis.conf)

# Connection pool exhausted (Node.js/Python app)
# Problem: app opens more connections than pool allows
# Fix: configure pool size correctly
# ioredis:
const redis = new Redis({
  host: 'localhost',
  port: 6379,
  maxRetriesPerRequest: 3,
  lazyConnect: true,
})
# Never create a new Redis instance per request — reuse one client

# Connection timeout in Kubernetes/Docker
# Redis inside cluster: use service name, not localhost
REDIS_HOST=redis-service  # not localhost
REDIS_URL=redis://redis-service:6379
```

---

## Memory Issues

```bash
# Check memory usage
redis-cli info memory
# used_memory_human: 1.50G         ← current usage
# used_memory_peak_human: 2.00G    ← peak
# mem_fragmentation_ratio: 1.5     ← ratio > 1.5 = fragmentation problem

# See memory per key pattern (top 10 largest key patterns)
redis-cli --memkeys | sort -t: -k2 -rn | head -10
# Or scan for large keys:
redis-cli --bigkeys

# Check memory limit and eviction policy
redis-cli config get maxmemory
redis-cli config get maxmemory-policy

# Eviction policies:
# noeviction    → returns error when memory full (default — bad for cache)
# allkeys-lru   → evicts least-recently-used key (best for pure cache)
# volatile-lru  → evicts LRU key with TTL set (balanced)
# allkeys-lfu   → evicts least-frequently-used (good for skewed access)

# Set a memory limit and policy (also set in redis.conf for persistence)
redis-cli config set maxmemory 2gb
redis-cli config set maxmemory-policy allkeys-lru

# Keys without TTL consuming memory
redis-cli --scan --pattern '*' | while read key; do
  ttl=$(redis-cli ttl "$key")
  if [ "$ttl" -eq -1 ]; then
    echo "No TTL: $key ($(redis-cli memory usage "$key") bytes)"
  fi
done
# Fix: set TTL on keys that should expire
redis-cli expire key_name 3600  # expire in 1 hour
```

---

## Cache Bugs

### Cache Returns Stale / Wrong Data

```bash
# Check what's actually in Redis
redis-cli get "user:123"
redis-cli hgetall "user:123:profile"

# Check TTL
redis-cli ttl "user:123"  # -1 = no TTL, -2 = key doesn't exist, positive = seconds remaining

# Manually delete a cached key to force refresh
redis-cli del "user:123"
redis-cli del "user:123" "user:124" "user:125"  # multiple keys

# Delete by pattern (careful — KEYS is blocking, use SCAN in production)
# Development only:
redis-cli keys "user:*" | xargs redis-cli del

# Production-safe deletion by pattern:
redis-cli --scan --pattern "user:*" | xargs -L 100 redis-cli del
```

### Cache Miss Rate Too High

```bash
# Check hit/miss ratio
redis-cli info stats | grep -E "keyspace_hits|keyspace_misses"
# keyspace_hits:100000
# keyspace_misses:50000
# Hit rate = hits / (hits + misses) = 66% — below 90% is a problem

# Check if keys are expiring too fast
redis-cli info keyspace
# db0:keys=5000,expires=4900,avg_ttl=3600  ← nearly all keys have TTL

# Monitor which keys are being missed
redis-cli monitor | grep "nil"  # nil response = cache miss
```

---

## Race Conditions / Atomicity

```bash
# Problem: two processes both check-then-set, causing a race
# Fix: use atomic Redis operations

# Atomic increment (no race)
redis-cli incr counter
redis-cli incrby counter 5

# Set only if not exists (atomic lock)
redis-cli set lock:user123 "locked" NX EX 30
# NX = only set if doesn't exist
# EX = expire in 30 seconds
# Returns "OK" if locked, nil if already locked

# Atomic compare-and-swap with Lua script
redis-cli eval "
  if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('set', KEYS[1], ARGV[2])
  else
    return 0
  end
" 1 "mykey" "oldvalue" "newvalue"

# MULTI/EXEC transaction — watch + execute atomically
redis-cli
WATCH balance:user123
MULTI
DECRBY balance:user123 100
INCRBY balance:user123:escrow 100
EXEC  # aborts if balance:user123 changed since WATCH
```

---

## Pub/Sub Debugging

```bash
# Subscribe to a channel (blocks, watching for messages)
redis-cli subscribe my-channel

# Publish a test message
redis-cli publish my-channel "test-message"

# Subscribe to pattern (multiple channels)
redis-cli psubscribe "user:*:notifications"

# Check how many clients are subscribed
redis-cli pubsub channels "*"     # list all active channels
redis-cli pubsub numsub my-channel  # subscriber count for specific channel

# Common issue: messages lost during subscriber restart
# Pub/Sub is fire-and-forget — no persistence, no delivery guarantee
# If you need delivery guarantees, use Redis Streams instead:
redis-cli xadd mystream '*' field value  # append to stream
redis-cli xreadgroup GROUP mygroup consumer1 COUNT 10 STREAMS mystream '>'  # consume
```

---

# BULLMQ / BULL (Node.js)

## First Move

```javascript
// Check queue depth and job states
const { Queue, QueueEvents } = require('bullmq')
const queue = new Queue('myQueue', { connection: redisConfig })

const counts = await queue.getJobCounts()
console.log(counts)
// { waiting: 100, active: 5, completed: 1000, failed: 23, delayed: 0, paused: 0 }

// See failed jobs
const failedJobs = await queue.getFailed(0, 20)  // first 20 failed jobs
for (const job of failedJobs) {
  console.log({
    id: job.id,
    name: job.name,
    data: job.data,
    failedReason: job.failedReason,
    stacktrace: job.stacktrace
  })
}

// See what active workers are doing
const workers = await queue.getWorkers()
console.log(workers)
```

---

## Jobs Stuck in Active State

```javascript
// Jobs stuck in "active" = worker crashed or stalled
// BullMQ moves stalled jobs back to waiting after stalledInterval

// Check stalled jobs
const stalled = await queue.getActive()
const stalledIds = await Promise.all(
  stalled.map(async job => {
    const token = await job.isFailed()
    return token ? job.id : null
  })
)

// Configure stall detection
const worker = new Worker('myQueue', processor, {
  connection: redisConfig,
  stalledInterval: 30000,   // check for stalls every 30s
  maxStalledCount: 2,       // move to failed after 2 stalls
  lockDuration: 30000,      // job lock expires after 30s if worker dies
})

// Fix: reduce job processing time or increase lockDuration
// Long-running jobs must renew their lock:
const worker = new Worker('myQueue', async (job) => {
  for (const chunk of chunks) {
    await processChunk(chunk)
    await job.updateProgress(progress)  // also renews the lock
  }
})
```

---

## Jobs Failing — Debug

```javascript
// See the failure reason + stacktrace
const job = await queue.getJob(jobId)
console.log('Failed reason:', job.failedReason)
console.log('Stacktrace:', job.stacktrace)
console.log('Attempt:', job.attemptsMade, '/', job.opts.attempts)

// Retry all failed jobs
const failedJobs = await queue.getFailed()
for (const job of failedJobs) {
  await job.retry()
}

// Retry a specific job
const job = await queue.getJob(jobId)
await job.retry()

// Configure retries with backoff
const queue = new Queue('myQueue', { connection })
await queue.add('sendEmail', { to: 'user@example.com' }, {
  attempts: 5,
  backoff: {
    type: 'exponential',
    delay: 1000  // 1s, 2s, 4s, 8s, 16s
  }
})

// Add error handling in the processor
const worker = new Worker('myQueue', async (job) => {
  try {
    await sendEmail(job.data)
  } catch (error) {
    // Decide: should this be retried or is it permanent failure?
    if (error.code === 'INVALID_EMAIL') {
      throw new UnrecoverableError('Invalid email — do not retry: ' + error.message)
    }
    throw error  // retriable error — BullMQ will retry per your config
  }
}, { connection })
```

---

## Queue Not Processing (Worker Dead)

```javascript
// Check if workers are actually running
const workers = await queue.getWorkers()
console.log('Active workers:', workers.length)

// Listen to worker events for diagnosis
const worker = new Worker('myQueue', processor, { connection })

worker.on('completed', (job) => {
  console.log(`Job ${job.id} completed`)
})
worker.on('failed', (job, err) => {
  console.error(`Job ${job?.id} failed:`, err.message)
})
worker.on('error', (err) => {
  console.error('Worker error:', err)  // Redis connection issues show here
})
worker.on('stalled', (jobId) => {
  console.warn(`Job ${jobId} stalled`)
})

// BullMQ dashboard — use Bull Board for visual queue monitoring
const { createBullBoard } = require('@bull-board/api')
const { BullMQAdapter } = require('@bull-board/api/bullMQAdapter')
const { ExpressAdapter } = require('@bull-board/express')

const serverAdapter = new ExpressAdapter()
createBullBoard({
  queues: [new BullMQAdapter(queue)],
  serverAdapter
})
app.use('/admin/queues', serverAdapter.getRouter())
```

---

## Redis Streams (Reliable Queues)

```bash
# Add messages to a stream
redis-cli xadd orders '*' user_id 123 product_id 456 quantity 2
# Returns: "1703000000000-0"  (timestamp-sequence ID)

# Create consumer group
redis-cli xgroup create orders myapp $ MKSTREAM

# Read new messages as a consumer
redis-cli xreadgroup GROUP myapp worker1 COUNT 10 BLOCK 2000 STREAMS orders '>'
# BLOCK 2000 = wait up to 2s for new messages

# Acknowledge processed message (removes from pending list)
redis-cli xack orders myapp 1703000000000-0

# See pending (unacknowledged) messages
redis-cli xpending orders myapp - + 10
# Shows: message ID, consumer, idle time, delivery count

# Reclaim messages idle > 30 seconds (worker crashed without acking)
redis-cli xautoclaim orders myapp recovered 30000 0-0
```
