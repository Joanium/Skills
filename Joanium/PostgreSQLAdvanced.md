---
name: PostgreSQL Advanced Patterns
trigger: postgresql, postgres, pg, explain analyze, slow query postgres, postgres index, window function, CTE, postgres json, pg performance, full text search postgres, postgres partitioning, row level security, postgres advanced, vacuum, pg_stat
description: Write advanced PostgreSQL queries, optimize slow queries with EXPLAIN ANALYZE, design indexes, use window functions, CTEs, JSONB, full-text search, partitioning, and row-level security. Use this skill whenever the user needs to go beyond basic SQL in PostgreSQL — including query optimization, advanced query patterns, schema performance, or PostgreSQL-specific features.
---

# ROLE
You are a PostgreSQL expert. You write queries that are correct, fast, and idiomatic to Postgres. You read EXPLAIN ANALYZE output fluently and know which features to reach for.

# EXPLAIN ANALYZE — READ QUERY PLANS

```sql
-- Always EXPLAIN ANALYZE on slow queries
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) 
SELECT * FROM orders WHERE user_id = 123 AND status = 'pending';

-- Key things to look for:
-- Seq Scan       → missing index (bad for large tables)
-- Index Scan     → good — using an index
-- Nested Loop    → OK for small inner sets, bad if large
-- Hash Join      → good for large equijoins
-- Sort           → expensive if on-disk ("Sort Method: external merge")
-- Rows=1000 (actual rows=100000) → bad row estimate → stale stats → run ANALYZE
-- Buffers: hit=X read=Y → hit=cache, read=disk (want mostly hits)

-- Fix stale statistics
ANALYZE orders;                -- update stats for one table
ANALYZE;                       -- update all tables
```

# INDEXING PATTERNS

```sql
-- Partial index — index only the rows you query
CREATE INDEX idx_orders_pending ON orders(created_at DESC) 
WHERE status = 'pending';
-- Much smaller than full index, faster for: WHERE status='pending' ORDER BY created_at DESC

-- Composite index — order matters: equality first, range last
-- For query: WHERE user_id = ? AND created_at > ?
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at DESC);

-- Covering index — index contains all needed columns (avoids table lookup)
CREATE INDEX idx_orders_covering ON orders(user_id, status) 
INCLUDE (total_cents, created_at);
-- Query: SELECT total_cents, created_at FROM orders WHERE user_id=? AND status=?
-- → Index only scan, never touches the table

-- Expression index
CREATE INDEX idx_users_lower_email ON users(lower(email));
-- Now this uses the index: WHERE lower(email) = lower($1)

-- GIN index for JSONB and full-text search
CREATE INDEX idx_products_attrs ON products USING GIN (attributes);
CREATE INDEX idx_articles_fts ON articles USING GIN (to_tsvector('english', body));

-- Find unused indexes (waste of write overhead)
SELECT indexname, idx_scan 
FROM pg_stat_user_indexes 
WHERE idx_scan = 0 AND schemaname = 'public';
```

# WINDOW FUNCTIONS

```sql
-- Running total
SELECT 
  order_date,
  total_cents,
  SUM(total_cents) OVER (ORDER BY order_date) AS running_total
FROM orders;

-- Rank within group
SELECT 
  user_id,
  product_id,
  quantity,
  RANK() OVER (PARTITION BY user_id ORDER BY quantity DESC) AS rank_by_user
FROM order_items;

-- Previous/next row values
SELECT 
  id,
  created_at,
  status,
  LAG(status) OVER (PARTITION BY user_id ORDER BY created_at) AS previous_status,
  LEAD(status) OVER (PARTITION BY user_id ORDER BY created_at) AS next_status
FROM orders;

-- Percentile / top N per group
SELECT * FROM (
  SELECT 
    user_id, order_id, total_cents,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY total_cents DESC) AS rn
  FROM orders
) ranked
WHERE rn <= 3;  -- top 3 orders per user

-- Moving average
SELECT 
  date,
  revenue,
  AVG(revenue) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS moving_avg_7d
FROM daily_revenue;
```

# CTEs — WITH CLAUSE

```sql
-- Basic CTE (readable query decomposition)
WITH active_users AS (
  SELECT id, email FROM users WHERE is_active = true AND deleted_at IS NULL
),
recent_orders AS (
  SELECT user_id, COUNT(*) AS order_count
  FROM orders
  WHERE created_at > NOW() - INTERVAL '30 days'
  GROUP BY user_id
)
SELECT 
  u.email,
  COALESCE(o.order_count, 0) AS orders_last_30d
FROM active_users u
LEFT JOIN recent_orders o ON o.user_id = u.id
ORDER BY orders_last_30d DESC;

-- Recursive CTE — tree/hierarchy traversal
WITH RECURSIVE category_tree AS (
  -- Base case: root categories
  SELECT id, name, parent_id, 0 AS depth, name::TEXT AS path
  FROM categories WHERE parent_id IS NULL
  
  UNION ALL
  
  -- Recursive case: children
  SELECT c.id, c.name, c.parent_id, ct.depth + 1, 
         ct.path || ' > ' || c.name
  FROM categories c
  JOIN category_tree ct ON ct.id = c.parent_id
)
SELECT * FROM category_tree ORDER BY path;
```

# JSONB — QUERYING AND INDEXING

```sql
-- JSONB column with sample data: {"brand": "Nike", "size": "M", "tags": ["sport", "outdoor"]}

-- Query operators
SELECT * FROM products WHERE attributes->>'brand' = 'Nike';
SELECT * FROM products WHERE attributes @> '{"brand": "Nike"}';  -- containment
SELECT * FROM products WHERE attributes ? 'brand';                -- key exists
SELECT * FROM products WHERE attributes->'tags' ? 'sport';        -- array contains value

-- Build JSON in query
SELECT 
  id,
  jsonb_build_object(
    'name', name,
    'brand', attributes->>'brand',
    'tags', attributes->'tags'
  ) AS product_json
FROM products;

-- Update specific JSONB key (no full replacement)
UPDATE products 
SET attributes = attributes || '{"in_stock": false}'::jsonb
WHERE id = 123;

-- Remove a key
UPDATE products 
SET attributes = attributes - 'legacy_field'
WHERE attributes ? 'legacy_field';

-- Expand JSONB array into rows
SELECT id, jsonb_array_elements_text(attributes->'tags') AS tag
FROM products;

-- Index specific JSONB path
CREATE INDEX idx_product_brand ON products ((attributes->>'brand'));
```

# FULL-TEXT SEARCH

```sql
-- Setup
ALTER TABLE articles ADD COLUMN search_vector TSVECTOR 
  GENERATED ALWAYS AS (
    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(body, '')), 'B')
  ) STORED;

CREATE INDEX idx_articles_search ON articles USING GIN (search_vector);

-- Search with ranking
SELECT 
  id, title,
  ts_rank(search_vector, query) AS rank,
  ts_headline('english', body, query, 'MaxWords=50, MinWords=20') AS excerpt
FROM articles, to_tsquery('english', 'postgresql & performance') AS query
WHERE search_vector @@ query
ORDER BY rank DESC
LIMIT 20;

-- OR query
to_tsquery('english', 'postgresql | mysql')

-- Phrase search
phraseto_tsquery('english', 'database performance')
```

# ROW-LEVEL SECURITY (RLS)

```sql
-- Enable RLS on a table
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy: users can only see their own documents
CREATE POLICY user_isolation ON documents
  USING (user_id = current_setting('app.current_user_id')::uuid);

-- Policy: org members can see org documents
CREATE POLICY org_isolation ON documents
  USING (
    org_id IN (
      SELECT org_id FROM org_members 
      WHERE user_id = current_setting('app.current_user_id')::uuid
    )
  );

-- Set the user context in your app before queries
-- Node.js example:
-- await db.query("SET LOCAL app.current_user_id = $1", [userId]);

-- Bypass RLS for admin operations
ALTER TABLE documents FORCE ROW LEVEL SECURITY;
-- Use a superuser or BYPASSRLS role for admin queries
```

# TABLE PARTITIONING

```sql
-- Range partitioning by date (good for time-series, logs)
CREATE TABLE events (
  id BIGINT GENERATED ALWAYS AS IDENTITY,
  user_id UUID NOT NULL,
  event_type VARCHAR(50) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  payload JSONB
) PARTITION BY RANGE (created_at);

-- Create partitions (automate with pg_partman extension)
CREATE TABLE events_2024_q1 PARTITION OF events
  FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE events_2024_q2 PARTITION OF events
  FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

-- Each partition can have its own indexes
CREATE INDEX ON events_2024_q1 (user_id, created_at DESC);
```

# USEFUL SYSTEM QUERIES

```sql
-- Find slow queries
SELECT query, mean_exec_time, calls, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC LIMIT 20;

-- Find missing indexes (sequential scans on large tables)
SELECT relname, seq_scan, idx_scan, n_live_tup
FROM pg_stat_user_tables
WHERE seq_scan > idx_scan AND n_live_tup > 10000
ORDER BY seq_scan DESC;

-- Table sizes
SELECT 
  relname AS table,
  pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
  pg_size_pretty(pg_relation_size(relid)) AS table_size,
  pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) AS index_size
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- Lock monitoring
SELECT pid, query, state, wait_event_type, wait_event, query_start
FROM pg_stat_activity
WHERE wait_event IS NOT NULL AND state != 'idle';

-- Bloat check (when to VACUUM)
SELECT schemaname, tablename, n_dead_tup, n_live_tup,
  round(n_dead_tup::numeric / nullif(n_live_tup, 0) * 100, 2) AS dead_pct
FROM pg_stat_user_tables
WHERE n_live_tup > 1000
ORDER BY dead_pct DESC NULLS LAST;
```
