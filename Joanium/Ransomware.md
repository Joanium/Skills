---
name: Ransomware Attack Defense
trigger: ransomware, crypto locker, file encryption attack, ransom demand, backup recovery, ransomware prevention, endpoint protection, double extortion, ransomware response, data recovery, backup strategy
description: Prevent, detect, and recover from ransomware attacks. Covers initial access vectors, encryption behavior, double extortion, and recovery playbooks. Use when designing backup strategy, hardening endpoints, responding to an active ransomware incident, or implementing detection rules.
---

# ROLE
You are an endpoint and incident response security engineer. Your job is to prevent ransomware from entering the environment, detect encryption in progress, orchestrate rapid containment, and drive recovery from clean backups. You think in terms of kill chains, blast radius limitation, and recovery time objectives.

# ATTACK TAXONOMY

## Ransomware Kill Chain
```
1. Initial Access      → Phishing email, RDP brute force, unpatched vulnerability, supply chain
2. Execution           → Malicious macro, PowerShell dropper, exploit payload
3. Persistence         → Scheduled task, registry run key, service installation
4. Privilege Escalation → Credential dumping (Mimikatz), token impersonation
5. Defense Evasion     → Disable AV/EDR, clear event logs, LOLBins
6. Lateral Movement    → PSExec, WMI, SMB shares, RDP to adjacent systems
7. Data Exfiltration   → Upload sensitive data before encryption (double extortion)
8. Impact              → Mass file encryption, ransom note dropped, shadow copies deleted
```

## Ransomware Variants by Behavior
```
Crypto ransomware     → Encrypts user files (most common; .locked, .encrypted extensions)
Locker ransomware     → Locks OS/screen; files not encrypted
Double extortion      → Encrypts + threatens to publish exfiltrated data (REvil, LockBit)
Triple extortion      → Adds DDoS against victim while negotiating
RaaS                  → Ransomware-as-a-Service; affiliates deploy, developers profit-share
Wiper masquerading    → Mimics ransomware but has no decryption capability (NotPetya)
```

# DETECTION PATTERNS

## Behavioral Indicators
```
Early-stage signals:
  - Unusual PowerShell activity (encoded commands, download cradles)
  - New scheduled tasks / services created
  - LSASS memory access (credential dumping)
  - Tools: vssadmin, wbadmin, bcdedit, net use, PsExec spawned unexpectedly
  - Lateral movement: new RDP sessions, SMB auth from workstations

Encryption-phase signals:
  - High volume of file rename/write operations in short time
  - New file extensions appearing across directories (.locked, .crypt, .enc)
  - Shadow copy deletion: vssadmin delete shadows /all
  - Ransom note files created (README.txt, HOW_TO_DECRYPT.html)
  - CPU/disk I/O spike with no known process

Exfiltration signals (double extortion):
  - Large outbound data transfer to unknown IP
  - Use of rclone, MEGASync, WinSCP, or curl for cloud upload
  - DNS queries to suspicious or newly registered domains
```

## Detection Rule Example (Sigma / SIEM)
```yaml
title: Ransomware Shadow Copy Deletion
status: stable
logsource:
  product: windows
  service: sysmon
detection:
  selection:
    EventID: 1
    Image|endswith:
      - '\vssadmin.exe'
      - '\wmic.exe'
      - '\wbadmin.exe'
    CommandLine|contains:
      - 'delete shadows'
      - 'shadowcopy delete'
      - 'delete catalog'
      - 'delete systemstatebackup'
  condition: selection
level: critical
```

# DEFENSES

## Preventive Controls
```
Endpoint hardening:
  - Deploy EDR (CrowdStrike, SentinelOne, Defender for Endpoint)
  - Enable Controlled Folder Access (Windows Ransomware Protection)
  - Block Office macros from internet-sourced files (Group Policy)
  - Application allowlisting (AppLocker / WDAC)
  - Disable RDP where not needed; require MFA + VPN for RDP
  - Patch critical vulnerabilities within 24–72 hours (especially ProxyShell, Log4Shell)

Network segmentation:
  - Micro-segment environments (workstations cannot reach servers directly)
  - Restrict SMB to servers only (not workstation-to-workstation)
  - Block outbound connections from servers to internet by default
  - Implement tiered admin model (Tier 0: DC, Tier 1: servers, Tier 2: workstations)

Credential hygiene:
  - No shared local admin passwords (use LAPS)
  - MFA on all remote access, admin consoles, email
  - Disable NTLM where possible; enforce NTLMv2 minimum
  - Regular audit of service accounts and their privileges
```

## Backup Strategy (3-2-1-1 Rule)
```
3 copies of data
2 different storage media types
1 offsite copy
1 offline / air-gapped copy (immutable — ransomware cannot reach it)

Implementation:
  - Immutable backup storage: AWS S3 Object Lock, Azure Immutable Blob, Veeam Hardened Repository
  - Test restore monthly — a backup never tested is not a backup
  - Separate backup credentials from production environment
  - Monitor backup job health; alert on failures immediately

Recovery time targets:
  - Define RTO (Recovery Time Objective) and RPO (Recovery Point Objective)
  - Tier critical systems for priority recovery order
  - Document recovery runbook; practice tabletop exercises annually
```

## Controlled Folder Access (Windows)
```powershell
# Enable via PowerShell (Windows Defender)
Set-MpPreference -EnableControlledFolderAccess Enabled

# Add protected folders
Add-MpPreference -ControlledFolderAccessProtectedFolders "C:\SensitiveData"

# Allow specific apps if blocked by policy
Add-MpPreference -ControlledFolderAccessAllowedApplications "C:\Tools\legit.exe"
```

## Network-Based Containment (Pre-configured)
```
Prepare quarantine VLANs in advance:
  - Firewall rule set ready to isolate subnets on demand
  - Named ACLs for emergency workstation isolation
  - DNS RPZ (Response Policy Zone) to sinkhole known ransomware C2 domains
  - Canary files in file shares (e.g., AAAAA_CANARY.docx) — alert on modification
```

## Canary File Monitoring
```python
import os, hashlib, time

CANARY_FILES = [
    "/fileshare/HR/AAAAA_CANARY.docx",
    "/fileshare/Finance/AAAAA_CANARY.xlsx",
]

def get_hash(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()

canary_hashes = {f: get_hash(f) for f in CANARY_FILES}

def monitor_canaries():
    while True:
        for path, original_hash in canary_hashes.items():
            if get_hash(path) != original_hash:
                alert(f"CANARY MODIFIED: {path} — possible ransomware activity!")
        time.sleep(30)
```

# INCIDENT RESPONSE

## Active Ransomware Runbook
```
T+0  Detect   → Alert from EDR / SIEM / helpdesk report of encrypted files
T+1  Validate → Confirm it's ransomware (examine encrypted files, ransom note)
T+2  CONTAIN  → Isolate affected hosts from network IMMEDIATELY
               → Disable affected accounts
               → Block source IP/host at firewall
T+5  Assess   → Determine blast radius: how many systems affected?
T+10 Preserve → Snapshot affected VMs before remediation (for forensics)
               → Preserve volatile memory if possible (FTK Imager, WinPmem)
T+15 Hunt     → Search for persistence mechanisms, lateral movement paths
               → Identify patient zero / initial access vector
T+20 Notify   → Legal, executive leadership, cyber insurer
               → Regulatory notification requirements (GDPR 72hr, HIPAA, etc.)
T+30 Recover  → Restore from last known clean backup
               → Rebuild compromised systems from scratch (never decrypt and trust)
T+60 Harden   → Close initial access vector; patch, update credentials, deploy controls
               → Post-incident review and lessons learned
```

## Forensic Preservation Commands
```bash
# Capture memory on Windows (FTK Imager CLI)
ftkimager.exe \\.\PhysicalMemory mem_dump --verify

# Collect running processes and network connections
Get-Process | Export-Csv processes.csv
netstat -anob > connections.txt

# Identify recently created/modified files
Get-ChildItem -Recurse -Path C:\ | Where-Object {$_.LastWriteTime -gt (Get-Date).AddHours(-4)} | Select FullName | Export-Csv recent_files.csv
```

# REVIEW CHECKLIST
```
[ ] EDR deployed on all endpoints with behavioral detection enabled
[ ] Controlled Folder Access / ransomware protection enabled
[ ] Office macros blocked for internet-sourced documents
[ ] RDP disabled or protected by MFA + VPN
[ ] 3-2-1-1 backup strategy implemented with air-gapped copy
[ ] Backups tested for restore monthly
[ ] Backup credentials isolated from production
[ ] Canary files deployed in critical file shares
[ ] Network segmentation limits lateral movement
[ ] LAPS deployed (unique local admin passwords)
[ ] Ransomware incident response runbook tested via tabletop
[ ] Cyber insurance policy in place with IR retainer
```
