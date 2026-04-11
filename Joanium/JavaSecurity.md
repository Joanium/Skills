---
name: Java Security
trigger: java security, sql injection, xss, authentication, jwt, bcrypt, password hashing, owasp, spring security, secure coding, csrf, input validation, java vulnerabilities, sensitive data, encryption java
description: Write secure Java applications. Covers OWASP Top 10 mitigations, password hashing, JWT, input validation, Spring Security basics, and secrets management.
---

# ROLE
You are a senior Java security engineer. Your job is to help developers write code that resists common attacks. Security is not an add-on — it must be baked into design. One missed validation or hardcoded secret can expose an entire application.

# OWASP TOP 10 — JAVA MITIGATIONS

## 1. SQL Injection — Always PreparedStatement
```java
// ✗ VULNERABLE — attacker input: ' OR '1'='1
String sql = "SELECT * FROM users WHERE email = '" + email + "'";

// ✓ SAFE — parameterized — value is never interpreted as SQL
PreparedStatement ps = conn.prepareStatement(
    "SELECT * FROM users WHERE email = ?");
ps.setString(1, email);

// Spring Data JPA — also safe (uses PreparedStatement internally)
userRepository.findByEmail(email);  // ✓

// Spring JdbcTemplate — safe with ? params
jdbc.query("SELECT * FROM users WHERE email = ?", rowMapper, email);  // ✓

// JPQL — safe with named params
em.createQuery("FROM User u WHERE u.email = :email")
  .setParameter("email", email);  // ✓

// NEVER: nativeQuery with string concat
@Query(value = "SELECT * FROM users WHERE role = '" + role + "'", nativeQuery = true)  // ✗
```

## 2. Broken Authentication — Password Hashing
```java
// NEVER store plaintext passwords or MD5/SHA1 hashes
// USE BCrypt, Argon2, or SCrypt — these are slow by design to resist brute force

// Spring Security BCrypt
BCryptPasswordEncoder encoder = new BCryptPasswordEncoder(12);  // strength 10-12

// Hash on registration
String hashed = encoder.encode(rawPassword);   // store this in DB
userRepo.save(new User(email, hashed));

// Verify on login
boolean matches = encoder.matches(rawPassword, storedHash);  // ✓ timing-safe compare

// Default BCrypt prefix:  $2a$12$...
// NEVER: "password".equals(storedHash)   ← timing attack + plaintext comparison
```

## 3. JWT — Sign and Validate Correctly
```java
// Dependency: io.jsonwebtoken:jjwt-api + jjwt-impl + jjwt-jackson

// Generate token
SecretKey key = Keys.hmacShaKeyFor(
    Decoders.BASE64.decode(secretBase64));   // key from env var, min 256 bits

String token = Jwts.builder()
    .subject(userId.toString())
    .claim("role", user.getRole())
    .issuedAt(new Date())
    .expiration(new Date(System.currentTimeMillis() + 86_400_000))  // 24h
    .signWith(key)
    .compact();

// Validate token
try {
    Claims claims = Jwts.parser()
        .verifyWith(key)
        .build()
        .parseSignedClaims(token)
        .getPayload();
    String userId = claims.getSubject();
} catch (JwtException e) {
    throw new UnauthorizedException("Invalid token");
}

// Store JWT in HttpOnly cookie (NOT localStorage — XSS can steal localStorage)
response.addCookie(new Cookie("auth_token", token) {{
    setHttpOnly(true);
    setSecure(true);
    setPath("/");
    setMaxAge(86400);
}});
```

## 4. XSS — Output Encoding
```java
// Never render user input as raw HTML
// Encode output on the way out — not on the way in

// Thymeleaf — automatically HTML-encodes by default
<span th:text="${userInput}">...</span>  // ✓ auto-encoded
<span th:utext="${userInput}">...</span> // ✗ unescaped — only for trusted HTML

// Spring — use HtmlUtils for manual encoding
String safe = HtmlUtils.htmlEscape(userInput);  // < → &lt;

// React (frontend) — JSX auto-escapes by default
<div>{userInput}</div>        // ✓ auto-escaped
<div dangerouslySetInnerHTML={{...}} />  // ✗ only if absolutely necessary + sanitized

// Content-Security-Policy header — defense in depth
response.setHeader("Content-Security-Policy",
    "default-src 'self'; script-src 'self'");
```

## 5. Insecure Deserialization
```java
// NEVER deserialize untrusted data with Java native serialization
ObjectInputStream ois = new ObjectInputStream(inputStream);
Object obj = ois.readObject();  // ✗ RCE if input is attacker-controlled

// SAFE alternatives:
// - Use JSON (Jackson) or XML — not native serialization
// - Validate/whitelist object type if you MUST use ObjectInputStream:
ObjectInputStream safe = new ObjectInputStream(input) {
    @Override
    protected Class<?> resolveClass(ObjectStreamClass desc)
            throws IOException, ClassNotFoundException {
        if (!ALLOWED_CLASSES.contains(desc.getName()))
            throw new InvalidClassException("Blocked: " + desc.getName());
        return super.resolveClass(desc);
    }
};
```

# SECRETS MANAGEMENT — NEVER HARDCODE
```java
// ✗ HARDCODED SECRETS — end up in Git history, logs, crash reports
String dbPass = "MyS3cur3P@ss!";
String apiKey = "sk_live_abc123";

// ✓ Environment variables
String dbPass = System.getenv("DB_PASSWORD");

// ✓ Spring — @Value from environment
@Value("${DB_PASSWORD}")
private String dbPassword;

// ✓ Spring Cloud Config / AWS Secrets Manager / Vault
// application.yml
spring:
  config:
    import: "aws-secretsmanager:/myapp/prod"

// .gitignore — never commit
.env
application-prod.yml    # if it has real values
secrets/
```

# INPUT VALIDATION
```java
// Validate at the entry point — controller boundary
public record CreateUserRequest(
    @NotBlank @Size(max = 100) String name,
    @Email @NotBlank String email,
    @Min(0) @Max(150) int age,
    @Pattern(regexp = "^[a-zA-Z0-9_]+$", message = "Alphanumeric only") String username
) {}

// File upload validation
public void handleUpload(MultipartFile file) {
    // 1 — Check extension (not just MIME type — easily spoofed)
    String filename = StringUtils.cleanPath(file.getOriginalFilename());
    String ext      = FilenameUtils.getExtension(filename).toLowerCase();
    if (!Set.of("jpg", "jpeg", "png", "pdf").contains(ext))
        throw new IllegalArgumentException("Invalid file type: " + ext);

    // 2 — Check size
    if (file.getSize() > 5 * 1024 * 1024)
        throw new IllegalArgumentException("Max file size is 5MB");

    // 3 — Never use original filename for disk storage
    String safeName = UUID.randomUUID() + "." + ext;
    Files.copy(file.getInputStream(), Paths.get(uploadDir, safeName));
}

// Path traversal prevention
String userInput = "../../../etc/passwd";
Path safePath = Paths.get(baseDir).resolve(userInput).normalize();
if (!safePath.startsWith(Paths.get(baseDir)))
    throw new SecurityException("Path traversal attempt");
```

# SPRING SECURITY BASICS
```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())                     // disable if using JWT
            .sessionManagement(sm -> sm
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS))  // JWT = stateless
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**").permitAll()  // public endpoints
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder(12);
    }
}
```

# HTTPS & TRANSPORT SECURITY
```yaml
# application.yml — enforce HTTPS
server:
  ssl:
    enabled: true
    key-store: classpath:keystore.p12
    key-store-password: ${SSL_PASSWORD}
    key-store-type: PKCS12

# Security headers — add via filter or Spring Security
response.setHeader("Strict-Transport-Security", "max-age=31536000; includeSubDomains");
response.setHeader("X-Content-Type-Options", "nosniff");
response.setHeader("X-Frame-Options", "DENY");
response.setHeader("Referrer-Policy", "no-referrer");
```

# BEST PRACTICES CHECKLIST
```
[ ] Never concatenate user input into SQL — always PreparedStatement or named params
[ ] Hash passwords with BCrypt (strength 10+) — never MD5/SHA1/plaintext
[ ] Store secrets in environment variables or a secrets manager — never in code or git
[ ] Validate all input at the controller boundary — type, range, format, length
[ ] Encode HTML output — never render raw user input as HTML
[ ] Never deserialize untrusted native Java serialized data
[ ] Set HttpOnly + Secure flags on all auth cookies
[ ] Use HTTPS everywhere — redirect HTTP to HTTPS
[ ] Add security headers: HSTS, X-Content-Type-Options, X-Frame-Options, CSP
[ ] Keep dependencies updated — run OWASP Dependency-Check in CI pipeline
```
