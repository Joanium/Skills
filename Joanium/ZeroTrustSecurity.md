---
name: Zero-Trust Security Architecture
trigger: zero trust, zero-trust, ZTA, never trust always verify, BeyondCorp, identity-aware proxy, ZTNA, microsegmentation, continuous verification, conditional access, least privilege, network perimeter, VPN replacement
description: Design zero-trust security architecture for modern infrastructure. Covers identity-centric access control, microsegmentation, device trust, continuous verification, and migration from perimeter-based security.
---

# ROLE
You are a senior security architect. Zero trust is not a product you buy — it's an architectural principle: never trust, always verify, regardless of network location. Your job is to translate that principle into concrete, implementable controls.

# THE CORE PRINCIPLE
```
PERIMETER SECURITY (old model):
  Outside firewall: untrusted ─────────┐
  Inside firewall:  trusted  ─────────►│ Corporate network → everything inside is trusted
                                       └─────────────────────────────────────────────────

ZERO TRUST (new model):
  There is no trusted zone. Every access request is treated as if it originates
  from an untrusted network, regardless of whether it comes from inside the
  corporate network or from the internet.

  User → request → Identity verified? Device trusted? Least privilege scope? Context OK?
                   All YES → allow, log, monitor
                   Any NO  → deny, alert, investigate
```

## The Five Pillars
```
1. IDENTITY:   Strong authentication on every request. MFA required. Short-lived tokens.
2. DEVICE:     Device health assessed before access. Unpatched = no access.
3. NETWORK:    Microsegmented. Services can only reach what they're explicitly permitted to reach.
4. APPLICATION: Access granted at the application level, not network level. No lateral movement.
5. DATA:       Data classified. Access controlled and logged per classification.
```

# IDENTITY & AUTHENTICATION

## Strong Identity Foundation
```
REQUIREMENTS:
  [ ] MFA enforced for all human users (phishing-resistant MFA preferred: FIDO2/WebAuthn)
  [ ] Single Sign-On (SSO) for all applications — no per-app passwords
  [ ] Machine identities: workload identity, not static API keys or passwords
  [ ] Short-lived credentials: JWT expiry < 1h, rotate service credentials frequently

MFA HIERARCHY (strongest to weakest):
  1. Hardware security key (YubiKey, FIDO2) — phishing-resistant
  2. TOTP app (Google Authenticator, 1Password) — acceptable
  3. Push notification app (Duo) — acceptable, watch for MFA fatigue attacks
  4. SMS OTP — avoid (SIM-swap attacks)
  5. No MFA — never

MACHINE IDENTITY OPTIONS:
  AWS:         IAM Roles for EC2/ECS/Lambda (no static keys)
  Kubernetes:  SPIFFE/SPIRE + Workload Identity
  GitHub CI:   OIDC tokens (no stored secrets in CI/CD)
  Service mesh: Istio mTLS with SPIFFE SVIDs (see ServiceMesh skill)
```

## Identity-Aware Proxy (IAP)
```
ARCHITECTURE:
  User → IAP (verifies identity + context) → Application
  Application never directly exposed — IAP is the only entry point

  IAP checks:
    ✓ Valid identity (SSO session + MFA)
    ✓ Device compliance (managed device? patched OS? disk encrypted?)
    ✓ Context (time of day, geolocation, behavior baseline)
    ✓ Authorization (does this identity have access to this resource?)

IMPLEMENTATIONS:
  Google BeyondCorp Enterprise — original IAP implementation
  Cloudflare Access           — zero-trust access for any application
  Teleport                    — infra access (SSH, k8s, databases) via zero-trust
  Pomerium                    — open-source IAP

EXAMPLE (Cloudflare Access):
  1. All internal apps sit behind Cloudflare Access
  2. No VPN needed — users access apps via browser
  3. Every request: verify SSO token → check device posture → check policy
  4. Policies per app: "Engineering group + enrolled device + MFA"
  5. Audit log: every access attempt, who, when, from where, device state
```

# DEVICE TRUST

## Device Posture Checks
```
Before granting access, verify:
  [ ] Device is enrolled in MDM (Mobile Device Management)
  [ ] OS is up to date (no major patches missing)
  [ ] Disk encryption enabled (FileVault / BitLocker)
  [ ] Antivirus / EDR agent running and healthy
  [ ] Screen lock enabled
  [ ] Firewall enabled
  [ ] Not jailbroken / rooted

POLICY EXAMPLE (Okta Device Trust):
  Policy: Access to production console
    IF device_managed = true
    AND os_version >= 14.0
    AND disk_encrypted = true
    AND last_check_in < 24h ago
    THEN allow
    ELSE deny + redirect to remediation instructions

IMPLEMENTATION OPTIONS:
  Okta Device Trust + Jamf (Mac/Mobile)
  Microsoft Intune + Conditional Access (Windows/Cross-platform)
  Kandji / Mosyle (Mac-focused)
  CrowdStrike Falcon (EDR + posture data feed to IAP)
```

# NETWORK MICROSEGMENTATION

## Replace Flat Networks
```
FLAT NETWORK (dangerous):
  Once inside (compromised credentials/device), attacker can reach everything
  Database server on same VLAN as web servers
  Lateral movement is easy

MICROSEGMENTED (zero-trust):
  Every service gets its own security boundary
  Service A can ONLY talk to Service B if explicitly allowed
  Default-deny on all traffic

  Implementation (Kubernetes NetworkPolicy):
```

```yaml
# Default deny all — must be applied to every namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}   # matches all pods
  policyTypes:
    - Ingress
    - Egress

---
# Explicitly allow: api-service → database only on port 5432
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-to-db
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: postgres
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: api-service
      ports:
        - protocol: TCP
          port: 5432
```

## Cloud Network Segmentation
```
AWS:
  VPC per environment (dev/staging/prod — no cross-VPC routing by default)
  Security Groups: stateful, per-resource rules (prefer over NACLs for simplicity)
  PrivateLink: expose services without routing through internet or peered VPC
  VPC Endpoints: S3, DynamoDB without internet routing

  Security Group Rules (principle of least privilege):
    ✓ Source: specific security group (not a CIDR range)
    ✗ Source: 0.0.0.0/0  (only for internet-facing load balancers on 443)
    ✗ Source: 10.0.0.0/8 (too broad — allows entire VPC to any service)

GCP:
  VPC Service Controls: define security perimeters around resources
  Org Policy constraints: restrict resource location, external access
  Private Service Connect: private access to Google APIs and services
```

# LEAST PRIVILEGE ACCESS

## Permission Design
```
PRINCIPLES:
  Grant minimum permissions needed for the task — nothing more
  Time-bound access: temporary elevation, not permanent admin
  Just-In-Time (JIT): request elevated access → approved → granted for N hours → expired
  Review regularly: unused permissions should be revoked automatically

ANTI-PATTERNS TO ELIMINATE:
  ✗ Shared accounts / credentials
  ✗ Permanent admin access — no one should have standing admin
  ✗ Broad IAM roles ("PowerUser" for a Lambda that only reads S3)
  ✗ Developer access to production databases directly

IAM POLICY EXAMPLE (AWS — principle of least privilege):
```

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadSpecificBucket",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-specific-bucket",
        "arn:aws:s3:::my-specific-bucket/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "true"
        }
      }
    }
  ]
}
```

```
JIT ACCESS TOOLS:
  AWS:         IAM Access Analyzer + temporary role sessions (STS AssumeRole)
  Teleport:    JIT access requests for SSH/k8s with approval workflow
  HashiCorp Vault: dynamic secrets (credentials generated on demand, auto-expire)
  Sym:         JIT access request workflows integrated with Slack
```

# CONTINUOUS VERIFICATION

## Session Monitoring
```
Zero trust verifies not just at login — but continuously:

SIGNALS TO MONITOR DURING SESSION:
  - User behavior baseline (typing speed, navigation patterns)
  - Impossible travel (logged in from NY, request from London 5min later)
  - Access pattern anomalies (downloading 10GB at 3am)
  - Device state change (MDM reports device no longer compliant)

RESPONSE TO ANOMALY:
  Low risk:    Log, continue session, flag for review
  Medium risk: Require re-authentication (step-up MFA)
  High risk:   Terminate session, lock account, notify security team

TOOLS:
  Okta ThreatInsight — behavioral analytics during session
  CrowdStrike Identity Protection — AD + session monitoring
  Cloudflare CASB — SaaS application access monitoring
```

# SECRETS MANAGEMENT

## No Static Secrets in Zero Trust
```
FORBIDDEN:
  ✗ API keys in environment variables that never rotate
  ✗ Database passwords in .env files or config repos
  ✗ Service accounts with non-expiring credentials
  ✗ Shared SSH keys among team members

REQUIRED:
  ✓ All secrets in a secrets manager (Vault, AWS Secrets Manager)
  ✓ Automatic secret rotation (every 30–90 days)
  ✓ Dynamic secrets generated on-demand (expire after use)
  ✓ Audit log for every secret access

DYNAMIC SECRETS (HashiCorp Vault):
  Application requests DB credentials → Vault generates unique credentials
  Credentials valid for 1 hour → auto-revoked after TTL
  Each service instance gets unique credentials
  Credential leak = limited blast radius (expires soon, unique per instance)
```

# MONITORING & AUDIT

## Zero-Trust Audit Requirements
```
LOG EVERYTHING:
  [ ] Every authentication attempt (success AND failure)
  [ ] Every authorization decision (allow AND deny)
  [ ] Every secrets access
  [ ] Every privileged action (admin operations)
  [ ] Device posture checks and results
  [ ] Policy changes and who made them

RETENTION:
  Security logs: 1 year minimum (SOC 2), 7 years for regulated industries
  Store in tamper-proof, append-only storage (WORM)
  Separate log account/project from operational accounts

ALERTS (tune for low false-positive rate):
  [ ] Account locked after N failures
  [ ] Access from new country/device
  [ ] Admin action outside business hours
  [ ] Bulk data export (high volume S3 download, DB dump)
  [ ] Failed MFA attempts (potential fatigue attack)
  [ ] Policy change: IAM permission added to production role
```

# MIGRATION ROADMAP
```
PHASE 1 — Identity (Month 1–2):
  [ ] Deploy SSO for all applications
  [ ] Enforce MFA for all users (start with phishing-resistant FIDO2 for admins)
  [ ] Eliminate shared accounts
  [ ] Inventory all service-to-service credentials

PHASE 2 — Device Trust (Month 2–3):
  [ ] Deploy MDM to all employee devices
  [ ] Implement device posture checks on IAP
  [ ] Block unmanaged devices from sensitive resources

PHASE 3 — Network Segmentation (Month 3–6):
  [ ] Implement default-deny network policies
  [ ] Deploy service mesh for service-to-service mTLS
  [ ] Remove direct developer SSH access → replace with Teleport/SSM

PHASE 4 — Secrets Hygiene (Month 4–6):
  [ ] Deploy HashiCorp Vault or cloud-native secrets manager
  [ ] Rotate all long-lived credentials
  [ ] Implement dynamic secrets for databases
  [ ] Remove all hardcoded credentials from code/configs

PHASE 5 — Continuous Verification (Month 6+):
  [ ] Deploy behavioral analytics
  [ ] Implement JIT access for all privileged operations
  [ ] Regular access reviews (quarterly at minimum)
  [ ] Automated access deprovisioning on role change / offboarding
```
