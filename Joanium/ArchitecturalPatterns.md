---
name: Architectural Patterns
trigger: architectural patterns, design architecture, system architecture, software architecture, mvc, mvvm, clean architecture, hexagonal architecture, layered architecture, event sourcing, cqrs
description: Understand and apply common architectural patterns including MVC, MVVM, Clean Architecture, Hexagonal/Ports & Adapters, Event Sourcing, CQRS, and Layered Architecture. Use when designing system architecture or evaluating architectural decisions.
---

# ROLE
You are a software architect. Your job is to help teams choose and implement architectural patterns that match their domain complexity, team size, and evolution needs. You prioritize maintainability, testability, and clear boundaries.

# ARCHITECTURAL PATTERNS

## Layered Architecture (N-Tier)
```
Presentation Layer → UI, API endpoints
Business Layer     → Business logic, validation, workflows
Persistence Layer  → Data access, repositories
Database Layer     → Storage

PROS: Simple, familiar, easy to understand
CONS: Tightly coupled layers, hard to test in isolation
USE WHEN: Simple CRUD applications, small teams, straightforward domains

Example:
controllers/
  UserController.ts      → Presentation
services/
  UserService.ts         → Business logic
repositories/
  UserRepository.ts      → Persistence
models/
  User.ts                → Domain
```

## MVC (Model-View-Controller)
```
Model   → Data and business logic
View    → UI presentation
Controller → Handles input, updates model, selects view

PROS: Clear separation of concerns, widely understood
CONS: Controller can become bloated, View-Model coupling
USE WHEN: Web applications, simple UIs, rapid development

Example (Express):
// Controller
app.get('/users/:id', async (req, res) => {
  const user = await UserService.findById(req.params.id)
  if (!user) return res.status(404).send('Not found')
  res.render('user/profile', { user })  // View
})
```

## MVVM (Model-View-ViewModel)
```
Model      → Data and business logic
View       → UI (declarative, data-bound)
ViewModel  → Presentation logic, state, commands

PROS: Excellent testability (ViewModel is pure logic), data binding
CONS: Can be overkill for simple UIs, ViewModel complexity
USE WHEN: Desktop apps, complex UIs, frameworks with data binding

Example (React-like):
// ViewModel (custom hook)
function useUserViewModel(userId: string) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(false)
  
  const loadUser = useCallback(async () => {
    setLoading(true)
    const data = await fetchUser(userId)
    setUser(data)
    setLoading(false)
  }, [userId])
  
  const updateName = async (name: string) => {
    await updateUser(userId, { name })
    setUser(prev => prev ? { ...prev, name } : null)
  }
  
  return { user, loading, loadUser, updateName }
}

// View (component uses ViewModel)
function UserProfile({ userId }) {
  const { user, loading, updateName } = useUserViewModel(userId)
  // ... render
}
```

## Clean Architecture
```
Entities        → Enterprise-wide business rules
Use Cases       → Application-specific business rules
Interface Adapters → Convert data between layers
Frameworks/Drivers → UI, DB, external services

DEPENDENCY RULE: Source code dependencies point inward
  → Inner layers know nothing about outer layers
  → Outer layers depend on inner layers

PROS: Framework independent, testable, maintainable
CONS: More boilerplate, learning curve, overkill for simple apps
USE WHEN: Long-lived applications, complex domains, multiple interfaces

Example:
src/
  entities/
    User.ts                    → Core business objects
  use-cases/
    CreateUser.ts              → Application business rules
    GetUser.ts
  interface-adapters/
    controllers/
      UserController.ts        → Convert HTTP to use case input
    presenters/
      UserPresenter.ts         → Convert use case output to HTTP
  frameworks/
    database/
      UserRepository.ts        → Data access implementation
    web/
      express/
        routes.ts              → Framework-specific routing
```

## Hexagonal Architecture (Ports & Adapters)
```
Application Core (Domain + Application Services)
    ↑
  Ports (Interfaces)
    ↑
Adapters (Implementations)
  → Primary adapters (driving): REST API, CLI, GraphQL
  → Secondary adapters (driven): Database, Email, External APIs

PROS: Domain-centric, easily swappable adapters, highly testable
CONS: Many interfaces/abstractions, initial complexity
USE WHEN: Domain-driven design, multiple interfaces, evolving tech stack

Example:
// Port (interface)
interface UserRepository {
  findById(id: string): Promise<User | null>
  save(user: User): Promise<void>
}

// Use case depends on port, not implementation
class GetUser {
  constructor(private repository: UserRepository) {}
  
  async execute(id: string): Promise<User> {
    const user = await this.repository.findById(id)
    if (!user) throw new UserNotFoundError(id)
    return user
  }
}

// Adapter implements port
class PostgresUserRepository implements UserRepository {
  async findById(id: string): Promise<User | null> {
    // PostgreSQL-specific implementation
  }
  
  async save(user: User): Promise<void> {
    // PostgreSQL-specific implementation
  }
}

// Wire up in composition root
const repository = new PostgresUserRepository(db)
const getUser = new GetUser(repository)
```

## Event Sourcing
```
State is derived from a sequence of events, not stored directly.
Instead of updating a record, you append an event.

PROS: Complete audit trail, temporal queries, event replay
CONS: Complexity, eventual consistency, event versioning
USE WHEN: Audit requirements, CQRS, complex business processes

Example:
// Events
interface Event {
  type: string
  aggregateId: string
  timestamp: Date
  payload: Record<string, any>
}

// Aggregate reconstructs state from events
class Order {
  constructor(
    public id: string,
    public items: OrderItem[] = [],
    public status: OrderStatus = 'created'
  ) {}
  
  static fromEvents(events: Event[]): Order {
    const order = new Order(events[0].aggregateId)
    for (const event of events) {
      order.applyEvent(event)
    }
    return order
  }
  
  applyEvent(event: Event) {
    switch (event.type) {
      case 'OrderCreated':
        this.items = event.payload.items
        break
      case 'ItemAdded':
        this.items.push(event.payload.item)
        break
      case 'OrderCompleted':
        this.status = 'completed'
        break
    }
  }
}
```

## CQRS (Command Query Responsibility Segregation)
```
Separate read and write operations into different models.
Commands change state, Queries read state.

PROS: Optimized read/write models, independent scaling, clear separation
CONS: Complexity, eventual consistency, two models to maintain
USE WHEN: Different read/write requirements, high-performance reads, complex domains

Example:
// Command side (write model)
class CreateUserCommand {
  constructor(
    public email: string,
    public name: string,
    public password: string
  ) {}
}

class CreateUserHandler {
  async handle(command: CreateUserCommand): Promise<string> {
    const user = new User(command.email, command.name, command.password)
    await this.userRepository.save(user)
    await this.eventBus.publish(new UserCreatedEvent(user.id))
    return user.id
  }
}

// Query side (read model — denormalized for fast reads)
class UserQueryModel {
  async findById(id: string): Promise<UserDto> {
    return this.readDb.query(
      'SELECT id, email, name, created_at FROM user_read_view WHERE id = ?',
      [id]
    )
  }
}
```

# PATTERN SELECTION GUIDE
```
Simple CRUD app          → Layered Architecture or MVC
Complex UI application   → MVVM or Clean Architecture
Domain-heavy application → Clean Architecture or Hexagonal
Audit/compliance needs   → Event Sourcing + CQRS
Multiple interfaces      → Hexagonal (Ports & Adapters)
High-performance reads   → CQRS with separate read model
Small team, simple domain → Layered or MVC
Large team, complex domain → Clean Architecture or Hexagonal
```

# REVIEW CHECKLIST
```
[ ] Architecture matches domain complexity
[ ] Dependency rule respected (inner layers independent)
[ ] Clear boundaries between components
[ ] Each component has single responsibility
[ ] Testable without framework dependencies
[ ] Data flow is unidirectional where possible
[ ] Error handling strategy consistent
[ ] Migration path from current architecture defined
```
