---
name: Linux Filesystem Hierarchy
trigger: linux filesystem, linux directories, linux folder structure, what is /etc, what is /var, what is /usr, linux directory layout, FHS, filesystem hierarchy standard, linux root folders, linux path, where is X on linux
description: Understand every top-level directory in the Linux Filesystem Hierarchy Standard (FHS). Use when navigating a Linux system, diagnosing where files should live, deciding where to install software, or troubleshooting missing files and permission errors.
---

Linux follows the **Filesystem Hierarchy Standard (FHS)**. Every directory has a defined purpose. Putting files in the wrong place causes breakage, security issues, or silent failures.

## Root-Level Directory Map

```
/
├── bin/       → Essential user binaries (ls, cp, cat, bash) — needed before /usr mounts
├── boot/      → Kernel, initramfs, bootloader config (GRUB). Do NOT delete anything here.
├── dev/       → Device files (not real files — hardware interfaces: /dev/sda, /dev/null, /dev/tty)
├── etc/       → System-wide configuration files. ALL config lives here. Plain text.
├── home/      → User home directories (/home/alice, /home/bob)
├── lib/       → Shared libraries for /bin and /sbin binaries
├── lib64/     → 64-bit shared libraries
├── lost+found/→ Recovered files after filesystem check (fsck). Usually empty. Don't touch.
├── media/     → Auto-mount point for removable media (USB drives, CDs)
├── mnt/       → Temporary manual mount points (you mount things here manually)
├── opt/       → Optional third-party software installed outside the package manager
├── proc/      → Virtual filesystem — live kernel and process info (NOT real files on disk)
├── root/      → Home directory of the root user (not inside /home)
├── run/       → Runtime data since last boot: PIDs, sockets, lock files. Cleared on reboot.
├── sbin/      → System binaries for root: fdisk, iptables, reboot
├── srv/       → Data served by the system (web server files, FTP data)
├── sys/       → Virtual filesystem — kernel device and driver info. Like /proc but structured.
├── tmp/       → Temporary files. World-writable. Usually cleared on reboot.
├── usr/       → Secondary hierarchy — most installed software lives here
│   ├── bin/   → User commands installed by packages (python3, git, vim)
│   ├── lib/   → Libraries for /usr/bin programs
│   ├── local/ → Locally compiled/installed software (not managed by package manager)
│   │   ├── bin/   → Your custom-compiled binaries
│   │   ├── lib/   → Libraries for /usr/local/bin
│   │   └── share/ → Architecture-independent data for local installs
│   ├── sbin/  → Non-essential system binaries (for root, installed by packages)
│   └── share/ → Architecture-independent data: man pages, icons, locale files
└── var/       → Variable data that changes at runtime
    ├── cache/ → Application cache data (apt cache, browser cache backends)
    ├── lib/   → Persistent application state (package manager db, docker data)
    ├── log/   → Log files from system and services
    ├── mail/  → User mailboxes
    ├── run/   → Old location for PID files (symlinked to /run on modern distros)
    ├── spool/ → Queued data: print jobs, cron jobs, mail queue
    └── tmp/   → Temporary files that persist across reboots (unlike /tmp)
```

## Where to Find Common Things

| What you want | Where to look |
|---|---|
| Network config | `/etc/network/`, `/etc/netplan/`, `/etc/NetworkManager/` |
| DNS settings | `/etc/resolv.conf`, `/etc/systemd/resolved.conf` |
| Hostname | `/etc/hostname` |
| Hosts file | `/etc/hosts` |
| User accounts | `/etc/passwd`, `/etc/shadow` (hashed passwords) |
| Groups | `/etc/group` |
| Cron jobs (system) | `/etc/crontab`, `/etc/cron.d/`, `/etc/cron.daily/` |
| Cron jobs (user) | `/var/spool/cron/crontabs/<username>` |
| SSH config | `/etc/ssh/sshd_config` (server), `~/.ssh/config` (client) |
| Sudoers | `/etc/sudoers` (edit with `visudo` ONLY) |
| Installed packages | `/var/lib/dpkg/` (Debian), `/var/lib/rpm/` (Red Hat) |
| Service units | `/etc/systemd/system/`, `/lib/systemd/system/` |
| Shell profiles | `~/.bashrc`, `~/.bash_profile`, `/etc/profile`, `/etc/profile.d/` |
| Environment vars | `/etc/environment`, `/etc/profile.d/*.sh` |
| Log files | `/var/log/` (see linux-logs skill) |
| Man pages | `/usr/share/man/` |
| Temp files | `/tmp/` (cleared on reboot), `/var/tmp/` (persists) |
| Kernel modules | `/lib/modules/$(uname -r)/` |
| Boot config | `/boot/grub/grub.cfg` or `/boot/grub2/grub.cfg` |
| Apt package cache | `/var/cache/apt/archives/` |

## Dangerous Directories — Handle With Extreme Care

```
/boot/         → Deleting kernel or initramfs = unbootable system
/etc/          → Wrong permissions or corrupt files = system won't boot or services fail
/lib/ /lib64/  → Removing libraries = cascading breakage of all binaries
/proc/ /sys/   → Never write here manually; writes affect live kernel state
/dev/          → Never delete device files; never write random data to /dev/sda
/root/         → Root's home; contains credentials and keys
/etc/shadow    → Hashed passwords; world-readable = offline password cracking risk
/etc/sudoers   → Corrupt this file = you lose all sudo access permanently
/var/lib/      → Contains package manager database, Docker volumes, database files
```

## Virtual Filesystems (/proc and /sys)

These look like directories but are **not real files on disk**. They are live interfaces to the kernel.

```bash
cat /proc/cpuinfo        # CPU information
cat /proc/meminfo        # Memory usage
cat /proc/$(pidof bash)/status  # Status of a running process
ls /proc/                # One numbered dir per running PID

cat /sys/class/net/eth0/speed   # Network interface speed
cat /sys/block/sda/size         # Disk size in 512-byte sectors
```

Writing to `/proc` or `/sys` changes kernel behavior in real time — useful for tuning, dangerous if done wrong.

## /tmp vs /var/tmp — Which to Use

| | `/tmp` | `/var/tmp` |
|---|---|---|
| Cleared on reboot | Yes (usually) | No |
| Typical use | Session-scoped scratch files | Files needed across reboots |
| Permission | 1777 (sticky bit — anyone can write, only owner can delete own files) | Same |
| Size limit | Often RAM-backed (tmpfs), limited | Disk-backed, larger |

## Key Rules

1. **Never run `rm -rf /` or `rm -rf /*`** — wipes the entire filesystem.
2. **Edit `/etc/sudoers` with `visudo` only** — it validates syntax before saving.
3. **`/usr/local/` is yours** — anything in `/usr/local/bin/` won't be overwritten by the package manager.
4. **/opt/ for big third-party apps** — JetBrains IDEs, custom Java apps, etc.
5. **Config belongs in /etc/** — not scattered in `/usr/share/` or `/var/`.
6. **Don't store data in /tmp/** — it may disappear on reboot or be cleared by the OS.
