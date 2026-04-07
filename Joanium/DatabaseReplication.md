---
name: Database Replication
trigger: database replication, read replicas, master slave replication, multi master replication, database scaling, replication lag, database high availability
description: Design and manage database replication topologies including primary-replica, multi-primary, and cross-region replication. Covers replication lag, failover, and read scaling. Use when scaling databases, setting up replicas, or implementing high availability.
---

# ROLE
You are a database reliability engineer. Your job is to design replication topologies that provide high availability, read scaling, and disaster recovery while managing replication lag and consistency trade-offs.

# REPLICATION TOPOLOGIES

## Primary-Replica (Leader-Follower)
```
Primary (read-write) → Replica 1 (read-only)
                     → Replica 2 (read-only)
                     → Replica 3 (read-only, different region)

PROS: Read scaling, high availability, backup source
CONS: Replication lag, write bottleneck on primary
USE WHEN: Read-heavy workloads, need HA, geographic distribution
```

## Multi-Primary (Multi-Master)
```
Primary 1 ↔ Primary 2 ↔ Primary 3
(all accept reads and writes)

PROS: Write scaling, no single point of failure
CONS: Conflict resolution complexity, eventual consistency
USE WHEN: Multi-region writes, active-active requirements
```

# IMPLEMENTATION

## PostgreSQL Streaming Replication
```
# Primary configuration (postgresql.conf)
wal_level = replica
max_wal_senders = 10
wal_keep_size = 1GB

# Create replication user
CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'secure_password';

# pg_hba.conf
host replication replicator replica_ip/32 md5

# Replica setup
pg_basebackup -h primary_host -D /var/lib/postgresql/data \
  -U replicator -P -v --checkpoint=fast

# Recovery configuration (standby.signal + postgresql.conf)
primary_conninfo = 'host=primary_host port=5432 user=replicator password=secure_password'
```

## Read Replica Routing
```typescript
// Route reads to replicas, writes to primary
class DatabaseRouter {
  private primary: DatabaseConnection
  private replicas: DatabaseConnection[]
  private currentIndex = 0

  async query(sql: string, params: any[], options?: QueryOptions) {
    if (options?.forcePrimary || this.isWriteQuery(sql)) {
      return this.primary.query(sql, params)
    }
    
    // Round-robin across replicas
    const replica = this.replicas[this.currentIndex % this.replicas.length]
    this.currentIndex++
    
    return replica.query(sql, params)
  }

  private isWriteQuery(sql: string): boolean {
    const trimmed = sql.trim().toUpperCase()
    return trimmed.startsWith('INSERT') ||
           trimmed.startsWith('UPDATE') ||
           trimmed.startsWith('DELETE') ||
           trimmed.startsWith('CREATE') ||
           trimmed.startsWith('ALTER') ||
           trimmed.startsWith('DROP')
  }
}
```

# REPLICATION LAG

## Monitoring
```sql
-- PostgreSQL: Check replication lag
SELECT
  client_addr,
  state,
  sent_lsn,
  write_lsn,
  flush_lsn,
  replay_lsn,
  EXTRACT(EPOCH FROM replay_lag) AS lag_seconds
FROM pg_stat_replication;

-- Alert if lag exceeds threshold
-- lag_seconds > 5 → Warning
-- lag_seconds > 30 → Critical
```

## Handling Lag in Application
```typescript
// Read-your-writes consistency
class SessionAwareRouter extends DatabaseRouter {
  private lastWriteTimestamp = new Map<string, number>()

  async queryForUser(userId: string, sql: string, params: any[]) {
    const lastWrite = this.lastWriteTimestamp.get(userId) || 0
    
    // Force primary if recent write for this user
    if (Date.now() - lastWrite < 5000) { // 5 second window
      return this.primary.query(sql, params)
    }
    
    return super.query(sql, params)
  }

  async write(userId: string, sql: string, params: any[]) {
    this.lastWriteTimestamp.set(userId, Date.now())
    return this.primary.query(sql, params)
  }
}
```

# FAILOVER
```
Automatic failover process:
1. Detect primary failure (health check timeout)
2. Elect new primary (most up-to-date replica)
3. Promote replica to primary
4. Update DNS/connection strings
5. Other replicas reconfigure to follow new primary
6. Old primary rejoins as replica when recovered

Tools:
- Patroni (PostgreSQL)
- Orchestrator (MySQL)
- Cloud provider managed (AWS RDS, GCP Cloud SQL)
```

# REVIEW CHECKLIST
```
[ ] Replication topology matches workload requirements
[ ] Replication lag monitored and alerted
[ ] Read routing distributes load across replicas
[ ] Read-your-writes consistency handled
[ ] Failover procedure tested regularly
[ ] Backups taken from replicas (not primary)
[ ] Cross-region replication for disaster recovery
[ ] Connection pooling configured for replica connections
```
