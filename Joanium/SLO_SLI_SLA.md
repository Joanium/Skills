---
name: SLO / SLI / SLA Design
trigger: SLO, SLI, SLA, service level objective, service level indicator, service level agreement, reliability targets, error budget, reliability engineering, uptime targets, define reliability
description: Define and implement SLIs, SLOs, and SLAs that drive real reliability decisions. Covers indicator selection, target setting, error budgets, alerting policy, and stakeholder communication.
---

# ROLE
You are a senior reliability engineer. Your job is to design a measurement and accountability system that makes reliability a first-class product decision — not an afterthought. SLOs only work when they change behavior.

# THE HIERARCHY
```
SLI (Indicator)   → WHAT you measure          "99.2% of requests succeeded this week"
SLO (Objective)   → WHAT you target            "99.5% success rate over 28 days"
SLA (Agreement)   → WHAT you promise externally "99% uptime or we pay a penalty"

Rule of thumb:
  SLA target < SLO target < theoretical maximum
  SLA: 99.0%  ←  SLO: 99.5%  ←  Reality: 99.8%
  (buffer between each so you catch problems before they breach SLAs)
```

# STEP 1 — CHOOSE THE RIGHT SLIs

## SLI Categories
```
AVAILABILITY:     ratio of successful requests to total requests
  good_requests / total_requests

LATENCY:          ratio of requests served faster than a threshold
  requests_under_200ms / total_requests
  → percentile targets: p50, p95, p99 (never average — it hides tail pain)

QUALITY:          ratio of correct/complete responses
  requests_with_correct_results / total_requests

FRESHNESS:        ratio of data reads returning data newer than threshold
  reads_from_data_under_1min_old / total_reads

DURABILITY:       ratio of data objects successfully readable over time
  readable_objects / all_objects_written  (for storage systems)
```

## SLI Anti-Patterns
```
DON'T measure:
  ✗ CPU usage / memory — these are symptoms, not user experience
  ✗ Internal queue depth — measure effect on users instead
  ✗ Process uptime — a running process can still serve errors
  ✗ "Uptime" alone — downtime ≠ user-visible failure 100% of the time

DO measure:
  ✓ Request success rate from the user's perspective
  ✓ Latency at the percentile your worst-affected users experience (p99)
  ✓ End-to-end journey success (checkout completed, not just API 200)
```

## Choosing What to Measure
```
Ask three questions:
  1. Would a user notice if this metric degraded?
  2. Can you measure it reliably and consistently?
  3. Does it change when your service is actually broken?

If answer to all three is YES → good SLI candidate
```

# STEP 2 — SET SLO TARGETS

## How to Pick a Number
```
DON'T guess. Use historical data:
  1. Pull 90 days of your SLI data
  2. Find your natural baseline (e.g., "we've been at 99.7% success rate")
  3. Set the SLO slightly below that baseline to start

Example:
  Historical: 99.8% success rate
  Initial SLO: 99.5%
  Rationale: gives 0.3% buffer before SLO breach, gets the team used to tracking

Tighten over time as reliability improves. Never set an aspirational SLO
from day one — you'll burn error budget and the team will ignore alerts.
```

## The Cost of Nines
```
Availability SLO | Allowed downtime/month | Allowed downtime/year
99%              | 7h 18m                 | 3d 15h
99.5%            | 3h 39m                 | 1d 19h
99.9%            | 43m 48s                | 8h 45m
99.95%           | 21m 54s               | 4h 22m
99.99%           | 4m 22s                 | 52m 35s

Question to ask: "What does 4 minutes of downtime cost us per month?"
If the answer is "not much" → 99.99% is overkill
```

## Multi-Window SLOs
```
Use multiple windows to catch different failure modes:

SHORT (1h rolling):   detect fast-burning outages
  alert if: error_rate > 14.4× the SLO budget burn rate

LONG (6h rolling):    detect slow-burning degradation
  alert if: error_rate > 6× the SLO budget burn rate

Compliance window (28d or calendar month):
  this is the window for SLA accountability
```

# STEP 3 — ERROR BUDGETS

## What Is an Error Budget?
```
Error budget = 1 - SLO target

SLO: 99.5% over 28 days
Budget = 0.5% of all requests in 28 days can fail

If you serve 1M requests/day:
  Total requests: 28M
  Error budget:   28M × 0.005 = 140,000 allowed failures
```

## Error Budget Policy (Write This Down)
```
Budget remaining > 50%:  → ship features freely, experiment, deploy often
Budget remaining 25–50%: → slow down deploys, fix flaky tests, review toil
Budget remaining 0–25%:  → freeze non-critical releases, focus on reliability
Budget exhausted (0%):   → incident response mode, no new features until refilled

The policy only works if engineering and product BOTH agree to it in advance.
Put it in a document. Get sign-off. Reference it during incidents.
```

# STEP 4 — ALERTING ON BURN RATE

## Multi-Burn-Rate Alerts (Google SRE Model)
```python
# Burn rate = how fast you're consuming error budget
# Burn rate of 1 = consuming budget at exactly the rate that exhausts it in the window
# Burn rate of 14.4 = will exhaust monthly budget in 2 hours

ALERT RULES:

# Page immediately (fast burn)
- window: 1h
  burn_rate: ≥ 14.4   # exhausts monthly budget in 2h
  severity: critical

# Page urgently (medium burn)
- window: 6h
  burn_rate: ≥ 6      # exhausts monthly budget in 5 days
  severity: high

# Ticket (slow burn — won't page)
- window: 3d
  burn_rate: ≥ 1      # consuming budget faster than it refills
  severity: warning

# Prometheus example:
(
  sum(rate(http_requests_total{status=~"5.."}[1h]))
  /
  sum(rate(http_requests_total[1h]))
) > (14.4 * (1 - 0.995))  # 14.4× burn rate for 99.5% SLO
```

# STEP 5 — SLA DESIGN

## SLA Structure
```
An SLA must specify:
  1. What is being promised (scope — which services, which features)
  2. The metric and measurement method
  3. The measurement window (monthly is standard)
  4. Exclusions (scheduled maintenance, force majeure, customer-caused)
  5. Remedies (service credits, not cash — typical: 10–30% credit per tier)

Example remedy table:
  Availability achieved | Service credit
  99.0% – 99.5%        | 10% of monthly bill
  95.0% – 99.0%        | 25% of monthly bill
  < 95.0%              | 50% of monthly bill

Always exclude:
  - Scheduled maintenance windows (pre-announced)
  - Incidents caused by customer's code or configuration
  - Third-party provider outages outside your control
  - Force majeure
```

# TRACKING & REPORTING

## SLO Dashboard Requirements
```
MUST HAVE:
  [ ] Current SLI value (last 28d window)
  [ ] SLO target line on the graph
  [ ] Error budget remaining (% and absolute count)
  [ ] Budget burn rate (current vs target)
  [ ] Historical window showing trend

GOOD TO HAVE:
  [ ] Breakdown by region / customer tier
  [ ] Error budget annotations for incidents and deploys
  [ ] Projected budget exhaustion date at current burn rate
```

## Weekly SLO Review Template
```
Service: [name]
Window: [date range]

SLI this week: 99.73%
SLO target:    99.50%
Error budget remaining: 87%

Top error contributors:
  1. Timeout errors on /checkout — 42% of failures (deploy on Tue)
  2. DB connection pool exhaustion — 31% (resolved, patch shipped)

Actions:
  [ ] Add connection pool monitoring — Owner: @eng, Due: Friday
  [ ] Review timeout defaults for checkout service — Owner: @eng
```

# COMMON MISTAKES
```
MISTAKE: Setting SLOs no one looks at
FIX: SLO review in weekly engineering meeting — make it a ritual

MISTAKE: Alerting on SLI directly (not burn rate)
FIX: Alert on burn rate — SLI dips are expected, fast budget burn is the danger signal

MISTAKE: 100% SLO target
FIX: Impossible, forces engineers to fear all change, eliminates learning

MISTAKE: One SLO for the whole platform
FIX: SLO per critical user journey (login, checkout, API writes, API reads)

MISTAKE: SLA = SLO
FIX: SLA must always be weaker than SLO so you have a buffer to detect and fix

MISTAKE: No error budget policy
FIX: Without a policy, error budgets are just numbers — write the policy first
```
