---
name: Privilege Escalation Defense
trigger: privilege escalation, privesc, sudo exploit, suid, setuid, token impersonation, local privilege escalation, kernel exploit, misconfigured permissions, path hijacking, dll hijacking, lpe, uac bypass, lateral movement
description: Detect and prevent local and domain privilege escalation attacks. Covers SUID/SUDO abuse, token impersonation, DLL hijacking, PATH manipulation, kernel exploits, and AD privilege escalation. Use when auditing system configurations, hardening servers, investigating endpoint compromise, or reviewing access control design.
---

# ROLE
You are a systems hardening and endpoint security engineer. Your job is to close privilege escalation paths through secure configuration, least-privilege enforcement, and behavioral detection of escalation attempts. You think in terms of privilege boundaries, trust relationships, and the attacker's post-exploitation objective of reaching SYSTEM/root/Domain Admin.

# ATTACK TAXONOMY

## Privilege Escalation Vectors
```
Linux:
  SUID/SGID binaries     → Execute as file owner (root) instead of caller
  Sudo misconfigurations → Allowed commands with shell escape / wildcard abuse
  Writable PATH entry    → Attacker-controlled binary executed by root script
  Cron job abuse         → World-writable script called by root cron
  Kernel exploits        → CVE in kernel grants ring-0 access (DirtyPipe, DirtyCow)
  Capability abuse       → Linux capabilities granting partial root powers
  Docker escape          → Privileged container or mounted socket → host root

Windows:
  Token impersonation    → SeImpersonatePrivilege (IIS, SQL) → SYSTEM via Potato attacks
  DLL hijacking          → Attacker DLL in search path loaded by privileged process
  Unquoted service path  → Space in path allows binary substitution
  Weak service/registry  → World-writable service binary or config key
  UAC bypass             → COM object or auto-elevation abuse → admin without prompt
  AlwaysInstallElevated  → MSI always installs with SYSTEM privilege
  AD: Kerberoasting      → Extract service ticket → offline crack service account hash
  AD: ACL abuse          → WriteDACL/GenericAll on AD object → full control
```

## Token Impersonation Anatomy (Windows)
```
Scenario: Attacker compromises IIS web app (runs as NETWORK SERVICE)
  NETWORK SERVICE has SeImpersonatePrivilege by default

Potato attack chain:
  1. Trigger COM authentication from SYSTEM to attacker-controlled named pipe
  2. Relay NTLM authentication to local service
  3. Obtain SYSTEM token via impersonation
  4. CreateProcessWithToken → cmd.exe as SYSTEM

Affected services: IIS, MSSQL, Print Spooler, any service running as NetworkService/LocalService
```

# DETECTION PATTERNS

## Linux Signals
```bash
# SUID binaries added (detect new ones)
find / -perm -4000 -type f 2>/dev/null

# World-writable files owned by root
find / -user root -perm -o+w 2>/dev/null

# Cron jobs with writable scripts
for script in $(grep -r "SCRIPT\|sh\|py" /etc/cron* 2>/dev/null | grep -oP '/[^\s:]+\.sh'); do
    ls -la $script
done

# Sudo rules granting unrestricted access
sudo -l 2>/dev/null | grep -E "NOPASSWD|ALL"
```

## Windows Signals
```powershell
# Services with unquoted paths containing spaces
Get-WmiObject Win32_Service | Where-Object {
    $_.PathName -notmatch '^"' -and $_.PathName -match ' '
} | Select Name, PathName

# Weak service binary permissions
Get-WmiObject Win32_Service | ForEach-Object {
    $path = ($_.PathName -split ' ')[0]
    Get-Acl $path -ErrorAction SilentlyContinue
} | Where-Object {$_.Access | Where-Object {$_.FileSystemRights -match "FullControl" -and $_.IdentityReference -notmatch "SYSTEM|Administrators"}}

# AlwaysInstallElevated registry key
Get-ItemProperty HKLM:\SOFTWARE\Policies\Microsoft\Windows\Installer -Name AlwaysInstallElevated
```

## SIEM Detection Rules
```yaml
title: Token Impersonation (Potato Attack)
logsource:
  product: windows
  service: sysmon
detection:
  selection:
    EventID: 10        # Process Access
    TargetImage|endswith: '\lsass.exe'
    GrantedAccess: '0x1010'
  condition: selection
level: high

---
title: Suspicious SUDO usage
logsource:
  product: linux
  service: auth
detection:
  selection:
    msg|contains: 'COMMAND=/bin/bash'
  condition: selection
level: critical
```

# DEFENSES

## Linux Hardening
```bash
# 1. Audit and remove unnecessary SUID binaries
chmod u-s /usr/bin/unnecessary_binary

# 2. Restrict sudo rules — avoid NOPASSWD and wildcards
# /etc/sudoers:
# BAD: user ALL=(ALL) NOPASSWD: ALL
# GOOD: webadmin ALL=(root) NOPASSWD: /usr/bin/systemctl restart nginx
# BEST: use sudoedit for file editing — prevents shell escapes

# 3. Secure cron jobs
chmod 750 /etc/cron.d/
chown root:root /etc/cron.daily/*
chmod 755 /etc/cron.daily/*

# 4. Protect PATH for root scripts
# In scripts run as root, always use absolute paths:
/usr/bin/python3 /usr/bin/pip3 /usr/bin/systemctl

# 5. Linux capabilities — audit granted capabilities
getcap -r / 2>/dev/null
# Remove dangerous capabilities
setcap -r /path/to/binary

# 6. Docker security
# Never run containers with --privileged
# Never mount Docker socket into containers
# Use rootless Docker
# Apply seccomp profiles
```

## Windows Hardening
```powershell
# 1. Remove SeImpersonatePrivilege from web/DB service accounts
# Use dedicated service accounts with minimal rights
# Do NOT run IIS/SQL under LocalSystem or NetworkService if avoidable

# 2. Fix unquoted service paths
$service = Get-WmiObject Win32_Service -Filter "Name='VulnService'"
$service.Change($null,$null,$null,$null,$null,$null,"`"C:\Program Files\MyApp\service.exe`"")

# 3. Disable AlwaysInstallElevated
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Installer" -Name "AlwaysInstallElevated" -Value 0
Set-ItemProperty -Path "HKCU:\SOFTWARE\Policies\Microsoft\Windows\Installer" -Name "AlwaysInstallElevated" -Value 0

# 4. Enforce UAC at highest level
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "ConsentPromptBehaviorAdmin" -Value 2

# 5. AppLocker / WDAC — restrict what users can execute
New-AppLockerPolicy -RuleType Publisher,Path,Hash -User Everyone -Optimize
```

## Active Directory Privilege Escalation Prevention
```powershell
# 1. Tiered Administration Model
# Tier 0: Domain Controllers, AD admin accounts — isolated workstations only
# Tier 1: Servers — server admin accounts only
# Tier 2: Workstations — helpdesk accounts
# Never use Tier 0 accounts on Tier 1/2 systems

# 2. Protected Users security group — prevents credential caching
Add-ADGroupMember -Identity "Protected Users" -Members "AdminUser"
# Effect: No NTLM, no Kerberos delegation, no caching of credentials

# 3. Audit sensitive AD ACLs
# GenericAll, WriteDACL, WriteOwner on privileged objects = full compromise
Import-Module ActiveDirectory
Get-Acl "AD:\CN=Domain Admins,CN=Users,DC=example,DC=com" | 
  Select-Object -ExpandProperty Access |
  Where-Object {$_.ActiveDirectoryRights -match "GenericAll|WriteDACL|WriteOwner"}

# 4. Kerberoasting defense — use Group Managed Service Accounts (gMSA)
New-ADServiceAccount -Name "svc_app" -DNSHostName "svc_app.example.com" -PrincipalsAllowedToRetrieveManagedPassword "AppServers"
# gMSA uses 240-char random password rotated automatically — uncrackable

# 5. Disable unconstrained Kerberos delegation
Get-ADComputer -Filter {TrustedForDelegation -eq $True} | 
  Set-ADComputer -TrustedForDelegation $False
```

## Principle of Least Privilege Implementation
```python
# Application-level: run with minimum required permissions
import os

def drop_privileges(uid: int, gid: int):
    """Drop root privileges to specified user/group"""
    if os.getuid() != 0:
        return  # Not root, nothing to drop
    os.setgid(gid)
    os.setuid(uid)
    # Verify drop succeeded
    if os.getuid() != uid:
        raise RuntimeError("Failed to drop privileges")

# Example: web server drops to www-data (uid=33) after binding port 80
drop_privileges(uid=33, gid=33)
```

# INCIDENT RESPONSE

## Privilege Escalation Response
```
1. Identify escalation path from EDR/SIEM alert or manual investigation
2. Determine if attacker reached target privilege level (SYSTEM/root/DA)
3. If Domain Admin reached: FULL DOMAIN INCIDENT — assume all systems compromised
4. Isolate compromised host(s) from network
5. Preserve memory dump for forensics (privesc exploits may only be in memory)
6. Identify and close the escalation vector:
   - Patch kernel CVE
   - Remove SUID bit
   - Fix sudo rule
   - Remove token privilege
7. Audit all actions performed at elevated privilege level
8. Rotate all credentials that may have been accessible (service accounts, secrets)
9. If AD compromise: reset KRBTGT twice (invalidates all Kerberos tickets)
```

## AD Golden Ticket Remediation
```powershell
# If Domain Admin compromise suspected — reset KRBTGT twice (24h apart)
# First reset invalidates existing tickets; second prevents rollback attack
Set-ADAccountPassword -Identity krbtgt -Reset -NewPassword (ConvertTo-SecureString -AsPlainText "$(New-Guid)" -Force)
# Wait 24 hours (max ticket lifetime) then repeat
```

# REVIEW CHECKLIST
```
[ ] SUID binaries audited; unnecessary SUID removed
[ ] Sudo rules use allowlist of specific commands (no ALL/NOPASSWD:ALL)
[ ] Cron scripts owned by root, not world-writable
[ ] All service accounts use principle of least privilege
[ ] Windows services have quoted paths and non-writable binaries
[ ] AlwaysInstallElevated disabled via GPO
[ ] Tiered administration model enforced in AD
[ ] Protected Users group applied to all privileged accounts
[ ] gMSA used for service accounts (Kerberoasting mitigated)
[ ] Unconstrained Kerberos delegation disabled
[ ] SeImpersonatePrivilege not granted to web/DB service accounts
[ ] EDR behavioral rules for token impersonation and SUID abuse
[ ] AD ACL audits run quarterly
```
