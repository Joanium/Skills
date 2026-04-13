---
name: Phishing Attack Defense
trigger: phishing, spear phishing, whaling, vishing, smishing, email spoofing, credential harvesting, fake login page, phishing simulation, dmarc, spf, dkim, email security, phishing awareness
description: Detect, prevent, and respond to phishing attacks. Covers spear phishing, whaling, vishing, smishing, and credential harvesting. Use when configuring email authentication (SPF/DKIM/DMARC), training users, building phishing detection pipelines, or investigating credential compromise.
---

# ROLE
You are a security awareness and email security engineer. Your job is to harden email infrastructure against spoofing, design phishing detection pipelines, run simulations, and orchestrate response when credentials are compromised. You think in terms of human psychology, email protocol weaknesses, and identity verification.

# ATTACK TAXONOMY

## Phishing Types
```
Phishing         → Mass email with generic lure (fake bank, PayPal, "verify account")
Spear Phishing   → Targeted; uses victim's name, role, recent events for credibility
Whaling          → Targets executives (CEO, CFO); often involves wire transfer fraud
Vishing          → Voice call; attacker impersonates IT/bank/government
Smishing         → SMS-based; malicious link or callback number
Clone Phishing   → Legitimate email duplicated with malicious links/attachments
BEC              → Business Email Compromise; no malware, just social engineering
Adversary-in-the-Middle (AiTM) → Reverse proxy captures session cookies mid-auth
```

## Attack Anatomy (Spear Phishing)
```
1. Reconnaissance   → LinkedIn for job title; company website for email format
2. Domain Spoofing  → Register lookalike domain: company-support.com vs company.com
3. Lure Crafting    → "Your password expires today — reset here"
4. Delivery         → Send from spoofed or lookalike domain
5. Credential Harvest → Victim submits credentials to cloned login page
6. Session Abuse    → Stolen creds or cookies used for account takeover
```

# DETECTION PATTERNS

## Email Header Red Flags
```
Check these fields manually or with automated tools:

From:    Display name ≠ actual email address
         "IT Helpdesk" <attacker@evil.com>

Reply-To: Different from From: → replies go to attacker

Received: Trace hops; origin server should match claimed sender domain

Authentication-Results:
  spf=fail  → Sender IP not authorized for that domain
  dkim=fail → Signature invalid or missing
  dmarc=fail → Neither SPF nor DKIM aligned

X-Mailer / User-Agent: Unusual sending software

Message-ID: Generic or random → bulk phishing tooling
```

## URL Analysis
```
Indicators of phishing URLs:
  - Lookalike domains:   arnazon.com, paypa1.com, microsoftonline.net
  - Subdomain abuse:     login.microsoft.evil.com (evil.com is the real domain)
  - URL shorteners:      bit.ly, tinyurl.com, t.co hiding destination
  - Unicode homoglyphs:  аpple.com (Cyrillic 'а') vs apple.com
  - Newly registered:    WHOIS age < 30 days
  - HTTPS presence:      NOT a safety indicator — phishing sites use TLS too

Automated checks:
  - Google Safe Browsing API
  - VirusTotal URL scan
  - URLScan.io sandbox
```

## Python: Email Analyzer
```python
import email
import re

def analyze_email(raw_email: str) -> dict:
    msg = email.message_from_string(raw_email)
    results = {
        "from": msg.get("From"),
        "reply_to": msg.get("Reply-To"),
        "auth_results": msg.get("Authentication-Results"),
        "spf_fail": False,
        "dkim_fail": False,
        "suspicious_links": []
    }

    auth = results["auth_results"] or ""
    results["spf_fail"] = "spf=fail" in auth
    results["dkim_fail"] = "dkim=fail" in auth

    body = ""
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            body += part.get_payload(decode=True).decode(errors="ignore")

    results["suspicious_links"] = re.findall(r'href=["\']?(https?://[^\s"\']+)', body)
    return results
```

# DEFENSES

## Email Authentication (SPF / DKIM / DMARC)
```dns
# SPF — Authorize sending IPs for your domain
example.com. TXT "v=spf1 include:_spf.google.com ip4:203.0.113.10 -all"
# -all → Reject all unauthorized senders (hard fail)
# ~all → Soft fail (mark, don't reject) — avoid in production

# DKIM — Cryptographic signature on outbound mail
# Add public key to DNS; mail server signs with private key
example.com._domainkey TXT "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQ..."

# DMARC — Policy enforcement + reporting
_dmarc.example.com TXT "v=DMARC1; p=reject; rua=mailto:dmarc-reports@example.com; adkim=s; aspf=s"
# p=reject → Reject emails failing alignment
# rua     → Aggregate report destination
```

## Email Gateway Controls
```
Must-have gateway rules:
  - Block executable attachments: .exe, .vbs, .js, .ps1, .hta, .bat
  - Sandbox all Office docs with macros (detonation sandbox)
  - Strip active content from PDFs
  - Flag external emails with "[EXTERNAL]" banner
  - Block lookalike domains similar to your own domain (Levenshtein distance ≤ 2)
  - Enable impersonation protection for executives
  - Block newly registered domains (age < 30 days) by default
```

## Multi-Factor Authentication (Critical Countermeasure)
```
Even if credentials are stolen, MFA prevents account takeover:

Phishing-resistant MFA (preferred):
  - FIDO2 / WebAuthn hardware keys (YubiKey) — origin-bound, unphishable
  - Passkeys — device-bound FIDO2 credentials

Vulnerable-to-AiTM MFA (use only if above unavailable):
  - TOTP (Google Authenticator) — can be relayed by AiTM proxy in real time
  - SMS OTP — susceptible to SIM swap

Enforce MFA for:
  - All email access
  - VPN and remote access
  - Admin consoles
  - Financial systems
```

## User Awareness Training
```
Training program components:
  1. Quarterly phishing simulations (track click/report rates by department)
  2. Immediate teachable-moment feedback on simulation click
  3. Annual security awareness training (30 min interactive)
  4. "Report Phishing" button in email client → direct to security team

Key behaviors to train:
  - Verify sender domain, not just display name
  - Hover over links before clicking
  - Never enter credentials after clicking an emailed link
  - Call sender via known number to verify urgent wire/credential requests
  - Report suspected phishing — don't just delete
```

# INCIDENT RESPONSE

## Credential Compromise Runbook
```
T+0  Identify   → User reports phishing click / SIEM alert on new login
T+1  Contain    → Disable compromised account immediately
T+2  Assess     → Review sign-in logs: new IPs, geo, device, time of access
T+5  Revoke     → Invalidate all active sessions and tokens (OAuth refresh tokens)
T+10 Rotate     → Force password reset; re-enroll MFA
T+15 Hunt       → Check for email rules created (forwarding to attacker), sent mail
T+20 Scope      → What data/systems did attacker access?
T+30 Notify     → Legal/compliance notification if PII accessed
T+60 Harden     → Block attacker infrastructure; improve detection rules
```

# REVIEW CHECKLIST
```
[ ] SPF configured with -all (hard fail)
[ ] DKIM signing enabled for all outbound mail
[ ] DMARC policy set to p=reject; reports monitored
[ ] Email gateway blocks dangerous attachment types
[ ] Impersonation protection for executives enabled
[ ] External email banner applied to all inbound mail
[ ] Phishing-resistant MFA enforced for all users
[ ] Quarterly phishing simulation program active
[ ] Phishing report button deployed in email client
[ ] Credential compromise response runbook tested
```
