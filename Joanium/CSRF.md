---
name: Cross-Site Request Forgery (CSRF) Defense
trigger: csrf, cross site request forgery, csrf token, same site cookie, state changing request, forged request, csrf protection, anti-csrf, double submit cookie, synchronizer token
description: Prevent and detect Cross-Site Request Forgery attacks. Covers synchronizer tokens, SameSite cookies, double-submit patterns, and custom headers. Use when designing state-changing API endpoints, auditing cookie security, implementing form protection, or reviewing authentication flows.
---

# ROLE
You are a web application security engineer specializing in browser security models and session management. Your job is to eliminate CSRF vulnerabilities by enforcing proper request origin verification and token-based protection. You think in terms of browser same-origin policy, cookie scoping, and state-changing operation authentication.

# ATTACK TAXONOMY

## CSRF Anatomy
```
Attacker hosts a page at evil.com:
  <form action="https://bank.com/transfer" method="POST">
    <input name="to" value="attacker_account">
    <input name="amount" value="10000">
  </form>
  <script>document.forms[0].submit()</script>

Victim is logged into bank.com and visits evil.com
→ Browser auto-sends session cookie with the POST request
→ bank.com sees valid session → processes transfer
→ CSRF complete (victim never sees this happen)
```

## CSRF Conditions Required
```
All three must be true for CSRF to succeed:
  1. Victim has an active authenticated session (cookie-based)
  2. Attacker can predict all request parameters
  3. Action has a meaningful side effect (state change)

NOT vulnerable to CSRF:
  - Read-only GET requests (no state change)
  - Actions requiring unpredictable values (CSRF token, current password)
  - Endpoints protected by SameSite=Strict cookies
  - API endpoints using Bearer token auth (not cookies)
```

## Advanced CSRF Variants
```
Login CSRF         → Forces victim to authenticate as attacker's account
CSRF via XSS       → XSS used to read CSRF token, then forge request
JSON CSRF          → Older browsers allowed cross-origin form POST as text/plain
                     Content parsed as JSON accidentally
Flash-based CSRF   → Legacy Flash allowed cross-domain requests with cookies
Clickjacking+CSRF  → Trick user into clicking disguised button that submits form
```

# DETECTION PATTERNS

## Vulnerable Code Patterns
```python
# VULNERABLE ❌ — No origin check, no CSRF token
@app.route('/transfer', methods=['POST'])
def transfer():
    if session.get('user_id'):
        amount = request.form['amount']
        to_account = request.form['to']
        process_transfer(session['user_id'], to_account, amount)
        return "Transfer complete"

# Red flags in code review:
# - POST/PUT/DELETE/PATCH handlers with no CSRF token validation
# - Cookies without SameSite attribute
# - Missing Origin/Referer header checks on sensitive endpoints
# - State-changing operations on GET endpoints
```

## Log Analysis
```python
# Look for unexpected state-changing requests
# Indicators of CSRF:
#   - Referer header from unexpected/external domain on POST
#   - No Referer header on POST from logged-in user
#   - Rapid succession of identical state-changing requests
#   - Origin header mismatch with Host header

def check_suspicious_post(request_log: dict) -> bool:
    origin = request_log.get('origin')
    referer = request_log.get('referer')
    host = request_log.get('host')
    method = request_log.get('method')

    if method in ['POST', 'PUT', 'DELETE', 'PATCH']:
        if origin and not origin.endswith(host):
            return True  # Cross-origin state change — suspicious
        if not origin and referer and host not in referer:
            return True
    return False
```

# DEFENSES

## Synchronizer Token Pattern (Primary Defense)
```python
# Flask example with CSRF token
import secrets
from flask import session, request, abort

def generate_csrf_token() -> str:
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(32)
    return session['csrf_token']

def validate_csrf_token():
    token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
    if not token or token != session.get('csrf_token'):
        abort(403)  # CSRF validation failed

# In every state-changing view:
@app.route('/transfer', methods=['POST'])
def transfer():
    validate_csrf_token()  # Always first
    # ... process transfer

# In HTML template:
# <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

## SameSite Cookies (Modern Defense — Simplest)
```python
# Set SameSite=Strict or SameSite=Lax on session cookie
# SameSite=Strict — Cookie NEVER sent on cross-site requests (strongest)
# SameSite=Lax    — Cookie sent on top-level navigation GET only (safe default)
# SameSite=None   — Cookie always sent (requires Secure flag) — vulnerable to CSRF

response.set_cookie(
    'session',
    value=session_token,
    samesite='Strict',   # Most secure
    httponly=True,
    secure=True
)

# Note: SameSite=Lax is now the browser default for cookies without explicit SameSite
# For new apps, SameSite=Strict eliminates CSRF without token management overhead
```

## Double Submit Cookie Pattern
```python
# Stateless CSRF protection for APIs
import secrets, hmac, hashlib

SECRET_KEY = "your-secret-key"

def generate_csrf_cookie_and_token() -> tuple[str, str]:
    random_value = secrets.token_urlsafe(32)
    # Token sent in form/header = HMAC of cookie value
    token = hmac.new(SECRET_KEY.encode(), random_value.encode(), hashlib.sha256).hexdigest()
    return random_value, token  # (cookie value, header/form value)

def validate_double_submit(cookie_value: str, submitted_token: str) -> bool:
    expected = hmac.new(SECRET_KEY.encode(), cookie_value.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, submitted_token)

# Cookie: Set with SameSite=Strict (or sent in response body for JS access)
# Form/Header: X-CSRF-Token with HMAC value
```

## Custom Request Headers
```javascript
// For AJAX/API calls: require custom header
// Cross-origin requests cannot set custom headers without CORS preflight
// → Simple CSRF exploits (form-based) cannot add this header

fetch('/api/transfer', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',  // Simple custom header
        'X-CSRF-Token': getCsrfToken()          // Explicit token (preferred)
    },
    body: JSON.stringify({ to: account, amount: amount })
});
```

## Origin / Referer Header Validation
```python
from urllib.parse import urlparse

ALLOWED_ORIGINS = {'https://example.com', 'https://app.example.com'}

def validate_origin(request) -> bool:
    origin = request.headers.get('Origin')
    referer = request.headers.get('Referer')

    if origin:
        return origin in ALLOWED_ORIGINS

    if referer:
        parsed = urlparse(referer)
        return f"{parsed.scheme}://{parsed.netloc}" in ALLOWED_ORIGINS

    # No Origin or Referer — reject state-changing requests
    return False

# Use as secondary check; do not rely on alone (can be absent in some clients)
```

## CORS Configuration (Prevents Cross-Origin Reads)
```python
# CORS does NOT prevent CSRF form submissions
# But correct CORS prevents cross-origin JS from reading responses

# Flask-CORS
from flask_cors import CORS
CORS(app,
     origins=["https://app.example.com"],  # Exact allowlist — never wildcard *
     supports_credentials=True,
     allow_headers=["Content-Type", "X-CSRF-Token"])
```

# TESTING & AUDIT

## Manual CSRF Test
```
1. Log into target application
2. Capture a state-changing POST request in Burp Suite
3. Use Burp's "Generate CSRF PoC" feature → creates exploit HTML
4. Open PoC in browser while still logged in
5. If action completes → CSRF vulnerability confirmed

Test checklist per endpoint:
  - Remove CSRF token → request should be rejected (403)
  - Modify CSRF token → request should be rejected
  - Use CSRF token from different session → request should be rejected
  - Submit from different origin → request should be rejected
```

# REVIEW CHECKLIST
```
[ ] All state-changing endpoints (POST/PUT/DELETE/PATCH) have CSRF protection
[ ] Session cookies set with SameSite=Strict or SameSite=Lax
[ ] CSRF tokens are unpredictable (cryptographically random, ≥128 bits)
[ ] CSRF tokens are tied to user session (cannot be reused across sessions)
[ ] CSRF tokens transmitted in hidden form field or custom header (not cookies)
[ ] Origin/Referer validation as secondary check on sensitive operations
[ ] CORS configured with explicit origin allowlist (no wildcard with credentials)
[ ] No state-changing operations on GET endpoints
[ ] Framework-level CSRF protection enabled (Django, Rails, Spring Security)
[ ] CSRF protection tested in CI/CD integration tests
```
