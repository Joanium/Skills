---
name: Event Sourcing & CQRS
trigger: event sourcing, CQRS, command query responsibility segregation, event store, append-only log, domain events, event replay, projections, read model, write model, audit log, immutable events
description: Design systems using event sourcing and CQRS. Covers event store design, command/query separation, projections, snapshots, event versioning, and when NOT to use these patterns.
---

# ROLE
You are a senior distributed systems architect. Event sourcing and CQRS are powerful but heavyweight — your job is to apply them where they genuinely belong and talk teams out of applying them everywhere else.

# CORE CONCEPTS

## Event Sourcing
```
TRADITIONAL:  Store current state
  users table: { id: 1, balance: 150, status: "active" }

EVENT SOURCED: Store the sequence of events that led to current state
  events: [
    { type: "AccountOpened",    data: { initialBalance: 200 } }
    { type: "MoneyWithdrawn",   data: { amount: 100 } }
    { type: "MoneyDeposited",   data: { amount: 50  } }
  ]
  → Replay all events → current balance = 150

BENEFITS:
  ✓ Complete audit log — free
  ✓ Time travel — reconstruct state at any point in history
  ✓ Event replay — rebuild projections, fix bugs retroactively
  ✓ Natural fit for domain events that business cares about

COSTS:
  ✗ More complex reads (must replay or maintain projections)
  ✗ Event schema migration is hard
  ✗ Eventual consistency in read models
  ✗ "What is the current state?" requires traversal or snapshot
```

## CQRS
```
Command  → writes, changes state, returns no data (or just an ID)
Query    → reads, never changes state, returns data

SEPARATE models for reading and writing:
  Write side: optimized for consistency, domain invariants, business rules
  Read side:  optimized for query performance, denormalized, pre-joined

Why separate them:
  Write model: small, focused aggregate — validates business rules
  Read model:  pre-built for the UI — no N+1 queries, no joins at runtime

They do NOT have to use the same database:
  Writes → PostgreSQL (ACID, append-only events table)
  Reads  → Redis, Elasticsearch, DynamoDB (whatever serves the query best)
```

# EVENT DESIGN

## What Makes a Good Event
```
RULES:
  1. Past tense verb — something that HAPPENED (not a command)
     OrderPlaced ✓     PlaceOrder ✗
     PaymentFailed ✓   FailPayment ✗

  2. Immutable — once written, never changed
     If you made a mistake → write a correcting event (MoneyRefunded)
     Not: edit the original MoneyCharged event

  3. Self-contained — include all data needed to process it
     BAD:  { type: "OrderShipped", orderId: 123 }
           → consumers must look up the order to do anything
     GOOD: { type: "OrderShipped", orderId: 123, customerId: 456,
              shippingAddress: {...}, items: [...] }

  4. Versioned from day one
     { type: "OrderPlaced", version: 1, ... }
```

## Event Envelope Schema
```typescript
interface DomainEvent {
  // Identity
  eventId:       string;    // uuid, globally unique
  eventType:     string;    // "OrderPlaced"
  eventVersion:  number;    // schema version (start at 1)

  // Routing
  aggregateType: string;    // "Order"
  aggregateId:   string;    // "ord_01HX..."
  sequenceNumber: number;   // position within this aggregate's stream

  // Time
  occurredAt:    string;    // ISO 8601 UTC

  // Tracing
  correlationId: string;    // traces a user action across services
  causationId:   string;    // the command or event that caused this

  // Payload
  data:          Record<string, unknown>;

  // Optional metadata
  metadata: {
    userId?:     string;    // who triggered this
    ipAddress?:  string;
    userAgent?:  string;
  };
}
```

# EVENT STORE DESIGN

## Schema (PostgreSQL)
```sql
CREATE TABLE events (
  event_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  aggregate_type  TEXT NOT NULL,
  aggregate_id    TEXT NOT NULL,
  sequence_number BIGINT NOT NULL,
  event_type      TEXT NOT NULL,
  event_version   INT NOT NULL DEFAULT 1,
  data            JSONB NOT NULL,
  metadata        JSONB NOT NULL DEFAULT '{}',
  occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Optimistic concurrency: prevents two writers from writing sequence N at the same time
  UNIQUE (aggregate_id, sequence_number)
);

-- Efficient stream reads
CREATE INDEX idx_events_aggregate ON events (aggregate_id, sequence_number ASC);

-- Global event ordering for projections
CREATE INDEX idx_events_global ON events (occurred_at ASC, event_id ASC);
```

## Optimistic Concurrency Control
```typescript
async function appendEvents(
  aggregateId: string,
  events: DomainEvent[],
  expectedVersion: number  // version client thinks is current
): Promise<void> {
  const currentVersion = await getLatestSequenceNumber(aggregateId);

  if (currentVersion !== expectedVersion) {
    throw new ConcurrencyError(
      `Expected version ${expectedVersion}, got ${currentVersion}. Retry the command.`
    );
  }

  await db.transaction(async (tx) => {
    for (let i = 0; i < events.length; i++) {
      await tx.query(
        `INSERT INTO events (aggregate_id, sequence_number, event_type, data, occurred_at)
         VALUES ($1, $2, $3, $4, $5)`,
        [aggregateId, expectedVersion + i + 1, events[i].eventType, events[i].data, new Date()]
      );
    }
  });
}
```

# AGGREGATES & COMMANDS

## Aggregate Pattern
```typescript
class OrderAggregate {
  private events: DomainEvent[] = [];

  // State — rebuilt by replaying events
  private id: string;
  private status: 'pending' | 'confirmed' | 'shipped' | 'cancelled';
  private items: OrderItem[];
  private totalAmount: number;

  // Load from event store
  static fromHistory(events: DomainEvent[]): OrderAggregate {
    const agg = new OrderAggregate();
    for (const event of events) {
      agg.apply(event, false);  // replay — don't record as new
    }
    return agg;
  }

  // Command handler — validates business rules, emits events
  placeOrder(items: OrderItem[], customerId: string): void {
    if (items.length === 0) throw new Error("Order must have at least one item");
    if (this.status !== undefined) throw new Error("Order already exists");

    this.apply({
      eventType: 'OrderPlaced',
      data: { items, customerId, totalAmount: this.calculateTotal(items) }
    }, true);
  }

  cancelOrder(reason: string): void {
    if (this.status === 'shipped') throw new Error("Cannot cancel a shipped order");
    if (this.status === 'cancelled') throw new Error("Already cancelled");

    this.apply({ eventType: 'OrderCancelled', data: { reason } }, true);
  }

  // Event application — pure state mutation, no side effects
  private apply(event: Partial<DomainEvent>, isNew: boolean): void {
    switch (event.eventType) {
      case 'OrderPlaced':
        this.status = 'pending';
        this.items = event.data.items;
        this.totalAmount = event.data.totalAmount;
        break;
      case 'OrderCancelled':
        this.status = 'cancelled';
        break;
    }
    if (isNew) this.events.push(event as DomainEvent);
  }

  getUncommittedEvents(): DomainEvent[] { return this.events; }
  clearUncommittedEvents(): void { this.events = []; }
}
```

# PROJECTIONS (READ MODELS)

## Projection Design
```typescript
// A projection listens to events and maintains a read-optimized view
class OrderListProjection {
  // Runs when new events arrive (real-time) or during replay (catch-up)

  async on(event: DomainEvent): Promise<void> {
    switch (event.eventType) {
      case 'OrderPlaced':
        await db.query(
          `INSERT INTO order_list_view (order_id, customer_id, status, total, placed_at)
           VALUES ($1, $2, 'pending', $3, $4)`,
          [event.aggregateId, event.data.customerId, event.data.totalAmount, event.occurredAt]
        );
        break;

      case 'OrderShipped':
        await db.query(
          `UPDATE order_list_view SET status = 'shipped', shipped_at = $1 WHERE order_id = $2`,
          [event.occurredAt, event.aggregateId]
        );
        break;

      case 'OrderCancelled':
        await db.query(
          `UPDATE order_list_view SET status = 'cancelled' WHERE order_id = $1`,
          [event.aggregateId]
        );
        break;
    }
  }
}

// Track projection position — allows replay from any point
CREATE TABLE projection_checkpoints (
  projection_name TEXT PRIMARY KEY,
  last_event_id   UUID,
  last_processed  TIMESTAMPTZ
);
```

# SNAPSHOTS

## When and How to Snapshot
```typescript
// Problem: replaying 10,000 events per request is slow
// Solution: periodically snapshot current state; replay only events after snapshot

const SNAPSHOT_EVERY_N_EVENTS = 100;

async function loadAggregate(aggregateId: string): Promise<OrderAggregate> {
  // 1. Try to load latest snapshot
  const snapshot = await snapshotStore.getLatest(aggregateId);

  // 2. Load events after snapshot (or all events if no snapshot)
  const fromSequence = snapshot?.sequenceNumber ?? 0;
  const events = await eventStore.getEvents(aggregateId, fromSequence);

  // 3. Restore from snapshot + remaining events
  const agg = snapshot
    ? OrderAggregate.fromSnapshot(snapshot.state)
    : new OrderAggregate();
  agg.applyHistory(events);

  return agg;
}

async function saveWithSnapshotCheck(agg: OrderAggregate): Promise<void> {
  await eventStore.append(agg.id, agg.getUncommittedEvents(), agg.version);

  if (agg.version % SNAPSHOT_EVERY_N_EVENTS === 0) {
    await snapshotStore.save({
      aggregateId: agg.id,
      sequenceNumber: agg.version,
      state: agg.toSnapshot(),
      savedAt: new Date()
    });
  }
}
```

# EVENT VERSIONING

## Upcasting (Preferred)
```typescript
// When event schema changes — upcast old events to new format at read time
// Original V1 event:  { type: "UserRegistered", data: { name: "Alice Smith" } }
// New V2 event:       { type: "UserRegistered", data: { firstName: "Alice", lastName: "Smith" } }

const upcasters: Record<string, (data: any) => any> = {
  'UserRegistered_v1': (data) => ({
    ...data,
    firstName: data.name.split(' ')[0],
    lastName: data.name.split(' ').slice(1).join(' '),
    name: undefined  // remove old field
  })
};

function upcast(event: DomainEvent): DomainEvent {
  const key = `${event.eventType}_v${event.eventVersion}`;
  const upcast = upcasters[key];
  if (!upcast) return event;
  return { ...event, data: upcast(event.data), eventVersion: event.eventVersion + 1 };
}
```

# WHEN TO USE (AND NOT USE)

## Use Event Sourcing When
```
✓ Complete audit trail is a business requirement (finance, healthcare, legal)
✓ You need to debug production state ("how did we end up here?")
✓ Business workflows are explicitly event-driven (order lifecycle, banking)
✓ You have complex domain logic with many state transitions
✓ Multiple independent consumers need to react to the same events
✓ You need to replay history to build new features retroactively
```

## DO NOT Use When
```
✗ Simple CRUD with no complex business rules (user profiles, settings)
✗ Team is new to DDD / event sourcing — learning curve is steep
✗ Data is ephemeral (sessions, caches, temp calculations)
✗ You need strong read consistency immediately after writes
✗ You're building an MVP and speed of delivery matters most

Start with traditional persistence. Migrate to event sourcing when the audit
trail and domain complexity justify the operational overhead.
```

# OPERATIONAL CHECKLIST
```
[ ] Event store is append-only — no UPDATE or DELETE on events table
[ ] Optimistic concurrency enforced on writes
[ ] Global event ordering guaranteed for projections
[ ] Projection checkpoints persisted — allows resumption after crash
[ ] Snapshot strategy defined for high-event-count aggregates
[ ] Event schema versioning strategy documented (upcasting preferred)
[ ] Dead letter queue for failed projection events
[ ] Event replay tested and documented (how do you rebuild a projection?)
[ ] Correlation/causation IDs on all events for distributed tracing
```
