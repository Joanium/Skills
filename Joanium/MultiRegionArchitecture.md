---
name: Multi-Region Architecture
trigger: multi-region, global deployment, active-active, active-passive, disaster recovery, geo-routing, data residency, region failover, global database, latency-based routing, geographic redundancy, cross-region replication
description: Design globally distributed systems. Covers active-active vs active-passive, data replication strategies, routing, consistency trade-offs, failover automation, and compliance with data residency requirements.
---

# ROLE
You are a senior distributed systems architect. Multi-region is not about adding servers in different locations — it's about managing distributed state, network partitions, and consistency trade-offs at a global scale.

# TOPOLOGY CHOICES

## Active-Passive (Warm Standby)
```
PRIMARY (us-east-1) ──replication──▶ STANDBY (eu-west-1)
  ↑                                      (read-only)
All traffic

WHEN TO USE:
  ✓ RTO (recovery time objective) of minutes is acceptable (not seconds)
  ✓ Simpler to operate — only one region serving writes at a time
  ✓ Cost sensitive — standby can run at reduced capacity
  ✓ Data residency doesn't require serving requests locally

FAILOVER PROCESS:
  1. Detect primary failure (health check → DNS TTL-based cutover)
  2. Promote standby database to writable
  3. Update DNS/load balancer to route to standby region
  4. Validate health, re-enable traffic
  Typical RTO: 2–10 minutes
  RPO (data loss): depends on replication lag — typically seconds to minutes
```

## Active-Active
```
REGION A (us-east-1) ◀──sync──▶ REGION B (eu-west-1)
     ↑                                   ↑
  ~50% traffic                        ~50% traffic

WHEN TO USE:
  ✓ RTO of seconds required (no failover — surviving region absorbs all traffic)
  ✓ Low latency for globally distributed users is a requirement
  ✓ Traffic volume too high for one region to absorb alone
  ✓ SLA requires near-zero downtime

CHALLENGES:
  ✗ Write conflicts — two regions can update the same record simultaneously
  ✗ Requires CRDT-friendly data models or conflict resolution strategy
  ✗ Much more expensive — N full-capacity regions
  ✗ Operational complexity: every deployment must handle cross-region state
```

## Active-Active-Read-Local (Hybrid — Common Best Practice)
```
WRITES ──▶ Single "home" region (based on user or entity ownership)
READS  ──▶ Local region (from replica — eventual consistency)

Examples:
  User in EU: reads from EU replica (fast), writes route to EU region
  User in US: reads from US replica (fast), writes route to US region
  
  Entities (accounts, orders) "owned" by a region
  Cross-region writes avoided by design — not by accident

This is how Stripe, Shopify, and most large-scale SaaS operate globally.
```

# DATA STRATEGY

## Replication Topology
```
SYNCHRONOUS replication:
  + No data loss (RPO = 0)
  - Write latency = local + cross-region RTT (~60–100ms US↔EU)
  - Writer blocks until standby acknowledges
  Use for: financial transactions, inventory (anything where losing data is catastrophic)

ASYNCHRONOUS replication:
  + Write latency unaffected
  - Data loss window = replication lag (typically <1s for well-tuned setups)
  Use for: user profile data, read replicas, analytics, sessions

SEMI-SYNCHRONOUS (one sync replica):
  + Durability guarantee with one ack
  - Slightly higher write latency
  Use for: most production systems (balance of safety and performance)
```

## Conflict Resolution Patterns
```
1. LAST WRITE WINS (LWW):
   Winner = highest timestamp
   Risk: clock skew between regions (use hybrid logical clocks, not wall clock)
   Use for: user preferences, non-critical settings

2. REGION OWNERSHIP:
   Each entity "belongs" to one region; only that region accepts writes
   Other regions read stale data but never write
   Use for: user accounts (user owns their account, home region = signup region)

3. CRDTs (Conflict-free Replicated Data Types):
   Data structures designed to merge without conflicts
   Examples: counters (increment only), sets (add-wins), shopping carts
   Use for: collaborative features, counters, presence

4. OPTIMISTIC LOCKING + MERGE:
   Detect conflicts at commit time, apply domain-specific merge logic
   Use for: documents, shared state with business-defined merge rules

5. PESSIMISTIC LOCKING (global):
   Acquire cross-region lock before write
   Use for: critical financial operations only — very high latency cost
```

## Database Options
```
GLOBALLY DISTRIBUTED DATABASES:
  CockroachDB      — serializable distributed SQL; auto-sharding by geography
  Google Spanner   — external consistency, TrueTime API; expensive
  PlanetScale      — MySQL-compatible; horizontal sharding
  Neon             — Postgres; regional branching (newer option)

READ REPLICAS (simpler, most common):
  RDS Multi-Region Read Replicas
  PgBouncer + streaming replication
  Aurora Global Database (up to 5 secondary regions, <1s replication lag)

EVENTUALLY CONSISTENT (for specific workloads):
  DynamoDB Global Tables — multi-region active-active, last-write-wins
  Cassandra — tunable consistency, excellent multi-DC support
  Redis (Aiven / Upstash) — for sessions, caching, rate limits
```

# ROUTING ARCHITECTURE

## DNS-Based Routing
```
LATENCY-BASED:
  Route 53 / Cloudflare — route user to the region with lowest RTT
  Update: Route53 latency routing policy per region
  TTL: 60s (shorter = faster failover, higher DNS query volume)

GEO-BASED (for data residency):
  European users → eu-west-1 only (GDPR data residency)
  Route 53 Geolocation routing
  Important: Geolocation ≠ latency — may not be the fastest region

FAILOVER:
  Route 53 health checks + DNS failover record
  Health check: HTTPS to /health endpoint, 30s interval, 3 failures = unhealthy
  Failover TTL: keep low (30–60s) for fast cutover
```

## Global Load Balancing
```
AWS:
  Global Accelerator → Anycast IPs → nearest edge → regional ALB
  + Persistent TCP connections (no client reconnect on failover)
  + ~60% lower latency than DNS-based for dynamic content
  + Sub-minute failover vs DNS TTL wait

GCP:
  Global HTTP(S) Load Balancer — single Anycast IP, routes to nearest backend
  Premium Tier networking — Google's backbone, not public internet

Cloudflare:
  Load Balancing + Argo Smart Routing
  Workers at edge for routing logic before hitting origin
```

# FAILOVER RUNBOOK

## Automated Failover
```python
# Health check + automatic DNS failover pseudocode
async def region_health_monitor():
    while True:
        health = await check_region_health(PRIMARY_REGION)

        if not health.is_healthy:
            consecutive_failures += 1
        else:
            consecutive_failures = 0

        if consecutive_failures >= FAILURE_THRESHOLD:  # e.g., 3 consecutive
            await trigger_failover(
                from_region=PRIMARY_REGION,
                to_region=FAILOVER_REGION
            )
            await notify_oncall(f"Failover triggered: {PRIMARY_REGION} → {FAILOVER_REGION}")
            break

        await asyncio.sleep(HEALTH_CHECK_INTERVAL)  # e.g., 10s

async def trigger_failover(from_region, to_region):
    # 1. Promote standby DB to writable
    await promote_database(to_region)

    # 2. Update traffic routing (DNS or load balancer)
    await update_routing(active_region=to_region)

    # 3. Scale up standby to full capacity if it was running reduced
    await scale_region(to_region, capacity="full")

    # 4. Block writes to degraded region to prevent split-brain
    await set_region_read_only(from_region)
```

## Manual Failover Checklist
```
[ ] Confirm primary region failure (≥ 2 independent sources)
[ ] Check replication lag — understand potential data loss window
[ ] Notify stakeholders before cutover
[ ] Promote standby DB (RDS: modify-db-cluster --enable-write-forwarding)
[ ] Update Route 53 / LB routing to DR region
[ ] Validate: smoke test critical user journeys in DR region
[ ] Monitor error rates post-cutover (5min, 15min, 30min checkpoints)
[ ] Communicate status page update
[ ] Do NOT attempt to fail back during incident — stabilize first
[ ] Schedule post-mortem and failback during business hours
```

# DATA RESIDENCY & COMPLIANCE

## GDPR / Regional Data Requirements
```
EU users' personal data must stay in EU:
  - Database: eu-west-1 only for EU users
  - Backups: stored in EU regions only
  - Logs: ensure log aggregation doesn't ship EU user data to US
  - CDN: Cloudflare Enterprise — EU-only data zone (Data Localization Suite)

Implementation:
  User entity has "home_region" field set at registration
  All PII queries routed to home_region database
  Read replicas in other regions contain only non-PII or EU-only data
  Audit log of all data access stored in same region as data

Tools:
  AWS: CloudTrail data events, S3 Object Lock for compliance records
  Terraform: enforce region constraints via policy-as-code (OPA / Sentinel)
```

# TESTING MULTI-REGION SYSTEMS
```
WHAT TO TEST:

Replication lag under load:
  → Run write-heavy load test on primary, measure lag to replica
  → Alert if lag > acceptable threshold (e.g., > 5s)

Failover time:
  → Simulate region failure in staging, measure actual RTO
  → Compare against SLO — do this quarterly minimum

Data consistency after failover:
  → After failover, verify no data was lost beyond RPO window
  → Run checksum comparison: primary record count vs promoted standby

Split-brain prevention:
  → Verify old primary correctly refuses writes after being demoted
  → Simulate network partition — confirm only one region accepts writes

Cross-region latency budget:
  → Measure actual p99 write latency with synchronous replication
  → Confirm it meets your application's requirements
```

# COST CONSIDERATIONS
```
COMPUTE:
  Active-passive: 1.5–2× baseline (standby at 50–75% capacity)
  Active-active:  2× baseline (full capacity in each region)

DATA TRANSFER:
  Cross-region replication traffic — often overlooked cost
  AWS: ~$0.02/GB cross-region; 1TB/day replication = ~$600/month
  Compress data before replication; replicate diffs not full snapshots

STORAGE:
  EBS snapshots cross-region for DR: ~$0.05/GB/month
  Aurora Global: additional replica storage per region

RULE OF THUMB:
  Multi-region active-active: 3–4× single-region cost
  Is your business continuity requirement worth 3–4× infrastructure spend?
  Calculate the cost of downtime first. Then decide.
```
