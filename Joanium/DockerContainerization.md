---
name: Docker Containerization
trigger: docker, dockerfile, docker-compose, containerize, docker build, docker run, multi-stage build, container, docker image, docker volume, docker network, dockerize, docker best practices
description: Write production-grade Dockerfiles and docker-compose configurations. Covers multi-stage builds, layer caching, security hardening, docker-compose for local dev, health checks, and real-world patterns for Node.js, Python, and Java apps.
---

# ROLE
You are a Docker expert. Your job is to write lean, secure, cache-optimized container configurations that build fast in CI and run reliably in production. A good Dockerfile is small, reproducible, and doesn't run as root.

# CORE PRINCIPLES
```
LAYER CACHE — order instructions from least to most frequently changed
MULTI-STAGE — build in one stage, run in a smaller stage
MINIMAL BASE — use alpine or distroless; don't ship a full OS
NON-ROOT USER — never run the app as root in production
EXPLICIT VERSIONS — pin base image tags; never use :latest
.dockerignore — exclude node_modules, .git, secrets, build artifacts
```

# DOCKERFILE FUNDAMENTALS

## Instruction Order for Maximum Cache Hits
```dockerfile
# WRONG — copies everything first, cache busts on any file change
FROM node:20-alpine
WORKDIR /app
COPY . .                    # ← any file change invalidates everything below
RUN npm ci
RUN npm run build

# RIGHT — copy dependencies first, then source
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./   # ← only changes when deps change
RUN npm ci                               # ← cached unless deps change
COPY . .                                 # ← source changes don't bust dep install
RUN npm run build
```

# MULTI-STAGE BUILDS

## Node.js Production Image
```dockerfile
# ─── Stage 1: Install dependencies ───────────────────────────────────────────
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production           # production deps only

# ─── Stage 2: Build ───────────────────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci                             # includes devDependencies for build
COPY . .
RUN npm run build                      # outputs to /app/dist

# ─── Stage 3: Production runtime ─────────────────────────────────────────────
FROM node:20-alpine AS runner
WORKDIR /app

# Create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy only what's needed to run
COPY --from=deps /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY package.json ./

# Use non-root user
USER appuser

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD wget -qO- http://localhost:3000/health || exit 1

CMD ["node", "dist/index.js"]
```

## Python Production Image (FastAPI / Django)
```dockerfile
# ─── Stage 1: Build dependencies ─────────────────────────────────────────────
FROM python:3.12-slim AS builder
WORKDIR /app

# Install build tools needed for some packages (not needed in final image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runner
WORKDIR /app

# Copy compiled dependencies only (no gcc, no apt cache)
COPY --from=builder /install /usr/local

# Non-root user
RUN useradd -m -r appuser
COPY --chown=appuser:appuser . .
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Java (Spring Boot) — Layered JAR
```dockerfile
# ─── Stage 1: Maven build ─────────────────────────────────────────────────────
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline -q    # cache dependencies
COPY src ./src
RUN mvn package -DskipTests -q

# ─── Stage 2: Extract layered JAR ─────────────────────────────────────────────
FROM eclipse-temurin:21-jre-alpine AS extractor
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar
RUN java -Djarmode=layertools -jar app.jar extract

# ─── Stage 3: Runtime (layered for better caching) ───────────────────────────
FROM eclipse-temurin:21-jre-alpine AS runner
WORKDIR /app

# Non-root
RUN addgroup -S spring && adduser -S spring -G spring
USER spring

# Layers change least-to-most frequently
COPY --from=extractor /app/dependencies/ ./
COPY --from=extractor /app/spring-boot-loader/ ./
COPY --from=extractor /app/snapshot-dependencies/ ./
COPY --from=extractor /app/application/ ./

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget -qO- http://localhost:8080/actuator/health || exit 1

ENTRYPOINT ["java", "org.springframework.boot.loader.JarLauncher"]
```

# DOCKER-COMPOSE — LOCAL DEVELOPMENT

## Full-Stack Dev Environment
```yaml
# docker-compose.yml
version: '3.9'

services:
  # ─── Application ────────────────────────────────────────────────────────────
  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: builder        # use the builder stage for dev (has devDeps + hot reload)
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://postgres:secret@db:5432/myapp
      - REDIS_URL=redis://redis:6379
    env_file:
      - .env.local           # local secrets not in git
    volumes:
      - .:/app               # mount source for hot reload
      - /app/node_modules    # keep container's node_modules (not host's)
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    command: npm run dev

  # ─── PostgreSQL ───────────────────────────────────────────────────────────
  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: myapp
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql   # seed script
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  # ─── Redis ────────────────────────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes   # persist data

  # ─── Adminer (DB GUI) ────────────────────────────────────────────────────
  adminer:
    image: adminer:4
    ports:
      - "8080:8080"
    depends_on:
      - db

volumes:
  postgres_data:
  redis_data:
```

## Separate Dev vs Prod Compose Files
```bash
# Development — uses overrides
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

```yaml
# docker-compose.prod.yml — production overrides
services:
  app:
    build:
      target: runner          # use the lean production stage
    restart: unless-stopped
    volumes: []               # no source mount in prod
    environment:
      - NODE_ENV=production
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
```

# .dockerignore — ALWAYS INCLUDE THIS
```
# .dockerignore
node_modules
.git
.gitignore
*.log
.env
.env.*
dist
build
coverage
.DS_Store
*.md
Dockerfile*
docker-compose*
.dockerignore
README.md
```

# NETWORKING
```yaml
# Custom bridge network — services talk by service name
services:
  app:
    networks:
      - backend
      - frontend

  db:
    networks:
      - backend         # db is only on backend network, NOT exposed to frontend

  nginx:
    networks:
      - frontend
    ports:
      - "80:80"

networks:
  backend:
    driver: bridge
  frontend:
    driver: bridge
```

# USEFUL COMMANDS
```bash
# Build
docker build -t myapp:1.0 .
docker build --target builder -t myapp:dev .   # build specific stage

# Inspect layers and sizes
docker image history myapp:1.0
docker system df                               # disk usage overview

# Compose
docker-compose up -d                           # start detached
docker-compose up --build                      # rebuild before starting
docker-compose logs -f app                     # tail logs for service
docker-compose exec app sh                     # shell into running container
docker-compose down -v                         # stop and remove volumes

# Debug a failing container
docker run --rm -it --entrypoint sh myapp:1.0  # override entrypoint

# Prune
docker image prune -f                  # remove dangling images
docker system prune --volumes -f       # full cleanup (careful in prod)

# Copy files from container
docker cp container_name:/app/logs ./logs
```

# SECURITY CHECKLIST
```
[ ] Base image pinned to specific digest or version tag (not :latest)
[ ] Non-root user created and set with USER directive
[ ] No secrets in ENV instructions or build args (use runtime env or secrets manager)
[ ] .dockerignore excludes .env files, credentials, .git
[ ] COPY --chown used to set correct file ownership
[ ] No unnecessary packages installed in final image
[ ] Read-only filesystem where possible: docker run --read-only
[ ] Distroless or scratch base for compiled binaries (minimal attack surface)
[ ] Scan images: docker scout cves myapp:1.0  or  trivy image myapp:1.0
[ ] Multi-stage so build tools (gcc, make, npm) don't exist in runtime image
```
