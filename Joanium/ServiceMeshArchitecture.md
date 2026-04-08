---
name: Service Mesh Architecture
trigger: service mesh, Istio, Envoy, Linkerd, sidecar proxy, mTLS, traffic management, circuit breaker mesh, service-to-service auth, observability mesh, ingress gateway, east-west traffic
description: Design and operate a service mesh for microservices. Covers sidecar proxies, mTLS, traffic policies, circuit breaking, observability, and when a mesh is and isn't justified.
---

# ROLE
You are a senior platform engineer. A service mesh solves real distributed systems problems — but it adds significant operational complexity. Your job is to configure it correctly and advise when a simpler approach is better.

# WHAT A SERVICE MESH DOES
```
WITHOUT MESH:
  Service A ──HTTP──▶ Service B
  - No encryption in transit between services
  - No automatic retries / circuit breaking
  - No visibility into service-to-service traffic
  - Every team implements their own resilience logic

WITH MESH:
  Service A ──▶ [Envoy sidecar] ──mTLS──▶ [Envoy sidecar] ──▶ Service B
  - Automatic mTLS (zero-trust network layer)
  - Retries, timeouts, circuit breaking in proxy — no app code changes
  - Rich metrics, traces, access logs — free, for all services
  - Traffic shaping: canary deploys, A/B routing, fault injection
```

## Control Plane vs Data Plane
```
DATA PLANE:   Envoy proxies — handle actual traffic
              One sidecar injected per pod automatically
              Intercepts all inbound/outbound traffic via iptables

CONTROL PLANE: Istio / Linkerd — configure the data plane
              Pushes configuration to all Envoy sidecars via xDS API
              Issues and rotates mTLS certificates (SPIFFE/SVID)
              Aggregates telemetry data
```

# CORE CONFIGURATION (ISTIO)

## Traffic Management Resources
```yaml
# VirtualService — how to route traffic to a destination
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: reviews-routing
spec:
  hosts:
    - reviews
  http:
    # Canary: send 10% to v2, 90% to v1
    - route:
        - destination:
            host: reviews
            subset: v1
          weight: 90
        - destination:
            host: reviews
            subset: v2
          weight: 10

    # Header-based routing (for internal testing)
    - match:
        - headers:
            x-canary-user:
              exact: "true"
      route:
        - destination:
            host: reviews
            subset: v2
```

```yaml
# DestinationRule — what to do when traffic arrives at a destination
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: reviews-destination
spec:
  host: reviews
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        h2UpgradePolicy: UPGRADE
        http1MaxPendingRequests: 50
    outlierDetection:        # Circuit breaker
      consecutiveGatewayErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
  subsets:
    - name: v1
      labels:
        version: v1
    - name: v2
      labels:
        version: v2
```

## Retry & Timeout Policy
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: payment-service
spec:
  hosts:
    - payment-service
  http:
    - timeout: 10s         # Overall request timeout
      retries:
        attempts: 3
        perTryTimeout: 3s
        retryOn: gateway-error,connect-failure,retriable-4xx
      route:
        - destination:
            host: payment-service

# retryOn values:
#   gateway-error          → 502, 503, 504
#   connect-failure        → TCP connection failure
#   retriable-4xx          → 409 Conflict
#   reset                  → connection reset by peer
#   retriable-status-codes → custom codes (set x-envoy-retriable-status-codes)

# NEVER retry on:
#   POST/PUT that are non-idempotent without idempotency keys
#   Payments, order creation unless you have idempotency tokens
```

# MUTUAL TLS (mTLS)

## Authentication Policy
```yaml
# STRICT mode — all traffic must be mTLS
# Set at mesh level in MeshConfig, then enforce per-namespace
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production         # apply to whole namespace
spec:
  mtls:
    mode: STRICT                # STRICT | PERMISSIVE | DISABLE

# PERMISSIVE during migration — accepts both plain and mTLS
# STRICT in production — reject all non-mTLS traffic
```

```yaml
# AuthorizationPolicy — which services can talk to which
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-frontend-to-api
  namespace: production
spec:
  selector:
    matchLabels:
      app: api-service
  action: ALLOW
  rules:
    - from:
        - source:
            principals:
              - "cluster.local/ns/production/sa/frontend-service"  # SPIFFE identity
      to:
        - operation:
            methods: ["GET", "POST"]
            paths: ["/api/*"]
```

## Certificate Rotation
```
Istio (Citadel / istiod) handles this automatically:
  - Issues SPIFFE SVIDs (X.509 certs) to each workload
  - Default cert TTL: 24h
  - Rotated before expiry automatically
  - No manual cert management needed

Verify cert issuance:
  istioctl proxy-config secret <pod-name> -n <namespace>
```

# OBSERVABILITY

## What You Get Automatically
```
METRICS (Prometheus):
  istio_requests_total          → request count by source, dest, method, status
  istio_request_duration_ms     → latency histogram
  istio_tcp_connections_opened  → connection counts

TRACES (Jaeger / Zipkin / OTLP):
  Propagate these headers in your app for trace continuity:
  x-request-id
  x-b3-traceid
  x-b3-spanid
  x-b3-parentspanid
  traceparent  (W3C standard — prefer this)

LOGS:
  Access logs from every Envoy — source IP, dest, method, status, duration
  Structured JSON by default in recent Istio versions
```

## Key Metrics to Alert On (Per Service)
```
SUCCESS RATE:
  1 - (sum(rate(istio_requests_total{response_code=~"5.."}[5m])) / sum(rate(istio_requests_total[5m])))

P99 LATENCY:
  histogram_quantile(0.99, sum(rate(istio_request_duration_milliseconds_bucket[5m])) by (le, destination_service_name))

CIRCUIT BREAKER EJECTIONS:
  sum(rate(envoy_cluster_outlier_detection_ejections_active[5m])) by (cluster_name)

PENDING REQUESTS (queue depth proxy):
  envoy_cluster_upstream_rq_pending_total
```

# INGRESS GATEWAY

## Gateway + VirtualService Pattern
```yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: main-gateway
spec:
  selector:
    istio: ingressgateway       # targets the ingress gateway deployment
  servers:
    - port:
        number: 443
        name: https
        protocol: HTTPS
      tls:
        mode: SIMPLE
        credentialName: tls-cert-secret   # Kubernetes secret with cert
      hosts:
        - "api.example.com"
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: api-routing
spec:
  hosts:
    - "api.example.com"
  gateways:
    - main-gateway
  http:
    - match:
        - uri:
            prefix: /v2/
      route:
        - destination:
            host: api-v2-service
            port:
              number: 8080
    - route:
        - destination:
            host: api-v1-service
            port:
              number: 8080
```

# FAULT INJECTION (CHAOS TESTING)

## Built-In Fault Injection
```yaml
# Inject 10% HTTP 503 errors + 5s delay into reviews service
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: reviews-fault-test
spec:
  hosts:
    - reviews
  http:
    - fault:
        abort:
          percentage:
            value: 10.0
          httpStatus: 503
        delay:
          percentage:
            value: 5.0
          fixedDelay: 5s
      route:
        - destination:
            host: reviews

# Only apply fault for specific test users:
    - match:
        - headers:
            x-test-user:
              exact: "chaos"
      fault:
        ...
```

# WHEN TO USE A SERVICE MESH

## Use a Mesh When
```
✓ 10+ microservices that communicate with each other
✓ Zero-trust security requirement — mTLS between every service
✓ Multiple teams, each owning services — consistent observability baseline
✓ Complex traffic routing: canary deploys, A/B, shadow traffic
✓ Need circuit breaking without modifying application code
✓ Compliance requires proof of encrypted service-to-service communication
```

## Don't Use a Mesh When
```
✗ Small number of services (< 5) — use library-level resilience instead
✗ Team doesn't own Kubernetes — mesh requires k8s expertise
✗ Latency-sensitive paths — sidecar adds ~1ms per hop (usually fine, sometimes not)
✗ Short-lived batch jobs — sidecar lifecycle management adds overhead
✗ Monolith with a few external API calls — overkill

Simpler alternatives:
  2–5 services: implement retry/timeout in app code (resilience4j, etc.)
  mTLS without mesh: cert-manager + application-level TLS
  Observability only: OpenTelemetry SDK in each service (no mesh needed)
```

# OPERATIONAL RUNBOOK
```
UPGRADE STRATEGY:
  [ ] Always upgrade control plane before data plane
  [ ] Use canary namespace — deploy new version to test namespace first
  [ ] Verify istiod health: kubectl rollout status deploy/istiod -n istio-system
  [ ] Monitor error rates during rollout

COMMON ISSUES:

503 errors after deploy:
  → Check Envoy config: istioctl proxy-config cluster <pod>
  → Check AuthorizationPolicy — did a new STRICT policy block traffic?
  → Check endpoint health: istioctl proxy-config endpoint <pod>

High Envoy sidecar CPU:
  → Reduce access log verbosity (disable for health check paths)
  → Use WasmPlugin instead of EnvoyFilter where possible
  → Consider meshConfig.accessLogFile: "" in high-volume services

mTLS PERMISSIVE → STRICT migration:
  1. Apply PERMISSIVE to namespace
  2. Confirm all services have sidecars injected
  3. Monitor: no plain-text traffic in Kiali/Zipkin
  4. Switch to STRICT
  5. Verify: test direct pod-to-pod connection is rejected

DAILY CHECKS:
  [ ] istiod pods healthy
  [ ] Certificate expiry warnings in logs
  [ ] Envoy pilot push latency (should be < 5s for config propagation)
  [ ] Check circuit breaker ejection metrics — unexpected spikes = upstream issues
```
