---
name: Clean Code & SOLID Principles
trigger: clean code, solid principles, single responsibility, open closed principle, liskov, interface segregation, dependency inversion, clean up my code, naming, code smells, functions too long, too many parameters, code quality, readable code, maintainable code, refactor for readability, dry principle, kiss principle
description: Write code that is readable, maintainable, and correct — by applying SOLID principles, clean naming, function design, and identifying code smells. Use when reviewing your own code for quality, teaching coding principles, or refactoring messy code to improve clarity.
---

Clean code is not about style preferences or aesthetics. It is about making the next person (often future-you) able to read, understand, and safely change the code. Code is read far more than it is written. Optimize for the reader.

## The Core Insight

```
"Any fool can write code that a computer can understand.
 Good programmers write code that humans can understand."
 — Martin Fowler

Clean code has one primary quality: it expresses intent clearly.
The reader should know what the code does without needing a comment to explain it.
```

---

## Naming — The Most Impactful Improvement

Good names replace comments. If you need a comment to explain a variable, the variable is named wrong.

### Variables and constants
```typescript
// BAD: What is d? What does the number mean?
const d = 86400;
if (ts > Date.now() - d * 1000) { ... }

// GOOD: Reads like a sentence
const ONE_DAY_IN_SECONDS = 86400;
const isWithinLastDay = createdAt > Date.now() - ONE_DAY_IN_SECONDS * 1000;

// BAD: Type in name, no meaning
const userArray = [];
const dataObj = {};
const strName = '';

// GOOD: What does it contain?
const activeUsers = [];
const userPreferences = {};
const firstName = '';

// BAD: Single letters outside loops
const u = users.find(u => u.id === id);

// GOOD: Meaningful at a glance
const currentUser = users.find(user => user.id === targetId);
```

### Functions — name the intent, not the implementation
```typescript
// BAD: describes HOW, not WHAT
function iterateUsersAndCheckStatusAndSendEmail(users) { ... }
function doStuff(data) { ... }
function process(input) { ... }

// GOOD: describes the purpose clearly
function notifyInactiveUsers(users: User[]) { ... }
function calculateRefundAmount(order: Order): number { ... }
function parseAuthorizationHeader(header: string): Token { ... }

// BAD: boolean returns with confusing names
function checkUser(user) → true/false  // check what? true = what?
function userData(user) → User         // "data" is noise

// GOOD: boolean names are predicates
function isActiveUser(user: User): boolean { ... }
function hasVerifiedEmail(user: User): boolean { ... }
function canAccessResource(user: User, resource: Resource): boolean { ... }
```

### Avoid noise words and encodings
```typescript
// Noise words — add no information
const userInfo = ...     // vs user
const orderData = ...    // vs order
const theManager = ...   // vs manager
const AccountManager = ...  // The?

// Hungarian notation — unnecessary in typed languages
const strEmail = ''     // vs email
const intCount = 0      // vs count
const bIsValid = false  // vs isValid

// Abbreviations that obscure meaning
const usr = ...    // vs user
const mgr = ...    // vs manager
const accCnt = ... // vs accountCount
const tmp = ...    // vs tempFile or intermediateResult
```

---

## Functions — One Thing, One Level

### Single Responsibility for Functions
A function does one thing if you cannot extract a meaningful sub-function from it. If you can, it does more than one thing.

```typescript
// BAD: Does five things
async function processOrder(orderId: string, userId: string) {
  // 1. Fetch the order
  const order = await db.query('SELECT * FROM orders WHERE id = $1', [orderId]);
  if (!order) throw new Error('Order not found');
  
  // 2. Validate it
  if (order.user_id !== userId) throw new Error('Unauthorized');
  if (order.status !== 'pending') throw new Error('Cannot process');
  
  // 3. Charge the payment
  const charge = await stripe.charges.create({
    amount: order.total_cents,
    currency: 'usd',
    customer: order.stripe_customer_id
  });
  
  // 4. Update order status
  await db.query('UPDATE orders SET status = $1 WHERE id = $2', ['paid', orderId]);
  
  // 5. Send email
  await sendgrid.send({
    to: order.user_email,
    subject: 'Order confirmed',
    html: `<p>Your order ${orderId} is confirmed.</p>`
  });
}

// GOOD: Each function does one thing at one level of abstraction
async function processOrder(orderId: string, userId: string) {
  const order = await fetchOrder(orderId);
  validateOrderAccess(order, userId);
  const charge = await chargeCustomer(order);
  await markOrderAsPaid(orderId, charge.id);
  await sendOrderConfirmation(order);
}

async function fetchOrder(orderId: string): Promise<Order> {
  const order = await orderRepository.findById(orderId);
  if (!order) throw new NotFoundError(`Order ${orderId} not found`);
  return order;
}

function validateOrderAccess(order: Order, userId: string): void {
  if (order.userId !== userId) throw new ForbiddenError('Access denied');
  if (order.status !== 'pending') throw new ConflictError('Order cannot be processed');
}
```

### Limit parameters
```typescript
// BAD: Too many positional parameters — easy to pass in wrong order
function createUser(name: string, email: string, role: string, 
                    isActive: boolean, plan: string, orgId: string) { }

// GOOD: Named parameters via object
interface CreateUserParams {
  name: string;
  email: string;
  role: 'admin' | 'member' | 'viewer';
  isActive?: boolean;  // clear which are optional
  plan: 'free' | 'pro' | 'enterprise';
  orgId: string;
}

function createUser(params: CreateUserParams) { }

// Calling code is self-documenting
createUser({
  name: 'Alice',
  email: 'alice@example.com',
  role: 'admin',
  plan: 'pro',
  orgId: 'org_123'
});
```

---

## SOLID Principles — Practical Application

### S — Single Responsibility Principle
A class should have one reason to change. "Reason to change" = the stakeholder whose requirements drive changes.

```typescript
// VIOLATION: UserService has THREE reasons to change
// (auth team changes, notification team changes, billing team changes)
class UserService {
  async register(email: string, password: string) {
    const hash = await bcrypt.hash(password, 10); // Auth concern
    const user = await this.db.create({ email, hash });
    await this.mailer.send(email, 'Welcome!');     // Notification concern
    await this.billing.createFreeAccount(user.id); // Billing concern
    return user;
  }
}

// COMPLIANT: Each class has one reason to change
class UserRegistrationService {
  constructor(
    private users: UserRepository,
    private auth: AuthService,
    private events: EventBus
  ) {}

  async register(email: string, password: string): Promise<User> {
    const passwordHash = await this.auth.hashPassword(password);
    const user = await this.users.create({ email, passwordHash });
    await this.events.emit('user.registered', { userId: user.id, email });
    return user;
  }
}
// AuthService owns auth logic (one reason to change)
// NotificationService listens to user.registered (one reason to change)
// BillingService listens to user.registered (one reason to change)
```

### O — Open/Closed Principle
Open for extension, closed for modification. Add behavior by adding code, not by changing existing code.

```typescript
// VIOLATION: Must modify this function every time a new export format is added
function exportReport(data: Report, format: string): Buffer {
  if (format === 'pdf') { /* PDF code */ }
  if (format === 'csv') { /* CSV code */ }
  if (format === 'xlsx') { /* Excel code */ }
  // Adding JSON means modifying this function — risk to existing formats
}

// COMPLIANT: Add new format = add new class, zero modification to existing
interface ReportExporter {
  export(report: Report): Buffer;
}

class PdfExporter implements ReportExporter { ... }
class CsvExporter implements ReportExporter { ... }
class XlsxExporter implements ReportExporter { ... }

const exporters = new Map<string, ReportExporter>([
  ['pdf', new PdfExporter()],
  ['csv', new CsvExporter()],
]);

// Adding JSON:
exporters.set('json', new JsonExporter()); // No existing code touched
```

### L — Liskov Substitution Principle
Subtypes must be substitutable for their base types without breaking correctness.

```typescript
// VIOLATION: Square "is-a" Rectangle, but breaks substitution
class Rectangle {
  setWidth(w: number)  { this.width = w; }
  setHeight(h: number) { this.height = h; }
  area() { return this.width * this.height; }
}

class Square extends Rectangle {
  setWidth(w: number)  { this.width = this.height = w; } // Breaks Rectangle contract!
  setHeight(h: number) { this.width = this.height = h; }
}

function scaleToTwiceHeight(rect: Rectangle) {
  const origWidth = rect.width;
  rect.setHeight(rect.height * 2);
  // Expects: area = origWidth * newHeight. With Square: WRONG
}

// COMPLIANT: Don't inherit — model differently
interface Shape { area(): number; }
class Rectangle implements Shape { ... }
class Square implements Shape { ... }  // Separate class, same interface
```

### I — Interface Segregation Principle
No client should be forced to depend on interfaces it doesn't use.

```typescript
// VIOLATION: Fat interface forces all implementors to implement everything
interface Worker {
  work(): void;
  eat(): void;
  sleep(): void;
}

class RobotWorker implements Worker {
  work() { /* does work */ }
  eat() { throw new Error('Robots do not eat'); }  // Forced to implement
  sleep() { throw new Error('Robots do not sleep'); }
}

// COMPLIANT: Segregated interfaces
interface Workable { work(): void; }
interface Eatable  { eat(): void; }
interface Sleepable { sleep(): void; }

class HumanWorker implements Workable, Eatable, Sleepable { ... }
class RobotWorker implements Workable { ... } // Only what it needs
```

### D — Dependency Inversion Principle
High-level modules should not depend on low-level modules. Both should depend on abstractions.

```typescript
// VIOLATION: OrderService directly imports a specific DB implementation
import { PostgresOrderRepository } from './postgresOrderRepository';

class OrderService {
  private repo = new PostgresOrderRepository(); // Hardwired to Postgres
  // Untestable without a database. Swapping to MySQL requires code change.
}

// COMPLIANT: Depend on abstraction, inject the implementation
interface OrderRepository {
  findById(id: string): Promise<Order | null>;
  save(order: Order): Promise<Order>;
}

class OrderService {
  constructor(private repo: OrderRepository) {} // Depends on the interface

  async getOrder(id: string) {
    return this.repo.findById(id);
  }
}

// Production: inject Postgres
const service = new OrderService(new PostgresOrderRepository(pool));

// Test: inject in-memory
const service = new OrderService(new InMemoryOrderRepository());
```

---

## Code Smells Reference

```
SMELL: Long Function (> 20-30 lines)
FIX: Extract sub-functions with descriptive names

SMELL: Long Parameter List (> 3-4 params)
FIX: Group related params into a parameter object

SMELL: Comments explaining WHAT the code does
FIX: Rename so the code explains itself; use comments for WHY

SMELL: Duplicate code (copy-paste)
FIX: Extract to a shared function or class

SMELL: Dead code (commented out, unused variables)
FIX: Delete it. Git remembers.

SMELL: Magic numbers and strings
FIX: const ONE_HOUR_MS = 3600_000; const MAX_RETRIES = 3;

SMELL: Boolean parameters (createUser(email, true, false))
FIX: Use named options object or separate functions

SMELL: Deep nesting (> 3 levels of if/loop)
FIX: Extract functions; use early returns to flatten

SMELL: God class (does everything)
FIX: Split by responsibility; look for clusters of fields used together

SMELL: Feature envy (method uses another class's data more than its own)
FIX: Move the method to the class whose data it uses most
```

---

## DRY, KISS, YAGNI

```
DRY — Don't Repeat Yourself
The rule is about KNOWLEDGE duplication, not text duplication.
Two similar-looking functions that represent different business concepts are NOT DRY violations.
Premature DRY (wrong abstraction) is worse than duplication.
Rule: Wait for the third duplication before abstracting.

KISS — Keep It Simple, Stupid
Every line of code is a liability. Simpler code has fewer bugs.
The question is always: "Is there a simpler way to express this?"
Clever code that requires reading twice is not clever — it's a bug waiting to happen.

YAGNI — You Aren't Gonna Need It
Don't build features for imagined future requirements.
Add the abstraction when you need it, not before.
"We might need this to be configurable" is almost always wrong.
The cost of adding flexibility you don't need today is:
  more code, more complexity, more maintenance, more bugs.
```

---

## Clean Code Review Checklist

```
Naming:
☐ Every name expresses intent without a comment?
☐ No noise words (data, info, manager, helper, util)?
☐ Boolean variables are predicates (isX, hasX, canX)?
☐ Function names are verbs describing what they DO?

Functions:
☐ Each function does ONE thing at ONE level of abstraction?
☐ Functions have ≤ 3-4 parameters (or a parameter object)?
☐ No boolean flag parameters?
☐ No output arguments (functions return; they don't modify passed objects)?

Structure:
☐ No duplication of knowledge (not just text)?
☐ No magic numbers or strings (named constants instead)?
☐ No dead code or commented-out code?
☐ No deep nesting (prefer early returns)?

Comments:
☐ Comments explain WHY, not WHAT?
☐ No comments that restate what the code already says?
☐ No commented-out code?
```
