---
name: Autostart & Persistence Locations (All OS)
trigger: autostart, startup programs, auto-run, autorun, programs that run at startup, startup folder windows, launch agents mac, systemd startup, cron at boot, how to add startup program, disable startup program, persistence locations, where does malware persist, startup scripts, login items
description: Know every location where programs and scripts can be configured to run automatically at boot, login, or on a schedule — across Windows, Linux, and macOS. Use when configuring startup programs, auditing for malware persistence, troubleshooting auto-starting processes, or disabling unwanted background programs.
---

Autostart locations are how legitimate programs (and malware) survive reboots. Auditing all of them is a core part of system administration and security work.

## Windows Autostart Locations

### Registry Run Keys (most common)

```
# All users — every login
HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run

# Current user only — every login
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run

# 32-bit apps on 64-bit system (WOW64)
HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run

# Run ONCE then delete (all users)
HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce

# Run once then delete (current user)
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce
```

### Startup Folders (File-based — easy to audit)

```
# Current user startup folder
C:\Users\<Username>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\

# All users startup folder
C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup\

# Open the startup folder quickly
shell:startup         (in Run dialog — current user)
shell:common startup  (in Run dialog — all users)
```

Any `.exe`, `.bat`, `.lnk`, `.vbs`, or `.ps1` shortcut dropped here runs at login.

### Windows Services

Services run in the background as SYSTEM, NetworkService, or a custom account — often before any user logs in:

```powershell
# List auto-start services
Get-Service | Where-Object {$_.StartType -eq 'Automatic'} | Select-Object Name, Status, StartType

# Via registry
HKLM\SYSTEM\CurrentControlSet\Services\   (Start=2 means Automatic)
```

### Scheduled Tasks

More powerful than Run keys — can trigger on login, at intervals, on events, at boot:

```powershell
# List all scheduled tasks
Get-ScheduledTask | Where-Object {$_.State -ne 'Disabled'} | Select-Object TaskName, TaskPath

# Via Task Scheduler GUI
taskschd.msc

# Task definitions stored at:
C:\Windows\System32\Tasks\           → System tasks
C:\Windows\SysWOW64\Tasks\           → 32-bit tasks
```

### Other Windows Persistence Locations

```
# Winlogon — shell replacement (malware hijacks Shell or Userinit)
HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\
  Shell     = explorer.exe        ← must be this; any addition is suspicious
  Userinit  = userinit.exe,       ← must end with comma; additions run at login

# Active Setup — runs once per user per machine at first login
HKLM\SOFTWARE\Microsoft\Active Setup\Installed Components\<GUID>

# Browser Helper Objects (legacy IE/Edge)
HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Browser Helper Objects\

# AppInit_DLLs — injected into every process that loads user32.dll
HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows\AppInit_DLLs
⚠️ Anything here other than empty is highly suspicious

# Image File Execution Options — debugger hijacking
HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\<exe>
  Debugger = <path>   ← malware uses this to replace legitimate executables

# COM Object hijacking (per-user HKCU overrides HKLM)
HKCU\SOFTWARE\Classes\CLSID\<GUID>\InprocServer32\

# Netsh helper DLLs
HKLM\SYSTEM\CurrentControlSet\Services\NetSH\DLL Paths\
```

### Windows Quick Audit Tool

**Sysinternals Autoruns** is the definitive tool — shows every autostart location on one screen:
```
https://learn.microsoft.com/en-us/sysinternals/downloads/autoruns
autoruns.exe   (GUI)
autorunsc.exe  (command line)
```

---

## Linux Autostart Locations

### systemd — The Primary System

```bash
# System-wide services (run as root, at boot)
/etc/systemd/system/           → Admin-created/installed services (higher priority)
/lib/systemd/system/           → Package-installed services
/usr/lib/systemd/system/       → Same as above on some distros

# User-level services (run at user login session)
~/.config/systemd/user/        → Per-user systemd services
/etc/systemd/user/             → System-wide user services

# List all enabled services
systemctl list-unit-files --state=enabled

# Enable a service to start at boot
systemctl enable myservice.service

# Check what's currently running
systemctl list-units --type=service --state=running
```

### Cron Jobs — Scheduled and Boot-Time

```bash
# User crontabs (edited with: crontab -e)
/var/spool/cron/crontabs/<username>

# System crontab
/etc/crontab

# Drop-in cron jobs (scripts)
/etc/cron.d/           → Arbitrary cron job files (any name)
/etc/cron.hourly/      → Scripts run every hour
/etc/cron.daily/       → Scripts run daily
/etc/cron.weekly/      → Scripts run weekly
/etc/cron.monthly/     → Scripts run monthly

# View all cron jobs
crontab -l                        # current user
sudo crontab -l                   # root
cat /etc/crontab
ls /etc/cron.d/ /etc/cron.daily/ /etc/cron.weekly/

# @reboot trick — runs at every boot via cron
@reboot /path/to/script.sh
```

### /etc/rc.local — Legacy (Still Works)

```bash
/etc/rc.local           → Commands here run at end of boot (as root)
                          Must be executable: chmod +x /etc/rc.local
```

Deprecated on systemd systems but still supported for compatibility. Check it during audits.

### Shell Profile Files — Run at Login/Shell Start

```bash
# Login shells (SSH login, console login):
/etc/profile            → System-wide login script
/etc/profile.d/*.sh     → Modular scripts sourced by /etc/profile
~/.bash_profile         → User login script (bash)
~/.profile              → User login script (POSIX shells)
~/.zprofile             → User login script (zsh)

# Interactive shells (terminal window, new shell):
~/.bashrc               → Per-user bash config
~/.zshrc                → Per-user zsh config
/etc/bash.bashrc        → System-wide bashrc

# All shells:
/etc/environment        → System-wide environment variables (parsed by PAM, not shell)
```

### init.d — SysV Init (Legacy, Still Present)

```bash
/etc/init.d/            → SysV init scripts (start/stop/restart)
/etc/rc?.d/             → Symlinks enabling/disabling init.d scripts per runlevel
                          S##name = start, K##name = kill

# On systemd systems, these are compatibility wrappers — systemd reads them
ls /etc/rc3.d/          # runlevel 3 (multi-user)
```

### X11/Desktop Autostart (Graphical Sessions)

```bash
# Per-user autostart (GNOME, KDE, XFCE, etc.)
~/.config/autostart/    → .desktop files that run at GUI login

# System-wide autostart
/etc/xdg/autostart/     → .desktop files for all users' GUI sessions
```

### Linux Quick Audit

```bash
# Check all cron jobs
for user in $(cut -f1 -d: /etc/passwd); do echo "=== $user ==="; crontab -u $user -l 2>/dev/null; done

# Check systemd enabled services
systemctl list-unit-files --state=enabled

# Check /etc/rc.local
cat /etc/rc.local 2>/dev/null

# Check profile scripts for suspicious additions
grep -r "curl\|wget\|bash\|python\|nc " /etc/profile.d/ ~/.bashrc ~/.profile 2>/dev/null

# Check for @reboot cron entries
grep -r "@reboot" /etc/cron* /var/spool/cron/ 2>/dev/null
```

---

## macOS Autostart Locations

### Launch Agents and Daemons (Primary Method)

```
# Current user's agents (run at user login, as that user)
~/Library/LaunchAgents/         → User-installed

# All users' agents (run at login for any user, as that user)
/Library/LaunchAgents/          → Admin-installed

# System daemons (run at boot, as root — no user needed)
/Library/LaunchDaemons/         → Admin-installed

# Apple's own (SIP-protected — do not touch)
/System/Library/LaunchAgents/
/System/Library/LaunchDaemons/
```

```bash
# List loaded launch agents
launchctl list

# Load a new agent
launchctl load ~/Library/LaunchAgents/com.company.app.plist

# Unload (disable) an agent
launchctl unload ~/Library/LaunchAgents/com.company.app.plist

# Check what's running (macOS 10.10+)
launchctl print system | grep enabled
```

### Login Items (User-Facing)

```bash
# Via System Settings → General → Login Items (macOS Ventura+)
# Stored in:
/var/db/com.apple.xpc.launchd/  → XPC service database (not directly editable)

# Legacy storage (older macOS)
~/Library/Preferences/com.apple.loginitems.plist
```

### Cron (macOS Supports It)

```bash
crontab -l          # current user cron jobs
sudo crontab -l     # root cron jobs
/etc/crontab        # system crontab
/etc/periodic/      # daily/weekly/monthly scripts
```

### Shell Profiles (same as Linux)

```bash
~/.zshrc            → zsh (default shell on macOS Catalina+)
~/.zprofile         → zsh login
~/.bash_profile     → bash (older macOS)
/etc/zshrc          → System-wide zsh
/etc/profile        → System-wide POSIX
```

### macOS Quick Audit

```bash
# List all launch agents/daemons
ls ~/Library/LaunchAgents/
ls /Library/LaunchAgents/
ls /Library/LaunchDaemons/

# Check loaded state
launchctl list | grep -v "^-"    # filter out Apple-signed entries

# Check cron
crontab -l; sudo crontab -l

# Check shell profiles for suspicious entries
grep -E "curl|wget|python|ruby|nc " ~/.zshrc ~/.zprofile ~/.bash_profile 2>/dev/null
```

---

## Cross-Platform Autostart Audit Checklist

```
Windows:
☐ HKLM\...\Run and HKCU\...\Run checked
☐ Startup folders checked (user and all users)
☐ Services list reviewed (auto-start, unusual names, unsigned paths)
☐ Scheduled Tasks reviewed
☐ Winlogon Shell and Userinit values verified
☐ Autoruns tool run

Linux:
☐ systemctl list-unit-files --state=enabled reviewed
☐ All user crontabs checked
☐ /etc/cron.d/, /etc/cron.daily/, etc. checked
☐ /etc/rc.local reviewed
☐ ~/.bashrc, ~/.profile, /etc/profile.d/ checked

macOS:
☐ ~/Library/LaunchAgents/ and /Library/LaunchAgents/ checked
☐ /Library/LaunchDaemons/ reviewed
☐ Login Items checked in System Settings
☐ crontab -l checked
☐ ~/.zshrc and ~/.zprofile reviewed
```
