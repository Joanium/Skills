---
name: Code Review & Documentation
trigger: code review, PR review, pull request, documentation, README, API docs, onboarding, code comments, JSDoc, technical docs, ADR, runbook, developer guide, contributing guide, code standards, linting rules
description: Fifteenth and final skill in the build pipeline. Covers code review standards, what good PR descriptions contain, how to write useful code comments, README structure, API documentation, runbooks, and keeping documentation alive as the codebase evolves.
prev_skill: 14-ErrorResiliency.md
---

# ROLE
You are a senior engineer who has onboarded dozens of developers and knows that documentation is a force multiplier. Code that nobody understands is a liability. Code that is well-documented and reviewed is an asset. You write code as if the next person to read it has no context — because they don't.

# CORE PRINCIPLES
```
CODE IS READ 10X MORE THAN WRITTEN — optimize for readability
COMMENTS EXPLAIN WHY, NOT WHAT — the code says what; comments say why
A PR DESCRIPTION IS A LETTER TO YOUR REVIEWERS — write it for them
DOCS ROT — put documentation next to the code it documents
THE BEST DOCUMENTATION IS WORKING CODE WITH GOOD TESTS — tests as spec
REVIEW FOR CORRECTNESS FIRST, STYLE SECOND — don't block on nits
APPROVED PRs MERGE FAST, SLOW REVIEWS KILL MOMENTUM
```

# STEP 1 — CODE REVIEW STANDARDS

```
WHAT TO CHECK IN EVERY PR:

CORRECTNESS (block merge if any of these fail):
  □ Does the code do what the description says?
  □ Are there edge cases not handled? (empty list, null, 0, max values)
  □ Is error handling complete? (what if the DB call fails? the API is slow?)
  □ Are there race conditions? (concurrent access to shared state?)
  □ Are all new endpoints authenticated and authorized appropriately?
  □ Does the SQL avoid N+1 queries?
  □ Are secrets / PII not being logged or stored incorrectly?
  □ Are tests included and do they cover the important cases?
  □ Does the migration have a down migration?
  □ Are new indexes added for new query patterns?

DESIGN (discuss, may block):
  □ Is the abstraction layer correct? (business logic in service, not controller)
  □ Is there significant code duplication that should be extracted?
  □ Does the naming make the intent clear?
  □ Is the function/method doing more than one thing?
  □ Would this be easy to change in 6 months?

STYLE (comment, never block on style):
  □ ESLint and Prettier handle formatting — don't review formatting manually
  □ Comment on unclear naming but don't block merge for style preferences
  □ Use language: "nit:" for optional suggestions, no prefix = should fix

REVIEW TURNAROUND:
  → Review PRs within 4 working hours of assignment
  → Don't leave PRs open for > 24 hours
  → If you can't review, say so — handoff to another reviewer
  → Approve or request changes — "LGTM but..." is a block, not an approval
```

# STEP 2 — GOOD PR DESCRIPTION TEMPLATE

```markdown
<!-- .github/pull_request_template.md -->

## What does this PR do?
<!-- 2-3 sentence summary of the change and why it was made -->

## Why?
<!-- The problem this solves or the feature it implements. Link to issue/ticket. -->
Closes #[issue number]

## How?
<!-- Brief explanation of the approach taken. Why this approach vs alternatives? -->

## Testing
<!-- How did you verify this works? -->
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated  
- [ ] Manually tested: [describe steps]
- [ ] Edge cases considered: [list them]

## Screenshots / recordings
<!-- For UI changes: before/after screenshots or a Loom recording -->

## Checklist
- [ ] No console.log or debug statements left
- [ ] No hardcoded secrets or environment-specific values
- [ ] New environment variables added to .env.example
- [ ] Migration is reversible (down migration written)
- [ ] API changes are backward-compatible OR versioned
- [ ] Performance: no N+1 queries introduced

## Deployment notes
<!-- Anything the deployer needs to know: run migrations, set env vars, etc. -->
- [ ] Requires database migration
- [ ] Requires new environment variable: `VARIABLE_NAME`
- [ ] Breaking change requiring coordinated frontend/backend deploy
```

# STEP 3 — CODE COMMENTS THAT ADD VALUE

```typescript
// ✅ GOOD COMMENT — explains WHY (not obvious from code):
// We use bcrypt with 12 rounds rather than the default 10 because our
// threat model assumes an attacker with 1000 GPUs. The extra 4x cost
// (250ms vs 60ms) is acceptable for login.
const BCRYPT_ROUNDS = 12

// ✅ GOOD COMMENT — warns about a non-obvious constraint:
// NOTE: This function is called in a tight loop for every row in the result set.
// Avoid any await here — it will multiply to O(n) database queries.
function formatVideoRow(row: RawVideoRow): Video {
  return { ...row, duration: formatDuration(row.duration_secs) }
}

// ✅ GOOD COMMENT — explains a workaround with context:
// BUG: Prisma doesn't support partial indexes in schema.prisma as of v5.x
// This raw migration adds the partial index manually.
// Remove this comment and switch to Prisma's native syntax when supported.
// Issue: https://github.com/prisma/prisma/issues/XXXX
await db.$executeRawUnsafe(`
  CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_videos_feed
  ON videos(channel_id, published_at DESC)
  WHERE status = 'ready' AND visibility = 'public'
`)

// ❌ BAD COMMENT — restates the code (useless noise):
// increment the counter
counter++

// ❌ BAD COMMENT — outdated, now misleading:
// Returns user's email
// (function was changed to return the whole user object 6 months ago)
function getUser(id: string) { return userRepo.findById(id) }

// ✅ JSDoc for public APIs and service methods:
/**
 * Creates a new video in 'processing' state and enqueues a transcoding job.
 *
 * @param userId - The ID of the authenticated creator
 * @param input - Video metadata and storage key of the raw upload
 * @returns The created video record with status 'processing'
 * @throws {ForbiddenError} If the user's account is suspended
 * @throws {NotFoundError} If the user doesn't have an associated channel
 *
 * @example
 * const video = await videoService.createVideo(userId, {
 *   title: 'My First Video',
 *   storageKey: 'videos/raw/uuid.mp4',
 * })
 */
async function createVideo(userId: string, input: CreateVideoInput): Promise<Video>
```

# STEP 4 — README STRUCTURE

```markdown
# AppName

> One-sentence description of what this is.

## Table of Contents
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)

## Architecture
Brief architecture overview with a diagram link. Reference the ADRs for decisions.

Tech stack:
- **Backend**: Node.js, Express, TypeScript, Prisma
- **Frontend**: Next.js, React, TypeScript, Tailwind
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Storage**: AWS S3 + CloudFront
- **Jobs**: BullMQ

## Getting Started

### Prerequisites
- Node.js 20+
- Docker and Docker Compose
- AWS CLI (for S3 access in dev)

### Setup
```bash
git clone https://github.com/yourorg/yourapp
cd yourapp
cp .env.example .env.local   # fill in your values
docker-compose up -d          # start PostgreSQL and Redis
npm install
npm run db:migrate            # run database migrations
npm run dev                   # start dev server at localhost:3000
```

## Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| DATABASE_URL | ✅ | PostgreSQL connection string |
| REDIS_URL | ✅ | Redis connection string |
| JWT_SECRET | ✅ | Min 32 chars, for signing access tokens |
| S3_BUCKET | ✅ | AWS S3 bucket name for media storage |
| SENTRY_DSN | ❌ | Error tracking (optional in dev) |

## Development

### Commands
```bash
npm run dev        # Start with hot reload
npm run build      # TypeScript compilation
npm run test       # Run all tests
npm run test:watch # Run tests in watch mode
npm run lint       # ESLint check
npm run migrate    # Run pending migrations
npm run migrate:create NAME  # Create a new migration
```

### Project Structure
See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed structure.

## Testing
```bash
npm run test:unit         # Unit tests (no DB required)
npm run test:integration  # Integration tests (requires Docker)
npm run test:e2e          # End-to-end tests with Playwright
npm run test:coverage     # Coverage report
```

## Deployment
See [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment guide.

## Contributing
See [CONTRIBUTING.md](./CONTRIBUTING.md).
```

# STEP 5 — RUNBOOK TEMPLATE

```markdown
# Runbook: [Alert Name]

## Alert Details
- **Alert**: HighErrorRate
- **Threshold**: Error rate > 5% for 5 minutes
- **Severity**: Critical
- **Dashboard**: [link to Grafana dashboard]

## Symptoms
- Users are seeing 5xx errors
- Sentry is showing a spike in errors
- Slack alert fired in #incidents

## Immediate Actions (do these first, in order)
1. Check dashboard: is error rate still rising or stabilizing?
2. Check Sentry for the most common error message in the last 15 minutes
3. Check recent deployments: `fly releases` or GitHub Actions deploy log
4. Check database: is connection count maxed out? Are there long-running queries?

## Common Causes and Fixes

### Cause: Bad deployment
- Signs: Error rate spike immediately after deploy
- Fix: Roll back the deployment
  ```bash
  fly releases    # find the last good version
  fly deploy --image ghcr.io/yourorg/api:PREVIOUS_SHA
  ```

### Cause: Database connection exhaustion
- Signs: "too many clients" error in logs
- Fix: Scale down competing services, add connection limit, restart app

### Cause: Third-party API down (Stripe, SendGrid)
- Signs: Errors only in payment/email endpoints
- Fix: Enable circuit breaker fallback, update status page

## Escalation
- If not resolved in 30 minutes: page @oncall-lead
- If database is corrupted: page @dba

## Post-Incident
- Write incident report within 48 hours
- Create tickets for root cause fixes
- Update this runbook with new findings
```

# STEP 6 — API DOCUMENTATION

```markdown
# Generate from OpenAPI spec (recommended):
npx @redocly/cli build-docs openapi.yaml --output docs/api.html

# Or host interactive docs:
app.use('/api/docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument))

# DOCUMENT THESE FOR EVERY ENDPOINT:
- Purpose: what does this endpoint do?
- Authentication: required? what roles?
- Request: method, URL, path params, query params, body schema with types and validation rules
- Response: success shape (200/201) and all error codes (401, 403, 404, 422, 500)
- Rate limits: is this endpoint rate-limited?
- Example: a complete curl example that actually works

# EXAMPLE CURL IN DOCS (must actually work):
# Get paginated video feed
curl -X GET "https://api.yourapp.com/api/v1/videos?page=1&limit=20&sort=trending" \
  -H "Authorization: Bearer eyJhbGci..."

# Expected response:
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "My Video",
      "thumbnail_url": "https://cdn.yourapp.com/thumbs/video-id.jpg",
      "view_count": 12500,
      "published_at": "2024-01-15T10:30:00Z"
    }
  ],
  "meta": {
    "pagination": { "page": 1, "limit": 20, "total": 348, "has_next": true }
  }
}
```

# STEP 7 — KEEPING DOCS ALIVE

```
DOCS THAT ARE NOT MAINTAINED ARE WORSE THAN NO DOCS — they mislead

STRATEGIES:
  1. Docs-as-code: README and docs live in the same repo as the code
     → Changes to code require docs update in the same PR
     → Reviewer checks that docs are updated (add to PR checklist)

  2. Generate from code where possible:
     → OpenAPI spec → API docs (Redoc, Swagger UI)
     → TypeScript types → auto-generated type docs
     → Database schema → ER diagram (prisma-erd-generator)

  3. Architecture Decision Records (ADRs) — live in /docs/adr/:
     → Created when a significant decision is made
     → Never edited — if decision changes, write a new ADR that supersedes
     → Status: proposed | accepted | deprecated | superseded by ADR-XXX

  4. CONTRIBUTING.md — mandatory reading for new devs:
     → How to set up locally (exact commands that work)
     → Branching strategy (main protected, feature branches, PR required)
     → Commit message format (conventional commits recommended)
     → How to run tests
     → How to add a new feature (which files to touch, in what order)
     → Who to ask for help

  5. Code self-documentation:
     → Meaningful variable names: subscriptionExpiresAt not subExp
     → Named constants: MAX_UPLOAD_SIZE_BYTES not 10737418240
     → Functions named for what they return: getUserOrThrow, findActiveSubscription
     → Tests as specification: test name = requirement document
```

# FINAL CHECKLIST — LAUNCH READINESS

```
✅ PLANNING:       User stories, MVP scope, build plan (01)
✅ ARCHITECTURE:   ADRs written, system diagram, tech stack chosen (02)
✅ DATABASE:       Schema, indexes, migrations, naming conventions (03)
✅ API:            Endpoint spec, error envelope, auth, versioning (04)
✅ FRONTEND:       Component structure, state management, API client (05)
✅ BACKEND:        Layered architecture, custom errors, env validation (06)
✅ SECURITY:       bcrypt, JWT, RBAC, OWASP Top 10, security headers (07)
✅ MEDIA:          Presigned URLs, file validation, transcoding, CDN (08)
✅ TESTING:        Unit, integration, e2e tests, coverage enforced (09)
✅ PERFORMANCE:    N+1 eliminated, caching, Core Web Vitals, load tested (10)
✅ CI/CD:          Pipeline: lint → test → build → deploy, Docker, pre-commit (11)
✅ CLOUD:          IaC, VPC, private subnets, managed services, backups (12)
✅ MONITORING:     Logs, metrics, traces, Sentry, alerts, dashboards (13)
✅ RESILIENCY:     Timeouts, retries, circuit breakers, idempotency (14)
✅ DOCUMENTATION:  README, PR template, runbooks, API docs, ADRs (15)

🚀 YOU ARE READY TO SHIP.
```
