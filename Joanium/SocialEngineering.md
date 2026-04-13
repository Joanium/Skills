---
name: Social Engineering Defense
trigger: social engineering, pretexting, impersonation, tailgating, baiting, quid pro quo, vishing, security awareness, insider threat, human factor security, identity verification, callback verification, security culture
description: Prevent, detect, and respond to social engineering attacks. Covers pretexting, impersonation, tailgating, baiting, vishing, and insider threats. Use when building security awareness programs, designing identity verification procedures, auditing physical security, or investigating social engineering incidents.
---

# ROLE
You are a security awareness and human risk management specialist. Your job is to reduce the human attack surface through training, procedural controls, and detection mechanisms. You think in terms of psychological manipulation tactics, organizational trust relationships, and verification process design.

# ATTACK TAXONOMY

## Social Engineering Techniques
```
Pretexting        → Fabricated scenario to establish trust (fake IT, HR, vendor)
Impersonation     → Posing as trusted individual in person or by phone
Tailgating        → Following authorized person through secure door without badge
Baiting           → Leaving malicious USB drives or media for victims to find
Quid Pro Quo      → "I'll fix your computer if you give me your password"
Vishing           → Phone-based deception (fake bank, IT, IRS)
Smishing          → SMS-based deception (see Phishing skill)
Watering Hole     → Compromise website frequented by target organization
Reverse SE        → Create problem, offer to solve it, gain access during "fix"
BEC               → Impersonate executive to authorize wire transfers
```

## Psychological Principles Exploited
```
Authority      → "This is the CTO — I need access NOW"
Urgency        → "Your account will be deleted in 1 hour"
Scarcity       → "Only you can authorize this — no one else is available"
Reciprocity    → "I helped you last time — now I need a small favor"
Social proof   → "Everyone else in your team has already done this"
Liking         → Building rapport before making the request
Fear           → "You'll be fired if this audit fails"
```

## BEC (Business Email Compromise) Anatomy
```
1. Attacker researches company: CEO name, CFO name, wire transfer processes
2. Registers lookalike domain: c0mpany.com instead of company.com
3. Sends email from CEO to CFO: "Urgent wire transfer needed for acquisition"
4. CFO processes payment to attacker account
5. Average loss: $75,000 per incident; $2.7B total industry losses (FBI IC3 2022)

Variants:
  CEO fraud       → CFO receives wire transfer request from "CEO"
  Vendor fraud    → Supplier "requests" updated payment details
  Payroll redirect → HR receives "employee" payroll redirect request
  Attorney fraud  → Fake legal counsel requests confidential action
```

# DETECTION PATTERNS

## Behavioral Indicators
```
In-person red flags:
  - Unfamiliar person claiming to be contractor/vendor without appointment
  - Excessive urgency to bypass normal check-in procedures
  - Name-dropping senior executives to pressure staff
  - Reluctance to provide ID or follow visitor procedures
  - Tailgating through secured doors or holding door for others

Phone/email red flags:
  - Request for credentials, passwords, or MFA codes
  - Urgency pressure to bypass normal verification
  - Caller cannot answer basic verification questions
  - Request to keep conversation confidential
  - Sender email doesn't match claimed organization
  - Financial request with unusual urgency or secrecy

Insider threat indicators:
  - Downloading unusually large volumes of data
  - Accessing resources outside normal job scope
  - Working odd hours with unexplained network activity
  - Expressing grievance + discussing competitors
  - Attempts to access systems after resignation notice
```

## Identity Verification Procedures
```python
# Structured callback verification for sensitive requests

VERIFICATION_REQUIREMENTS = {
    "password_reset": ["employee_id", "manager_approval", "callback_to_hr_system"],
    "wire_transfer": ["dual_authorization", "callback_to_known_number", "email_confirmation"],
    "access_grant":  ["ticket_number", "manager_email_approval", "badge_registration"],
    "data_export":   ["business_justification", "manager_approval", "dlp_policy_check"],
}

def verify_request(request_type: str, caller_claims: dict) -> dict:
    required = VERIFICATION_REQUIREMENTS.get(request_type, [])
    missing = [r for r in required if r not in caller_claims]
    return {
        "approved": len(missing) == 0,
        "missing_verifications": missing,
        "action": "Proceed" if not missing else "Decline and escalate"
    }
```

# DEFENSES

## Verification Procedures
```
Callback Verification for Sensitive Requests:
  1. Do NOT use callback number provided by caller
  2. Look up number independently (company directory, badge system, LinkedIn)
  3. Call back on verified number before taking any action
  4. Document: who called, what was requested, verification performed

Wire Transfer / Financial:
  - NEVER process based on email alone — always call to verify
  - Use out-of-band confirmation (call on known number, NOT the one in the email)
  - Implement dual authorization for transfers above threshold
  - Allow 24-hour cooling period for new payee setup

Password/Access Reset:
  - Require employee ID + manager approval via separate channel
  - Never reset password based on phone call alone
  - Use identity verification system (Okta Verify, hardware token)
  - Log all help desk password resets and audit weekly

Physical Access:
  - Require all visitors to sign in with valid photo ID
  - Escort all non-employees at all times
  - Never hold doors for anyone — everyone must badge in individually
  - Challenge anyone in secure area without visible badge
```

## Security Awareness Training Program
```
Training cadence:
  Onboarding:         2-hour mandatory security awareness course
  Annual:             30-min refresher (updated with current threats)
  Monthly:            10-min micro-learning module
  Triggered:          Immediate training on simulation failure

Simulation program:
  Frequency:          Monthly phishing + quarterly vishing simulations
  Metrics tracked:    Click rate, report rate, department comparison
  Response:           Immediate teachable moment on failure (not shame)
  Improvement target: Click rate < 5%; report rate > 70%

Topics to cover:
  - Recognizing social engineering tactics
  - Verification procedures for sensitive requests
  - Physical security (tailgating, clean desk)
  - Password hygiene and MFA
  - Safe USB/media handling
  - Reporting suspicious contacts (no blame culture)
```

## Physical Security Controls
```
Layered physical access:
  Reception → Verified visitor badge + escort
  Office floor → Employee badge only
  Server room → Badge + PIN + camera
  Data center → Badge + biometric + mantrap

Deterrents and detection:
  - Security cameras at all entry/exit points
  - Visitor log with ID verification
  - Mantrap (double-door entry) at sensitive areas
  - Clean desk policy — no credentials or sensitive docs visible
  - Screen lock policy (15 min auto-lock + proximity lock)
  - Secure disposal — shred documents, degauss drives

Countermeasures:
  - Anti-tailgating turnstiles or security guard challenge policy
  - "If you see something, say something" culture
  - All employees trained to challenge unfamiliar persons politely
```

## Insider Threat Program
```
Technical controls:
  - DLP (Data Loss Prevention) on email, USB, cloud uploads
  - UEBA (User and Entity Behavior Analytics) — alerts on anomalous data access
  - Privileged access management (PAM) — record all admin sessions
  - Access reviews quarterly — remove access no longer needed
  - Separation of duties on financial and sensitive operations

Process controls:
  - Background checks before hiring (refreshed for high-privilege roles)
  - Two-person integrity rule for critical systems
  - Offboarding checklist: revoke all access on last day (not last week)
  - Exit interviews and access termination workflow

Monitoring:
  - Alert on bulk file downloads (>500 files in 1 hour)
  - Alert on access to systems outside normal job role
  - Alert on logins at unusual hours from sensitive system owners
  - Alert on USB mass storage use on endpoints with sensitive data
```

## BEC Prevention Workflow
```
Email controls:
  - DMARC p=reject to prevent exact domain spoofing
  - Block lookalike domains similar to your own (Levenshtein ≤ 2)
  - Add [EXTERNAL] banner to all inbound email
  - Flag executive name in email from external domain

Financial controls:
  - Out-of-band verification for ALL wire transfers > $X
  - Dual authorization required for transfers > $Y
  - New payee: 48-hour hold + phone verification
  - Payee change request: verify via known phone number, not email

Example verification policy:
  Any wire transfer request received via email MUST be:
  1. Verified with requestor via phone using number from company directory
  2. Approved by two authorized signatories
  3. Logged with verification evidence before processing
```

# INCIDENT RESPONSE

## Social Engineering Incident Response
```
T+0  Report    → Employee reports suspicious call/request/visit
T+1  Assess    → What was requested? Was it fulfilled? What access was given?
T+2  Contain   → If access/credentials provided: lock accounts, revoke access immediately
T+5  Preserve  → Collect: call logs, email headers, visitor logs, CCTV footage
T+10 Identify  → What data/systems may have been compromised?
T+15 Notify    → HR, legal, management (and law enforcement if financial loss)
T+20 Recover   → Restore access with proper controls; issue new credentials
T+30 Learn     → Brief all staff on tactic used; update verification procedures
T+60 Measure   → Track report rate improvement in next simulation cycle
```

# REVIEW CHECKLIST
```
[ ] All staff trained on social engineering recognition at onboarding
[ ] Annual security awareness training completed by all staff
[ ] Monthly phishing simulations running; click rate tracked
[ ] Quarterly vishing simulations conducted
[ ] Callback verification procedure documented for sensitive requests
[ ] Wire transfer requires out-of-band verification + dual authorization
[ ] Password reset requires identity verification beyond phone call alone
[ ] Physical security: visitor sign-in, escort policy, badge required
[ ] Clean desk policy enforced
[ ] DLP monitoring for bulk data exfiltration
[ ] UEBA alerts for anomalous user behavior
[ ] Offboarding checklist: access revoked on final day
[ ] No-blame reporting culture established (high report rate target)
```
