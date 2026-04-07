---
name: Domain Driven Design
trigger: domain driven design, ddd, bounded context, aggregate root, entity, value object, domain model, ubiquitous language, context mapping
description: Apply Domain-Driven Design principles including bounded contexts, aggregates, entities, value objects, and context mapping. Use when modeling complex domains, designing microservice boundaries, or aligning code with business concepts.
---

# ROLE
You are a domain modeling expert. Your job is to help teams design software that reflects business reality using DDD patterns — bounded contexts, aggregates, entities, and value objects.

# STRATEGIC DESIGN

## Bounded Contexts
```
A bounded context is a boundary within which a model is defined and applicable.
Each context has its own ubiquitous language, model, and team ownership.

Example E-Commerce:
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Sales Context  │  │ Shipping Context │  │ Billing Context  │
│                 │  │                  │  │                  │
│ Product         │  │ Shipment        │  │ Invoice           │
│ Order           │  │ DeliveryRoute   │  │ Payment           │
│ Customer (buyer)│  │ Warehouse       │  │ Customer (payer)  │
└─────────────────┘  └─────────────────┘  └─────────────────┘

Note: "Customer" means different things in each context.
```

## Context Mapping Patterns
```
Shared Kernel     → Two teams share a common model (requires coordination)
Customer-Supplier → Downstream team depends on upstream team's model
Conformist        → Downstream conforms to upstream without influence
Anti-Corruption Layer → Translate between contexts to protect your model
Open Host Service → Upstream provides a well-defined protocol for all
Published Language → Shared schema/protocol (standard format)
Separate Ways     → No integration, completely independent
```

# TACTICAL DESIGN

## Building Blocks
```typescript
// Entity — has identity, mutable
class Order {
  constructor(
    readonly id: OrderId,
    private items: OrderItem[],
    private status: OrderStatus
  ) {}

  addItem(item: OrderItem): void {
    if (this.status !== 'draft') {
      throw new Error('Cannot modify completed order')
    }
    this.items.push(item)
  }

  complete(): void {
    if (this.items.length === 0) {
      throw new Error('Order must have items')
    }
    this.status = 'completed'
  }
}

// Value Object — no identity, immutable
class Money {
  constructor(
    readonly amount: number,
    readonly currency: string
  ) {
    if (amount < 0) throw new Error('Amount cannot be negative')
  }

  add(other: Money): Money {
    if (this.currency !== other.currency) {
      throw new Error('Cannot add different currencies')
    }
    return new Money(this.amount + other.amount, this.currency)
  }
}

// Aggregate Root — gateway to aggregate consistency
class Order {
  // Only way to modify order items is through the aggregate root
  // All invariants enforced here
  // External objects reference Order by ID only
}

// Repository — persistence abstraction for aggregates
interface OrderRepository {
  findById(id: OrderId): Promise<Order | null>
  save(order: Order): Promise<void>
  remove(order: Order): Promise<void>
}

// Domain Service — business logic that doesn't fit in an entity
interface PricingService {
  calculateTotal(order: Order, discounts: Discount[]): Money
  applyTax(amount: Money, region: Region): Money
}
```

# EVENT MODELING
```
Domain Events — something important happened in the domain

class OrderPlacedEvent {
  constructor(
    readonly orderId: OrderId,
    readonly customerId: CustomerId,
    readonly total: Money,
    readonly occurredAt: Date
  ) {}
}

// Published by aggregate
class Order {
  private events: DomainEvent[] = []

  complete(): void {
    // ... business logic
    this.events.push(new OrderCompletedEvent(this.id))
  }

  pullEvents(): DomainEvent[] {
    const events = [...this.events]
    this.events = []
    return events
  }
}
```

# REVIEW CHECKLIST
```
[ ] Bounded contexts identified and boundaries defined
[ ] Each context has its own ubiquitous language
[ ] Aggregates are small (1-3 entities max)
[ ] Value objects used for measurements/descriptions
[ ] Aggregate roots enforce invariants
[ ] Context mapping relationships documented
[ ] Domain events capture important business occurrences
[ ] Infrastructure separated from domain layer
```
