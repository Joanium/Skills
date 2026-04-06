---
name: Database Query Optimization
trigger: slow query, query optimization, optimize sql, database performance, query tuning, explain plan, index design, slow database, n+1 query, query too slow, db bottleneck, explain analyze
description: Diagnose and fix slow database queries through systematic analysis of execution plans, index design, and query restructuring. Use when queries are too slow, the database is a bottleneck, or you're designing indexes for a new feature.
---

A slow query is a conversation between your code and the database about what you actually want. Most performance problems happen because the database is working much harder than it needs to — fetching rows you'll discard, scanning tables you could skip, joining in the wrong order. Learn to read what the database is telling you.

## Diagnosis First, Optimization Second

Never guess. Measure before you change anything.

```sql
-- PostgreSQL: always start here
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123;

-- MySQL
EXPLAIN FORMAT=JSON SELECT * FROM orders WHERE user_id = 123;

-- Add BUFFERS to see cache hit rates in PostgreSQL
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) SELECT ...;
```

**What to look for in EXPLAIN output:**
```
Seq Scan        → Full table scan. Usually bad on large tables.
Index Scan      → Using an index. Good.
Index Only Scan → Reading only from the index. Best for covered queries.
Nested Loop     → Fine for small datasets, dangerous for large ones.
Hash Join       → Good for large equi-joins.
Merge Join      → Good for pre-sorted large datasets.

Rows=1000 (actual=50000) → Stale statistics. Run ANALYZE.
cost=0.00..9999.99       → Estimated cost. Higher = more work.
actual time=0.1..2340.5  → Real time in milliseconds. This is the truth.
```

## Finding Slow Queries

### PostgreSQL: pg_stat_statements
```sql
-- Top 10 slowest queries by total time
SELECT 
  round(total_exec_time::numeric, 2) AS total_ms,
  calls,
  round(mean_exec_time::numeric, 2) AS mean_ms,
  round((100 * total_exec_time / sum(total_exec_time) OVER ())::numeric, 2) AS pct,
  query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- Queries with the most rows examined vs returned (efficiency ratio)
SELECT 
  query,
  calls,
  rows,
  round(mean_exec_time::numeric, 2) AS mean_ms
FROM pg_stat_statements
WHERE calls > 100
ORDER BY mean_exec_time DESC
LIMIT 20;
```

### MySQL: slow query log
```sql
-- Enable slow query log
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1; -- queries > 1 second

-- Then use: mysqldumpslow -s t /var/log/mysql/slow.log
```

### Application-Level: detect N+1
```javascript
// ORM logging (Sequelize)
const sequelize = new Sequelize({ logging: console.log });

// Knex query count middleware
let queryCount = 0;
knex.on('query', () => queryCount++);
// If queryCount > ~5 per request, you likely have N+1
```

## The N+1 Problem

The single most common database performance killer:

```javascript
// BAD: N+1 — 1 query for orders + 1 per order for the user
const orders = await Order.findAll();
for (const order of orders) {
  const user = await User.findByPk(order.userId); // N queries!
  console.log(user.name);
}

// GOOD: 2 queries — eager load
const orders = await Order.findAll({
  include: [{ model: User }]
});

// BETTER: 1 query with JOIN
const orders = await Order.findAll({
  include: [{ model: User, required: true }] // INNER JOIN
});

// BEST for reporting: raw SQL join
SELECT o.id, o.total, u.name 
FROM orders o
JOIN users u ON u.id = o.user_id
WHERE o.created_at > NOW() - INTERVAL '7 days';
```

## Index Design

### When to add an index
```sql
-- Check if a column has an index
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'orders' AND indexdef LIKE '%user_id%';

-- Check index usage (drop unused indexes)
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
WHERE idx_scan = 0  -- never used!
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Index types and when to use them
```sql
-- B-tree (default): equality, range, ORDER BY
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_created ON orders(created_at DESC);

-- Composite index: column order matters!
-- Supports WHERE user_id = ? AND status = ? 
-- Also supports WHERE user_id = ? alone
-- Does NOT support WHERE status = ? alone
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- Partial index: only index rows you query
-- Perfect for "active" records
CREATE INDEX idx_orders_pending ON orders(created_at)
WHERE status = 'pending';

-- Covering index: include extra columns to avoid table lookup
-- Query can be satisfied from index alone (Index Only Scan)
CREATE INDEX idx_orders_cover ON orders(user_id)
INCLUDE (total, status, created_at);

-- GIN index: for JSONB, arrays, full-text search
CREATE INDEX idx_orders_metadata ON orders USING GIN(metadata);

-- Expression index: for computed columns
CREATE INDEX idx_users_lower_email ON users(lower(email));
```

### The most important index rules
```
1. Index columns you filter on (WHERE, JOIN ON)
2. Index columns you sort on (ORDER BY) — direction matters
3. Put high-cardinality columns first in composite indexes
4. Index foreign keys — always (unindexed FKs cause full scans on joins)
5. Never index low-cardinality booleans alone (use partial index instead)
6. Indexes slow writes — don't add them speculatively
```

## Query Restructuring Patterns

### Replace correlated subqueries with JOINs
```sql
-- SLOW: correlated subquery runs once per row
SELECT u.id, u.name,
  (SELECT COUNT(*) FROM orders WHERE user_id = u.id) AS order_count
FROM users u;

-- FAST: one pass with GROUP BY
SELECT u.id, u.name, COUNT(o.id) AS order_count
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
GROUP BY u.id, u.name;
```

### Use CTEs for readability, not always for performance
```sql
-- CTEs are not always optimized (PostgreSQL < 12 treats them as barriers)
-- Test with EXPLAIN ANALYZE both ways

WITH recent_orders AS (
  SELECT * FROM orders
  WHERE created_at > NOW() - INTERVAL '30 days'
)
SELECT user_id, SUM(total) 
FROM recent_orders
GROUP BY user_id;
```

### Pagination: cursor vs offset
```sql
-- SLOW: OFFSET becomes expensive on large tables
SELECT * FROM orders ORDER BY id LIMIT 20 OFFSET 100000;

-- FAST: cursor-based pagination
SELECT * FROM orders 
WHERE id > 100000  -- last seen ID from previous page
ORDER BY id 
LIMIT 20;
```

### Avoid functions on indexed columns in WHERE clauses
```sql
-- SLOW: function prevents index use
SELECT * FROM users WHERE LOWER(email) = 'alice@example.com';

-- FAST: use an expression index (see above), or store normalized
SELECT * FROM users WHERE email = lower('Alice@Example.Com');
-- With: CREATE INDEX ON users(lower(email));
```

## PostgreSQL-Specific Optimizations

```sql
-- Check for table bloat (dead rows from updates/deletes)
SELECT relname, n_dead_tup, n_live_tup, 
  round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 1) AS dead_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY dead_pct DESC;

-- Force manual vacuum on bloated tables
VACUUM ANALYZE orders;

-- Update statistics for better query plans
ANALYZE orders;

-- Check for missing FK indexes
SELECT conrelid::regclass AS table, conname, confrelid::regclass AS foreign_table
FROM pg_constraint
WHERE contype = 'f'
  AND NOT EXISTS (
    SELECT 1 FROM pg_index i
    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
    WHERE i.indrelid = conrelid AND a.attnum = conkey[1]
  );
```

## Query Optimization Checklist

```
Diagnosis:
☐ Run EXPLAIN ANALYZE on the slow query
☐ Identify the most expensive node (highest actual time)
☐ Check for Seq Scans on large tables
☐ Check rows estimate vs actual (stale stats?)
☐ Run ANALYZE if estimates are wildly off

Common fixes:
☐ Add index on WHERE/JOIN columns
☐ Add index on ORDER BY columns
☐ Fix N+1 with eager loading or a JOIN
☐ Replace OFFSET pagination with cursor pagination
☐ Remove functions from WHERE clauses on indexed columns
☐ Use covering indexes for hot read paths
☐ Add partial indexes for filtered queries (WHERE status = 'active')

After changes:
☐ EXPLAIN ANALYZE again — did it improve?
☐ Check index is actually being used (not just created)
☐ Test with production-scale data volume
☐ Monitor query time in production for 24h post-deploy
☐ Add the query to a performance regression test
```

## Optimization Summary Template

```
## Query Optimization Report

**Query:** [The slow query or the feature it supports]
**Observed latency:** [e.g., p95: 2.4s]
**Table size:** [e.g., orders: 12M rows]

**Root cause:** [e.g., Seq Scan on orders.user_id — no index, 800ms]

**Changes made:**
1. Added index: CREATE INDEX idx_orders_user_id ON orders(user_id);
2. Rewrote N+1 to JOIN (reduced 47 queries → 2)

**After optimization:** [p95: 18ms]
**Risk:** [Low — index add is non-blocking in PostgreSQL 12+]
**Rollback:** DROP INDEX idx_orders_user_id;
```
