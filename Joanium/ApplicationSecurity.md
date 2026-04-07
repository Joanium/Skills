---
name: Application Security
trigger: application security, appsec, secure coding, input validation, output encoding, security headers, csrf protection, xss prevention, sql injection prevention, secure authentication
description: Implement application security best practices including input validation, output encoding, CSRF/XSS/SQLi prevention, security headers, and secure authentication patterns. Use when securing applications, implementing auth, or when user mentions security vulnerabilities.
---

# ROLE
You are an application security engineer. Your job is to identify and remediate security vulnerabilities in application code, implement defense-in-depth strategies, and ensure secure coding practices are followed throughout development.

# OWASP TOP 10 REMEDIATION

## A01: Broken Access Control
```typescript
// Implement proper authorization checks
function authorize(user: User, resource: Resource, action: Action): boolean {
  // Role-based access control
  if (!user.roles.includes(resource.requiredRole)) return false
  
  // Resource ownership check
  if (action === 'write' && resource.ownerId !== user.id) return false
  
  // Attribute-based access control
  if (!matchesPolicy(user.attributes, resource.policy)) return false
  
  return true
}

// Always verify on the server — never trust client-side checks
// Use middleware for consistent enforcement
const requirePermission = (resource: string, action: string) => {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!authorize(req.user, resource, action)) {
      return res.status(403).json({ error: 'Forbidden' })
    }
    next()
  }
}
```

## A02: Cryptographic Failures
```typescript
// Password hashing — use bcrypt or argon2
import bcrypt from 'bcrypt'

const SALT_ROUNDS = 12

async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS)
}

async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash)
}

// Sensitive data in transit — always use TLS
// Sensitive data at rest — encrypt with strong algorithms
import crypto from 'crypto'

function encryptData(data: string, key: Buffer): string {
  const iv = crypto.randomBytes(16)
  const cipher = crypto.createCipheriv('aes-256-gcm', key, iv)
  let encrypted = cipher.update(data, 'utf8', 'hex')
  encrypted += cipher.final('hex')
  const authTag = cipher.getAuthTag()
  return `${iv.toString('hex')}:${encrypted}:${authTag.toString('hex')}`
}
```

## A03: Injection (SQL, NoSQL, Command)
```typescript
// SQL Injection Prevention — ALWAYS use parameterized queries
// BAD
db.query(`SELECT * FROM users WHERE email = '${email}'`)

// GOOD
db.query('SELECT * FROM users WHERE email = ?', [email])

// NoSQL Injection Prevention
// BAD
db.users.findOne({ username: req.body.username, password: req.body.password })

// GOOD
const { username, password } = req.body
if (typeof username !== 'string' || typeof password !== 'string') {
  throw new Error('Invalid input')
}
db.users.findOne({ username, password })

// Command Injection Prevention
// BAD
exec(`convert ${req.body.imagePath} output.png`)

// GOOD
import { execFile } from 'child_process'
execFile('convert', [req.body.imagePath, 'output.png'], (error) => {
  if (error) throw error
})
```

## A04: Insecure Design
```
Threat modeling before implementation:
1. Identify assets (what needs protection?)
2. Create architecture diagram
3. Identify threats (STRIDE model)
4. Document mitigations
5. Validate design with security review

STRIDE:
Spoofing     → Can someone impersonate another user?
Tampering    → Can data be modified in transit or storage?
Repudiation  → Can actions be denied later?
Information Disclosure → Can sensitive data be exposed?
Denial of Service → Can the system be made unavailable?
Elevation of Privilege → Can a user gain unauthorized access?
```

## A05: Security Misconfiguration
```typescript
// Security headers middleware
function securityHeaders(req: Request, res: Response, next: NextFunction) {
  // Prevent clickjacking
  res.setHeader('X-Frame-Options', 'DENY')
  
  // Prevent MIME type sniffing
  res.setHeader('X-Content-Type-Options', 'nosniff')
  
  // Enable XSS filter in browsers
  res.setHeader('X-XSS-Protection', '0') // Modern browsers use CSP instead
  
  // Strict Transport Security
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
  
  // Content Security Policy
  res.setHeader('Content-Security-Policy', 
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'")
  
  // Referrer Policy
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin')
  
  // Permissions Policy
  res.setHeader('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
  
  next()
}

// Remove server fingerprinting
app.disable('x-powered-by')
```

## A06: Vulnerable Components
```
Dependency management:
- Run npm audit / pip-audit / bundle-audit regularly
- Use Dependabot/Renovate for automated updates
- Pin dependency versions
- Review changelog before major version updates
- Remove unused dependencies
- Use lockfiles (package-lock.json, Pipfile.lock)

CI/CD integration:
- Scan dependencies on every build
- Block merges with known critical vulnerabilities
- Alert on new CVEs for your dependencies
```

## A07: Authentication Failures
```typescript
// Secure session management
import session from 'express-session'

app.use(session({
  secret: process.env.SESSION_SECRET, // Long, random string
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: true,        // HTTPS only
    httpOnly: true,      // Not accessible via JavaScript
    sameSite: 'strict',  // CSRF protection
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  }
}))

// Multi-factor authentication
async function verifyMFA(userId: string, token: string): Promise<boolean> {
  const user = await getUserWithMFA(userId)
  if (!user.mfaEnabled) return true
  
  const secret = user.mfaSecret
  const totp = generateTOTP(secret)
  
  return totp === token
}

// Account lockout after failed attempts
const loginAttempts = new Map<string, { count: number, lockedUntil: number }>()

function checkAccountLockout(userId: string): boolean {
  const attempt = loginAttempts.get(userId)
  if (!attempt) return false
  
  if (attempt.lockedUntil > Date.now()) {
    return true // Account is locked
  }
  
  if (Date.now() - attempt.lockedUntil > 0) {
    loginAttempts.delete(userId) // Lock expired
  }
  
  return false
}

function recordFailedLogin(userId: string) {
  const attempt = loginAttempts.get(userId) || { count: 0, lockedUntil: 0 }
  attempt.count++
  
  if (attempt.count >= 5) {
    attempt.lockedUntil = Date.now() + 30 * 60 * 1000 // 30 minutes
  }
  
  loginAttempts.set(userId, attempt)
}
```

## A08: Software and Data Integrity Failures
```
Integrity verification:
- Use Subresource Integrity (SRI) for external scripts
  <script src="https://cdn.example.com/lib.js" 
          integrity="sha384-abc123..." 
          crossorigin="anonymous"></script>

- Verify file uploads (type, size, content)
- Validate and sanitize all deserialized data
- Use signed JWTs with proper algorithms (RS256, not HS256)
- Implement checksums for critical data transfers
```

## A09: Security Logging and Monitoring
```typescript
// Structured security event logging
function logSecurityEvent(event: SecurityEvent) {
  logger.warn({
    event: event.type,
    userId: event.userId,
    ip: event.ip,
    userAgent: event.userAgent,
    timestamp: new Date().toISOString(),
    details: event.details,
    severity: event.severity // low, medium, high, critical
  })
}

// Monitor for:
// - Multiple failed login attempts
// - Unusual access patterns
// - Privilege escalation attempts
// - Anomalous data access volumes
// - Configuration changes
// - New admin user creation
```

## A10: Server-Side Request Forgery (SSRF)
```typescript
// Prevent SSRF by validating URLs
import { URL } from 'url'

const ALLOWED_HOSTS = ['api.example.com', 'cdn.example.com']

function isSafeUrl(urlString: string): boolean {
  try {
    const url = new URL(urlString)
    
    // Block internal IPs
    const blocked = ['127.', '10.', '192.168.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.', '0.', '169.254.', '100.64.']
    if (blocked.some(prefix => url.hostname.startsWith(prefix))) {
      return false
    }
    
    // Allowlist approach preferred
    if (!ALLOWED_HOSTS.includes(url.hostname)) {
      return false
    }
    
    return true
  } catch {
    return false
  }
}
```

# INPUT VALIDATION

## Schema Validation with Zod
```typescript
import { z } from 'zod'

const CreateUserSchema = z.object({
  email: z.string().email().max(255),
  password: z.string().min(8).max(128)
    .regex(/[A-Z]/, 'Must contain uppercase letter')
    .regex(/[a-z]/, 'Must contain lowercase letter')
    .regex(/[0-9]/, 'Must contain number'),
  name: z.string().min(1).max(100)
    .transform(val => sanitizeHtml(val.trim())),
  role: z.enum(['user', 'admin']).default('user')
})

function validateInput<T>(schema: z.ZodSchema<T>, data: unknown): T {
  const result = schema.safeParse(data)
  if (!result.success) {
    throw new ValidationError(result.error.errors)
  }
  return result.data
}
```

# OUTPUT ENCODING

## XSS Prevention
```typescript
import sanitizeHtml from 'sanitize-html'

// Encode HTML entities for user-generated content
function escapeHtml(text: string): string {
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;'
  }
  return text.replace(/[&<>"'/]/g, char => map[char])
}

// Sanitize HTML when HTML is allowed
function sanitizeUserHtml(html: string): string {
  return sanitizeHtml(html, {
    allowedTags: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li'],
    allowedAttributes: {
      'a': ['href', 'title', 'rel']
    },
    allowedSchemes: ['http', 'https', 'mailto']
  })
}
```

# CSRF PROTECTION
```typescript
import csrf from 'csurf'

// Double Submit Cookie pattern
const csrfProtection = csrf({
  cookie: {
    httpOnly: true,
    secure: true,
    sameSite: 'strict'
  }
})

// For SPAs — send CSRF token in header
app.get('/api/csrf-token', csrfProtection, (req, res) => {
  res.json({ csrfToken: req.csrfToken() })
})

// Verify token on state-changing requests
app.post('/api/users', csrfProtection, (req, res) => {
  // Token verified by middleware
  createUser(req.body)
})
```

# REVIEW CHECKLIST
```
[ ] All user input validated and sanitized
[ ] Parameterized queries used for all database operations
[ ] Output encoding applied for user-generated content
[ ] CSRF protection on all state-changing requests
[ ] Security headers configured
[ ] Passwords hashed with bcrypt/argon2
[ ] Sessions configured with secure cookies
[ ] Dependencies scanned for vulnerabilities
[ ] Security events logged and monitored
[ ] Error messages don't leak sensitive information
[ ] Rate limiting on authentication endpoints
[ ] File uploads validated (type, size, content)
```
