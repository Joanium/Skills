---
name: Error Handling & Resiliency
trigger: error handling, resilience, retry logic, circuit breaker, graceful degradation, timeout, fallback, rate limiting, queue failure, partial failure, fault tolerance, bulkhead, dead letter queue, idempotency
description: Fourteenth skill in the build pipeline. Covers building systems that handle failure gracefully — retry strategies, circuit breakers, timeout patterns, graceful degradation, idempotency, and recovering from partial failures without data corruption.
prev_skill: 13-MonitoringObservability.md
next_skill: 15-CodeReviewDocumentation.md
---

# ROLE
You are a reliability engineer who understands that distributed systems fail — networks partition, third-party APIs go down, databases get slow. Your job is to make the system degrade gracefully rather than fail catastrophically. You design for failure, not just for the happy path.

# CORE PRINCIPLES
```
EXPECT FAILURE — every network call can fail; every service can be slow; disks fill up
FAIL FAST — detect failures quickly; don't let callers wait indefinitely
DEGRADE GRACEFULLY — when a feature fails, serve a degraded experience, not an error page
IDEMPOTENCY — processing a message twice must produce the same result as processing it once
BULKHEADS — isolate failures; a slow external API must not exhaust your main thread pool
TIMEOUTS ON EVERYTHING — no call should be allowed to wait forever
```

# STEP 1 — TIMEOUT STRATEGY

```typescript
// RULE: Every external call MUST have a timeout. No exceptions.

// HTTP requests:
import axios from 'axios'

const externalApiClient = axios.create({
  baseURL: 'https://api.external.com',
  timeout: 5_000,  // 5 second timeout — external APIs can be slow
})

// Database queries (Prisma):
// Set at connection level:
const db = new PrismaClient({
  datasources: { db: { url: `${DATABASE_URL}&connect_timeout=10&socket_timeout=10` } }
})

// Redis operations:
const redis = new Redis({
  host: env.REDIS_HOST,
  commandTimeout: 1_000,  // 1 second — Redis should always be fast; if not, something is wrong
  connectTimeout: 5_000,
})

// Generic timeout wrapper (use for any async operation):
export function withTimeout<T>(
  promise: Promise<T>,
  ms: number,
  label: string
): Promise<T> {
  const timeout = new Promise<never>((_, reject) =>
    setTimeout(() => reject(new Error(`${label} timed out after ${ms}ms`)), ms)
  )
  return Promise.race([promise, timeout])
}

// Usage:
const user = await withTimeout(
  userService.findById(userId),
  3_000,
  'findUser'
)

// TIMEOUT BUDGET:
//   External APIs (Stripe, SendGrid, Twilio): 10 seconds
//   Your own services: 2-3 seconds
//   Database queries: 5 seconds (< 1s for indexed reads)
//   Redis: 500ms (if Redis takes > 1s, you have a problem)
//   File system: 5 seconds
```

# STEP 2 — RETRY STRATEGY

```typescript
// WHEN TO RETRY:
//   ✅ Transient errors: network timeouts, 503/429 responses, connection resets
//   ❌ Never retry: 400, 401, 403, 404, 422 — these are permanent failures

import retry from 'async-retry'

async function callExternalAPI(payload: unknown) {
  return retry(async (bail, attempt) => {
    try {
      return await externalApiClient.post('/endpoint', payload)
    } catch (err) {
      const status = err.response?.status

      // Permanent failure — don't retry:
      if (status && status >= 400 && status < 500 && status !== 429) {
        bail(err)  // bail() stops retrying immediately
        return
      }

      logger.warn({ err, attempt }, 'External API call failed, retrying...')
      throw err  // throw to trigger retry
    }
  }, {
    retries: 3,
    factor:  2,                // exponential: 1s, 2s, 4s
    minTimeout: 1_000,
    maxTimeout: 10_000,
    randomize: true,           // add jitter to prevent thundering herd
    onRetry: (err, attempt) => {
      logger.warn({ err: err.message, attempt }, 'Retrying after error')
    }
  })
}

// RETRY IN BULLMQ (background jobs):
const queue = new Queue('email', { connection: redis })

// Job configuration with retry:
await queue.add('send-welcome-email', { userId }, {
  attempts: 5,
  backoff: {
    type: 'exponential',
    delay: 2_000,  // 2s, 4s, 8s, 16s, 32s
  },
  removeOnComplete: { count: 1000 },  // keep last 1000 completed
  removeOnFail:     { count: 5000 },  // keep last 5000 failed for debugging
})

// DEAD LETTER QUEUE — jobs that fail after all retries:
const worker = new Worker('email', async (job) => {
  await sendEmail(job.data)
}, { connection: redis })

worker.on('failed', async (job, err) => {
  if (job!.attemptsMade >= job!.opts.attempts!) {
    // All retries exhausted — move to dead letter queue for manual review
    await deadLetterQueue.add('email-dlq', {
      originalJob: job!.data,
      error: err.message,
      failedAt: new Date().toISOString(),
    })
    logger.error({ jobId: job!.id, err }, 'Job moved to dead letter queue')
  }
})
```

# STEP 3 — CIRCUIT BREAKER

```typescript
// Circuit breaker: stop calling a service that's failing; let it recover
// States: CLOSED (normal) → OPEN (failing, stop calling) → HALF-OPEN (test recovery)

import CircuitBreaker from 'opossum'

const transcodeBreaker = new CircuitBreaker(callTranscodeService, {
  timeout:         10_000,   // if call takes > 10s, trigger failure
  errorThresholdPercentage: 50,  // open circuit if > 50% of calls fail
  resetTimeout:    30_000,   // try again after 30s (half-open)
  volumeThreshold: 5,        // need at least 5 calls before calculating percentage
})

transcodeBreaker.on('open',     () => logger.warn('Transcode circuit OPEN — stopping calls'))
transcodeBreaker.on('halfOpen', () => logger.info('Transcode circuit HALF-OPEN — testing'))
transcodeBreaker.on('close',    () => logger.info('Transcode circuit CLOSED — service recovered'))

// Use the breaker instead of calling directly:
async function requestTranscode(videoId: string) {
  try {
    return await transcodeBreaker.fire(videoId)
  } catch (err) {
    if (transcodeBreaker.opened) {
      // Circuit is open — service is down, provide fallback:
      logger.warn({ videoId }, 'Transcode service unavailable — queuing for later')
      await retryQueue.add('transcode-retry', { videoId }, { delay: 60_000 })
      return { status: 'queued', message: 'Transcoding queued — will retry shortly' }
    }
    throw err
  }
}
```

# STEP 4 — GRACEFUL DEGRADATION

```typescript
// PRINCIPLE: When a non-critical feature fails, serve the page without it.
//            When a critical feature fails, show a meaningful error.

// EXAMPLE: Homepage feed — recommendations are non-critical
async function getHomepageFeed(userId?: string) {
  const [videos, recommendations] = await Promise.allSettled([
    videoRepo.getTrending(),           // critical
    recommendationService.get(userId), // non-critical — AI service might be down
  ])

  return {
    videos: videos.status === 'fulfilled' ? videos.value : [],  // if this fails, big problem
    recommendations: recommendations.status === 'fulfilled'
      ? recommendations.value
      : [],  // silently degrade — show trending instead of personalized
  }
}

// EXAMPLE: Video page — comments are non-critical
async function getVideoPage(videoId: string) {
  const video = await videoRepo.findById(videoId)  // critical — fail if this fails
  if (!video) throw new NotFoundError('Video')

  let comments = []
  try {
    comments = await withTimeout(commentService.getByVideo(videoId), 2_000, 'comments')
  } catch (err) {
    logger.warn({ err, videoId }, 'Failed to load comments — degrading gracefully')
    // comments stays [] — page renders without comments, with a "Comments unavailable" message
  }

  return { video, comments, commentsAvailable: comments.length > 0 }
}

// CACHE AS FALLBACK — serve stale data when upstream is down:
async function getChannelWithFallback(channelId: string) {
  try {
    const channel = await withTimeout(channelRepo.findById(channelId), 2_000, 'channel')
    await redis.setex(`channel:${channelId}`, 300, JSON.stringify(channel))
    return channel
  } catch (err) {
    // Upstream failed — serve stale cache:
    const cached = await redis.get(`channel:${channelId}`)
    if (cached) {
      logger.warn({ channelId }, 'Serving stale cache due to DB unavailability')
      return JSON.parse(cached)
    }
    throw err  // no cache either — re-throw
  }
}
```

# STEP 5 — IDEMPOTENCY

```typescript
// IDEMPOTENCY: processing the same request twice = same result as processing once
// Critical for: payment processing, email sending, job processing, webhooks

// STRATEGY 1: Natural idempotency (DB unique constraints)
// Prevent duplicate likes at the DB level:
// PRIMARY KEY (user_id, video_id) → INSERT ... ON CONFLICT DO NOTHING
await db.query(
  'INSERT INTO video_likes (user_id, video_id) VALUES ($1, $2) ON CONFLICT DO NOTHING',
  [userId, videoId]
)

// STRATEGY 2: Idempotency key (for payment / critical operations)
async function createPayment(
  userId: string,
  amount: number,
  idempotencyKey: string  // client generates UUID once, resends same key on retry
): Promise<Payment> {
  // Check if we've already processed this request:
  const existing = await paymentRepo.findByIdempotencyKey(idempotencyKey)
  if (existing) return existing  // return the same result — don't charge twice

  const payment = await stripeClient.charges.create({
    amount,
    currency: 'usd',
    customer: userId,
  }, {
    idempotencyKey  // Stripe also supports this — prevents double-charging on their side
  })

  return paymentRepo.create({ ...payment, idempotencyKey })
}

// STRATEGY 3: Job idempotency (prevent processing same event twice)
const worker = new Worker('webhook', async (job) => {
  const { eventId, eventType, payload } = job.data

  // Check if already processed (use Redis with TTL):
  const alreadyProcessed = await redis.get(`processed:${eventId}`)
  if (alreadyProcessed) {
    logger.info({ eventId }, 'Event already processed — skipping')
    return
  }

  await processWebhookEvent(eventType, payload)

  // Mark as processed (keep for 24h to handle late duplicates):
  await redis.setex(`processed:${eventId}`, 86400, '1')
})
```

# STEP 6 — GRACEFUL SHUTDOWN

```typescript
// When your server shuts down (during deploy), drain in-flight requests
// Don't kill connections abruptly — finish what you started

const server = app.listen(env.PORT, () => {
  logger.info({ port: env.PORT }, 'Server started')
})

async function gracefulShutdown(signal: string) {
  logger.info({ signal }, 'Received shutdown signal')

  // 1. Stop accepting new connections:
  server.close(async () => {
    logger.info('HTTP server closed')

    // 2. Wait for in-flight requests to complete (max 30s):
    await new Promise(resolve => setTimeout(resolve, 100))

    // 3. Close database connections:
    await db.$disconnect()
    logger.info('Database connections closed')

    // 4. Close Redis connection:
    await redis.quit()
    logger.info('Redis connection closed')

    // 5. Exit cleanly:
    process.exit(0)
  })

  // Force exit if graceful shutdown takes too long:
  setTimeout(() => {
    logger.error('Graceful shutdown timed out — forcing exit')
    process.exit(1)
  }, 30_000)
}

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'))
process.on('SIGINT',  () => gracefulShutdown('SIGINT'))
process.on('unhandledRejection', (reason, promise) => {
  logger.fatal({ reason, promise }, 'Unhandled promise rejection')
  process.exit(1)
})
```

# STEP 7 — RATE LIMITING (PROTECTION AGAINST ABUSE)

```typescript
import rateLimit from 'express-rate-limit'
import RedisStore from 'rate-limit-redis'

// Global rate limit (all endpoints):
app.use(rateLimit({
  windowMs: 60_000,  // 1 minute
  max: 100,          // 100 requests per minute per IP
  standardHeaders: true,
  legacyHeaders: false,
  store: new RedisStore({ client: redis }),  // share across all instances
  message: { error: { code: 'RATE_LIMITED', message: 'Too many requests. Retry in 60 seconds.' } }
}))

// Strict rate limit for auth endpoints (prevent brute force):
const authRateLimit = rateLimit({
  windowMs: 15 * 60_000,  // 15 minutes
  max: 5,                 // 5 login attempts per 15 min per IP
  skipSuccessfulRequests: true,
  store: new RedisStore({ client: redis, prefix: 'rl:auth:' }),
})

router.post('/auth/login', authRateLimit, authController.login)

// Per-user rate limit for expensive operations:
const uploadRateLimit = rateLimit({
  windowMs: 60 * 60_000,  // 1 hour
  max: 10,               // 10 uploads per hour per user
  keyGenerator: (req) => `upload:${req.user?.id ?? req.ip}`,
  store: new RedisStore({ client: redis, prefix: 'rl:upload:' }),
})

router.post('/upload/presigned', authenticate, uploadRateLimit, uploadController.presign)
```

# CHECKLIST — Before Moving to Code Review & Documentation

```
✅ Timeouts set on every external call (DB, Redis, HTTP, queues)
✅ Retry logic with exponential backoff and jitter for transient failures
✅ Circuit breaker on unstable external dependencies
✅ Non-critical features degrade gracefully (errors don't bubble to user)
✅ Stale cache fallback for critical read paths
✅ Idempotency for all critical operations (payments, emails, job processing)
✅ Graceful shutdown handler drains connections before exit
✅ Dead letter queue for jobs that exhaust retries
✅ Rate limiting on all endpoints (global + strict on auth + per-user on expensive ops)
✅ Unhandled promise rejection handler terminates process loudly
→ NEXT: 15-CodeReviewDocumentation.md
```
