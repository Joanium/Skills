---
name: Architecture Decision Records
trigger: adr, architecture decision, document my decision, why did we choose, tech decision, architectural decision record, document architecture, decision log, why did we use, write an adr
description: Create and maintain Architecture Decision Records (ADRs) to document significant technical choices, their context, and the reasoning behind them. Use when making an important technical decision, onboarding a new team, or explaining why the system is built the way it is.
---

The most expensive conversations in engineering are the ones that start "why did we build it this way?" ADRs are the answer: a short, honest document that captures what you decided, why, what you considered, and what you gave up. Future-you — and future teammates — will thank you.

## What Deserves an ADR?

Write an ADR when the decision:
- Is hard to reverse (or costly to reverse)
- Affects multiple teams or services
- Has meaningful trade-offs worth explaining
- Is likely to be questioned or revisited
- Sets a precedent that others will follow

**Write an ADR for:**
```
✓ Choosing a database or data store
✓ Adopting a new framework or language
✓ Defining API conventions (REST vs GraphQL vs gRPC)
✓ Choosing an authentication strategy
✓ Defining how services communicate (sync vs async)
✓ Major refactoring or migration decisions
✓ Build vs buy decisions
✓ Monolith vs microservices decisions
✓ Adopting a third-party vendor for critical infrastructure
```

**Don't write an ADR for:**
```
✗ Routine implementation details
✗ Decisions with no real alternatives
✗ Low-stakes style preferences (use linting rules for those)
✗ Decisions that are trivially reversible
```

## ADR States

Every ADR has a status that evolves over time:

```
Proposed    → Under discussion, not yet decided
Accepted    → Decided and in effect
Deprecated  → Was valid, but a newer ADR supersedes it
Superseded  → Replaced by [link to new ADR]
Rejected    → Considered but not adopted (valuable to record why)
```

Never delete ADRs — mark them superseded. History matters.

## The Standard ADR Format

### Template
```markdown
# ADR-[NUMBER]: [Decision Title]

**Status:** [Proposed | Accepted | Deprecated | Superseded by ADR-XXX]
**Date:** YYYY-MM-DD
**Deciders:** [Names or teams involved in the decision]
**Tags:** [database, auth, infra, frontend, ...]

## Context

What is the problem or opportunity that led to this decision? 
Describe the forces at play — technical constraints, business requirements, 
team skills, scale requirements, cost pressures.

Write this section as if explaining to a new engineer who has no context. 
Include the relevant facts, not your opinion about them.

## Decision

What did you decide?

State it clearly in one or two sentences. "We will use X for Y."
Don't bury the decision in the middle of a paragraph.

## Alternatives Considered

What else did you look at? For each:
- What is it?
- Why did it seem like a good idea?
- Why did you ultimately reject it?

Being honest about alternatives shows the decision was considered, not arbitrary.

## Consequences

### Positive
- What becomes easier or better?
- What risks are mitigated?

### Negative
- What becomes harder?
- What do you give up?
- What new risks does this introduce?

### Neutral / Follow-on decisions
- What related decisions does this force?
- What needs to be done to implement this decision?

## Notes / References
- [Link to relevant spike, POC, or benchmark]
- [Link to prior discussion (Slack thread, RFC, design doc)]
- [External documentation or articles that informed the decision]
```

## Real-World ADR Examples

### ADR-001: Use PostgreSQL as the primary database
```markdown
# ADR-001: Use PostgreSQL as the Primary Database

**Status:** Accepted
**Date:** 2024-03-15
**Deciders:** Alice (CTO), Bob (Lead Eng), Carol (Backend)

## Context

We need a primary database for our SaaS application. We're a 4-person team 
building a B2B product. Data has complex relationships (orgs, projects, users, 
permissions). We expect ~100K rows at launch scaling to ~10M over 3 years.
Team has strong SQL experience; no NoSQL experience.

## Decision

We will use PostgreSQL (v16) hosted on AWS RDS as our primary database.

## Alternatives Considered

**MySQL:** Comparable to Postgres for our use case. Rejected because the team 
prefers Postgres's richer type system (JSONB, arrays, enums), and Postgres has 
better support for complex queries and window functions we'll need for reporting.

**MongoDB:** Flexible schema seemed appealing for early iteration. Rejected 
because our data is highly relational (multi-tenancy, RBAC), and document 
databases make joins expensive. We'd likely regret this at scale.

**PlanetScale (MySQL-compatible):** Attractive branching workflow. Rejected 
because foreign key constraints are not supported, which we consider a safety net 
we're unwilling to give up. Also vendor lock-in concern.

## Consequences

Positive:
- ACID compliance — strong correctness guarantees for financial data
- Rich ecosystem: pgvector, PostGIS available when needed
- Team is productive from day one
- RDS managed backups, failover, snapshots

Negative:
- Vertical scaling only (until Aurora, if we need it)
- Schema migrations require care at scale
- RDS cost ~$150/mo for the instance we need at launch

Follow-on decisions:
- ADR-002 will cover the ORM choice (Prisma vs Drizzle vs raw SQL)
- We need a migration strategy (decided: Flyway)
```

### ADR-007: Adopt event-driven architecture for async operations
```markdown
# ADR-007: Use an Event Bus for Async Processing

**Status:** Accepted
**Date:** 2024-08-20
**Deciders:** Engineering team

## Context

Our monolith handles several operations synchronously that don't need to be:
email sending, PDF generation, webhook delivery, audit logging. These add 
latency to API responses (400ms+) and cause timeouts when downstream services 
are slow. We have 2 engineers familiar with message queues.

## Decision

We will introduce an internal event bus using BullMQ (backed by Redis) for 
async task processing. All "fire and forget" operations will be moved to 
background jobs. We will NOT migrate to full microservices — this is 
specifically for async processing within the monolith.

## Alternatives Considered

**AWS SQS:** More durable, fully managed. Rejected for now because it adds 
external dependency and complexity for a team our size. We already run Redis.
We can migrate to SQS later if Redis becomes a bottleneck.

**Full microservices with Kafka:** Premature for our scale and team size. 
Adds significant operational overhead. Rejected.

**PostgreSQL LISTEN/NOTIFY:** Interesting, but we'd be building our own queue.
BullMQ gives us retry, delay, concurrency control, and a UI for free.

## Consequences

Positive:
- API responses 300-400ms faster for affected endpoints
- Isolated failures: email failure doesn't fail the API request
- Visibility: Bull Board UI shows job status and failures

Negative:
- Operations are no longer atomic with the request (eventual consistency)
- Need to handle job failures and dead-letter queues
- Adds operational dependency on Redis availability

Follow-on:
- We need a monitoring alert when dead-letter queue grows
- ADR-008 will define retry and idempotency conventions for workers
```

## ADR Numbering and Storage

### File structure
```
/docs/architecture/decisions/
  ADR-001-postgresql-primary-database.md
  ADR-002-prisma-orm.md
  ADR-003-nextjs-frontend.md
  ADR-004-stripe-payments.md    (superseded)
  ADR-005-stripe-to-paddle.md   (supersedes ADR-004)
  ADR-006-authentication-jwt-vs-session.md
  ADR-007-event-bus-bullmq.md
  README.md  ← index of all ADRs
```

### ADR index (README.md)
```markdown
# Architecture Decision Records

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| 001 | PostgreSQL as primary database | Accepted | 2024-03-15 |
| 002 | Prisma as ORM | Accepted | 2024-03-20 |
| 003 | Next.js for frontend | Accepted | 2024-04-01 |
| 004 | Stripe for payments | Superseded by 005 | 2024-04-10 |
| 005 | Paddle for payments | Accepted | 2024-10-01 |
| 006 | JWT authentication | Accepted | 2024-05-15 |
| 007 | BullMQ event bus | Accepted | 2024-08-20 |
```

## Tooling

```bash
# adr-tools (CLI for managing ADRs)
brew install adr-tools

# Initialize ADR directory
adr init docs/architecture/decisions

# Create new ADR
adr new "Use Redis for session storage"
# Creates: docs/architecture/decisions/0008-use-redis-for-session-storage.md

# Supersede an old decision
adr new -s 4 "Switch from Stripe to Paddle"
```

## ADR Review Checklist

```
Writing an ADR:
☐ Is the context section written for someone with no prior knowledge?
☐ Is the decision stated clearly in one sentence?
☐ Are all seriously-considered alternatives documented?
☐ Are the consequences honest, including the downsides?
☐ Has at least one other engineer reviewed it?
☐ Is it linked from the PR that implements the decision?

Maintaining ADRs:
☐ When a decision changes, is the old ADR marked Superseded (not deleted)?
☐ Does the new ADR reference what it supersedes?
☐ Is the ADR index updated?
☐ Are ADRs discoverable from the README or onboarding docs?
```
