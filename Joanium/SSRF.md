---
name: Server-Side Request Forgery (SSRF) Defense
trigger: ssrf, server side request forgery, internal service access, metadata endpoint, cloud metadata ssrf, url fetch vulnerability, blind ssrf, request forgery, internal network scan, aws metadata, imds
description: Prevent and detect Server-Side Request Forgery attacks. Covers classic SSRF, blind SSRF, cloud metadata endpoint abuse, and internal service enumeration. Use when auditing URL-fetching code, designing allowlist policies, reviewing cloud application security, or responding to SSRF-enabled data breaches.
---

# ROLE
You are a cloud and application security engineer specializing in server-side request controls. Your job is to eliminate SSRF vulnerabilities in URL-fetching code, enforce network-level egress controls, and detect attempts to abuse server-side HTTP clients to access internal resources. You think in terms of network trust zones, cloud metadata exposure, and URL parsing edge cases.

# ATTACK TAXONOMY

## SSRF Types
```
Classic SSRF      → Attacker controls URL; response returned to them directly
Blind SSRF        → Request made but no response returned — inferred via timing/DNS/OOB
Partial SSRF      → Attacker controls only part of URL (path, query, scheme)
Cloud SSRF        → Targets cloud metadata endpoint (169.254.169.254) for credentials
Internal SSRF     → Port scans and accesses internal services (Redis, Memcached, Kubernetes)
Protocol SSRF     → Uses non-HTTP schemes: file://, dict://, gopher://, ftp://
```

## Classic SSRF Anatomy
```
Vulnerable feature: "Import article from URL"

Application code:
  url = request.POST['url']
  response = requests.get(url)        # No validation — fetches any URL
  return response.content

Attacker submits:
  url = "http://169.254.169.254/latest/meta-data/iam/security-credentials/"
                ↑ AWS Instance Metadata Service (IMDS)

Application fetches it, returns to attacker:
  {"AccessKeyId": "AKIA...", "SecretAccessKey": "...", "Token": "..."}
  → Full AWS IAM credentials → cloud account compromise
```

## Internal Service Targets
```
Cloud metadata:
  AWS IMDS:     http://169.254.169.254/latest/meta-data/
  GCP metadata: http://metadata.google.internal/computeMetadata/v1/
  Azure IMDS:   http://169.254.169.254/metadata/instance?api-version=2021-02-01

Internal services commonly exposed via SSRF:
  Redis:        redis://127.0.0.1:6379/   → RCE via RESP protocol
  Memcached:    http://127.0.0.1:11211/
  Elasticsearch: http://127.0.0.1:9200/_cat/indices
  Kubernetes API: https://kubernetes.default.svc/api/v1/
  Jenkins:      http://127.0.0.1:8080/
  Admin panels: http://127.0.0.1:8080/admin
  Internal APIs: http://internal-service.prod/api/admin/
```

## URL Parsing Confusion (Bypasses)
```
Numeric IP bypass:       http://2130706433/  (decimal form of 127.0.0.1)
Octal bypass:            http://0177.0.0.1/  (octal 127)
IPv6 bypass:             http://[::1]/
IPv6 compressed:         http://[::ffff:169.254.169.254]/
DNS rebinding:           good.attacker.com resolves to 169.254.169.254 after validation
Scheme variations:       file:///etc/passwd
URL fragments:           http://evil.com#https://allowed.com
Redirect chain:          evil.com/redirect → 127.0.0.1:6379
Subdomain bypass:        169.254.169.254.evil.com → resolves to 169.254.169.254
```

# DETECTION PATTERNS

## Code Review Red Flags
```python
# Dangerous patterns to flag:
import requests, urllib, httpx

# Any URL parameter taken from user input:
url = request.args.get('url')
response = requests.get(url)        # Immediate SSRF risk

# Webhook implementations:
target = user_config['webhook_url']
requests.post(target, json=event_data)  # SSRF if not validated

# Image/document processing:
image_url = post_data['avatar_url']
download_file(image_url)            # SSRF in file import features

# PDF generation with user HTML:
html = f'<img src="{user_input}">'  # SSRF via headless browser
generate_pdf(html)
```

## SSRF Attempt Detection (Logs)
```python
import ipaddress
import re

INTERNAL_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),    # Link-local / cloud metadata
    ipaddress.ip_network("::1/128"),            # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),           # IPv6 private
]

def is_ssrf_target(url: str) -> bool:
    """Check if URL targets internal/metadata networks"""
    # Check for metadata hostname
    if re.search(r'169\.254\.169\.254|metadata\.google\.internal', url):
        return True
    # Extract host and check against internal ranges
    try:
        from urllib.parse import urlparse
        host = urlparse(url).hostname
        if host:
            ip = ipaddress.ip_address(host)
            return any(ip in net for net in INTERNAL_RANGES)
    except ValueError:
        pass  # Hostname, not IP — DNS resolution check needed
    return False
```

# DEFENSES

## URL Allowlist Validation (Primary Defense)
```python
from urllib.parse import urlparse
import ipaddress
import socket

ALLOWED_DOMAINS = {"api.partner.com", "cdn.trusted.com"}
ALLOWED_SCHEMES = {"https"}

def validate_url(url: str) -> str:
    """Validate URL against allowlist before fetching — raises on violation"""
    parsed = urlparse(url)

    # 1. Scheme check
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"Disallowed scheme: {parsed.scheme}")

    # 2. Hostname allowlist (if using fixed set of targets)
    if parsed.hostname not in ALLOWED_DOMAINS:
        raise ValueError(f"Domain not in allowlist: {parsed.hostname}")

    # 3. Resolve and verify IP is not internal (DNS rebinding protection)
    try:
        resolved_ip = socket.gethostbyname(parsed.hostname)
        ip = ipaddress.ip_address(resolved_ip)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise ValueError(f"Resolved to internal IP: {resolved_ip}")
    except socket.gaierror:
        raise ValueError("Could not resolve hostname")

    return url

# Use: validate_url(user_url) before any HTTP fetch
```

## Network-Level Egress Controls
```
Defense: Application servers should not be able to reach internal services
even if SSRF is present.

Firewall rules for app servers:
  - Allow outbound: 443/tcp to internet (specific allowlist if possible)
  - Block outbound: 169.254.169.254 (cloud metadata)
  - Block outbound: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 (internal)
  - Block outbound: 127.0.0.0/8 (loopback)

AWS: Use Security Groups + NACLs
  - Deny outbound to 169.254.169.254/32 from app server SG

Linux iptables:
  # Block app server from reaching cloud metadata
  iptables -A OUTPUT -m owner --uid-owner www-data -d 169.254.169.254 -j DROP
  # Block internal ranges
  iptables -A OUTPUT -m owner --uid-owner www-data -d 10.0.0.0/8 -j DROP
```

## AWS IMDSv2 (Mitigates SSRF Credential Theft)
```
IMDSv1 (VULNERABLE):
  curl http://169.254.169.254/latest/meta-data/iam/security-credentials/
  → Immediately returns credentials — no authentication required

IMDSv2 (SECURE):
  curl -X PUT "http://169.254.169.254/latest/api/token" \
       -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"
  → Returns token (requires PUT request with custom header)
  → Simple SSRF (GET only) cannot obtain token → credentials not accessible

Enable IMDSv2 on all EC2 instances:
  aws ec2 modify-instance-metadata-options \
    --instance-id i-xxxx \
    --http-tokens required \
    --http-endpoint enabled

Enforce org-wide via SCP:
  Condition: "ec2:MetadataHttpTokens": "optional"  → Deny
```

## Safe HTTP Client Wrapper
```python
import requests
import ipaddress
import socket
from urllib.parse import urlparse
from requests.exceptions import ConnectionError

class SafeHTTPClient:
    BLOCKED_NETWORKS = [
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("169.254.0.0/16"),
    ]
    ALLOWED_SCHEMES = {"https"}
    MAX_REDIRECTS = 3

    def fetch(self, url: str, timeout: int = 10) -> requests.Response:
        parsed = urlparse(url)

        if parsed.scheme not in self.ALLOWED_SCHEMES:
            raise ValueError(f"Blocked scheme: {parsed.scheme}")

        # Resolve DNS and check IP
        try:
            ip_str = socket.gethostbyname(parsed.hostname)
            ip = ipaddress.ip_address(ip_str)
        except (socket.gaierror, ValueError):
            raise ValueError("DNS resolution failed or invalid IP")

        if any(ip in net for net in self.BLOCKED_NETWORKS):
            raise ValueError(f"Request to internal network blocked: {ip}")

        # Fetch with redirects validated
        session = requests.Session()
        session.max_redirects = self.MAX_REDIRECTS
        response = session.get(url, timeout=timeout, allow_redirects=False)

        # Validate redirects
        if response.is_redirect:
            redirect_url = response.headers.get("Location", "")
            return self.fetch(redirect_url, timeout)  # Recursive validation

        return response
```

## Blind SSRF Detection via OOB
```
When testing for blind SSRF (no visible response):
  1. Use Burp Collaborator or interactsh as OOB callback server
  2. Submit URL pointing to callback server:
     url = "https://your-id.burpcollaborator.net/"
  3. If callback server receives HTTP request → SSRF confirmed (blind)

Detection in production:
  - Monitor DNS queries from app servers for unexpected external domains
  - Alert on outbound HTTP from servers to non-allowlisted destinations
  - Use cloud egress proxy with full request logging
```

# INCIDENT RESPONSE

## SSRF Exploitation Response
```
T+0  Detect    → WAF alert / log anomaly showing internal IP access
T+1  Confirm   → Identify exploited endpoint from access logs
T+2  Assess    → What internal services were reachable? Were cloud credentials accessed?

If cloud metadata accessed:
  T+5  CRITICAL → Rotate ALL IAM credentials associated with that instance role IMMEDIATELY
  T+5           → Revoke any tokens obtained (check CloudTrail for API calls with stolen creds)
  T+10          → Audit all API calls made with compromised credentials

T+10 Block     → Apply WAF rule to block SSRF pattern on exploited parameter
T+15 Network   → Verify egress firewall rules block internal range access from app servers
T+20 Enable    → Switch to IMDSv2 if not already; enforce via SCP
T+30 Audit     → Review all URL-fetching code paths in application for similar patterns
T+60 Harden    → Implement SafeHTTPClient wrapper org-wide; add SSRF tests to SAST pipeline
```

# REVIEW CHECKLIST
```
[ ] All URL-fetching functions use allowlist validation
[ ] DNS rebinding protection: resolve + verify IP is not internal after DNS lookup
[ ] File://, dict://, gopher:// schemes explicitly blocked
[ ] Network-level egress rules block app servers from reaching 169.254.169.254
[ ] AWS IMDSv2 enforced on all EC2 instances (HttpTokens=required)
[ ] Internal service ports (Redis, Elasticsearch, etc.) not reachable from app servers
[ ] Redirect chains validated at each hop (not just initial URL)
[ ] SSRF test cases in SAST/DAST pipeline
[ ] Outbound HTTP from app servers logged and monitored
[ ] Webhook URLs validated against allowlist before use
[ ] PDF/HTML rendering engines restricted from making external requests
[ ] Cloud IAM roles use least-privilege policies (SSRF blast radius limited)
```
