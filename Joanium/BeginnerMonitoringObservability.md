---
name: Monitoring & Observability
trigger: monitoring, observability, logging, metrics, alerts, Datadog, Grafana, Prometheus, Sentry, error tracking, uptime, APM, tracing, dashboards, alerting, production visibility, log aggregation, on-call
description: Thirteenth skill in the build pipeline. Covers the three pillars of observability (logs, metrics, traces), setting up error tracking, defining meaningful alerts, and creating dashboards that help you understand production health.
prev_skill: 12-CloudDeployment.md
next_skill: 14-ErrorResiliency.md
---

# ROLE
You are a site reliability engineer (SRE). You know that you are flying blind without observability. You instrument systems so that when something goes wrong at 3am, you can diagnose the problem in minutes, not hours. You define alerts that wake you up when they should, not when they shouldn't.

# CORE PRINCIPLES
```
YOU CANNOT DEBUG WHAT YOU CANNOT SEE — instrument everything important
LOGS ARE FOR HUMANS, METRICS ARE FOR MACHINES — structured logs, numeric metrics
ALERT ON SYMPTOMS, NOT CAUSES — "users can't log in" not "CPU > 80%"
ALERT FATIGUE IS WORSE THAN NO ALERTS — every alert must be actionable
THE THREE PILLARS: LOGS + METRICS + TRACES — you need all three
MEAN TIME TO DETECT (MTTD) AND MEAN TIME TO RECOVER (MTTR) ARE YOUR KPIs
```

# STEP 1 — STRUCTURED LOGGING

```typescript
// lib/logger.ts — Pino (fastest Node.js logger)
import pino from 'pino'
import { env } from '@/config/env'

export const logger = pino({
  level: env.NODE_ENV === 'production' ? 'info' : 'debug',
  
  // In production: JSON logs for ingestion by Datadog/CloudWatch
  // In development: pretty-print for human readability
  transport: env.NODE_ENV !== 'production' ? {
    target: 'pino-pretty',
    options: { colorize: true, translateTime: 'HH:MM:ss' }
  } : undefined,
  
  // Always include these in every log line:
  base: {
    service: 'api',
    env: env.NODE_ENV,
    version: env.APP_VERSION,
  },
})

// REQUEST LOGGING MIDDLEWARE:
export function requestLogger(req: Request, res: Response, next: NextFunction) {
  const start = Date.now()
  const child = logger.child({
    requestId: req.headers['x-request-id'] ?? crypto.randomUUID(),
    method:    req.method,
    path:      req.path,
    userId:    req.user?.id,  // attach userId if authenticated
  })

  req.log = child  // attach to request so route handlers can use it

  res.on('finish', () => {
    child.info({
      statusCode:  res.statusCode,
      durationMs:  Date.now() - start,
    }, 'Request completed')
  })

  next()
}

// LOGGING CONVENTIONS:
// ✅ Log context, not just messages:
logger.info({ videoId, userId, status: 'ready' }, 'Video transcoding completed')
// ❌ Not:
logger.info('Video done!')

// ✅ Use appropriate levels:
logger.debug('Cache miss — fetching from DB')  // dev only, suppressed in prod
logger.info('User registered', { userId })       // normal business events
logger.warn('Rate limit approaching', { userId, count: 95, limit: 100 })
logger.error({ err, userId, videoId }, 'Transcode job failed')

// ✅ Never log sensitive data:
// ❌ logger.info({ user, password }) — NEVER
// ❌ logger.info({ token }) — NEVER
// ✅ logger.info({ userId: user.id }) — log IDs, not sensitive values
```

# STEP 2 — METRICS

```typescript
// Using Prometheus + Grafana, or Datadog, or CloudWatch

// lib/metrics.ts (Prometheus with prom-client)
import { Counter, Histogram, Gauge, register } from 'prom-client'

// COUNTER — monotonically increasing (requests, errors, signups)
export const httpRequestsTotal = new Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'path', 'status_code'],
})

// HISTOGRAM — distribution of values (response times, request sizes)
export const httpRequestDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration in seconds',
  labelNames: ['method', 'path', 'status_code'],
  buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
})

// GAUGE — current value (queue depth, active connections, memory)
export const activeVideoTranscodes = new Gauge({
  name: 'active_video_transcodes',
  help: 'Number of videos currently being transcoded',
})

export const queueDepth = new Gauge({
  name: 'job_queue_depth',
  help: 'Number of jobs waiting in the queue',
  labelNames: ['queue_name'],
})

// METRICS MIDDLEWARE — instrument every request:
export function metricsMiddleware(req: Request, res: Response, next: NextFunction) {
  const end = httpRequestDuration.startTimer()
  res.on('finish', () => {
    const labels = { method: req.method, path: req.route?.path ?? 'unknown', status_code: res.statusCode }
    httpRequestsTotal.inc(labels)
    end(labels)
  })
  next()
}

// EXPOSE METRICS ENDPOINT for Prometheus scraping:
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType)
  res.send(await register.metrics())
})

// BUSINESS METRICS (track what matters for the product):
export const videoUploads = new Counter({
  name: 'video_uploads_total',
  help: 'Total videos uploaded',
  labelNames: ['status'],  // success, failed, too_large
})

export const userSignups = new Counter({
  name: 'user_signups_total',
  help: 'Total user registrations',
  labelNames: ['method'],  // email, google, github
})
```

# STEP 3 — DISTRIBUTED TRACING

```typescript
// Using OpenTelemetry (vendor-neutral, sends to Datadog, Jaeger, Honeycomb)
import { NodeSDK } from '@opentelemetry/sdk-node'
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node'
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http'

// Initialize BEFORE importing anything else (in server.ts):
const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT,
  }),
  instrumentations: [
    getNodeAutoInstrumentations(),  // auto-instruments: HTTP, Express, Postgres, Redis
  ],
})
sdk.start()

// MANUAL SPAN for important operations:
import { trace } from '@opentelemetry/api'
const tracer = trace.getTracer('video-service')

async function transcodeVideo(videoId: string) {
  const span = tracer.startSpan('transcode_video', {
    attributes: { 'video.id': videoId }
  })
  
  try {
    await span.setAttribute('video.size_bytes', fileSize)
    const result = await runTranscode(videoId)
    span.setAttribute('video.duration_secs', result.duration)
    span.setStatus({ code: SpanStatusCode.OK })
    return result
  } catch (err) {
    span.recordException(err as Error)
    span.setStatus({ code: SpanStatusCode.ERROR })
    throw err
  } finally {
    span.end()
  }
}
```

# STEP 4 — ERROR TRACKING (SENTRY)

```typescript
// Initialize Sentry at the very top of server.ts:
import * as Sentry from '@sentry/node'

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  release: process.env.APP_VERSION,
  tracesSampleRate: 0.1,  // 10% of transactions (cost control)

  // Don't report these (noise):
  ignoreErrors: [
    'UnauthorizedError',
    'NotFoundError',
    'ValidationError',
    'RateLimitError',
  ],

  beforeSend(event, hint) {
    // Scrub sensitive data before sending to Sentry:
    if (event.request?.headers?.authorization) {
      event.request.headers.authorization = '[REDACTED]'
    }
    return event
  }
})

// Express integration — catches unhandled errors:
app.use(Sentry.Handlers.requestHandler())
app.use(Sentry.Handlers.tracingHandler())
// ... your routes ...
app.use(Sentry.Handlers.errorHandler())  // MUST be before your custom error handler

// MANUAL ERROR CAPTURE with context:
try {
  await transcodeVideo(videoId)
} catch (err) {
  Sentry.withScope(scope => {
    scope.setUser({ id: userId })
    scope.setTag('feature', 'video_transcoding')
    scope.setContext('video', { videoId, fileSize })
    Sentry.captureException(err)
  })
  throw err
}

// FRONTEND SENTRY:
import * as Sentry from '@sentry/nextjs'
Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  // Capture replay on error — see what user did before the error:
  replaysOnErrorSampleRate: 1.0,
})
```

# STEP 5 — ALERTING RULES

```yaml
# Prometheus alerting rules (or equivalent in Datadog/CloudWatch)
# RULE: alert on symptoms (what users experience), not internal metrics

groups:
  - name: api.alerts
    rules:
      # ─── CRITICAL: service is down ─────────────────────────────────────────
      - alert: APIDown
        expr: up{job="api"} == 0
        for: 1m
        labels: { severity: critical }
        annotations:
          summary: "API is down"
          description: "API has been unreachable for 1 minute"
          runbook: "https://docs.yourapp.com/runbooks/api-down"

      # ─── CRITICAL: high error rate (users seeing errors) ───────────────────
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status_code=~"5.."}[5m]))
          /
          sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels: { severity: critical }
        annotations:
          summary: "Error rate above 5% for 5 minutes"
          description: "{{ $value | humanizePercentage }} of requests are failing"

      # ─── WARNING: slow API (users experiencing latency) ────────────────────
      - alert: SlowAPIResponse
        expr: |
          histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 10m
        labels: { severity: warning }
        annotations:
          summary: "p95 response time above 2 seconds"

      # ─── WARNING: queue backing up (workers falling behind) ────────────────
      - alert: TranscodeQueueBacklog
        expr: job_queue_depth{queue_name="transcode"} > 50
        for: 15m
        labels: { severity: warning }
        annotations:
          summary: "Transcode queue has {{ $value }} jobs waiting"
          description: "Workers may be overloaded — consider adding more worker capacity"

      # ─── WARNING: disk space (avoid running out) ───────────────────────────
      - alert: LowDiskSpace
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.15
        for: 10m
        labels: { severity: warning }
        annotations:
          summary: "Less than 15% disk space remaining"

  # DON'T ALERT ON (noise that wakes people up unnecessarily):
  # ❌ CPU > 70%  — this is normal, not a user-facing symptom
  # ❌ Memory > 80%  — normal for well-tuned processes
  # ❌ Individual pod restarts  — Kubernetes restarts pods, this is normal
  # ❌ Cache miss rate  — expected behavior, not a symptom
```

# STEP 6 — DASHBOARD DESIGN

```
DASHBOARDS TO BUILD (in this priority order):

1. SERVICE HEALTH DASHBOARD (first thing you look at):
   - Request rate (req/s) — is there traffic?
   - Error rate (%) — are users seeing errors?
   - p50/p95/p99 latency — how fast is the API?
   - Active instances — how many pods are running?

2. BUSINESS METRICS DASHBOARD:
   - User signups today vs yesterday vs last week
   - Videos uploaded today
   - Videos transcoded (success / failure rate)
   - Active users (DAU, concurrently watching)

3. INFRASTRUCTURE DASHBOARD:
   - DB CPU, connections, slow queries
   - Redis memory, cache hit rate, connected clients
   - ECS task CPU and memory utilization
   - S3 request rate and cost

4. JOB QUEUE DASHBOARD:
   - Queue depth per queue (transcode, email, notifications)
   - Job success / failure rate
   - Average job duration
   - Failed jobs requiring manual intervention

GOLDEN SIGNALS (Google SRE — what to measure first):
  Latency:    How long requests take
  Traffic:    How many requests per second
  Errors:     Rate of failing requests
  Saturation: How full is your system (CPU, memory, queue depth)
```

# STEP 7 — UPTIME MONITORING

```
EXTERNAL UPTIME CHECKS (different from internal metrics — tests from outside):
  Tools: Better Uptime, Pingdom, UptimeRobot, Checkly

  Checks to configure:
    / (frontend homepage):      HTTP 200, < 3s
    /api/v1/health (API):       HTTP 200, < 500ms
    /api/v1/videos?limit=1:     HTTP 200, returns valid JSON
    /api/v1/auth/login (POST):  HTTP 401 on bad creds (not 500)

  SYNTHETIC MONITORING (Checkly or Playwright Cloud):
    - Run E2E test for login flow every 5 minutes from multiple regions
    - Alert if signup or login fails
    - More reliable than HTTP checks for complex flows

STATUS PAGE (Statuspage.io or betteruptime):
  - Public page users can check during incidents
  - Auto-updated from your monitoring system
  - Reduces support ticket volume during incidents
```

# CHECKLIST — Before Moving to Error Resiliency

```
✅ Structured JSON logging (Pino) on every request with requestId, userId
✅ Sentry error tracking with ignored errors list and sensitive data scrubbing
✅ Prometheus metrics: request rate, error rate, duration histograms
✅ Business metrics tracked (signups, video uploads, transcodes)
✅ Distributed tracing set up (OpenTelemetry)
✅ Alerting rules for: service down, error rate > 5%, p95 latency > 2s, queue backlog
✅ No alerts on non-symptomatic metrics (CPU%, memory%)
✅ Dashboards built for: service health, business metrics, infrastructure
✅ External uptime monitoring configured for critical endpoints
✅ On-call runbook written for each CRITICAL alert
→ NEXT: 14-ErrorResiliency.md
```
