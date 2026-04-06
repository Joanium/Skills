---
name: Database Design
trigger: design a database, schema design, data model, database schema, table structure, relationships, normalization, foreign key, indexes, ERD, postgres schema, mongodb schema, relational model
description: Design clean, performant, evolvable database schemas. Covers relational modeling, normalization, naming conventions, relationships, indexes, soft deletes, auditing, and common modeling patterns.
---

# ROLE
You are a database architect. Your job is to design schemas that accurately model the domain, perform well under load, evolve cleanly over time, and protect data integrity. Schema mistakes are expensive — they compound with every row written.

# CORE PRINCIPLES
```
MODEL THE DOMAIN FIRST — understand the real-world concepts before touching SQL
NORMALIZE TO REMOVE REDUNDANCY — every fact stored exactly once
DENORMALIZE DELIBERATELY — only for read performance, with documented reasons
ENFORCE INTEGRITY AT THE DB LEVEL — not just in application code
DESIGN FOR EVOLUTION — you will add columns; make it non-destructive
NAMES ARE CONTRACTS — rename nothing without a migration plan
```

# NAMING CONVENTIONS
```sql
-- Tables: plural, snake_case
users, orders, order_items, product_variants, email_templates

-- Columns: snake_case
user_id, created_at, is_active, first_name, stripe_customer_id

-- Primary keys: always 'id'
id  (not user_id on the users table — that's confusing)

-- Foreign keys: {referenced_table_singular}_id
order_id, user_id, product_id, created_by_user_id

-- Boolean columns: is_ or has_ prefix
is_active, is_verified, has_paid, is_deleted

-- Timestamps: created_at, updated_at, deleted_at (for soft deletes)

-- Junction/pivot tables: both table names, alphabetical order
order_products, role_users, tag_posts

-- Indexes: idx_{table}_{columns}
idx_users_email
idx_orders_user_id_created_at
idx_products_category_id_is_active
```

# COLUMN TYPES — CHOOSE PRECISELY
```sql
-- IDs: use UUIDs (distributed safe, no cardinality leakage)
id UUID DEFAULT gen_random_uuid() PRIMARY KEY
-- Or: ULID for sortable UUIDs (use pgulid extension)
-- Only use BIGSERIAL if you never expose the ID externally and don't need distributed generation

-- Strings: VARCHAR over TEXT for constrained fields
email       VARCHAR(254)  -- email max is 254 chars
name        VARCHAR(255)
country_code VARCHAR(2)   -- always constrain what you know
notes       TEXT          -- genuinely unbounded text
url         VARCHAR(2048)

-- Numbers
price       NUMERIC(12, 2)  -- NEVER float for money — use NUMERIC
quantity    INTEGER
percentage  NUMERIC(5, 2)   -- 100.00 max
latitude    NUMERIC(9, 6)
longitude   NUMERIC(9, 6)

-- Timestamps: always WITH TIME ZONE
created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
deleted_at  TIMESTAMPTZ  -- NULL = not deleted

-- Enum values: use CHECK constraint or a lookup table
status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'active', 'cancelled'))
-- For extensible enums: use a reference/lookup table instead

-- JSON: use JSONB (binary, indexed) not JSON (text)
metadata    JSONB
```

# NORMALIZATION

## The Three Forms You Need to Know
```sql
-- 1NF: Each column holds one value (no arrays, no comma-separated lists)
WRONG: tags VARCHAR  -- "api,mobile,backend" stored in one field
RIGHT: tags table with tag_id, name; post_tags junction table

-- 2NF: Non-key columns depend on the WHOLE primary key
WRONG (composite PK): order_items(order_id, product_id, product_name)
  -- product_name depends on product_id alone, not (order_id, product_id)
RIGHT: store product_name in products table; join when needed

-- 3NF: No transitive dependencies (A→B→C: B shouldn't depend on non-key A)
WRONG: users(id, zip_code, city, state)
  -- city and state depend on zip_code, not on user id
RIGHT: zip_codes(zip_code, city, state); users(id, zip_code)
```

## When to Denormalize
```sql
-- Acceptable denormalization with documented reasoning:

-- 1. Snapshot historical values — prices change, orders shouldn't
order_items (
  order_id    UUID REFERENCES orders,
  product_id  UUID REFERENCES products,
  unit_price  NUMERIC(12,2) NOT NULL,  -- DENORM: snapshot price at time of purchase
  quantity    INTEGER NOT NULL
)

-- 2. Cached aggregates for hot read paths
users (
  id              UUID PRIMARY KEY,
  order_count     INTEGER NOT NULL DEFAULT 0,  -- DENORM: cached, updated via trigger
  lifetime_value  NUMERIC(12,2) NOT NULL DEFAULT 0
)

-- 3. Search/filter optimization
products (
  id              UUID PRIMARY KEY,
  category_id     UUID REFERENCES categories,
  category_name   VARCHAR(100),  -- DENORM: avoids JOIN on every product list query
  CONSTRAINT fk_category CHECK (...)
)
```

# RELATIONSHIPS

## One-to-Many
```sql
-- The "many" side holds the foreign key
CREATE TABLE orders (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  -- ON DELETE RESTRICT: prevent deleting users who have orders (safest default)
  -- ON DELETE CASCADE:  delete orders when user deleted (careful)
  -- ON DELETE SET NULL: set user_id = NULL when user deleted (requires nullable FK)
  status     VARCHAR(20) NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_orders_user_id ON orders(user_id);  -- always index FKs
```

## Many-to-Many
```sql
-- Always via a junction table
CREATE TABLE product_tags (
  product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  tag_id     UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (product_id, tag_id)  -- composite PK = no duplicate pairs
);
CREATE INDEX idx_product_tags_tag_id ON product_tags(tag_id);  -- index both directions
```

## Self-Referential (Hierarchy / Tree)
```sql
-- Categories, org charts, comment threads
CREATE TABLE categories (
  id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name      VARCHAR(255) NOT NULL,
  parent_id UUID REFERENCES categories(id),  -- NULL = root category
  path      LTREE  -- pg ltree extension: efficient ancestor/descendant queries
);

-- For deep trees, use Materialized Path or Nested Sets instead of Adjacency List
-- ltree path: 'root.electronics.phones.smartphones'
CREATE INDEX idx_categories_path ON categories USING GIST(path);
```

## Polymorphic Associations
```sql
-- OPTION 1: Separate tables per type (preferred for type safety)
CREATE TABLE user_comments    (id UUID PK, user_id UUID, body TEXT, post_id UUID REFERENCES posts);
CREATE TABLE product_comments (id UUID PK, user_id UUID, body TEXT, product_id UUID REFERENCES products);

-- OPTION 2: Generic with type column (simpler, but loses FK enforcement)
CREATE TABLE comments (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id),
  body            TEXT NOT NULL,
  commentable_type VARCHAR(50) NOT NULL,  -- 'post', 'product', 'order'
  commentable_id   UUID NOT NULL,         -- no FK constraint possible here
  INDEX idx_comments_commentable (commentable_type, commentable_id)
);
```

# INDEXES — WHEN AND WHAT
```sql
-- ALWAYS index:
-- 1. Foreign key columns (for JOIN and DELETE performance)
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- 2. Columns used in WHERE clauses with high cardinality
CREATE INDEX idx_users_email ON users(email);  -- email is unique per user

-- 3. Columns used in ORDER BY on large tables
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);

-- COMPOSITE INDEXES: column order matters
-- For WHERE user_id = ? AND created_at > ?:
CREATE INDEX idx_orders_user_created ON orders(user_id, created_at DESC);
-- user_id first (equality), created_at second (range)

-- PARTIAL INDEXES: index only the subset you query
CREATE INDEX idx_orders_pending ON orders(user_id, created_at)
  WHERE status = 'pending';  -- much smaller, much faster for pending order queries

-- UNIQUE INDEXES: enforce uniqueness + fast lookup
CREATE UNIQUE INDEX idx_users_email_unique ON users(email);
CREATE UNIQUE INDEX idx_users_google_id ON users(google_id) WHERE google_id IS NOT NULL;

-- NEVER index:
-- Low cardinality columns (boolean, status with 3 values) — unless partial
-- Columns never used in WHERE/JOIN/ORDER BY
-- Very frequently updated columns (index maintenance overhead)
```

# SOFT DELETES
```sql
-- Add deleted_at to any table that needs audit trail or recovery
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMPTZ;

-- Query active records: always filter in app OR use a view
CREATE VIEW active_users AS
  SELECT * FROM users WHERE deleted_at IS NULL;

-- Partial index for active-only queries (ignores deleted rows)
CREATE INDEX idx_users_active_email ON users(email)
  WHERE deleted_at IS NULL;

-- Unique constraint that ignores deleted rows
CREATE UNIQUE INDEX idx_users_email_active ON users(email)
  WHERE deleted_at IS NULL;
-- Allows: reuse email after soft-delete (same email can re-register)
```

# AUDIT TRAIL
```sql
-- Option 1: created_by / updated_by columns
CREATE TABLE products (
  id              UUID PRIMARY KEY,
  name            VARCHAR(255) NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by      UUID REFERENCES users(id),
  updated_by      UUID REFERENCES users(id)
);

-- Option 2: Dedicated audit log table (full history)
CREATE TABLE audit_log (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  table_name  VARCHAR(50) NOT NULL,
  record_id   UUID NOT NULL,
  action      VARCHAR(10) NOT NULL,  -- INSERT, UPDATE, DELETE
  old_data    JSONB,
  new_data    JSONB,
  user_id     UUID REFERENCES users(id),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id);

-- Trigger to auto-populate audit log
CREATE OR REPLACE FUNCTION audit_trigger_fn() RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO audit_log(table_name, record_id, action, old_data, new_data)
  VALUES (TG_TABLE_NAME, COALESCE(NEW.id, OLD.id), TG_OP,
    CASE WHEN TG_OP != 'INSERT' THEN row_to_json(OLD) END,
    CASE WHEN TG_OP != 'DELETE' THEN row_to_json(NEW) END);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

# COMMON MODELING PATTERNS

## Money / Pricing
```sql
-- ALWAYS store in the smallest currency unit (cents, not dollars)
-- NEVER use FLOAT for money
amount_cents  INTEGER NOT NULL  -- 1000 = $10.00
currency      VARCHAR(3) NOT NULL DEFAULT 'USD'  -- ISO 4217

-- Or: NUMERIC with explicit precision
amount        NUMERIC(12, 2) NOT NULL  -- max 9,999,999,999.99
```

## Status Machines
```sql
-- Document valid transitions in a comment
-- status: pending → processing → completed
--         pending → cancelled
--         processing → failed → pending (retry)
status VARCHAR(20) NOT NULL DEFAULT 'pending'
  CHECK (status IN ('pending', 'processing', 'completed', 'cancelled', 'failed'))
```

## Versioning / History
```sql
-- Immutable history: never update, only insert new versions
CREATE TABLE product_prices (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id  UUID NOT NULL REFERENCES products(id),
  price_cents INTEGER NOT NULL,
  valid_from  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  valid_until TIMESTAMPTZ,  -- NULL = currently active
  created_by  UUID REFERENCES users(id)
);
-- Get current price: WHERE valid_until IS NULL (or valid_until > NOW())
```

# MIGRATION SAFETY CHECKLIST
```sql
-- Safe operations (non-blocking on Postgres):
ADD COLUMN nullable                  -- instant
ADD COLUMN with DEFAULT (PG 11+)     -- instant (no table rewrite)
CREATE INDEX CONCURRENTLY            -- doesn't lock
DROP COLUMN                          -- instant (logical remove)
ADD CONSTRAINT NOT VALID             -- doesn't validate existing rows

-- Dangerous operations (lock the table):
ADD COLUMN NOT NULL without DEFAULT  -- rewrites entire table
DROP NOT NULL                        -- safe actually
ADD COLUMN with volatile DEFAULT     -- rewrites in PG < 11
RENAME COLUMN/TABLE                  -- breaks dependent code instantly
CHANGE COLUMN TYPE                   -- rewrites table

-- Safe NOT NULL migration pattern:
-- 1. Add nullable
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
-- 2. Backfill in batches (don't do all at once)
UPDATE users SET phone = '' WHERE phone IS NULL AND id > last_processed_id LIMIT 10000;
-- 3. Add NOT NULL after backfill complete
ALTER TABLE users ALTER COLUMN phone SET NOT NULL;
```
