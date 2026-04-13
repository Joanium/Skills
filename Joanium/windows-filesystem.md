---
name: Windows Filesystem & Directory Structure
trigger: windows directories, windows folders, windows filesystem, what is system32, windows folder structure, windows path, where is X on windows, windows directory, C drive layout, windows program files, appdata, windows special folders
description: Understand every important Windows directory — what lives there, what is safe to touch, what is dangerous, and where to find configuration, logs, user data, and installed programs. Use when troubleshooting, scripting, managing software, or auditing a Windows system.
---

Windows has a layered directory structure. Knowing it prevents accidental breakage, speeds up troubleshooting, and is essential for scripting and automation.

## Top-Level C:\ Directory Map

```
C:\
├── Program Files\          → 64-bit installed applications
├── Program Files (x86)\    → 32-bit installed applications (on 64-bit Windows)
├── ProgramData\            → Machine-wide app data (all users). Hidden by default.
├── Users\                  → All user profiles
│   ├── Public\             → Shared folder — all users can read/write
│   ├── Default\            → Template copied when a new user profile is created
│   └── <Username>\         → Your user profile (see User Directories section)
├── Windows\                → The OS itself. Be very careful here.
│   ├── System32\           → 64-bit system DLLs and core executables
│   ├── SysWOW64\           → 32-bit system DLLs (runs on 64-bit Windows)
│   ├── WinSxS\             → Side-by-side assembly store (DLL versions). Very large.
│   ├── Temp\               → System-level temporary files
│   ├── Fonts\              → Installed system fonts
│   ├── Logs\               → Windows component logs (CBS, DISM, etc.)
│   ├── Prefetch\           → App launch cache for faster startup. Safe to clear occasionally.
│   └── inf\                → Driver setup information files
└── $Recycle.Bin\           → Recycle bin for all users. Hidden. One subfolder per user SID.
```

## The Windows\ Directory — Critical Subdirectories

| Path | Purpose | Touch? |
|---|---|---|
| `Windows\System32\` | Core 64-bit DLLs, system executables (`cmd.exe`, `notepad.exe`, `svchost.exe`) | ⚠️ Never delete, be careful modifying |
| `Windows\SysWOW64\` | 32-bit DLL versions for backward compat on 64-bit systems | ⚠️ Never delete |
| `Windows\WinSxS\` | All versions of all Windows components. Very large (10–30 GB). | ✅ Clean with `DISM /Online /Cleanup-Image /StartComponentCleanup` only |
| `Windows\System32\drivers\` | Kernel-mode device drivers (.sys files) | ⚠️ Dangerous — bad driver = blue screen |
| `Windows\System32\config\` | Registry hive files (SAM, SYSTEM, SOFTWARE, SECURITY) | 🚫 Never touch while Windows is running |
| `Windows\System32\winevt\Logs\` | Windows Event Log files (.evtx) | ✅ Read with Event Viewer; safe to archive |
| `Windows\Temp\` | System-level temp files | ✅ Safe to clear when no services are running |
| `Windows\Prefetch\` | Prefetch data for app launch speed | ✅ Safe to clear; Windows regenerates |
| `Windows\Minidump\` | Crash dump files after BSODs | ✅ Read with WinDbg; safe to delete |
| `Windows\SoftwareDistribution\` | Windows Update download cache | ✅ Safe to clear (stop Windows Update service first) |

## User Profile Directories (C:\Users\<Username>\)

```
C:\Users\<Username>\
├── AppData\                → Hidden. Application data for this user.
│   ├── Local\              → Machine-specific app data (large files, caches, local DBs)
│   │   ├── Temp\           → User-level temp files. Safe to clear regularly.
│   │   └── Microsoft\      → Edge, Office, Windows data
│   ├── LocalLow\           → Low-integrity app data (sandboxed apps like browsers)
│   └── Roaming\            → Syncs across machines on domain. Config files, small data.
│       ├── Microsoft\      → Office settings, Outlook profiles, Start menu
│       └── <AppName>\      → Per-app roaming config
├── Desktop\
├── Documents\
├── Downloads\
├── Music\
├── Pictures\
├── Videos\
├── Favorites\              → IE/Edge bookmarks
├── Links\
├── Contacts\
└── Saved Games\
```

### AppData Breakdown — Where Apps Store What

| Folder | Stores | Sync on domain? |
|---|---|---|
| `AppData\Roaming\` | Settings, preferences, small config | ✅ Yes |
| `AppData\Local\` | Caches, large data, machine-specific state | ❌ No |
| `AppData\LocalLow\` | Low-trust sandboxed app data (browsers, PDF readers) | ❌ No |

**Common locations inside AppData:**
```
AppData\Roaming\Microsoft\Windows\Start Menu\Programs\    → User Start Menu shortcuts
AppData\Roaming\Microsoft\Windows\Recent\                 → Recent files list
AppData\Roaming\Microsoft\Credentials\                    → Saved credentials
AppData\Local\Microsoft\Windows\INetCache\                → Browser/IE cache
AppData\Local\Temp\                                       → User temp files — SAFE TO CLEAR
AppData\Local\Google\Chrome\User Data\Default\            → Chrome profile data
AppData\Roaming\Code\User\                                → VS Code settings
AppData\Roaming\npm\                                      → Global npm packages
```

## ProgramData vs Program Files — The Difference

| | `C:\Program Files\` | `C:\ProgramData\` |
|---|---|---|
| What | Installed application executables, DLLs | Machine-wide application data (databases, configs, licenses) |
| Per-user? | No — shared | No — shared across all users |
| Hidden by default? | No | **Yes** |
| Written to at runtime? | Rarely (bad practice) | Yes — apps write here constantly |
| Example | `Program Files\Git\bin\git.exe` | `ProgramData\chocolatey\`, `ProgramData\Docker\` |

## Environment Variables — Key Windows Paths

Always use environment variables in scripts instead of hardcoded paths:

```batch
%SystemRoot%           → C:\Windows
%SystemDrive%          → C:
%ProgramFiles%         → C:\Program Files
%ProgramFiles(x86)%    → C:\Program Files (x86)
%ProgramData%          → C:\ProgramData
%UserProfile%          → C:\Users\<Username>
%AppData%              → C:\Users\<Username>\AppData\Roaming
%LocalAppData%         → C:\Users\<Username>\AppData\Local
%Temp%                 → C:\Users\<Username>\AppData\Local\Temp
%WinDir%               → C:\Windows
%ComSpec%              → C:\Windows\System32\cmd.exe
%Public%               → C:\Users\Public
%HomeDrive%            → C:
%HomePath%             → \Users\<Username>
```

PowerShell equivalents:
```powershell
$env:USERPROFILE        # C:\Users\<Username>
$env:APPDATA            # AppData\Roaming
$env:LOCALAPPDATA       # AppData\Local
[Environment]::GetFolderPath('Desktop')   # Localization-safe path
```

## Dangerous Paths — Do Not Touch Without Care

```
C:\Windows\System32\              → Deleting DLLs here breaks Windows immediately
C:\Windows\System32\config\       → Live registry hive files — never modify while OS is running
C:\Windows\System32\drivers\      → Kernel drivers — wrong file = BSOD on next boot
C:\Windows\Boot\                  → Bootloader files — corruption = unbootable system
C:\Windows\WinSxS\               → Never manually delete — use DISM for cleanup
C:\Users\<User>\AppData\Roaming\Microsoft\Protect\  → DPAPI master keys (decrypts saved passwords)
C:\ProgramData\Microsoft\Windows\Start Menu\        → Modifying breaks Start Menu for all users
```

## Safe Cleanup Locations

```
C:\Windows\Temp\                              → Safe when services are stopped
C:\Users\<User>\AppData\Local\Temp\           → Safe to clear; use %Temp% variable
C:\Windows\SoftwareDistribution\Download\     → Safe; stop wuauserv service first
C:\Windows\Prefetch\                          → Safe; Windows regenerates
C:\$Recycle.Bin\                              → Safe; permanently deletes recycled files
C:\Windows\Minidump\                          → Safe after reviewing crash dumps
```

## System32 vs SysWOW64 — The Confusing 32/64-bit Flip

On 64-bit Windows, **System32 contains 64-bit DLLs** and **SysWOW64 contains 32-bit DLLs**. This is counterintuitive but intentional (backward compat with old code that hardcoded "System32").

- 64-bit process loading a DLL → goes to `System32`
- 32-bit process loading a DLL → Windows redirects to `SysWOW64` transparently

When writing scripts that target `System32` from a 32-bit process, use `Sysnative` as an alias to bypass the redirect:
```batch
C:\Windows\Sysnative\cmd.exe   → Forces 64-bit cmd.exe from a 32-bit script context
```
