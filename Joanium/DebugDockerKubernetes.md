---
name: Debug — Docker / Kubernetes
trigger: docker bug, kubernetes error, container crash, pod crashing, crashloopbackoff, imagepullbackoff, docker build failing, container not starting, k8s error, kubectl, docker compose failing, oomkilled, pending pod, service not reachable
description: Hyper-specific debugging guide for Docker and Kubernetes. Real error states, real commands, real fixes. Covers container crashes, build failures, K8s pod states, networking, resource issues, and config debugging.
---

# Debug — Docker / Kubernetes

---

# DOCKER

## First Move

```bash
# See all containers — running AND stopped
docker ps -a

# See what a container is actually doing / why it failed
docker logs container_name           # all logs
docker logs container_name --tail 50  # last 50 lines
docker logs container_name -f         # follow (live tail)
docker logs container_name 2>&1 | grep -i "error\|fatal\|exception"

# Inspect the container config, mounts, env vars, exit code
docker inspect container_name

# Check exit code
docker inspect container_name --format='{{.State.ExitCode}}'
# 0 = success, 1 = app error, 137 = OOM killed (SIGKILL), 143 = SIGTERM

# Get into a running container
docker exec -it container_name bash
docker exec -it container_name sh   # if bash not available

# Get into a crashed/stopped container (can't exec into stopped container)
# Override entrypoint to get a shell instead
docker run -it --entrypoint sh image_name
```

---

## Container Crashes Immediately

```bash
# Check exit code and last logs
docker ps -a  # see Status column — "Exited (1)" or "Exited (137)"
docker logs <container_id>

# Exit code meanings:
# 1    → App crashed — check logs for the error
# 137  → OOM killed (out of memory)
# 139  → Segfault
# 143  → Graceful shutdown (SIGTERM) — probably intentional

# Run interactively to see what happens
docker run --rm -it image_name   # --rm removes container after exit
# If your entrypoint is a script, override it:
docker run --rm -it --entrypoint /bin/sh image_name
# Now manually run the startup command to see the error

# Container exits because process finishes — it's not a server
# Fix: ensure your CMD runs a foreground process, not a background one
CMD ["node", "server.js"]       # Good — foreground
CMD ["node", "server.js &"]     # Bad — process goes to background, container exits
```

---

## Docker Build Failures

```dockerfile
# Build with no cache — forces fresh build to catch stale layer issues
docker build --no-cache -t myapp .

# Build with verbose output
docker build --progress=plain -t myapp . 2>&1 | tee build.log

# Common build errors:

# 1. "failed to solve: failed to read dockerfile"
# → Dockerfile not found in build context
ls Dockerfile  # check it exists
# Or specify path:
docker build -f path/to/Dockerfile .

# 2. "COPY failed: file not found"
# → File not in build context (excluded by .dockerignore or wrong path)
cat .dockerignore  # check what's excluded
# Files must be INSIDE the build context (the . at end of docker build command)
# Cannot COPY ../outside_context/file — fix: move build context up

# 3. Package install failures (node_modules, pip, apt)
# Often caused by expired apt cache in a cached layer
# Fix: --no-cache or bust the cache with a build arg:
ARG CACHE_BUST=1
RUN apt-get update && apt-get install -y curl  # Layer re-runs when CACHE_BUST changes

# 4. Permission denied errors
# Fix: run as correct user, or set permissions
RUN chown -R node:node /app
USER node  # run as non-root (also a security best practice)

# 5. Multi-stage build — wrong stage name
FROM node:20-alpine AS builder   # stage name is "builder"
COPY --from=builder /app/dist .  # must match exactly
```

---

## Docker Compose Issues

```bash
# Bring up with log output
docker compose up          # foreground — see all logs
docker compose up -d       # background
docker compose up --build  # rebuild images before starting

# See logs per service
docker compose logs web
docker compose logs db --tail 30 -f

# Service can't connect to another service
# Services talk to each other by SERVICE NAME, not localhost
# In your app config:
DATABASE_URL=postgresql://user:pass@db:5432/dbname  # 'db' = service name in compose
REDIS_URL=redis://redis:6379                         # 'redis' = service name

# Wait for dependencies — services start in parallel, not sequentially
# Use depends_on with health checks:
services:
  web:
    depends_on:
      db:
        condition: service_healthy  # waits until db is healthy
  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

# Volume mount changes not reflecting
docker compose down -v  # -v removes volumes too — careful!
docker compose up --build

# Port already in use
lsof -ti:5432 | xargs kill -9  # kill what's on that port
```

---

## Common Dockerfile Optimizations

```dockerfile
# LAYER CACHING: put less-frequently-changing layers first
# Bad — package installs re-run every time ANY source file changes:
COPY . .
RUN npm install

# Good — node_modules layer cached until package.json changes:
COPY package*.json ./
RUN npm install
COPY . .     # source code changes don't bust the npm install layer

# .dockerignore — always create this
echo "node_modules
.git
.env
*.log
dist" > .dockerignore

# Multi-stage builds — small production images
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS production
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["node", "dist/index.js"]
# Result: ~150MB instead of 1GB+ development image
```

---

# KUBERNETES

## Pod Debugging

```bash
# See all pods and their status
kubectl get pods -n namespace
kubectl get pods --all-namespaces   # all namespaces

# See why a pod is in a bad state
kubectl describe pod pod-name -n namespace
# Read the Events section at the bottom — most diagnostic info is there

# See pod logs
kubectl logs pod-name -n namespace
kubectl logs pod-name -n namespace --previous    # logs from previous crashed container
kubectl logs pod-name -n namespace -f             # follow live
kubectl logs pod-name -n namespace -c container  # specific container in pod

# Shell into a running pod
kubectl exec -it pod-name -n namespace -- bash
kubectl exec -it pod-name -n namespace -- sh  # if bash unavailable

# Run a debug pod (when the actual pod keeps crashing)
kubectl run debug --image=busybox --rm -it --restart=Never -- sh
kubectl run debug --image=postgres:16 --rm -it --restart=Never -- psql -h db-service -U postgres
```

---

## Pod States and Fixes

### `CrashLoopBackOff`

```bash
# Pod keeps crashing and restarting — exponential backoff kicks in
kubectl logs pod-name --previous  # logs from BEFORE the restart
kubectl describe pod pod-name     # check Events section

# Common causes:
# 1. App crashes on startup — check logs for the exception
# 2. Missing environment variable — app exits when required config is absent
#    Fix: check env vars are set in deployment spec
kubectl get deployment my-app -o yaml | grep -A 20 'env:'

# 3. Liveness probe failing — K8s kills the pod because it thinks it's unhealthy
kubectl describe pod pod-name | grep -A 10 "Liveness\|Readiness"
# Fix: check probe endpoint actually returns 200
# Fix: increase initialDelaySeconds if app takes time to start
livenessProbe:
  httpGet:
    path: /health
    port: 3000
  initialDelaySeconds: 30   # wait 30s before first check
  failureThreshold: 5        # allow 5 failures before killing

# 4. OOMKilled — out of memory
kubectl describe pod pod-name | grep -A 5 "OOMKilled\|memory"
# Fix: increase memory limit in deployment
resources:
  requests:
    memory: "256Mi"
  limits:
    memory: "512Mi"  # increase this
```

### `ImagePullBackOff` / `ErrImagePull`

```bash
kubectl describe pod pod-name | grep -A 10 "Events:"
# Look for: "Failed to pull image" or "unauthorized" or "not found"

# 1. Image doesn't exist / wrong tag
kubectl get deployment my-app -o yaml | grep image:
docker pull your-registry/image:tag  # test pulling manually

# 2. Private registry — missing pull secret
kubectl get secret -n namespace  # is there a registry secret?
# Create it:
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=pass \
  --namespace=namespace

# Add to deployment:
spec:
  imagePullSecrets:
    - name: regcred

# 3. Rate limited (Docker Hub)
# Use a registry mirror or authenticate to raise limits
```

### `Pending` Pod

```bash
kubectl describe pod pod-name  # check Events for reason

# 1. Insufficient resources — no node has enough CPU/memory
# Events show: "0/3 nodes are available: 3 Insufficient memory"
kubectl top nodes  # check node resource usage
kubectl describe nodes | grep -A 5 "Allocated resources"
# Fix: increase resource limits or add more nodes

# 2. No matching node selector / affinity
kubectl get node --show-labels  # check what labels nodes have
# Check pod's nodeSelector or affinity rules match existing nodes

# 3. PersistentVolumeClaim not bound
kubectl get pvc -n namespace
# STATUS should be Bound — if Pending, the PV doesn't exist or storage class wrong
kubectl describe pvc pvc-name  # see why it's not binding
```

---

## Service Networking Debugging

```bash
# Test service DNS resolution from inside the cluster
kubectl run dns-test --image=busybox --rm -it --restart=Never -- \
  nslookup my-service.namespace.svc.cluster.local

# Service name format: <service-name>.<namespace>.svc.cluster.local
# Within same namespace: just <service-name>

# Test if service is reachable
kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never -- \
  curl -v http://my-service:3000/health

# Check service endpoints — are any pods actually behind the service?
kubectl get endpoints my-service -n namespace
# If ENDPOINTS is "<none>" — the service selector doesn't match any pod labels

# Check the service selector vs pod labels
kubectl get service my-service -o yaml | grep -A 5 selector:
kubectl get pods --show-labels | grep my-service-label
# The labels must match exactly

# Port-forward to test a service locally
kubectl port-forward service/my-service 8080:3000 -n namespace
# Now: curl localhost:8080  (proxies to service:3000)

# Port-forward directly to a pod
kubectl port-forward pod/my-pod-abc123 8080:3000 -n namespace
```

---

## ConfigMap / Secret Issues

```bash
# Verify the secret/configmap exists and has the right keys
kubectl get configmap my-config -n namespace -o yaml
kubectl get secret my-secret -n namespace -o yaml
# Secret values are base64 encoded — decode to verify:
kubectl get secret my-secret -o jsonpath='{.data.API_KEY}' | base64 --decode

# Verify the pod is mounting the right values
kubectl exec -it pod-name -- env | grep MY_VAR     # check env var is set
kubectl exec -it pod-name -- cat /etc/config/file  # check mounted file

# Secret/ConfigMap updated but pod didn't pick it up
# Pods only see new values if they restart (for env vars)
# For mounted files — they update automatically within ~1 minute
kubectl rollout restart deployment/my-app  # trigger rolling restart
```

---

## Resource and OOM Issues

```bash
# Check resource usage across all pods
kubectl top pods -n namespace
kubectl top nodes

# Find pods without resource limits (dangerous in production)
kubectl get pods -o json | jq '.items[] | select(.spec.containers[].resources.limits == null) | .metadata.name'

# Recommended resource spec:
resources:
  requests:            # what the scheduler uses to place the pod
    cpu: "100m"        # 100 millicores = 0.1 CPU
    memory: "128Mi"
  limits:              # hard cap — OOMKill if exceeded
    cpu: "500m"
    memory: "512Mi"

# HPA (autoscaler) not scaling — check metrics server
kubectl get hpa -n namespace
kubectl describe hpa my-hpa -n namespace
# Metrics: <unknown>/50% means metrics-server isn't running
kubectl get deployment metrics-server -n kube-system
```
