---
name: API Security OWASP
trigger: api security, owasp api, api vulnerabilities, secure api, broken object level authorization, BOLA, BFLA, api authentication security, api authorization, mass assignment, api hardening
description: Secure REST and GraphQL APIs against the OWASP API Security Top 10. Covers broken access control, authentication flaws, input validation, rate limiting, sensitive data exposure, and security testing.
---

# ROLE
You are a senior security engineer specializing in API security. APIs are the largest attack surface in modern applications — they expose business logic, hold sensitive data, and often have weaker protections than UI layers. Fix the root cause, not the symptom.

# OWASP API SECURITY TOP 10 — WITH FIXES

## API1: Broken Object Level Authorization (BOLA / IDOR)
```
PROBLEM: API accepts user-supplied ID and returns the object without checking ownership.

VULNERABLE:
  GET /api/orders/12345
  → Returns any order if you change the ID, even other users' orders

FIX: Always validate that the authenticated user owns or has permission to access the resource.

// Node.js example
router.get('/orders/:id', authenticate, async (req, res) => {
  const order = await Order.findById(req.params.id);

  // WRONG: just checking existence
  if (!order) return res.status(404).json({ error: 'NOT_FOUND' });

  // CORRECT: check ownership
  if (order.userId !== req.user.id && !req.user.hasRole('admin')) {
    return res.status(403).json({ error: 'FORBIDDEN' });
  }

  res.json({ data: order });
});

Use non-sequential IDs (UUIDs or Stripe-style prefixed IDs) to prevent enumeration,
but never rely on ID obscurity alone — always enforce authorization.
```

## API2: Broken Authentication
```
COMMON FLAWS:
  - No rate limiting on /login (unlimited brute-force)
  - JWT with weak secret (crackable offline)
  - JWT algorithm set to 'none' accepted
  - Long-lived tokens with no rotation
  - Passwords stored as MD5 or SHA1

FIX — JWT best practices:
  // Sign with RS256 (asymmetric) or HS256 with 256-bit secret minimum
  const token = jwt.sign(
    { sub: user.id, role: user.role },
    process.env.JWT_SECRET,  // min 32 random bytes
    {
      algorithm: 'HS256',
      expiresIn: '15m',       // short-lived access token
      issuer: 'api.myapp.com',
      audience: 'myapp-clients'
    }
  );

  // Verify strictly
  const payload = jwt.verify(token, process.env.JWT_SECRET, {
    algorithms: ['HS256'],    // explicitly allowlist — rejects 'none'
    issuer: 'api.myapp.com',
    audience: 'myapp-clients'
  });

FIX — Rate limit auth endpoints aggressively:
  // Express + rate-limit
  const loginLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,  // 15 minutes
    max: 10,                    // 10 attempts per IP per window
    message: { error: { code: 'TOO_MANY_ATTEMPTS', message: 'Try again in 15 minutes' } },
    standardHeaders: true,
  });
  router.post('/auth/login', loginLimiter, loginHandler);

FIX — Password storage:
  const hash = await bcrypt.hash(password, 12);   // bcrypt, cost factor 12+
  // OR: argon2.hash(password, { memoryCost: 65536, timeCost: 3 })
```

## API3: Broken Object Property Level Authorization (Mass Assignment)
```
PROBLEM: Client can set properties they shouldn't be able to (e.g., role, isAdmin).

VULNERABLE:
  PATCH /users/me
  Body: { "name": "Alice", "role": "admin" }  ← user setting their own role

FIX: Explicitly allowlist accepted fields. Never spread req.body directly.

// WRONG
await User.update(req.user.id, req.body);  // user can set anything

// CORRECT — pick only fields the user is allowed to change
const { name, email, bio } = req.body;
await User.update(req.user.id, { name, email, bio });

// With Zod for full validation + stripping
const UpdateUserSchema = z.object({
  name:  z.string().min(1).max(100).optional(),
  email: z.string().email().optional(),
  bio:   z.string().max(500).optional(),
  // role is NOT in this schema — even if sent, it's ignored
});

const updates = UpdateUserSchema.parse(req.body);
await User.update(req.user.id, updates);
```

## API4: Unrestricted Resource Consumption
```
PROTECT AGAINST: Large payloads, expensive queries, unlimited pagination, file bombs

// Limit request body size
app.use(express.json({ limit: '100kb' }));
app.use(express.urlencoded({ limit: '100kb', extended: true }));

// Paginate all list endpoints — never return unbounded result sets
const MAX_PAGE_SIZE = 100;
const limit = Math.min(parseInt(req.query.limit) || 25, MAX_PAGE_SIZE);

// Timeout expensive operations
const result = await Promise.race([
  runExpensiveQuery(params),
  new Promise((_, reject) =>
    setTimeout(() => reject(new Error('QUERY_TIMEOUT')), 5000)
  )
]);

// GraphQL — depth and complexity limits
import depthLimit from 'graphql-depth-limit';
import { createComplexityLimitRule } from 'graphql-validation-complexity';

const server = new ApolloServer({
  validationRules: [
    depthLimit(10),
    createComplexityLimitRule(1000),
  ]
});
```

## API5: Broken Function Level Authorization (BFLA)
```
PROBLEM: Low-privilege users can call admin-only endpoints.

VULNERABLE:
  DELETE /admin/users/:id   ← no role check, any authenticated user can delete

FIX — Role-based middleware:
  const requireRole = (...roles) => (req, res, next) => {
    if (!req.user || !roles.includes(req.user.role)) {
      return res.status(403).json({ error: { code: 'FORBIDDEN' } });
    }
    next();
  };

  router.delete('/admin/users/:id', authenticate, requireRole('admin'), deleteUser);
  router.get('/reports/revenue',    authenticate, requireRole('admin', 'finance'), getRevenue);

FIX — Check permissions at the resource level (ABAC for complex cases):
  const canRefundOrder = (user, order) =>
    user.role === 'admin' ||
    (user.role === 'support' && order.status !== 'delivered') ||
    (user.id === order.customerId && withinRefundWindow(order));

  if (!canRefundOrder(req.user, order)) {
    return res.status(403).json({ error: { code: 'REFUND_NOT_PERMITTED' } });
  }
```

## API6: Unrestricted Access to Sensitive Business Flows
```
PROTECT: Password reset, account creation, expensive operations from automation

// CAPTCHA on public, sensitive flows (or bot detection)
// IP-based rate limiting + behavioral analysis
// For SMS/email: rate limit per recipient, not per IP

const otpLimiter = rateLimit({
  windowMs: 60 * 60 * 1000,
  max: 5,
  keyGenerator: (req) => req.body.email || req.ip,  // per-email, not per-IP
});
router.post('/auth/send-otp', otpLimiter, sendOTP);
```

## API7: Server-Side Request Forgery (SSRF)
```
VULNERABLE: Any endpoint that fetches a user-supplied URL

PROTECT:
  - Allowlist of permitted external domains (never blocklist)
  - Block internal IP ranges before making any outbound request
  - Use a dedicated egress proxy with allowlist enforcement

import dns from 'dns/promises';
import ipRangeCheck from 'ip-range-check';

const BLOCKED_RANGES = [
  '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16',
  '127.0.0.0/8', '169.254.0.0/16', '::1/128'
];

async function isSafeUrl(urlStr: string): Promise<boolean> {
  const url = new URL(urlStr);  // throws if invalid
  const addresses = await dns.resolve4(url.hostname);
  return !addresses.some(ip => ipRangeCheck(ip, BLOCKED_RANGES));
}

router.post('/webhooks/test', async (req, res) => {
  const { url } = req.body;
  if (!(await isSafeUrl(url))) {
    return res.status(400).json({ error: { code: 'UNSAFE_URL' } });
  }
  // proceed to fetch
});
```

## API8: Security Misconfiguration
```
COMMON ISSUES:
  - CORS set to * in production
  - Debug endpoints exposed (/actuator, /swagger, /__debug)
  - Stack traces in error responses
  - Default credentials unchanged
  - Unnecessary HTTP methods enabled

FIX — CORS:
  app.use(cors({
    origin: ['https://app.mycompany.com', 'https://admin.mycompany.com'],
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
  }));

FIX — Security headers:
  app.use(helmet());  // sets X-Frame-Options, X-Content-Type-Options, etc.
  // or manually:
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');

FIX — Never leak stack traces in production:
  app.use((err, req, res, next) => {
    logger.error({ err, requestId: req.id }, 'Unhandled error');
    res.status(500).json({
      error: {
        code: 'INTERNAL_ERROR',
        message: 'An unexpected error occurred',
        requestId: req.id,  // correlate to logs, but don't expose internals
      }
    });
  });
```

## API9: Improper Inventory Management
```
RISKS: Old API versions still running, shadow APIs, undocumented endpoints

FIX:
  - Maintain OpenAPI spec as source of truth — generate from code, not docs
  - API gateway routes inventory all endpoints
  - Sunset old versions: return Sunset and Deprecation headers
  - Periodic audit: compare spec against actual routes in production
  - Decommission unused endpoints — don't just ignore them
```

## API10: Unsafe Consumption of APIs
```
RISK: Trusting data from third-party APIs without validation

FIX — Treat external API data as untrusted:
  const ThirdPartyUserSchema = z.object({
    id:    z.string(),
    email: z.string().email(),
    name:  z.string().max(200),
  });

  const rawData = await thirdPartyClient.getUser(id);
  const user = ThirdPartyUserSchema.parse(rawData);  // throws on invalid data
```

# SECURITY HEADERS REFERENCE
```http
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: default-src 'none'; frame-ancestors 'none'
Referrer-Policy: no-referrer
Permissions-Policy: camera=(), microphone=(), geolocation=()
Cache-Control: no-store  (for sensitive endpoints)
```

# API SECURITY CHECKLIST
```
Authentication & Authorization:
  [ ] All endpoints require authentication (except explicitly public ones)
  [ ] Object-level authorization on every resource endpoint
  [ ] Function-level roles enforced (not just authenticated)
  [ ] JWT: short expiry, strong algorithm, explicit allowlist

Input & Output:
  [ ] Schema validation on every request body (Zod, Joi, etc.)
  [ ] Mass assignment prevented — explicit field allowlists
  [ ] Sensitive fields excluded from responses (password hash, SSN, tokens)
  [ ] Error messages don't reveal internal structure or stack traces

Transport & Headers:
  [ ] HTTPS enforced — HTTP redirects to HTTPS
  [ ] CORS locked to known origins
  [ ] Security headers set on all responses

Rate Limiting & DoS:
  [ ] Rate limits on all endpoints, stricter on auth/payment flows
  [ ] Request body size limits
  [ ] Pagination limits enforced
  [ ] Timeout on long-running operations

Operations:
  [ ] All API endpoints in registry / OpenAPI spec
  [ ] Old versions formally deprecated with Sunset headers
  [ ] Authentication failures and 403s logged and alerted on
  [ ] API keys rotatable without downtime
```
