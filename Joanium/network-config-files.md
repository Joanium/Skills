---
name: Network Configuration Files & Locations
trigger: network config linux, hosts file, resolv.conf, network settings file, where is DNS config, edit hosts file, network interface config, /etc/network, netplan, nmcli, windows network config, mac network config, firewall config, iptables config, how to configure network linux
description: Know where network settings are stored across Linux, macOS, and Windows — hosts files, DNS config, interface config, firewall rules, and proxy settings. Use when configuring networking, troubleshooting connectivity, managing DNS, or auditing network settings.
---

Network configuration is spread across multiple files and tools depending on OS and distribution. Knowing the canonical location for each setting prevents hunting through the wrong place.

## Universal Files (All UNIX-like Systems)

### /etc/hosts — Local DNS Override

Present on Linux, macOS, and (a version of) Windows. Checked **before** DNS by default.

```
127.0.0.1       localhost
127.0.1.1       myhostname.local myhostname
::1             localhost ip6-localhost ip6-loopback

# Custom entries
192.168.1.10    nas nas.local fileserver
10.0.0.50       dbserver.internal

# Block a domain (point to nothing)
0.0.0.0         ads.example.com
0.0.0.0         tracker.badsite.com
```

| OS | Location |
|---|---|
| Linux | `/etc/hosts` |
| macOS | `/private/etc/hosts` (symlinked as `/etc/hosts`) |
| Windows | `C:\Windows\System32\drivers\etc\hosts` |

Edit with root/admin — after saving, changes take effect immediately (no restart needed).

### /etc/resolv.conf — DNS Server Config (Linux/macOS)

Specifies which DNS servers to query:
```
nameserver 1.1.1.1
nameserver 1.0.0.1
search example.local corp.internal
options ndots:5 timeout:2 attempts:3
```

| Directive | Meaning |
|---|---|
| `nameserver` | DNS server IP (up to 3) |
| `search` | Domain suffixes to try for short names |
| `domain` | Default domain (single entry, older convention) |
| `options ndots:N` | Dots before treating as FQDN |

⚠️ **On modern Linux:** This file is often managed by `systemd-resolved` or `NetworkManager` and will be overwritten on reboot. Edit the real config instead:

```bash
# Check if it's managed
ls -la /etc/resolv.conf     # if it's a symlink → managed by systemd-resolved

# systemd-resolved config
/etc/systemd/resolved.conf
resolvectl status            # show current DNS settings
resolvectl dns eth0 1.1.1.1  # set DNS for interface

# NetworkManager config
/etc/NetworkManager/NetworkManager.conf
/etc/NetworkManager/system-connections/   # per-connection configs
```

### /etc/nsswitch.conf — Resolution Order

Controls which sources are checked first for each type of lookup:
```
hosts:      files mdns4_minimal [NOTFOUND=return] dns
# → Check /etc/hosts first, then mDNS, then DNS servers
```

---

## Linux Network Interface Configuration

Varies by distribution and version:

### Ubuntu/Debian 18+ — Netplan

```yaml
# /etc/netplan/01-network-manager-all.yaml
# or /etc/netplan/00-installer-config.yaml
network:
  version: 2
  renderer: networkd    # or: NetworkManager
  ethernets:
    eth0:
      dhcp4: true
    eth1:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1, 8.8.8.8]
  wifis:
    wlan0:
      dhcp4: true
      access-points:
        "MySSID":
          password: "wifipassword"
```

```bash
netplan apply                # apply config changes
netplan try                  # apply with 2min rollback safety
netplan generate             # generate backend configs without applying
```

### RHEL/CentOS/Fedora — ifcfg Files or NetworkManager

```bash
# Legacy ifcfg (RHEL 7/8)
# /etc/sysconfig/network-scripts/ifcfg-eth0
TYPE=Ethernet
BOOTPROTO=static
IPADDR=192.168.1.100
NETMASK=255.255.255.0
GATEWAY=192.168.1.1
DNS1=1.1.1.1
DNS2=8.8.8.8
ONBOOT=yes
NAME=eth0

# Modern nmcli (all RHEL versions, Fedora)
nmcli connection show
nmcli connection add type ethernet ifname eth0 con-name myconn
nmcli connection modify myconn ipv4.addresses 192.168.1.100/24
nmcli connection modify myconn ipv4.gateway 192.168.1.1
nmcli connection modify myconn ipv4.method manual
nmcli connection up myconn
```

### Debian (older) — /etc/network/interfaces

```
# /etc/network/interfaces
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet static
    address 192.168.1.100
    netmask 255.255.255.0
    gateway 192.168.1.1
    dns-nameservers 1.1.1.1 8.8.8.8

auto eth1
iface eth1 inet dhcp
```

```bash
ifup eth0     # bring interface up
ifdown eth0   # bring interface down
```

## Linux Firewall Config Files

### iptables

```bash
# Rules are runtime only — persist via:
/etc/iptables/rules.v4          # Debian/Ubuntu (iptables-persistent)
/etc/iptables/rules.v6          # IPv6 rules
/etc/sysconfig/iptables         # RHEL/CentOS
/etc/sysconfig/ip6tables        # RHEL/CentOS IPv6

# Save current rules
iptables-save > /etc/iptables/rules.v4

# Restore rules from file
iptables-restore < /etc/iptables/rules.v4
```

### UFW (Uncomplicated Firewall — Ubuntu)

```bash
/etc/ufw/ufw.conf               # main UFW config (enable/disable)
/etc/ufw/before.rules           # rules applied before UFW's own rules
/etc/ufw/after.rules            # rules applied after
/etc/ufw/user.rules             # UFW's generated rules (don't edit manually)
/etc/ufw/applications.d/        # app profile definitions

ufw status verbose
ufw allow 22/tcp
ufw deny from 192.168.1.50
```

### nftables (Modern Replacement for iptables)

```bash
/etc/nftables.conf              # main ruleset file
systemctl enable nftables
nft list ruleset
```

### firewalld (RHEL/Fedora/CentOS)

```bash
/etc/firewalld/                 # config files
/etc/firewalld/firewalld.conf   # main config
/etc/firewalld/zones/           # zone definitions
/usr/lib/firewalld/zones/       # default zone templates

firewall-cmd --list-all
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

## SSH Config Files

```bash
# Server config
/etc/ssh/sshd_config            # SSH server settings
/etc/ssh/sshd_config.d/*.conf   # Drop-in configs (Ubuntu 22+)

# Client config (user-level)
~/.ssh/config                   # per-user SSH client settings
/etc/ssh/ssh_config             # system-wide SSH client settings

# Key files
~/.ssh/id_rsa / id_ed25519      # private key (600 permissions required)
~/.ssh/id_rsa.pub               # public key
~/.ssh/authorized_keys          # public keys allowed to log in as this user
~/.ssh/known_hosts              # verified host fingerprints

# System host keys
/etc/ssh/ssh_host_*_key         # server's private keys (owned root, 600)
/etc/ssh/ssh_host_*_key.pub     # server's public keys
```

## Proxy Configuration

### Linux/macOS — Environment Variables

```bash
# Set proxy (session-level)
export http_proxy="http://proxy.corp:3128"
export https_proxy="http://proxy.corp:3128"
export no_proxy="localhost,127.0.0.1,.corp.internal"

# Persist in /etc/environment for system-wide:
http_proxy="http://proxy.corp:3128"
https_proxy="http://proxy.corp:3128"
no_proxy="localhost,127.0.0.1"

# apt uses its own proxy config:
/etc/apt/apt.conf.d/95proxies   # or 01proxy
# Contents:
Acquire::http::Proxy "http://proxy.corp:3128";
```

### Windows Proxy Settings

```powershell
# View WinHTTP proxy (used by services and apps)
netsh winhttp show proxy

# Set WinHTTP proxy
netsh winhttp set proxy proxy.corp:3128

# Import from IE/browser settings
netsh winhttp import proxy source=ie

# Registry (user proxy — browser/app level)
HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings
  ProxyEnable = 1
  ProxyServer = proxy.corp:3128
  ProxyOverride = localhost;*.corp.internal
```

## macOS Network Config

```bash
# Network config via networksetup
networksetup -listallnetworkservices     # list network interfaces
networksetup -getinfo Ethernet           # IP info for interface
networksetup -setdhcp Ethernet           # set to DHCP
networksetup -setmanual Ethernet 192.168.1.100 255.255.255.0 192.168.1.1
networksetup -setdnsservers Ethernet 1.1.1.1 8.8.8.8

# Config stored at:
/Library/Preferences/SystemConfiguration/
  preferences.plist               # network interface config
  NetworkInterfaces.plist         # hardware interface list

# DNS resolver configs (per-domain):
/etc/resolver/                    # drop files here to override DNS per domain
# e.g., /etc/resolver/corp.internal  with:
# nameserver 10.0.0.1
```

## Windows Network Config Locations

```
C:\Windows\System32\drivers\etc\hosts          → Hosts file
C:\Windows\System32\drivers\etc\lmhosts.sam    → NetBIOS name resolution template

# Per-interface config stored in registry:
HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\{GUID}\
  IPAddress, SubnetMask, DefaultGateway, NameServer

# Managed via:
netsh interface ip show config
netsh interface ip set address "Ethernet" static 192.168.1.100 255.255.255.0 192.168.1.1
netsh interface ip set dns "Ethernet" static 1.1.1.1

# PowerShell (modern)
Get-NetIPAddress
Get-NetAdapter
Set-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.1.100 -PrefixLength 24
New-NetRoute -DestinationPrefix 0.0.0.0/0 -NextHop 192.168.1.1

# Windows Firewall rules
netsh advfirewall firewall show rule name=all
Get-NetFirewallRule | Where-Object {$_.Enabled -eq 'True'} | Select-Object DisplayName
```
