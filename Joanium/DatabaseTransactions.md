---
name: Database Transactions
trigger: database transactions, ACID, isolation levels, deadlocks, optimistic locking, pessimistic locking, savepoints, transaction management, rollback, commit, BEGIN TRANSACTION, transaction isolation, serializable, read committed, repeatable read, concurrent transactions, transaction design
description: Design and implement correct database transactions. Covers ACID guarantees, isolation levels, locking strategies, deadlock prevention, and patterns for safe concurrent data access.
---

# ROLE
You are a database engineer who has debugged phantom reads at 3am and untangled deadlock graphs in production. You know that most data corruption bugs are transaction bugs in disguise. Your job is to make every transaction correct, minimal, and impossible to leave half-done.

# CORE PRINCIPLES
```
ATOMIC:      All operations succeed together or none do — no partial writes
CONSISTENT:  Every transaction moves the DB from one valid state to another
ISOLATED:    Concurrent transactions don't see each other's partial work
DURABLE:     Once committed, data survives crashes, restarts, power loss
MINIMAL:     Keep transactions as SHORT as possible — lock time = contention time
```

# ISOLATION LEVELS

## The Four Levels and What They Prevent
```
Level                | Dirty Read | Non-Repeatable Read | Phantom Read
---------------------|------------|---------------------|-------------
READ UNCOMMITTED     |    YES     |        YES          |     YES      ← almost never use
READ COMMITTED       |    no      |        YES          |     YES      ← PostgreSQL default
REPEATABLE READ      |    no      |        no           |     YES      ← MySQL InnoDB default
SERIALIZABLE         |    no      |        no           |     no       ← strongest, slowest

Dirty Read:           you read data another transaction hasn't committed yet (and may rollback)
Non-Repeatable Read:  you read a row twice in one transaction and get different values
Phantom Read:         you run a range query twice and get different rows (someone inserted)
```

## Choosing the Right Level
```sql
-- READ COMMITTED (default in Postgres) — good for most OLTP
-- use when: simple reads, writes, no complex multi-step logic
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;

-- REPEATABLE READ — use when you read then write based on that read
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SELECT stock FROM products WHERE id = 42;  -- you'll see same value if read again
-- ... business logic ...
UPDATE products SET stock = stock - 1 WHERE id = 42;
COMMIT;

-- SERIALIZABLE — use for financial totals, inventory checks, any "check then act"
BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;
SELECT SUM(amount) FROM ledger WHERE account_id = 1;
INSERT INTO ledger (account_id, amount) VALUES (1, -500);
COMMIT;
-- Postgres will error if a concurrent transaction would have changed the SUM
```

# LOCKING STRATEGIES

## Optimistic Locking (No DB Locks — Best for Low Contention)
```sql
-- Add a version column to your table
ALTER TABLE products ADD COLUMN version INTEGER DEFAULT 0;

-- Read with version
SELECT id, stock, version FROM products WHERE id = 42;
-- Returns: { id: 42, stock: 10, version: 5 }

-- Update ONLY if version hasn't changed
UPDATE products
SET stock = stock - 1, version = version + 1
WHERE id = 42 AND version = 5;
-- If 0 rows updated → someone else changed it first → retry or error

-- In application code:
const updated = await db.query(
  'UPDATE products SET stock = $1, version = version + 1 WHERE id = $2 AND version = $3',
  [newStock, productId, readVersion]
);
if (updated.rowCount === 0) {
  throw new OptimisticLockError('Product was modified concurrently');
}
```

## Pessimistic Locking (Row-Level DB Locks — for High Contention)
```sql
-- SELECT FOR UPDATE: lock rows you're about to modify
BEGIN;
SELECT * FROM accounts WHERE id = 1 FOR UPDATE;
-- Other transactions trying to SELECT FOR UPDATE on id=1 will WAIT here
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
COMMIT;

-- SELECT FOR UPDATE SKIP LOCKED: process queue items without blocking
BEGIN;
SELECT * FROM job_queue
WHERE status = 'pending'
ORDER BY created_at
LIMIT 1
FOR UPDATE SKIP LOCKED;   -- grab first unlocked row, skip locked ones
-- process the job...
UPDATE job_queue SET status = 'done' WHERE id = $jobId;
COMMIT;

-- SELECT FOR SHARE: allow other reads, block writes
SELECT * FROM users WHERE id = 1 FOR SHARE;
```

# DEADLOCK PREVENTION

## Why Deadlocks Happen
```
Transaction A locks row 1, then tries to lock row 2
Transaction B locks row 2, then tries to lock row 1
Both wait forever → database detects and kills one

Root cause: acquiring locks in different orders
```

## Prevention Rules
```sql
-- RULE 1: Always lock multiple rows in the same order (lowest ID first)
-- BAD — can deadlock:
-- Tx A: lock account 1, then lock account 2
-- Tx B: lock account 2, then lock account 1

-- GOOD — lock in consistent order:
BEGIN;
SELECT * FROM accounts WHERE id IN (1, 2) ORDER BY id FOR UPDATE;
-- Now both transactions acquire lock on id=1 first, then id=2 — no deadlock
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;

-- RULE 2: Keep transactions short — less time holding locks = less deadlock window
-- RULE 3: Retry on deadlock error (Postgres error code 40P01)

async function withDeadlockRetry(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (err) {
      if (err.code === '40P01' && i < maxRetries - 1) {
        await sleep(Math.random() * 100);  // jitter before retry
        continue;
      }
      throw err;
    }
  }
}
```

# SAVEPOINTS (Partial Rollback)
```sql
-- Savepoints let you rollback PART of a transaction
BEGIN;

INSERT INTO orders (user_id, total) VALUES (1, 500);

SAVEPOINT after_order;

INSERT INTO order_items (order_id, product_id) VALUES (99, 42);
-- This fails (FK violation)

ROLLBACK TO SAVEPOINT after_order;  -- undo only the order_items insert
-- orders insert is still intact

-- Continue with corrected data:
INSERT INTO order_items (order_id, product_id) VALUES (1, 42);

COMMIT;
```

# TRANSACTION PATTERNS

## Check-Then-Act Pattern (Avoid Race Conditions)
```sql
-- BAD — race condition between SELECT and UPDATE:
-- SELECT balance FROM accounts WHERE id = 1;  -- reads 100
-- (another transaction withdraws 80 here)
-- UPDATE accounts SET balance = balance - 100 WHERE id = 1;  -- balance goes to -80!

-- GOOD — do the check inside the UPDATE atomically:
BEGIN;
UPDATE accounts
SET balance = balance - 100
WHERE id = 1 AND balance >= 100;   -- condition checked atomically

IF NOT FOUND THEN
  ROLLBACK;
  RAISE EXCEPTION 'Insufficient balance';
END IF;
COMMIT;
```

## Upsert Pattern (Insert or Update Atomically)
```sql
-- PostgreSQL
INSERT INTO user_settings (user_id, theme, notifications)
VALUES (1, 'dark', true)
ON CONFLICT (user_id)
DO UPDATE SET
  theme = EXCLUDED.theme,
  notifications = EXCLUDED.notifications,
  updated_at = NOW();

-- MySQL
INSERT INTO user_settings (user_id, theme, notifications)
VALUES (1, 'dark', 1)
ON DUPLICATE KEY UPDATE
  theme = VALUES(theme),
  notifications = VALUES(notifications);
```

## Outbox Pattern (Transactional Event Publishing)
```sql
-- Problem: write to DB + publish to message queue can't be atomic
-- Solution: write event to DB in same transaction, publish separately

BEGIN;
UPDATE orders SET status = 'shipped' WHERE id = 456;
INSERT INTO outbox (event_type, payload, created_at)
VALUES ('ORDER_SHIPPED', '{"orderId": 456}', NOW());
COMMIT;

-- Separate process reads outbox and publishes events
-- Guarantees: event is published if and only if DB write succeeds
```

# APPLICATION-LEVEL TRANSACTION MANAGEMENT

## Node.js / Postgres (pg)
```javascript
const client = await pool.connect();
try {
  await client.query('BEGIN');

  const { rows } = await client.query(
    'SELECT balance FROM accounts WHERE id = $1 FOR UPDATE',
    [fromId]
  );
  if (rows[0].balance < amount) throw new Error('Insufficient funds');

  await client.query(
    'UPDATE accounts SET balance = balance - $1 WHERE id = $2',
    [amount, fromId]
  );
  await client.query(
    'UPDATE accounts SET balance = balance + $1 WHERE id = $2',
    [amount, toId]
  );

  await client.query('COMMIT');
} catch (err) {
  await client.query('ROLLBACK');
  throw err;
} finally {
  client.release();
}
```

## Prisma Transactions
```typescript
// Sequential (each step uses results of previous)
const [order, _] = await prisma.$transaction([
  prisma.order.create({ data: { userId: 1, total: 500 } }),
  prisma.inventory.update({
    where: { productId: 42 },
    data: { stock: { decrement: 1 } }
  })
]);

// Interactive (for complex logic, conditional branching)
const result = await prisma.$transaction(async (tx) => {
  const user = await tx.user.findUnique({ where: { id: 1 } });
  if (!user.isActive) throw new Error('Inactive user');

  return tx.order.create({ data: { userId: 1, total: 500 } });
}, {
  isolationLevel: Prisma.TransactionIsolationLevel.Serializable,
  timeout: 5000  // ms before auto-rollback
});
```

# COMMON MISTAKES
```
❌  Long-running transactions: network calls, file I/O, user input INSIDE transactions
    → locks held for seconds/minutes → everything queues behind you

❌  Swallowing errors without rollback:
    try { await query1(); } catch {}  // transaction still open, in bad state
    → always rollback on any error

❌  Not using transactions for multi-step writes:
    await createOrder();   // succeeds
    await deductStock();   // fails → order exists but stock not deducted

❌  Nested transactions without savepoints:
    BEGIN inside a BEGIN in most DBs — behavior is not what you expect

✅  Correct pattern: open transaction → do all reads+writes → commit or rollback
✅  Keep transactions < 100ms whenever possible
✅  Use connection pool properly — release connection in finally block
```

# TRANSACTION CHECKLIST
```
[ ] All related writes in a single transaction
[ ] Correct isolation level chosen for the use case
[ ] Locks acquired in consistent order (prevent deadlocks)
[ ] Transaction closed (COMMIT or ROLLBACK) in every code path
[ ] Connection released back to pool in finally block
[ ] Deadlock retry logic in place for high-contention flows
[ ] No external I/O (HTTP, file, sleep) inside transaction scope
[ ] Long transactions broken into smaller batches where possible
[ ] Savepoints used for optional sub-operations
[ ] Outbox pattern used when events must be published alongside writes
```
