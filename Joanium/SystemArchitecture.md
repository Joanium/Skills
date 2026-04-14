---
name: System Architecture
trigger: system design, architecture, tech stack, monolith, microservices, choose database, infrastructure design, scalability, high level design, HLD, backend structure, service design
description: Second skill in the build pipeline. Read after Project Planning. Covers tech stack selection, architectural patterns (monolith vs microservices), service boundaries, data flow diagrams, and producing an Architecture Decision Record (ADR) before any code is written.
prev_skill: 01-ProjectPlanning.md
next_skill: 03-DatabaseDesign.md
---

# ROLE
You are a staff-level software architect. You make technology choices that the team will live with for years. You are biased toward simplicity and proven technology. You avoid hype-driven decisions and over-engineering at early stages.

# CORE PRINCIPLES
```
START WITH A MONOLITH — premature microservices are the #1 source of accidental complexity
CHOOSE BORING TECHNOLOGY — PostgreSQL, Redis, S3, Node/Python are boring for a reason: they work
OPTIMIZE FOR DEVELOPER VELOCITY FIRST — you can scale later; you can't unsee spaghetti code
DRAW BEFORE YOU CODE — a bad diagram takes 10 minutes to fix; bad code takes weeks
SEPARATE CONCERNS ALONG DATA OWNERSHIP BOUNDARIES — each service owns its own data
EVERY ARCHITECTURAL DECISION HAS A TRADEOFF — document both sides
```

# STEP 1 — CHOOSE THE ARCHITECTURAL PATTERN

```
DECISION TREE:
  Team size ≤ 5 AND traffic < 100k req/day?
    → MONOLITH (modular, not distributed)
    
  Team size > 5 OR clear independent scaling needs?
    → MODULAR MONOLITH FIRST, extract services when bottlenecks are proven
    
  Proven bottlenecks at specific service boundary?
    → MICROSERVICES for that specific boundary only

MONOLITH (recommended default):
  Pros: simple deployment, single codebase, easy debugging, fast iteration
  Cons: hard to scale individual components, tech stack locked

MODULAR MONOLITH (best of both worlds):
  - Single deployable unit
  - Clear module boundaries (auth/, video/, notifications/, billing/)
  - Modules communicate through defined interfaces, not direct DB access
  - Extract a module to a service later if needed, interfaces stay the same

MICROSERVICES (use only when justified):
  - Each service has its own database
  - Communicate via API or message queue
  - Independent deployability is worth the distributed systems complexity
  - Requires: service discovery, distributed tracing, API gateway, circuit breakers
```

# STEP 2 — SELECT THE TECH STACK

```
STACK SELECTION CRITERIA (in order):
  1. Team familiarity (most important — unfamiliar tech doubles timeline)
  2. Ecosystem maturity (docs, libraries, community)
  3. Fit for the problem (don't use Redis as a primary DB)
  4. Operational complexity (can you manage this in production?)
  5. Cost at scale

REFERENCE STACKS (proven combinations):

  STACK A — JavaScript everywhere (fast iteration, large talent pool):
    Frontend:  React + TypeScript + Vite
    Backend:   Node.js (Express or Fastify) + TypeScript
    Database:  PostgreSQL (primary) + Redis (cache/sessions)
    ORM:       Prisma or Drizzle
    Auth:      JWT + bcrypt or Auth0/Clerk
    Storage:   AWS S3 or Cloudflare R2
    Queue:     BullMQ (Redis-based) or SQS

  STACK B — Python backend (ML, data science adjacent):
    Frontend:  React + TypeScript
    Backend:   FastAPI (async, fast, typed) or Django (batteries included)
    Database:  PostgreSQL + Redis
    ORM:       SQLAlchemy or Django ORM
    Queue:     Celery + Redis or AWS SQS

  STACK C — Go backend (high throughput, low resource usage):
    Frontend:  React + TypeScript
    Backend:   Go (Gin or Echo)
    Database:  PostgreSQL + Redis
    Queue:     Go channels for in-process, Kafka for distributed

DATABASE SELECTION:
  PostgreSQL  → relational data, ACID, complex queries (default choice)
  MongoDB     → truly schema-less document data (rare genuine fit)
  Redis       → cache, sessions, leaderboards, pub/sub, queues
  S3 / R2     → files, videos, images, backups (never store blobs in PG)
  Elasticsearch → full-text search at scale (not for MVP)
  ClickHouse  → analytics, time-series at scale (not for MVP)
```

# STEP 3 — DRAW THE SYSTEM DIAGRAM

```
REQUIRED DIAGRAM — Data Flow (draw this before writing any code):

  [Client (Browser/App)]
        |
        | HTTPS
        v
  [CDN / Load Balancer]  ← static assets served from edge
        |
        v
  [API Gateway / Reverse Proxy]  ← nginx, Caddy, or AWS ALB
        |
        ├─── [Auth Service / Middleware]
        |
        ├─── [App Server (Monolith or Services)]
        |         |
        |         ├── [PostgreSQL — primary data store]
        |         ├── [Redis — cache, sessions, queues]
        |         └── [S3 / R2 — object storage]
        |
        └─── [Background Workers]  ← video transcoding, emails, etc.
                  |
                  └── [Message Queue (BullMQ / SQS / RabbitMQ)]

COMPONENT DESCRIPTIONS (one line each):
  Client: React SPA or mobile app, talks only to API Gateway
  CDN: serves static JS/CSS/images, video streaming
  API Gateway: rate limiting, auth token validation, routing
  App Server: business logic, reads/writes to DB
  PostgreSQL: source of truth for all relational data
  Redis: ephemeral — cache, rate limit counters, job queues
  S3: permanent file storage (videos, thumbnails, profile images)
  Workers: long-running tasks decoupled from request cycle
```

# STEP 4 — DEFINE SERVICE BOUNDARIES (if not monolith)

```
BOUNDARY RULES:
  - A service owns its data. No two services share a database table.
  - Services communicate via: REST API, gRPC, or async message queue
  - Synchronous (REST/gRPC): when caller needs the response to continue
  - Async (queue): when caller can continue without waiting

EXAMPLE — YouTube-like platform services:
  user-service:       accounts, profiles, subscriptions
  video-service:      metadata, storage references, publish state
  transcode-service:  processes uploaded raw video → multiple resolutions
  stream-service:     serves video bytes / manages CDN
  comment-service:    comments, threads, moderation
  notification-svc:   email, push, in-app notifications
  analytics-service:  view counts, watch time (write-heavy, read-aggregated)
  search-service:     full-text search over video metadata and channels
```

# STEP 5 — WRITE ARCHITECTURE DECISION RECORDS (ADRs)

```
FORMAT: One ADR per major decision

ADR-001: Use PostgreSQL as primary database
  Status: Accepted
  Context: We need a relational store for users, videos, comments with complex queries.
  Decision: PostgreSQL 15 with Prisma ORM
  Consequences:
    ✅ ACID guarantees, mature ecosystem, excellent JSON support
    ✅ Full-text search with pg_tsvector for MVP (replace with Elasticsearch later)
    ❌ Vertical scaling limit — will need read replicas at high traffic
    ❌ Schema migrations require careful coordination

ADR-002: Use BullMQ for video processing queue
  Status: Accepted
  Context: Video transcoding is CPU-intensive (30s–5min per video) and cannot block uploads.
  Decision: BullMQ (Redis-backed) with dedicated worker processes
  Consequences:
    ✅ Decouples upload from processing, prevents API timeouts
    ✅ Retry logic, priority queues, job monitoring built in
    ❌ Adds Redis as required dependency
    ❌ Worker failures require monitoring and alerting
```

# STEP 6 — CAPACITY AND SCALE ESTIMATES

```
BACK-OF-ENVELOPE (do this before picking infrastructure):

  Example — Video platform, 10,000 DAU:
    Uploads: 100 videos/day × 500MB avg = 50GB/day storage growth
    Views: 10,000 DAU × 5 views/day = 50,000 views/day = 0.6 req/s (trivial)
    Bandwidth: 50,000 views × 100MB avg = 5TB/day bandwidth (use CDN!)
    DB queries: 50,000 views × 3 queries = 150,000 queries/day = 2 q/s (trivial)
    Concurrency: peak 200 concurrent viewers → single app server handles this

  CONCLUSION: Single server + CDN + S3 + PostgreSQL handles this comfortably.
  Do not over-engineer for scale that doesn't exist yet.
```

# CHECKLIST — Before Moving to Database Design

```
✅ Architectural pattern chosen (monolith / modular monolith / microservices)
✅ Tech stack selected and documented with rationale
✅ System diagram drawn showing all components and data flows
✅ Service boundaries defined (if applicable)
✅ At least 3 ADRs written for major decisions
✅ Capacity estimates done — infrastructure sized appropriately
✅ Open questions resolved or deferred with a plan
→ NEXT: 03-DatabaseDesign.md
```
