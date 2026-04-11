---
name: Java Exception Handling
trigger: java exceptions, try catch finally, checked unchecked exception, custom exception, exception hierarchy, throw throws, exception handling best practices, java error handling, rethrow, multicatch, try with resources
description: Handle exceptions correctly in Java. Covers checked vs unchecked exceptions, custom exceptions, try-with-resources, exception chaining, and anti-patterns that silently swallow errors.
---

# ROLE
You are a senior Java engineer. Your job is to help developers write robust, informative exception handling. Bad exception handling is worse than no handling — swallowed exceptions turn bugs invisible.

# EXCEPTION HIERARCHY
```
Throwable
  ├── Error           → JVM-level failures (OutOfMemoryError, StackOverflowError)
  │                     Do NOT catch — you can't recover from these
  └── Exception
        ├── RuntimeException (Unchecked — NOT required to declare or catch)
        │     ├── NullPointerException
        │     ├── IllegalArgumentException
        │     ├── IllegalStateException
        │     ├── IndexOutOfBoundsException
        │     └── ... (your custom unchecked exceptions go here)
        └── IOException, SQLException, ... (Checked — MUST declare or catch)
              └── ... (your custom checked exceptions go here)
```

# CHECKED vs UNCHECKED
```
CHECKED   → Recoverable situations the caller should explicitly handle
            (FileNotFoundException, SQLException, ParseException)
            Force the caller to think about failure modes
            Declare with 'throws' or wrap in try-catch

UNCHECKED → Programming errors or unrecoverable states
            (NullPointerException, IllegalArgumentException)
            Should NOT be caught — fix the code instead
            Don't declare in method signatures

RULE: In modern Java (Spring etc.) — prefer UNCHECKED custom exceptions.
      Checked exceptions create annoying throws chains and often get swallowed.
```

# BASIC SYNTAX
```java
// try-catch-finally
try {
    riskyOperation();
} catch (IOException e) {
    log.error("IO error: {}", e.getMessage(), e);
    throw new ServiceException("Storage unavailable", e);  // wrap, don't swallow
} catch (SQLException e) {
    log.error("DB error", e);
    throw new DataAccessException("DB failed", e);
} finally {
    // ALWAYS runs — even if exception is thrown or return is called
    // Use for cleanup only — never throw from finally (hides original exception)
    cleanup();
}

// Multi-catch (Java 7+) — same handler for multiple types
try {
    process();
} catch (IOException | SQLException e) {
    log.error("External dependency error", e);
    throw new ServiceException("Dependency failure", e);
}
```

# TRY-WITH-RESOURCES — ALWAYS USE FOR CLOSEABLE
```java
// BAD — manual close, error-prone
Connection conn = null;
try {
    conn = dataSource.getConnection();
    // ... work ...
} catch (SQLException e) {
    throw new RuntimeException(e);
} finally {
    if (conn != null) {
        try { conn.close(); }           // ✗ verbose, easy to forget
        catch (SQLException ignore) {}
    }
}

// GOOD — try-with-resources (Java 7+)
// close() is called automatically, even if exception is thrown
try (Connection conn    = dataSource.getConnection();
     PreparedStatement ps = conn.prepareStatement(sql)) {

    ps.setString(1, userId);
    ResultSet rs = ps.executeQuery();
    // ...
} catch (SQLException e) {
    throw new DataAccessException("Query failed", e);
}

// Custom resource — implement AutoCloseable
public class FileProcessor implements AutoCloseable {
    @Override
    public void close() { /* cleanup */ }
}

try (FileProcessor fp = new FileProcessor("data.csv")) {
    fp.process();
}
```

# CUSTOM EXCEPTIONS
```java
// Base unchecked exception for your domain
public class AppException extends RuntimeException {
    private final String errorCode;

    public AppException(String errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
    }

    public AppException(String errorCode, String message, Throwable cause) {
        super(message, cause);     // ✓ always chain cause — preserves stack trace
        this.errorCode = errorCode;
    }

    public String getErrorCode() { return errorCode; }
}

// Specific exceptions extend base
public class ResourceNotFoundException extends AppException {
    public ResourceNotFoundException(String resource, Object id) {
        super("NOT_FOUND", resource + " with id " + id + " not found");
    }
}

public class BusinessRuleException extends AppException {
    public BusinessRuleException(String message) {
        super("BUSINESS_RULE_VIOLATION", message);
    }
}

// Usage
throw new ResourceNotFoundException("User", userId);
throw new BusinessRuleException("Cannot cancel a shipped order");
```

# EXCEPTION CHAINING — NEVER LOSE THE CAUSE
```java
// BAD — original cause is gone
try {
    Files.readAllBytes(path);
} catch (IOException e) {
    throw new ServiceException("Read failed");   // ✗ cause swallowed
}

// GOOD — chain the cause
try {
    Files.readAllBytes(path);
} catch (IOException e) {
    throw new ServiceException("Read failed", e);  // ✓ cause preserved
}

// BAD — wrapping loses type info
catch (IOException e) {
    throw new RuntimeException(e);   // ✗ — use a named exception
}
```

# THROWING — GUIDELINES
```java
// Throw at the right level
// LOW LEVEL: throw descriptive exception with context
public User findById(Long id) {
    return userRepo.findById(id)
        .orElseThrow(() -> new ResourceNotFoundException("User", id));
}

// Use IllegalArgumentException for bad input to public methods
public void setAge(int age) {
    if (age < 0 || age > 150)
        throw new IllegalArgumentException("Age must be 0-150, got: " + age);
}

// Use IllegalStateException for invalid object state
public void checkout() {
    if (items.isEmpty())
        throw new IllegalStateException("Cannot checkout an empty cart");
}

// Use UnsupportedOperationException for unimplemented optional operations
@Override
public void remove() {
    throw new UnsupportedOperationException("This iterator is read-only");
}
```

# ANTI-PATTERNS — NEVER DO THESE
```java
// 1 — Swallow exception silently
try { parse(input); } catch (Exception e) {}   // ✗ bug becomes invisible

// 2 — Catch Exception (too broad)
try { ... } catch (Exception e) { ... }        // ✗ catches NPE, OOM, everything

// 3 — Catch Throwable
try { ... } catch (Throwable t) { ... }        // ✗ catches Error — never recoverable

// 4 — Log AND rethrow (double logging)
catch (Exception e) {
    log.error("Error", e);     // logs here
    throw e;                   // logs again at caller — two identical stack traces
}
// RULE: either log OR rethrow — not both

// 5 — Use exceptions for control flow
try {
    return Integer.parseInt(s);
} catch (NumberFormatException e) {
    return -1;                 // ✗ exceptions are expensive — use Integer.parseInt check
}
// GOOD: if (s != null && s.matches("\\d+")) return Integer.parseInt(s);

// 6 — Throw from finally block
finally {
    conn.close();   // if close() throws, original exception is lost
}
// GOOD: catch and log close() errors silently inside finally
```

# LOGGING EXCEPTIONS CORRECTLY
```java
// Log with full stack trace — pass exception as last arg to SLF4J
log.error("Failed to process order {}", orderId, e);   // ✓ includes stack trace
log.error("Failed: " + e.getMessage());                 // ✗ no stack trace, string concat

// Log at the right level
log.warn(...)   // expected failure, degraded mode
log.error(...)  // unexpected failure, needs investigation
log.debug(...)  // low-level details (disable in prod)

// Include context in the message
log.error("Payment failed for orderId={}, userId={}", orderId, userId, e);  // ✓
log.error("Payment failed", e);   // ✗ no context to search logs
```

# BEST PRACTICES CHECKLIST
```
[ ] Always chain the cause when wrapping: throw new MyException("msg", cause)
[ ] Use try-with-resources for all Closeable (streams, connections, readers)
[ ] Create domain-specific unchecked exceptions — don't throw raw RuntimeException
[ ] Either log or rethrow an exception — never both
[ ] Never swallow exceptions silently — at minimum log at warn level
[ ] Don't catch Exception or Throwable — catch the specific type you can handle
[ ] Throw IllegalArgumentException for bad method arguments (with the bad value in message)
[ ] Throw IllegalStateException for invalid object state
[ ] Include context (IDs, values) in exception messages — make them searchable
[ ] Use @ControllerAdvice / @RestControllerAdvice in Spring for centralized error handling
```
