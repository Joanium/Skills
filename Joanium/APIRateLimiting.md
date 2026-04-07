---
name: API Rate Limiting
trigger: rate limiting, throttle api, api throttling, request rate limit, token bucket, sliding window, rate limit strategy, ddos protection
description: Implement API rate limiting strategies including token bucket, sliding window, fixed window, and leaky bucket algorithms. Covers distributed rate limiting and per-user quotas. Use when protecting APIs from abuse, implementing throttling, or preventing DDoS.
---

# ROLE
You are a platform engineer specializing in API protection. Your job is to implement rate limiting that protects services while providing fair access to legitimate users.

# RATE LIMITING ALGORITHMS

## Token Bucket
```typescript
class TokenBucket {
  private tokens: number
  private lastRefill: number

  constructor(
    private capacity: number,
    private refillRate: number // tokens per second
  ) {
    this.tokens = capacity
    this.lastRefill = Date.now()
  }

  consume(count: number = 1): boolean {
    this.refill()
    if (this.tokens >= count) {
      this.tokens -= count
      return true
    }
    return false
  }

  private refill() {
    const now = Date.now()
    const elapsed = (now - this.lastRefill) / 1000
    this.tokens = Math.min(this.capacity, this.tokens + elapsed * this.refillRate)
    this.lastRefill = now
  }
}
```

## Sliding Window
```typescript
import Redis from 'ioredis'

class SlidingWindowRateLimiter {
  constructor(private redis: Redis) {}

  async isAllowed(key: string, limit: number, windowMs: number): Promise<boolean> {
    const now = Date.now()
    const windowStart = now - windowMs
    
    // Remove old entries
    await this.redis.zremrangebyscore(key, 0, windowStart)
    
    // Count current window
    const count = await this.redis.zcard(key)
    
    if (count >= limit) return false
    
    // Add current request
    await this.redis.zadd(key, now, `${now}-${Math.random()}`)
    await this.redis.expire(key, Math.ceil(windowMs / 1000))
    
    return true
  }
}
```

# EXPRESS MIDDLEWARE
```typescript
import rateLimit from 'express-rate-limit'
import RedisStore from 'rate-limit-redis'
import Redis from 'ioredis'

const redis = new Redis()

const limiter = rateLimit({
  store: new RedisStore({
    sendCommand: (...args: string[]) => redis.call(...args)
  }),
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per window
  message: { error: 'Too many requests, please try again later' },
  standardHeaders: true, // Return rate limit info in headers
  legacyHeaders: false,
  keyGenerator: (req) => req.ip,
})

// Per-user rate limiting
const userLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: (req) => req.user?.role === 'premium' ? 1000 : 100,
  keyGenerator: (req) => req.user?.id || req.ip
})
```

# REVIEW CHECKLIST
```
[ ] Rate limits appropriate for endpoint sensitivity
[ ] Distributed rate limiting (Redis) for multi-instance
[ ] Per-user and per-IP limits configured
[ ] Rate limit headers returned (X-RateLimit-*)
[ ] Graceful degradation, not hard blocking
[ ] Different limits for different endpoint tiers
[ ] Monitoring for rate-limited requests
```
