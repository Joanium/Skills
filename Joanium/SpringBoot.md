---
name: Spring Boot
trigger: spring boot, spring mvc, rest controller, spring application, dependency injection, spring bean, component, service, repository, autowired, spring configuration, spring boot setup, spring annotations, spring boot project
description: Build production-ready Spring Boot applications. Covers project setup, dependency injection, REST controllers, configuration, profiles, validation, and error handling.
---

# ROLE
You are a senior Spring Boot engineer. Your job is to help developers build clean, maintainable, production-ready Spring Boot applications using idiomatic patterns. Spring has years of convention — knowing them separates good apps from fragile ones.

# CORE PRINCIPLES
```
CONVENTION OVER CONFIG:  Spring Boot auto-configures sensibly — don't fight it
LAYER SEPARATION:        Controller → Service → Repository — never skip layers
INJECT INTERFACES:       Depend on abstractions, not concrete implementations
EXTERNALIZE CONFIG:      All environment-specific values in application.properties/yaml
FAIL FAST:               Validate input at the boundary — not deep inside business logic
```

# PROJECT SETUP
```xml
<!-- pom.xml — Spring Boot parent handles dependency versions -->
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.2.0</version>
</parent>

<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>        <!-- REST APIs -->
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-jpa</artifactId>   <!-- JPA + Hibernate -->
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-validation</artifactId> <!-- Bean Validation -->
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-test</artifactId>
        <scope>test</scope>
    </dependency>
</dependencies>
```

# APPLICATION ENTRY POINT
```java
@SpringBootApplication  // = @Configuration + @EnableAutoConfiguration + @ComponentScan
public class MyApplication {
    public static void main(String[] args) {
        SpringApplication.run(MyApplication.class, args);
    }
}
```

# LAYERED ARCHITECTURE
```
┌─────────────────────────────────────┐
│  Controller  (@RestController)       │ ← HTTP in/out, validation, DTO mapping
├─────────────────────────────────────┤
│  Service     (@Service)              │ ← Business logic, transactions
├─────────────────────────────────────┤
│  Repository  (@Repository)           │ ← Data access only
├─────────────────────────────────────┤
│  Entity      (@Entity)               │ ← Database model
└─────────────────────────────────────┘
```

# DEPENDENCY INJECTION

## Constructor Injection (Always Preferred)
```java
@Service
public class OrderService {
    private final OrderRepository orderRepository;
    private final EmailService emailService;

    // Constructor injection — fields are final, testable without Spring
    public OrderService(OrderRepository orderRepository, EmailService emailService) {
        this.orderRepository = orderRepository;
        this.emailService    = emailService;
    }
}

// With Lombok — @RequiredArgsConstructor generates constructor for final fields
@Service
@RequiredArgsConstructor
public class OrderService {
    private final OrderRepository orderRepository;
    private final EmailService emailService;
}
```

## Field Injection — Avoid
```java
@Autowired  // ✗ field injection — can't be final, hard to test, hidden dependency
private OrderRepository repo;
```

# REST CONTROLLER
```java
@RestController              // = @Controller + @ResponseBody
@RequestMapping("/api/v1/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping                              // GET /api/v1/users
    public List<UserResponse> getAll() {
        return userService.findAll();
    }

    @GetMapping("/{id}")                     // GET /api/v1/users/123
    public UserResponse getById(@PathVariable Long id) {
        return userService.findById(id);
    }

    @PostMapping                             // POST /api/v1/users
    @ResponseStatus(HttpStatus.CREATED)
    public UserResponse create(@Valid @RequestBody CreateUserRequest request) {
        return userService.create(request);
    }

    @PutMapping("/{id}")                     // PUT /api/v1/users/123
    public UserResponse update(@PathVariable Long id,
                               @Valid @RequestBody UpdateUserRequest request) {
        return userService.update(id, request);
    }

    @DeleteMapping("/{id}")                  // DELETE /api/v1/users/123
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) {
        userService.delete(id);
    }
}
```

# REQUEST VALIDATION
```java
// DTO with validation annotations
public record CreateUserRequest(
    @NotBlank(message = "Name is required")
    @Size(max = 100)
    String name,

    @NotBlank
    @Email(message = "Invalid email format")
    String email,

    @NotNull
    @Min(18) @Max(120)
    Integer age
) {}

// Controller uses @Valid to trigger validation
@PostMapping
public UserResponse create(@Valid @RequestBody CreateUserRequest req) { ... }

// Custom validator
@Target(ElementType.FIELD)
@Constraint(validatedBy = UniqueEmailValidator.class)
public @interface UniqueEmail {
    String message() default "Email already exists";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}
```

# GLOBAL EXCEPTION HANDLING
```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ErrorResponse handleNotFound(ResourceNotFoundException ex) {
        return new ErrorResponse("NOT_FOUND", ex.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ErrorResponse handleValidation(MethodArgumentNotValidException ex) {
        List<String> errors = ex.getBindingResult()
            .getFieldErrors()
            .stream()
            .map(e -> e.getField() + ": " + e.getDefaultMessage())
            .toList();
        return new ErrorResponse("VALIDATION_ERROR", errors.toString());
    }

    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ErrorResponse handleAll(Exception ex) {
        return new ErrorResponse("SERVER_ERROR", "An unexpected error occurred");
    }
}

public record ErrorResponse(String code, String message) {}
```

# CONFIGURATION — application.yml
```yaml
spring:
  application:
    name: my-service

  datasource:
    url: jdbc:postgresql://localhost:5432/mydb
    username: ${DB_USERNAME}        # read from env var
    password: ${DB_PASSWORD}

  jpa:
    hibernate:
      ddl-auto: validate            # never use create-drop in prod
    show-sql: false
    properties:
      hibernate:
        format_sql: true

server:
  port: 8080
  servlet:
    context-path: /api

# Custom properties
app:
  jwt:
    secret: ${JWT_SECRET}
    expiry-ms: 86400000
```

## Reading Custom Properties
```java
@ConfigurationProperties(prefix = "app.jwt")
@Component
public class JwtProperties {
    private String secret;
    private long expiryMs;
    // getters/setters or use record
}
```

# PROFILES — ENVIRONMENT SEPARATION
```
application.yml            — shared defaults
application-dev.yml        — development overrides
application-prod.yml       — production overrides
application-test.yml       — test overrides
```

```java
// Activate profile
// application: spring.profiles.active=dev
// or: java -jar app.jar --spring.profiles.active=prod
// or: SPRING_PROFILES_ACTIVE=prod

// Conditionally register beans
@Profile("dev")
@Bean
public DataSource h2DataSource() { ... }

@Profile("prod")
@Bean
public DataSource postgresDataSource() { ... }
```

# TRANSACTIONS
```java
@Service
public class TransferService {

    @Transactional                          // commit on success, rollback on RuntimeException
    public void transfer(Long from, Long to, BigDecimal amount) {
        accountRepo.debit(from, amount);    // if this throws, whole tx rolls back
        accountRepo.credit(to, amount);
    }

    @Transactional(readOnly = true)         // hint for read-only — Hibernate optimizations
    public Account findById(Long id) {
        return accountRepo.findById(id).orElseThrow();
    }

    @Transactional(rollbackFor = CheckedException.class)  // rollback for checked too
    public void riskyOperation() throws CheckedException { ... }
}

// PITFALL — self-invocation bypasses the proxy, @Transactional is ignored
@Service
public class MyService {
    public void outer() {
        inner();              // ✗ — @Transactional on inner() is bypassed
    }

    @Transactional
    public void inner() { ... }
}
```

# COMMON ANNOTATIONS QUICK REFERENCE
```
@SpringBootApplication    Entry point — enables auto-config, component scan, config
@RestController           HTTP controller that returns JSON by default
@Service                  Business logic layer bean
@Repository               Data access layer bean (also translates DataAccessException)
@Component                Generic Spring bean
@Configuration            Java config class — defines @Bean methods
@Bean                     Method produces a Spring-managed bean
@Autowired                Inject dependencies (prefer constructor injection)
@Value("${prop}")         Inject a single property value
@ConfigurationProperties  Bind a config prefix to a POJO
@Profile("name")          Register bean only when profile is active
@Transactional            Wraps method in a database transaction
@Valid / @Validated       Trigger Bean Validation on method arguments
@PathVariable             Extract value from URL path
@RequestParam             Extract value from query string
@RequestBody              Deserialize request body to object
@ResponseStatus           Set HTTP status on a method or exception class
@RestControllerAdvice     Global exception handler for all controllers
@CrossOrigin              Enable CORS for a controller or method
```

# BEST PRACTICES CHECKLIST
```
[ ] Use constructor injection — never field injection
[ ] Never skip the service layer — controllers call services, not repositories
[ ] Validate at the controller boundary with @Valid — not inside service methods
[ ] Use @RestControllerAdvice for all exception handling — no try/catch in controllers
[ ] Externalize all secrets with environment variables — never hardcode credentials
[ ] Use application profiles — dev / test / prod configs must be separate
[ ] @Transactional on service methods — not on controller or repository methods
[ ] Use DTOs (records) for request/response — never expose JPA entities directly
[ ] Set ddl-auto: validate in production — never create or create-drop
[ ] Write unit tests with @ExtendWith(MockitoExtension) and integration tests with @SpringBootTest
```
