---
name: Refactoring
trigger: refactor this, clean up code, improve code quality, code smell, technical debt, restructure, extract function, simplify, make this readable, this code is messy, hard to understand, spaghetti code
description: Systematically identify and eliminate code smells, apply refactoring patterns, and improve code quality without breaking behavior. Covers the full refactoring catalog with before/after examples in JS/TS and Python.
---

# ROLE
You are a software craftsperson. Your job is to make code cleaner, more readable, and more maintainable — without changing observable behavior. Refactoring is a discipline: small steps, tests verify nothing broke, commit often.

# GOLDEN RULES
```
NEVER REFACTOR WITHOUT TESTS — if tests don't exist, write them first
SMALL STEPS — one refactoring at a time, run tests after each
NEVER MIX REFACTORING WITH FEATURE WORK — separate commits
MAKE THE CHANGE EASY, THEN MAKE THE EASY CHANGE — Kent Beck
THE BOY SCOUT RULE — leave code cleaner than you found it
```

# CODE SMELLS — CATALOG AND FIXES

## 1. Long Function (God Function)
```typescript
// SMELL: one function doing 5 different things
async function processOrder(orderId: string) {
  const order = await db.query(`SELECT * FROM orders WHERE id = ?`, [orderId])
  if (!order) throw new Error('Order not found')
  
  // validate inventory
  for (const item of order.items) {
    const stock = await db.query(`SELECT stock FROM products WHERE id = ?`, [item.productId])
    if (stock < item.quantity) throw new Error(`Insufficient stock for ${item.productId}`)
  }
  
  // calculate total
  let total = 0
  for (const item of order.items) {
    total += item.price * item.quantity
  }
  if (order.coupon) {
    total = total * (1 - order.coupon.discount)
  }
  
  // charge payment
  const charge = await stripe.charges.create({ amount: total * 100, currency: 'usd', ... })
  
  // send email
  await sendgrid.send({ to: order.user.email, subject: 'Order confirmed', ... })
  
  return { success: true, chargeId: charge.id }
}

// REFACTORED: each function has one job
async function processOrder(orderId: string) {
  const order = await getOrder(orderId)
  await validateInventory(order.items)
  const total = calculateOrderTotal(order)
  const charge = await chargePayment(order.user, total)
  await sendOrderConfirmation(order.user, order)
  return { success: true, chargeId: charge.id }
}

async function validateInventory(items: OrderItem[]): Promise<void> { ... }
function calculateOrderTotal(order: Order): number { ... }
async function chargePayment(user: User, amount: number): Promise<Charge> { ... }
async function sendOrderConfirmation(user: User, order: Order): Promise<void> { ... }
```

## 2. Long Parameter List (> 3 params)
```typescript
// SMELL: function takes 6 parameters — caller can't remember order
function createUser(name: string, email: string, role: string, plan: string, sendWelcome: boolean, trialDays: number) { ... }

// Every call is unreadable:
createUser('Alice', 'alice@ex.com', 'admin', 'pro', true, 14)  // what does 14 mean?

// FIX: introduce parameter object
interface CreateUserOptions {
  name: string
  email: string
  role: 'admin' | 'member' | 'viewer'
  plan: 'free' | 'pro' | 'enterprise'
  sendWelcomeEmail?: boolean  // optional with default
  trialDays?: number
}

function createUser(options: CreateUserOptions) { ... }

// Call is now self-documenting:
createUser({ name: 'Alice', email: 'alice@ex.com', role: 'admin', plan: 'pro', trialDays: 14 })
```

## 3. Duplicate Code (DRY Violation)
```python
# SMELL: same logic in two places — one will be updated, one won't

def calculate_contractor_pay(hours, rate):
    subtotal = hours * rate
    if subtotal > 10000:
        tax = subtotal * 0.3
    else:
        tax = subtotal * 0.2
    return subtotal - tax

def calculate_employee_pay(hours, rate, bonus):
    subtotal = hours * rate + bonus
    if subtotal > 10000:
        tax = subtotal * 0.3
    else:
        tax = subtotal * 0.2   # exact same tax logic — DRY violation
    return subtotal - tax

# FIX: extract the shared logic
def calculate_tax(amount: float) -> float:
    rate = 0.3 if amount > 10_000 else 0.2
    return amount * rate

def calculate_contractor_pay(hours: float, rate: float) -> float:
    subtotal = hours * rate
    return subtotal - calculate_tax(subtotal)

def calculate_employee_pay(hours: float, rate: float, bonus: float) -> float:
    subtotal = hours * rate + bonus
    return subtotal - calculate_tax(subtotal)
```

## 4. Magic Numbers / Magic Strings
```typescript
// SMELL: what does 86400 mean? what is 'adm'?
if (lastLogin < Date.now() - 86400000) { ... }
if (user.role === 'adm') { ... }
setTimeout(refresh, 300000)

// FIX: named constants
const ONE_DAY_MS = 24 * 60 * 60 * 1000
const REFRESH_INTERVAL_MS = 5 * 60 * 1000

const UserRole = {
  ADMIN: 'adm',
  MEMBER: 'mem',
  VIEWER: 'viw',
} as const

if (lastLogin < Date.now() - ONE_DAY_MS) { ... }
if (user.role === UserRole.ADMIN) { ... }
setTimeout(refresh, REFRESH_INTERVAL_MS)
```

## 5. Deep Nesting (Arrow Anti-Pattern)
```javascript
// SMELL: 4 levels of indentation — hard to follow the happy path
function processPayment(order) {
  if (order) {
    if (order.items.length > 0) {
      if (order.user.isActive) {
        if (order.payment.isValid) {
          // happy path buried 4 levels deep
          return charge(order)
        } else {
          return { error: 'Invalid payment' }
        }
      } else {
        return { error: 'Inactive user' }
      }
    } else {
      return { error: 'Empty order' }
    }
  } else {
    return { error: 'No order' }
  }
}

// FIX: early returns (guard clauses) — invert the conditions
function processPayment(order) {
  if (!order)                  return { error: 'No order' }
  if (!order.items.length)     return { error: 'Empty order' }
  if (!order.user.isActive)    return { error: 'Inactive user' }
  if (!order.payment.isValid)  return { error: 'Invalid payment' }

  // happy path is clean and obvious
  return charge(order)
}
```

## 6. Feature Envy (Method Using Another Class's Data Too Much)
```python
# SMELL: OrderPrinter knows too much about Order internals
class OrderPrinter:
    def print_summary(self, order):
        print(f"Order #{order.id}")
        print(f"Customer: {order.customer.first_name} {order.customer.last_name}")
        discount = order.coupon.discount if order.coupon else 0
        subtotal = sum(item.price * item.qty for item in order.items)
        total = subtotal * (1 - discount)
        print(f"Total: ${total:.2f}")

# FIX: move behavior to the class that owns the data
class Order:
    def get_summary(self) -> str:
        return (
            f"Order #{self.id}\n"
            f"Customer: {self.customer.full_name}\n"
            f"Total: ${self.total:.2f}"
        )

    @property
    def total(self) -> float:
        discount = self.coupon.discount if self.coupon else 0
        return sum(i.price * i.qty for i in self.items) * (1 - discount)

class OrderPrinter:
    def print_summary(self, order):
        print(order.get_summary())  # now just delegates
```

## 7. Primitive Obsession
```typescript
// SMELL: using primitives for concepts that have behavior
function sendEmail(email: string, subject: string, body: string) {
  if (!email.includes('@')) throw new Error('Invalid email')
  // ...
}

// Validation repeated everywhere email is used
// FIX: wrap primitives in value objects
class Email {
  private readonly value: string

  constructor(raw: string) {
    if (!raw.includes('@') || !raw.includes('.')) {
      throw new Error(`Invalid email: ${raw}`)
    }
    this.value = raw.toLowerCase().trim()
  }

  toString() { return this.value }
  getDomain() { return this.value.split('@')[1] }
}

function sendEmail(to: Email, subject: string, body: string) {
  // Email is guaranteed valid by construction — no validation needed here
}
```

## 8. Boolean Trap
```typescript
// SMELL: what does true mean here?
updateUser(userId, true, false, true)  // impossible to understand at call site

// FIX: named options object or named parameters
updateUser(userId, {
  sendNotification: true,
  forceLogout: false,
  updateTimestamp: true
})
```

## 9. Data Clumps
```python
# SMELL: same 3 fields always appear together — they want to be a class
def create_shipment(street, city, postal_code, weight):
    ...
def calculate_shipping_cost(street, city, postal_code):
    ...
def validate_address(street, city, postal_code):
    ...

# FIX: extract the clump into a class
@dataclass
class Address:
    street: str
    city: str
    postal_code: str

    def validate(self) -> bool: ...
    def to_label(self) -> str: ...

def create_shipment(destination: Address, weight: float): ...
def calculate_shipping_cost(destination: Address) -> float: ...
```

## 10. Switch/if-else on Type (Replace with Polymorphism)
```typescript
// SMELL: adding a new payment type means editing this function
function processPayment(payment: Payment) {
  switch (payment.type) {
    case 'credit_card':
      return chargeCreditCard(payment)
    case 'paypal':
      return chargePaypal(payment)
    case 'crypto':
      return chargeCrypto(payment)
    default:
      throw new Error(`Unknown payment type: ${payment.type}`)
  }
}

// FIX: polymorphism — each type knows how to process itself
interface Payment {
  process(): Promise<ChargeResult>
}

class CreditCardPayment implements Payment {
  async process() { return chargeCreditCard(this) }
}
class PaypalPayment implements Payment {
  async process() { return chargePaypal(this) }
}

// Now adding a new type doesn't touch existing code (Open/Closed Principle)
async function processPayment(payment: Payment) {
  return payment.process()
}
```

# REFACTORING SEQUENCE
```
Step 1: UNDERSTAND — read the code, understand what it does, check test coverage
Step 2: TEST — if tests are absent or weak, write them now
Step 3: IDENTIFY — pick ONE smell to fix, not all at once
Step 4: REFACTOR — apply the minimum change to address that smell
Step 5: VERIFY — run tests, confirm all pass
Step 6: COMMIT — small, focused commit with a clear message
Step 7: REPEAT — pick the next smell

Message format: "refactor: extract calculateTax from processPayment"
NOT: "refactor: clean up processPayment" (too vague)
NOT: "refactor + fix bug + add feature" (too much)
```
