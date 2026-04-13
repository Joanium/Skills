---
name: DDoS Attack Defense
trigger: ddos, distributed denial of service, dos attack, volumetric attack, syn flood, http flood, amplification attack, rate limiting, traffic scrubbing, botnet attack, layer 7 ddos, application layer attack
description: Detect, mitigate, and recover from Distributed Denial of Service attacks. Covers volumetric, protocol, and application-layer (L7) attacks. Use when designing rate-limiting, configuring CDN/WAF protection, analyzing traffic anomalies, or responding to availability incidents.
---

# ROLE
You are a network and infrastructure security engineer. Your job is to design DDoS-resilient architectures, implement rate-limiting and traffic scrubbing, and orchestrate rapid incident response to restore availability. You think in terms of traffic profiles, attack vectors, and layered mitigation pipelines.

# ATTACK TAXONOMY

## DDoS Categories
```
Layer 3/4 Volumetric   → Flood bandwidth/PPS capacity
  - UDP Flood            Saturates bandwidth with UDP packets
  - ICMP Flood           Ping flood exhausting bandwidth
  - SYN Flood            Half-open TCP connections exhaust server state
  - Amplification        DNS/NTP/Memcached reflection multiplies attacker bandwidth

Layer 4 Protocol        → Exhaust stateful device resources
  - SYN Flood            Fills connection tables on firewalls/load balancers
  - ACK/RST Flood        Disrupts TCP state machines

Layer 7 Application     → Mimic legitimate traffic; hardest to filter
  - HTTP Flood           High-RPS GET/POST requests exhaust web server threads
  - Slowloris            Opens many slow HTTP connections; starves thread pool
  - DNS Query Flood      Overwhelms authoritative/recursive DNS servers
  - SSL Renegotiation    CPU-exhausting TLS handshake flood
```

## Amplification Factors
```
Protocol        | Amplification Factor
----------------|----------------------
DNS             | 28x – 54x
NTP             | Up to 556x
Memcached       | Up to 51,000x
SSDP            | Up to 30x
CharGen         | Up to 358x

Mitigation: BCP38 ingress filtering — never allow spoofed source IPs from your network
```

# DETECTION PATTERNS

## Traffic Anomaly Indicators
```
Volumetric signals:
  - Sudden bandwidth spike (>2x baseline in <60s)
  - PPS rate exceeding link capacity
  - High percentage of UDP/ICMP with no established sessions

Protocol signals:
  - SYN/ACK ratio drops below 0.5 (many unanswered SYNs)
  - Half-open TCP connections spike
  - Connection table utilization >80%

Application signals:
  - RPS spike from small IP set (botnet traffic)
  - Request rate per IP >>  normal user behavior
  - High percentage of identical request signatures
  - Abnormal HTTP status distribution (e.g., 503 spike)
  - Slowloris: many connections in ESTABLISHED state with no data
```

## Detection Code (Rate Anomaly)
```python
from collections import defaultdict
import time

request_counts = defaultdict(list)
RATE_LIMIT = 100       # requests per window
WINDOW_SECONDS = 10

def is_rate_exceeded(ip: str) -> bool:
    now = time.time()
    window_start = now - WINDOW_SECONDS
    # Prune old entries
    request_counts[ip] = [t for t in request_counts[ip] if t > window_start]
    request_counts[ip].append(now)
    return len(request_counts[ip]) > RATE_LIMIT

# Production: use Redis with INCR + EXPIRE for distributed rate limiting
```

# DEFENSES

## Architecture: Defense in Depth
```
[Internet]
    ↓
[BGP Anycast / Upstream Scrubbing Center]  ← Volumetric mitigation
    ↓
[CDN Edge (Cloudflare / Akamai / AWS Shield)]  ← L3/L4 filtering + caching
    ↓
[WAF]  ← L7 HTTP filtering, rate limiting, challenge pages
    ↓
[Load Balancer]  ← Connection limiting, health checks
    ↓
[Origin Servers]  ← Last-line rate limiting, resource isolation
```

## Rate Limiting (Nginx)
```nginx
# /etc/nginx/nginx.conf

# Define rate limit zones
limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

server {
    location /api/ {
        limit_req zone=api burst=50 nodelay;
        limit_conn conn_limit 20;
    }

    location /auth/login {
        limit_req zone=login burst=3 nodelay;
    }
}
```

## SYN Flood Mitigation (Linux Kernel)
```bash
# Enable SYN cookies (kernel validates without allocating state)
sysctl -w net.ipv4.tcp_syncookies=1

# Reduce SYN-ACK retries
sysctl -w net.ipv4.tcp_synack_retries=2

# Increase backlog queue size
sysctl -w net.ipv4.tcp_max_syn_backlog=4096

# Persist in /etc/sysctl.conf
```

## Slowloris Mitigation
```nginx
# Limit slow request bodies
client_body_timeout 10s;
client_header_timeout 10s;
keepalive_timeout 15s;
send_timeout 10s;

# Limit open connections per IP
limit_conn conn_limit 20;
```

## Cloud Provider DDoS Protection
```
AWS Shield Standard  → Free, always-on L3/L4 protection
AWS Shield Advanced  → L7 + DRT support + cost protection ($3k/month)
Cloudflare Magic Transit → BGP-announced IP protection
Google Cloud Armor   → Adaptive L7 WAF + DDoS rules
Azure DDoS Protection → Standard tier with adaptive tuning
```

## CAPTCHA / JS Challenge for L7 Floods
```
When HTTP flood detected:
1. Serve JS challenge page (Cloudflare Turnstile / hCaptcha)
2. Bots fail browser challenge → blocked
3. Humans solve challenge → receive session cookie → proceed

Trigger challenge when:
  - RPS from single IP > threshold
  - ASN/country anomaly detected
  - User-Agent absent or known-bot signature
```

# INCIDENT RESPONSE

## Runbook
```
T+0  Detect  → Confirm attack via monitoring dashboard (PPS, RPS, error rates)
T+1  Classify → Volumetric? Protocol? Application layer?
T+2  Activate → Enable upstream scrubbing / CDN under-attack mode
T+5  Filter   → Apply IP block lists; enable rate limiting; deploy CAPTCHA
T+10 Escalate → Contact ISP/upstream for null-routing if volumetric >100 Gbps
T+15 Communicate → Status page update; internal incident channel
T+30 Assess  → Review filtered traffic; confirm origin servers healthy
T+60 Post-IR  → Document attack profile; update detection thresholds; tune rules
```

## Traffic Analysis Commands
```bash
# Top source IPs by packet count (requires tcpdump/pcap)
tcpdump -nn -r capture.pcap | awk '{print $3}' | sort | uniq -c | sort -rn | head 20

# Netflow: top talkers
nfdump -r /var/cache/nfdump -s ip/bytes -n 20

# Check SYN flood in progress
ss -s          # Connection summary
netstat -an | grep SYN_RECV | wc -l
```

# REVIEW CHECKLIST
```
[ ] Upstream scrubbing or CDN in place for volumetric attacks
[ ] Rate limiting configured at edge and origin
[ ] SYN cookies enabled on all Linux servers
[ ] Connection/request timeouts tuned (Slowloris mitigation)
[ ] BCP38 ingress filtering enforced (no spoofed traffic from your ASN)
[ ] DDoS runbook documented and tested
[ ] Alert thresholds set for PPS, RPS, error rate anomalies
[ ] Cloud DDoS protection tier appropriate for risk level
[ ] Status page and communication plan prepared
[ ] Post-incident review process defined
```
