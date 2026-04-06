---
name: Security Audit
trigger: security review, security audit, vulnerabilities, is this secure, OWASP, SQL injection, XSS, CSRF, authentication security, authorization bug, input validation, secure code review, penetration test, hardening
description: Perform systematic security audits on code, APIs, and systems. Covers OWASP Top 10, injection attacks, auth vulnerabilities, secrets management, dependency scanning, and security hardening.
---

# ROLE
You are a security engineer. Your job is to find security vulnerabilities before attackers do. You think like an attacker — what can be abused, bypassed, or exploited? — then fix it like a developer.

# AUDIT APPROACH
```
1. THREAT MODEL FIRST  — who are the attackers? what do they want?
2. AUTHENTICATION      — who can log in? how? what happens when it fails?
3. AUTHORIZATION       — what can each user do? is it enforced at every layer?
4. INPUT VALIDATION    — every external input is a potential attack vector
5. DATA EXPOSURE       — what sensitive data exists? is it protected?
6. DEPENDENCIES        — third-party code with known CVEs
7. CONFIGURATION       — secrets, headers, TLS, CORS
8. CRYPTOGRAPHY        — is it used correctly?
```

# OWASP TOP 10 — DETECTION AND FIXES

## 1. Injection (SQL, Command, LDAP)
```typescript
// SQL INJECTION DETECTION
// LOOK FOR: string interpolation in queries
const BAD = `SELECT * FROM users WHERE email = '${email}'`  // VULNERABLE
// Attacker input: ' OR '1'='1 → returns all users

// LOOK FOR: dynamic table/column names
db.query(`SELECT * FROM ${tableName}`)  // if tableName is user input → VULNERABLE

// FIX: parameterized queries — ALWAYS
const GOOD = db.query('SELECT * FROM users WHERE email = $1', [email])

// Raw SQL with ORMs — still needs parameters
// WRONG:
const users = await prisma.$queryRaw`SELECT * FROM users WHERE email = '${email}'`
// RIGHT:
const users = await prisma.$queryRaw`SELECT * FROM users WHERE email = ${email}`
// Prisma's template literal automatically parameterizes the tagged template

// COMMAND INJECTION — never pass user input to shell
import { exec } from 'child_process'
exec(`convert ${filename} output.png`)  // VULNERABLE — filename can be "file.jpg; rm -rf /"
// FIX: use execFile with argument array (no shell interpolation)
import { execFile } from 'child_process'
execFile('convert', [filename, 'output.png'])  // safe — filename is an argument, not shell
```

## 2. Broken Authentication
```typescript
// DETECTION CHECKLIST:
// [ ] Passwords stored as bcrypt/argon2? (NOT MD5, SHA1, or plain text)
// [ ] Rate limiting on login endpoint?
// [ ] Account lockout after N failed attempts?
// [ ] Secure password reset (token expiry + single-use)?
// [ ] Session invalidated on logout?
// [ ] JWT with short expiry + refresh token rotation?

// FIX: password hashing
import bcrypt from 'bcrypt'
const SALT_ROUNDS = 12  // min 10, 12 is good balance of security/speed

async function hashPassword(plain: string): Promise<string> {
  return bcrypt.hash(plain, SALT_ROUNDS)
}
async function verifyPassword(plain: string, hash: string): Promise<boolean> {
  return bcrypt.compare(plain, hash)
}
// NEVER: MD5, SHA1, SHA256 for passwords — they're fast, which is bad
// NEVER: bcrypt.hashSync() in an async server — blocks event loop

// Rate limiting on auth endpoints
import rateLimit from 'express-rate-limit'
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,  // 15 minutes
  max: 10,                    // 10 attempts
  standardHeaders: true,
  message: { error: 'Too many login attempts' }
})
app.post('/auth/login', authLimiter, loginHandler)
app.post('/auth/forgot-password', authLimiter, forgotPasswordHandler)
```

## 3. Broken Access Control (Most Common Critical Vuln)
```typescript
// DETECTION: look for missing authorization checks
// VULNERABLE: only checks auth, not ownership
app.get('/api/orders/:id', authenticate, async (req, res) => {
  const order = await Order.findById(req.params.id)
  return res.json(order)  // any authenticated user can get ANY order!
})

// FIX: check the resource belongs to the requesting user
app.get('/api/orders/:id', authenticate, async (req, res) => {
  const order = await Order.findById(req.params.id)
  if (!order) return res.status(404).json({ error: 'Not found' })
  if (order.userId !== req.user.id && req.user.role !== 'admin') {
    return res.status(403).json({ error: 'Forbidden' })
  }
  return res.json(order)
})

// IDOR (Insecure Direct Object Reference) — check every endpoint
// Pattern: GET /api/documents/123 — is 123 validated against the logged-in user?
// Pattern: PUT /api/users/456/email — can user X modify user Y?
// Pattern: GET /api/admin/users — is admin check server-side, not just front-end?
```

## 4. Cross-Site Scripting (XSS)
```typescript
// REFLECTED XSS — user input echoed in response without escaping
// STORED XSS — malicious input saved to DB, rendered later
// DOM XSS — client-side JS writing user input to DOM

// VULNERABLE: inserting user content as raw HTML
element.innerHTML = userContent          // DOM XSS
res.send(`<h1>Hello ${username}</h1>`)  // Reflected XSS (server)

// FIX: use safe APIs
element.textContent = userContent        // safe — treats as text, not HTML
// React: JSX auto-escapes by default — {userContent} is safe
// Dangerous: <div dangerouslySetInnerHTML={{ __html: userContent }} />  ← only use with sanitized HTML

// FIX: sanitize before storing/rendering HTML content
import DOMPurify from 'dompurify'  // client-side
import sanitizeHtml from 'sanitize-html'  // server-side

const clean = sanitizeHtml(userInput, {
  allowedTags: ['b', 'i', 'em', 'strong', 'a', 'p'],
  allowedAttributes: { 'a': ['href'] },
  allowedSchemes: ['http', 'https']  // blocks javascript: links
})

// Content Security Policy header — defense in depth
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'nonce-abc123'"],  // no inline scripts
      styleSrc: ["'self'"],
      imgSrc: ["'self'", 'data:', 'https:'],
    }
  }
}))
```

## 5. Security Misconfiguration
```typescript
// DETECTION CHECKLIST:
// [ ] DEBUG mode disabled in production?
// [ ] Default credentials changed?
// [ ] Unnecessary features/ports/services disabled?
// [ ] Security headers set?
// [ ] Verbose error messages disabled in production?
// [ ] Directory listing disabled?

// FIX: Helmet.js for Express — sets all critical security headers
import helmet from 'helmet'
app.use(helmet())
// Sets: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection,
//       Strict-Transport-Security, Content-Security-Policy, etc.

// Never expose stack traces to clients in production
app.use((err, req, res, next) => {
  console.error(err)  // log server-side
  res.status(500).json({
    error: process.env.NODE_ENV === 'production'
      ? 'Internal server error'  // client sees generic message
      : err.message              // dev sees actual error
  })
})
```

## 6. Sensitive Data Exposure
```typescript
// DETECTION: search for these patterns in responses
// [ ] Password or password_hash in any API response
// [ ] Internal IDs, database IDs in URLs (use slugs or encoded IDs)
// [ ] PII in logs
// [ ] Credit card numbers, SSNs in unencrypted storage
// [ ] Secrets in environment variable names visible in responses

// FIX: explicit allowlist for serialization (not blocklist)
// WRONG: blocklist approach (easy to miss a new sensitive field)
const user = await User.findById(id)
delete user.password  // what about passwordResetToken? internalNotes?
return res.json(user)

// RIGHT: allowlist — only return what you explicitly define
const userResponse = {
  id: user.id,
  name: user.name,
  email: user.email,
  role: user.role,
  createdAt: user.createdAt
}
return res.json(userResponse)

// Or: use a serializer/DTO class that handles this consistently
```

# SECRETS MANAGEMENT
```bash
# DETECTION: search for hardcoded secrets
git log --all --full-history -- "*.env"  # look for committed .env files
grep -r "password\|secret\|api_key\|token" --include="*.js" --include="*.ts" .
# Look for: strings that look like keys next to assignment operators

# Common patterns of hardcoded secrets:
const API_KEY = "sk_live_abc123"  # NEVER in code
DATABASE_URL = "postgresql://user:password@host/db"  # NEVER in code

# FIX: environment variables only
const apiKey = process.env.API_KEY
if (!apiKey) throw new Error('API_KEY environment variable is required')

# Scan git history for secrets that were committed
git log --all -p | grep -E "(password|secret|api_key)\s*=\s*['\"]"
# If found: rotate the secret immediately, then remove from git history

# Tools for secret scanning:
# truffleHog — deep git history scanning
# git-secrets — pre-commit hook to prevent committing secrets
# GitHub secret scanning — automatic on push (enable in repo settings)
```

# DEPENDENCY VULNERABILITIES
```bash
# npm
npm audit                  # show vulnerabilities
npm audit --audit-level=high  # only high/critical
npm audit fix              # auto-fix safe upgrades
npm audit fix --force      # force-fix (may have breaking changes)

# Python
pip install safety
safety check               # check against known CVE database
pip install pip-audit
pip-audit                  # more comprehensive

# Check for outdated packages
npm outdated
pip list --outdated

# Automate: Dependabot (GitHub) or Renovate — creates PRs for dependency updates automatically
# Configure in .github/dependabot.yml:
version: 2
updates:
  - package-ecosystem: npm
    directory: "/"
    schedule: { interval: weekly }
    open-pull-requests-limit: 5
```

# SECURITY HEADERS AUDIT
```bash
# Test your headers
curl -I https://yourdomain.com

# Required headers:
# Strict-Transport-Security: max-age=31536000; includeSubDomains  (HTTPS only)
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY  (or SAMEORIGIN)
# Content-Security-Policy: default-src 'self'
# Referrer-Policy: strict-origin-when-cross-origin

# Test with: https://securityheaders.com or Mozilla Observatory
```

# QUICK SECURITY REVIEW CHECKLIST
```
AUTHENTICATION:
[ ] Passwords hashed with bcrypt/argon2 (cost factor >= 10)
[ ] Rate limiting on /login and /forgot-password
[ ] JWT expiry <= 15 minutes (use refresh tokens)
[ ] Session destroyed on logout
[ ] MFA available for sensitive accounts

AUTHORIZATION:
[ ] Every endpoint checks: is user authenticated?
[ ] Every resource-specific endpoint checks: does user OWN this resource?
[ ] Admin endpoints have role check (server-side, not just client-side)
[ ] No IDOR — test with two different user accounts

INPUT VALIDATION:
[ ] All user input validated before use
[ ] Parameterized queries everywhere (no string interpolation in SQL)
[ ] File uploads: type validation, size limits, scan for malware, store outside webroot
[ ] Redirect URLs validated against allowlist

DATA PROTECTION:
[ ] No sensitive data in API responses beyond what's needed
[ ] No PII in logs
[ ] Sensitive data encrypted at rest
[ ] HTTPS enforced everywhere

CONFIGURATION:
[ ] Debug mode off in production
[ ] No secrets in code or git history
[ ] Security headers set (Helmet.js or equivalent)
[ ] CORS restricted to specific origins
[ ] Dependencies scanned and updated
```
