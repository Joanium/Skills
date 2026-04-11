---
name: Java Records & Sealed Classes
trigger: java record, sealed class, sealed interface, permits, record class, java 16, java 17, immutable data class, data transfer object record, pattern matching, java modern features, value object java
description: Use Java's modern type system features — records for immutable data carriers and sealed classes for exhaustive type hierarchies. Covers syntax, customization, pattern matching, and when to use each.
---

# ROLE
You are a senior Java engineer. Your job is to help developers use modern Java (16+) type features correctly. Records replace boilerplate DTOs. Sealed classes make type hierarchies explicit and safe. Together they enable expressive, safe domain modeling.

# RECORDS — IMMUTABLE DATA CARRIERS (Java 16+)

## Basics
```java
// Record — one line replaces ~50 lines of boilerplate
public record User(Long id, String name, String email) {}

// Compiler generates automatically:
// - private final fields (id, name, email)
// - canonical constructor
// - getters: id(), name(), email()  (NOT getId() — no "get" prefix)
// - equals() based on all components
// - hashCode() based on all components
// - toString()  e.g. "User[id=1, name=Alice, email=alice@ex.com]"

// Usage
User user = new User(1L, "Alice", "alice@ex.com");
user.id();     // 1L
user.name();   // "Alice"
user.email();  // "alice@ex.com"
```

## Customizing Records
```java
public record CreateUserRequest(String name, String email, int age) {

    // Compact canonical constructor — validate on creation
    public CreateUserRequest {
        Objects.requireNonNull(name, "name must not be null");
        name  = name.trim();           // can normalize here
        email = email.toLowerCase();   // normalize
        if (age < 0 || age > 150) throw new IllegalArgumentException("Invalid age: " + age);
    }

    // Additional methods
    public boolean isAdult() {
        return age >= 18;
    }

    // Static factory
    public static CreateUserRequest of(String name, String email) {
        return new CreateUserRequest(name, email, 0);
    }
}
```

## Records as DTOs — Ideal Pattern
```java
// Request DTO (replaces POJO + Lombok)
public record CreateOrderRequest(
    @NotNull String userId,
    @NotNull String productId,
    @Min(1) int quantity,
    String promoCode        // nullable
) {}

// Response DTO
public record OrderResponse(
    String orderId,
    String status,
    BigDecimal total,
    LocalDateTime createdAt
) {}

// Service method
public OrderResponse placeOrder(CreateOrderRequest request) {
    Order order = orderService.create(request);
    return new OrderResponse(order.getId(), order.getStatus().name(),
                             order.getTotal(), order.getCreatedAt());
}
```

## Nested Records (Common for Complex Responses)
```java
public record UserProfile(
    Long id,
    String name,
    Address address,
    List<String> roles
) {
    public record Address(String street, String city, String country) {}
}

UserProfile.Address addr = new UserProfile.Address("123 Main St", "Chennai", "India");
UserProfile profile = new UserProfile(1L, "Joel", addr, List.of("ADMIN", "USER"));
```

## Records with Generics
```java
public record Page<T>(List<T> content, int page, int size, long totalElements) {
    public int totalPages() {
        return size == 0 ? 0 : (int) Math.ceil((double) totalElements / size);
    }
}

Page<User> result = new Page<>(users, 0, 20, 100L);
```

## What Records CANNOT Do
```java
// ✗ Records cannot extend a class (they implicitly extend Record)
public record User(String name) extends BaseEntity {}  // compile error

// ✗ Record fields cannot be mutable (no setters, all final)
user.name = "Bob";  // compile error

// ✗ Records cannot declare instance fields outside the constructor
public record User(String name) {
    private String nickname = "nick";  // ✗ compile error
}

// ✓ Records CAN implement interfaces
public record Point(int x, int y) implements Comparable<Point> {
    @Override
    public int compareTo(Point other) {
        return Integer.compare(this.x, other.x);
    }
}
```

# SEALED CLASSES — CONTROLLED INHERITANCE (Java 17+)

## Basics
```java
// Sealed class — only listed classes can extend it
public sealed class Shape permits Circle, Rectangle, Triangle {}

public final class Circle    extends Shape { double radius; }
public final class Rectangle extends Shape { double width, height; }
public non-sealed class Triangle extends Shape { }  // Triangle can be extended freely

// Permitted subclass must be in same package (or same file for unnamed module)

// Options for subclass:
// final      → no further extension
// sealed     → restrict extension further
// non-sealed → allow free extension (opt out of sealing)
```

## Sealed Interfaces
```java
// Sealed interface — defines a closed set of implementations
public sealed interface Result<T> permits Result.Success, Result.Failure {

    record Success<T>(T value) implements Result<T> {}
    record Failure<T>(String error, Exception cause) implements Result<T> {}
}

// Usage
Result<User> result = userService.findUser(id);
```

## Pattern Matching with Sealed Classes — switch (Java 21)
```java
// Exhaustive switch — compiler knows all subtypes of Shape
double area = switch (shape) {
    case Circle    c -> Math.PI * c.radius() * c.radius();
    case Rectangle r -> r.width() * r.height();
    case Triangle  t -> calculateTriangleArea(t);
    // No default needed — compiler verifies all cases are covered
};

// With guards (Java 21 pattern matching)
String describe = switch (shape) {
    case Circle c when c.radius() > 100 -> "Large circle";
    case Circle c                       -> "Small circle";
    case Rectangle r when r.width() == r.height() -> "Square";
    case Rectangle r                    -> "Rectangle";
    case Triangle t                     -> "Triangle";
};
```

## Result / Either Pattern — Sealed + Records
```java
// Replace exception-based control flow with typed results
public sealed interface PaymentResult permits PaymentResult.Success, PaymentResult.Failure {
    record Success(String transactionId, BigDecimal charged) implements PaymentResult {}
    record Failure(String code, String message) implements PaymentResult {}
}

// In service
public PaymentResult processPayment(PaymentRequest request) {
    try {
        String txId = gateway.charge(request.amount(), request.card());
        return new PaymentResult.Success(txId, request.amount());
    } catch (CardDeclinedException e) {
        return new PaymentResult.Failure("DECLINED", e.getMessage());
    }
}

// In caller — forced to handle both cases
PaymentResult result = paymentService.processPayment(request);
switch (result) {
    case PaymentResult.Success s -> log.info("Charged {}", s.transactionId());
    case PaymentResult.Failure f -> log.warn("Payment failed: {}", f.message());
}
```

# RECORDS vs LOMBOK vs PLAIN POJO
```
                  Record    Lombok @Value  POJO + boilerplate
Immutable           ✓           ✓               manual
Concise             ✓           ✓               ✗
Extends class       ✗           ✓               ✓
Mutable fields      ✗           ✗               ✓
Pattern matching    ✓           ✗               ✗
Java version        16+         Any             Any
JSON (Jackson)      ✓*          ✓               ✓
JPA entity          ✗           ✓               ✓

* Jackson needs @JsonProperty on record components or constructor config

RULE:
  DTOs, request/response objects, value objects → Records
  JPA entities (mutable, proxied by Hibernate)  → Lombok @Data / POJO
  Domain objects needing inheritance            → Regular class + Lombok
```

# BEST PRACTICES CHECKLIST
```
[ ] Use records for all DTOs — request objects, response objects, value objects
[ ] Validate in the compact constructor — records are the right place for invariants
[ ] Use sealed interfaces for closed type hierarchies (status, result types)
[ ] Pair sealed types with switch expressions for exhaustive, compile-checked handling
[ ] Use Result<T> (sealed record) instead of checked exceptions for expected failures
[ ] Records work with Jackson — add @JsonProperty if Jackson can't match constructor params
[ ] Don't use records as JPA entities — Hibernate needs mutable, proxiable objects
[ ] Keep records small — if a record needs a lot of logic, it might be a class
[ ] Records are immutable by design — never try to work around this with static mutable state
[ ] Use List.copyOf() in record constructor for defensive copying of collection components
```
