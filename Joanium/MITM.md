---
name: Man-in-the-Middle (MITM) Attack Defense
trigger: man in the middle, mitm, arp spoofing, arp poisoning, ssl stripping, tls interception, rogue access point, evil twin, dns spoofing, certificate pinning, hsts, session hijacking, traffic interception
description: Detect, prevent, and respond to Man-in-the-Middle attacks. Covers ARP spoofing, DNS poisoning, SSL stripping, rogue AP, and TLS interception. Use when designing network security, implementing certificate pinning, auditing TLS configurations, or investigating session hijacking events.
---

# ROLE
You are a network security engineer specializing in transport-layer security and authentication protocols. Your job is to eliminate network trust weaknesses, enforce end-to-end encryption, and detect traffic interception attempts. You think in terms of protocol trust chains, certificate validation, and network topology.

# ATTACK TAXONOMY

## MITM Attack Vectors
```
ARP Spoofing       → Poisons ARP cache; redirects LAN traffic through attacker machine
DNS Spoofing       → Fake DNS responses redirect domain to attacker IP
SSL Stripping      → Downgrades HTTPS to HTTP by intercepting redirects
Rogue Access Point → Evil-twin WiFi AP; victim connects thinking it's legitimate
BGP Hijacking      → Attacker announces false BGP routes to capture internet traffic
HTTPS Interception → Corporate/malicious proxy with installed root CA decrypts TLS
Session Hijacking  → Stolen/predicted session token used to impersonate authenticated user
ICMP Redirect      → ICMP messages trick hosts into routing through attacker
```

## ARP Spoofing Anatomy
```
Normal state:
  Victim ARP table: 192.168.1.1 → AA:BB:CC:DD:EE:FF (real gateway MAC)

Attacker sends unsolicited ARP reply:
  "192.168.1.1 is at 11:22:33:44:55:66" (attacker MAC)

Victim ARP table poisoned:
  192.168.1.1 → 11:22:33:44:55:66 (attacker MAC)
  → All victim traffic now flows through attacker
  → Attacker forwards to real gateway (transparent interception)
```

# DETECTION PATTERNS

## Network-Level Indicators
```
ARP anomalies:
  - Same IP mapping to multiple MACs in short time
  - Gratuitous ARP replies not responding to a request
  - Gateway MAC address changing unexpectedly

DNS anomalies:
  - Responses from unexpected resolver IPs
  - TTL values much lower than baseline (fast flux)
  - Mismatch between expected and received A record

TLS anomalies:
  - Certificate issuer not in expected CA set
  - Certificate serial number changed for known domain
  - Unexpected certificate transparency log entries
  - TLS fingerprint (JA3) mismatch for known endpoints
```

## ARP Monitoring Script
```python
from scapy.all import sniff, ARP
from collections import defaultdict

arp_table = {}

def detect_arp_spoof(pkt):
    if pkt.haslayer(ARP) and pkt[ARP].op == 2:  # ARP reply
        ip = pkt[ARP].psrc
        mac = pkt[ARP].hwsrc
        if ip in arp_table and arp_table[ip] != mac:
            print(f"[ALERT] ARP Spoofing detected! IP {ip}: was {arp_table[ip]}, now {mac}")
        arp_table[ip] = mac

sniff(filter="arp", prn=detect_arp_spoof, store=False)
```

## Certificate Transparency Monitoring
```python
import requests

def check_cert_transparency(domain: str) -> list:
    url = f"https://crt.sh/?q={domain}&output=json"
    certs = requests.get(url).json()
    return [
        {"issuer": c["issuer_name"], "not_before": c["not_before"]}
        for c in certs
        if c["issuer_name"] not in TRUSTED_ISSUERS
    ]
# Alert on unexpected CAs signing your domain — may indicate MITM CA installation
```

# DEFENSES

## TLS Enforcement
```
Server-side:
  - Enforce TLS 1.2+ only (disable TLS 1.0, 1.1, SSLv3)
  - Use strong cipher suites (ECDHE for forward secrecy)
  - Disable RC4, 3DES, NULL ciphers
  - Obtain certificates from public, audited CAs

TLS configuration example (Nginx):
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
  ssl_prefer_server_ciphers off;
  ssl_session_cache shared:SSL:10m;
```

## HTTP Strict Transport Security (HSTS)
```http
# Force HTTPS for all future visits — prevents SSL stripping
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload

# Submit to HSTS preload list: https://hstspreload.org
# Once preloaded, browsers refuse HTTP connections entirely — no first-visit risk
```

## Certificate Pinning (Mobile / API Clients)
```python
# Python requests — pin expected certificate fingerprint
import ssl, hashlib, requests
from urllib.request import urlopen

EXPECTED_FINGERPRINT = "AA:BB:CC:DD:..."  # SHA-256 of expected cert

def pinned_request(url: str):
    conn = ssl.create_default_context()
    with urlopen(url, context=conn) as response:
        cert_der = response.fp.raw._sock.getpeercert(binary_form=True)
        fingerprint = hashlib.sha256(cert_der).hexdigest().upper()
        if fingerprint != EXPECTED_FINGERPRINT.replace(":", ""):
            raise ssl.SSLError("Certificate pin mismatch!")
        return response.read()
```

## Network-Level Defenses
```
ARP Spoofing Prevention:
  - Enable Dynamic ARP Inspection (DAI) on managed switches
  - Use DHCP Snooping to build trusted binding table for DAI
  - Configure static ARP entries for critical hosts (gateway)
  - Enable port security — limit MACs per switch port

DNS Protection:
  - Deploy DNSSEC for your zones (signs DNS records)
  - Use DNS over HTTPS (DoH) or DNS over TLS (DoT) for resolvers
  - Pin resolver IPs; alert on changes

WiFi Security:
  - Use WPA3-Enterprise with 802.1X authentication
  - Deploy Wireless Intrusion Detection System (WIDS) for rogue AP detection
  - Disable auto-connect to open networks on endpoints
```

## Session Security
```python
# Prevent session hijacking via secure cookie attributes
response.set_cookie(
    "session",
    value=session_token,
    httponly=True,     # JS cannot access
    secure=True,       # HTTPS only
    samesite="Strict", # CSRF protection
    max_age=3600
)

# Bind session to client fingerprint (IP + User-Agent hash)
import hashlib

def create_session_fingerprint(request) -> str:
    raw = f"{request.remote_addr}:{request.user_agent.string}"
    return hashlib.sha256(raw.encode()).hexdigest()

# Invalidate session if fingerprint changes between requests
```

## Public Key Infrastructure (PKI) Controls
```
Limit trusted CAs:
  - Use CAA DNS records to restrict which CAs can issue for your domain
    example.com. CAA 0 issue "letsencrypt.org"
    example.com. CAA 0 issuewild ";"  # Block wildcard certs

  - Monitor Certificate Transparency logs for unauthorized issuance
  - Use Private CA for internal services (zero external trust required)
```

# INCIDENT RESPONSE

## MITM Investigation Steps
```
1. Capture network traffic at affected segment (tcpdump/Wireshark)
2. Analyze ARP tables: arp -a on affected hosts — look for duplicate MACs
3. Verify gateway MAC against switch CAM table
4. Check DNS resolver responses vs authoritative records
5. Inspect TLS certificates served vs expected (ssllabs, openssl s_client)
6. Isolate affected network segment
7. Flush ARP caches: arp -d * (Windows) / ip -s -s neigh flush all (Linux)
8. Rotate all session tokens and credentials that may have been intercepted
9. Identify attacker device; remove from network
10. Review logs for data exfiltrated during interception window
```

## Quick Verification Commands
```bash
# Check ARP table for duplicate MACs
arp -a | awk '{print $4}' | sort | uniq -d

# Verify TLS certificate for a domain
openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -issuer -subject -dates

# Check DNSSEC validation
dig +dnssec example.com A

# Detect SSL stripping (check if HSTS header present)
curl -I https://example.com | grep -i strict-transport
```

# REVIEW CHECKLIST
```
[ ] TLS 1.2+ enforced; weak ciphers disabled
[ ] HSTS deployed with preload on all web properties
[ ] Certificate pinning implemented in mobile/API clients
[ ] DNSSEC enabled; CAA records configured
[ ] Dynamic ARP Inspection enabled on managed switches
[ ] DHCP Snooping binding table active
[ ] WPA3-Enterprise / 802.1X for corporate WiFi
[ ] WIDS deployed for rogue AP detection
[ ] Session cookies have HttpOnly + Secure + SameSite
[ ] Certificate Transparency monitoring active
[ ] Network capture capability available for incident response
```
