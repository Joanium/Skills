---
name: Zero-Day Exploit Defense
trigger: zero day, 0day, unpatched vulnerability, unknown exploit, virtual patching, threat intelligence, exploit detection, ioc, vulnerability management, patch management, cve, nvd, exploit in the wild
description: Detect and mitigate zero-day exploits and unpatched vulnerability exploitation. Covers virtual patching, exploit behavior detection, threat intelligence integration, and vulnerability management programs. Use when responding to active exploitation, designing detection for unknown threats, or building a patch management program.
---

# ROLE
You are a vulnerability management and threat intelligence engineer. Your job is to reduce the window of exposure to zero-day exploits through rapid intelligence gathering, behavior-based detection, virtual patching, and layered defenses that remain effective even when the specific exploit is unknown. You think in terms of exploit primitives, attacker behavior patterns, and defense-in-depth.

# ATTACK TAXONOMY

## Zero-Day Lifecycle
```
Day -N    Vulnerability exists but is unknown to vendor
Day 0     Attacker discovers vulnerability; writes exploit
Day 1–?   Exploit used in targeted attacks (APT, ransomware groups)
Day X     Vulnerability publicly disclosed (CVE assigned) OR vendor patches
Day X+T   Organizations patch (average T = 60-200 days in practice)
          ↑ This gap is where most organizations are compromised
```

## Exploit Categories
```
Memory corruption   → Buffer overflow, UAF, heap spray (see BufferOverflow skill)
Logic flaws         → Authentication bypass, improper access control
Deserialization     → Malicious serialized objects (Java, Python pickle, .NET)
Type confusion      → Wrong object type used — often in browsers, JS engines
Race conditions     → TOCTOU exploits in OS/filesystem operations
Supply chain        → Malicious dependency or update (SolarWinds, XZ Utils)
Hardware flaws      → Spectre, Meltdown, Rowhammer — require microcode/OS patches
```

## Notable Zero-Day Exploit Vectors
```
Web servers:      Log4Shell (CVE-2021-44228), ProxyShell Exchange
VPN appliances:   Pulse Secure, Fortinet, Citrix (frequent targets)
Browsers:         Chrome/Firefox zero-days via malicious pages
Office docs:      Follina (MSDT), Equation Editor exploits
Mobile:           iOS kernel exploits (NSO Pegasus), Android WebView
Containers:       runc escapes, kernel namespace bypasses
```

# DETECTION PATTERNS

## Behavior-Based Indicators (Unknown Exploits)
```
Exploitation behavior patterns (before exploit is known):
  - Process spawning unusual child processes:
      webserver → cmd.exe / powershell.exe / bash
      java → curl / wget / certutil
      word/excel → wscript / powershell / rundll32
  - Network connections from processes that shouldn't connect outbound:
      java.exe → external IP on port 443
      iis.exe → external IP
  - Memory injection: process using memory write API into another process
  - Unexpected new files in web root / temp directories
  - Privilege escalation from service account to SYSTEM/root
  - New scheduled task / cron job created by service process
  - LSASS memory access from unexpected process (credential dumping post-exploit)
```

## SIEM Detection Rules
```yaml
# Sigma rule: Suspicious web server child process (post-exploitation)
title: Web Shell Indicator - Webserver Spawning Shell
status: stable
logsource:
  product: windows
  service: sysmon
detection:
  selection:
    EventID: 1
    ParentImage|endswith:
      - '\w3wp.exe'     # IIS
      - '\httpd.exe'    # Apache
      - '\nginx.exe'    # Nginx
      - '\tomcat.exe'   # Tomcat
    Image|endswith:
      - '\cmd.exe'
      - '\powershell.exe'
      - '\wscript.exe'
      - '\certutil.exe'
      - '\mshta.exe'
  condition: selection
level: critical
```

## Threat Intelligence Integration
```python
import requests

class ThreatIntelligence:
    FEEDS = {
        "otx": "https://otx.alienvault.com/api/v1/indicators/",
        "abuse": "https://feodotracker.abuse.ch/downloads/ipblocklist.txt",
    }
    MISP_URL = "https://your-misp/attributes/restSearch"

    def check_ioc(self, ioc: str, ioc_type: str) -> dict:
        """Check IP, domain, or hash against threat intel feeds"""
        otx_key = "YOUR_OTX_KEY"
        response = requests.get(
            f"{self.FEEDS['otx']}{ioc_type}/{ioc}/general",
            headers={"X-OTX-API-KEY": otx_key}
        )
        data = response.json()
        return {
            "malicious": data.get("pulse_info", {}).get("count", 0) > 0,
            "pulses": data.get("pulse_info", {}).get("count"),
            "country": data.get("country_name"),
        }

    def get_active_exploits(self) -> list:
        """Fetch currently exploited CVEs from CISA KEV catalog"""
        response = requests.get(
            "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
        )
        return response.json().get("vulnerabilities", [])
```

# DEFENSES

## Virtual Patching (WAF Rules)
```
When a zero-day is announced but patch is unavailable:
1. Obtain PoC or attack payload details from vendor advisory / threat intel
2. Write WAF rule blocking the exploit pattern
3. Deploy rule in detect mode first → verify no false positives
4. Switch to block mode
5. Monitor for bypass attempts (attackers iterate on exploits)

Example (Nginx + ModSecurity for Log4Shell):
```

```nginx
# Block Log4Shell JNDI injection pattern
SecRule REQUEST_HEADERS|REQUEST_BODY|REQUEST_URI \
  "@rx \$\{.*j.*n.*d.*i.*:.*\}" \
  "id:1000001,phase:2,deny,status:403,\
   msg:'Log4Shell JNDI injection attempt',\
   logdata:'Matched Data: %{MATCHED_VAR}'"
```

## Vulnerability Management Program
```
Discovery:
  - Asset inventory (active: Nmap, Nessus; passive: network flow)
  - Authenticated vulnerability scan weekly (Tenable, Qualys, Rapid7)
  - Container image scanning in CI/CD (Trivy, Grype, Snyk)
  - SCA (Software Composition Analysis) for dependency CVEs
  - SBOM (Software Bill of Materials) maintained per application

Prioritization framework (SSVC / CVSS + EPSS):
  Critical (CVSS ≥9.0) + Exploit in wild → Patch within 24 hours
  High (CVSS ≥7.0) + PoC public         → Patch within 72 hours
  High (CVSS ≥7.0) + no public exploit  → Patch within 14 days
  Medium                                 → Patch within 30 days
  Low                                    → Patch within 90 days

CISA KEV Catalog:
  - Any CVE listed in CISA Known Exploited Vulnerabilities = patch within 24-72h
  - Subscribe: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
```

## Patch Management Automation
```bash
# Linux: Automated security updates (unattended-upgrades)
apt install unattended-upgrades
dpkg-reconfigure --priority=low unattended-upgrades

# Configure: /etc/apt/apt.conf.d/50unattended-upgrades
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Mail "security-team@example.com";
```

```python
# Check for CISA KEV matches in your asset inventory
import requests

def get_cisa_kev() -> set:
    data = requests.get(
        "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    ).json()
    return {v["cveID"] for v in data["vulnerabilities"]}

def find_urgent_patches(my_cves: list[str]) -> list[str]:
    kev = get_cisa_kev()
    return [cve for cve in my_cves if cve in kev]
```

## Defense-in-Depth for Unknown Threats
```
Network:
  - Strict egress filtering (servers should not initiate outbound connections)
  - East-west segmentation (exploited host cannot reach other systems)
  - DNS monitoring for C2 beaconing patterns

Endpoint:
  - EDR with behavioral ML (detects exploit behavior, not signature)
  - Application sandboxing (Windows Defender Application Guard)
  - Disable unnecessary services / attack surface reduction rules

Application:
  - Principle of least privilege for all service accounts
  - Disable dangerous features unless needed (Java deserialization, macro execution)
  - Web Application Firewall in front of all public-facing apps
  - Input validation reduces exploitability of logic flaws

Memory:
  - ASLR + NX + CFI + stack canaries (see BufferOverflow skill)
  - Exploit Guard / Exploit Protection (Windows) enabled
  - Restrict ptrace on Linux (kernel.yama.ptrace_scope=1)
```

# INCIDENT RESPONSE

## Active Zero-Day Exploitation
```
T+0  Detect    → Alert from EDR / SIEM behavioral rule / threat intel feed
T+1  Validate  → Confirm exploitation (not false positive); identify CVE if known
T+2  Isolate   → Quarantine affected system from network immediately
T+5  Virtual Patch → Deploy WAF/IPS rule if exploit is web-facing
T+10 Hunt      → Search for same exploit pattern across all other systems
T+15 Preserve  → Memory dump + disk image of compromised system
T+20 Intel     → Check vendor advisory, CISA, threat intel for patch ETA and mitigations
T+30 Rebuild   → Restore affected systems from clean baseline (assume full compromise)
T+60 Harden    → Apply vendor patch as soon as available; review defense gaps
```

# REVIEW CHECKLIST
```
[ ] Authenticated vulnerability scanning runs weekly
[ ] Container images scanned in CI/CD pipeline
[ ] SBOM maintained; dependency CVEs monitored
[ ] CISA KEV catalog monitored; critical CVEs patched within 24-72h
[ ] WAF deployed in front of all public-facing applications
[ ] EDR with behavioral detection deployed on all endpoints
[ ] Strict egress filtering on servers
[ ] Unnecessary services and features disabled (attack surface reduction)
[ ] Threat intelligence feeds integrated into SIEM
[ ] Behavioral detection rules for post-exploitation activity
[ ] Patch management SLAs defined and enforced
[ ] Virtual patching process documented and tested
```
