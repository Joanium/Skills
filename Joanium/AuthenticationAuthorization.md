---
name: Authentication & Authorization
trigger: authentication, authorization, JWT, OAuth2, session auth, RBAC, access control, login, password hashing, refresh token, bearer token, auth middleware, auth flow, secure auth, role-based access, PKCE, OpenID Connect
description: Implement secure authentication and authorization systems. Covers JWT (access + refresh tokens), session-based auth, OAuth2/OIDC flows, password hashing, RBAC, auth middleware, and security best practices.
---

# ROLE
You are a security-focused backend engineer. Your job is to implement authentication and authorization that is correct by default, hard to misconfigure, and follows industry standards. Most auth bugs are catastrophic — get this right.

# AUTH FUNDAMENTALS

## Authentication vs Authorization
```
AUTHENTICATION — who are you? (verify identity)
  → Passwords, tokens, biometrics, SSO

AUTHORIZATION — what can you do? (verify permission)
  → RBAC, ABAC, ownership checks, scopes
```

## Password Hashing — The Only Correct Approach
```typescript
import bcrypt from 'bcrypt'
// OR
import { hash, verify } from '@node-rs/argon2'  // faster, more modern

// bcrypt
const SALT_ROUNDS = 12   // balance between security and speed (~250ms at 12)

async function hashPassword(plaintext: string): Promise<string> {
  return bcrypt.hash(plaintext, SALT_ROUNDS)
}

async function verifyPassword(plaintext: string, hash: string): Promise<boolean> {
  return bcrypt.compare(plaintext, hash)
}

// NEVER:
// ✗ MD5, SHA1, SHA256 for passwords — not designed for this
// ✗ Store plaintext passwords
// ✗ Roll your own hashing algorithm
// ✗ Use the same salt for all passwords (bcrypt handles per-password salts)
```

# JWT — JSON WEB TOKENS

## Access + Refresh Token Pattern
```
Access Token:  short-lived (15 min), sent on every request
Refresh Token: long-lived (7-30 days), stored securely, used to get new access tokens

WHY:
- If access token is stolen, it expires in 15 min
- Refresh token is only sent to /auth/refresh, reducing exposure
- Logout = delete refresh token from server (stateful invalidation)
```

## Issuing Tokens
```typescript
import jwt from 'jsonwebtoken'

const ACCESS_SECRET  = process.env.JWT_ACCESS_SECRET!   // different secrets!
const REFRESH_SECRET = process.env.JWT_REFRESH_SECRET!

interface TokenPayload {
  userId: string
  email: string
  role: string
}

function issueAccessToken(payload: TokenPayload): string {
  return jwt.sign(payload, ACCESS_SECRET, {
    expiresIn: '15m',
    issuer: 'myapp',
    audience: 'myapp-client',
  })
}

function issueRefreshToken(userId: string): string {
  return jwt.sign({ userId }, REFRESH_SECRET, {
    expiresIn: '7d',
    issuer: 'myapp',
  })
}

// Verify access token
function verifyAccessToken(token: string): TokenPayload {
  try {
    return jwt.verify(token, ACCESS_SECRET, {
      issuer: 'myapp',
      audience: 'myapp-client',
    }) as TokenPayload
  } catch (err) {
    if (err instanceof jwt.TokenExpiredError) throw new Error('TOKEN_EXPIRED')
    if (err instanceof jwt.JsonWebTokenError)  throw new Error('TOKEN_INVALID')
    throw err
  }
}
```

## Auth Middleware (Express)
```typescript
import { Request, Response, NextFunction } from 'express'

// Augment Express Request type
declare global {
  namespace Express {
    interface Request {
      user?: TokenPayload
    }
  }
}

export function requireAuth(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization
  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ error: { code: 'MISSING_TOKEN' } })
  }

  const token = authHeader.slice(7)   // remove "Bearer "

  try {
    req.user = verifyAccessToken(token)
    next()
  } catch (err) {
    if (err instanceof Error && err.message === 'TOKEN_EXPIRED') {
      return res.status(401).json({ error: { code: 'TOKEN_EXPIRED' } })
    }
    return res.status(401).json({ error: { code: 'INVALID_TOKEN' } })
  }
}

// Role middleware
export function requireRole(...roles: string[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user) return res.status(401).json({ error: 'Unauthorized' })
    if (!roles.includes(req.user.role)) {
      return res.status(403).json({ error: { code: 'FORBIDDEN' } })
    }
    next()
  }
}

// Usage
router.get('/admin/users', requireAuth, requireRole('admin'), listUsers)
router.get('/profile', requireAuth, getProfile)
```

## Refresh Token Flow
```typescript
// Store refresh tokens in DB (allows revocation)
interface RefreshToken {
  token: string
  userId: string
  expiresAt: Date
  revokedAt: Date | null
}

async function login(email: string, password: string) {
  const user = await db.users.findByEmail(email)
  if (!user) throw new Error('INVALID_CREDENTIALS')  // generic — don't reveal if email exists

  const valid = await verifyPassword(password, user.passwordHash)
  if (!valid) throw new Error('INVALID_CREDENTIALS')

  const accessToken  = issueAccessToken({ userId: user.id, email: user.email, role: user.role })
  const refreshToken = issueRefreshToken(user.id)

  // Store refresh token hash (not plaintext) in DB
  await db.refreshTokens.create({
    token: await hashPassword(refreshToken),   // hash the refresh token too
    userId: user.id,
    expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
  })

  return { accessToken, refreshToken }
}

async function refresh(incomingToken: string) {
  let payload: { userId: string }
  try {
    payload = jwt.verify(incomingToken, REFRESH_SECRET) as { userId: string }
  } catch {
    throw new Error('INVALID_REFRESH_TOKEN')
  }

  // Find matching token in DB
  const tokens = await db.refreshTokens.findValid(payload.userId)
  const match = await Promise.any(
    tokens.map(async t => {
      const valid = await verifyPassword(incomingToken, t.token)
      if (!valid) throw new Error('no match')
      return t
    })
  ).catch(() => null)

  if (!match) throw new Error('REFRESH_TOKEN_NOT_FOUND')

  // Rotate: revoke old, issue new
  await db.refreshTokens.revoke(match.id)

  const user = await db.users.findById(payload.userId)
  const newAccessToken  = issueAccessToken({ userId: user.id, email: user.email, role: user.role })
  const newRefreshToken = issueRefreshToken(user.id)

  await db.refreshTokens.create({ /* ... store new one */ })

  return { accessToken: newAccessToken, refreshToken: newRefreshToken }
}

async function logout(userId: string) {
  // Revoke all refresh tokens for this user
  await db.refreshTokens.revokeAll(userId)
}
```

## Token Storage (Frontend)
```
ACCESS TOKEN:
  Store in memory (JS variable / React state) — safest
  ✗ NOT in localStorage — vulnerable to XSS (any JS can read it)
  ✗ NOT in sessionStorage — same problem

REFRESH TOKEN:
  Store in httpOnly cookie — JS can't read it, only sent automatically
  Cookie settings: httpOnly=true, secure=true, sameSite='strict', path='/auth/refresh'
  ✗ NOT in localStorage

httpOnly Cookie setup (Express):
```
```typescript
res.cookie('refreshToken', refreshToken, {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'strict',
  maxAge: 7 * 24 * 60 * 60 * 1000,  // 7 days in ms
  path: '/auth/refresh',             // only sent to this path
})
```

# SESSION-BASED AUTH (Alternative to JWT)
```typescript
// Use for: server-rendered apps, simpler architecture, when you need instant revocation
import session from 'express-session'
import RedisStore from 'connect-redis'
import { createClient } from 'redis'

const redisClient = createClient({ url: process.env.REDIS_URL })
await redisClient.connect()

app.use(session({
  store: new RedisStore({ client: redisClient }),
  secret: process.env.SESSION_SECRET!,
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production',
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000,   // 24 hours
    sameSite: 'strict',
  },
  name: '__Host-session',   // __Host- prefix = extra security for secure+path='/' cookies
}))

// Login
async function loginHandler(req, res) {
  const user = await validateCredentials(req.body.email, req.body.password)
  req.session.userId = user.id
  req.session.role   = user.role
  res.json({ success: true })
}

// Auth middleware
function requireSession(req, res, next) {
  if (!req.session.userId) return res.status(401).json({ error: 'Unauthorized' })
  next()
}

// Logout
function logoutHandler(req, res) {
  req.session.destroy(err => {
    res.clearCookie('__Host-session')
    res.json({ success: true })
  })
}
```

# OAUTH2 / OIDC — "Sign in with Google"

## Authorization Code Flow with PKCE (Correct Flow)
```typescript
import crypto from 'crypto'

// Step 1: Generate PKCE code verifier and challenge
function generatePKCE() {
  const verifier = crypto.randomBytes(32).toString('base64url')
  const challenge = crypto.createHash('sha256').update(verifier).digest('base64url')
  return { verifier, challenge }
}

// Step 2: Redirect user to OAuth provider
function startOAuthFlow(req, res) {
  const { verifier, challenge } = generatePKCE()
  const state = crypto.randomBytes(16).toString('hex')

  // Store verifier and state in session (to verify callback)
  req.session.pkceVerifier = verifier
  req.session.oauthState   = state

  const params = new URLSearchParams({
    client_id: process.env.GOOGLE_CLIENT_ID!,
    redirect_uri: 'https://myapp.com/auth/callback',
    response_type: 'code',
    scope: 'openid email profile',
    state,
    code_challenge: challenge,
    code_challenge_method: 'S256',
  })

  res.redirect(`https://accounts.google.com/o/oauth2/v2/auth?${params}`)
}

// Step 3: Handle callback
async function oauthCallback(req, res) {
  const { code, state } = req.query

  // Verify state (CSRF protection)
  if (state !== req.session.oauthState) {
    return res.status(400).json({ error: 'Invalid state' })
  }

  // Exchange code for tokens
  const tokenRes = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    body: new URLSearchParams({
      code: code as string,
      client_id: process.env.GOOGLE_CLIENT_ID!,
      client_secret: process.env.GOOGLE_CLIENT_SECRET!,
      redirect_uri: 'https://myapp.com/auth/callback',
      grant_type: 'authorization_code',
      code_verifier: req.session.pkceVerifier,  // PKCE verification
    }),
  })

  const { id_token } = await tokenRes.json()

  // Decode and verify ID token (use a library like jose)
  const { payload } = await jwtVerify(id_token, GOOGLE_JWKS, { issuer: 'https://accounts.google.com' })
  const { sub, email, name } = payload

  // Upsert user in your database
  const user = await db.users.upsert({ googleId: sub, email, name })

  // Issue your own session/tokens
  const { accessToken, refreshToken } = await issueTokens(user)
  // ...
}
```

# RBAC — ROLE-BASED ACCESS CONTROL
```typescript
// Define permissions per role
const PERMISSIONS = {
  admin: ['users:read', 'users:write', 'users:delete', 'posts:read', 'posts:write', 'posts:delete'],
  editor: ['posts:read', 'posts:write', 'users:read'],
  viewer: ['posts:read', 'users:read'],
} as const

type Role = keyof typeof PERMISSIONS
type Permission = (typeof PERMISSIONS)[Role][number]

function can(role: Role, permission: Permission): boolean {
  return (PERMISSIONS[role] as readonly string[]).includes(permission)
}

// Middleware factory
function requirePermission(permission: Permission) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user) return res.status(401).json({ error: 'Unauthorized' })
    if (!can(req.user.role as Role, permission)) {
      return res.status(403).json({ error: 'Forbidden', required: permission })
    }
    next()
  }
}

// Usage
router.delete('/users/:id', requireAuth, requirePermission('users:delete'), deleteUser)
router.put('/posts/:id', requireAuth, requirePermission('posts:write'), updatePost)

// Resource ownership check (combine with RBAC)
async function deletePost(req: Request, res: Response) {
  const post = await db.posts.findById(req.params.id)
  if (!post) return res.status(404).json({ error: 'Not found' })

  // Owner OR admin can delete
  const isOwner = post.authorId === req.user!.userId
  const isAdmin = req.user!.role === 'admin'
  if (!isOwner && !isAdmin) {
    return res.status(403).json({ error: 'Forbidden' })
  }

  await db.posts.delete(post.id)
  res.status(204).end()
}
```

# SECURITY CHECKLIST
```
Passwords:
[ ] bcrypt/argon2 with work factor ≥ 12
[ ] Minimum 8 chars, no maximum (hashing handles length)
[ ] Breach detection: check against HaveIBeenPwned API on registration
[ ] Rate limit login endpoint (5 attempts / 15 min per IP)

Tokens:
[ ] Access tokens expire in ≤ 15 minutes
[ ] Refresh tokens stored as bcrypt hash in DB (not plaintext)
[ ] Refresh tokens rotated on each use
[ ] Tokens signed with strong secret (≥ 256-bit random, different per type)
[ ] Verify iss, aud, exp claims on every request

Transport:
[ ] HTTPS everywhere (redirect HTTP → HTTPS)
[ ] HSTS header: Strict-Transport-Security: max-age=31536000; includeSubDomains
[ ] Tokens never in URLs (query params) — headers only

Session:
[ ] httpOnly + secure + sameSite=strict cookies
[ ] Regenerate session ID on login (session fixation prevention)
[ ] Session invalidation on logout
[ ] CSRF tokens for non-JSON form endpoints

General:
[ ] Never reveal if an email exists on login ("Invalid credentials" for both cases)
[ ] Implement account lockout after N failed attempts
[ ] Log auth events (login, logout, failed attempts, token refresh)
[ ] MFA support (TOTP with otplib or speakeasy)
```
