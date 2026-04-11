---
name: Java Clean Code
trigger: java clean code, naming conventions, method length, code smells, refactoring, solid principles, java best practices, readable code, code quality, dry principle, single responsibility, code review java
description: Write Java code that is readable, maintainable, and easy to change. Covers naming, method design, SOLID principles, common code smells, and refactoring patterns.
---

# ROLE
You are a senior Java engineer and code reviewer. Your job is to help developers write code that a colleague can understand and modify six months later. Code is written once and read hundreds of times — clarity is not optional.

# CORE PRINCIPLES
```
READABLE FIRST:   Code is communication — optimize for the reader, not the writer
SMALL UNITS:      Functions do ONE thing. Classes have ONE reason to change.
NAMES AS DOCS:    A good name eliminates the need for a comment
DRY:              Don't Repeat Yourself — duplication is the root of most maintenance pain
FAIL FAST:        Validate early, return early — don't nest happy paths
```

# NAMING CONVENTIONS

## Classes
```java
// Nouns or noun phrases — what it IS
UserService, OrderRepository, PaymentProcessor, EmailMessage
// NOT: ProcessUsers, HandleOrders, DoPayment (verbs = wrong)

// Specific — name should narrow the concept
CustomerEmailNotificationService  ✓
EmailService                      (too broad — emails what?)

// No meaningless suffixes
UserData, UserInfo, UserObject, UserThing  ✗
User                                       ✓ (if it IS the domain object)
```

## Methods
```java
// Verbs or verb phrases — what it DOES
findById(), calculateTotal(), sendWelcomeEmail(), isEligibleForDiscount()
// NOT: user(), result(), data()

// Consistent vocabulary — pick one word per concept, use it everywhere
fetch vs get vs retrieve vs find  → pick one, use it everywhere
create vs make vs build vs new    → pick one

// Boolean methods — is/has/can/should prefix
isActive(), hasPermission(), canEdit(), shouldSendNotification()
// NOT: active(), permission() — ambiguous as boolean

// Don't encode the type in the name
String nameString;  ✗  →  String name;  ✓
List<User> userList;  ✗  →  List<User> users;  ✓
```

## Variables & Constants
```java
// Meaningful, pronounceable, searchable
int d;                          ✗  →  int daysSinceLastLogin;  ✓
double temp;                    ✗  →  double temperatureCelsius;  ✓
String e;                       ✗  →  String email;  ✓

// Constants — SCREAMING_SNAKE_CASE
static final int MAX_RETRY_ATTEMPTS   = 3;
static final String DEFAULT_TIMEZONE  = "UTC";
static final Duration SESSION_TIMEOUT = Duration.ofMinutes(30);

// Loop variable exception — i, j, k OK in tight loops
for (int i = 0; i < items.size(); i++) { ... }
```

# METHOD DESIGN

## Do One Thing
```java
// BAD — validates, saves, sends email, logs — four responsibilities
public User createUser(String name, String email, String password) {
    if (email == null || !email.contains("@")) throw new IllegalArgumentException(...);
    String hash = BCrypt.hash(password);
    User user = new User(name, email, hash);
    userRepo.save(user);
    emailService.sendWelcome(email);
    log.info("User created: {}", email);
    return user;
}

// GOOD — each method does one thing
public User createUser(CreateUserRequest request) {
    validate(request);
    User user = buildUser(request);
    userRepo.save(user);
    eventPublisher.publish(new UserCreatedEvent(user));
    return user;
}

private void validate(CreateUserRequest request) { ... }
private User buildUser(CreateUserRequest request) { ... }
```

## Argument Count
```java
// 0–2 args → fine
// 3 args    → acceptable but think if they belong together
// 4+ args   → introduce a parameter object

// BAD
public Order createOrder(String userId, String productId, int quantity,
                         String shippingAddress, String promoCode) { ... }

// GOOD — parameter object groups related args
public Order createOrder(CreateOrderRequest request) { ... }

public record CreateOrderRequest(
    String userId, String productId, int quantity,
    String shippingAddress, String promoCode
) {}
```

## Return Early — Avoid Deep Nesting
```java
// BAD — arrow anti-pattern (deeply nested)
public String processOrder(Order order) {
    if (order != null) {
        if (order.isValid()) {
            if (order.hasItems()) {
                if (inventory.available(order)) {
                    return fulfillOrder(order);
                }
            }
        }
    }
    return null;
}

// GOOD — guard clauses (return/throw early)
public String processOrder(Order order) {
    if (order == null)            throw new IllegalArgumentException("Order is null");
    if (!order.isValid())         throw new BusinessRuleException("Order is invalid");
    if (!order.hasItems())        throw new BusinessRuleException("Order has no items");
    if (!inventory.available(order)) throw new InsufficientInventoryException(order);

    return fulfillOrder(order);  // happy path at the bottom, unindented
}
```

# SOLID PRINCIPLES

## S — Single Responsibility
```java
// BAD — UserService does user logic, email, AND PDF generation
public class UserService {
    public void createUser(User u) { ... }
    public void sendWelcomeEmail(User u) { ... }   // ✗ not user service's job
    public byte[] generateUserReport(User u) { ... } // ✗ not user service's job
}

// GOOD — separate classes, separate concerns
public class UserService    { public void createUser(User u) { ... } }
public class EmailService   { public void sendWelcome(User u) { ... } }
public class ReportService  { public byte[] generateUserReport(User u) { ... } }
```

## O — Open/Closed
```java
// BAD — add payment type = modify existing code
public double calculateFee(String paymentType, double amount) {
    if (paymentType.equals("CARD"))   return amount * 0.02;
    if (paymentType.equals("PAYPAL")) return amount * 0.03;
    // ✗ adding CRYPTO means editing this method
}

// GOOD — open for extension via polymorphism
public interface PaymentProcessor {
    double calculateFee(double amount);
}
public class CardPaymentProcessor   implements PaymentProcessor { ... }
public class PaypalPaymentProcessor implements PaymentProcessor { ... }
public class CryptoPaymentProcessor implements PaymentProcessor { ... }
// Adding CRYPTO = new class, zero existing code changed
```

## L — Liskov Substitution
```java
// Subclass must be usable wherever superclass is used — no surprises
// BAD
class Rectangle { setWidth(int w); setHeight(int h); }
class Square extends Rectangle {
    @Override setWidth(int w)  { super.setWidth(w);  super.setHeight(w); }  // ✗ breaks Rectangle contract
    @Override setHeight(int h) { super.setWidth(h);  super.setHeight(h); }
}

// GOOD — don't extend when the behavior contract differs
// Shape <- Rectangle
// Shape <- Square
// (separate siblings, no inheritance)
```

## I — Interface Segregation
```java
// BAD — fat interface forces unnecessary methods
interface Worker {
    void work();
    void eat();    // robots don't eat — forced to implement no-op
    void sleep();  // robots don't sleep
}

// GOOD — small, focused interfaces
interface Workable  { void work(); }
interface Feedable  { void eat(); }
interface Restable  { void sleep(); }

class Human implements Workable, Feedable, Restable { ... }
class Robot implements Workable { ... }
```

## D — Dependency Inversion
```java
// BAD — high-level module depends on low-level concrete class
public class OrderService {
    private MySQLOrderRepository repo = new MySQLOrderRepository();  // ✗ concrete
}

// GOOD — depend on abstraction; inject the implementation
public class OrderService {
    private final OrderRepository repo;   // interface

    public OrderService(OrderRepository repo) { this.repo = repo; }
    // Spring injects MySQLOrderRepository or MockOrderRepository — OrderService doesn't care
}
```

# COMMON CODE SMELLS

## Long Method
```java
// If a method needs a comment header to explain a section — extract that section
// Rule of thumb: if it scrolls off the screen, it's too long
// Extract sub-steps into well-named private methods
```

## Primitive Obsession
```java
// BAD — primitives everywhere lose meaning
void transfer(String accountFrom, String accountTo, double amount) { }

// GOOD — value objects carry meaning and validation
void transfer(AccountId from, AccountId to, Money amount) { }

public record Money(BigDecimal amount, Currency currency) {
    public Money { if (amount.compareTo(BigDecimal.ZERO) < 0) throw new IllegalArgumentException(); }
}
```

## Magic Numbers / Strings
```java
// BAD
if (status == 3)  { ... }
if (type.equals("A")) { ... }

// GOOD — named constants or enums
if (status == OrderStatus.SHIPPED.code()) { ... }
if (type == AccountType.ADMIN) { ... }
```

## Comments That Explain What (Not Why)
```java
// BAD — comment restates the code
i++;  // increment i

// BAD — comment compensates for bad naming
// check if user can see content
if (u.r >= 3 && u.s && !u.b) { ... }

// GOOD — good name replaces comment
if (user.hasViewPermission()) { ... }

// GOOD — comment explains WHY (business rule, non-obvious decision)
// Subtract 1 day to account for same-day delivery window cut-off at 11:59 PM UTC
Instant cutoff = Instant.now().minus(1, ChronoUnit.DAYS);
```

# BEST PRACTICES CHECKLIST
```
[ ] Name classes as nouns, methods as verbs — be specific, not generic
[ ] Methods should do ONE thing — if you can't name it precisely, split it
[ ] Use guard clauses (early return/throw) instead of nested if blocks
[ ] Limit method parameters to 3 or fewer — use parameter objects beyond that
[ ] No magic numbers or strings — name them as constants or enums
[ ] Depend on interfaces, not concrete implementations
[ ] Replace comments that explain WHAT with better names
[ ] Keep comments for WHY — non-obvious business rules, workarounds, constraints
[ ] Delete dead code — don't comment it out and leave it (git tracks history)
[ ] Run a code review checklist: names, single responsibility, no duplication, no magic values
```
