---
name: macOS Filesystem & Directory Structure
trigger: macos directories, macos filesystem, macos folder structure, mac folders, what is /Library on mac, macos path, application support mac, macos hidden folders, mac system directories, where is X on mac, macos directory layout
description: Understand macOS directory structure — system, user, and application directories, where configuration lives, what is protected by SIP, and where to safely store data. Use when troubleshooting apps, writing scripts, managing preferences, or diagnosing permission issues.
---

macOS is Unix-based (Darwin/XNU kernel) and follows a modified version of the BSD filesystem hierarchy, layered with Apple-specific conventions. Understanding both layers is essential.

## Top-Level Directory Map

```
/
├── Applications/        → Installed apps (GUI apps as .app bundles). User installs go here too.
├── Library/             → System-wide configuration, frameworks, caches, preferences
├── System/              → macOS OS files. Protected by SIP — cannot be modified.
│   └── Library/         → Apple frameworks, extensions, services bundled with macOS
├── Users/               → All user home directories
│   ├── Shared/          → Files shared between all local users
│   └── <username>/      → Your home directory
├── Volumes/             → Mount point for all disks (external drives, DMGs, network shares)
├── private/             → Real location of /tmp, /var, /etc (symlinked from root)
│   ├── etc/             → System config files (symlinked as /etc)
│   ├── tmp/             → Temporary files (symlinked as /tmp)
│   └── var/             → Variable runtime data (symlinked as /var)
├── etc/  → symlink to /private/etc
├── tmp/  → symlink to /private/tmp
├── var/  → symlink to /private/var
├── bin/             → Core Unix binaries (bash, ls, cp, cat)
├── sbin/            → System binaries (fsck, mount, reboot)
├── usr/             → Unix tools and libraries
│   ├── bin/         → User commands (python3, git via Xcode CLT, ssh, curl)
│   ├── lib/         → System libraries
│   ├── local/       → Homebrew installs here (on Intel Macs: /usr/local; Apple Silicon: /opt/homebrew)
│   └── share/       → Shared data, man pages
├── opt/             → On Apple Silicon: Homebrew installs to /opt/homebrew/
└── dev/             → Device files (like Linux)
```

## The Library Folder — Three Distinct Locations

This is the most important macOS-specific concept. There are THREE `Library` folders with different scopes:

| Location | Scope | What lives here |
|---|---|---|
| `/Library/` | System-wide (all users) | Launch daemons, system-wide prefs, fonts, frameworks for all users |
| `/System/Library/` | Apple OS only (SIP-protected) | Apple's own frameworks, extensions, services — DO NOT TOUCH |
| `~/Library/` | Current user only | Your app preferences, caches, application support data |

### ~/Library/ Subdirectory Breakdown (Your User Library)

```
~/Library/
├── Application Support/     → App data, databases, user files apps store long-term
│   ├── Google/Chrome/       → Chrome user profiles
│   ├── Code/                → VS Code extensions and settings
│   └── com.apple.sharedfilelist/  → Recent items, favorites
├── Preferences/             → .plist files — all app preferences
│   ├── com.apple.finder.plist    → Finder settings
│   └── com.apple.dock.plist      → Dock configuration
├── Caches/                  → Temporary cache data. Safe to delete (apps regenerate).
│   ├── com.apple.Safari/    → Safari cache
│   └── <BundleID>/          → Per-app cache
├── Logs/                    → Application and crash logs
├── Containers/              → Sandboxed app data (Mac App Store apps)
│   └── com.apple.<App>/Data/Library/  → Each sandboxed app has its own Library
├── Group Containers/        → Data shared between apps by the same developer (iCloud, iWork)
├── Keychains/               → Keychain database files (DO NOT manually edit)
├── Mail/                    → Apple Mail data — messages, attachments
├── Safari/                  → Safari bookmarks, history, reading list
├── LaunchAgents/            → Per-user launch agents (run when you log in)
├── Fonts/                   → Fonts installed for this user only
├── ColorPickers/            → Custom color pickers
└── Input Methods/           → Custom keyboard input methods
```

## System Integrity Protection (SIP) — Protected Paths

SIP (rootless mode, enabled by default) prevents modification of these paths — even as root:

```
/System/
/bin/
/sbin/
/usr/   (except /usr/local/)
```

You **cannot** modify these without disabling SIP (requires booting to Recovery Mode). This is intentional and protects against malware and accidental damage.

**Safe to modify even as regular user:**
- `/usr/local/` (Homebrew on Intel)
- `/opt/homebrew/` (Homebrew on Apple Silicon)
- `/Applications/` (with password)
- `~/Library/` (your user library)
- `/Library/` (with password for some locations)

## Homebrew — Where It Installs

Homebrew deliberately avoids SIP-protected paths:

```bash
# Intel Mac
/usr/local/bin/        → CLI tools
/usr/local/lib/        → Libraries
/usr/local/Cellar/     → Actual package files (symlinked into bin/lib)
/usr/local/Caskroom/   → GUI apps installed via Homebrew Cask

# Apple Silicon (M1/M2/M3/M4)
/opt/homebrew/bin/
/opt/homebrew/lib/
/opt/homebrew/Cellar/
/opt/homebrew/Caskroom/
```

Check which you have: `brew --prefix`

## Application Support vs Preferences vs Caches

| Folder | Data type | Delete safe? | Notes |
|---|---|---|---|
| `~/Library/Application Support/<App>/` | User data, databases, project files | ⚠️ No — data loss | Deleting may remove documents or history |
| `~/Library/Preferences/<bundle>.plist` | App settings | ✅ Yes — resets settings | App will regenerate with defaults |
| `~/Library/Caches/<App>/` | Regenerable cache | ✅ Yes | App will rebuild on next launch (may be slow) |
| `~/Library/Logs/` | Log files | ✅ Yes | Only needed for troubleshooting |
| `~/Library/Saved Application State/` | Window restore state | ✅ Yes | Apps reopen without restoring windows |

## Launch Agents and Launch Daemons — Auto-Start Locations

These are the macOS equivalent of Windows services and startup entries:

| Location | Who runs it | Runs as |
|---|---|---|
| `~/Library/LaunchAgents/` | Current user's agents | Current user |
| `/Library/LaunchAgents/` | System-wide user agents | Current user (at login) |
| `/Library/LaunchDaemons/` | System-wide daemons | root |
| `/System/Library/LaunchAgents/` | Apple's own agents (SIP-protected) | — |
| `/System/Library/LaunchDaemons/` | Apple's own daemons (SIP-protected) | root |

```bash
# List running launch agents/daemons
launchctl list

# Load a new agent
launchctl load ~/Library/LaunchAgents/com.me.myjob.plist

# Unload (stop) an agent
launchctl unload ~/Library/LaunchAgents/com.me.myjob.plist
```

## Where to Find Common Things

| What | Where |
|---|---|
| App preferences | `~/Library/Preferences/<bundle-id>.plist` |
| App data | `~/Library/Application Support/<AppName>/` |
| System hosts file | `/private/etc/hosts` (or `/etc/hosts` symlink) |
| DNS settings | `/private/etc/resolv.conf` |
| Network interfaces | System Preferences → Network, or `networksetup -listallnetworkservices` |
| Crash reports | `~/Library/Logs/DiagnosticReports/` |
| System crash reports | `/Library/Logs/DiagnosticReports/` |
| Shell config (zsh default) | `~/.zshrc`, `~/.zprofile` |
| SSH keys and config | `~/.ssh/` |
| Global npm packages | `/usr/local/lib/node_modules/` or `$(brew --prefix)/lib/node_modules/` |
| Keychain | `~/Library/Keychains/login.keychain-db` |
| macOS system logs | `log show`, `Console.app`, `/var/log/system.log` |

## Dangerous Paths

```
/System/Library/          → SIP-protected; modifying requires disabling SIP (bad idea)
~/Library/Keychains/      → Do not manually edit; corrupt keychain = lost passwords
~/Library/Mail/           → Contains all your emails; backup before touching
/private/etc/sudoers      → Corrupt this = lose all sudo access
/Volumes/Macintosh HD/    → When booted externally, this is the live system volume
```

## macOS Hidden Files and How to Show Them

```bash
# Show hidden files in Finder (toggle)
defaults write com.apple.finder AppleShowAllFiles TRUE; killall Finder

# List hidden files in terminal
ls -la ~

# Hidden by convention: files/folders starting with a dot
~/.zshrc    ~/.ssh/    ~/.gitconfig    ~/.config/
```

Files and folders starting with `.` are hidden by default. The `~/Library/` folder is also hidden from Finder by default — access it via **Go → Go to Folder → ~/Library** in Finder.
