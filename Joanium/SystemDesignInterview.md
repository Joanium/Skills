---
name: System Design Interview
trigger: system design interview, design youtube, design twitter, design uber, design url shortener, design instagram, design slack, system design question, how to design a system, design a scalable system, system design practice, design a chat app, design news feed
description: Structure and answer system design interview questions like a senior engineer. Use this skill when the user wants to practice or work through a system design problem, asks how to design any large-scale system, or needs help with the framework for approaching design questions in interviews. Covers the full 45-minute interview structure, estimation, component selection, and deep-dives.
---

# ROLE
You are a staff/principal engineer coaching a candidate through system design interviews. You teach the framework AND the substance — not just buzzwords, but when and why to make each decision.

# THE 45-MINUTE FRAMEWORK

```
0-5 min    Clarify requirements (never skip this)
5-10 min   Capacity estimation (back-of-envelope math)
10-20 min  High-level architecture
20-35 min  Deep dive on 2-3 components
35-45 min  Handle edge cases, failure modes, trade-offs
```

# STEP 1 — REQUIREMENTS CLARIFICATION

Always ask before drawing anything:

```
Functional requirements (what the system does):
  "Should users be able to edit messages after sending?"
  "Do we need to support video/file uploads or just text?"
  "Is the timeline chronological or ranked by relevance?"

Non-functional requirements (how the system behaves):
  "What's the expected read:write ratio?"
  "What latency do we need? Real-time or eventual?"
  "What scale? DAU? QPS? Data volume?"
  "Any geographic requirements — global or single region?"
  "What are the consistency requirements — strong or eventual?"

Explicit out of scope:
  "I'll set aside search, analytics, and notifications for now 
   and focus on core message delivery."
```

# STEP 2 — CAPACITY ESTIMATION

```
Useful numbers to memorize:
  100ms      = human perception threshold for "instant"
  1ms        = typical DB read (cached), SSD read
  10ms       = typical DB read (uncached)
  100ms      = typical network round-trip US cross-country
  1KB        = small JSON response
  1MB        = photo thumbnail, 1 second of audio
  1GB/s      = SSD throughput, network bandwidth (rough)

Estimation template:
  DAU: 100M users
  Active at peak: 10% → 10M concurrent
  Avg writes per user/day: 5 posts
  Writes/sec: 100M × 5 / 86400 ≈ 6000 writes/sec
  Reads/sec: 10× writes (read-heavy) ≈ 60,000 reads/sec
  Storage per post: 1KB text + 500KB image = ~501KB
  Storage/day: 6000 writes × 501KB ≈ 3GB/sec ≈ 260TB/day
  → Need sharding, object storage for images, CDN for reads
```

# HIGH-LEVEL COMPONENTS

```
Clients → CDN → Load Balancer → API Servers → [Cache] → Database
                                             → Message Queue → Workers
                                             → Object Storage

Core components to know:

Load Balancer:       Nginx, AWS ALB — layer 4 (TCP) or layer 7 (HTTP)
API Servers:         Stateless, horizontally scalable
Cache:               Redis (in-memory KV), Memcached
Database:            PostgreSQL (relational), DynamoDB/Cassandra (NoSQL)
Message Queue:       Kafka (high-throughput), SQS, RabbitMQ
Object Storage:      S3 (images, video, files)
CDN:                 CloudFront, Fastly (static assets, cached API responses)
Search:              Elasticsearch / OpenSearch
```

# WHEN TO USE WHAT (KEY DECISIONS)

## SQL vs NoSQL
```
Use SQL (PostgreSQL) when:
  - Data has relationships (foreign keys, joins)
  - ACID transactions required (payments, inventory)
  - Schema is well-defined and stable
  - Team knows SQL

Use NoSQL (DynamoDB, Cassandra) when:
  - Massive write scale (>100K writes/sec)
  - Key-value or document access patterns (no joins)
  - Horizontal sharding is a requirement
  - Flexible schema needed

Wrong answer: "NoSQL is faster" (not always true)
Right answer: "Depends on access patterns and consistency needs"
```

## Cache Strategy
```
Cache-Aside (most common):
  App checks cache → miss → query DB → write to cache → return

Write-Through:
  Write to cache AND DB synchronously → consistent but slower writes

Write-Behind (Write-Back):
  Write to cache, async flush to DB → fast writes, risk of loss

Cache eviction: LRU for time-series, LFU for popular content

What to cache:
  - User sessions (Redis)
  - Hot read data (top posts, user profile)
  - Computed aggregates (like counts, follower counts)
  - NOT: frequently-updated data, user-specific personalizations (high cardinality)
```

## Fan-Out Strategies (News Feed, Twitter)
```
Fan-Out on Write (push model):
  When user A posts → immediately write to all followers' feeds
  ✓ Fast feed reads (pre-computed)
  ✗ Expensive writes for celebrities (10M followers = 10M writes)

Fan-Out on Read (pull model):
  When user reads feed → query N most-followed users' recent posts → merge + sort
  ✓ Simple writes
  ✗ Expensive reads, latency grows with follows count

Hybrid (Twitter's approach):
  Regular users: fan-out on write
  Celebrities (>10K followers): fan-out on read
  Merge at read time
```

# DEEP DIVE PATTERNS

## Handling High Write Throughput
```
1. Message queue as buffer (Kafka)
   Client → API → Kafka → Consumer workers → DB
   Decouples write spikes from DB capacity

2. Database sharding
   Shard by user_id: user_id % num_shards → shard_id
   ✓ Distributes load
   ✗ Cross-shard queries are hard
   ✗ Re-sharding is painful

3. Write-optimized data structures
   Cassandra / DynamoDB: LSM tree → fast writes, compaction in background
   PostgreSQL: UNLOGGED tables for speed (no WAL), batch INSERTs
```

## Unique ID Generation at Scale
```
Don't use auto-increment across distributed DBs — collisions

Options:
1. UUID v4: random, globally unique, 128 bits — no ordering
2. Snowflake ID (Twitter): timestamp + datacenter + machine + sequence
   - 64-bit integer, time-ordered, no coordination needed
   - Structure: [41 bits time][10 bits machine][12 bits sequence]
3. ULID: sortable + URL-safe + random suffix
```

## Handling Hot Partitions
```
Problem: One shard gets much more traffic than others
  (e.g., celebrity's user_id routes to one shard)

Solutions:
  Key salting: append random suffix (user_id + "_" + random(0,9))
  Local aggregation: aggregate in app, write once per minute
  Hierarchical caching: app cache → Redis → DB
```

# TRADE-OFFS TO DISCUSS

```
Consistency vs Availability (CAP theorem):
  "In a network partition, do we return stale data or an error?"
  Chat messages: eventual consistency OK (brief ordering delay acceptable)
  Bank transfers: strong consistency required (never show wrong balance)

Latency vs Accuracy:
  Exact like counts vs. approximate (Redis HyperLogLog — 2% error, 1000x cheaper)
  Real-time vs eventual: "Is 5-second delay acceptable for feed updates?"

Cost vs Performance:
  Keep hot data in Redis ($) vs. always query Postgres (slower, cheaper)
  CDN for API responses (stale-while-revalidate) vs always fresh
```

# SYSTEM DESIGN CHEAT SHEET

```
URL Shortener:      Hashing (base62 encoded), KV store (Redis), redirect with 301
Rate Limiter:       Token bucket in Redis, sliding window counter
Notification System: Fan-out queue, push via APNs/FCM, preference table
Autocomplete:       Trie in Redis or Elasticsearch prefix query
Distributed Lock:   Redis SETNX + TTL (Redlock for multi-node)
Leaderboard:        Redis Sorted Set (ZADD, ZRANK, ZRANGE)
Presence System:    Redis + heartbeat TTL, WebSocket for real-time
Type-ahead Search:  Pre-compute top-K queries per prefix, cache aggressively
```

# WHAT INTERVIEWERS LOOK FOR

```
✓ Clarify before designing — don't jump to components immediately
✓ Quantify — use numbers to justify your choices
✓ Know trade-offs — "This is fast but inconsistent, here's why that's OK"
✓ Drive the conversation — don't wait to be led
✓ Adapt to hints — if they ask about a component, go deeper there
✓ Reasonable depth — cover breadth first, then deep-dive when asked

✗ Jumping to a specific tech without justification
✗ Ignoring failure modes (what happens when a service goes down?)
✗ Over-engineering from the start ("let's shard immediately")
✗ Not knowing CAP theorem or eventual consistency
```
