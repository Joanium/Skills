---
name: Monitoring Observability
trigger: monitoring, observability, logging, metrics, tracing, prometheus, grafana, datadog, sentry, alerting, logs, error tracking, performance monitoring, SLO, SLA, dashboards, pagerduty
description: Design and implement observability for production systems. Covers structured logging, metrics, distributed tracing, alerting, SLOs, dashboards, and incident response tooling.
---

# ROLE
You are a site reliability engineer. Your job is to make systems understandable from the outside — so when something breaks at 3am, the right person can diagnose and fix it in minutes, not hours.

# THE THREE PILLARS
```
LOGS    → what happened and why (discrete events, queryable)
METRICS → what is happening right now (numbers over time, alertable)
TRACES  → where did this request go (latency breakdown, dependency map)

USE EACH FOR ITS PURPOSE:
  Logs   → debugging a specific incident ("what happened to order 123?")
  Metrics → detecting and alerting on trends ("error rate spiked at 14:32")
  Traces → performance diagnosis ("why is this endpoint taking 3s?")
```

# STRUCTURED LOGGING

## The Right Way to Log
```typescript
// WRONG: unstructured — impossible to search, parse, alert on
console.log("User 123 placed order 456 for $89.99 at 2024-01-15")
console.log("Error processing payment for order " + orderId)

// RIGHT: structured JSON — every field is queryable
import pino from 'pino'  // Node.js
const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  base: { service: 'order-service', version: process.env.APP_VERSION },
})

logger.info({ orderId, userId, amount: 89.99, currency: 'USD' }, 'Order placed')
logger.error({ orderId, error: err.message, stack: err.stack }, 'Payment processing failed')

// Output (easily parsed by Datadog/CloudWatch/Loki):
// {"level":"info","time":"2024-01-15T10:30:00Z","service":"order-service","orderId":"ord_123","userId":"usr_456","amount":89.99,"msg":"Order placed"}
```

```python
# Python — structlog
import structlog

logger = structlog.get_logger()
log = logger.bind(service="order-service", version=os.getenv("APP_VERSION"))

log.info("order_placed", order_id=order_id, user_id=user_id, amount=89.99)
log.error("payment_failed", order_id=order_id, error=str(e), exc_info=True)
```

## What to Log — and What Not To
```
LOG: request start/end (with duration), state transitions, errors (with context),
     security events (login, permission denied), background job start/complete/fail

DON'T LOG: passwords, tokens, PII (unless masked), raw SQL queries in production,
           health check hits (noise), successful cache hits (noise)

LOG LEVELS:
  ERROR  → something broke, needs attention (triggers alerts)
  WARN   → degraded state, not broken (no alert, but worth reviewing)
  INFO   → normal business events (order placed, user registered)
  DEBUG  → detailed diagnostic info (only enabled when debugging)
```

## Request Context Propagation
```typescript
// Every log line for a request should share a request ID
// Use AsyncLocalStorage (Node.js) to propagate without passing through every function

import { AsyncLocalStorage } from 'async_hooks'
const requestContext = new AsyncLocalStorage<{ requestId: string; userId?: string }>()

// Middleware: set context at start of request
app.use((req, res, next) => {
  const requestId = req.headers['x-request-id'] as string || crypto.randomUUID()
  res.setHeader('x-request-id', requestId)  // echo back to client

  requestContext.run({ requestId, userId: req.user?.id }, next)
})

// Logger: automatically includes context in every log
const logger = pino({
  mixin() {
    return requestContext.getStore() ?? {}  // adds requestId + userId to every log line
  }
})
```

# METRICS

## The Four Golden Signals (Monitor These First)
```
1. LATENCY      → how long requests take (p50, p95, p99)
2. TRAFFIC      → how much demand (requests/sec, events/sec)
3. ERRORS       → rate of failures (error %, 5xx rate)
4. SATURATION   → how full the system is (CPU %, memory %, queue depth)
```

## Prometheus Metrics in Node.js
```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client'
const register = new Registry()

// Counter — monotonically increasing
const httpRequestsTotal = new Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'route', 'status'],
  registers: [register]
})

// Histogram — distribution of values (latency buckets)
const httpRequestDurationMs = new Histogram({
  name: 'http_request_duration_ms',
  help: 'HTTP request latency in milliseconds',
  labelNames: ['method', 'route', 'status'],
  buckets: [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000],
  registers: [register]
})

// Gauge — value that goes up and down
const activeConnections = new Gauge({
  name: 'active_connections',
  help: 'Number of active DB connections',
  registers: [register]
})

// Middleware to record all request metrics automatically
app.use((req, res, next) => {
  const start = Date.now()
  res.on('finish', () => {
    const duration = Date.now() - start
    const labels = { method: req.method, route: req.route?.path ?? req.path, status: res.statusCode }
    httpRequestsTotal.inc(labels)
    httpRequestDurationMs.observe(labels, duration)
  })
  next()
})

// Expose /metrics endpoint for Prometheus to scrape
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType)
  res.send(await register.metrics())
})
```

## Prometheus Query Language (PromQL) — Useful Queries
```promql
# Error rate (last 5 minutes)
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100

# 95th percentile latency
histogram_quantile(0.95, rate(http_request_duration_ms_bucket[5m]))

# Requests per second by route
topk(10, rate(http_requests_total[5m])) by (route)

# Alert: error rate > 1% for 5 minutes
ALERT HighErrorRate
  IF rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
  FOR 5m
  LABELS { severity="critical" }
  ANNOTATIONS { summary="Error rate above 1%" }
```

# DISTRIBUTED TRACING

## OpenTelemetry (Vendor-Neutral Standard)
```typescript
// instrumentation.ts — initialize before app starts
import { NodeSDK } from '@opentelemetry/sdk-node'
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http'
import { HttpInstrumentation } from '@opentelemetry/instrumentation-http'
import { ExpressInstrumentation } from '@opentelemetry/instrumentation-express'
import { PgInstrumentation } from '@opentelemetry/instrumentation-pg'

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT  // Jaeger, Tempo, Datadog, etc.
  }),
  instrumentations: [
    new HttpInstrumentation(),      // auto-traces all HTTP requests
    new ExpressInstrumentation(),   // auto-traces Express routes
    new PgInstrumentation(),        // auto-traces all DB queries
  ]
})
sdk.start()
// This gives you traces with zero code changes in your handlers

// Custom spans for business logic
import { trace } from '@opentelemetry/api'
const tracer = trace.getTracer('order-service')

async function processPayment(order: Order) {
  const span = tracer.startSpan('processPayment', {
    attributes: { 'order.id': order.id, 'order.amount': order.total }
  })
  try {
    const result = await chargeStripe(order)
    span.setAttributes({ 'stripe.charge_id': result.id })
    return result
  } catch (err) {
    span.recordException(err)
    span.setStatus({ code: SpanStatusCode.ERROR })
    throw err
  } finally {
    span.end()
  }
}
```

# SLOs (Service Level Objectives)

## Defining SLOs
```yaml
# SLI: what you measure  |  SLO: the target  |  Error Budget: the tolerance

service: api-gateway

slos:
  - name: Availability
    sli: "successful requests / total requests"
    target: 99.9%              # 43.8 min downtime/month allowed
    window: 30d

  - name: Latency
    sli: "requests completing in < 200ms"
    target: 95%                # 95th percentile under 200ms
    window: 30d

  - name: Error Rate
    sli: "non-5xx responses / total responses"
    target: 99.5%
    window: 30d

error_budget_policy:
  - burn_rate: 14x → page immediately (consuming 1h budget in 5 min)
  - burn_rate: 6x  → alert (consuming 1d budget in 1h)
  - burn_rate: 1x  → weekly review
```

## Grafana Dashboard Setup
```json
// Key panels for every service dashboard:
// 1. Request Rate (req/s)
// 2. Error Rate (%)
// 3. Latency p50 / p95 / p99
// 4. Apdex Score (satisfaction metric)
// 5. Active Instances / Pod Count
// 6. CPU / Memory Usage
// 7. DB Connection Pool (used / max)
// 8. External API latency (Stripe, Sendgrid, etc.)
// 9. Queue Depth (if applicable)
// 10. Error log stream (live tail)
```

# ALERTING — ALERT ON SYMPTOMS, NOT CAUSES
```yaml
# BAD ALERT: alerts on cause
- alert: HighCpuUsage
  when: cpu > 80%
  # CPU at 80% with 0% error rate = irrelevant. Users aren't affected.

# GOOD ALERT: alerts on symptom (user-visible impact)
- alert: HighErrorRate
  when: error_rate > 1% for 5min
  severity: critical
  runbook: https://wiki/runbooks/high-error-rate

- alert: HighLatency
  when: p99_latency > 2000ms for 5min
  severity: warning
  runbook: https://wiki/runbooks/high-latency

- alert: ServiceDown
  when: availability < 99% for 2min
  severity: critical
  page: true

# ALERT RULES:
# 1. Every alert has a runbook link
# 2. Every alert has a clear action the on-call can take
# 3. Alerts that fire and require no action = alert fatigue = ignored alerts
# 4. Review alert frequency monthly — high-frequency alerts with no action = delete them
```

# RUNBOOK TEMPLATE
```markdown
## Alert: HighErrorRate

**Severity:** Critical  
**SLO Impact:** Consuming error budget at >6x rate

### 1. Verify the alert
```bash
# Check current error rate
curl -s 'https://prometheus/api/v1/query?query=...' | jq .
# Check which endpoints are affected
kubectl logs -n prod -l app=api --tail=100 | grep '"level":"error"'
```

### 2. Common Causes & Fixes
| Symptom | Cause | Fix |
|---------|-------|-----|
| All endpoints 500 | DB connection failed | `kubectl rollout restart deployment/api` |
| Specific endpoint 500 | Bad deploy | `kubectl rollout undo deployment/api` |
| 503 responses | Pod OOMKilled | Increase memory limit, redeploy |

### 3. Escalation
- 5 min no improvement → page team lead
- 15 min no improvement → incident commander  

### 4. Post-Incident
- Write incident report within 24h
- Add regression test for root cause
```
