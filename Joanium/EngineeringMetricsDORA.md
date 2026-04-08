---
name: Engineering Metrics and DORA
trigger: engineering metrics, dora metrics, developer productivity, deployment frequency, lead time for changes, change failure rate, mean time to recover, MTTR, engineering KPIs, team performance metrics, developer experience metrics
description: Measure and improve engineering team performance using DORA metrics and broader developer experience indicators. Covers metric collection, baseline benchmarks, improvement strategies, and common anti-patterns.
---

# ROLE
You are a senior engineering leader or platform engineer. Metrics should drive improvement, not create fear. The goal is to understand where the system (process, tooling, architecture) is slowing the team down — not to rank individuals.

# CORE PRINCIPLES
```
MEASURE THE SYSTEM:    Metrics describe process and tooling health, not individual performance.
OUTCOMES OVER OUTPUT:  Deploys shipped matters less than value delivered safely.
BASELINES FIRST:       You can't improve what you haven't measured. Measure before optimizing.
LEADING INDICATORS:    Lag indicators (incidents) tell you what happened. Leading indicators predict it.
DISCUSS, DON'T PUNISH: Metrics surface conversations, not performance reviews.
```

# THE FOUR DORA METRICS
```
DORA (DevOps Research and Assessment) identified 4 metrics that predict high-performing teams.
High performers score well on ALL four — not just throughput or just stability.

┌─────────────────────────────────┬──────────────┬──────────────┬────────────────┐
│ Metric                          │ Elite        │ High         │ Medium/Low     │
├─────────────────────────────────┼──────────────┼──────────────┼────────────────┤
│ Deployment Frequency            │ On-demand    │ Daily–Weekly │ Weekly–Monthly │
│ Lead Time for Changes           │ < 1 hour     │ 1 day–1 week │ 1 week–1 month │
│ Change Failure Rate             │ 0–5%         │ 5–10%        │ 10–15%         │
│ Mean Time to Recover (MTTR)     │ < 1 hour     │ < 1 day      │ 1 day–1 week   │
└─────────────────────────────────┴──────────────┴──────────────┴────────────────┘
```

## Metric 1: Deployment Frequency
```
WHAT: How often does code reach production?
WHY: Frequent, small deploys = less risk per deploy + faster feedback.

Measurement:
  deploy_count_per_day = COUNT(deploys WHERE environment = 'production')
                                       / COUNT(DISTINCT DATE(deployed_at))

Common obstacles:
  - Manual deployment steps (automate the pipeline)
  - Long code review queues (limit WIP, improve PR size norms)
  - Lack of feature flags (can't deploy without being "done")
  - Flaky CI (failing builds stop the pipeline)
  - Monolith release coupling (teams block each other)

Improvement levers:
  → Trunk-based development + feature flags
  → Automate all deployment steps
  → Limit PR size (< 400 lines as guideline)
  → Fix the flakiest 20% of tests (gets 80% of CI reliability)
```

## Metric 2: Lead Time for Changes
```
WHAT: Time from "code committed" to "code in production".
WHY: Long lead time = slow feedback, big batches, high risk.

Measurement:
  lead_time = deployed_at - first_commit_in_pr_at
  Report: median and p90 (outliers matter)

Stages to decompose:
  Coding time:     first_commit → PR opened
  Review time:     PR opened → approved
  Merge time:      approved → merged
  Pipeline time:   merged → deployed to production
  Rollout time:    deployed → 100% of traffic (if gradual)

Common bottlenecks by stage:
  Long coding:    Large, complex tasks — break down better
  Long review:    Few reviewers, culture of slow reviews, large PRs
  Long pipeline:  Slow tests, large docker builds, sequential stages
  Long rollout:   No canary/feature flags, manual deploy approval

Improvement levers:
  → Parallelize CI test stages
  → Cache dependencies and build artifacts
  → Reduce PR size with better task decomposition
  → Set review SLA expectations (e.g., first response within 4h)
```

## Metric 3: Change Failure Rate
```
WHAT: % of deployments that cause a production incident, rollback, or hotfix.
WHY: High failure rate = fear of deploying = batching = bigger changes = more failure.

Measurement:
  change_failure_rate = failed_deploys / total_deploys
  A deploy is "failed" if it resulted in: P1/P2 incident, rollback, or hotfix within 24h

Common root causes:
  - Insufficient test coverage of critical paths
  - No staging environment or non-representative staging
  - DB migrations without backward compatibility
  - Config changes not validated before deploy
  - Insufficient load testing

Improvement levers:
  → Contract tests for inter-service dependencies
  → Integration tests on production-like data
  → Canary deployments with automated rollback on error rate spike
  → Database migration discipline (backward-compatible changes only)
  → Pre-deploy checklist automation
```

## Metric 4: Mean Time to Recover (MTTR)
```
WHAT: Average time from incident start to service restoration.
WHY: Fast recovery makes risk manageable. Slow recovery makes it existential.

Measurement:
  MTTR = AVG(incident_resolved_at - incident_detected_at)
  Decompose: Detection time + Response time + Diagnosis time + Fix time + Verification time

Time to detect is often the biggest gap — monitor before customers report.

Common bottlenecks:
  Detection:   No alerting; customers report before monitoring does
  Response:    On-call rotation unclear; escalation slow
  Diagnosis:   Poor observability; no distributed tracing; logs unstructured
  Fix:         Rollback slow or manual; no feature flags to disable bad features
  Verification: No automated validation post-fix

Improvement levers:
  → Set SLO-based alerts (burn rate) — detect before customers do
  → Documented, tested runbooks linked from every alert
  → One-command rollback procedure
  → Postmortems that fix root causes (not just symptoms)
  → Chaos engineering — practice recovery before the real incident
```

# SUPPLEMENTARY METRICS

## Developer Experience (DX) Metrics
```
CI Build Duration:
  Target: < 10 minutes for full pipeline
  Track: p50 and p90 build time per day
  Action: > 15 min consistently → investigate and optimize

Test Flakiness Rate:
  flaky_rate = flaky_test_failures / total_test_runs
  Target: < 1%
  Action: Quarantine and fix top 10 flakiest tests (usually 80% of the problem)

PR Review Turnaround:
  first_response_time: time to first reviewer comment
  Target: p50 < 4h, p90 < 24h
  Watch for: PRs open > 3 days without activity

Time Lost to Incidents (Engineering Tax):
  eng_tax = incident_eng_hours / total_eng_hours_per_week
  Target: < 10%
  High eng_tax → prioritize reliability over features
```

## Outcome Metrics (Beyond DORA)
```
Release Rollback Rate:
  Indicator of: deployment confidence, backward compatibility discipline

Feature Cycle Time:
  Time from "feature spec signed off" → "in production"
  Includes planning, design, implementation, review, deploy

Error Budget Consumption:
  % of monthly SLO error budget consumed
  Connects technical reliability to business commitments

Incident-Free Deploy Streak:
  Streak of consecutive deployments without incident
  Motivating leading indicator (vs. lagging MTTR)
```

# DATA COLLECTION
```python
# Collecting DORA metrics from GitHub + PagerDuty
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class DeploymentMetrics:
    deployment_frequency: float   # deploys per day (30d avg)
    lead_time_p50_hours: float    # median lead time
    lead_time_p90_hours: float
    change_failure_rate: float    # 0–1 fraction
    mttr_hours: float             # mean time to recover

def compute_dora_metrics(
    deployments: list[dict],
    incidents: list[dict],
    prs: list[dict],
    window_days: int = 30
) -> DeploymentMetrics:
    window_start = datetime.now() - timedelta(days=window_days)

    # Filter to window
    recent_deploys = [d for d in deployments if d['deployed_at'] > window_start]
    recent_incidents = [i for i in incidents if i['started_at'] > window_start]

    # 1. Deployment frequency
    deploy_freq = len(recent_deploys) / window_days

    # 2. Lead time (commit to deploy)
    lead_times = [
        (d['deployed_at'] - d['first_commit_at']).total_seconds() / 3600
        for d in recent_deploys
    ]
    lead_times.sort()
    p50 = lead_times[len(lead_times) // 2] if lead_times else 0
    p90 = lead_times[int(len(lead_times) * 0.9)] if lead_times else 0

    # 3. Change failure rate
    failed = sum(1 for d in recent_deploys if d.get('caused_incident'))
    cfr = failed / max(len(recent_deploys), 1)

    # 4. MTTR
    recovery_times = [
        (i['resolved_at'] - i['started_at']).total_seconds() / 3600
        for i in recent_incidents if i.get('resolved_at')
    ]
    mttr = sum(recovery_times) / max(len(recovery_times), 1)

    return DeploymentMetrics(deploy_freq, p50, p90, cfr, mttr)
```

# ANTI-PATTERNS
```
MEASURING INDIVIDUALS:
  ✗ "Alice had 3 incidents this quarter"
  ✓ "Our team's MTTR was 4 hours — what made those incidents take so long?"

GOODHART'S LAW — When a metric becomes a target, it ceases to be a good metric:
  ✗ "Team must ship 10 PRs per week" → trivial PRs, split work artificially
  ✗ "Zero incidents" → teams stop deploying or under-report issues
  ✓ Use metrics to diagnose, not mandate

VANITY METRICS:
  ✗ Lines of code (effort ≠ value)
  ✗ Number of features shipped (without quality or adoption signal)
  ✗ "Velocity" in points (relative, gameable, not comparable across teams)

IGNORING CONTEXT:
  Metrics without context mislead. High CFR during a major migration ≠ same as steady-state.
  Annotate metric timelines with: launches, migrations, team changes, on-call staffing.
```

# IMPROVEMENT ROADMAP TEMPLATE
```
Current State (baseline — 30-day average):
  Deployment Frequency:  2 deploys/week   (target: daily)
  Lead Time P50:         3 days           (target: < 1 day)
  Change Failure Rate:   12%              (target: < 5%)
  MTTR:                  6 hours          (target: < 2 hours)

Root Cause Analysis:
  1. Long lead time → Long CI (18 min), few reviewers
  2. High CFR → No staging parity, missing integration tests
  3. High MTTR → Alerts fire after customers report, no runbooks

Initiatives (prioritized by expected DORA impact):
  Q1: Fix top 10 flaky tests, parallelize CI → target 8 min builds → lead time ↓
  Q1: Add 20 critical integration tests for checkout flow → CFR ↓
  Q2: SLO-based alerting (burn rate) → detection time ↓ → MTTR ↓
  Q2: Runbook for top 5 incident types → MTTR ↓
  Q2: Trunk-based development + feature flags → deploy freq ↑

Review cadence: Monthly metrics review, quarterly goal adjustment
```
