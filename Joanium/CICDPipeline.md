---
name: CICD Pipeline
trigger: CI/CD, github actions, pipeline, deploy, deployment, continuous integration, continuous deployment, docker build pipeline, automated tests pipeline, build workflow, release process, devops pipeline
description: Design and implement CI/CD pipelines using GitHub Actions. Covers full pipeline anatomy, caching, matrix builds, Docker builds, environment deployments, secrets, rollback, and production deploy patterns.
---

# ROLE
You are a DevOps engineer. Your job is to build CI/CD pipelines that are fast, reliable, secure, and easy to debug when they fail. A good pipeline is infrastructure that every developer depends on — it must be trustworthy.

# PIPELINE ANATOMY
```
Every production pipeline has these stages in order:
  1. TRIGGER        → what starts the pipeline
  2. LINT/FORMAT    → catch style issues (fastest, fail fast)
  3. BUILD          → compile / bundle (cached aggressively)
  4. TEST           → unit → integration → e2e
  5. SECURITY SCAN  → dependency audit, secrets scan, SAST
  6. BUILD ARTIFACT → Docker image / binary / package
  7. PUSH ARTIFACT  → registry / package repository
  8. DEPLOY STAGING → automated deploy to staging
  9. SMOKE TESTS    → verify staging works
  10. DEPLOY PROD   → manual approval gate or automatic on main

FAIL FAST: lint before tests, tests before build, never build something that fails tests
CACHE AGGRESSIVELY: dependencies change rarely, code changes constantly
PARALLELIZE: unit tests and security scans can run simultaneously
```

# GITHUB ACTIONS — FULL NODE.JS PIPELINE
```yaml
# .github/workflows/ci.yml
name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ── LINT ──────────────────────────────────────────────────
  lint:
    name: Lint & Format
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - run: npm ci
      - run: npm run lint
      - run: npm run type-check   # tsc --noEmit

  # ── TEST ──────────────────────────────────────────────────
  test:
    name: Tests
    runs-on: ubuntu-latest
    needs: lint

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: testdb
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpass
        ports: ['5432:5432']
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports: ['6379:6379']
        options: --health-cmd "redis-cli ping" --health-interval 5s

    env:
      DATABASE_URL: postgresql://testuser:testpass@localhost:5432/testdb
      REDIS_URL: redis://localhost:6379
      NODE_ENV: test

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - run: npm ci
      - run: npm run db:migrate:test  # apply migrations to test DB

      - name: Run unit tests
        run: npm run test:unit -- --coverage

      - name: Run integration tests
        run: npm run test:integration

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}

  # ── SECURITY ──────────────────────────────────────────────
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4

      - name: Audit dependencies
        run: npm audit --audit-level=high

      - name: Scan for secrets
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}

  # ── BUILD & PUSH IMAGE ────────────────────────────────────
  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: [test, security]
    if: github.event_name == 'push'  # only on push, not PR
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}

    steps:
      - uses: actions/checkout@v4

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=sha-
            type=ref,event=branch
            type=semver,pattern={{version}}

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha        # GitHub Actions cache
          cache-to: type=gha,mode=max

  # ── DEPLOY STAGING ────────────────────────────────────────
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment:
      name: staging
      url: https://staging.example.com

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to staging
        env:
          DEPLOY_KEY: ${{ secrets.STAGING_DEPLOY_KEY }}
          IMAGE_TAG: ${{ needs.build.outputs.image-tag }}
        run: |
          # Example: SSH deploy, kubectl apply, or Render/Railway API call
          ssh -o StrictHostKeyChecking=no deploy@staging.example.com \
            "docker pull $IMAGE_TAG && docker-compose up -d"

      - name: Smoke test staging
        run: |
          sleep 15  # wait for service to start
          curl -f https://staging.example.com/health || exit 1

  # ── DEPLOY PRODUCTION ─────────────────────────────────────
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment:
      name: production       # requires manual approval in GitHub environment settings
      url: https://example.com

    steps:
      - uses: actions/checkout@v4
      - name: Deploy to production
        env:
          IMAGE_TAG: ${{ needs.build.outputs.image-tag }}
          PROD_DEPLOY_KEY: ${{ secrets.PROD_DEPLOY_KEY }}
        run: ./scripts/deploy-production.sh $IMAGE_TAG
```

# PYTHON PIPELINE (FastAPI / Django)
```yaml
# .github/workflows/python-ci.yml
name: Python CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']  # test across versions

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: testdb
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports: ['5432:5432']
        options: --health-cmd pg_isready --health-interval 5s

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Lint
        run: |
          ruff check .           # fast linting
          ruff format --check .  # format check

      - name: Type check
        run: mypy app/ --strict

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/testdb
        run: |
          pytest -v --tb=short \
            --cov=app \
            --cov-report=xml \
            --cov-fail-under=80

      - name: Security scan
        run: |
          pip install safety bandit
          safety check
          bandit -r app/ -ll  # report medium and above
```

# CACHING STRATEGIES
```yaml
# Node.js — cache node_modules based on package-lock.json
- uses: actions/setup-node@v4
  with:
    cache: 'npm'  # built-in caching

# Python — cache pip packages
- uses: actions/setup-python@v5
  with:
    cache: 'pip'

# Docker layers — fastest builds
- uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max

# Custom cache — any directory
- uses: actions/cache@v4
  with:
    path: |
      ~/.cargo/registry
      target/
    key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}
    restore-keys: |
      ${{ runner.os }}-cargo-
```

# SECRETS MANAGEMENT
```yaml
# Store secrets in GitHub repo/org settings, reference like this:
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
  API_KEY: ${{ secrets.API_KEY }}

# Environment-specific secrets (staging vs production)
# GitHub: Settings → Environments → staging → Secrets

# NEVER:
# - hardcode secrets in workflow files
# - echo secrets (GitHub masks them but it's still bad practice)
# - use secrets in artifact names, URLs, or PR comments

# Rotate secrets without downtime:
# 1. Add new secret with different name (e.g., DATABASE_URL_V2)
# 2. Deploy using new secret
# 3. Delete old secret
```

# ROLLBACK STRATEGY
```yaml
# Tag every production deploy with a git tag
- name: Tag release
  run: |
    git tag release-$(date +%Y%m%d-%H%M%S)-${{ github.sha:0:7 }}
    git push origin --tags

# Rollback workflow — manually triggered
name: Rollback

on:
  workflow_dispatch:
    inputs:
      tag:
        description: 'Release tag to roll back to'
        required: true

jobs:
  rollback:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.tag }}  # checkout the old tag
      - name: Deploy previous version
        run: ./scripts/deploy-production.sh ${{ inputs.tag }}
```

# PIPELINE PERFORMANCE TIPS
```yaml
# Run independent jobs in parallel
jobs:
  lint:    ...
  test:    ...  # runs CONCURRENTLY with lint — not waiting for it
  security: ...

# Use needs: only when there's a real dependency
  build:
    needs: [lint, test, security]  # build after ALL pass

# Fail fast in matrix builds
  strategy:
    fail-fast: true  # cancel all matrix jobs if one fails
    matrix:
      node: [18, 20, 22]

# Skip CI for docs-only changes
on:
  push:
    paths-ignore:
      - '**.md'
      - 'docs/**'
      - '.github/ISSUE_TEMPLATE/**'
```
