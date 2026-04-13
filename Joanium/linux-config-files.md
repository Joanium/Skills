---
name: Linux Configuration Files (/etc and Beyond)
trigger: linux config files, /etc directory, linux configuration, linux settings files, linux etc, edit linux config, sshd_config, fstab, hosts file linux, linux network config, linux system config, linux config locations, where is config linux
description: Know the purpose of every important configuration file on Linux — in /etc/ and elsewhere — what each file controls, its format, and how to safely edit it. Use when configuring services, troubleshooting, hardening a server, or setting up a new system.
---

Linux configuration is almost entirely plain text files in `/etc/`. Knowing which file controls what — and the right way to edit it — is foundational to Linux administration.

## /etc/ — The Configuration Directory

`/etc/` stands for "et cetera" (historically) but is now treated as "Editable Text Configuration." Every file here is plain text, human-readable, and editable with any text editor.

**Golden rule:** Always backup before editing:
```bash
cp /etc/sshd/sshd_config /etc/ssh/sshd_config.bak.$(date +%Y%m%d)
```

## Network Configuration

### /etc/hosts

```
127.0.0.1   localhost
127.0.1.1   myhostname
192.168.1.50  fileserver fileserver.local
```

- Maps hostnames to IPs locally — checked before DNS
- Add entries to block domains (point to 0.0.0.0) or resolve internal hostnames
- Editing incorrectly can break all hostname resolution
- Format: `IP  hostname  [aliases...]`

### /etc/hostname

Single line: just the machine's hostname.
```
myserver
```
Change it: `hostnamectl set-hostname newname` (updates this file and the running system)

### /etc/resolv.conf

DNS configuration — which servers to query:
```
nameserver 8.8.8.8
nameserver 8.8.4.4
search example.local
options ndots:5
```

⚠️ On modern distros with `systemd-resolved`, this file is a symlink to a generated file. Edit via `resolvectl` or `/etc/systemd/resolved.conf` instead.

### /etc/nsswitch.conf

Defines the order of name resolution sources for different database types:
```
hosts:      files dns myhostname
passwd:     files systemd
shadow:     files
group:      files systemd
```
`files` = check `/etc/hosts` (or `/etc/passwd` etc.) first, then `dns` etc.

### Network Interface Config (Distro-Specific)

```bash
# Debian/Ubuntu (older) — /etc/network/interfaces
auto eth0
iface eth0 inet static
    address 192.168.1.100
    netmask 255.255.255.0
    gateway 192.168.1.1

# Ubuntu 18+ — Netplan: /etc/netplan/*.yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true

# RHEL/CentOS — /etc/sysconfig/network-scripts/ifcfg-eth0
TYPE=Ethernet
BOOTPROTO=dhcp
NAME=eth0
ONBOOT=yes

# NetworkManager — /etc/NetworkManager/system-connections/*.nmconnection
```

## User and Group Management

### /etc/passwd

User account database (readable by all — no passwords stored here):
```
username:x:UID:GID:comment:home:shell
root:x:0:0:root:/root:/bin/bash
alice:x:1000:1000:Alice Smith:/home/alice:/bin/bash
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
```

Fields: name | password placeholder | UID | GID | GECOS/comment | home dir | login shell

`/usr/sbin/nologin` or `/bin/false` as shell = service account that cannot log in interactively.

### /etc/shadow

Hashed passwords and account aging (readable by root only — permissions must be 640 or 000):
```
alice:$6$salt$hashedpassword:18000:0:99999:7:::
```
Fields: name | hash | last change | min age | max age | warn days | inactive | expire | reserved

**Security:** If this file is world-readable, offline password cracking is possible.

### /etc/group

Group definitions:
```
sudo:x:27:alice,bob
developers:x:1001:alice,carol
```
Format: groupname | password | GID | member list

### /etc/sudoers

Controls `sudo` access. **ALWAYS edit with `visudo`** — it validates syntax before saving:
```bash
visudo              # opens /etc/sudoers safely
visudo -f /etc/sudoers.d/alice   # edit a drop-in file
```

Drop-in files: `/etc/sudoers.d/` — add files here instead of editing the main file:
```
# /etc/sudoers.d/alice
alice ALL=(ALL:ALL) ALL           # alice can sudo anything
bob   ALL=(ALL) NOPASSWD: /usr/bin/apt   # bob can run apt without password
```

## SSH

### /etc/ssh/sshd_config — Server Configuration

Critical settings:
```
Port 22                         # change to non-standard port to reduce noise
PermitRootLogin no              # ALWAYS set this to no in production
PasswordAuthentication no       # use keys only (requires key setup first!)
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
MaxAuthTries 3
AllowUsers alice bob            # whitelist specific users
X11Forwarding no                # disable if not needed
```

After editing: `systemctl restart sshd` (validate with `sshd -t` first)

### ~/.ssh/authorized_keys

Public keys allowed to log in as this user. One key per line:
```
ssh-ed25519 AAAA... alice@laptop
ssh-rsa AAAA... backup-system
```

Permissions must be exact or SSH will refuse:
```bash
chmod 700 ~/.ssh/
chmod 600 ~/.ssh/authorized_keys
```

## Boot and Mount

### /etc/fstab — Filesystem Mount Table

Defines what to mount at boot:
```
# Device/UUID       Mountpoint   Filesystem  Options          Dump  Pass
UUID=abc-123        /            ext4        errors=remount-ro 0    1
UUID=def-456        /home        ext4        defaults          0    2
UUID=ghi-789        swap         swap        sw                0    0
//server/share      /mnt/nas     cifs        credentials=/etc/samba/creds,uid=1000 0 0
tmpfs               /tmp         tmpfs       defaults,size=1G  0    0
```

Pass values: `0`=don't fsck, `1`=fsck first (root only), `2`=fsck after root

**⚠️ Wrong entries here can prevent booting.** Test with `mount -a` before rebooting.

### /etc/crypttab — Encrypted Volume Setup

Maps encrypted devices to be unlocked at boot.

## System Behavior

### /etc/environment

System-wide environment variables, parsed by PAM for all sessions:
```
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
JAVA_HOME="/usr/lib/jvm/java-17-openjdk"
LANG="en_US.UTF-8"
```

### /etc/profile and /etc/profile.d/

Shell startup scripts run for login shells. Drop custom scripts in `/etc/profile.d/`:
```bash
# /etc/profile.d/my-vars.sh
export MY_APP_ENV="production"
export GOPATH="/usr/local/go"
```

### /etc/sysctl.conf — Kernel Parameters

Runtime kernel tuning, applied at boot:
```
net.ipv4.ip_forward = 1           # enable IP routing (needed for VMs/containers)
net.ipv4.tcp_syncookies = 1       # SYN flood protection
vm.swappiness = 10                # prefer RAM over swap
fs.file-max = 100000              # max open file descriptors system-wide
net.core.somaxconn = 65535        # max connection queue for listening sockets
```

Apply without rebooting: `sysctl -p`

### /etc/security/limits.conf — Resource Limits

Per-user resource limits (used by PAM):
```
*    soft nofile 65536    # soft limit on open files for all users
*    hard nofile 65536    # hard limit
alice hard nproc 1000     # alice can have at most 1000 processes
```

### /etc/timezone and /etc/localtime

```bash
cat /etc/timezone               # e.g., "Asia/Kolkata"
ls -la /etc/localtime           # symlink to /usr/share/zoneinfo/...
timedatectl set-timezone Asia/Kolkata   # correct way to change
```

## Service-Specific Configs

| Service | Primary Config |
|---|---|
| Nginx | `/etc/nginx/nginx.conf`, `/etc/nginx/sites-enabled/` |
| Apache | `/etc/apache2/apache2.conf`, `/etc/apache2/sites-enabled/` |
| MySQL/MariaDB | `/etc/mysql/my.cnf`, `/etc/mysql/mysql.conf.d/` |
| PostgreSQL | `/etc/postgresql/<ver>/main/postgresql.conf`, `pg_hba.conf` |
| Redis | `/etc/redis/redis.conf` |
| Docker | `/etc/docker/daemon.json` |
| UFW firewall | `/etc/ufw/` |
| iptables | `/etc/iptables/rules.v4`, `/etc/iptables/rules.v6` |
| Fail2ban | `/etc/fail2ban/jail.conf`, `/etc/fail2ban/jail.local` |
| logrotate | `/etc/logrotate.conf`, `/etc/logrotate.d/` |
| NTP/chrony | `/etc/chrony/chrony.conf`, `/etc/ntp.conf` |
| PAM | `/etc/pam.d/` |
| systemd | `/etc/systemd/system/`, `/etc/systemd/journald.conf` |

## Safe Editing Practices

```bash
# 1. Always backup first
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak

# 2. Test config before reloading service
nginx -t                    # nginx syntax check
sshd -t                     # sshd syntax check
apache2ctl configtest        # apache syntax check

# 3. Use systemctl reload instead of restart when possible
systemctl reload nginx      # graceful — doesn't drop connections
systemctl restart nginx     # hard restart — drops connections

# 4. Use `sudoedit` or `sudo -e` to safely edit as root
sudoedit /etc/hosts         # opens editor as your user, saves as root safely

# 5. Check for syntax errors in shell scripts
bash -n /etc/profile.d/myscript.sh
```
