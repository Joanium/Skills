---
name: Database Connection Pooling
trigger: connection pool, database connections, pgbouncer, connection pooling, too many connections, max connections postgres, pool size, connection exhaustion, db pool configuration, pgpool
description: Design, configure, and debug database connection pools for production systems. Covers pool sizing math, PgBouncer, application-level pooling, connection exhaustion diagnosis, and multi-tenant pooling strategies.
---

# ROLE
You are a senior backend engineer specializing in database infrastructure. Connection pools are one of the most common sources of production incidents — too few connections starve the app, too many overwhelm the database. Get this right and you prevent a class of 3am pages.

# CORE PRINCIPLES
```
CONNECTIONS ARE EXPENSIVE:  Each Postgres connection costs ~5–10MB RAM and a process/thread.
POOL AT EVERY TIER:         App pool → PgBouncer → Postgres. Each layer has a role.
SIZE WITH MATH, NOT GUESSES: Formula-based pool sizing beats trial and error.
MONITOR THE WAIT TIME:      Pool queue wait is the canary — watch it before timeouts spike.
FAIL FAST ON EXHAUSTION:    Return an error quickly rather than queuing requests indefinitely.
```

# POOL SIZING FORMULA
```
The right pool size is NOT "max out your DB connections".

Postgres optimal concurrency = num_cores × 2 (I/O bound workloads add a multiplier)
  Example: 8-core DB server → 16 backend connections optimal for CPU-bound
  For I/O-bound (typical web APIs): 8 × 2 × 2 = ~32 concurrent active queries

Pool size per app instance:
  pool_size = (DB_max_connections - superuser_reserved) / num_app_instances

  Example:
    Postgres max_connections = 100
    Reserved for admin/migrations: 5
    App instances: 5
    → Pool per instance = (100 - 5) / 5 = 19

  Start conservatively — you can always increase. Over-pooling causes contention.

Queue / overflow:
  max_overflow = pool_size × 0.5   (50% burst headroom)
  queue_timeout = 5s               (fail fast — don't queue forever)
```

# APPLICATION-LEVEL POOLING

## Node.js — pg (node-postgres)
```javascript
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,               // max connections in pool
  min: 5,                // keep warm connections ready
  idleTimeoutMillis: 30_000,    // close idle connections after 30s
  connectionTimeoutMillis: 5_000, // fail fast if pool exhausted
  allowExitOnIdle: false,        // keep pool alive in long-running processes
});

// Always release back to pool — use pool.connect() only when you need transactions
// For simple queries, use pool.query() directly (auto-releases)
const { rows } = await pool.query('SELECT * FROM users WHERE id = $1', [userId]);

// Transactions — manual connect/release
const client = await pool.connect();
try {
  await client.query('BEGIN');
  await client.query('INSERT INTO orders ...', [...]);
  await client.query('UPDATE inventory ...', [...]);
  await client.query('COMMIT');
} catch (err) {
  await client.query('ROLLBACK');
  throw err;
} finally {
  client.release();  // ALWAYS release, even on error — or pool drains permanently
}

// Monitor pool health
setInterval(() => {
  logger.info({
    totalCount: pool.totalCount,
    idleCount: pool.idleCount,
    waitingCount: pool.waitingCount,  // queue depth — alert if consistently > 0
  }, 'DB pool stats');
}, 30_000);
```

## Python — SQLAlchemy
```python
from sqlalchemy import create_engine, event
from sqlalchemy.pool import QueuePool

engine = create_engine(
    os.environ["DATABASE_URL"],
    poolclass=QueuePool,
    pool_size=10,          # base pool size
    max_overflow=5,        # allow burst up to pool_size + max_overflow = 15
    pool_timeout=5,        # wait max 5s for a connection before raising
    pool_recycle=1800,     # recycle connections older than 30min (avoids stale TCP)
    pool_pre_ping=True,    # validate connection before use (catches server restarts)
)

# With FastAPI — one engine, shared across requests
# Do NOT create a new engine per request
@asynccontextmanager
async def lifespan(app: FastAPI):
    # engine already created at module level
    yield
    engine.dispose()  # close pool on shutdown
```

## Go — pgx
```go
import "github.com/jackc/pgx/v5/pgxpool"

config, _ := pgxpool.ParseConfig(os.Getenv("DATABASE_URL"))
config.MaxConns = 20
config.MinConns = 5
config.MaxConnLifetime = 30 * time.Minute  // recycle long-lived connections
config.MaxConnIdleTime = 5 * time.Minute
config.HealthCheckPeriod = 1 * time.Minute

pool, err := pgxpool.NewWithConfig(context.Background(), config)
// Pool is safe for concurrent use — share it across goroutines, never create per-request
```

# PGBOUNCER — PROXY-LEVEL POOLING
```
WHY: Postgres can't handle thousands of connections efficiently.
     PgBouncer sits between app and DB, multiplexing many app connections → few DB connections.

MODES:
  session:     One DB connection per client session (same as no pooling — avoid)
  transaction: DB connection held only during a transaction (BEST for most apps)
  statement:   Connection per statement (incompatible with transactions — rarely useful)

# pgbouncer.ini
[databases]
myapp = host=postgres-primary port=5432 dbname=myapp pool_size=25

[pgbouncer]
listen_port = 6432
listen_addr = *
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/users.txt
pool_mode = transaction       # ← most efficient
max_client_conn = 1000        # clients can connect freely
default_pool_size = 25        # only 25 real DB connections per database
min_pool_size = 5
reserve_pool_size = 5         # emergency burst connections
reserve_pool_timeout = 3      # wait 3s before using reserve pool
server_idle_timeout = 60      # close idle server connections after 60s
client_idle_timeout = 0       # keep client connections open (managed by app pool)

# CAVEATS with transaction mode:
# - SET/RESET session variables don't persist across transactions
# - LISTEN/NOTIFY requires session mode
# - Prepared statements need server_reset_query or track_extra_parameters
```

# DIAGNOSING CONNECTION EXHAUSTION
```sql
-- Current connections by state
SELECT state, count(*), max(now() - query_start) AS max_duration
FROM pg_stat_activity
WHERE datname = 'myapp'
GROUP BY state
ORDER BY count DESC;

-- Long-running queries (potential holders of connections)
SELECT pid, now() - query_start AS duration, state, left(query, 100) AS query
FROM pg_stat_activity
WHERE datname = 'myapp'
  AND now() - query_start > interval '30 seconds'
ORDER BY duration DESC;

-- Idle-in-transaction (major leak signal — connections held open doing nothing)
SELECT pid, now() - state_change AS idle_duration, left(query, 100) AS last_query
FROM pg_stat_activity
WHERE state = 'idle in transaction'
  AND now() - state_change > interval '10 seconds';

-- Kill a stuck connection
SELECT pg_terminate_backend(pid) WHERE pid = 12345;

-- Set idle-in-transaction timeout (prevent leaks at DB level)
ALTER DATABASE myapp SET idle_in_transaction_session_timeout = '30s';
```

# COMMON ISSUES & FIXES
```
SYMPTOM: "too many connections" errors
CAUSE:   App instances × pool_size > max_connections
FIX:     Reduce pool_size per instance, add PgBouncer, increase max_connections (with RAM)

SYMPTOM: "connection timeout" or pool wait queue building up
CAUSE:   Slow queries holding connections, pool undersized for traffic
FIX:     Find and optimize slow queries first; then tune pool size

SYMPTOM: "connection reset by peer" or "broken pipe" errors
CAUSE:   Connections stale after network interruption or DB restart
FIX:     Enable pool_pre_ping=True (SQLAlchemy) or health check intervals
         Set pool_recycle to less than server's TCP idle timeout

SYMPTOM: Idle-in-transaction connections piling up
CAUSE:   App opened transaction, never committed or rolled back (crash or bug)
FIX:     Set idle_in_transaction_session_timeout = '30s' on DB
         Fix application code — always use try/finally to release connections

SYMPTOM: PgBouncer transaction mode breaks SET/RESET or LISTEN
CAUSE:   Session-level state doesn't persist across transactions in transaction mode
FIX:     Use server_reset_query for cleanup, or switch specific operations to session mode
```

# MONITORING METRICS TO ALERT ON
```
Application pool:
  pool.waitingCount > 0 consistently → pool starved, add connections or optimize queries
  pool.idleCount ≈ 0 consistently    → pool exhausted, increase pool_size
  connectionTimeout errors           → pool exhausted under load

PgBouncer:
  cl_waiting > 0                     → clients queuing for connection
  sv_idle ≈ 0                        → all server connections busy
  maxwait_us > 1_000_000 (1s)        → serious pool pressure

Postgres:
  numbackends approaching max_connections  → danger zone
  idle in transaction > 10 connections    → connection leak
  avg_wait_time in pg_stat_activity       → lock contention
```

# MULTI-TENANT POOLING STRATEGY
```
For SaaS with per-tenant databases or schemas:

Option A — Shared pool with schema switching (same DB):
  - Use search_path per request: SET search_path = tenant_123, public
  - PgBouncer transaction mode: SET doesn't persist → reset with server_reset_query
  - Or use RLS (Row Level Security) with a shared pool

Option B — Per-tenant connection pool (separate DBs):
  - Dynamic pool map: tenantId → Pool
  - Lazy initialization: create pool on first request per tenant
  - Evict idle tenant pools (LRU cache with TTL)

  const pools = new Map<string, Pool>();

  function getPool(tenantId: string): Pool {
    if (!pools.has(tenantId)) {
      pools.set(tenantId, new Pool({
        connectionString: getTenantDSN(tenantId),
        max: 5,  // smaller per-tenant pool
        idleTimeoutMillis: 60_000,
      }));
    }
    return pools.get(tenantId)!;
  }
```
