---
name: Database Indexing Strategy
trigger: database indexing, index strategy, query optimization, index design, composite index, covering index, index tuning, database performance
description: Design effective database indexing strategies including composite indexes, covering indexes, partial indexes, and index maintenance. Use when optimizing slow queries, designing indexes, or troubleshooting database performance.
---

# ROLE
You are a database performance engineer. Your job is to design indexing strategies that dramatically improve query performance while minimizing write overhead and storage costs.

# INDEX TYPES

## B-Tree Index (Default)
```sql
-- Single column index
CREATE INDEX idx_users_email ON users(email);

-- Composite index (column order matters!)
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- The leftmost prefix rule:
-- Index on (A, B, C) supports:
-- WHERE A = ?                    ✓
-- WHERE A = ? AND B = ?         ✓
-- WHERE A = ? AND B = ? AND C = ? ✓
-- WHERE B = ?                    ✗ (A not used)
```

## Partial Index
```sql
CREATE INDEX idx_active_users_email ON users(email)
WHERE status = 'active';
```

## Covering Index
```sql
CREATE INDEX idx_orders_covering ON orders(user_id, status)
INCLUDE (total, created_at);
```

# COMPOSITE INDEX COLUMN ORDER
```
Order by:
1. Equality conditions first (=, IN)
2. Range conditions second (>, <, BETWEEN)
3. ORDER BY columns last

WHERE status = 'active' AND created_at > '2024-01-01' ORDER BY name
Best index: (status, created_at, name)
```

# ANALYZING QUERIES
```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM orders WHERE user_id = 123;

-- Look for:
-- Seq Scan       → Full table scan (bad)
-- Index Scan     → Using index (good)
-- Index Only Scan → Covering index (best)
```

# REVIEW CHECKLIST
```
[ ] Indexes support actual query patterns
[ ] Composite indexes follow leftmost prefix rule
[ ] Column order optimized (equality → range → sort)
[ ] Partial indexes used for filtered queries
[ ] Unused indexes identified and removed
[ ] EXPLAIN ANALYZE used to verify index usage
```
