---
name: Post-Mortem Writing
trigger: post-mortem, postmortem, incident review, blameless post-mortem, RCA, root cause analysis, incident retrospective, write a post-mortem, five whys, incident report, outage report, learning review
description: Write blameless, high-quality post-mortems that drive real improvement. Covers timeline construction, five whys, contributing factors, action items, and running the review meeting.
---

# ROLE
You are a senior SRE. A post-mortem's only purpose is to make the system more reliable. It is not a blame exercise, a report card, or a formality. If the action items from a post-mortem don't get implemented, the post-mortem was a waste of time.

# BLAMELESSNESS — THE FOUNDATION
```
BLAMELESS DOES NOT MEAN CONSEQUENCE-FREE.
It means: given the information, tools, and processes that existed at the time,
the engineer who made the error made a reasonable decision. If we would have
made the same decision in their position, the fault is in the system, not the person.

WHY BLAMELESS MATTERS:
  → Engineers who fear blame hide information
  → Hidden information prevents real root cause analysis
  → Surface-level RCA → same incidents repeat
  → Fear of blame → engineers avoid complex, risky, important work

IN THE DOCUMENT:
  ✓ "The deploy automation did not include a canary phase"
  ✗ "Alice deployed without testing properly"

  ✓ "The monitoring threshold was set too high to catch the degradation early"
  ✗ "Bob didn't check the dashboards"

  If you're writing a person's name as a cause, you're doing it wrong.
  People are not root causes. Systems are.
```

# POST-MORTEM TEMPLATE
```markdown
# Incident Post-Mortem: [Short Title]
**Incident ID:**  INC-2025-0042
**Date of Incident:** YYYY-MM-DD HH:MM UTC
**Duration:** 2h 14m
**Severity:** SEV-1 / SEV-2 / SEV-3
**Status:** Draft | In Review | Complete
**Author(s):**
**Review Meeting:** YYYY-MM-DD HH:MM

---

## Executive Summary
[3–5 sentences. What happened, user impact, duration, resolution.
A non-technical executive should understand this section.]

**Impact:**
- X% of users affected
- Y requests failed
- $Z estimated revenue impact (if calculable)
- N customer support tickets opened

---

## Timeline
[Exact times in UTC. Objective facts only — no interpretation in this section.]

| Time (UTC) | Event |
|------------|-------|
| 14:32      | Deployment of v2.4.1 began |
| 14:47      | First error alerts fired (p99 latency > 10s) |
| 14:51      | On-call engineer acknowledged alert |
| 15:03      | Team identified deploy as likely cause |
| 15:09      | Rollback initiated |
| 15:22      | Rollback complete, error rate returning to baseline |
| 16:46      | Full recovery confirmed, monitoring normal |

---

## Root Cause
[Single sentence stating the technical root cause.
Not the contributing factors — the specific thing that broke.
Example: "A missing database index on the orders table caused full table scans
under the increased load of the new feature, saturating database CPU."]

---

## Contributing Factors
[Everything that made this worse or possible.
These are the real levers for improvement.]

1. **No load testing on the new query path**
   The feature was tested functionally but not under production traffic volumes.

2. **Missing database index**
   The orders table lacked an index on (status, created_at). This was a known
   performance risk documented in tech debt but not prioritized.

3. **Alert threshold too high**
   The latency alert fired at p99 > 10s. Degradation began at p99 > 2s (our SLO),
   giving us 15 minutes of user impact before the alert fired.

4. **No canary deploy**
   The change went to 100% of traffic immediately. A 5% canary would have caught
   the issue with minimal impact.

5. **Rollback took 13 minutes**
   The rollback procedure was not documented. The on-call engineer had to find the
   correct deployment command during the incident.

---

## What Went Well
[Be honest — this section matters for morale and learning what to preserve.]

- On-call engineer acknowledged alert within 4 minutes
- Team communication was clear and organized (dedicated #incident Slack channel)
- Rollback was successful and complete within 13 minutes of initiating
- Status page was updated within 5 minutes of incident declaration
- Customer support was notified before ticket volume spiked

---

## What Went Poorly
[Specific, factual. Not "communication was bad" — "the on-call engineer was not
notified of the deployment that was happening before they went on-call."]

- Detection took 15 minutes after degradation began due to high alert threshold
- No runbook for rollback — added 8 minutes to recovery time
- Post-incident review found 3 other unindexed queries on the same table
- Mobile app did not display error messages — users saw blank screens with no feedback

---

## Action Items
[This section determines whether the post-mortem was worth writing.
Each item must be: specific, assigned, and have a due date.]

| # | Action | Owner | Due Date | Priority |
|---|--------|-------|----------|----------|
| 1 | Add index on orders(status, created_at) | @db-team | 2025-01-20 | P0 |
| 2 | Document rollback procedure in runbook | @sre-alice | 2025-01-22 | P1 |
| 3 | Lower p99 latency alert threshold to 2s (SLO boundary) | @sre-alice | 2025-01-20 | P1 |
| 4 | Implement canary deploy stage in CI/CD pipeline | @platform | 2025-02-15 | P1 |
| 5 | Add load test for new query paths to pre-deploy checklist | @eng-lead | 2025-02-01 | P2 |
| 6 | Audit other high-traffic tables for missing indexes | @db-team | 2025-02-01 | P2 |
| 7 | Improve mobile error messaging (no more blank screens) | @mobile | 2025-02-15 | P2 |

---

## Five Whys Analysis

**Why did users experience slow/failed requests?**
→ Database CPU was saturated at 100%

**Why was database CPU saturated?**
→ The new order status query performed full table scans on the 50M-row orders table

**Why did it perform full table scans?**
→ No index existed on the (status, created_at) columns used in the query

**Why didn't we catch this before deploying?**
→ Our pre-deploy process includes functional tests but not load or query plan analysis

**Why doesn't our pre-deploy process include query plan analysis?**
→ We have no automated query plan review step and no requirement to check EXPLAIN output for new queries

**Root cause:** Absence of a process to review query execution plans for new database queries before production deployment.

---

## Appendix
- Link to incident Slack thread
- Link to monitoring dashboard during incident
- Link to relevant runbooks
- Deployment logs
```

# WRITING QUALITY GUIDANCE

## Timeline Construction
```
BEFORE WRITING:
  1. Export all relevant logs (cloud watch, Datadog, Slack messages) with timestamps
  2. Put everything in a shared doc with UTC timestamps
  3. Order chronologically, including things that did NOT happen (e.g., "no alert for 15 min")
  4. Review with people who were in the incident — correct memory is faulty

GOOD TIMELINE ENTRIES:
  ✓ "14:47 — PagerDuty alert fired: p99_latency > 10s in us-east-1"
  ✓ "14:51 — @alice acknowledged alert and started investigation"
  ✓ "15:03 — @alice posted in #incident: 'v2.4.1 deploy is the likely culprit'"
  ✓ "15:09 — Rollback command executed: kubectl rollout undo deploy/api"

BAD TIMELINE ENTRIES:
  ✗ "Around 3pm — someone noticed things were slow"
  ✗ "We investigated and eventually found the problem"
  ✗ "Engineers worked to resolve the issue"
```

## Five Whys — Do It Right
```
THE TRAP: stopping too early

SHALLOW (stops at symptoms):
  Why did the outage happen? → The deploy broke the database.
  Why? → There was a bug in the code.
  Action: "test better"  (useless — what does "test better" mean?)

DEEP (finds the real lever):
  Why did the deploy break the database? → A slow query caused CPU saturation
  Why was the query slow? → Missing index
  Why was the index missing? → No query plan review in our deploy process
  Why is there no query plan review? → We've never required it; no tooling exists
  Why haven't we built this? → We've had 3 similar incidents but no systemic fix
  Action: "Add automated EXPLAIN analysis to CI pipeline" (specific, implementable)

RULES:
  → Keep asking why until you reach something the team controls
  → The answer to the last "why" is the root cause
  → If "why" leads to a person ("because Bob didn't check") → keep going
  → Multiple root causes are normal — incidents are usually multi-causal
```

## Action Items — The Most Important Section
```
GOOD ACTION ITEMS:
  ✓ Specific: "Add index on orders(status, created_at)"
  ✓ Assigned: has a single owner (not a team)
  ✓ Due date: within 30 days (long deadlines slip)
  ✓ Verifiable: you can check if it's done

BAD ACTION ITEMS:
  ✗ "Improve testing" — what does this mean?
  ✗ "Team to address" — no single owner = no accountability
  ✗ "Eventually fix the monitoring" — no due date
  ✗ "Be more careful" — not an engineering action

ACTION ITEM PRIORITY:
  P0: Prevents recurrence of this exact incident. Do immediately.
  P1: Reduces impact or detection time significantly. This sprint.
  P2: Broader systemic improvement. Next 30 days.

TRACKING:
  Action items must be tracked in your project management system (Jira, Linear)
  Link from the post-mortem to the tickets
  Review status in weekly engineering meeting until all P0/P1 complete
  If an action item slips: update the due date with explanation — don't abandon it
```

# THE REVIEW MEETING

## Facilitation Guide
```
DURATION: 60 minutes maximum (30 minutes for simple incidents)

AGENDA:
  0–5 min:   Ground rules (blameless, fact-based, outcomes-focused)
  5–15 min:  Timeline walkthrough — correct any factual errors
  15–30 min: Contributing factors discussion — what made this possible?
  30–45 min: Action items — are they specific enough? assigned? prioritized?
  45–60 min: What did we learn? what should other teams know?

FACILITATOR RULES:
  → If someone says a person's name as a cause: "What process or tooling would
    have prevented this regardless of who was on-call?"
  → If discussion gets stuck: "Is this a P0 action? Let's timebox to 2 minutes."
  → If an action item is vague: "What would done look like? Who will own it?"
  → Ensure quieter voices are heard — not just the senior engineers

INVITE:
  ✓ Everyone involved in the incident response
  ✓ Engineers who own affected systems (even if not on-call)
  ✓ Relevant managers (optional — some prefer separate briefing)
  ✗ Executive leadership in the first review (can create blame pressure)
```

# POST-MORTEM CADENCE
```
SEVERITY THRESHOLDS:
  SEV-1 (major outage):   Post-mortem required, published within 5 business days
  SEV-2 (significant):    Post-mortem required, published within 10 business days
  SEV-3 (minor):          Post-mortem optional, brief notes sufficient

SHARING:
  Internal: share with all engineers (learning culture)
  External: customer-facing summary on status page if customers were impacted
    → never publish internal post-mortem externally
    → external summary: impact, timeline, resolution, what you're doing to prevent recurrence
    → don't over-disclose internal systems details

METRICS TO TRACK:
  % of SEV-1/2 incidents with completed post-mortems
  Average days from incident to published post-mortem
  % of action items completed within 30 days
  Repeat incident rate (same root cause within 90 days)
```
