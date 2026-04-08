---
name: Database Sharding & Partitioning
trigger: database sharding, horizontal sharding, shard key, partitioning, partition strategy, horizontal scaling database, sharding strategy, consistent hashing, shard routing, cross-shard queries, resharding, partition pruning
description: Design and implement database sharding and partitioning strategies. Covers shard key selection, routing, partition types, cross-shard operations, resharding, and when to avoid sharding entirely.
---

# ROLE
You are a senior database engineer. Sharding is one of the most consequential architectural decisions you can make — easy to get wrong, very painful to undo. Your job is to choose the right strategy for the problem and implement it without creating worse problems.

# START HERE: DO YOU ACTUALLY NEED SHARDING?

## Exhaust These First
```
Before sharding, verify you've done all of these:

INDEXING:
  [ ] All query predicates have appropriate indexes
  [ ] No sequential scans on large tables (check pg_stat_user_tables)
  [ ] Covering indexes for high-frequency queries

READ SCALING:
  [ ] Read replicas for read-heavy workloads
  [ ] Connection pooling (PgBouncer) — improves throughput 3–5×
  [ ] Query result caching (Redis) for frequently-read data

VERTICAL SCALING:
  [ ] Larger instance type? (RDS r6g.8xlarge before sharding)
  [ ] More IOPS? (provisioned IOPS vs gp3)

DATA ARCHIVAL:
  [ ] Archive historical data to S3 / data warehouse
  [ ] Table partitioning (partition pruning can eliminate 99% of I/O)
  [ ] Soft delete + periodic hard delete of old data

WHEN YOU ACTUALLY NEED SHARDING:
  → Single node has maxed CPU/RAM/IOPS and vertical scaling is not cost-effective
  → Write throughput exceeds single-node limits (~10K–50K writes/s for Postgres)
  → Data volume is growing faster than storage can scale
  → Need multi-region writes (each region owns its shard)
```

# PARTITIONING (WITHIN ONE DATABASE)

## Range Partitioning
```sql
-- Partition by time — most common use case (logs, events, time-series)
CREATE TABLE events (
  id          BIGSERIAL,
  user_id     BIGINT NOT NULL,
  event_type  TEXT NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL,
  payload     JSONB
) PARTITION BY RANGE (occurred_at);

-- Monthly partitions — auto-created, auto-pruned
CREATE TABLE events_2025_01 PARTITION OF events
  FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE events_2025_02 PARTITION OF events
  FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- PostgreSQL prunes unused partitions automatically in queries:
SELECT * FROM events WHERE occurred_at >= '2025-03-01';
-- → Only scans events_2025_03, not all 24 monthly partitions

-- Create future partitions before they're needed (cron job or pg_partman)
-- pg_partman automates this for you
```

## Hash Partitioning
```sql
-- Distribute rows evenly when there's no natural time dimension
CREATE TABLE orders (
  id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id   BIGINT NOT NULL,
  total     NUMERIC(10,2)
) PARTITION BY HASH (user_id);

-- 8 partitions — distribute load evenly
CREATE TABLE orders_p0 PARTITION OF orders FOR VALUES WITH (MODULUS 8, REMAINDER 0);
CREATE TABLE orders_p1 PARTITION OF orders FOR VALUES WITH (MODULUS 8, REMAINDER 1);
-- ... p2 through p7

-- Each partition is a separate physical file → parallel I/O
-- Queries with user_id predicate → only scans 1/8 of data
```

## List Partitioning
```sql
-- Partition by known categorical values — ideal for geographic data
CREATE TABLE users (
  id     UUID,
  region TEXT NOT NULL,
  email  TEXT
) PARTITION BY LIST (region);

CREATE TABLE users_us PARTITION OF users FOR VALUES IN ('us-east', 'us-west', 'us-central');
CREATE TABLE users_eu PARTITION OF users FOR VALUES IN ('eu-west', 'eu-central', 'eu-north');
CREATE TABLE users_ap PARTITION OF users FOR VALUES IN ('ap-southeast', 'ap-northeast');

-- Perfect for data residency requirements:
--   EU users stay in eu-* partitions → point eu-* to EU-region tablespace
```

# HORIZONTAL SHARDING (ACROSS MULTIPLE DATABASES)

## Shard Key Selection — Most Important Decision
```
THE SHARD KEY DETERMINES EVERYTHING:
  - Which queries are fast (same-shard) vs slow (cross-shard)
  - Whether shards stay balanced or get hot spots
  - How painful resharding will be

GOOD SHARD KEY PROPERTIES:
  ✓ High cardinality — many distinct values
  ✓ Evenly distributed — no hot spots (avoid status fields, boolean, country)
  ✓ Immutable — the key never changes after the row is created
  ✓ Present in almost every query — don't shard on a field you rarely filter on

COMMON PATTERNS:
  Multi-tenant SaaS:    tenant_id / organization_id
  Social platform:      user_id
  E-commerce:           user_id (not order_id — orders need user context)
  IoT/Time-series:      device_id (+ time partitioning within shard)
  Geographic:           region (if data residency matters more than balance)

ANTI-PATTERNS:
  ✗ Auto-increment integer: all new rows go to the last shard → hot spot
  ✗ Timestamp only: same as above — all current writes on last shard
  ✗ Status field: low cardinality → some shards grow much larger
  ✗ Composite key with non-immutable field: shard assignment can change
```

## Shard Routing Strategies

### Hash-Based (Most Common)
```python
def get_shard(shard_key: str, num_shards: int) -> int:
    # Consistent, deterministic routing
    return int(hashlib.sha256(shard_key.encode()).hexdigest(), 16) % num_shards

# Problem: changing num_shards remaps ALL keys
# Solution: consistent hashing (see below)

# Example lookup:
user_id = "usr_01HX2J3K4L"
shard_number = get_shard(user_id, num_shards=16)
db_connection = shard_pool[shard_number]
```

### Consistent Hashing (For Resharding)
```python
import bisect
import hashlib

class ConsistentHashRing:
    def __init__(self, nodes: list[str], replicas: int = 150):
        self.replicas = replicas
        self.ring = {}
        self.sorted_keys = []

        for node in nodes:
            self.add_node(node)

    def add_node(self, node: str):
        for i in range(self.replicas):
            key = self._hash(f"{node}:{i}")
            self.ring[key] = node
            self.sorted_keys.append(key)
        self.sorted_keys.sort()

    def remove_node(self, node: str):
        # When removing a node: only that node's keys remap to neighbors
        # Not a full remap of all keys
        for i in range(self.replicas):
            key = self._hash(f"{node}:{i}")
            del self.ring[key]
            self.sorted_keys.remove(key)

    def get_node(self, key: str) -> str:
        hash_key = self._hash(key)
        idx = bisect.bisect(self.sorted_keys, hash_key) % len(self.sorted_keys)
        return self.ring[self.sorted_keys[idx]]

    def _hash(self, value: str) -> int:
        return int(hashlib.md5(value.encode()).hexdigest(), 16)

# Adding a new shard: only ~1/N of existing keys remap to the new shard
ring = ConsistentHashRing(nodes=["shard-0", "shard-1", "shard-2"])
ring.add_node("shard-3")  # Only ~25% of data moves to shard-3
```

### Lookup Table (Range-Based Routing)
```sql
-- Explicit mapping: control which tenant goes to which shard
CREATE TABLE shard_routing (
  tenant_id   UUID PRIMARY KEY,
  shard_id    INT NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Expensive tenants get dedicated shards; small tenants share
INSERT INTO shard_routing (tenant_id, shard_id) VALUES
  ('acme-corp',   1),   -- large tenant, dedicated shard
  ('small-co',    2),   -- small tenants share shard 2
  ('tiny-inc',    2);

-- Routing logic:
-- SELECT shard_id FROM shard_routing WHERE tenant_id = ?
-- → connect to shard_{shard_id} database

-- Pros: precise control, can rebalance without rehashing
-- Cons: routing table itself becomes a bottleneck (cache it aggressively)
```

# CROSS-SHARD OPERATIONS

## The Problem
```
WITHIN ONE SHARD: fast, ACID, joins work normally
ACROSS SHARDS:    slow, no native ACID, joins require application-level merge

WHAT REQUIRES CROSS-SHARD:
  SELECT * FROM orders WHERE status = 'pending'  → must query ALL shards
  SELECT COUNT(*) FROM users                     → must query ALL shards, sum results
  JOIN users u ON o.user_id = u.id               → if users and orders are on different shards

STRATEGIES:
```

### Scatter-Gather
```python
async def get_pending_orders_across_shards():
    # Query all shards in parallel, merge results
    tasks = [query_shard(shard_id, "SELECT * FROM orders WHERE status = 'pending'")
             for shard_id in range(NUM_SHARDS)]

    results = await asyncio.gather(*tasks)

    # Merge and sort in application
    all_orders = [order for shard_result in results for order in shard_result]
    return sorted(all_orders, key=lambda o: o.created_at, reverse=True)

# Cost: N round-trips (N = number of shards)
# Mitigation: keep number of shards low (8–32) for cross-shard queries
```

### Colocation (Design Shards Together)
```
Key insight: shard RELATED data together on the same shard

BAD: users on shard by user_id, orders on shard by order_id
  → user_id=123 is on shard 3, their orders might be on shards 1, 7, 15

GOOD: users AND orders sharded by user_id
  → user_id=123 is always on shard 3. Their orders are ALWAYS on shard 3.
  → join users + orders for a user = single-shard query

PRINCIPLE: choose one global shard key and apply it consistently across all tables
```

### Global Tables (Read-Only Reference Data)
```
Some tables are read-only reference data that every shard needs:
  - Product catalog
  - Country codes
  - Configuration tables

Copy these to EVERY shard:
  - Written once, read everywhere
  - Changes replicated to all shards (acceptable for slow-changing data)
  - No cross-shard query needed for joins against these tables
```

# RESHARDING

## Resharding Strategy (Online, No Downtime)
```
CHALLENGE: Moving data between shards while live traffic continues

STEPS:
1. Double-write period:
   - New writes go to both old shard AND new shard
   - Reads still come from old shard

2. Backfill:
   - Copy historical data from old shard to new shard
   - Track progress per row (use a migration ID / offset)

3. Verify:
   - Checksums: count and hash data in both shards
   - Confirm new shard is current (no missing writes)

4. Cut over reads:
   - Start reading from new shard for affected keys
   - Monitor error rate

5. Stop double-writes:
   - Once reads confirmed good, stop writing to old shard for these keys

6. Cleanup:
   - After retention period, delete migrated data from old shard

TOOLING:
  Vitess: purpose-built MySQL sharding with online resharding
  Citus: Postgres extension with built-in rebalancing
  Custom: the above pattern implemented with a migration service
```

# MONITORING SHARDED SYSTEMS

## Key Metrics
```sql
-- Check for hot shards (one shard getting much more load than others)
SELECT shard_id,
       COUNT(*) as row_count,
       MAX(updated_at) as last_write,
       pg_size_pretty(pg_total_relation_size('orders')) as table_size
FROM shard_metadata
GROUP BY shard_id
ORDER BY row_count DESC;

-- Flag if any shard has > 2× the average size → hot spot
```

```python
# Application-level shard health dashboard:
SHARD_METRICS = [
    "query_latency_p99",      # per shard — hot shard shows higher latency
    "connection_pool_usage",  # near 100% = shard is saturated
    "write_throughput",       # should be roughly equal across shards
    "row_count",              # should grow at similar rates
    "replication_lag",        # if shards have replicas
]
```

# DECISION CHECKLIST
```
Before choosing a sharding approach:
  [ ] Have you exhausted vertical scaling + indexing + caching?
  [ ] What is your shard key? Is it immutable? Evenly distributed? High cardinality?
  [ ] What are your most common query patterns? Will they be cross-shard?
  [ ] How will you handle cross-shard queries / reports?
  [ ] What is your resharding plan when you need more shards?
  [ ] Can your team operate N databases instead of 1?
  [ ] Have you considered Citus, CockroachDB, or Vitess instead of DIY?

RULE OF THUMB:
  8–32 shards: manageable manually
  32–128 shards: need orchestration tooling (Vitess, Citus)
  128+ shards: you're Google/Meta — use a purpose-built distributed database
```
