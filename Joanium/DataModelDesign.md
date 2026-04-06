---
name: Domain Modeling & Data Model Design
trigger: data model, domain model, entity design, schema design, model my domain, data modeling, entity relationship, database schema, model relationships, domain driven, design my schema, model design, data structure design, domain entities
description: Design clear, extensible data models by identifying domain entities, relationships, and constraints before writing a single table. Use when starting a new feature area, designing a schema from scratch, or untangling an overgrown domain model.
---

A good data model is the foundation everything else is built on. A bad data model is technical debt that never stops compounding — it shapes every query, every API, every migration for years. Take the time to think it through before you type `CREATE TABLE`.

## Modeling Process: Think Before You Schema

The order matters:

```
1. Understand the domain (business language first)
2. Identify entities and relationships
3. Define invariants and constraints
4. Sketch the ERD
5. Validate against real use cases
6. THEN write SQL
```

Most schema problems come from skipping steps 1-4.

## Step 1: Domain Discovery — Speak the Business Language

Before modeling, interview the domain experts (product managers, business stakeholders):

```
Questions to ask:
- "What are the core 'things' in this system?" → Entities
- "What can a [thing] do?" → Behaviors / state transitions
- "What makes a [thing] valid?" → Invariants / constraints
- "What can a [thing] belong to?" → Relationships
- "What do you call it when X does Y?" → Ubiquitous language

Write down the exact words they use. Those become your table and column names.

Example discoveries from an e-commerce domain interview:
"A customer places an order"
"An order contains one or more line items"
"A line item has a product and a quantity"
"An order can be placed, confirmed, shipped, or delivered"
"A customer can have multiple shipping addresses"
"A product can be in stock or out of stock"
"A discount code can be applied to an order, not a line item"
```

## Step 2: Identify Entities and Relationships

From the domain language, extract:

```
Entities (nouns) → Tables
- Customer, Order, LineItem, Product, Address, DiscountCode

Relationships → Foreign keys / junction tables
- Customer places Order             → orders.customer_id
- Order contains LineItems          → line_items.order_id
- LineItem references Product       → line_items.product_id
- Customer has Addresses            → addresses.customer_id (or junction)
- Order applies DiscountCode        → orders.discount_code_id (nullable)

Attributes (adjectives/values) → Columns
- Customer: email, name, created_at
- Order: status, total_amount, currency, placed_at
- Product: name, sku, price_cents, inventory_count
```

## Step 3: Relationship Cardinality

Get this wrong and you'll be migrating data for months.

```
One-to-One (1:1)
- User ←→ UserProfile
- Pattern: FK on the dependent table
  users: id, email
  user_profiles: id, user_id UNIQUE, bio, avatar_url

One-to-Many (1:N) — most common
- Customer → Orders (one customer, many orders)
- Pattern: FK on the "many" side
  orders: id, customer_id, status, total

Many-to-Many (M:N)
- Products ←→ Tags (a product has many tags; a tag has many products)
- Pattern: Junction/pivot table
  product_tags: product_id, tag_id, PRIMARY KEY (product_id, tag_id)

One-to-Many-to-Many (hierarchical/tree)
- Categories with subcategories
- Pattern: Adjacency list or nested sets
  categories: id, name, parent_id REFERENCES categories(id)
```

## Step 4: Invariants and Constraints — Encode the Rules

The database should make illegal states impossible. Use constraints, not just application code:

```sql
-- Every order must belong to a customer
orders.customer_id NOT NULL REFERENCES customers(id)

-- Order total must be non-negative
orders.total_amount_cents >= 0

-- Valid order statuses only
orders.status IN ('draft', 'placed', 'confirmed', 'shipped', 'delivered', 'cancelled')

-- Line item quantity must be positive
line_items.quantity > 0

-- Price at time of purchase is immutable (snapshot)
line_items.unit_price_cents NOT NULL -- stored at order time, not calculated

-- Email must be unique
customers.email UNIQUE NOT NULL

-- A customer can only apply a discount code once
UNIQUE INDEX (customer_id, discount_code_id) on redemptions table

-- Check constraint example in PostgreSQL
ALTER TABLE orders ADD CONSTRAINT chk_positive_total 
  CHECK (total_amount_cents >= 0);
```

**The golden rule:** If it's a business rule, encode it in the database. Application bugs happen. Database constraints are the last line of defense.

## Common Data Modeling Patterns

### Polymorphic associations (use with caution)
```sql
-- Pattern: One table of comments for any entity type
-- Works: Simple to add new entity types
-- Problem: No FK constraint possible — can have orphaned records

comments:
  id, body, created_at,
  commentable_type VARCHAR ('post', 'product', 'order'),
  commentable_id   BIGINT

-- Better alternative: Separate tables per type
post_comments:    id, post_id REFERENCES posts(id), body
product_comments: id, product_id REFERENCES products(id), body

-- Best alternative for many types: use a universal ID (UUID) approach
```

### Soft deletes (deleted_at pattern)
```sql
-- Add to any table that needs logical deletion
ALTER TABLE products ADD COLUMN deleted_at TIMESTAMPTZ;

-- Query: always filter out deleted
SELECT * FROM products WHERE deleted_at IS NULL;

-- Soft delete
UPDATE products SET deleted_at = NOW() WHERE id = $1;

-- Partial index for performance
CREATE INDEX idx_products_active ON products(id) WHERE deleted_at IS NULL;

-- Caution: soft deletes complicate UNIQUE constraints
-- A customer might "delete" their account and re-register with the same email
-- Handle with: UNIQUE (email) WHERE deleted_at IS NULL
```

### Status state machine
```sql
-- Store status history alongside current status
CREATE TABLE order_status_history (
  id         BIGSERIAL PRIMARY KEY,
  order_id   BIGINT REFERENCES orders(id),
  status     TEXT NOT NULL,
  reason     TEXT,
  created_by BIGINT REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Valid transitions (enforced in application, documented here)
-- draft → placed
-- placed → confirmed | cancelled
-- confirmed → shipped | cancelled
-- shipped → delivered
-- Any state → cancelled (with reason)
```

### Storing money
```sql
-- NEVER store money as FLOAT or DOUBLE (floating point errors)
-- Use integer (cents/pence) or NUMERIC with fixed precision

-- Good: store in cents
price_cents INTEGER NOT NULL  -- 2000 = $20.00
currency    CHAR(3) NOT NULL  -- 'USD', 'EUR', 'GBP'

-- Good: PostgreSQL NUMERIC
price NUMERIC(12, 2) NOT NULL  -- up to 9,999,999,999.99

-- Always store currency alongside amount
-- Always store the price at time of transaction (snapshot)
-- line_items.unit_price_cents — the price when the order was placed
-- NOT calculated from products.price_cents (which may change)
```

### JSONB for flexible attributes
```sql
-- Use for: metadata, configuration, extensible attributes
-- Avoid for: anything you query or filter on (use columns instead)

CREATE TABLE products (
  id       BIGSERIAL PRIMARY KEY,
  name     TEXT NOT NULL,
  sku      TEXT UNIQUE NOT NULL,
  price_cents INTEGER NOT NULL,
  
  -- Flexible attributes that differ by product type
  attributes JSONB DEFAULT '{}'
  -- Example: {"color": "red", "size": "L", "material": "cotton"}
  -- Example: {"weight_kg": 0.5, "dimensions": {"w": 10, "h": 20, "d": 5}}
);

-- Index on a specific JSONB key for performance
CREATE INDEX idx_products_color ON products((attributes->>'color'));

-- GIN index for full JSONB search
CREATE INDEX idx_products_attrs ON products USING GIN(attributes);

-- Query:
SELECT * FROM products WHERE attributes->>'color' = 'red';
SELECT * FROM products WHERE attributes @> '{"size": "L"}';
```

## ERD Review Checklist

```
Entities:
☐ Every entity has a surrogate primary key (id)?
☐ Every entity has created_at and updated_at timestamps?
☐ Every entity name is a noun from the business domain?

Relationships:
☐ Every FK has NOT NULL where the relationship is required?
☐ Every FK has an index (unindexed FKs cause slow joins)?
☐ M:N relationships have a junction table with a composite PK?
☐ Circular dependencies are intentional and documented?

Constraints:
☐ Business rules are encoded as DB constraints, not just app logic?
☐ ENUM columns have a CHECK constraint for valid values?
☐ Unique constraints reflect real-world uniqueness rules?
☐ Money columns are INTEGER (cents) or NUMERIC — never FLOAT?
☐ Nullable columns are intentionally nullable (not just default)?

Scale:
☐ Large tables have appropriate indexes on query patterns?
☐ Time-series or log tables have a partition strategy?
☐ JSONB is used only for unstructured/flexible data?
☐ N+1 access patterns identified and mitigated in design?

Validation:
☐ Modeled 5 real user scenarios against the schema?
☐ Checked that each scenario results in a clean, efficient query?
☐ Verified schema handles edge cases (nulls, empty collections, duplicates)?
```

## Data Model Documentation Template

```markdown
## Domain: [Name] — Data Model

**Owner:** [Team]
**Last updated:** [Date]

### Entities Overview

| Entity | Table | Description |
|--------|-------|-------------|
| Customer | customers | End user who places orders |
| Order | orders | A purchase transaction |
| Line Item | line_items | A single product within an order |
| Product | products | A purchasable item |

### Key Design Decisions

**Decision 1: Price snapshot in line_items**
Line items store unit_price_cents at the time of purchase.
This is intentional — products can change price; historical orders must not.

**Decision 2: Soft delete for products**
Products are soft-deleted (deleted_at) because order history must reference them.
Hard-deleting a product would break historical order displays.

**Decision 3: Status history table**
Order status changes are logged in order_status_history for audit purposes.
The current status is denormalized onto orders for query performance.

### ERD
[Embed or link to diagram]

### Index Strategy
| Index | Table | Columns | Reason |
|-------|-------|---------|--------|
| idx_orders_customer | orders | customer_id | FK join, orders by customer |
| idx_orders_status | orders | status, created_at | Dashboard queries |
| idx_line_items_order | line_items | order_id | Always fetched by order |
```
