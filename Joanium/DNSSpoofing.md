---
name: DNS Spoofing & Poisoning Defense
trigger: dns spoofing, dns poisoning, dns cache poisoning, dns hijacking, dnssec, dns over https, doh, dns over tls, dot, dns security, resolver security, dns attack, kaminsky attack, dns amplification
description: Prevent and detect DNS spoofing, cache poisoning, and DNS hijacking attacks. Covers DNSSEC, DNS over HTTPS/TLS, resolver hardening, and DNS monitoring. Use when configuring DNS infrastructure, auditing resolver security, investigating traffic redirection, or deploying encrypted DNS.
---

# ROLE
You are a DNS and network security engineer. Your job is to secure DNS infrastructure against poisoning and hijacking attacks, deploy cryptographic validation, and monitor for anomalous resolution patterns. You think in terms of DNS trust chains, resolver behavior, and traffic integrity.

# ATTACK TAXONOMY

## DNS Attack Types
```
Cache Poisoning     → Inject false DNS records into resolver cache
DNS Hijacking       → Modify DNS settings on router/host to use rogue resolver
DNS Spoofing        → Forge DNS response packets to intercept resolution
BGP Hijacking       → Reroute traffic at routing level to intercept DNS queries
Subdomain Takeover  → Abandoned CNAME target claimed by attacker
DNS Amplification   → DDoS reflection using DNS (see DDoS skill)
DNS Tunneling       → Encode C2 traffic in DNS queries/responses to bypass firewalls
NXDOMAIN Hijacking  → ISP/attacker intercepts failed lookups for ad injection
```

## Cache Poisoning Anatomy (Kaminsky Attack)
```
DNS resolver asks authoritative server for victim.com
Attacker floods resolver with forged responses:
  - Guesses transaction ID (16-bit = 65,536 possibilities)
  - Forged answer: victim.com → attacker_ip
  - Race condition: arrive before legitimate response

Once poisoned:
  - All users of that resolver are redirected to attacker IP
  - Attack is invisible to end users
  - Persists until TTL expires (can be hours or days)

Kaminsky made this practical by querying random subdomains
(foo123.victim.com) to force repeated cache misses → repeated guessing windows
```

## DNS Tunneling Anatomy
```
C2 communication disguised as DNS queries:
  Client → resolver: TXT query for "aGVsbG8.c2.evil.com"
                      ↑ base64 encoded command data
  Resolver → authoritative evil.com server (attacker-controlled)
  Response TXT: "aGVsbG8=" (base64 encoded response)

Characteristics:
  - High query volume to single domain
  - Unusually long subdomain labels (>30 chars)
  - High entropy in subdomain names
  - TXT/NULL/MX record types for data encoding
  - Low TTL values
```

# DETECTION PATTERNS

## DNS Anomaly Indicators
```
Cache poisoning signals:
  - DNS responses with different TTL than baseline for same record
  - Response arriving from unexpected source IP (not authoritative server)
  - Sudden change in resolved IP for a known domain
  - DNSSEC validation failures

DNS tunneling signals:
  - High query rate to single domain (>100 queries/min)
  - Subdomain label length > 30 characters
  - High entropy in subdomain portion (Shannon entropy > 3.5)
  - Unusual record types: TXT, NULL, MX used frequently
  - Low or zero TTL responses
  - Query volume spikes not correlated with normal traffic patterns

DNS hijacking signals:
  - Resolver IP changed on endpoint
  - DNS response from unexpected server IP
  - NXDOMAIN responses returning IPs instead of errors
```

## DNS Tunneling Detector
```python
import math
from collections import Counter

def shannon_entropy(s: str) -> float:
    """Calculate entropy of a string — high entropy = likely encoded data"""
    if not s:
        return 0
    counts = Counter(s)
    length = len(s)
    return -sum((c/length) * math.log2(c/length) for c in counts.values())

def is_dns_tunnel_candidate(fqdn: str) -> dict:
    labels = fqdn.split('.')
    subdomain = '.'.join(labels[:-2]) if len(labels) > 2 else ''

    flags = {
        "high_entropy": shannon_entropy(subdomain) > 3.5,
        "long_label": any(len(l) > 30 for l in labels),
        "many_labels": len(labels) > 5,
        "numeric_heavy": sum(c.isdigit() for c in subdomain) / max(len(subdomain), 1) > 0.3,
    }
    flags["suspicious"] = sum(flags.values()) >= 2
    return flags

# Examples:
# is_dns_tunnel_candidate("aGVsbG8gd29ybGQ.data.evil.com") → suspicious: True
# is_dns_tunnel_candidate("www.google.com") → suspicious: False
```

# DEFENSES

## DNSSEC (Cryptographic DNS Validation)
```dns
# DNSSEC adds digital signatures to DNS records
# Resolver validates chain of trust from root → TLD → zone

# Enable DNSSEC on your zone (BIND example):
zone "example.com" {
    type master;
    file "/etc/bind/example.com.zone";
    dnssec-policy "default";
    inline-signing yes;
};

# Generate ZSK and KSK
dnssec-keygen -a ECDSAP256SHA256 -f KSK example.com
dnssec-keygen -a ECDSAP256SHA256 example.com

# Submit DS record to parent zone registrar
dnssec-dsfromkey Kexample.com.+013+xxxxx.key

# Verify DNSSEC from outside:
dig +dnssec example.com A
dig +dnssec example.com DNSKEY
```

## DNS over HTTPS / TLS (Encrypted Transport)
```
DoH (DNS over HTTPS) — Port 443
  - DNS queries encrypted inside HTTPS
  - Prevents eavesdropping on DNS queries
  - Prevents MITM manipulation of responses

DoT (DNS over TLS) — Port 853
  - DNS encrypted inside TLS
  - Easier to filter/monitor than DoH (distinct port)

Configure system resolver for DoT (Ubuntu):
  # /etc/systemd/resolved.conf
  [Resolve]
  DNS=9.9.9.9#dns.quad9.net 149.112.112.112#dns.quad9.net
  DNSOverTLS=yes
  DNSSEC=yes

Configure DoH in application (Python):
  import httpx

  def resolve_doh(hostname: str) -> str:
      response = httpx.get(
          "https://cloudflare-dns.com/dns-query",
          params={"name": hostname, "type": "A"},
          headers={"Accept": "application/dns-json"}
      )
      return response.json()["Answer"][0]["data"]
```

## Resolver Hardening
```
Bind9 resolver hardening:
  options {
    // Randomize source port (defeats transaction ID guessing)
    use-v4-udp-ports { range 1024 65535; };
    avoid-v4-udp-ports { range 1 1023; };

    // Refuse recursive queries from outside
    allow-recursion { 192.168.0.0/24; 127.0.0.1; };

    // Enable DNSSEC validation
    dnssec-validation auto;

    // Limit cache size (reduce poisoning blast radius)
    max-cache-size 256m;
    max-cache-ttl 86400;

    // Minimize query info sent upstream
    qname-minimization strict;

    // Rate limit to mitigate amplification
    rate-limit { responses-per-second 15; };
  };
```

## Subdomain Takeover Prevention
```bash
# Find dangling CNAMEs — records pointing to unregistered targets
# 1. List all CNAME records in your zone
dig axfr example.com @your-ns-server | grep CNAME

# 2. Check each target is still registered/active
for cname in $(dig axfr example.com | awk '/CNAME/{print $5}'); do
    if ! host $cname > /dev/null 2>&1; then
        echo "DANGLING CNAME: $cname — SUBDOMAIN TAKEOVER RISK"
    fi
done

# Prevention:
# - Remove DNS records immediately when cloud resources are deprovisioned
# - Audit DNS zone monthly for dangling CNAMEs
# - Use CAA records to restrict certificate issuance
# - Monitor Certificate Transparency for unexpected certs on your subdomains
```

## DNS Monitoring and Alerting
```python
import subprocess
import socket

KNOWN_RESOLUTIONS = {
    "example.com": "203.0.113.10",
    "api.example.com": "203.0.113.11",
}

def monitor_dns_consistency():
    """Alert if DNS resolution changes unexpectedly"""
    alerts = []
    for domain, expected_ip in KNOWN_RESOLUTIONS.items():
        try:
            resolved = socket.gethostbyname(domain)
            if resolved != expected_ip:
                alerts.append({
                    "domain": domain,
                    "expected": expected_ip,
                    "got": resolved,
                    "severity": "HIGH"
                })
        except socket.gaierror as e:
            alerts.append({"domain": domain, "error": str(e)})
    return alerts

# Run this from multiple geographic locations via monitoring service
# Discrepancy between locations = DNS hijacking indicator
```

## CAA Records (Certificate Authority Authorization)
```dns
# Restrict which CAs can issue certificates for your domain
# Prevents attacker from obtaining cert for your domain after DNS hijack

example.com. CAA 0 issue "letsencrypt.org"
example.com. CAA 0 issue "digicert.com"
example.com. CAA 0 issuewild ";"         # Block wildcard certs
example.com. CAA 0 iodef "mailto:security@example.com"  # Violation reports

# Check CAA records:
dig example.com CAA
```

# INCIDENT RESPONSE

## DNS Poisoning/Hijacking Response
```
1. Confirm: resolve affected domain from multiple resolvers/locations
   → Different IPs = hijacking in progress

2. Identify scope:
   - Is it your authoritative DNS modified?
   - Is it a recursive resolver poisoned?
   - Is it end-user DNS settings changed (malware)?

3. Immediate mitigations:
   - Flush affected resolver cache: rndc flushname victim.com
   - Push out DNSSEC signatures if signing infrastructure available
   - Alert users to potential traffic interception via status page

4. Authoritative DNS compromise:
   - Rotate DNS provider credentials immediately
   - Check zone transfer logs for unauthorized changes
   - Review all records modified in last 24-48h
   - Enable DNS registry lock at registrar level

5. Inform:
   - Certificate authorities (check for fraudulent certs issued)
   - Affected users (credentials/sessions may be compromised)
   - CERT/CSIRT if significant scope

6. Recovery:
   - Restore authoritative records to known-good state
   - Deploy DNSSEC if not already active
   - Enable two-factor authentication at DNS registrar
```

# REVIEW CHECKLIST
```
[ ] DNSSEC enabled and validated for all authoritative zones
[ ] DS records submitted to parent zone registrar
[ ] Resolver validates DNSSEC (dnssec-validation auto)
[ ] DNS over TLS or DoH configured for internal resolvers
[ ] Source port randomization enabled on resolvers (mitigates Kaminsky)
[ ] Recursive queries restricted to internal networks only
[ ] CAA records configured for all domains
[ ] DNS zone audited monthly for dangling CNAMEs
[ ] Certificate Transparency monitoring active for your domains
[ ] DNS registrar account has MFA and registry lock enabled
[ ] DNS tunneling detection rules active in SIEM
[ ] DNS resolution monitoring alerts on unexpected IP changes
```
