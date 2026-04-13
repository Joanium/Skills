---
name: Linux File Permissions & Ownership
trigger: linux permissions, chmod, chown, file permissions linux, permission denied linux, rwx, octal permissions, setuid, setgid, sticky bit, linux ownership, umask, ACL linux, dangerous permissions linux, world writable
description: Understand and manage Linux file permissions and ownership — read/write/execute bits, octal notation, special bits (setuid/setgid/sticky), ownership, umask, and ACLs. Use when fixing "Permission denied" errors, auditing security, writing scripts, or configuring shared directories.
---

Linux permissions control who can read, write, and execute every file and directory. Getting them wrong causes either broken access or serious security vulnerabilities.

## Permission Basics

Every file has three permission sets and two ownership properties:

```
-rwxr-xr--  2  alice  developers  4096  Apr 10 12:00  script.sh
│└──┴──┴──  │  │────  │─────────  │───  │──────────  │────────
│ u   g  o  │  owner  group       size  modified     filename
│           └─ hard links
└─ type: - (file), d (directory), l (symlink), c (char device), b (block device)
```

### Permission Bits

| Symbol | Meaning for files | Meaning for directories |
|---|---|---|
| `r` (read, 4) | Read file contents | List directory contents (`ls`) |
| `w` (write, 2) | Modify file contents | Create/delete/rename files inside |
| `x` (execute, 1) | Run as program | Enter directory (`cd`) |
| `-` | Permission not granted | Permission not granted |

Three sets apply in order — first match wins:
1. **u** (user/owner) — the file's owner
2. **g** (group) — members of the file's group
3. **o** (others) — everyone else

## Octal Notation

Permissions are represented as three octal digits (one per set):

```
r=4, w=2, x=1

755  →  rwxr-xr-x   owner: rwx (7), group: r-x (5), others: r-x (5)
644  →  rw-r--r--   owner: rw- (6), group: r-- (4), others: r-- (4)
600  →  rw-------   owner: rw- (6), group: --- (0), others: --- (0)
777  →  rwxrwxrwx   everyone full access — DANGEROUS for most files
```

## chmod — Changing Permissions

```bash
# Octal (absolute) mode
chmod 755 script.sh       # rwxr-xr-x
chmod 644 config.conf     # rw-r--r--
chmod 600 ~/.ssh/id_rsa   # rw------- (SSH private key MUST be this)
chmod 700 ~/.ssh/          # rwx------ (SSH directory)

# Symbolic mode
chmod u+x script.sh       # add execute for owner
chmod go-w file.txt       # remove write for group and others
chmod a+r file.txt        # add read for all (u+g+o)
chmod u=rwx,go=rx dir/    # set explicitly

# Recursive
chmod -R 755 /var/www/html/
```

## chown — Changing Ownership

```bash
chown alice file.txt              # change owner to alice
chown alice:developers file.txt   # change owner and group
chown :developers file.txt        # change group only (same as chgrp)
chown -R www-data:www-data /var/www/  # recursive
```

## Common Permission Patterns and What They Mean

| Permission | Octal | Typical use |
|---|---|---|
| `rwx------` | 700 | Private scripts, home dir, SSH keys |
| `rw-------` | 600 | Private files, SSH private keys, secrets |
| `rwxr-xr-x` | 755 | Public scripts, directories, binaries |
| `rw-r--r--` | 644 | Public config files, web content |
| `rw-rw-r--` | 664 | Shared files within a team |
| `rwxrwxr-x` | 775 | Shared directories within a team |
| `rwxrwxrwx` | 777 | ⚠️ Avoid — world-writable is a security risk |
| `rwsrwsr-x` | 6775 | Setuid + setgid (see below) |

## Special Permission Bits — Setuid, Setgid, Sticky

There is a fourth octal digit (prefix) for special bits:

```
4000 = setuid
2000 = setgid
1000 = sticky bit
```

### Setuid (4 prefix — SUID)

When set on an **executable**, it runs with the **file owner's privileges** instead of the caller's:

```bash
ls -la /usr/bin/passwd
-rwsr-xr-x  1  root  root  /usr/bin/passwd    # s = setuid set
```

`passwd` is owned by root and has setuid — so any user can run it and it temporarily runs as root to modify `/etc/shadow`. This is how non-root users change their own password.

**Security risk:** A setuid root binary with a vulnerability = instant privilege escalation.

```bash
# Find all setuid files — audit these
find / -perm -4000 -type f 2>/dev/null

# Set setuid
chmod u+s /path/to/binary    # or chmod 4755
```

### Setgid (2 prefix — SGID)

**On executables:** Runs with the file's **group** privileges.

**On directories:** New files created inside **inherit the directory's group** (instead of the creator's primary group). Useful for shared project directories.

```bash
chmod g+s /shared/projects/    # new files get 'projects' group
chmod 2775 /shared/projects/
```

### Sticky Bit (1 prefix)

**On directories:** Users can only delete or rename **their own files**, even if they have write access to the directory. `/tmp` uses this.

```bash
ls -la / | grep tmp
drwxrwxrwt  ...  tmp    # t = sticky bit set

chmod +t /shared/tmp/   # or chmod 1777
```

**Without sticky bit on /tmp:** User A could delete User B's temp files. With it, only the owner or root can delete each file.

## umask — Default Permission Mask

`umask` defines what permissions are **removed** from newly created files:

```bash
umask          # show current mask (typically 0022 or 0002)
umask 0022     # set mask
```

How it works:
```
New file base permissions:  666 (rw-rw-rw-)
umask:                      022
Result:                     644 (rw-r--r--)

New dir base permissions:   777 (rwxrwxrwx)
umask:                      022
Result:                     755 (rwxr-xr-x)
```

| umask | New files | New dirs | Typical for |
|---|---|---|---|
| 0022 | 644 | 755 | Single-user system |
| 0002 | 664 | 775 | Shared group workspace |
| 0077 | 600 | 700 | High-security / private use |

Set persistently in `~/.bashrc` or `/etc/profile`.

## Dangerous Permission Configurations

```bash
# World-writable files — anyone can modify
find / -perm -0002 -type f 2>/dev/null

# World-writable directories without sticky bit — files can be deleted by others
find / -perm -0002 -type d ! -perm -1000 2>/dev/null

# Setuid root binaries — audit carefully
find / -perm -4000 -user root -type f 2>/dev/null

# Files owned by no one (orphaned after user deletion)
find / -nouser -o -nogroup 2>/dev/null

# World-writable .sh or .py scripts that are run by root (cron, services)
# These are local privilege escalation vectors!
```

## ACLs — Access Control Lists (Extended Permissions)

For fine-grained control beyond owner/group/other:

```bash
# View ACL
getfacl file.txt

# Grant alice read+write even though she's not the owner/group
setfacl -m u:alice:rw file.txt

# Grant developers group read-only
setfacl -m g:developers:r file.txt

# Remove ACL for bob
setfacl -x u:bob file.txt

# Remove all ACLs
setfacl -b file.txt
```

`ls -la` shows a `+` at end of permissions when an ACL exists: `-rw-r--r--+`

## Quick Security Audit Checklist

```bash
# 1. World-writable files outside /tmp
find / -path /proc -prune -o -perm -0002 -type f -print 2>/dev/null

# 2. Setuid/setgid binaries
find / -perm /6000 -type f 2>/dev/null

# 3. Files writable by everyone in /etc
find /etc -perm -0002 2>/dev/null

# 4. SSH keys with wrong permissions (must be 600)
ls -la ~/.ssh/

# 5. Config files with secrets that are world-readable
ls -la .env .env.* *.conf *.key *.pem
```

## SSH Key Permissions — Must Be Exact

SSH is strict about permissions and will refuse to use keys with wrong permissions:

```bash
chmod 700 ~/.ssh/
chmod 600 ~/.ssh/id_rsa         # private key
chmod 644 ~/.ssh/id_rsa.pub     # public key
chmod 644 ~/.ssh/authorized_keys
chmod 644 ~/.ssh/known_hosts
chmod 600 ~/.ssh/config
```
