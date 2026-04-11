---
name: Java Logging
trigger: java logging, slf4j, logback, log4j, logger, log levels, logging configuration, java log, structured logging, log format, logback.xml, logging best practices, mdc, java logs
description: Add effective, structured logging to Java applications using SLF4J and Logback. Covers log levels, SLF4J API, Logback configuration, MDC for request tracing, and what to log vs. not log.
---

# ROLE
You are a senior Java engineer. Your job is to help developers add logging that actually helps — clear, structured, and at the right level. Bad logging drowns signal in noise or hides failures completely.

# CORE PRINCIPLES
```
USE SLF4J API:     Always log through SLF4J — swap implementations without code changes
PARAMETERIZE:      Never concatenate strings in log calls — use {} placeholders
RIGHT LEVEL:       Use the right level — don't log everything at INFO
INCLUDE CONTEXT:   Log IDs and values — "failed" is useless, "orderId=123 failed" is not
LOG EXCEPTIONS:    Always pass Throwable as last argument — never just e.getMessage()
```

# DEPENDENCY SETUP
```xml
<!-- SLF4J API + Logback implementation (standard for Spring Boot) -->
<dependency>
    <groupId>ch.qos.logback</groupId>
    <artifactId>logback-classic</artifactId>
</dependency>

<!-- Spring Boot includes these automatically via spring-boot-starter -->
<!-- For non-Spring projects, add both: -->
<dependency>
    <groupId>org.slf4j</groupId>
    <artifactId>slf4j-api</artifactId>
    <version>2.0.9</version>
</dependency>
<dependency>
    <groupId>ch.qos.logback</groupId>
    <artifactId>logback-classic</artifactId>
    <version>1.4.14</version>
</dependency>
```

# LOGGER SETUP
```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class UserService {
    // One logger per class — static final, named after the class
    private static final Logger log = LoggerFactory.getLogger(UserService.class);

    // With Lombok — @Slf4j generates: private static final Logger log = ...
    // @Slf4j
    // public class UserService { ... }
}
```

# LOG LEVELS — WHEN TO USE EACH
```
TRACE   → Fine-grained step-by-step execution details (disabled in prod)
          "Entering method processPayment with orderId={}"

DEBUG   → Diagnostic info useful during development and debugging
          "Cache miss for userId={}, fetching from DB"
          "Query returned {} rows in {}ms"

INFO    → Normal significant business events — the narrative of what the app did
          "User {} created successfully"
          "Order {} placed, total={}"
          "Service started on port {}"

WARN    → Unexpected but recoverable — something to investigate but not alert on
          "Retry attempt {} of {} for paymentId={}"
          "Deprecated API called by client {}"
          "Rate limit approaching for userId={}"

ERROR   → Failure that needs human attention — always include exception
          "Failed to process payment for orderId={}, userId={}"
          "Database connection lost"
```

# PARAMETERIZED LOGGING — CRITICAL
```java
// BAD — string concatenation always runs, even when log level is disabled
log.debug("Processing order: " + orderId + " for user: " + userId);  // ✗

// GOOD — {} placeholder, string only built if level is enabled
log.debug("Processing order: {} for user: {}", orderId, userId);    // ✓

// Exception — always the LAST argument (SLF4J handles it specially)
log.error("Failed to process order {}", orderId, e);   // ✓ full stack trace logged
log.error("Failed: " + e.getMessage());                 // ✗ no stack trace, no context

// Multiple values
log.info("Payment received: orderId={}, amount={}, currency={}", orderId, amount, currency);

// Conditional — when building the message itself is expensive
if (log.isDebugEnabled()) {
    log.debug("Detailed state: {}", expensiveToCompute());
}
```

# LOGBACK CONFIGURATION — logback-spring.xml
```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>

    <!-- Console appender -->
    <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>

    <!-- Rolling file appender -->
    <appender name="FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>logs/app.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <fileNamePattern>logs/app.%d{yyyy-MM-dd}.%i.gz</fileNamePattern>
            <timeBasedFileNamingAndTriggeringPolicy
                class="ch.qos.logback.core.rolling.SizeAndTimeBasedFNATP">
                <maxFileSize>100MB</maxFileSize>
            </timeBasedFileNamingAndTriggeringPolicy>
            <maxHistory>30</maxHistory>     <!-- keep 30 days -->
            <totalSizeCap>3GB</totalSizeCap>
        </rollingPolicy>
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} [%X{requestId}] - %msg%n</pattern>
        </encoder>
    </appender>

    <!-- Package-level config -->
    <logger name="com.myapp" level="DEBUG" />
    <logger name="org.hibernate.SQL" level="DEBUG" />
    <logger name="com.zaxxer.hikari" level="INFO" />

    <!-- Root logger -->
    <root level="INFO">
        <appender-ref ref="CONSOLE" />
        <appender-ref ref="FILE" />
    </root>

    <!-- Profile-based config (Spring) -->
    <springProfile name="prod">
        <root level="WARN">
            <appender-ref ref="FILE" />
        </root>
    </springProfile>

</configuration>
```

# application.yml — SPRING LOGGING
```yaml
logging:
  level:
    root: INFO
    com.myapp: DEBUG
    org.hibernate.SQL: DEBUG
    org.springframework.web: WARN
  file:
    name: logs/app.log
  pattern:
    console: "%d{HH:mm:ss.SSS} %-5level %logger{20} - %msg%n"
```

# MDC — MAPPED DIAGNOSTIC CONTEXT (REQUEST TRACING)
```java
// MDC attaches key-value pairs to the current thread's log context
// All log messages in the same request automatically include them

// In a filter or interceptor
import org.slf4j.MDC;

@Component
public class RequestLoggingFilter implements Filter {

    @Override
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)
            throws IOException, ServletException {

        String requestId = UUID.randomUUID().toString();
        MDC.put("requestId", requestId);
        MDC.put("userId", extractUserId((HttpServletRequest) req));

        try {
            chain.doFilter(req, res);
        } finally {
            MDC.clear();   // CRITICAL — always clear in finally, thread pool reuses threads
        }
    }
}

// Pattern includes %X{requestId} to print MDC value:
// 2024-01-15 10:30:00 INFO UserService [req-abc123] - User 42 created
```

# STRUCTURED / JSON LOGGING (PRODUCTION)
```xml
<!-- Logstash encoder for JSON output (ELK stack / Splunk / CloudWatch) -->
<dependency>
    <groupId>net.logstash.logback</groupId>
    <artifactId>logstash-logback-encoder</artifactId>
    <version>7.4</version>
</dependency>
```

```xml
<appender name="JSON" class="ch.qos.logback.core.ConsoleAppender">
    <encoder class="net.logstash.logback.encoder.LogstashEncoder">
        <includeMdcKeyName>requestId</includeMdcKeyName>
        <includeMdcKeyName>userId</includeMdcKeyName>
    </encoder>
</appender>
```

```json
// JSON log output — searchable in any log aggregation system
{
  "@timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "logger": "com.myapp.UserService",
  "message": "User 42 created",
  "requestId": "req-abc123",
  "userId": "42"
}
```

# WHAT NOT TO LOG
```
✗ Passwords, API keys, tokens — ever
✗ Full credit card numbers, SSNs, PII in plain text
✗ Entire request/response bodies in production (too large, may contain sensitive data)
✗ Stack traces at DEBUG level for expected business exceptions
✗ SUCCESS for every DB row read (volume kills disk and readability)
✗ Thread.sleep or loop iteration counters at INFO

✓ Business event milestones (created, updated, failed, retried)
✓ External API calls: URL, status code, duration (not body)
✓ Exceptions — full stack trace at ERROR, message at WARN
✓ Request start/end with duration at INFO or DEBUG
✓ Configuration on startup (which profile, which DB, which port)
```

# BEST PRACTICES CHECKLIST
```
[ ] Use SLF4J API — never Log4j or java.util.logging directly in application code
[ ] Declare logger as private static final, named after the class
[ ] Use {} placeholders — never string concatenation in log calls
[ ] Pass Throwable as last argument to get full stack traces
[ ] Set MDC requestId in every incoming request, clear in finally
[ ] Use DEBUG for development details, INFO for business events, ERROR for failures
[ ] Never log passwords, tokens, or PII
[ ] Use rolling file appenders with size and time limits in production
[ ] Use JSON/structured logging when shipping to log aggregation (ELK, Splunk)
[ ] Use @Slf4j (Lombok) to eliminate logger boilerplate
```
