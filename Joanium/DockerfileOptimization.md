---
name: Dockerfile Optimization
trigger: dockerfile, docker image, docker build, image size, layer caching, multi-stage build, container image, docker optimize, slow docker build, large docker image, docker best practices, .dockerignore
description: Write and optimize Dockerfiles for small image size, fast builds, and production security. Use this skill whenever the user shares a Dockerfile, complains about slow builds or large images, asks about multi-stage builds, layer caching, or wants to containerize an application correctly. Covers language-specific patterns for Node, Python, Go, and Java.
---

# ROLE
You are a container engineer. You write Dockerfiles that build fast (cached layers), produce small images (only what's needed), and run securely (non-root, minimal attack surface).

# THE FOUR GOALS
```
1. FAST BUILDS    → layer caching, parallelism, .dockerignore
2. SMALL IMAGES   → multi-stage builds, minimal base images
3. SECURE         → non-root user, no secrets in layers, pinned versions
4. REPRODUCIBLE   → pinned base image digests, lock files committed
```

# LAYER CACHING — THE FUNDAMENTAL RULE

```dockerfile
# Cache breaks from the CHANGED layer downward.
# Order: things that change least → things that change most

# BAD: copy everything first, then install — cache busts on every code change
COPY . .
RUN npm install

# GOOD: install dependencies first (cached as long as package.json doesn't change)
COPY package.json package-lock.json ./
RUN npm ci --production
COPY . .                # code changes don't bust dependency layer
```

# MULTI-STAGE BUILDS (Always Use for Production)

```dockerfile
# ============================================================
# Node.js — Multi-stage
# ============================================================
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --production

FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs
USER nextjs

COPY --from=deps --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/dist ./dist
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./

EXPOSE 3000
CMD ["node", "dist/index.js"]
```

```dockerfile
# ============================================================
# Python (FastAPI / Flask) — Multi-stage
# ============================================================
FROM python:3.12-slim AS builder
WORKDIR /app

RUN pip install --upgrade pip
COPY requirements.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim AS runner
WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

# Non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# ============================================================
# Go — distroless (minimal attack surface)
# ============================================================
FROM golang:1.22-alpine AS builder
WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o server ./cmd/server

FROM gcr.io/distroless/static:nonroot AS runner
COPY --from=builder /app/server /server
EXPOSE 8080
ENTRYPOINT ["/server"]
```

```dockerfile
# ============================================================
# Java (Spring Boot) — layered jar
# ============================================================
FROM eclipse-temurin:21-jdk-alpine AS builder
WORKDIR /app
COPY mvnw pom.xml ./
COPY .mvn .mvn
RUN ./mvnw dependency:go-offline -q

COPY src ./src
RUN ./mvnw package -DskipTests -q

# Extract Spring Boot layers for better caching
RUN java -Djarmode=layertools -jar target/*.jar extract --destination extracted

FROM eclipse-temurin:21-jre-alpine AS runner
WORKDIR /app
RUN addgroup -S spring && adduser -S spring -G spring
USER spring:spring

COPY --from=builder /app/extracted/dependencies ./
COPY --from=builder /app/extracted/spring-boot-loader ./
COPY --from=builder /app/extracted/snapshot-dependencies ./
COPY --from=builder /app/extracted/application ./

EXPOSE 8080
ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]
```

# .dockerignore (ALWAYS CREATE)

```
# .dockerignore
node_modules/
npm-debug.log
.git/
.gitignore
.env
.env.*
*.md
docs/
tests/
coverage/
.DS_Store
Dockerfile*
docker-compose*
.dockerignore

# Python
__pycache__/
*.pyc
*.pyo
.venv/
.pytest_cache/

# Go
vendor/
*.test

# Build artifacts
dist/
build/
target/
*.jar
!app.jar
```

# BASE IMAGE SELECTION

```
Prefer smaller base images:
  ubuntu:22.04    → 77MB  (too large for most apps)
  debian:bookworm-slim → 75MB
  alpine:3.19     → 7MB   (musl libc — some native modules break)
  distroless      → 2MB   (Google, no shell — best for Go/Java)
  scratch         → 0MB   (only for fully static binaries)

Language recommendations:
  Node.js  → node:20-alpine
  Python   → python:3.12-slim  (alpine can cause issues with some wheels)
  Go       → gcr.io/distroless/static:nonroot
  Java     → eclipse-temurin:21-jre-alpine
  Rust     → gcr.io/distroless/cc:nonroot

Always pin to a specific version tag — never :latest in production
```

# SECURITY PRACTICES

```dockerfile
# 1. Always run as non-root
RUN addgroup --system --gid 1001 app && \
    adduser --system --uid 1001 --ingroup app app
USER app

# 2. Never store secrets in ENV or ARG (visible in image history)
# BAD:
ENV DATABASE_URL=postgres://user:password@host/db

# GOOD: Pass secrets at runtime via env or secrets manager
# docker run -e DATABASE_URL=... myimage
# Or use Docker secrets / Kubernetes secrets

# 3. Pin base image by digest for reproducibility
FROM node:20.11.0-alpine3.19@sha256:abc123...

# 4. Minimize installed packages
RUN apk add --no-cache curl  # --no-cache avoids caching package index
# Remove build deps after use
RUN apk add --no-cache --virtual .build-deps gcc musl-dev \
    && pip install cryptography \
    && apk del .build-deps

# 5. COPY specific files, not entire context
COPY src/ ./src/
COPY package.json ./
# NOT: COPY . .   (unless .dockerignore is comprehensive)
```

# HEALTHCHECK

```dockerfile
# Always add HEALTHCHECK for production containers
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# For distroless images (no curl):
HEALTHCHECK --interval=30s --timeout=3s \
  CMD ["/server", "--healthcheck"]
```

# COMMON MISTAKES

```dockerfile
# ❌ Installing build tools in final image
RUN apt-get install -y build-essential python3-dev
# ✓ Put these in a builder stage only

# ❌ Running as root
USER root  # or not specifying USER at all
# ✓ Always USER nonroot

# ❌ Multiple RUN commands that could be combined
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get clean
# ✓ Chain into one layer
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# ❌ COPY . . before installing dependencies
COPY . .
RUN npm install
# ✓ Install deps from lockfile first (see caching section)

# ❌ Not using --production / --no-dev for production builds
RUN npm install              # installs devDependencies too
# ✓
RUN npm ci --omit=dev
```

# QUICK SIZE AUDIT

```bash
# See image layers and sizes
docker history myimage:latest --human --format "{{.Size}}\t{{.CreatedBy}}"

# Dive tool — interactive layer explorer
docker run --rm -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  wagoodman/dive:latest myimage:latest

# Check final image size
docker images myimage --format "{{.Size}}"
```
