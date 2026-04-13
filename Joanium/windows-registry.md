---
name: Windows Registry — Structure, Key Locations & Dangers
trigger: windows registry, regedit, registry hive, HKEY, registry keys, windows registry edit, registry dangerous, HKLM, HKCU, registry autorun, where are registry keys, windows registry paths, registry file locations, SAM registry, SYSTEM hive
description: Understand the Windows Registry — its five root hives, what lives where, where to find autorun entries, user settings, software config, and system settings. Know which keys are dangerous to modify and where malware hides. Use when troubleshooting, auditing, scripting, or managing Windows systems.
---

The Windows Registry is a hierarchical database that stores OS and application configuration. Every installed program, hardware device, user preference, and service registration lives here. Knowing its structure is essential for troubleshooting, scripting, and security work.

## The Five Root Hives (HKEY_*)

```
HKEY_LOCAL_MACHINE  (HKLM)   → Machine-wide settings — hardware, drivers, services, installed software
HKEY_CURRENT_USER   (HKCU)   → Settings for the currently logged-in user
HKEY_USERS          (HKU)    → All user profiles on the machine (HKCU is an alias to the current user's key here)
HKEY_CLASSES_ROOT   (HKCR)   → File type associations, COM objects, shell extensions (merge of HKLM\SOFTWARE\Classes and HKCU\SOFTWARE\Classes)
HKEY_CURRENT_CONFIG (HKCC)   → Current hardware profile (alias into HKLM\SYSTEM\CurrentControlSet\Hardware Profiles\Current)
```

## HKLM — Machine-Wide Settings Breakdown

```
HKLM\
├── HARDWARE\           → Runtime hardware detection (NOT stored on disk — built at boot from device probing)
├── SAM\                → Security Account Manager: local user accounts, groups, passwords
│                          ⚠️ ACL-protected even from administrators (requires SYSTEM privileges)
├── SECURITY\           → Security policy, LSA secrets, cached credentials
│                          ⚠️ ACL-protected — accessible by SYSTEM only
├── SOFTWARE\           → Installed software configuration, system settings
│   ├── Microsoft\Windows\CurrentVersion\
│   │   ├── Run\        → ⚠️ AUTORUN — programs listed here run at every user login
│   │   ├── RunOnce\    → Run once at next login, then deleted
│   │   ├── Uninstall\  → Installed programs registry (what Control Panel reads)
│   │   ├── Explorer\   → Explorer settings, shell folders
│   │   └── Policies\   → Group Policy settings enforced machine-wide
│   ├── <Vendor>\<App>\ → Per-application machine-wide config
│   └── Classes\        → File associations, COM, shell extensions (machine-wide)
└── SYSTEM\
    ├── CurrentControlSet\
    │   ├── Services\   → All Windows services and drivers — name, start type, image path
    │   ├── Control\    → System control parameters, session manager, computer name
    │   └── Enum\       → Hardware enumeration (PnP devices)
    └── Select\         → Which ControlSet is current/last-known-good
```

## HKCU — Current User Settings Breakdown

```
HKCU\
├── SOFTWARE\
│   ├── Microsoft\Windows\CurrentVersion\
│   │   ├── Run\        → ⚠️ AUTORUN — runs at login for THIS user only
│   │   ├── RunOnce\    → Runs once at next login for this user
│   │   ├── Explorer\   → Per-user Explorer settings
│   │   └── Policies\   → Per-user Group Policy
│   └── <Vendor>\<App>\ → Per-application per-user settings
├── Environment\        → Per-user environment variables (not session-level — persisted)
├── Control Panel\      → Per-user control panel settings (accessibility, mouse, keyboard)
├── Network\            → Mapped network drives
└── Printers\           → Per-user printer settings
```

## Autorun Locations — Where Programs Auto-Start

These are the most security-relevant registry keys. Malware almost always uses one of these:

```
# Run at every login (all users)
HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run

# Run at every login (current user only)
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run

# Run once then delete (all users)
HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce

# Run once then delete (current user)
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce

# 32-bit apps on 64-bit Windows (WOW64 redirect)
HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run

# Services — more powerful, runs as SYSTEM
HKLM\SYSTEM\CurrentControlSet\Services\<ServiceName>

# Active Setup — runs once per user at first login
HKLM\SOFTWARE\Microsoft\Active Setup\Installed Components\

# Shell extensions that load into Explorer
HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\
  → Userinit (must be: userinit.exe,)  ← malware hijacks this
  → Shell (must be: explorer.exe)      ← malware hijacks this

# Browser Helper Objects (IE/legacy)
HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Browser Helper Objects\
```

**Check all autorun locations with:** `Autoruns.exe` from Sysinternals (Microsoft) — the gold standard tool.

## Services Registry — How Windows Services Are Defined

```
HKLM\SYSTEM\CurrentControlSet\Services\<ServiceName>\
├── ImagePath    → Path to the executable (e.g., "C:\Windows\System32\svchost.exe -k netsvcs")
├── DisplayName  → Human-readable name shown in Services.msc
├── Start        → Start type: 0=Boot, 1=System, 2=Auto, 3=Manual, 4=Disabled
├── Type         → 1=Kernel driver, 2=File system driver, 16=Win32 own process, 32=Win32 shared process
├── ObjectName   → Account to run as (LocalSystem, LocalService, NetworkService, or custom)
└── Parameters\  → Service-specific configuration
```

Start type values:
- **0 (Boot):** Loaded by boot loader — kernel drivers
- **1 (System):** Loaded early in kernel init
- **2 (Auto):** Started automatically at OS startup — most services
- **3 (Manual):** Started on demand
- **4 (Disabled):** Never starts

## Registry Hive Files on Disk

The registry lives in these files (you cannot edit them while Windows is running):

```
C:\Windows\System32\config\
├── SAM         → HKLM\SAM (local accounts)
├── SECURITY    → HKLM\SECURITY (security policy, LSA secrets)
├── SOFTWARE    → HKLM\SOFTWARE
├── SYSTEM      → HKLM\SYSTEM
└── DEFAULT     → HKU\.DEFAULT (default profile, not a real user)

C:\Users\<Username>\
├── NTUSER.DAT          → HKCU for that user (loaded when they log in)
└── AppData\Local\Microsoft\Windows\UsrClass.dat  → HKCU\SOFTWARE\Classes for that user
```

**Offline access:** You can mount these hive files in Regedit without booting the system:
`File → Load Hive` — useful for forensics or recovery.

## Common Troubleshooting Locations

| What | Registry Path |
|---|---|
| Installed programs list | `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\` |
| 32-bit programs on 64-bit | `HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\` |
| File type associations | `HKCR\.<extension>` and `HKCR\<ProgID>` |
| Default browser | `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.html` |
| Computer name | `HKLM\SYSTEM\CurrentControlSet\Control\ComputerName\ComputerName` |
| Windows version | `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion` |
| Environment variables (system) | `HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment` |
| Environment variables (user) | `HKCU\Environment` |
| Winlogon (startup shell) | `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon` |
| Recent files MRU lists | `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs` |
| Network interfaces config | `HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\` |
| Time zone | `HKLM\SYSTEM\CurrentControlSet\Control\TimeZoneInformation` |

## Dangerous Keys — Handle With Care

```
HKLM\SYSTEM\CurrentControlSet\Services\   → Wrong value = unbootable or broken services
HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\
  → Shell or Userinit corrupted = can't log in
HKLM\SAM                                  → Local account database — corruption = lost accounts
HKLM\SECURITY                             → LSA secrets including cached domain credentials
HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\BootExecute
  → Programs that run before Windows loads fully — malware target
```

## Registry Command Line Tools

```powershell
# Read a value
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v ProductName

# Add/modify a value
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v MyApp /t REG_SZ /d "C:\path\app.exe" /f

# Delete a value
reg delete "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v MyApp /f

# Export a key to a .reg file
reg export "HKLM\SOFTWARE\MyApp" C:\backup\myapp.reg

# Import a .reg file
reg import C:\backup\myapp.reg

# PowerShell — read
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion"

# PowerShell — set
Set-ItemProperty -Path "HKCU:\Environment" -Name "MY_VAR" -Value "hello"

# PowerShell — new key
New-Item -Path "HKCU:\SOFTWARE\MyCompany\MyApp" -Force
```

## Quick Security Audit

```powershell
# Check all autorun entries (PowerShell)
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
Get-ItemProperty "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
Get-ItemProperty "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"

# Check Winlogon (should be explorer.exe and userinit.exe,)
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"

# List all auto-starting services
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\*" |
  Where-Object { $_.Start -eq 2 } |
  Select-Object PSChildName, ImagePath, Start
```
