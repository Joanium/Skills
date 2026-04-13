---
name: Brute Force & Credential Stuffing Defense
trigger: brute force, credential stuffing, password spraying, account lockout, login rate limiting, password cracking, dictionary attack, rainbow table, account takeover, breached credentials, have i been pwned, login anomaly detection
description: Prevent and detect brute force attacks, credential stuffing, and password spraying. Covers account lockout, CAPTCHA, anomaly detection, and breached password screening. Use when designing authentication systems, auditing login endpoints, detecting account takeover, or responding to large-scale credential attacks.
---

# ROLE
You are an identity and authentication security engineer. Your job is to harden login systems against automated credential attacks while maintaining legitimate user access. You think in terms of attacker economics — making attacks unprofitable through friction, detection, and rapid lockout without degrading UX for real users.

# ATTACK TAXONOMY

## Attack Types
```
Brute Force         → Try all possible passwords systematically (slow, noisy)
Dictionary Attack   → Try wordlist of common passwords / leaked passwords
Credential Stuffing → Replay username:password pairs from data breaches (high success rate)
Password Spraying   → Try ONE common password against MANY accounts (avoids lockout per-user)
Reverse Brute Force → Fix password "Password1!" and cycle usernames
Rainbow Table       → Precomputed hash → plaintext lookup (defeated by salting)
Credential Cracking → Offline attack on stolen hash database
```

## Credential Stuffing Scale
```
Attack economics:
  - Attacker buys breach dataset: 100M credentials for $20 on dark web
  - Uses automated tool (Sentry MBA, OpenBullet) for parallel testing
  - Success rate: 0.5–2% of tested credentials (500K–2M accounts)
  - Proxied through residential proxies → each IP appears legitimate

Detection challenge:
  - Each IP may make only 1–5 requests (matches normal behavior)
  - Valid username/password → no error → less visible than brute force
  - Distributed across thousands of IPs and ASNs
```

# DETECTION PATTERNS

## Signals and Thresholds
```
Per-account signals:
  - N failed logins from different IPs in T minutes
  - Successful login from new country/ASN/device
  - Login at unusual time vs historical pattern
  - Multiple accounts logged in from same IP

Global signals:
  - Login failure rate spike across all accounts
  - High ratio of failed:successful logins (baseline: < 5:1)
  - Unusual geographic distribution of login attempts
  - Known bad IP/ASN (proxy, Tor exit node, cloud/datacenter IP)
  - Many accounts receiving first-time logins from same IP block
```

## Anomaly Detection (Python)
```python
from collections import defaultdict
import time

login_attempts = defaultdict(list)  # {username: [timestamps]}
ip_attempts = defaultdict(set)       # {ip: set of usernames tried}

MAX_FAILS_PER_USER = 5
WINDOW_SECONDS = 300
SPRAY_THRESHOLD = 50  # IPs trying >50 accounts

def check_brute_force(username: str, ip: str, success: bool) -> dict:
    now = time.time()
    window_start = now - WINDOW_SECONDS

    # Per-user rate check
    login_attempts[username] = [t for t in login_attempts[username] if t > window_start]
    if not success:
        login_attempts[username].append(now)

    ip_attempts[ip].add(username)

    return {
        "lockout": len(login_attempts[username]) >= MAX_FAILS_PER_USER,
        "spray_detected": len(ip_attempts[ip]) >= SPRAY_THRESHOLD,
        "fail_count": len(login_attempts[username])
    }
```

# DEFENSES

## Account Lockout & Progressive Delay
```python
import time
from functools import wraps

LOCKOUT_THRESHOLD = 5      # Failures before lockout
LOCKOUT_DURATION = 900     # 15 minutes
PROGRESSIVE_DELAYS = [0, 0, 1, 2, 5, 10]  # Seconds delay per attempt

failed_attempts = {}  # {username: {"count": int, "locked_until": float}}

def get_login_delay(attempt_count: int) -> int:
    idx = min(attempt_count, len(PROGRESSIVE_DELAYS) - 1)
    return PROGRESSIVE_DELAYS[idx]

def check_lockout(username: str) -> bool:
    record = failed_attempts.get(username, {})
    if record.get("locked_until", 0) > time.time():
        return True  # Still locked
    return False

def record_failure(username: str):
    record = failed_attempts.setdefault(username, {"count": 0})
    record["count"] += 1
    if record["count"] >= LOCKOUT_THRESHOLD:
        record["locked_until"] = time.time() + LOCKOUT_DURATION

def record_success(username: str):
    failed_attempts.pop(username, None)  # Reset on success

# Production: store in Redis with TTL for distributed systems
```

## CAPTCHA Strategy
```
Tiered CAPTCHA approach (balance security vs UX):

Tier 0 — No CAPTCHA:    First 2 failed attempts (normal user typos)
Tier 1 — Invisible:     Attempts 3-4 (Cloudflare Turnstile, hCaptcha invisible)
Tier 2 — Challenge:     Attempt 5+ (visible puzzle challenge)
Tier 3 — Lockout:       Attempt 6+ (time-based lockout + email verification)

For password spraying detection:
  - Trigger CAPTCHA based on IP-level failure rate, not just per-account
  - Challenge IPs with >10 failed logins across any accounts in 5 minutes
```

## Multi-Factor Authentication
```
MFA completely defeats credential stuffing for enrolled accounts
— Even valid username:password cannot log in without the second factor

Deployment priority:
  1. Admin accounts — mandatory, immediate
  2. Privileged/finance users — mandatory
  3. All users — mandatory (with grace period)

Phishing-resistant MFA (strongest):
  - FIDO2 / Passkeys — bound to origin domain; cannot be replayed

Acceptable MFA:
  - TOTP (authenticator app)
  - Push notification (Duo, Okta Verify)

Avoid:
  - SMS OTP (SIM swap risk)
```

## Breached Password Screening
```python
import hashlib
import requests

def is_pwned_password(password: str) -> bool:
    """Check Have I Been Pwned API (k-anonymity — full hash never sent)"""
    sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]

    response = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}")
    for line in response.text.splitlines():
        hash_suffix, count = line.split(":")
        if hash_suffix == suffix:
            return True  # Password appears in breach database
    return False

# Block registration and force password reset if breached
def validate_new_password(password: str) -> bool:
    if is_pwned_password(password):
        raise ValueError("This password was found in a data breach. Choose another.")
    return True
```

## Password Policy (Modern NIST Guidelines)
```
NIST SP 800-63B recommendations:
  ✅ Minimum 8 characters (12+ encouraged)
  ✅ Allow up to 64 characters
  ✅ Allow all printable ASCII + Unicode
  ✅ Check against breach databases (HIBP)
  ✅ Check against common passwords list
  ✅ No forced periodic rotation (causes weaker passwords)
  ❌ Do NOT require complexity rules (uppercase + symbol + number)
     — Users just do: Password1! → complexity met but weak
  ❌ Do NOT use security questions

Password hashing (server-side):
  Use: bcrypt (cost ≥12), scrypt, Argon2id
  Never: MD5, SHA1, SHA256 (unsalted), plain text
```

## Secure Password Hashing
```python
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)  # Cost factor 12 — ~250ms per hash
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), stored_hash.encode())
    # bcrypt.checkpw is timing-safe — prevents timing attacks
```

## IP Reputation and Velocity Controls
```python
import requests

KNOWN_PROXY_ASN = {
    "AS14061",  # DigitalOcean
    "AS16509",  # Amazon AWS
    # Add Tor exit node list, known proxy ASNs
}

def assess_ip_risk(ip: str) -> str:
    # Use IP reputation service (AbuseIPDB, IPQualityScore, Cloudflare)
    response = requests.get(
        f"https://api.abuseipdb.com/api/v2/check",
        params={"ipAddress": ip, "maxAgeInDays": 30},
        headers={"Key": API_KEY}
    )
    data = response.json()["data"]
    if data["abuseConfidenceScore"] > 50:
        return "high_risk"
    if data.get("isTor") or data.get("isVpn"):
        return "proxy"
    return "normal"
```

# INCIDENT RESPONSE

## Active Credential Stuffing Attack
```
T+0  Detect     → Alert: login failure rate >10x baseline
T+1  Assess     → Confirm credential stuffing (diverse IPs, targeted accounts)
T+2  Rate Limit → Apply aggressive rate limiting on login endpoint at WAF
T+3  Block      → Block known-bad ASNs, datacenter IP ranges
T+5  CAPTCHA    → Enable CAPTCHA for all logins globally
T+10 Notify     → Identify successfully compromised accounts
T+15 Contain    → Force password reset + MFA re-enrollment for compromised accounts
T+20 Analyze    → Determine breach source (correlate with known breaches)
T+30 Communicate → Notify affected users; advise password manager usage
T+60 Harden     → Deploy MFA mandate; integrate HIBP password screening
```

# REVIEW CHECKLIST
```
[ ] Progressive lockout/delay on failed login (resistant to password spraying)
[ ] Per-IP login rate limiting at WAF and application layer
[ ] CAPTCHA triggered on suspicious login patterns
[ ] MFA enforced for all accounts (FIDO2 preferred)
[ ] Breached password check at registration and password change
[ ] Passwords hashed with bcrypt/Argon2id (cost factor appropriate)
[ ] No plain-text or reversibly encrypted password storage
[ ] Login anomaly detection alerts configured (new country, new device)
[ ] IP reputation check integrated
[ ] Timing-safe comparison used in credential verification
[ ] Login failure reason does not distinguish valid vs invalid username
```
