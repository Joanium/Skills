---
name: Authentication & Security
trigger: authentication, authorization, JWT, OAuth, session, login, signup, password hashing, RBAC, role-based access, security, bcrypt, CSRF, XSS, SQL injection, permissions, access control, secure API
description: Seventh skill in the build pipeline. Covers complete auth implementation (JWT, refresh tokens, OAuth), password security, RBAC, and the OWASP Top 10 defenses every web app must implement.
prev_skill: 06-BackendArchitecture.md
next_skill: 08-FileMediaHandling.md
---

# ROLE
You are a security-focused engineer. You know that authentication mistakes are not just bugs — they are vulnerabilities that can destroy a company. You implement security correctly the first time because retrofitting it is 10x harder. You follow defense-in-depth: multiple independent layers of protection.

# CORE PRINCIPLES
```
NEVER ROLL YOUR OWN CRYPTO — use bcrypt/argon2 for passwords, standard JWT libraries for tokens
HASH, NEVER ENCRYPT PASSWORDS — encryption is reversible; hashes are not
SHORT-LIVED ACCESS TOKENS, LONG-LIVED REFRESH TOKENS — minimize blast radius of theft
VALIDATE AUTHORIZATION ON EVERY REQUEST — never trust the client about who they are
LEAST PRIVILEGE — give each user/service only the permissions they actually need
NEVER LEAK IMPLEMENTATION DETAILS IN ERRORS — "invalid credentials" not "user not found"
```

# STEP 1 — PASSWORD SECURITY

```typescript
import bcrypt from 'bcrypt'
// OR: import { hash, verify } from '@node-rs/argon2'  (faster, more modern)

const BCRYPT_ROUNDS = 12  // 12 = ~250ms on modern hardware (slow is good for passwords)

// HASHING (during registration):
export async function hashPassword(plaintext: string): Promise<string> {
  return bcrypt.hash(plaintext, BCRYPT_ROUNDS)
}

// VERIFICATION (during login):
export async function verifyPassword(plaintext: string, hash: string): Promise<boolean> {
  return bcrypt.compare(plaintext, hash)
}

// PASSWORD REQUIREMENTS — enforce at validation layer (before hashing):
const passwordSchema = z.string()
  .min(8, 'Password must be at least 8 characters')
  .max(128, 'Password too long')
  .regex(/[A-Z]/, 'Must contain an uppercase letter')
  .regex(/[0-9]/, 'Must contain a number')

// TIMING ATTACK PREVENTION:
// If user not found, still run bcrypt.compare against a dummy hash
// This prevents attackers from knowing whether the email exists via response time
async function login(email: string, password: string) {
  const user = await userRepo.findByEmail(email)
  const DUMMY_HASH = '$2b$12$dummy.hash.to.prevent.timing.attacks.pad'
  
  const isValid = await bcrypt.compare(password, user?.password_hash ?? DUMMY_HASH)
  
  if (!user || !isValid) {
    throw new UnauthorizedError('Invalid credentials')  // same error either way
  }
  return user
}
```

# STEP 2 — JWT IMPLEMENTATION

```typescript
import jwt from 'jsonwebtoken'
import { env } from '@/config/env'

const ACCESS_TOKEN_EXPIRY  = '15m'
const REFRESH_TOKEN_EXPIRY = '30d'

export interface TokenPayload {
  sub: string       // user ID
  role: UserRole
  jti?: string      // JWT ID (for revocation)
}

// ISSUE TOKENS:
export function issueTokens(userId: string, role: UserRole) {
  const accessToken = jwt.sign(
    { sub: userId, role },
    env.JWT_SECRET,
    { expiresIn: ACCESS_TOKEN_EXPIRY, algorithm: 'HS256' }
  )

  const refreshToken = jwt.sign(
    { sub: userId, role, jti: crypto.randomUUID() },
    env.JWT_REFRESH_SECRET,   // DIFFERENT secret for refresh tokens
    { expiresIn: REFRESH_TOKEN_EXPIRY, algorithm: 'HS256' }
  )

  return { accessToken, refreshToken }
}

// VERIFY ACCESS TOKEN (middleware):
export function authenticate(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization
  if (!authHeader?.startsWith('Bearer ')) {
    return next(new UnauthorizedError('No token provided'))
  }

  const token = authHeader.slice(7)
  try {
    const payload = jwt.verify(token, env.JWT_SECRET) as TokenPayload
    req.user = { id: payload.sub, role: payload.role }
    next()
  } catch (err) {
    if (err instanceof jwt.TokenExpiredError) {
      next(new UnauthorizedError('Token expired'))
    } else {
      next(new UnauthorizedError('Invalid token'))
    }
  }
}

// REFRESH FLOW:
export async function refreshAccessToken(refreshToken: string) {
  let payload: TokenPayload
  try {
    payload = jwt.verify(refreshToken, env.JWT_REFRESH_SECRET) as TokenPayload
  } catch {
    throw new UnauthorizedError('Invalid refresh token')
  }

  // Check if refresh token has been revoked (store revoked JTIs in Redis)
  const isRevoked = await redis.get(`revoked:${payload.jti}`)
  if (isRevoked) throw new UnauthorizedError('Token revoked')

  const user = await userRepo.findById(payload.sub)
  if (!user || user.is_banned) throw new ForbiddenError('Account disabled')

  return issueTokens(user.id, user.role)
}

// LOGOUT — revoke the refresh token:
export async function logout(refreshToken: string) {
  try {
    const payload = jwt.verify(refreshToken, env.JWT_REFRESH_SECRET) as TokenPayload
    const ttl = payload.exp! - Math.floor(Date.now() / 1000)
    await redis.setex(`revoked:${payload.jti}`, ttl, '1')
  } catch {
    // Token already invalid — nothing to revoke
  }
}
```

# STEP 3 — ROLE-BASED ACCESS CONTROL (RBAC)

```typescript
// types/roles.ts
export type UserRole = 'viewer' | 'creator' | 'moderator' | 'admin'

// Define a permission matrix
const PERMISSIONS = {
  'video:create':  ['creator', 'admin'],
  'video:delete':  ['admin'],                       // only admins can force-delete
  'video:delete:own': ['creator', 'admin'],         // creators can delete their own
  'comment:delete:any': ['moderator', 'admin'],
  'user:ban':      ['moderator', 'admin'],
  'admin:panel':   ['admin'],
} as const

type Permission = keyof typeof PERMISSIONS

// middleware/authorize.ts
export function authorize(permission: Permission) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user) return next(new UnauthorizedError())
    
    const allowed = PERMISSIONS[permission] as readonly string[]
    if (!allowed.includes(req.user.role)) {
      return next(new ForbiddenError('Insufficient permissions'))
    }
    next()
  }
}

// OWNERSHIP CHECK (resource-level authorization):
export function requireOwnership(getOwnerId: (req: Request) => Promise<string>) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const ownerId = await getOwnerId(req)
      if (req.user!.id !== ownerId && req.user!.role !== 'admin') {
        return next(new ForbiddenError('Not your resource'))
      }
      next()
    } catch (err) {
      next(err)
    }
  }
}

// Usage in routes:
router.delete('/videos/:id', 
  authenticate,
  authorize('video:delete:own'),
  requireOwnership(async (req) => {
    const video = await videoRepo.findById(req.params.id)
    if (!video) throw new NotFoundError('Video')
    return video.owner_id
  }),
  ctrl.delete
)
```

# STEP 4 — OAUTH / SOCIAL LOGIN

```typescript
// Using Passport.js or a provider SDK (Auth0, Clerk recommended for simplicity)

// MANUAL GOOGLE OAUTH FLOW (if not using an auth library):
// 1. Redirect user to Google consent screen
// 2. Google redirects back with ?code=...
// 3. Exchange code for access token (server-to-server)
// 4. Fetch user profile from Google
// 5. Find or create user in your DB
// 6. Issue your own JWT pair

router.get('/auth/google', (req, res) => {
  const params = new URLSearchParams({
    client_id:     env.GOOGLE_CLIENT_ID,
    redirect_uri:  env.GOOGLE_REDIRECT_URI,
    response_type: 'code',
    scope:         'openid email profile',
    state:         generateState(),  // CSRF protection
  })
  res.redirect(`https://accounts.google.com/o/oauth2/v2/auth?${params}`)
})

router.get('/auth/google/callback', async (req, res) => {
  const { code, state } = req.query
  // 1. Verify state matches (CSRF protection)
  // 2. Exchange code for tokens
  const googleTokens = await exchangeCodeForTokens(code)
  // 3. Get user profile
  const profile = await getGoogleProfile(googleTokens.access_token)
  // 4. Find or create user
  const user = await authService.findOrCreateFromOAuth('google', profile.sub, profile.email)
  // 5. Issue your tokens
  const { accessToken, refreshToken } = issueTokens(user.id, user.role)
  // 6. Return tokens (via redirect with cookie, or JSON)
  res.cookie('refresh_token', refreshToken, { httpOnly: true, secure: true, sameSite: 'strict' })
  res.redirect(`${env.FRONTEND_URL}/auth/callback?token=${accessToken}`)
})
```

# STEP 5 — OWASP TOP 10 DEFENSES

```
1. INJECTION (SQL, NoSQL, Command)
   ✅ ALWAYS use parameterized queries or ORM — never string concatenation in SQL
   ✅ Validate and sanitize all user input (Zod schemas)
   ❌ NEVER: db.query(`SELECT * FROM users WHERE id = '${req.params.id}'`)
   ✅ ALWAYS: db.query('SELECT * FROM users WHERE id = $1', [req.params.id])

2. BROKEN AUTHENTICATION
   ✅ bcrypt with 12+ rounds for passwords
   ✅ Short-lived access tokens (15 min)
   ✅ Refresh token rotation and revocation
   ✅ Rate limit login endpoint (5 attempts per 15 min per IP)
   ✅ Lock account after 10 failed attempts

3. XSS (Cross-Site Scripting)
   ✅ React auto-escapes JSX by default — don't use dangerouslySetInnerHTML
   ✅ Set Content-Security-Policy header via helmet
   ✅ httpOnly cookies for refresh tokens (JS cannot access)
   ✅ Sanitize user-generated HTML if you render it (use DOMPurify)

4. IDOR (Insecure Direct Object References)
   ✅ ALWAYS verify ownership before allowing access to a resource
   ✅ Use UUIDs instead of sequential IDs to prevent enumeration
   ✅ Never trust client-provided user IDs — always read from req.user

5. SECURITY MISCONFIGURATION
   ✅ Remove X-Powered-By header (helmet does this)
   ✅ Never commit secrets to git — use .env files + secrets manager
   ✅ Different secrets for each environment (dev/staging/prod)
   ✅ Disable detailed error messages in production

6. SENSITIVE DATA EXPOSURE
   ✅ Never return password_hash in API responses
   ✅ HTTPS everywhere (use HSTS header)
   ✅ Encrypt PII at rest (database encryption)
   ✅ Never log sensitive data (tokens, passwords, PII)

7. CSRF (Cross-Site Request Forgery)
   ✅ JWT in Authorization header (not cookies) is immune to CSRF
   ✅ If using cookies: SameSite=Strict or SameSite=Lax + CSRF token
   ✅ Verify Origin/Referer headers on state-changing requests

8. RATE LIMITING
   ✅ Global: 100 req/min per IP
   ✅ Login: 5 attempts per 15 min per IP + per account
   ✅ Registration: 3 per hour per IP
   ✅ Upload: 10 per hour per user
   ✅ Return Retry-After header when rate limited
```

# STEP 6 — SECURITY HEADERS CHECKLIST

```typescript
// helmet() defaults handle most of these — verify each is set:
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc:  ["'self'"],         // no inline scripts
      imgSrc:     ["'self'", "data:", "https://your-cdn.com"],
      mediaSrc:   ["https://your-cdn.com"],
    }
  },
  hsts: { maxAge: 31536000, includeSubDomains: true },  // force HTTPS for 1 year
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
}))
```

# CHECKLIST — Before Moving to File & Media Handling

```
✅ Password hashing with bcrypt (12 rounds), timing-safe comparison
✅ JWT access tokens (15min) + refresh tokens (30 days, different secret)
✅ Refresh token revocation via Redis
✅ RBAC middleware with permission matrix
✅ Ownership checks for all resource mutations
✅ Rate limiting on auth endpoints
✅ All OWASP Top 10 items addressed
✅ Security headers via helmet()
✅ No sensitive data leaked in error responses
✅ No secrets in code — all in env vars
→ NEXT: 08-FileMediaHandling.md
```
