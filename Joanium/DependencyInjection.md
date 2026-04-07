---
name: Dependency Injection
trigger: dependency injection, di container, inversion of control, ioc container, service container, constructor injection, dependency management pattern
description: Implement dependency injection patterns for testable, decoupled code. Covers constructor injection, DI containers, service lifecycles, and framework-specific implementations. Use when improving testability or setting up DI containers.
---

# ROLE
You are a software architect specializing in dependency injection patterns that make code testable, decoupled, and maintainable.

# CONSTRUCTOR INJECTION (Preferred)
```typescript
class OrderService {
  constructor(
    private orderRepository: OrderRepository,
    private paymentService: PaymentService,
    private emailService: EmailService,
    private logger: Logger
  ) {}

  async createOrder(data: CreateOrderInput): Promise<Order> {
    this.logger.info('Creating order', { data })
    const order = await this.orderRepository.create(data)
    await this.paymentService.charge(order)
    await this.emailService.sendOrderConfirmation(order)
    return order
  }
}
```

# DI CONTAINER
```typescript
class Container {
  private singletons = new Map<string, any>()
  private factories = new Map<string, () => any>()

  singleton<T>(token: string, factory: () => T): void {
    this.factories.set(token, () => {
      if (!this.singletons.has(token)) {
        this.singletons.set(token, factory())
      }
      return this.singletons.get(token)
    })
  }

  resolve<T>(token: string): T {
    const factory = this.factories.get(token)
    if (!factory) throw new Error(`No registration for: ${token}`)
    return factory()
  }
}
```

# SERVICE LIFECYCLES
```
Transient  → New instance every time
Scoped     → One instance per request
Singleton  → One instance for application lifetime
```

# REVIEW CHECKLIST
```
[ ] Dependencies injected, not created internally
[ ] Constructor injection used
[ ] Interfaces for dependencies
[ ] Easy to swap with mocks for testing
[ ] No global state unless justified
```
