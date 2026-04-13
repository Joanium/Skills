---
name: Temp Files, Caches & Safe Cleanup Locations
trigger: temp files, clear temp, disk space linux, clean disk windows, cache cleanup, where are temp files, delete temp files, free up disk space, /tmp cleanup, windows temp folder, mac cache cleanup, disk full linux, safe to delete, what can i delete
description: Know where temporary files and caches live on Linux, macOS, and Windows — what is safe to delete, what will regenerate automatically, and what to never touch. Use when freeing up disk space, troubleshooting disk-full errors, or setting up automated cleanup.
---

Disk full? Slow system? Knowing what's safe to delete versus what will break things is essential. Temporary files and caches are meant to be cleaned, but not all of them at all times.

## The Golden Rules of Cleanup

1. **Caches are always safe to delete** — apps regenerate them (next launch will be slower)
2. **Temp files of running processes are NOT safe to delete** — wait until the app is closed
3. **Logs are usually safe to archive or delete** — unless you're actively debugging
4. **Never delete files you don't understand** — look them up first
5. **Running processes hold file descriptors** — even "deleted" files take space until the process closes them

## Linux Cleanup Locations

### /tmp — Session Temp Files

```
Location: /tmp/
Cleared:   On reboot (usually — depends on systemd-tmpfiles config)
Contents:  Temp files created by any process or user
Permission: World-writable with sticky bit (1777)
```

```bash
# Safe to delete files YOU own in /tmp
rm -f /tmp/myfile.tmp

# Safe to clear all of /tmp (when no services are running that need it)
# WARNING: Don't do this on a live production system
sudo find /tmp -mindepth 1 -delete

# Check what's taking space
du -sh /tmp/*  2>/dev/null | sort -rh | head -20
```

### /var/tmp — Persistent Temp Files

```
Location: /var/tmp/
Cleared:   NOT on reboot — persists (that's the difference from /tmp)
Use case: Temp files that need to survive reboots (e.g., package manager work)
```

```bash
# Safer to check before deleting — some package managers use this
ls -la /var/tmp/
# Generally safe to clear files older than a few days:
sudo find /var/tmp -mindepth 1 -mtime +7 -delete
```

### Package Manager Caches

```bash
# APT (Debian/Ubuntu) — downloaded .deb files
/var/cache/apt/archives/
/var/cache/apt/pkgcache.bin
/var/cache/apt/srcpkgcache.bin

# Clean apt cache — safe
sudo apt clean                  # removes all cached .deb files
sudo apt autoclean              # removes only outdated cached packages
sudo apt autoremove             # removes unused dependency packages

# DNF/YUM (RHEL/Fedora/CentOS)
/var/cache/dnf/
sudo dnf clean all              # clear all dnf caches
sudo yum clean all

# Pacman (Arch)
/var/cache/pacman/pkg/
sudo pacman -Sc                 # remove unused cached packages
sudo pacman -Scc                # remove all cached packages

# Snap
/var/lib/snapd/cache/
sudo snap set system refresh.retain=2   # keep only 2 old snap versions
```

### systemd Journal (Can Grow Very Large)

```bash
journalctl --disk-usage         # how much space the journal uses

# Clean by time
sudo journalctl --vacuum-time=7d      # keep only last 7 days
sudo journalctl --vacuum-time=30d

# Clean by size
sudo journalctl --vacuum-size=500M    # keep only 500MB of logs
sudo journalctl --vacuum-size=1G
```

### Docker (Can Consume Tens of GB)

```bash
docker system df                # show disk usage by component

# Safe cleanup of unused containers, networks, dangling images
docker system prune             # removes stopped containers, dangling images, unused networks
docker system prune -a          # also removes images not used by any container
docker system prune -af --volumes   # ⚠️ also removes volumes — data loss possible

# Individual cleanup
docker container prune          # remove stopped containers
docker image prune              # remove dangling (untagged) images
docker image prune -a           # remove all unused images
docker volume prune             # ⚠️ removes unused volumes — check before running
docker network prune            # remove unused networks

# Docker data location:
/var/lib/docker/                # all Docker data (images, containers, volumes)
```

### User-Level Caches

```bash
~/.cache/                       # XDG cache dir — app caches
# Contents: browser caches, thumbnail cache, pip cache, npm cache, etc.

# Safe to delete entire ~/.cache:
rm -rf ~/.cache/*

# Thumbnail cache (can grow large)
rm -rf ~/.cache/thumbnails/

# pip cache
pip cache purge
# or: rm -rf ~/.cache/pip/

# npm cache
npm cache clean --force
# Location: ~/.npm/

# yarn cache
yarn cache clean
# Location: ~/.yarn/cache/ or ~/.cache/yarn/

# Cargo (Rust)
# ~/.cargo/registry/  ← safe to delete, re-downloads on next build
# ~/.cargo/git/       ← safe to delete

# Go build cache
go clean -cache         # removes build cache (~/.cache/go/build/)
go clean -modcache      # removes module cache (~/go/pkg/mod/) — re-downloads
```

### Log Rotation and Cleanup

```bash
# Current logs — only delete if not needed for debugging
/var/log/

# Force log rotation (rotates all logs now)
sudo logrotate -f /etc/logrotate.conf

# Safe to delete — already rotated
/var/log/*.gz          # compressed old logs
/var/log/*.1           # yesterday's logs (if space critical)

# Find large log files
find /var/log -name "*.log" -size +100M 2>/dev/null | xargs ls -lh
```

### General Space Analysis

```bash
# How full are disks?
df -h

# What's using the most space? (top-level)
du -sh /* 2>/dev/null | sort -rh | head -20

# Drill into a specific directory
du -sh /var/log/* | sort -rh | head -10

# Find large files anywhere
find / -size +500M -type f 2>/dev/null | xargs ls -lh

# Find recently modified large files (possible runaway log)
find /var -name "*.log" -size +50M -mtime -1 2>/dev/null
```

---

## Windows Cleanup Locations

### Safe to Delete

```
C:\Windows\Temp\
→ System temp files. Safe when no services are using them.
→ Best practice: Stop services first or do it in Safe Mode

%TEMP% = C:\Users\<Username>\AppData\Local\Temp\
→ Per-user temp files. Safe to delete contents.
→ Open in Explorer: type %temp% in the address bar or Run dialog
→ Some files may be locked by running apps — skip those

C:\Windows\Prefetch\
→ App launch cache files (.pf files). Safe to delete.
→ Windows regenerates them; next app launches will be slightly slower once.

C:\Windows\SoftwareDistribution\Download\
→ Windows Update downloaded files. 
→ Stop Windows Update service first: net stop wuauserv
→ Delete contents, then: net start wuauserv

C:\Windows\Installer\
→ Patch cache — needed for uninstall/repair of some apps.
→ Do NOT delete unless you use a specialized tool (PatchCleaner).
→ Deleting manually can break MSI-based software uninstallers.

C:\Windows\WinSxS\
→ Component store. Very large (10–30 GB).
→ DO NOT delete manually. Use DISM to clean it up:
→ DISM /Online /Cleanup-Image /StartComponentCleanup
→ DISM /Online /Cleanup-Image /SPSuperseded (after SP installs)

C:\$Recycle.Bin\
→ Recycle bin for all users. Safe to empty via Explorer or:
→ rd /s /q C:\$Recycle.Bin\

C:\Users\<Username>\AppData\Local\Microsoft\Windows\INetCache\
→ IE/Edge browser cache. Safe to delete.
→ Also: Edge cache: C:\Users\<Username>\AppData\Local\Microsoft\Edge\User Data\Default\Cache\
→ Chrome cache: C:\Users\<Username>\AppData\Local\Google\Chrome\User Data\Default\Cache\
```

### Windows Built-In Cleanup Tools

```powershell
# Disk Cleanup (GUI)
cleanmgr.exe
cleanmgr.exe /d C:          # target C: drive
cleanmgr.exe /sageset:1      # configure what to clean
cleanmgr.exe /sagerun:1      # run configured cleanup (admin-level)

# Storage Sense (modern — Settings > System > Storage)
# Configure via PowerShell:
Set-StorageSetting -Name StorageSenseEnabled -Value 1

# DISM — Windows component store cleanup
DISM /Online /Cleanup-Image /StartComponentCleanup
DISM /Online /Cleanup-Image /RestoreHealth    # also repairs corruption

# Clear Windows Update cache
net stop wuauserv
rd /s /q C:\Windows\SoftwareDistribution\Download
net start wuauserv
```

### Developer Tool Caches (Windows)

```powershell
# npm (Node.js)
npm cache clean --force
# Location: %APPDATA%\npm-cache\

# pip (Python)
pip cache purge
# Location: %LOCALAPPDATA%\pip\Cache\

# NuGet (.NET)
dotnet nuget locals all --clear
# Location: %USERPROFILE%\.nuget\packages\

# Maven (Java)
# Location: %USERPROFILE%\.m2\repository\ — safe to delete, re-downloads
Remove-Item -Recurse "$env:USERPROFILE\.m2\repository" -Force

# Gradle (Java)
# Location: %USERPROFILE%\.gradle\caches\ — safe to delete
Remove-Item -Recurse "$env:USERPROFILE\.gradle\caches" -Force
```

---

## macOS Cleanup Locations

### User Cache (Safe to Delete)

```bash
~/Library/Caches/               # per-user app caches
# Safe to delete entire directory — apps regenerate
rm -rf ~/Library/Caches/*

# Specific app caches:
~/Library/Caches/com.apple.Safari/
~/Library/Caches/Google/Chrome/Default/Cache/
~/Library/Caches/com.spotify.client/

# System caches (requires sudo)
/Library/Caches/                # system-wide app caches
sudo rm -rf /Library/Caches/*
```

### Xcode Derived Data and Archives (Often Huge — 10–50 GB)

```bash
~/Library/Developer/Xcode/DerivedData/   # build products — safe to delete
~/Library/Developer/Xcode/Archives/       # app archives — only delete old ones you don't need
~/Library/Developer/CoreSimulator/Devices/ # simulator data — use: xcrun simctl delete unavailable

# Clean from Xcode: Product > Clean Build Folder (⌘+⇧+K)
# Or from command line:
rm -rf ~/Library/Developer/Xcode/DerivedData/*
```

### Homebrew Cache

```bash
brew cleanup                     # remove old versions of installed formulae
brew cleanup -s                  # also remove cached downloads
# Cache location: ~/Library/Caches/Homebrew/
```

### Application Logs

```bash
~/Library/Logs/                  # user app logs — safe to delete
/Library/Logs/                   # system app logs — safe to delete
/private/var/log/                # system logs — managed by newsyslog

# Crash reports
~/Library/Logs/DiagnosticReports/    # user crash reports — safe to delete
/Library/Logs/DiagnosticReports/     # system crash reports — safe to delete
```

### macOS System and App Data

```bash
# Saved application state (window restoration)
~/Library/Saved\ Application\ State/    # safe to delete — apps lose window restore
rm -rf ~/Library/Saved\ Application\ State/*

# Large Mail attachments
~/Library/Mail/V10/              # Mail data — DON'T delete unless migrating/quitting Mail

# iOS device backups (can be 10s of GB)
~/Library/Application\ Support/MobileSync/Backup/

# Old iOS updates
~/Library/iTunes/iPhone\ Software\ Updates/

# Docker for Mac
~/Library/Containers/com.docker.docker/Data/  # all Docker data
```

### macOS Built-In Storage Analysis

```bash
# Terminal
du -sh ~/Library/Caches/* 2>/dev/null | sort -rh | head -20
du -sh ~/* 2>/dev/null | sort -rh | head -10

# GUI tools:
# System Settings → General → Storage (shows breakdown by category)
# Or third-party: DaisyDisk, OmniDiskSweeper, ncdu
```

---

## Quick Reference — Is It Safe to Delete?

| Location | Safe? | Notes |
|---|---|---|
| `/tmp/*` (Linux) | ✅ After reboot or if no running process owns them | |
| `/var/cache/apt/archives/` | ✅ | Packages re-downloaded if needed |
| `~/.cache/` (Linux/macOS) | ✅ | Apps regenerate |
| `~/Library/Caches/` (macOS) | ✅ | Apps regenerate |
| `%TEMP%` (Windows) | ✅ | Skip locked files |
| `journalctl` logs | ✅ Use vacuum commands | |
| `/var/log/*.gz` | ✅ Rotated old logs | |
| `docker system prune` | ✅ | Unused containers/images |
| `docker volume prune` | ⚠️ | Only unused volumes — check first |
| `Windows\SoftwareDistribution\Download\` | ✅ Stop service first | |
| `Windows\Installer\` | ❌ | Breaks MSI uninstalls |
| `Windows\WinSxS\` | ❌ Direct delete | Use DISM only |
| `/var/lib/docker/` | ❌ Direct delete | Use docker commands |
| `~/Library/Mail/` | ❌ | Email data — back up first |
| `/etc/*` | ❌ | Config files — never delete |
| `/lib`, `/usr/lib` | ❌ | System libraries |
