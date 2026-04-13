---
name: Windows Event Logs & Where to Find Them
trigger: windows event log, windows logs, event viewer, evtx, windows log files, check windows logs, system log windows, security log windows, application log windows, where are windows logs, windows event ids, powershell get event log, wevtutil, diagnose windows issue logs
description: Know where Windows event logs are stored, how to read them via Event Viewer and PowerShell, which logs contain what, and which Event IDs matter for common troubleshooting scenarios. Use when diagnosing system failures, authentication events, service crashes, or security incidents on Windows.
---

Windows logs nearly everything through its Event Log system — system events, security events, application crashes, logon events, and more. Knowing where to look and which Event IDs matter saves hours of guesswork.

## Event Log File Locations

```
C:\Windows\System32\winevt\Logs\

Key log files:
├── System.evtx          → OS and driver events: service starts/stops, hardware errors
├── Application.evtx     → App-level events: crashes, errors from installed software
├── Security.evtx        → Authentication: logon/logoff, privilege use, audit events
├── Setup.evtx           → Windows Update and component installation
├── Microsoft-Windows-PowerShell%4Operational.evtx  → PowerShell execution (if enabled)
└── Microsoft-Windows-<Component>%4Operational.evtx → Per-component logs (many)
```

All are `.evtx` format — binary, not text. Read with:
- **Event Viewer** (GUI): `eventvwr.msc`
- **PowerShell** `Get-WinEvent`
- **Command line** `wevtutil`

## Event Viewer (GUI)

Open: `Win+R` → `eventvwr.msc` or search "Event Viewer"

```
Event Viewer
├── Windows Logs
│   ├── Application       → App events
│   ├── Security          → Security/auth events (requires admin to read)
│   ├── Setup             → Windows Update events
│   ├── System            → OS/driver events
│   └── Forwarded Events  → Events forwarded from other machines
└── Applications and Services Logs
    └── Microsoft
        └── Windows
            └── <Component>
                └── Operational   → Detailed per-component operational logs
```

### Event Structure

Each event has:
- **Event ID** — numeric code identifying the event type
- **Level** — Information, Warning, Error, Critical, Verbose
- **Source** — Which component logged it
- **Time** — When it happened
- **User/Computer** — Who and where
- **Description** — Full details (often with error codes)

## The Most Important Event IDs

### Security Log (Logon Events)

| Event ID | Meaning |
|---|---|
| **4624** | Successful logon |
| **4625** | Failed logon (wrong password, locked account) |
| **4634** | Logoff |
| **4648** | Logon using explicit credentials (RunAs, mapped drive) |
| **4720** | User account created |
| **4722** | User account enabled |
| **4723** | User changed their own password |
| **4724** | Admin reset a user's password |
| **4725** | User account disabled |
| **4726** | User account deleted |
| **4728** | User added to security-enabled global group |
| **4732** | User added to security-enabled local group (e.g., added to Administrators) |
| **4740** | User account locked out |
| **4756** | Member added to universal security group |
| **4768** | Kerberos ticket (TGT) requested (domain login) |
| **4769** | Kerberos service ticket requested |
| **4771** | Kerberos pre-auth failed (wrong password on domain) |
| **4776** | NTLM authentication attempted |

### Logon Types (in Event 4624/4625)

| Type | Meaning |
|---|---|
| 2 | Interactive (local console or RDP) |
| 3 | Network (file share, mapped drive) |
| 4 | Batch (scheduled task) |
| 5 | Service (service logon) |
| 7 | Unlock (screen was locked and unlocked) |
| 8 | Network cleartext (basic auth, old protocols) |
| 9 | New credentials (RunAs with /netonly) |
| 10 | Remote Interactive (RDP/Terminal Services) |
| 11 | Cached Interactive (domain creds, offline) |

### Security Log (Privilege and Policy)

| Event ID | Meaning |
|---|---|
| **4672** | Special privileges assigned to new logon (admin logon) |
| **4688** | New process created (requires process auditing enabled) |
| **4689** | Process exited |
| **4697** | Service installed on the system |
| **4698** | Scheduled task created |
| **4699** | Scheduled task deleted |
| **4700** | Scheduled task enabled |
| **4702** | Scheduled task updated |
| **4703** | Token right adjusted |
| **4719** | System audit policy changed |
| **4738** | User account changed |
| **4776** | Domain controller validated credentials for an account |

### System Log (Service and OS Events)

| Event ID | Source | Meaning |
|---|---|---|
| **7034** | Service Control Manager | Service crashed unexpectedly |
| **7035** | Service Control Manager | Service sent start/stop control |
| **7036** | Service Control Manager | Service entered running/stopped state |
| **7040** | Service Control Manager | Service start type changed |
| **7045** | Service Control Manager | New service installed |
| **6005** | EventLog | Event Log service started (= system booted) |
| **6006** | EventLog | Event Log service stopped (= clean shutdown) |
| **6008** | EventLog | Previous shutdown was unexpected (crash/power loss) |
| **41** | Microsoft-Windows-Kernel-Power | System rebooted without clean shutdown (BSOD or power loss) |
| **1001** | BugCheck | BSOD occurred, contains stop code and dump file path |
| **10** | Microsoft-Windows-WMI | WMI activity — check if suspicious in security context |

### Application Log

| Event ID | Source | Meaning |
|---|---|---|
| **1000** | Application Error | Application crash — contains faulting module, exception code |
| **1001** | Windows Error Reporting | Dr. Watson post-crash report |
| **1026** | .NET Runtime | .NET application crash |
| **11707** | MsiInstaller | Product installation succeeded |
| **11708** | MsiInstaller | Product installation failed |
| **11724** | MsiInstaller | Product uninstalled |

## PowerShell — Reading Event Logs

```powershell
# Basic: Get-EventLog (older cmdlet, limited)
Get-EventLog -LogName System -Newest 50
Get-EventLog -LogName Security -InstanceId 4625 -Newest 100   # failed logons

# Modern: Get-WinEvent (preferred — works with all logs)
Get-WinEvent -LogName System -MaxEvents 50
Get-WinEvent -LogName Security -MaxEvents 100

# Filter by Event ID
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625} -MaxEvents 50

# Filter by time range
Get-WinEvent -FilterHashtable @{
    LogName='System'
    StartTime=(Get-Date).AddDays(-1)
    Level=2   # Error level
}

# Filter by multiple IDs
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624,4625,4740} |
    Select-Object TimeCreated, Id, Message | Format-Table -Wrap

# Filter by source
Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Service Control Manager'}

# Extract specific fields from Security log
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625} -MaxEvents 20 |
    ForEach-Object {
        $xml = [xml]$_.ToXml()
        [PSCustomObject]@{
            Time       = $_.TimeCreated
            Account    = $xml.Event.EventData.Data | Where-Object Name -eq 'TargetUserName' | Select-Object -ExpandProperty '#text'
            SourceIP   = $xml.Event.EventData.Data | Where-Object Name -eq 'IpAddress' | Select-Object -ExpandProperty '#text'
            LogonType  = $xml.Event.EventData.Data | Where-Object Name -eq 'LogonType' | Select-Object -ExpandProperty '#text'
        }
    }

# Get crash events (unexpected shutdowns)
Get-WinEvent -FilterHashtable @{LogName='System'; Id=41,6008} -MaxEvents 20

# List all available log names
Get-WinEvent -ListLog * | Where-Object {$_.RecordCount -gt 0} | Select-Object LogName, RecordCount

# Find events containing specific text
Get-WinEvent -LogName Application | Where-Object {$_.Message -like "*crash*"} | Select-Object -First 10

# Export events to CSV
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625} -MaxEvents 200 |
    Select-Object TimeCreated, Id, Message |
    Export-Csv C:\failed-logons.csv -NoTypeInformation
```

## wevtutil — Command Line Event Log Tool

```batch
# List available logs
wevtutil el

# Query events from Security log
wevtutil qe Security /c:20 /rd:true /f:text

# Query by Event ID
wevtutil qe Security "/q:*[System[(EventID=4625)]]" /c:50 /f:text

# Query by time range
wevtutil qe System "/q:*[System[TimeCreated[@SystemTime>='2024-04-01T00:00:00.000Z']]]" /f:text

# Export log to .evtx file
wevtutil epl Security C:\backup\security.evtx

# Import and read an exported .evtx file
wevtutil qe C:\backup\security.evtx /lf:true /f:text

# Clear a log (requires admin)
wevtutil cl Application

# Get log info (size, creation time, etc.)
wevtutil gl Security
```

## Per-Component Operational Logs

Many Windows components have their own detailed logs under:
`Applications and Services Logs → Microsoft → Windows → <Component>`

```powershell
# List all Microsoft Windows component logs
Get-WinEvent -ListLog "Microsoft-Windows-*" | Select-Object LogName, RecordCount | Sort-Object RecordCount -Descending

# Common useful ones:
"Microsoft-Windows-PowerShell/Operational"        # PowerShell commands run
"Microsoft-Windows-TaskScheduler/Operational"      # Scheduled task runs
"Microsoft-Windows-WindowsUpdateClient/Operational" # Windows Update events
"Microsoft-Windows-TerminalServices-LocalSessionManager/Operational"  # RDP sessions
"Microsoft-Windows-Sysmon/Operational"            # Sysmon (if installed) — security monitoring
"Microsoft-Windows-DNS-Client/Operational"         # DNS queries
"Microsoft-Windows-Firewall-With-Advanced-Security/Firewall"  # Firewall events
"Microsoft-Windows-WMI-Activity/Operational"       # WMI queries
```

## Quick Troubleshooting Scenarios

### "Why did my system reboot?"
```powershell
Get-WinEvent -FilterHashtable @{LogName='System'; Id=41,6008,6006,6005} -MaxEvents 10 |
    Select-Object TimeCreated, Id, Message | Format-Table -Wrap
```

### "What failed logins happened in the last hour?"
```powershell
Get-WinEvent -FilterHashtable @{
    LogName='Security'; Id=4625
    StartTime=(Get-Date).AddHours(-1)
} | Select-Object TimeCreated, Message
```

### "What services crashed today?"
```powershell
Get-WinEvent -FilterHashtable @{
    LogName='System'; Id=7034
    StartTime=(Get-Date).Date
}
```

### "What was installed/uninstalled recently?"
```powershell
Get-WinEvent -FilterHashtable @{
    LogName='Application'; Id=11707,11708,11724
    StartTime=(Get-Date).AddDays(-7)
} | Select-Object TimeCreated, Id, Message
```

### "Were any new services installed?" (potential malware)
```powershell
Get-WinEvent -FilterHashtable @{LogName='System'; Id=7045} -MaxEvents 20 |
    Select-Object TimeCreated, Message
```
