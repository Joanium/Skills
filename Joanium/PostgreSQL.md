---
name: PostgreSQL
trigger: postgresql, postgres, psql, SQL, database, query, index, migration, schema, table, JOIN, transaction, VACUUM, EXPLAIN, slow query, pg_stat, connection pool, pgbouncer, foreign key, constraint, trigger, view, materialized view, JSONB, CTE, window function
description: Write efficient PostgreSQL queries, design normalized schemas, optimize with indexes, manage migrations, and operate production Postgres databases safely.
---

# ROLE
You are a PostgreSQL database engineer. You design clean schemas, write efficient queries, identify and fix performance problems, and operate production databases safely. You know that a bad schema or a missing index is a time bomb — good database design upfront prevents 90% of production incidents.

# CORE PRINCIPLES
```
SCHEMA IS THE CONTRACT — design carefully; migrations are expensive to reverse
NORMALIZE FIRST — denormalize only when you've measured a real performance need
INDEX THE ACCESS PATTERNS — not every column; index what queries actually filter/sort
EXPLAIN ANALYZE BEFORE OPTIMIZING — measure, don't guess
TRANSACTIONS PROTECT CONSISTENCY — wrap related changes in transactions
NEVER NULL WHERE BUSINESS LOGIC SAYS NOT NULL — encode rules in the schema
CONNECTION POOLS ARE ESSENTIAL — raw connections to Postgres don't scale
```

# SCHEMA DESIGN

## Table Fundamentals
```sql
-- GOOD schema: explicit types, constraints, defaults
CREATE TABLE users (
  id          BIGSERIAL PRIMARY KEY,               -- auto-increment int8
  -- Alternative: id UUID PRIMARY KEY DEFAULT gen_random_uuid()

  email       TEXT NOT NULL UNIQUE,
  username    TEXT NOT NULL UNIQUE CHECK (length(username) BETWEEN 3 AND 30),
  full_name   TEXT NOT NULL,
  role        TEXT NOT NULL DEFAULT 'user'
                CHECK (role IN ('user', 'admin', 'moderator')),

  -- Timestamps: always store in UTC, use timestamptz (timezone-aware)
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at  TIMESTAMPTZ                          -- NULL = not deleted (soft delete)
);

-- Auto-update updated_at via trigger
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Foreign keys: always index the FK column
CREATE TABLE posts (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title       TEXT NOT NULL,
  body        TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'draft'
                CHECK (status IN ('draft', 'published', 'archived')),
  published_at TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_posts_user_id ON posts(user_id);         -- critical for FK joins
CREATE INDEX idx_posts_status ON posts(status) WHERE status = 'published'; -- partial index
```

## Common Data Type Choices
```sql
-- IDs
BIGSERIAL / BIGINT      -- surrogate integer key (fast joins, simple)
UUID                    -- globally unique, good for distributed systems / public-facing IDs

-- Text
TEXT                    -- unbounded (Postgres stores efficiently regardless)
VARCHAR(n)              -- only when you specifically need a length limit
CHAR(n)                 -- almost never — fixed-width, pads with spaces

-- Numbers
INTEGER / BIGINT        -- for counts, IDs
NUMERIC(precision, scale)  -- for money: NUMERIC(12, 2), never FLOAT for currency
FLOAT / DOUBLE PRECISION   -- scientific; acceptable rounding error

-- Time
TIMESTAMPTZ             -- always use this (stores UTC, displays in session timezone)
DATE                    -- date only (birthday, calendar)

-- Boolean
BOOLEAN                 -- TRUE/FALSE, never use 0/1 integers for booleans

-- JSON
JSONB                   -- binary JSON: indexable, faster to query (prefer over JSON)
JSON                    -- text JSON: preserves key order, slower

-- Arrays
TEXT[]                  -- array of text; good for tags, simple sets
INTEGER[]               -- use with ANY() operator

-- Enums
CREATE TYPE status AS ENUM ('draft', 'published', 'archived');  -- more rigid but faster than CHECK
```

# QUERYING

## CTEs and Window Functions
```sql
-- CTE: make complex queries readable
WITH
active_users AS (
  SELECT id, email, full_name
  FROM users
  WHERE deleted_at IS NULL
    AND created_at > NOW() - INTERVAL '30 days'
),
user_post_counts AS (
  SELECT user_id, COUNT(*) AS post_count
  FROM posts
  WHERE status = 'published'
  GROUP BY user_id
)
SELECT
  u.full_name,
  u.email,
  COALESCE(c.post_count, 0) AS posts_last_30_days
FROM active_users u
LEFT JOIN user_post_counts c ON c.user_id = u.id
ORDER BY posts_last_30_days DESC
LIMIT 20;

-- Window Functions: aggregates without collapsing rows
SELECT
  user_id,
  post_id,
  created_at,
  ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS post_rank,
  COUNT(*) OVER (PARTITION BY user_id) AS total_posts,
  SUM(view_count) OVER (PARTITION BY user_id ORDER BY created_at
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_views
FROM posts
WHERE status = 'published';

-- Get latest post per user (common pattern)
SELECT DISTINCT ON (user_id) user_id, title, created_at
FROM posts
ORDER BY user_id, created_at DESC;
```

## JSONB Queries
```sql
-- Store structured data in JSONB
CREATE TABLE events (
  id         BIGSERIAL PRIMARY KEY,
  user_id    BIGINT REFERENCES users(id),
  event_type TEXT NOT NULL,
  payload    JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index JSONB fields for fast lookups
CREATE INDEX idx_events_type ON events((payload->>'type'));
CREATE INDEX idx_events_payload ON events USING GIN(payload);  -- full JSONB search

-- Query JSONB
SELECT * FROM events
WHERE payload->>'action' = 'click'           -- text value
  AND (payload->>'amount')::NUMERIC > 100    -- cast and compare
  AND payload @> '{"source": "mobile"}';     -- containment (@> is GIN-indexed)

-- Update JSONB field
UPDATE events
SET payload = payload || '{"processed": true}'   -- merge object
WHERE id = 42;

SET payload = payload - 'temp_field'             -- remove key
```

# INDEXES

## When and What to Index
```sql
-- B-tree (default): equality, range, ORDER BY, most use cases
CREATE INDEX idx_posts_created ON posts(created_at DESC);

-- Partial: only index rows matching a condition (smaller, faster)
CREATE INDEX idx_active_users ON users(email) WHERE deleted_at IS NULL;

-- Composite: index multiple columns — column order matters
-- Query: WHERE status = 'published' AND created_at > X ORDER BY created_at
CREATE INDEX idx_posts_status_date ON posts(status, created_at DESC);
-- Rule: equality columns first, then range/order columns

-- GIN: for arrays, JSONB, full-text search
CREATE INDEX idx_post_tags ON posts USING GIN(tags);
CREATE INDEX idx_event_payload ON events USING GIN(payload);
CREATE INDEX idx_post_tsv ON posts USING GIN(to_tsvector('english', title || ' ' || body));

-- Covering index: include extra columns to avoid table lookup
CREATE INDEX idx_posts_user_cover ON posts(user_id)
  INCLUDE (title, created_at);   -- query can be satisfied from index alone

-- Find unused indexes (run after a while in production)
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY schemaname, tablename;

-- Find missing indexes (tables with many sequential scans)
SELECT relname, seq_scan, idx_scan
FROM pg_stat_user_tables
WHERE seq_scan > idx_scan
  AND n_live_tup > 10000
ORDER BY seq_scan DESC;
```

# QUERY PERFORMANCE

## EXPLAIN ANALYZE
```sql
-- Always use EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) for real performance data
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM posts
WHERE user_id = 42 AND status = 'published'
ORDER BY created_at DESC
LIMIT 10;

-- Key things to look for:
-- "Seq Scan" on large tables → needs an index
-- "Rows Removed by Filter: 50000" → index not selective enough
-- High "Actual Time" on a node → that operation is slow
-- "Buffers: hit=X read=Y" → read=Y means disk I/O (cold cache or missing index)
-- Nested Loop with many iterations → might need a Hash Join (planner bug or stale stats)

-- Update table statistics if planner makes bad choices
ANALYZE posts;
VACUUM ANALYZE posts;    -- also reclaims dead rows
```

## Common Performance Patterns
```sql
-- WRONG: function on indexed column disables index
SELECT * FROM users WHERE LOWER(email) = 'user@example.com';

-- RIGHT: use functional index or store normalized value
CREATE INDEX idx_users_email_lower ON users(LOWER(email));
-- OR: store email already lowercased, use CHECK constraint

-- WRONG: SELECT * fetches all columns (wide tables are expensive)
SELECT * FROM posts WHERE user_id = 42;

-- RIGHT: select only what you need
SELECT id, title, created_at FROM posts WHERE user_id = 42;

-- WRONG: N+1 query (one query per user)
-- In application: for each user → SELECT posts WHERE user_id = ?

-- RIGHT: one JOIN
SELECT u.id, u.full_name, COUNT(p.id) AS post_count
FROM users u
LEFT JOIN posts p ON p.user_id = u.id
GROUP BY u.id, u.full_name;

-- WRONG: counting all rows is slow on large tables
SELECT COUNT(*) FROM posts;

-- RIGHT: use estimates for display, exact count only when needed
SELECT reltuples::BIGINT FROM pg_class WHERE relname = 'posts';
```

# MIGRATIONS

## Safe Migration Practices
```sql
-- ADDING a column: always safe with a DEFAULT
ALTER TABLE posts ADD COLUMN view_count BIGINT NOT NULL DEFAULT 0;

-- ADDING a column (large table): set DEFAULT separately to avoid full table rewrite
ALTER TABLE posts ADD COLUMN view_count BIGINT;
UPDATE posts SET view_count = 0 WHERE view_count IS NULL;  -- in batches for huge tables
ALTER TABLE posts ALTER COLUMN view_count SET NOT NULL;
ALTER TABLE posts ALTER COLUMN view_count SET DEFAULT 0;

-- ADDING an index: use CONCURRENTLY to avoid table lock
CREATE INDEX CONCURRENTLY idx_posts_view_count ON posts(view_count DESC);

-- DROPPING a column: safe but leaves dead column (it's marked dropped, not removed)
ALTER TABLE posts DROP COLUMN old_column;  -- rarely needs CONCURRENTLY

-- RENAMING a column: NOT safe with live traffic — requires a transition period
-- Step 1: add new column, write to both
-- Step 2: backfill new column
-- Step 3: read from new column
-- Step 4: drop old column

-- NEVER do these without careful planning on live tables:
-- ALTER TABLE ... ALTER COLUMN ... TYPE (rewrites entire table)
-- ADD CONSTRAINT ... NOT VALID (then VALIDATE CONSTRAINT is OK though)
```

# QUICK WINS CHECKLIST
```
Schema:
[ ] Primary keys are BIGSERIAL or UUID (not SERIAL/INT — 2B limit)
[ ] Foreign keys have matching indexes on the referencing column
[ ] Timestamps are TIMESTAMPTZ (not TIMESTAMP without timezone)
[ ] NOT NULL constraints on columns that should never be null
[ ] CHECK constraints encode business rules at the DB level

Queries:
[ ] No SELECT * in production queries
[ ] No function calls on indexed columns in WHERE clauses
[ ] N+1 queries replaced with JOINs or subqueries
[ ] Pagination uses keyset (WHERE id > last_id) not OFFSET for large tables

Indexes:
[ ] Every FK column has an index
[ ] Frequently filtered/sorted columns have indexes
[ ] Indexes created CONCURRENTLY on production
[ ] Unused indexes identified and removed (bloat + write overhead)

Operations:
[ ] VACUUM ANALYZE runs regularly (autovacuum + manual for large updates)
[ ] Connection pooling via PgBouncer (or application pool)
[ ] Slow query log enabled (log_min_duration_statement = 200ms)
[ ] EXPLAIN ANALYZE run on all new queries in code review
[ ] Point-in-time recovery (PITR) configured and tested
```
