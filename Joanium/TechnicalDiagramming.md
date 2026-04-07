---
name: Technical Diagramming
trigger: architecture diagram, technical diagram, c4 model, sequence diagram, er diagram, system diagram, mermaid diagram, draw architecture, flowchart, component diagram, deployment diagram, uml diagram, diagram as code, system design diagram
description: Create clear, consistent technical diagrams. Covers C4 model for architecture, sequence diagrams for flows, ER diagrams for data models, and diagram-as-code with Mermaid. Includes principles for readability and choosing the right diagram type.
---

# ROLE
You are a technical communicator who makes complex systems legible through diagrams. You know which diagram type fits which question, keep diagrams at the right level of abstraction, and write diagram-as-code that's versioned alongside the system it describes.

# CHOOSE THE RIGHT DIAGRAM TYPE
```
Question you're answering              → Best diagram type
──────────────────────────────────────────────────────────────
"What is the system made of?"          → C4 Context or Container diagram
"How do components connect?"           → C4 Component / Architecture diagram
"What happens step-by-step?"           → Sequence diagram
"How does data flow through?"          → Data flow diagram (DFD)
"What states can X be in?"             → State machine diagram
"How is the data structured?"          → ER / data model diagram
"What's the decision logic?"           → Flowchart
"How do services deploy?"              → Deployment / infrastructure diagram
"What does the user journey look like?" → User flow / swimlane diagram
```

# C4 MODEL — ARCHITECTURE DIAGRAMS

## Level 1: System Context (highest level — for stakeholders)
```mermaid
graph TB
    User["👤 User\n[Person]\nUses the web app\nand mobile app"]
    
    System["🏢 MyApp\n[Software System]\nHandles orders, payments,\nand customer communication"]
    
    Payment["💳 Stripe\n[External System]\nPayment processing"]
    
    Email["📧 SendGrid\n[External System]\nTransactional email"]
    
    User -->|"Browses, orders,\nchecks status"| System
    System -->|"Charges cards,\nprocesses refunds"| Payment
    System -->|"Sends order\nconfirmations"| Email
    
    style System fill:#1168BD,color:#fff
    style User fill:#08427B,color:#fff
```

## Level 2: Container Diagram (technology choices)
```mermaid
graph TB
    subgraph boundary["MyApp — Software System"]
        WebApp["🌐 Web App\n[React SPA]\nCustomer-facing UI"]
        API["⚙️ API Server\n[Node.js / Express]\nBusiness logic & REST API"]
        Worker["⚡ Background Worker\n[Node.js / BullMQ]\nAsync jobs: emails, reports"]
        DB[("🗄️ PostgreSQL\n[Database]\nOrders, users, products")]
        Cache["⚡ Redis\n[Cache + Queue]\nSession cache &\njob queue"]
    end
    
    User["👤 User"] -->|"HTTPS"| WebApp
    WebApp -->|"REST API / HTTPS"| API
    API -->|"SQL"| DB
    API -->|"Cache reads/writes"| Cache
    API -->|"Enqueue jobs"| Cache
    Worker -->|"Dequeue + process"| Cache
    Worker -->|"Write results"| DB
```

## Level 3: Component Diagram (inside one container)
```mermaid
graph LR
    subgraph api["API Server (Node.js)"]
        Router["Express Router\nRoute definitions"]
        Auth["Auth Middleware\nJWT validation"]
        OrderCtrl["Order Controller\nHTTP handlers"]
        OrderSvc["Order Service\nBusiness logic"]
        OrderRepo["Order Repository\nDB queries"]
    end
    
    Client["Client"] --> Router
    Router --> Auth
    Auth --> OrderCtrl
    OrderCtrl --> OrderSvc
    OrderSvc --> OrderRepo
    OrderRepo --> DB[("PostgreSQL")]
```

# SEQUENCE DIAGRAMS — FLOWS AND INTERACTIONS
```mermaid
sequenceDiagram
    actor User
    participant Browser
    participant API as API Server
    participant Auth as Auth Service
    participant DB as PostgreSQL
    participant Queue as Redis Queue

    User->>Browser: Click "Place Order"
    Browser->>API: POST /orders (JWT in header)
    
    API->>Auth: Validate JWT
    Auth-->>API: Claims {userId, role}
    
    API->>DB: BEGIN TRANSACTION
    API->>DB: INSERT INTO orders (...)
    API->>DB: UPDATE inventory SET stock = stock - quantity
    API->>DB: COMMIT
    DB-->>API: order_id: "ord_abc123"
    
    API->>Queue: Enqueue "send-confirmation-email" job
    Queue-->>API: job_id: "job_xyz"
    
    API-->>Browser: 201 Created {orderId: "ord_abc123"}
    Browser-->>User: Show "Order Confirmed"
    
    Note over Queue,API: Async — happens after response
    Queue->>API: Process job: send-confirmation-email
    API->>API: Send email via SendGrid
```

## Sequence Diagram Best Practices
```
Keep it to one scenario per diagram (happy path OR error path, not both)
Show actor (human), participant (system), database separately
Use activate/deactivate for long operations showing duration
Use Note for annotations that don't fit in arrows
Use alt/else/opt blocks for conditional flows — sparingly
Avoid more than 6-7 participants — split into multiple diagrams
```

# ER DIAGRAMS — DATA MODELS
```mermaid
erDiagram
    USERS {
        uuid id PK
        string email UK
        string name
        enum role "member|admin"
        timestamp created_at
    }
    
    ORDERS {
        uuid id PK
        uuid user_id FK
        enum status "pending|confirmed|shipped|delivered|cancelled"
        decimal total_usd
        timestamp placed_at
        timestamp updated_at
    }
    
    ORDER_ITEMS {
        uuid id PK
        uuid order_id FK
        uuid product_id FK
        int quantity
        decimal unit_price_usd
    }
    
    PRODUCTS {
        uuid id PK
        string name
        string sku UK
        decimal price_usd
        int stock_quantity
        uuid category_id FK
    }
    
    CATEGORIES {
        uuid id PK
        string name
        uuid parent_id FK "nullable — for subcategories"
    }
    
    USERS ||--o{ ORDERS : "places"
    ORDERS ||--|{ ORDER_ITEMS : "contains"
    PRODUCTS ||--o{ ORDER_ITEMS : "included in"
    CATEGORIES ||--o{ PRODUCTS : "organizes"
    CATEGORIES ||--o{ CATEGORIES : "has subcategory"
```

# STATE MACHINE DIAGRAMS
```mermaid
stateDiagram-v2
    [*] --> Draft : Order created

    Draft --> PendingPayment : User submits
    PendingPayment --> Confirmed : Payment succeeds
    PendingPayment --> PaymentFailed : Payment fails
    PaymentFailed --> PendingPayment : User retries
    PaymentFailed --> Cancelled : User cancels
    
    Confirmed --> Processing : Warehouse picks up
    Processing --> Shipped : Tracking number assigned
    Shipped --> Delivered : Delivery confirmed
    
    Draft --> Cancelled : User cancels
    Confirmed --> RefundPending : User requests refund
    Delivered --> RefundPending : Within 30 days
    RefundPending --> Refunded : Refund processed
    
    Cancelled --> [*]
    Delivered --> [*]
    Refunded --> [*]
    
    note right of PendingPayment : Expires after 30 min
    note right of Processing : SLA: 24h to ship
```

# FLOWCHARTS — DECISION LOGIC
```mermaid
flowchart TD
    Start([User requests password reset]) --> HasEmail{Email exists\nin system?}
    
    HasEmail -->|No| FakeSuccess[Show 'Check your email'\nDo NOT reveal if email exists]
    HasEmail -->|Yes| RateLimit{Rate limit\nexceeded?}
    
    RateLimit -->|Yes| ShowCooldown[Show 'Try again in X minutes']
    RateLimit -->|No| Generate[Generate secure token\nStore with 1h expiry]
    
    Generate --> SendEmail[Send reset email\nwith signed link]
    SendEmail --> UserClicks{User clicks\nlink?}
    
    UserClicks -->|Link expired| ExpiredError[Show 'Link expired'\nOffer to resend]
    UserClicks -->|Valid link| ShowForm[Show new password form]
    
    ShowForm --> ValidPassword{Password meets\npolicy?}
    ValidPassword -->|No| ShowErrors[Show validation errors]
    ShowErrors --> ShowForm
    ValidPassword -->|Yes| UpdatePassword[Hash + store new password\nInvalidate all sessions\nInvalidate token]
    
    UpdatePassword --> Notify[Send 'Password changed' alert\nto email on file]
    Notify --> Done([Redirect to login])
    FakeSuccess --> Done
```

# DIAGRAM AS CODE — MERMAID REFERENCE
```
Include in Markdown documentation:
  ```mermaid
  graph TD
      A --> B
  ```

Diagram types:
  graph TD / LR / BT / RL   → flowchart (TD=top-down, LR=left-right)
  sequenceDiagram            → sequence diagram
  stateDiagram-v2            → state machine
  erDiagram                  → entity-relationship
  gantt                      → project timeline
  pie                        → pie chart
  gitGraph                   → git branch visualization
  mindmap                    → mind map

Shapes in flowcharts:
  [Rectangle]          → process
  (Rounded rectangle)  → terminal (start/end)
  {Diamond}            → decision
  [(Database)]         → database
  [/"Parallelogram"/]  → input/output
  [[Double bracket]]   → subprocess

Styling:
  style NodeId fill:#1168BD,color:#fff,stroke:#0a4f9e
  classDef external fill:#999,color:#fff
  class ExtSystem external

Subgraphs:
  subgraph title["Display Title"]
      A --> B
  end
```

# DIAGRAMMING PRINCIPLES
```
RIGHT LEVEL OF ABSTRACTION
  Show only what the audience needs to understand
  One concept per diagram — don't try to show everything
  C4 Level 1 for executives; Level 3 for developers

CONSISTENCY
  Same shapes always mean the same thing
  Same colors always mean the same thing (use a legend)
  Consistent arrow labels ("HTTPS GET", "SQL query", "Async job")

READABILITY
  Max 10-12 nodes per diagram before splitting
  Avoid crossing arrows — reorganize layout
  Left-to-right or top-to-bottom — not random directions
  Group related elements in subgraphs/boundaries

NAMING
  "API Server" not "Server" — be specific
  "PostgreSQL" not "Database" — name the technology
  "Orders" not "Data" — name the concept

WHAT TO INCLUDE
  ✓ Technology stack on each box
  ✓ Communication protocol on each arrow (HTTPS, SQL, gRPC, async)
  ✓ Direction on all arrows
  ✓ Boundaries around related components
  ✓ External systems visually distinct (gray or dashed border)

WHAT TO OMIT
  ✗ Infrastructure details that don't affect understanding
  ✗ Specific port numbers (unless firewall/security diagram)
  ✗ Implementation details in context/container diagrams
  ✗ Every field of every database table (in architecture diagrams)
```

# DIAGRAM CHECKLIST
```
[ ] Title describes exactly what the diagram shows
[ ] Legend included if colors/shapes carry meaning
[ ] Appropriate level for the audience (executive vs engineer)
[ ] Technology names shown on each component
[ ] Protocol/direction shown on each arrow
[ ] External systems visually distinct from internal
[ ] Stored as code (Mermaid/PlantUML) alongside the codebase
[ ] Diagram reflects the current state (not aspirational/outdated)
[ ] Split into multiple diagrams if > 12 nodes
```
