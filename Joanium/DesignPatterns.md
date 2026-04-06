---
name: Design Patterns
trigger: design pattern, which pattern should i use, factory pattern, singleton, observer pattern, strategy pattern, decorator pattern, repository pattern, patterns for, refactor to pattern, gang of four, structural pattern, behavioral pattern, creational pattern, dependency injection pattern
description: Identify and implement the right design pattern for a given problem. Covers creational, structural, and behavioral patterns with real code examples, when to use them, and — critically — when not to. Use when designing a new abstraction, refactoring messy code, or reviewing architectural decisions.
---

Design patterns are solutions to recurring problems, not decorations to add to your code. The engineer who applies a pattern where it doesn't fit has made the code more complex, not better. Learn the pattern AND its context. Apply it only when the problem matches.

## The Meta-Question Before Any Pattern

```
Before applying any pattern, ask:
1. What problem does this solve?
2. Is that actually the problem I have RIGHT NOW?
3. Would a simpler approach work?

The Factory pattern doesn't make code better — it makes code 
with a SPECIFIC CREATION PROBLEM better. If you don't have 
that problem, it just adds indirection.
```

---

## Creational Patterns — How Objects Are Made

### Factory Method
**Problem:** You need to create objects, but the exact type depends on runtime conditions, and the creation logic is complex or might vary.

```typescript
// WITHOUT PATTERN: Growing if/switch is hard to extend
function createNotification(type: string, message: string) {
  if (type === 'email') return new EmailNotification(message, smtpClient);
  if (type === 'sms') return new SmsNotification(message, twilioClient);
  if (type === 'push') return new PushNotification(message, fcmClient);
  // Adding Slack means editing this function — violates Open/Closed
}

// WITH FACTORY METHOD
interface Notification {
  send(userId: string): Promise<void>;
}

abstract class NotificationFactory {
  // Factory method — subclasses decide the product
  abstract create(message: string): Notification;
  
  // Template method uses the factory
  async notify(userId: string, message: string) {
    const notification = this.create(message);
    await notification.send(userId);
  }
}

class EmailNotificationFactory extends NotificationFactory {
  create(message: string) { return new EmailNotification(message, this.smtp); }
}

class SmsNotificationFactory extends NotificationFactory {
  create(message: string) { return new SmsNotification(message, this.twilio); }
}

// Adding Slack: new class, zero changes to existing code
class SlackNotificationFactory extends NotificationFactory {
  create(message: string) { return new SlackNotification(message, this.slack); }
}

// Use a registry instead of if/else
const factories = new Map<string, NotificationFactory>([
  ['email', new EmailNotificationFactory(smtp)],
  ['sms',   new SmsNotificationFactory(twilio)],
  ['slack', new SlackNotificationFactory(slack)],
]);

const factory = factories.get(type);
if (!factory) throw new Error(`Unknown notification type: ${type}`);
await factory.notify(userId, message);
```

**Use when:** Creating objects whose type isn't known until runtime; when creation logic is complex and should be isolated; when you want to add new types without changing existing code.  
**Avoid when:** You only have one type, or construction is trivial.

---

### Builder
**Problem:** Constructing an object requires many parameters, some optional, and the combination of parameters determines validity.

```typescript
// BAD: Telescoping constructor
new Query(table, null, null, null, 'created_at', 'DESC', 10, 0);
// What does null mean in each position?

// WITH BUILDER
class QueryBuilder {
  private table: string;
  private conditions: string[] = [];
  private orderBy?: string;
  private orderDir: 'ASC' | 'DESC' = 'ASC';
  private limitVal?: number;
  private offsetVal: number = 0;

  from(table: string) { this.table = table; return this; }
  where(condition: string) { this.conditions.push(condition); return this; }
  order(column: string, dir: 'ASC' | 'DESC' = 'ASC') {
    this.orderBy = column; this.orderDir = dir; return this;
  }
  limit(n: number) { this.limitVal = n; return this; }
  offset(n: number) { this.offsetVal = n; return this; }

  build(): Query {
    if (!this.table) throw new Error('Table is required');
    return new Query(this);
  }
}

// Readable, self-documenting
const query = new QueryBuilder()
  .from('orders')
  .where('status = $1')
  .where('created_at > $2')
  .order('created_at', 'DESC')
  .limit(20)
  .build();
```

**Use when:** Constructors have > 4–5 parameters; many parameters are optional; invalid combinations should be caught at build time.  
**Avoid when:** Objects are simple — use a plain object/struct instead.

---

### Singleton
**Problem:** Exactly one instance of a class must exist (database connection pool, configuration, logger).

```typescript
// Module-level singleton (preferred in Node.js — modules are cached)
// db.ts
import { Pool } from 'pg';

const pool = new Pool({ connectionString: process.env.DATABASE_URL });

export default pool;  // The module IS the singleton

// Anywhere in the app:
import pool from './db';  // Same instance every time
```

```typescript
// Classic Singleton (when module pattern isn't available)
class Config {
  private static instance: Config;
  private data: Record<string, string>;

  private constructor() {
    this.data = { ...process.env };  // private constructor = no `new Config()`
  }

  static getInstance(): Config {
    if (!Config.instance) Config.instance = new Config();
    return Config.instance;
  }

  get(key: string) { return this.data[key]; }
}
```

**Use when:** Exactly one instance is genuinely required (connection pool, app config).  
**Avoid when:** You're using it to avoid passing dependencies — use dependency injection instead. Global state accessed via Singleton is hidden coupling.

---

## Structural Patterns — How Objects Are Composed

### Repository
**Problem:** Business logic is tangled with database queries, making it hard to test and hard to change the data source.

```typescript
// WITHOUT PATTERN: Business logic knows about SQL
class OrderService {
  async getHighValueOrders(customerId: string) {
    const rows = await db.query(
      `SELECT * FROM orders WHERE customer_id = $1 AND total_cents > 10000`,
      [customerId]
    );
    // Business logic buried with SQL
    return rows.map(r => ({ ...r, total: r.total_cents / 100 }));
  }
}

// WITH REPOSITORY PATTERN
// The interface (the contract) — business logic talks only to this
interface OrderRepository {
  findHighValueByCustomer(customerId: string, thresholdCents: number): Promise<Order[]>;
  findById(id: string): Promise<Order | null>;
  save(order: Order): Promise<Order>;
}

// The implementation — knows about SQL, nothing else does
class PostgresOrderRepository implements OrderRepository {
  async findHighValueByCustomer(customerId: string, thresholdCents: number) {
    const rows = await this.db.query(
      `SELECT * FROM orders WHERE customer_id = $1 AND total_cents > $2`,
      [customerId, thresholdCents]
    );
    return rows.map(this.toDomain);
  }
  
  private toDomain(row: any): Order {
    return new Order({ ...row, total: row.total_cents / 100 });
  }
}

// For tests — no database needed
class InMemoryOrderRepository implements OrderRepository {
  private orders: Order[] = [];
  
  async findHighValueByCustomer(customerId: string, thresholdCents: number) {
    return this.orders.filter(o =>
      o.customerId === customerId && o.totalCents > thresholdCents
    );
  }
}

// Business logic is clean and testable
class OrderService {
  constructor(private orders: OrderRepository) {}

  async getHighValueOrders(customerId: string) {
    return this.orders.findHighValueByCustomer(customerId, 10000);
  }
}

// Production
const service = new OrderService(new PostgresOrderRepository(db));

// Test
const service = new OrderService(new InMemoryOrderRepository());
```

**Use when:** You want to test business logic without a database; you may swap data sources; queries are complex and should be isolated.

---

### Decorator
**Problem:** You need to add behavior to an object without modifying its class, and the behavior should be composable.

```typescript
interface Logger {
  log(message: string): void;
}

class ConsoleLogger implements Logger {
  log(message: string) { console.log(message); }
}

// Decorators add behavior by wrapping
class TimestampLogger implements Logger {
  constructor(private inner: Logger) {}
  log(message: string) {
    this.inner.log(`[${new Date().toISOString()}] ${message}`);
  }
}

class PrefixLogger implements Logger {
  constructor(private inner: Logger, private prefix: string) {}
  log(message: string) {
    this.inner.log(`[${this.prefix}] ${message}`);
  }
}

class SamplingLogger implements Logger {
  constructor(private inner: Logger, private rate: number) {}
  log(message: string) {
    if (Math.random() < this.rate) this.inner.log(message);
  }
}

// Compose behaviors at runtime — no subclass explosion
const logger = new PrefixLogger(
  new TimestampLogger(
    new SamplingLogger(new ConsoleLogger(), 0.1)  // log 10% of messages
  ),
  'payments'
);

logger.log('Charge processed');
// → [payments] [2024-03-15T10:30:00Z] Charge processed  (10% of the time)
```

**Use when:** You need to add orthogonal behaviors (logging, caching, retrying, auth) to objects without modifying them; behaviors should be composable.

---

## Behavioral Patterns — How Objects Communicate

### Strategy
**Problem:** An algorithm has multiple implementations that should be swappable at runtime.

```typescript
// WITHOUT PATTERN: if/else for every algorithm variant
function sortProducts(products: Product[], method: string) {
  if (method === 'price-asc') return products.sort((a, b) => a.price - b.price);
  if (method === 'price-desc') return products.sort((a, b) => b.price - a.price);
  if (method === 'rating') return products.sort((a, b) => b.rating - a.rating);
  if (method === 'name') return products.sort((a, b) => a.name.localeCompare(b.name));
}

// WITH STRATEGY
type SortStrategy = (products: Product[]) => Product[];

const sortStrategies: Record<string, SortStrategy> = {
  'price-asc':  (p) => [...p].sort((a, b) => a.price - b.price),
  'price-desc': (p) => [...p].sort((a, b) => b.price - a.price),
  'rating':     (p) => [...p].sort((a, b) => b.rating - a.rating),
  'name':       (p) => [...p].sort((a, b) => a.name.localeCompare(b.name)),
};

function sortProducts(products: Product[], method: string): Product[] {
  const strategy = sortStrategies[method];
  if (!strategy) throw new Error(`Unknown sort method: ${method}`);
  return strategy(products);
}

// Adding a new sort: one new entry in the object — no if/else touched
sortStrategies['relevance'] = (p) => rankByRelevance(p);
```

**Use when:** Multiple algorithms do the same job differently; the algorithm choice is a runtime decision; you want to add algorithms without changing calling code.

---

### Observer (Event Emitter)
**Problem:** An object's state changes need to trigger actions in other objects without tight coupling between them.

```typescript
// Event bus (Observer in Node.js)
type Handler<T> = (payload: T) => void | Promise<void>;

class EventBus {
  private handlers = new Map<string, Handler<any>[]>();

  on<T>(event: string, handler: Handler<T>) {
    const existing = this.handlers.get(event) ?? [];
    this.handlers.set(event, [...existing, handler]);
    return () => this.off(event, handler); // Returns unsubscribe fn
  }

  off(event: string, handler: Handler<any>) {
    this.handlers.set(event,
      (this.handlers.get(event) ?? []).filter(h => h !== handler)
    );
  }

  async emit<T>(event: string, payload: T) {
    const handlers = this.handlers.get(event) ?? [];
    await Promise.all(handlers.map(h => h(payload)));
  }
}

// Usage — loose coupling between Order and its side effects
const bus = new EventBus();

// Subscribers registered independently — Order knows nothing about them
bus.on('order.placed', async ({ orderId, userId, total }) => {
  await emailService.sendOrderConfirmation(userId, orderId);
});

bus.on('order.placed', async ({ userId, total }) => {
  await loyaltyService.awardPoints(userId, total);
});

bus.on('order.placed', async ({ orderId }) => {
  await analyticsService.track('purchase', { orderId });
});

// Publisher is clean
class OrderService {
  async placeOrder(cart: Cart, userId: string) {
    const order = await this.orders.create(cart, userId);
    await bus.emit('order.placed', { orderId: order.id, userId, total: order.total });
    return order;
  }
}
```

**Use when:** One event should trigger many reactions; you want to decouple the publisher from its side effects; reactions should be addable without modifying the publisher.

---

### Command
**Problem:** You need to encapsulate operations as objects — for queuing, undo/redo, logging, or retrying.

```typescript
interface Command<T = void> {
  execute(): Promise<T>;
  undo?(): Promise<void>;
}

class TransferFundsCommand implements Command {
  constructor(
    private accounts: AccountRepository,
    private fromId: string,
    private toId: string,
    private amount: number
  ) {}

  async execute() {
    await this.accounts.debit(this.fromId, this.amount);
    await this.accounts.credit(this.toId, this.amount);
  }

  async undo() {
    await this.accounts.debit(this.toId, this.amount);
    await this.accounts.credit(this.fromId, this.amount);
  }
}

// Command processor handles queueing, retrying, history
class CommandBus {
  private history: Command[] = [];

  async execute(command: Command) {
    await command.execute();
    this.history.push(command);
  }

  async undoLast() {
    const command = this.history.pop();
    if (command?.undo) await command.undo();
  }
}
```

**Use when:** Operations need to be queued, logged, retried, or undone; you want to decouple the request from the execution.

---

## Pattern Selection Guide

```
Creating objects?
  ├─ Complex construction, many optional params → Builder
  ├─ Type determined at runtime → Factory Method
  └─ Must be exactly one instance → Singleton (use sparingly)

Adding behavior to objects?
  ├─ Orthogonal concerns (logging, caching, retry) → Decorator
  ├─ Hide data access behind a clean interface → Repository
  └─ Wrap an incompatible interface → Adapter

Objects communicating?
  ├─ Multiple algorithms, swappable → Strategy
  ├─ One event, many reactions → Observer
  ├─ Encapsulate operations (queue/undo) → Command
  └─ Step-by-step algorithm with variable steps → Template Method
```

## Anti-Patterns to Avoid

```
❌ Singleton used to avoid passing dependencies
   → Use dependency injection instead. Hidden global state is technical debt.

❌ Factory when you only have one type
   → Just use `new MyThing()`. Patterns add indirection; earn it.

❌ Repository wrapping every ORM method 1:1
   → A repository over Prisma with findMany/create/delete re-exported is noise.
   → Repositories should expose domain-meaningful methods, not ORM-shaped ones.

❌ Observer for simple linear code
   → If A always triggers B, just call B from A. Events add indirection.
   → Use Observer when you genuinely don't know who the subscribers are.

❌ Using patterns as resume keywords
   → The goal is readable, maintainable code. Not "Enterprise Architecture".
```
