---
name: Linux Log Files & Where to Find Them
trigger: linux logs, log files linux, where are logs linux, /var/log, syslog, journald, journalctl, linux logging, check logs linux, system logs linux, application logs, service logs, auth log, kernel log, how to read linux logs
description: Know exactly where to find logs on Linux — system logs, authentication logs, service logs, application logs — and how to read them with journalctl, tail, grep, and other tools. Use when diagnosing boot failures, authentication problems, service crashes, application errors, or security incidents.
---

Linux logging happens in two parallel systems on modern distros: the **traditional syslog files** in `/var/log/` and **systemd's journal** (`journalctl`). Knowing both is essential.

## /var/log/ — The Main Log Directory

```
/var/log/
├── syslog          → General system messages (Debian/Ubuntu) — catch-all
├── messages        → General system messages (RHEL/CentOS/Fedora)
├── auth.log        → Authentication: login attempts, sudo, SSH (Debian/Ubuntu)
├── secure          → Authentication log (RHEL/CentOS equivalent of auth.log)
├── kern.log        → Kernel messages only
├── dmesg           → Boot-time kernel ring buffer messages (hardware, drivers)
├── boot.log        → Boot process messages
├── faillog         → Failed login attempts (binary — use `faillog` command)
├── lastlog         → Last login per user (binary — use `lastlog` command)
├── wtmp            → Login/logout history (binary — use `last` command)
├── btmp            → Failed login attempts (binary — use `lastb` command)
├── cron.log        → Cron job execution logs (Debian/Ubuntu)
├── dpkg.log        → Package install/remove history (Debian/Ubuntu)
├── apt/            → Detailed apt package manager logs
├── yum.log         → Package install/remove history (CentOS/RHEL)
├── mail.log        → Mail server (postfix, sendmail) events
├── Xorg.0.log      → X11 display server log
├── journal/        → systemd journal binary store
├── nginx/
│   ├── access.log  → Web request log
│   └── error.log   → Web server errors
├── apache2/
│   ├── access.log
│   └── error.log
├── mysql/
│   └── error.log
├── postgresql/
│   └── postgresql-<version>-main.log
└── cups/           → Printer service logs
```

## Which Log to Check for What

| Problem | First log to check |
|---|---|
| System won't boot | `journalctl -b -1` (previous boot), `/var/log/boot.log` |
| Service crashed | `journalctl -u <service-name> -n 100` |
| Login failure | `/var/log/auth.log` or `/var/log/secure` |
| SSH brute force | `/var/log/auth.log` — grep for "Failed password" |
| Sudo abuse | `/var/log/auth.log` — grep for "sudo" |
| Kernel panic or hardware error | `dmesg`, `journalctl -k`, `/var/log/kern.log` |
| Package install failed | `/var/log/dpkg.log`, `/var/log/apt/` |
| Application error | App-specific log in `/var/log/<app>/error.log` |
| Web server 500 error | `/var/log/nginx/error.log` or `/var/log/apache2/error.log` |
| Database errors | `/var/log/mysql/error.log`, `/var/log/postgresql/` |
| Disk or filesystem error | `dmesg | grep -i "error\|fail\|warn"`, `/var/log/kern.log` |
| OOM (Out of Memory) killer | `dmesg | grep -i "oom\|killed"` |
| Cron job not running | `/var/log/cron.log` or `journalctl -u cron` |

## journalctl — systemd Journal (Modern Systems)

`journalctl` queries the binary journal managed by `systemd-journald`. It's the primary tool on any systemd-based distro (Ubuntu 16+, Debian 8+, RHEL 7+, Fedora, Arch, etc.).

```bash
# All logs since last boot
journalctl -b

# Logs from previous boot (useful after a crash)
journalctl -b -1
journalctl -b -2    # two boots ago

# Follow (like tail -f) — live streaming
journalctl -f

# Specific service
journalctl -u nginx
journalctl -u ssh -n 50           # last 50 lines for ssh
journalctl -u docker -f           # follow docker logs live

# Time ranges
journalctl --since "2024-04-10 10:00:00" --until "2024-04-10 12:00:00"
journalctl --since "1 hour ago"
journalctl --since today

# Priority filtering
journalctl -p err               # errors and above only
journalctl -p warning           # warnings and above
# Levels: emerg, alert, crit, err, warning, notice, info, debug

# Kernel messages only
journalctl -k
journalctl -k -b -1    # kernel messages from previous boot

# Show disk usage of journal
journalctl --disk-usage

# Vacuum old journal logs
journalctl --vacuum-time=7d      # keep only last 7 days
journalctl --vacuum-size=500M    # keep only 500MB

# Output as JSON
journalctl -u nginx -o json-pretty | head -50

# Show log entries with specific string
journalctl | grep "Out of memory"
```

## tail, grep, less — Working With Text Logs

```bash
# Follow a log in real time
tail -f /var/log/syslog
tail -f /var/log/nginx/access.log

# Last 100 lines
tail -n 100 /var/log/auth.log

# Search for pattern
grep "Failed password" /var/log/auth.log
grep "ERROR" /var/log/syslog | tail -50

# Case-insensitive search
grep -i "error\|fail\|warn" /var/log/syslog

# Show 5 lines of context around matches
grep -C 5 "segfault" /var/log/syslog

# Search compressed rotated logs too
zgrep "Failed" /var/log/auth.log.2.gz

# Combine tail and grep
tail -f /var/log/syslog | grep --line-buffered "error"

# Navigate with less
less /var/log/syslog
# In less: G=end, g=start, /pattern to search, n=next match, q=quit
```

## Log Rotation — /etc/logrotate.d/

Logs rotate automatically to prevent filling the disk. Rotated files follow naming conventions:

```
syslog          → current
syslog.1        → yesterday's / last rotation
syslog.2.gz     → compressed older log
syslog.3.gz
syslog.4.gz
```

Configuration: `/etc/logrotate.conf` and `/etc/logrotate.d/<service>`

```bash
# Force immediate rotation
logrotate -f /etc/logrotate.conf

# View rotation config for nginx
cat /etc/logrotate.d/nginx
```

## dmesg — Kernel Ring Buffer

Kernel messages from the current boot (hardware detection, driver issues, filesystem errors):

```bash
dmesg                          # all kernel messages
dmesg | tail -50               # recent messages
dmesg -T                       # with human-readable timestamps
dmesg | grep -i "error\|fail\|warn"
dmesg | grep -i "usb"          # USB device events
dmesg | grep -i "oom\|killed"  # Out of memory killer
dmesg | grep -i "sda\|nvme"    # Disk errors
dmesg -w                       # follow in real time (like tail -f)
```

## Authentication Log Patterns to Know

```bash
# Failed SSH login attempts
grep "Failed password" /var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -rn
# → Shows top IP addresses brute-forcing your SSH

# Successful logins
grep "Accepted password\|Accepted publickey" /var/log/auth.log

# Sudo usage
grep "sudo" /var/log/auth.log

# User account changes
grep "useradd\|userdel\|usermod\|passwd" /var/log/auth.log

# Last logins (reads /var/log/wtmp)
last -n 20

# Failed logins (reads /var/log/btmp)
lastb -n 20
```

## Log Locations by Distro

| Log | Debian/Ubuntu | RHEL/CentOS/Fedora | Arch |
|---|---|---|---|
| General syslog | `/var/log/syslog` | `/var/log/messages` | journal only |
| Auth log | `/var/log/auth.log` | `/var/log/secure` | journal only |
| Boot log | `/var/log/boot.log` | `/var/log/boot.log` | `journalctl -b` |
| Package log | `/var/log/dpkg.log` | `/var/log/yum.log` | `/var/log/pacman.log` |

Modern Arch Linux uses the journal exclusively — no `/var/log/syslog`. Always use `journalctl`.

## Journal Persistence — Is It Saved Across Reboots?

```bash
# Check if journal persists across reboots
ls /var/log/journal/    # if this directory exists, it's persistent

# Enable persistent journal
mkdir -p /var/log/journal
systemd-tmpfiles --create --prefix /var/log/journal
# or edit /etc/systemd/journald.conf:
# Storage=persistent
```

Without persistent storage, journal is lost on reboot and only lives in `/run/log/journal/`.
