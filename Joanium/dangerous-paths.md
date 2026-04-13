---
name: Dangerous OS Paths — Never Delete or Modify Without Care
trigger: dangerous paths, never delete, safe to delete, what not to delete linux, system32 delete, dangerous folders, critical system files, will this break my system, rm rf dangerous, windows critical files, protected files, what happens if I delete X
description: Know exactly which paths and files are critical to OS function, what breaking them causes, and the safe alternatives. Use before deleting anything in system directories, when cleaning up disk space, or when assessing the impact of a change.
---

Some paths look like cleanup candidates but will destroy the OS if touched. Others look scary but are safe. This skill gives you the definitive danger map.

## The Universal Rule

> **If you don't know exactly what a file does and what will break without it, don't delete it.**

The second rule: **Always backup before modifying any system file.** A broken `/etc/fstab` or `/etc/sudoers` can make a system unbootable or unmanageable in seconds.

---

## Linux — Extremely Dangerous Paths

### 🚫 Never Delete or Modify — Immediate System Failure

```
/bin/           → Core binaries. Delete ls, cp, or bash → terminal stops working.
/sbin/          → System admin binaries. Delete mount, reboot → can't manage system.
/lib/           → Shared libraries. Delete libc.so.6 → EVERY program on the system stops.
/lib64/         → 64-bit libraries. Same consequence as /lib/.
/usr/lib/       → More libraries. Deleting breaks installed applications.
/usr/bin/       → Installed user commands. Delete python3 → all Python scripts fail.
/boot/          → Kernel and bootloader. Delete vmlinuz or initrd → system won't boot.
/boot/grub/     → GRUB bootloader config. Corrupt → unbootable.
/dev/           → Device files. Delete /dev/sda → can't access the disk.
                  Delete /dev/null → programs that write to it will fail or hang.
/proc/          → Virtual kernel filesystem. Never write to it manually.
/sys/           → Virtual kernel device tree. Writes affect live kernel state.
```

### 🚫 Never Delete — Authentication and Access Breakage

```
/etc/passwd     → Delete or corrupt → no one can log in (login looks up users here)
/etc/shadow     → Hashed passwords. Delete → root loses password; accounts broken.
/etc/group      → Group definitions. Delete → group-based permissions fail everywhere.
/etc/sudoers    → Corrupt this (e.g., by editing directly without visudo) → sudo stops working.
                  Recovery requires booting to single-user mode or rescue media.
/etc/ssh/ssh_host_*_key  → Server SSH host keys. Delete → SSH server identity changes,
                           all clients get "WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED"
                           and refuse to connect until they clear their known_hosts.
```

### ⚠️ Dangerous to Modify — Careful Editing Required

```
/etc/fstab      → Wrong entry here → system won't boot (filesystem fails to mount).
                  Always: mount -a before rebooting to test.
/etc/grub.d/    → GRUB generation scripts. Corrupt → can't regenerate bootloader.
/etc/network/   → Wrong network config → lose remote access permanently.
/etc/hosts      → Corrupt → hostname resolution breaks for all processes.
/etc/ld.so.conf → Library search path. Wrong entry → binaries can't find libraries.
/etc/pam.d/     → PAM authentication modules. Delete or corrupt → can't log in.
/etc/crontab    → Syntax errors can silently prevent all cron jobs from running.
                  Test with: crontab -l (to check) or use cron syntax validators.
/etc/systemd/   → Wrong unit file syntax → service fails to start, may cause boot issues.
/var/lib/dpkg/  → APT/dpkg package database. Corrupt → can't install/remove packages.
/var/lib/rpm/   → RPM package database (RHEL/CentOS). Same risk.
```

### The Most Dangerous Linux Commands

```bash
# ❌ NEVER run these
rm -rf /                    # Wipes entire filesystem. On older systems, actually works.
rm -rf /*                   # Same — deletes contents of /
rm -rf ./*  (from /)        # Same
chmod -R 777 /              # Makes entire system world-writable — catastrophic security
chown -R nobody /           # Changes ownership of everything — breaks all permission checks
dd if=/dev/zero of=/dev/sda # Zeros your disk. No recovery.
dd if=/dev/urandom of=/dev/sda  # Same — irreversible disk wipe
mkfs.ext4 /dev/sda          # Formats your disk — immediate data loss

# ❌ Commands that look safe but aren't
mv /lib /lib.bak            # Breaks ALL programs immediately (can't find libraries)
                            # Do NOT rename or move system lib dirs, even temporarily
```

---

## Windows — Extremely Dangerous Paths

### 🚫 Never Delete or Modify

```
C:\Windows\System32\
→ Core system DLLs and executables. Deleting kernel32.dll, ntdll.dll, or any core DLL
  causes immediate system failure. Windows will not boot or will BSOD.

C:\Windows\System32\config\SAM
C:\Windows\System32\config\SYSTEM
C:\Windows\System32\config\SOFTWARE
C:\Windows\System32\config\SECURITY
→ Registry hive files. NEVER modify while Windows is running.
  Corruption = unbootable system or permanent loss of all accounts and settings.

C:\Windows\System32\drivers\
→ Kernel mode drivers (.sys files). Deleting a required driver = BSOD on next boot.

C:\Windows\Boot\
→ Bootloader files. Deleting bootmgr or BCD = "BOOTMGR is missing" on next boot.

C:\Windows\WinSxS\
→ Component store. Contains all Windows component versions.
  Manual deletion breaks Windows Update and system repair. Use DISM only.

C:\Windows\SysWOW64\
→ 32-bit system DLLs. Delete = all 32-bit applications fail.

C:\Windows\System32\ntoskrnl.exe    → Windows kernel. Delete = BSOD immediately.
C:\Windows\System32\hal.dll         → Hardware abstraction layer. Delete = BSOD.
C:\Windows\System32\winload.exe     → Boot loader. Delete = won't boot.
```

### ⚠️ Dangerous to Modify

```
C:\Windows\System32\drivers\etc\hosts
→ Syntax errors break hostname resolution for all applications.

HKLM\SYSTEM\CurrentControlSet\Services\
→ Wrong Start value, deleted ImagePath, or corrupted service key = services fail to start,
  possible unbootable system if a critical service is affected.

HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\
  Shell = explorer.exe      → Change this = Windows starts without the shell (blank screen)
  Userinit = userinit.exe,  → Change this = can't log in

C:\Windows\Installer\
→ MSI install cache. Manual deletion breaks uninstall and repair for many applications.
  Use PatchCleaner to safely prune this directory.

C:\Users\<User>\NTUSER.DAT
→ User's registry hive. Corrupt or delete = that user's profile breaks.
  Windows may create a temporary profile on next login, losing all settings.
```

### Windows: Misleadingly Large Files That Are Safe With the Right Tool

```
C:\Windows\WinSxS\         → Use: DISM /Online /Cleanup-Image /StartComponentCleanup
C:\Windows\Installer\      → Use: PatchCleaner tool only
C:\pagefile.sys            → Virtual memory page file. Windows manages this size.
                             Don't delete manually; disable via System Properties if needed.
C:\hiberfil.sys            → Hibernate file (size = RAM amount).
                             Safe to remove only if you disable hibernation:
                             powercfg /hibernate off
C:\swapfile.sys            → Used by Windows Store apps. Don't delete manually.
```

---

## macOS — Dangerous Paths

### 🚫 Never Delete — SIP-Protected

Apple's System Integrity Protection (SIP) prevents modification of these paths even as root. Attempting to delete anything here will fail with "Operation not permitted":

```
/System/               → Core macOS OS files
/System/Library/       → Apple's frameworks, extensions, services
/bin/                  → Core Unix binaries
/sbin/                 → System binaries
/usr/ (except /usr/local/)   → System utilities and libraries
```

### ⚠️ Dangerous to Modify (SIP doesn't protect these)

```
/private/etc/hosts      → Break this = DNS resolution fails for all apps.
/private/etc/sudoers    → Corrupt = lose all sudo access.
/private/etc/fstab      → Wrong entry = filesystem won't mount on boot.
~/Library/Keychains/    → Never manually edit.
                          Corrupted keychain = saved passwords lost, apps crash.
~/Library/Mail/         → Delete = all emails gone. Back up before touching.

/Library/LaunchDaemons/ → Malformed plist = service fails; very malformed = boot loop.
                          Validate with: plutil -lint /Library/LaunchDaemons/myfile.plist
```

---

## What Actually Happens When You Break Each Thing

| What you broke | What fails | Recovery |
|---|---|---|
| Linux `/etc/sudoers` (wrong syntax) | All sudo commands fail immediately | Boot to single-user mode (add `single` to kernel cmdline), edit the file |
| Linux `/etc/fstab` (bad entry) | System won't boot past filesystem mount | Boot from live USB, mount filesystem, edit /etc/fstab |
| Linux `/lib/libc.so.6` deleted | Every single program stops working — system is dead | Boot from live USB, chroot in, reinstall libc |
| Linux `/etc/passwd` deleted | No one can log in | Boot from live USB, restore from backup |
| Windows `System32\kernel32.dll` deleted | Immediate BSOD on next boot | WinRE recovery console, `sfc /scannow` from installation media |
| Windows Registry hive corrupted | Boot failure or login failure | WinRE → Advanced Options → Startup Repair or System Restore |
| Windows `C:\Windows\Boot\` deleted | "BOOTMGR is missing" on reboot | WinRE → Startup Repair, or: `bootrec /fixboot /fixmbr /rebuildbcd` |
| macOS `/etc/hosts` corrupted | DNS resolution fails for all apps | Boot to Recovery Mode, use Terminal to edit |
| macOS `~/Library/Keychains/` deleted | Saved passwords lost, apps that use keychain crash | Restore from Time Machine |

---

## Danger Level Summary

```
🔴 CATASTROPHIC — Permanent data loss or unbootable system, difficult/impossible recovery
   Linux:   /lib/, /boot/, /etc/passwd, /etc/shadow
   Windows: System32 DLLs, Registry hives, Boot files
   macOS:   /System/ (SIP prevents this), ~/Library/Keychains/

🟠 SEVERE — System broken, recovery requires rescue media or significant work
   Linux:   /etc/fstab, /etc/sudoers, /bin/, /sbin/
   Windows: C:\Windows\Installer\, Winlogon registry keys
   macOS:   /etc/sudoers, /Library/LaunchDaemons/ with bad plists

🟡 MODERATE — Service or feature broken, recoverable without rescue media
   Linux:   /etc/hosts, /etc/crontab, /etc/network/
   Windows: C:\Windows\Temp\ (wrong timing), Startup registry keys
   macOS:   ~/Library/Preferences/ (resets app settings), LaunchAgents

🟢 SAFE TO CLEAN (with caveats)
   /tmp/, %TEMP%, ~/Library/Caches/, ~/.cache/
   /var/cache/apt/, Windows Prefetch, SoftwareDistribution\Download\
```
