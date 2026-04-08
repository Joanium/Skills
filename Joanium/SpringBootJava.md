---
name: Spring Boot Java
trigger: spring boot, spring mvc, spring data jpa, rest controller, spring security, hibernate, java api, @Service, @Repository, @Entity, @SpringBootApplication, application.properties, spring beans, dependency injection java
description: Build production-grade Java REST APIs with Spring Boot — covering REST controllers, JPA repositories, service layers, validation, exception handling, security, and configuration.
---

# ROLE
You are a senior Java/Spring Boot engineer. You write clean, layered Spring Boot applications with proper separation of concerns, exception handling, and idiomatic Spring patterns.

# PROJECT STRUCTURE
```
src/main/java/com/example/app/
├── controller/          ← HTTP layer — maps routes, validates input, delegates
│   └── UserController.java
├── service/             ← Business logic — transactions live here
│   ├── UserService.java
│   └── UserServiceImpl.java
├── repository/          ← Data access — Spring Data JPA interfaces
│   └── UserRepository.java
├── entity/              ← JPA entities — database tables
│   └── User.java
├── dto/                 ← Data Transfer Objects — API request/response shapes
│   ├── UserRequest.java
│   └── UserResponse.java
├── exception/           ← Custom exceptions + global handler
│   ├── ResourceNotFoundException.java
│   └── GlobalExceptionHandler.java
├── config/              ← Security, CORS, beans
│   └── SecurityConfig.java
└── AppApplication.java
```

# ENTITY LAYER
```java
@Entity
@Table(name = "users")
@Getter @Setter @NoArgsConstructor   // Lombok
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private String id;

    @Column(nullable = false, unique = true)
    private String email;

    @Column(nullable = false)
    private String name;

    @Enumerated(EnumType.STRING)
    private Role role = Role.USER;

    @CreationTimestamp
    private Instant createdAt;

    @UpdateTimestamp
    private Instant updatedAt;

    // Relationships
    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Order> orders = new ArrayList<>();
}
```

# DTO LAYER — Never Expose Entities Directly
```java
// Request DTO — input validation via Jakarta Bean Validation
public record UserRequest(
    @NotBlank(message = "Name is required")
    @Size(min = 2, max = 100)
    String name,

    @NotBlank
    @Email(message = "Must be a valid email")
    String email,

    @NotBlank
    @Size(min = 8, message = "Password must be at least 8 characters")
    String password
) {}

// Response DTO — what the API returns
public record UserResponse(
    String id,
    String name,
    String email,
    String role,
    Instant createdAt
) {
    // Static factory from entity
    public static UserResponse from(User user) {
        return new UserResponse(
            user.getId(),
            user.getName(),
            user.getEmail(),
            user.getRole().name(),
            user.getCreatedAt()
        );
    }
}
```

# REPOSITORY LAYER
```java
@Repository
public interface UserRepository extends JpaRepository<User, String> {

    // Spring Data derives query from method name
    Optional<User> findByEmail(String email);
    boolean existsByEmail(String email);
    List<User> findByRole(Role role);

    // Custom JPQL query
    @Query("SELECT u FROM User u WHERE u.createdAt > :since AND u.role = :role")
    List<User> findRecentByRole(@Param("since") Instant since, @Param("role") Role role);

    // Pagination
    Page<User> findAll(Pageable pageable);

    // Projection — fetch only specific fields
    @Query("SELECT u.id, u.name, u.email FROM User u")
    List<UserSummary> findAllSummaries();
}
```

# SERVICE LAYER — Business Logic + Transactions
```java
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)   // default: read-only; override on writes
public class UserServiceImpl implements UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public Page<UserResponse> getUsers(Pageable pageable) {
        return userRepository.findAll(pageable).map(UserResponse::from);
    }

    public UserResponse getUserById(String id) {
        return userRepository.findById(id)
            .map(UserResponse::from)
            .orElseThrow(() -> new ResourceNotFoundException("User", id));
    }

    @Transactional   // override — this writes to DB
    public UserResponse createUser(UserRequest request) {
        if (userRepository.existsByEmail(request.email())) {
            throw new ConflictException("Email already in use: " + request.email());
        }

        User user = new User();
        user.setName(request.name());
        user.setEmail(request.email().toLowerCase());
        user.setPassword(passwordEncoder.encode(request.password()));

        return UserResponse.from(userRepository.save(user));
    }

    @Transactional
    public UserResponse updateUser(String id, UserRequest request) {
        User user = userRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("User", id));

        user.setName(request.name());
        // No explicit save() needed — dirty checking handles it within @Transactional
        return UserResponse.from(user);
    }

    @Transactional
    public void deleteUser(String id) {
        if (!userRepository.existsById(id)) {
            throw new ResourceNotFoundException("User", id);
        }
        userRepository.deleteById(id);
    }
}
```

# CONTROLLER LAYER
```java
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
@Validated
public class UserController {

    private final UserService userService;

    @GetMapping
    public ResponseEntity<Page<UserResponse>> getUsers(
        @PageableDefault(size = 20, sort = "createdAt", direction = Sort.Direction.DESC)
        Pageable pageable
    ) {
        return ResponseEntity.ok(userService.getUsers(pageable));
    }

    @GetMapping("/{id}")
    public ResponseEntity<UserResponse> getUserById(@PathVariable String id) {
        return ResponseEntity.ok(userService.getUserById(id));
    }

    @PostMapping
    public ResponseEntity<UserResponse> createUser(
        @RequestBody @Valid UserRequest request
    ) {
        UserResponse created = userService.createUser(request);
        URI location = URI.create("/api/v1/users/" + created.id());
        return ResponseEntity.created(location).body(created);
    }

    @PatchMapping("/{id}")
    public ResponseEntity<UserResponse> updateUser(
        @PathVariable String id,
        @RequestBody @Valid UserRequest request
    ) {
        return ResponseEntity.ok(userService.updateUser(id, request));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteUser(@PathVariable String id) {
        userService.deleteUser(id);
        return ResponseEntity.noContent().build();
    }
}
```

# GLOBAL EXCEPTION HANDLING
```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(ResourceNotFoundException ex) {
        return ResponseEntity.status(404).body(
            new ErrorResponse("NOT_FOUND", ex.getMessage())
        );
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException ex) {
        List<FieldError> errors = ex.getBindingResult().getFieldErrors().stream()
            .map(e -> new FieldError(e.getField(), e.getDefaultMessage()))
            .toList();
        return ResponseEntity.status(422).body(
            new ErrorResponse("VALIDATION_ERROR", "Validation failed", errors)
        );
    }

    @ExceptionHandler(ConflictException.class)
    public ResponseEntity<ErrorResponse> handleConflict(ConflictException ex) {
        return ResponseEntity.status(409).body(
            new ErrorResponse("CONFLICT", ex.getMessage())
        );
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGeneral(Exception ex) {
        log.error("Unhandled exception", ex);
        return ResponseEntity.status(500).body(
            new ErrorResponse("INTERNAL_ERROR", "An unexpected error occurred")
        );
    }
}

// Custom exception
public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String resource, String id) {
        super(resource + " with id '" + id + "' not found");
    }
}
```

# SECURITY CONFIGURATION (Spring Security 6)
```java
@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtAuthFilter jwtAuthFilter;

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf.disable())
            .sessionManagement(s -> s.sessionCreationPolicy(STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/v1/auth/**").permitAll()
                .requestMatchers("/actuator/health").permitAll()
                .requestMatchers(HttpMethod.GET, "/api/v1/products/**").permitAll()
                .requestMatchers("/api/v1/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class)
            .build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder(12);
    }
}
```

# APPLICATION PROPERTIES
```yaml
# application.yml
spring:
  datasource:
    url: ${DB_URL:jdbc:postgresql://localhost:5432/myapp}
    username: ${DB_USER}
    password: ${DB_PASS}

  jpa:
    hibernate:
      ddl-auto: validate        # NEVER use create/create-drop in prod
    show-sql: false             # true only for dev
    properties:
      hibernate:
        format_sql: true
        default_schema: public

  flyway:
    enabled: true               # always use migrations, not ddl-auto: update

server:
  port: 8080

logging:
  level:
    com.example.app: DEBUG
    org.springframework.security: INFO
```

# COMMON MISTAKES TO AVOID
```
✗ Exposing JPA entities directly from controllers — always use DTOs
✗ Putting business logic in controllers — move to @Service
✗ Using @Transactional on controller methods — belongs in service layer
✗ Using ddl-auto: update/create in production — use Flyway migrations
✗ Not using Optional — always check findById(), never assume presence
✗ Field injection (@Autowired on fields) — use constructor injection (Lombok @RequiredArgsConstructor)
✗ Catching and swallowing exceptions without logging
✗ No pagination on list endpoints — always use Pageable for collections
```
