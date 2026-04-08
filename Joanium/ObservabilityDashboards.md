---
name: Observability Dashboards
trigger: observability dashboard, grafana dashboard, metrics dashboard, datadog dashboard, build a dashboard, monitoring dashboard, service dashboard, golden signals dashboard, SLO dashboard, operational dashboard
description: Design and build effective observability dashboards for production services. Covers the Four Golden Signals, SLO tracking, service topology, dashboard hierarchy, and Grafana/Datadog implementation patterns.
---

# ROLE
You are a senior SRE or platform engineer. A dashboard that doesn't tell you the answer during an incident is decoration. Every panel must answer a specific question an on-call engineer would ask. Design for 3am, not demos.

# CORE PRINCIPLES
```
ANSWER A QUESTION:      Every panel title should be a question. The visualization is the answer.
THREE-TIER HIERARCHY:   Home → Service → Component. Don't mix levels of abstraction.
ORIENT, DIAGNOSE, FIX:  Dashboards help you know something is wrong, understand why, then fix it.
RED/AMBER/GREEN:        Status should be obvious at a glance — no interpreting numbers.
LINK FORWARD:           Every dashboard links to the next level of detail.
```

# DASHBOARD HIERARCHY
```
TIER 1 — EXECUTIVE / HOME DASHBOARD
  Audience:   Anyone — at a glance, is everything okay?
  Content:    Status of all services (RAG), overall SLO compliance, active incidents
  Update:     1-minute refresh
  Panels:     ~8–12 panels maximum

TIER 2 — SERVICE DASHBOARD (one per service)
  Audience:   On-call engineers
  Content:    Four Golden Signals, dependencies health, recent deploys, SLO error budget
  Update:     30-second refresh
  Panels:     ~15–20 panels

TIER 3 — COMPONENT / DEEP-DIVE DASHBOARD
  Audience:   Engineers debugging a specific issue
  Content:    DB query latency breakdown, queue depth per topic, cache hit rates by key type
  Update:     10-second refresh during incident, 1-minute normally
  Panels:     Unlimited — this is investigation space
```

# FOUR GOLDEN SIGNALS — IMPLEMENTATION
```
LATENCY (response time)
  Panel: Latency Distribution (p50 / p95 / p99)
  Why: Average lies. p99 is what your worst-experience users feel.

  # Prometheus / Grafana
  histogram_quantile(0.99,
    sum(rate(http_request_duration_seconds_bucket{service="orders"}[5m])) by (le, endpoint)
  )

  Thresholds: green < 200ms | amber < 500ms | red > 500ms (adjust to your SLO)

TRAFFIC (request volume)
  Panel: Requests per Second (total, by endpoint)
  Why: Traffic drops signal failures. Traffic spikes signal load or abuse.

  sum(rate(http_requests_total{service="orders"}[1m])) by (endpoint, method)

  Annotation: overlay deployment markers to correlate traffic changes with deploys

ERRORS (error rate)
  Panel: Error Rate % (5xx / 4xx / total)
  Why: Absolute error count is meaningless — rate vs. total traffic is what matters.

  # 5xx error rate
  sum(rate(http_requests_total{service="orders", status=~"5.."}[5m]))
  /
  sum(rate(http_requests_total{service="orders"}[5m]))

  Thresholds: green < 0.1% | amber < 1% | red > 1%
  Note: 4xx separately — high 404 may indicate client bugs, not service bugs

SATURATION (resource utilization)
  Panel: CPU, Memory, Connection Pool, Queue Depth
  Why: Saturation predicts failure before it happens.

  # CPU
  rate(container_cpu_usage_seconds_total{pod=~"orders-.*"}[5m]) / container_spec_cpu_quota

  # DB connection pool utilization
  db_pool_connections_in_use / db_pool_size_max

  Thresholds: green < 60% | amber < 80% | red > 80%
```

# SLO DASHBOARD PANELS
```
ERROR BUDGET BURN RATE (most important SLO panel)
  Shows: How fast you're burning the monthly error budget right now.
  Formula: burn rate = error rate / (1 - SLO target)
  Example: 99.9% SLO → 0.1% budget. If error rate = 1%, burn rate = 10× (gone in 3 days)

  # Grafana multi-window burn rate alert (SRE workbook recommended)
  (
    rate(http_requests_total{status=~"5.."}[1h])
    / rate(http_requests_total[1h])
  ) / 0.001   # 0.001 = 1 - 0.999 SLO target

  Alert: burn rate > 14.4× (burns monthly budget in 2 hours) → page immediately
         burn rate > 6× (burns in 5 hours) → ticket + Slack

ERROR BUDGET REMAINING (30-day rolling)
  Shows: How much budget is left this month.
  Panel type: Gauge with thresholds.

  Thresholds: green > 50% remaining | amber 10–50% | red < 10%

SLO COMPLIANCE TREND
  Shows: 7-day and 30-day SLO compliance as a time-series.
  Useful for: Spotting gradual degradation before budget runs out.
```

# PANEL DESIGN PATTERNS
```
PANEL TITLES — Use questions, not labels:
  ✓ "Is error rate within SLO?" (answer visible in threshold colors)
  ✓ "How fast is the DB responding?"
  ✗ "Error Rate"
  ✗ "Latency"

THRESHOLD COLORING — Always set thresholds, never leave default:
  Green = healthy, Amber = degraded but within SLO, Red = SLO at risk or breached

TIME RANGES — Set useful defaults:
  Service dashboard: last 3 hours default (captures incidents + recent history)
  SLO dashboard: last 30 days (error budget view)
  Deep-dive: last 1 hour (incident investigation)

ANNOTATIONS — Overlay events that explain changes:
  - Deployment markers (pull from CI/CD)
  - Incident start/end markers
  - Config change markers
  - Traffic anomaly markers

LINKS — Every dashboard links to the next level:
  Service panel → deep-dive component dashboard
  Error panel → log search pre-filtered for errors
  Latency panel → trace explorer with slow-trace filter
  Deployment marker → diff in CI/CD system
```

# GRAFANA IMPLEMENTATION
```json
// Panel JSON skeleton — Latency by Endpoint (Heatmap)
{
  "title": "Is request latency within SLO?",
  "type": "timeseries",
  "gridPos": { "h": 8, "w": 12 },
  "targets": [
    {
      "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{service=\"$service\"}[$__rate_interval])) by (le))",
      "legendFormat": "p99"
    },
    {
      "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{service=\"$service\"}[$__rate_interval])) by (le))",
      "legendFormat": "p95"
    },
    {
      "expr": "histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket{service=\"$service\"}[$__rate_interval])) by (le))",
      "legendFormat": "p50"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "s",
      "thresholds": {
        "mode": "absolute",
        "steps": [
          { "value": null, "color": "green" },
          { "value": 0.2, "color": "yellow" },
          { "value": 0.5, "color": "red" }
        ]
      }
    }
  }
}
```

# DATADOG DASHBOARD PATTERNS
```python
# Datadog dashboard as code (Terraform / datadog-api-client)

# Error rate widget
{
    "definition": {
        "type": "timeseries",
        "title": "Is error rate within SLO?",
        "requests": [
            {
                "q": "sum:http.requests{status:5xx,service:orders}.as_rate() / sum:http.requests{service:orders}.as_rate()",
                "display_type": "line",
                "style": { "line_type": "solid", "line_width": "thick" }
            }
        ],
        "markers": [
            { "value": "y = 0.001", "display_type": "error dashed", "label": "SLO limit (0.1%)" }
        ],
        "yaxis": { "min": "0", "max": "0.05" }
    }
}
```

# SERVICE DASHBOARD TEMPLATE LAYOUT
```
Row 1 — Status bar
  [Overall Health RAG] [SLO Error Budget Gauge] [Active Alerts Count] [Last Deploy time]

Row 2 — Traffic & Errors
  [Requests/sec (time series)]  [Error Rate % (time series)]

Row 3 — Latency
  [p50/p95/p99 (time series)]  [Latency heatmap by endpoint]

Row 4 — Saturation
  [CPU %]  [Memory %]  [DB pool %]  [Queue depth]

Row 5 — Dependencies
  [DB latency]  [Cache hit rate]  [External API error rate]

Row 6 — Context
  [Deploy annotations overlaid on error rate] [Recent alerts table]
```

# ANTI-PATTERNS TO AVOID
```
VANITY METRICS:
  ✗ Total requests all-time (means nothing operationally)
  ✗ Uptime percentage without SLO context
  ✗ "Requests per minute" without error rate alongside it

AVERAGES WITHOUT PERCENTILES:
  ✗ Average latency alone (hides tail latency from worst-affected users)
  ✓ Always p50 + p95 + p99 together

TOO MANY PANELS:
  ✗ 50-panel service dashboard that requires scrolling during an incident
  ✓ 15–20 panels max on a service dashboard; link to deep-dive for the rest

STALE DASHBOARDS:
  ✗ Dashboard last updated 18 months ago — half the queries broken
  ✓ Dashboards as code (Grafonnet, Terraform) — reviewed on service changes

MISSING CONTEXT:
  ✗ Error spike with no way to know if a deploy just happened
  ✓ Deployment annotations overlaid on every time-series panel
```

# DASHBOARD CHECKLIST
```
[ ] Each panel answers a specific question (stated in the title)
  [ ] Thresholds set with green/amber/red on every numeric panel
  [ ] SLO target line marked on error rate and latency panels
  [ ] Time range defaults match the dashboard's purpose
  [ ] Deployment annotations enabled on key panels
  [ ] Each panel links to the next level of detail (logs, traces, deep-dive)
  [ ] Dashboard variables (service, environment, region) for reuse
  [ ] Dashboard tested during an incident simulation
  [ ] Dashboard linked from on-call runbook
  [ ] Dashboard reviewed and updated after every major incident
```
