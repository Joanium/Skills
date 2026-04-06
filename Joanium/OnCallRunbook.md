---
name: On-Call Runbook Writing
trigger: runbook, on-call runbook, write a runbook, alert runbook, incident runbook, on-call documentation, playbook, alert response, who do i page, escalation runbook, ops runbook, operational documentation
description: Write clear, actionable on-call runbooks that help engineers diagnose and resolve incidents quickly — especially engineers unfamiliar with the system. Use when setting up alerts, documenting services, or after a post-mortem reveals missing operational guidance.
---

A runbook is a letter to the engineer who gets paged at 3am. That engineer may be you. More likely it's someone else. They're stressed, possibly groggy, and they don't have time to explore. Write for them: clear, step-by-step, actionable, with nothing assumed.

## The Core Rule: Runbooks Must Be Immediately Actionable

A runbook fails if an on-call engineer reads it and still doesn't know what to do. Every runbook should answer four questions in order:

```
1. What is broken? (detection)
2. How bad is it? (severity)
3. How do I fix it? (steps)
4. Who do I call if I can't? (escalation)
```

If your runbook sends them on a research expedition ("investigate the logs"), it has failed.

## Runbook Structure

### Template
```markdown
# [Alert Name] — Runbook

**Alert:** [Name of the alert exactly as it appears in PagerDuty/Opsgenie]
**Service:** [Which service/component is affected]
**Severity:** [P1 Critical / P2 High / P3 Medium / P4 Low]
**Team:** [Owning team]
**Last reviewed:** [YYYY-MM-DD — runbooks without a review date are suspect]

---

## What This Alert Means

[1-3 sentences. What is happening and why it's a problem. 
No acronyms. No assumed knowledge.]

Example: "The payment processing worker has fallen behind. Orders submitted 
by users are not being processed. Users will see their cart stuck in 
'Processing' state. Revenue is not being collected."

## Severity Assessment

Before doing anything else, determine severity:

| Condition | Severity |
|-----------|----------|
| Queue > 10,000 and growing | P1 — wake the tech lead |
| Queue > 1,000 and growing  | P2 — work it now |
| Queue > 100, stable        | P3 — fix before EOD |
| Queue spiky but recovering | P4 — monitor and close |

## Immediate Impact

- **Users affected:** [e.g., "All users submitting payments"]
- **Revenue impact:** [e.g., "$X/minute if payment queue is blocked"]
- **External communications needed?** [Yes — page comms team / No]

---

## Diagnosis Steps

### Step 1: Confirm the problem
[Link to the dashboard]
[Specific metric to look at]
[What "bad" looks like vs. "recovering"]

```bash
# Check queue depth
redis-cli -h $REDIS_HOST llen payment:jobs:waiting

# Check worker processes
kubectl get pods -n production -l app=payment-worker

# Check recent errors
kubectl logs -n production -l app=payment-worker --since=10m | grep ERROR
```

### Step 2: Identify the root cause

Work through these in order, stopping when you find the issue:

**Is it a worker crash?**
```bash
kubectl get pods -n production -l app=payment-worker
# Look for CrashLoopBackOff or Restarts > 0

kubectl describe pod <pod-name> -n production
# Scroll to Events section at the bottom
```

**Is it a downstream dependency?**
```bash
# Check Stripe status
curl https://status.stripe.com/api/v2/status.json | jq .status.description

# Check database connectivity from a worker
kubectl exec -it <payment-worker-pod> -- node -e "require('./db').ping()"
```

**Is it a code bug from a recent deploy?**
```bash
# Check recent deployments
kubectl rollout history deployment/payment-worker -n production

# Get the error from the dead-letter queue
redis-cli -h $REDIS_HOST lrange payment:jobs:failed 0 4
```

---

## Resolution Steps

### Fix A: Worker pod is crashed/unresponsive
```bash
# Restart the workers (safe to do)
kubectl rollout restart deployment/payment-worker -n production

# Watch them come back up
kubectl rollout status deployment/payment-worker -n production --watch

# Verify queue is draining
watch -n 5 "redis-cli -h $REDIS_HOST llen payment:jobs:waiting"
```

### Fix B: Downstream Stripe is down
```bash
# Do NOT retry — let the queue hold jobs (it retries automatically)
# Check Stripe status page: https://status.stripe.com

# If Stripe is down for > 15 minutes:
# 1. Page the engineering lead (see escalation below)
# 2. Post in #incidents: "Stripe is down, payment processing paused, 
#    jobs queued and will process when Stripe recovers"
# 3. No code changes needed — jobs retry automatically

# When Stripe recovers, monitor queue drain:
watch -n 5 "redis-cli -h $REDIS_HOST llen payment:jobs:waiting"
```

### Fix C: Database connectivity issue
```bash
# Check RDS instance health
aws rds describe-db-instances --db-instance-identifier prod-payments \
  --query 'DBInstances[0].DBInstanceStatus'

# Check connection count (approaching max_connections?)
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# If pool is saturated, restart workers to release connections
kubectl rollout restart deployment/payment-worker -n production
```

### Fix D: Bug from recent deploy
```bash
# Roll back to previous version
kubectl rollout undo deployment/payment-worker -n production

# Verify rollback succeeded
kubectl rollout status deployment/payment-worker -n production

# Manually retry failed jobs (after rollback stabilizes)
# Run this in the payment-worker shell:
kubectl exec -it <pod> -- node scripts/retry-failed-jobs.js --limit 100

# Page the deploying engineer and team lead
```

---

## Validation

After applying a fix, confirm recovery:

```bash
# Queue should be draining (number going down)
watch -n 10 "redis-cli -h $REDIS_HOST llen payment:jobs:waiting"

# Error rate should be dropping
# Dashboard: [link]

# Check that jobs are actually completing
redis-cli -h $REDIS_HOST llen payment:jobs:completed
# Should be increasing

# Wait 5 minutes and confirm no new failures
redis-cli -h $REDIS_HOST llen payment:jobs:failed
```

**Close the incident when:** Queue is below 50 and draining, error rate back to baseline.

---

## Escalation

| When | Who | How | SLA |
|------|-----|-----|-----|
| You're stuck after 15 min | Engineering lead | PagerDuty secondary | Immediate |
| Stripe is down > 15 min | Engineering lead + Comms | Slack #incidents + PD | Immediate |
| Database is down | DBA on-call | PagerDuty DBA rotation | Immediate |
| Revenue impact > $10K | VP Engineering | Phone call | Immediate |

**Engineering lead on-call:** [Link to PagerDuty rotation schedule]
**Comms contact:** [Slack handle]

---

## Post-Incident

After resolving the incident:
1. Post resolution in #incidents: "[Resolved] Payment queue cleared. 
   Root cause: [brief]. [N] jobs re-queued and processing."
2. Create a post-mortem ticket if: P1 incident, or recurrence of same issue
3. Update this runbook if any steps were unclear or wrong

**Post-mortem template:** [Link]
**Incident log:** [Link to your incident tracker]
```

## Runbook Quality Checklist

```
Content:
☐ Is the alert name at the top exactly as it appears in the alerting system?
☐ Is the user/business impact described in plain language (no acronyms)?
☐ Are severity levels defined with specific measurable criteria?
☐ Are all commands copy-paste ready (with real variable names or noted env vars)?
☐ Are links to dashboards included (not "check the dashboard")?
☐ Is there a fix for each likely root cause?
☐ Is there a clear "how do I know it's fixed" section?
☐ Is the escalation path specific? (names, not roles)

Maintenance:
☐ Is there a "last reviewed" date?
☐ Does the runbook review happen after every related incident?
☐ Is the runbook linked from the alert itself (PagerDuty notes, Opsgenie)?
☐ Has a junior engineer read through it cold? (If they couldn't follow it, rewrite it)
☐ Are command examples tested in the actual environment (not just written from memory)?
```

## Runbook Anti-Patterns

```
ANTI-PATTERN: "Investigate the logs"
FIX: "Run this command and look for lines containing ERROR:"
  kubectl logs -l app=payment-worker --since=10m | grep ERROR

ANTI-PATTERN: "Contact the database team"
FIX: "Page the DBA on-call via PagerDuty rotation 'Database On-Call'. 
  If no response in 10 minutes, call [name] at [number]."

ANTI-PATTERN: "Check if the service is healthy"
FIX: "Run: curl -f https://api.internal/health/payments
  Expected: HTTP 200 with {"status":"ok"}
  If you get 500 or timeout: go to Fix B below"

ANTI-PATTERN: "Restart the service if necessary"
FIX: "If worker pod shows CrashLoopBackOff: [exact restart command]"

ANTI-PATTERN: A 5-year-old runbook with dead links and wrong command syntax
FIX: Add "Last reviewed" date. Review after every incident. 
  Delete the runbook if the service no longer exists.
```
