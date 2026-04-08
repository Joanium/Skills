---
name: Docker Compose Local Development
trigger: docker compose, docker-compose, local development environment, local docker setup, docker compose services, development environment setup, local stack, docker compose postgres redis, compose file
description: Build reliable, fast local development environments with Docker Compose. Covers service composition, networking, volumes, environment management, dependency health checks, and developer experience optimization.
---

# ROLE
You are a senior DevOps or platform engineer. Local development environments should be boring to set up — `docker compose up` and you're coding in 2 minutes. Every deviation from that goal is a tax on every developer, every day.

# CORE PRINCIPLES
```
ONE COMMAND SETUP:    `docker compose up` should work first time, every time.
PARITY WITH PROD:     Same versions, same config shape, different values.
FAST FEEDBACK:        Hot reload for application code — never rebuild for source changes.
EXPLICIT DEPS:        All external dependencies (DB, cache, queues) run locally.
SECRETS SEPARATE:     .env.example in git. .env never in git.
```

# CANONICAL COMPOSE FILE STRUCTURE
```yaml
# compose.yaml (preferred name — `docker-compose.yml` is legacy spelling)
name: myapp

services:

  # ─── Application Services ─────────────────────────────────────────────
  api:
    build:
      context: .
      dockerfile: Dockerfile.dev
      target: development    # multi-stage: only build dev stage locally
    ports:
      - "3000:3000"          # host:container
    volumes:
      - ./src:/app/src:cached            # mount source for hot reload
      - /app/node_modules                # anonymous volume — don't mount host node_modules
    environment:
      NODE_ENV: development
      DATABASE_URL: postgres://myapp:password@postgres:5432/myapp_dev
      REDIS_URL: redis://redis:6379
    env_file:
      - .env                 # developer-local overrides (gitignored)
    depends_on:
      postgres:
        condition: service_healthy  # wait for actual readiness, not just container start
      redis:
        condition: service_healthy
    networks:
      - internal

  worker:
    build:
      context: .
      dockerfile: Dockerfile.dev
    command: npm run worker:dev
    volumes:
      - ./src:/app/src:cached
      - /app/node_modules
    environment:
      DATABASE_URL: postgres://myapp:password@postgres:5432/myapp_dev
      REDIS_URL: redis://redis:6379
    depends_on:
      - api       # assumes api starts shared infra
    networks:
      - internal

  # ─── Infrastructure Services ──────────────────────────────────────────
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: myapp
      POSTGRES_PASSWORD: password     # local only — never production
      POSTGRES_DB: myapp_dev
    ports:
      - "5432:5432"          # expose to host so devs can use psql/DBeaver directly
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/db/seed.sql:/docker-entrypoint-initdb.d/seed.sql:ro  # auto-runs on init
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U myapp -d myapp_dev"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - internal

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - internal

  mailhog:
    image: mailhog/mailhog:latest
    ports:
      - "1025:1025"    # SMTP — configure app to send here
      - "8025:8025"    # Web UI — view sent emails at localhost:8025
    networks:
      - internal

# ─── Networks ─────────────────────────────────────────────────────────────
networks:
  internal:
    driver: bridge

# ─── Volumes ──────────────────────────────────────────────────────────────
volumes:
  postgres_data:    # persist DB between restarts
```

# DOCKERFILE FOR DEVELOPMENT
```dockerfile
# Dockerfile.dev — fast rebuilds, hot reload
FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json ./

FROM base AS development
# Install ALL dependencies (including devDependencies for hot reload tools)
RUN npm ci
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]   # nodemon, ts-node-dev, or vite

FROM base AS production-deps
RUN npm ci --omit=dev

FROM base AS production
COPY --from=production-deps /app/node_modules ./node_modules
COPY . .
RUN npm run build
CMD ["node", "dist/server.js"]
```

# ENVIRONMENT MANAGEMENT
```bash
# .env.example — committed to git, documents all required variables
DATABASE_URL=postgres://myapp:password@localhost:5432/myapp_dev
REDIS_URL=redis://localhost:6379
SESSION_SECRET=change-me-to-something-random-32-chars-minimum
STRIPE_SECRET_KEY=sk_test_YOUR_STRIPE_TEST_KEY_HERE
SENDGRID_API_KEY=YOUR_SENDGRID_KEY

# Developer workflow:
cp .env.example .env
# Edit .env with real test API keys

# .gitignore — ALWAYS include
.env
.env.local
.env.*.local
```

# HEALTH CHECKS — DEPENDENCY READINESS
```yaml
# Pattern: always use service_healthy, not service_started
depends_on:
  postgres:
    condition: service_healthy    # waits for pg_isready
  redis:
    condition: service_healthy    # waits for PONG
  kafka:
    condition: service_healthy

# Kafka healthcheck example
kafka:
  image: confluentinc/cp-kafka:7.6.0
  healthcheck:
    test: ["CMD-SHELL", "kafka-broker-api-versions --bootstrap-server localhost:9092"]
    interval: 10s
    timeout: 10s
    retries: 10
    start_period: 30s   # kafka takes a while to start

# ElasticSearch healthcheck
elasticsearch:
  image: elasticsearch:8.12.0
  healthcheck:
    test: ["CMD-SHELL", "curl -sf http://localhost:9200/_cluster/health | grep -qv '\"status\":\"red\"'"]
    interval: 10s
    retries: 10
    start_period: 30s
```

# OVERRIDE FILES — ENVIRONMENT VARIANTS
```yaml
# compose.override.yaml — auto-loaded with compose.yaml for local dev
# (developer machine specific settings — gitignored or committed for team use)
services:
  api:
    ports:
      - "9229:9229"    # Node.js debugger port
    environment:
      DEBUG: "app:*"   # verbose logging

# compose.test.yaml — for integration tests in CI
# Run: docker compose -f compose.yaml -f compose.test.yaml up --abort-on-container-exit
services:
  api:
    command: npm test
    environment:
      DATABASE_URL: postgres://myapp:password@postgres:5432/myapp_test
  postgres:
    environment:
      POSTGRES_DB: myapp_test
    tmpfs:
      - /var/lib/postgresql/data    # in-memory for speed in CI, no persistence needed
```

# COMMON WORKFLOWS
```bash
# Start everything
docker compose up

# Start in background + tail logs
docker compose up -d && docker compose logs -f api

# Start specific service + its deps
docker compose up api    # starts postgres and redis automatically via depends_on

# Rebuild after changing Dockerfile or dependencies
docker compose up --build api

# Run a one-off command in a service (DB migrations, seeds)
docker compose run --rm api npm run db:migrate
docker compose run --rm api npm run db:seed

# Open a shell in a running container
docker compose exec api sh
docker compose exec postgres psql -U myapp myapp_dev

# Tear down and remove volumes (full reset)
docker compose down -v

# See logs for a specific service
docker compose logs -f --tail=100 api

# Check service health status
docker compose ps
```

# PERFORMANCE OPTIMIZATIONS
```yaml
# Volume mount performance (macOS especially)
volumes:
  - ./src:/app/src:cached      # :cached = host writes flush async (faster)
  - /app/node_modules           # anonymous volume — don't bind mount dependencies

# Use BuildKit for faster image builds
# Set in shell: export DOCKER_BUILDKIT=1
# Or in compose.yaml:
x-build-args: &build-args
  DOCKER_BUILDKIT: "1"

# Layer caching — install deps before copying source
# WRONG order (invalidates cache on every source change):
COPY . .
RUN npm ci

# CORRECT order (deps only reinstall when package.json changes):
COPY package*.json ./
RUN npm ci
COPY . .
```

# COMMON ISSUES & FIXES
```
ISSUE: Port already in use
FIX:   `lsof -ti:5432 | xargs kill` or change host port in compose.yaml

ISSUE: Container starts but app can't connect to postgres
FIX:   Use service name as hostname (postgres, not localhost)
       Ensure depends_on condition: service_healthy (not just started)

ISSUE: node_modules conflicts (macOS bind mount performance)
FIX:   Add anonymous volume for node_modules — compose picks container's version

ISSUE: DB migrations run before postgres is ready
FIX:   Use wait-for-it.sh or healthcheck + depends_on service_healthy

ISSUE: Changes not hot-reloading
FIX:   Check volume mount path matches dev server watch path
       On macOS: check CHOKIDAR_USEPOLLING=true for filesystem polling

ISSUE: Container exits immediately
FIX:   docker compose logs <service> — usually missing env var or crashed process
       Run with docker compose run --rm api sh to debug interactively
```

# DEVELOPER ONBOARDING SCRIPT
```bash
#!/bin/bash
# scripts/setup.sh — run once to set up local environment

set -e

echo "Setting up local development environment..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker required. Install from docker.com"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "Docker Compose V2 required"; exit 1; }

# Environment setup
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — add your API keys"
fi

# Start infrastructure
docker compose up -d postgres redis

# Wait for healthy
echo "Waiting for database..."
docker compose run --rm api sh -c "until pg_isready -h postgres -U myapp; do sleep 1; done"

# Run migrations and seed
docker compose run --rm api npm run db:migrate
docker compose run --rm api npm run db:seed

echo "Setup complete! Run: docker compose up"
```
