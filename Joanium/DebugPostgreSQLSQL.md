---
name: Debug — PostgreSQL / SQL
trigger: postgres error, sql bug, slow query, query not returning results, deadlock postgres, migration failing, connection refused postgres, pg error, database error, orm query wrong, explain analyze, index not used, n+1 query
description: Hyper-specific debugging guide for PostgreSQL and SQL. Real error codes, real causes, real fixes. Covers slow queries, EXPLAIN ANALYZE, locking/deadlocks, connection issues, index diagnosis, and common query bugs.
---

# Debug — PostgreSQL / SQL

## First Move

```bash
# Connect to your database
psql -U username -d dbname -h localhost

# Check PostgreSQL is running
pg_isready -h localhost -U postgres

# Check version
psql --version
SELECT version();

# See all active connections and what they're doing
SELECT pid, usename, application_name, state, query, query_start, wait_event_type, wait_event
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start;

# Check DB size and table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) AS total_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC;
```

---

## Slow Queries — EXPLAIN ANALYZE

`EXPLAIN` shows the query plan. `EXPLAIN ANALYZE` actually runs it and shows real timing.

```sql
-- Always start with EXPLAIN ANALYZE for slow queries
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT u.*, p.name as plan_name
FROM users u
JOIN subscriptions s ON s.user_id = u.id
JOIN plans p ON p.id = s.plan_id
WHERE u.created_at > '2024-01-01'
  AND s.status = 'active';

-- Read the output:
-- Seq Scan on users  (cost=0.00..12500.00 rows=50000 width=64)
--                        ↑ estimated rows              actual rows ↓
--   (actual time=0.123..456.789 rows=48234 loops=1)
--   Buffers: shared hit=1234 read=5678   ← read = went to disk (slow!)
-- Filter: (created_at > '2024-01-01'::timestamp)
--   Rows Removed by Filter: 200000  ← filtering 200K rows — needs an index!

-- Bad signs to look for:
-- "Seq Scan" on a large table  → likely needs an index
-- "Rows Removed by Filter: X"  → index on that filter column needed
-- "Hash Join" with large "Batches: N" → not enough work_mem for hash
-- "Nested Loop" with high row count  → N+1 in SQL
-- High "Buffers: ... read=" numbers  → data not in cache, hitting disk
```

---

## Index Diagnosis

```sql
-- Check if an index exists
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'users';

-- Check if your index is being used (after running some queries)
SELECT
  indexrelname AS index,
  idx_scan AS times_used,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
WHERE relname = 'users'
ORDER BY idx_scan DESC;

-- Find tables with zero index scans (maybe wrong indexes)
SELECT relname, seq_scan, idx_scan
FROM pg_stat_user_tables
WHERE seq_scan > idx_scan
  AND n_live_tup > 10000  -- only large tables
ORDER BY seq_scan DESC;

-- Why is my index NOT being used?

-- 1. Function wrapping the column
WHERE LOWER(email) = 'user@example.com'  -- index on email not used
-- Fix: create a functional index
CREATE INDEX idx_users_email_lower ON users (LOWER(email));
-- Or: store the value normalized

-- 2. Type mismatch — casting defeats the index
WHERE user_id = '123'  -- user_id is integer, '123' is text → implicit cast
-- Fix: match the type
WHERE user_id = 123

-- 3. Planner thinks seq scan is faster (low row count or bad stats)
-- Force index use to test (don't leave this in production)
SET enable_seqscan = OFF;
EXPLAIN ANALYZE SELECT ...;
SET enable_seqscan = ON;

-- Update statistics if rows changed a lot
ANALYZE users;
-- Or full vacuum + analyze
VACUUM ANALYZE users;

-- 4. Low cardinality column (e.g., status with 2 values)
-- Index may not help if query returns 40% of rows — planner prefers seq scan
-- Fix: partial index for selective values
CREATE INDEX idx_users_pending ON users (id) WHERE status = 'pending';
-- Now: WHERE status = 'pending' uses this small index

-- Create indexes correctly
CREATE INDEX CONCURRENTLY idx_users_email ON users (email);  -- CONCURRENTLY = no table lock!
CREATE INDEX idx_orders_user_status ON orders (user_id, status);  -- composite for multi-column WHERE
CREATE INDEX idx_posts_created ON posts (created_at DESC);  -- DESC for ORDER BY ... DESC
```

---

## Locking and Deadlocks

```sql
-- See what's locked right now
SELECT
  pid,
  relation::regclass AS table,
  locktype,
  mode,
  granted,
  query
FROM pg_locks l
JOIN pg_stat_activity a USING (pid)
WHERE NOT granted;  -- waiting for a lock

-- Find lock chain — who is blocking whom
SELECT
  blocked.pid AS blocked_pid,
  blocked.query AS blocked_query,
  blocking.pid AS blocking_pid,
  blocking.query AS blocking_query
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking ON blocking.pid = ANY(pg_blocking_pids(blocked.pid))
WHERE blocked.wait_event_type = 'Lock';

-- Kill a blocking query (use carefully)
SELECT pg_terminate_backend(pid);  -- hard kill — terminates connection
SELECT pg_cancel_backend(pid);     -- soft cancel — cancels query, keeps connection

-- Deadlock analysis — check PostgreSQL logs
-- PostgreSQL logs deadlocks automatically — find them:
-- DETAIL: Process 12345 waits for ShareLock on transaction 789; blocked by process 67890

-- Prevent deadlocks:
-- 1. Always acquire locks in the same order across transactions
-- 2. Keep transactions short
-- 3. Use SELECT ... FOR UPDATE SKIP LOCKED for queue patterns
SELECT id, payload FROM jobs
WHERE status = 'pending'
LIMIT 1
FOR UPDATE SKIP LOCKED;  -- skips rows locked by other workers — no deadlock

-- 4. Use advisory locks for application-level coordination
SELECT pg_try_advisory_lock(user_id)  -- returns true if got the lock
```

---

## Common Query Bugs

### Query Returns Wrong Results

```sql
-- NULL comparisons — NULL != anything including NULL
WHERE status != 'inactive'  -- rows with NULL status are EXCLUDED (NULL != 'inactive' = NULL, not TRUE)
-- Fix:
WHERE status != 'inactive' OR status IS NULL

-- Implicit type coercion
WHERE created_at = '2024-01-15'
-- created_at is TIMESTAMP — this works but compares to midnight only
-- Fix: use a range
WHERE created_at >= '2024-01-15' AND created_at < '2024-01-16'

-- GROUP BY with non-aggregated columns
SELECT user_id, name, COUNT(*)
FROM orders
GROUP BY user_id  -- Error in strict SQL: name must be in GROUP BY or aggregated
GROUP BY user_id, name  -- Fix

-- DISTINCT vs GROUP BY for deduplication
SELECT DISTINCT user_id FROM orders        -- simpler, same result for single column
SELECT user_id FROM orders GROUP BY user_id  -- needed when combining with aggregates

-- JOIN produces more rows than expected (unintentional fan-out)
-- If user has 3 orders and 2 addresses → JOIN gives 6 rows
SELECT u.id, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
LEFT JOIN addresses a ON a.user_id = u.id  -- joins multiply rows!
GROUP BY u.id
-- Fix: pre-aggregate in a subquery
SELECT u.id, o.order_count
FROM users u
LEFT JOIN (
  SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id
) o ON o.user_id = u.id
```

---

### Missing Data / Empty Results

```sql
-- INNER JOIN vs LEFT JOIN
SELECT u.name, o.total
FROM users u
INNER JOIN orders o ON o.user_id = u.id  -- users with NO orders are excluded!
-- Fix: use LEFT JOIN to keep all users
LEFT JOIN orders o ON o.user_id = u.id  -- NULL order columns for users with no orders

-- WHERE clause on LEFT JOIN column kills it
SELECT u.name, o.total
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE o.status = 'active'  -- users with no orders → o.status IS NULL → excluded!
-- Fix: move filter to JOIN condition
LEFT JOIN orders o ON o.user_id = u.id AND o.status = 'active'

-- HAVING vs WHERE
WHERE COUNT(*) > 5    -- Error: aggregate not allowed in WHERE
HAVING COUNT(*) > 5  -- Correct: HAVING filters after GROUP BY
```

---

## Connection Issues

```bash
# "too many connections" error
# Check current connections
SELECT count(*), state FROM pg_stat_activity GROUP BY state;
SELECT max_conn FROM pg_settings WHERE name = 'max_connections';

# Fix: use a connection pool — never connect directly from app
# PgBouncer (most common):
# - transaction mode: 1 connection serves many requests (best for web apps)
# - session mode: 1 connection per client session

# Connection string with PgBouncer (port 6432 usually):
DATABASE_URL=postgresql://user:pass@localhost:6432/dbname

# "connection refused" — check PostgreSQL is running
pg_isready
systemctl status postgresql
# Check pg_hba.conf for auth rules
sudo cat /etc/postgresql/*/main/pg_hba.conf

# "SSL required" errors
# Add ?sslmode=require or ?sslmode=disable to connection string
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
```

---

## Migrations (Raw SQL)

```sql
-- Always make migrations transactional
BEGIN;

ALTER TABLE users ADD COLUMN phone VARCHAR(20);
CREATE INDEX CONCURRENTLY ... -- Error: CONCURRENTLY can't be inside transaction
-- Remove CONCURRENTLY if inside BEGIN/COMMIT, or create index separately

COMMIT;

-- Large table migrations — avoid locking
-- Adding a nullable column: fast, no rewrite
ALTER TABLE users ADD COLUMN metadata JSONB;  -- instant even on huge tables

-- Adding NOT NULL column: dangerous on large tables (rewrites table)
-- Safe approach:
ALTER TABLE users ADD COLUMN score INT;      -- nullable first
UPDATE users SET score = 0 WHERE score IS NULL;  -- backfill in batches
ALTER TABLE users ALTER COLUMN score SET NOT NULL;  -- then add constraint

-- Adding an index without locking reads/writes
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
-- Takes longer but doesn't block any operations

-- Check if migration succeeded
\d users  -- describe table — shows columns and indexes

-- Revert a migration
ALTER TABLE users DROP COLUMN phone;
DROP INDEX idx_users_email;
```

---

## Performance Tuning

```sql
-- Slow aggregate query? Try materialized views
CREATE MATERIALIZED VIEW user_stats AS
SELECT
  user_id,
  COUNT(*) as total_orders,
  SUM(total) as lifetime_value,
  MAX(created_at) as last_order
FROM orders
GROUP BY user_id;

CREATE INDEX ON user_stats (user_id);

-- Refresh (does not lock reads in PostgreSQL 9.4+)
REFRESH MATERIALIZED VIEW CONCURRENTLY user_stats;

-- Useful config for development (see all slow queries)
-- In postgresql.conf or via SET:
SET log_min_duration_statement = 100;  -- log queries taking > 100ms
SET log_statement = 'all';             -- log all statements (very verbose)

-- work_mem — affects hash joins and sorts (per-operation, not per-connection)
SET work_mem = '64MB';  -- try increasing if hash joins are slow
-- CAREFUL: max connections × work_mem × operations per query = RAM usage

-- Check table bloat (dead rows from updates/deletes)
SELECT
  relname,
  n_dead_tup,
  n_live_tup,
  round(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 1) AS dead_pct
FROM pg_stat_user_tables
WHERE n_live_tup > 0
ORDER BY dead_pct DESC;
-- If dead_pct > 20% → run VACUUM ANALYZE table_name
```
