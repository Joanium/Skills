---
name: DevOps & CI/CD
trigger: CI/CD, pipeline, GitHub Actions, Docker, Dockerfile, containerize, continuous integration, continuous deployment, automated pipeline, build pipeline, lint, format, pre-commit, deploy pipeline, staging
description: Eleventh skill in the build pipeline. Covers Dockerizing your application, writing GitHub Actions CI/CD pipelines, environment management, database migration automation, and zero-downtime deployment strategies.
prev_skill: 10-PerformanceOptimization.md
next_skill: 12-CloudDeployment.md
---

# ROLE
You are a DevOps engineer who has been paged at 3am because a bad deployment took down production. You build pipelines that catch problems before they reach users. You automate everything repeatable so that deployments are boring, not scary. Your motto: if it's not automated, it will eventually be done wrong.

# CORE PRINCIPLES
```
AUTOMATE THE BORING STUFF — linting, testing, building, deploying should not require human steps
FAIL FAST IN CI — catch errors as early as possible (lint before tests, tests before build)
NEVER DEPLOY UNTESTED CODE — every merge to main must pass all tests first
STAGING IS YOUR PRODUCTION DRESS REHEARSAL — test on identical infrastructure
MIGRATIONS BEFORE CODE — run DB migrations before deploying new application code
ONE-COMMAND DEPLOY — if deploy requires more than one command, it will be done wrong
ROLLBACK MUST BE FAST — if you can't roll back in under 5 minutes, you can't deploy safely
```

# STEP 1 — DOCKERFILE

```dockerfile
# Backend Dockerfile (Node.js)
# Multi-stage build: smaller final image, no dev dependencies in production

# ─── STAGE 1: Dependencies ───────────────────────────────────────────────────
FROM node:20-alpine AS deps
WORKDIR /app

# Copy package files first (layer cache: only re-runs npm ci if package.json changes)
COPY package.json package-lock.json ./
RUN npm ci --frozen-lockfile  # exact versions, fails if lock file is stale

# ─── STAGE 2: Build ──────────────────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build  # TypeScript compilation

# ─── STAGE 3: Production ─────────────────────────────────────────────────────
FROM node:20-alpine AS runner
WORKDIR /app

# Security: run as non-root user
RUN addgroup --system --gid 1001 nodejs \
 && adduser  --system --uid 1001 nodeapp
USER nodeapp

# Only copy what production needs
COPY --from=builder --chown=nodeapp:nodejs /app/dist ./dist
COPY --from=builder --chown=nodeapp:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nodeapp:nodejs /app/package.json ./

ENV NODE_ENV=production
ENV PORT=3000
EXPOSE 3000

# Healthcheck — Docker and orchestrators use this
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["node", "dist/server.js"]
```

```dockerfile
# Frontend Dockerfile (Next.js)
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --frozen-lockfile

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Build args for environment variables needed at build time
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs \
 && adduser  --system --uid 1001 nextjs
USER nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
```

```yaml
# docker-compose.yml — local development
version: '3.8'
services:
  api:
    build: ./backend
    ports: ["3000:3000"]
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/appdb
      REDIS_URL: redis://cache:6379
    volumes:
      - ./backend/src:/app/src  # hot reload in dev
    depends_on:
      db:    { condition: service_healthy }
      cache: { condition: service_started }

  frontend:
    build: ./frontend
    ports: ["3001:3000"]
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:3000

  db:
    image: postgres:15-alpine
    environment: { POSTGRES_PASSWORD: postgres, POSTGRES_DB: appdb }
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 5s
      retries: 5

  cache:
    image: redis:7-alpine
    ports: ["6379:6379"]

volumes:
  postgres_data:
```

# STEP 2 — GITHUB ACTIONS CI PIPELINE

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'

jobs:
  # ─── JOB 1: Lint and Type Check (fastest, runs first) ──────────────────────
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci --frozen-lockfile
      - run: npm run lint        # ESLint
      - run: npm run typecheck   # tsc --noEmit
      - run: npm run format:check # Prettier

  # ─── JOB 2: Unit Tests ─────────────────────────────────────────────────────
  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: ${{ env.NODE_VERSION }}, cache: 'npm' }
      - run: npm ci --frozen-lockfile
      - run: npm run test:unit -- --coverage
      - uses: actions/upload-artifact@v4
        with: { name: coverage, path: coverage/ }

  # ─── JOB 3: Integration Tests (needs DB) ───────────────────────────────────
  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5
        ports: ['5432:5432']
      redis:
        image: redis:7-alpine
        ports: ['6379:6379']

    env:
      DATABASE_URL: postgresql://postgres:postgres@localhost:5432/testdb
      REDIS_URL:    redis://localhost:6379
      JWT_SECRET:   test-secret-minimum-32-characters-long
      NODE_ENV:     test

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: ${{ env.NODE_VERSION }}, cache: 'npm' }
      - run: npm ci --frozen-lockfile
      - run: npm run db:migrate  # run migrations on test DB
      - run: npm run test:integration

  # ─── JOB 4: Build Docker Image ─────────────────────────────────────────────
  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: [lint, unit-tests, integration-tests]  # only build if all tests pass
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: |
            ghcr.io/${{ github.repository }}/api:${{ github.sha }}
            ghcr.io/${{ github.repository }}/api:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

# STEP 3 — CD PIPELINE (DEPLOY TO STAGING AND PRODUCTION)

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    environment: staging   # requires environment protection rules in GitHub

    steps:
      - uses: actions/checkout@v4

      # 1. Run DB migrations BEFORE deploying new code
      - name: Run database migrations
        run: |
          docker run --rm \
            -e DATABASE_URL=${{ secrets.STAGING_DATABASE_URL }} \
            ghcr.io/${{ github.repository }}/api:${{ github.sha }} \
            node dist/migrate.js
        
      # 2. Deploy to staging (ECS / Fly.io / Railway etc.)
      - name: Deploy API to staging
        uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          task-definition: task-definition-staging.json
          service: api-staging
          cluster: app-cluster-staging
          image: ghcr.io/${{ github.repository }}/api:${{ github.sha }}
          wait-for-service-stability: true

      # 3. Run smoke tests against staging
      - name: Smoke test staging
        run: |
          curl -f https://api-staging.yourapp.com/health
          curl -f https://api-staging.yourapp.com/api/v1/videos?limit=1

  # Production requires manual approval (GitHub Environment protection)
  deploy-production:
    name: Deploy to Production
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production  # requires approval from designated reviewers

    steps:
      - name: Run database migrations
        run: |
          docker run --rm \
            -e DATABASE_URL=${{ secrets.PROD_DATABASE_URL }} \
            ghcr.io/${{ github.repository }}/api:${{ github.sha }} \
            node dist/migrate.js

      - name: Blue/green deploy to production
        # deploy new version alongside old, then switch traffic
        uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          task-definition: task-definition-prod.json
          service: api-production
          cluster: app-cluster-production
          image: ghcr.io/${{ github.repository }}/api:${{ github.sha }}
          wait-for-service-stability: true

      - name: Smoke test production
        run: curl -f https://api.yourapp.com/health
```

# STEP 4 — ENVIRONMENT MANAGEMENT

```
ENVIRONMENTS:
  local       → docker-compose, .env.local, developer's machine
  test        → ephemeral, created in CI, torn down after test run
  staging     → persistent, mirrors production, used for QA
  production  → customer-facing, highest availability requirement

ENVIRONMENT VARIABLES STRATEGY:
  ✅ Store secrets in GitHub Actions Secrets / AWS Secrets Manager / Vault
  ✅ Never commit secrets to git — even in private repos
  ✅ Validate all env vars at startup (see 06-BackendArchitecture.md)
  ✅ Different credentials for each environment (never share prod DB with staging)

.env STRUCTURE:
  .env.example     → committed to git, template with no real values
  .env.local       → gitignored, developer's personal overrides
  .env.test        → committed, only for test runner (no real credentials)

SECRETS ROTATION:
  - JWT_SECRET, database passwords rotate every 90 days
  - AWS access keys rotate every 90 days
  - Use short-lived OIDC tokens in CI/CD instead of long-lived AWS keys
```

# STEP 5 — ZERO-DOWNTIME DEPLOYMENT

```
STRATEGIES:

ROLLING DEPLOYMENT (default in ECS / Kubernetes):
  - Replace instances one by one
  - At any moment, some instances run old code, some run new
  - Requires: backward-compatible API changes and DB migrations
  - Risk: if new code has a bug, it affects a fraction of traffic first

BLUE/GREEN DEPLOYMENT (safer, more expensive):
  - Deploy new version to entirely separate environment (green)
  - Run smoke tests on green
  - Switch load balancer from blue to green
  - Keep blue running for 15 min (easy rollback by switching back)
  - Terminate blue after confidence

CANARY DEPLOYMENT (progressive):
  - Route 5% of traffic to new version
  - Monitor error rate and latency for 15 min
  - If healthy → 25% → 50% → 100%
  - Automatic rollback if error rate spikes

MIGRATION COMPATIBILITY RULES (prevent downtime during rolling deploy):
  When adding a column: make it nullable OR provide a default
  When renaming a column:
    Step 1: Add new column, write to both old and new
    Step 2: Read from new column, still write to both
    Step 3: Stop writing to old column
    Step 4: Drop old column
  When removing a column:
    Step 1: Remove code references (deploy)
    Step 2: Drop column in migration (deploy next release)
```

# STEP 6 — PRE-COMMIT HOOKS

```json
// package.json
{
  "scripts": {
    "lint":         "eslint src --ext .ts,.tsx",
    "format":       "prettier --write src",
    "format:check": "prettier --check src",
    "typecheck":    "tsc --noEmit",
    "test":         "vitest run",
    "test:unit":    "vitest run src/**/*.unit.test.ts",
    "test:integration": "vitest run src/**/*.integration.test.ts",
    "prepare":      "husky install"
  }
}
```

```bash
# .husky/pre-commit — runs before every commit
#!/bin/sh
npx lint-staged  # only runs on staged files — fast

# .lintstagedrc.json
{
  "*.{ts,tsx}": ["eslint --fix", "prettier --write"],
  "*.{json,md,yaml}": ["prettier --write"]
}

# .husky/pre-push — runs before git push
#!/bin/sh
npm run typecheck && npm run test:unit
# (integration tests run in CI, not locally — they're slower)
```

# CHECKLIST — Before Moving to Cloud Deployment

```
✅ Dockerfile written (multi-stage, non-root user, healthcheck)
✅ docker-compose.yml for local development
✅ CI pipeline: lint → unit tests → integration tests → build
✅ CD pipeline: migrations first, then deploy, then smoke test
✅ Staging environment configured and deployed to
✅ Production deploy requires manual approval
✅ Rollback procedure documented and tested
✅ Zero-downtime deployment strategy chosen
✅ Pre-commit hooks installed (lint + format on staged files)
✅ All secrets in environment-specific secret stores, not in git
→ NEXT: 12-CloudDeployment.md
```
