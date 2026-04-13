---
name: User Directories & Home Folder Structure
trigger: home directory, user profile, where are user files, home folder linux, user folder windows, profile folder, ~/.config, where does X store its files, user data location, XDG directories, application data user, per user config, user specific files
description: Know where user-specific files, configuration, and application data live on Linux, macOS, and Windows — home directories, XDG paths, AppData structure, dotfiles, and per-app storage locations. Use when managing user data, setting up new systems, writing cross-platform scripts, or troubleshooting per-user issues.
---

Applications store user data in specific, standardized locations. Knowing where each type of data lives — settings, caches, documents, runtime files — is essential for backup, troubleshooting, and scripting.

## Linux — Home Directory Structure

```
~/ = /home/<username>/     (root's home is /root/ — an exception)

~/
├── .bashrc                → Bash interactive shell config (runs every terminal open)
├── .bash_profile          → Bash login shell config (runs on SSH login, console login)
├── .profile               → POSIX login shell config (used by sh, dash; fallback for bash)
├── .zshrc                 → Zsh interactive config
├── .zprofile              → Zsh login config
├── .gitconfig             → Git user settings
├── .ssh/                  → SSH keys and config (must be chmod 700)
│   ├── id_ed25519         → Private key (must be chmod 600)
│   ├── id_ed25519.pub     → Public key
│   ├── authorized_keys    → Keys allowed to SSH in as you
│   ├── known_hosts        → Verified host fingerprints
│   └── config             → SSH client config (aliases, options per host)
├── .gnupg/                → GPG keys and config (chmod 700)
├── .config/               → XDG config dir — app-specific config
│   ├── git/config         → Git config (modern location)
│   ├── nvim/              → Neovim config
│   ├── htop/              → htop settings
│   └── autostart/         → Desktop session autostart .desktop files
├── .local/
│   ├── share/             → XDG data dir — app data, installed fonts, icons
│   │   ├── applications/  → User-installed .desktop files
│   │   ├── fonts/         → User-installed fonts
│   │   └── <app>/         → Per-app data
│   └── bin/               → User-installed binaries (add to PATH)
├── .cache/                → XDG cache dir — regenerable data (safe to delete)
├── Desktop/
├── Documents/
├── Downloads/
├── Music/
├── Pictures/
└── Videos/
```

## XDG Base Directory Specification (Linux Standard)

The XDG spec standardizes where apps store their data. Apps that follow it use these:

| Variable | Default | Purpose |
|---|---|---|
| `XDG_CONFIG_HOME` | `~/.config` | User configuration |
| `XDG_DATA_HOME` | `~/.local/share` | User data |
| `XDG_CACHE_HOME` | `~/.cache` | Cached data (safe to delete) |
| `XDG_RUNTIME_DIR` | `/run/user/<UID>/` | Runtime files (sockets, PIDs) — cleared on logout |
| `XDG_STATE_HOME` | `~/.local/state` | App state (logs, history) |

```bash
# Check current XDG paths
echo $XDG_CONFIG_HOME     # usually empty (means default ~/.config)
echo $XDG_DATA_HOME

# Override in ~/.bashrc or ~/.profile:
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_DATA_HOME="$HOME/.local/share"
export XDG_CACHE_HOME="$HOME/.cache"
```

## Common Application Data Locations (Linux)

```bash
# Development tools
~/.config/Code/            → VS Code settings
~/.vscode/                 → VS Code extensions (some versions)
~/.config/nvim/            → Neovim
~/.vim/                    → Vim
~/.tmux.conf               → tmux config
~/.config/tmux/            → tmux (modern)

# Shells
~/.bash_history            → Bash command history
~/.zsh_history             → Zsh command history
~/.config/fish/            → Fish shell config and history

# Version control
~/.gitconfig               → Git global config
~/.config/git/config       → Git global config (XDG-compliant path)
~/.config/gh/              → GitHub CLI config

# Runtimes and package managers
~/.npm/                    → npm cache (older)
~/.cache/npm/              → npm cache (newer)
~/.cargo/                  → Rust toolchain and packages
~/.go/ or ~/go/            → Go workspace
~/.pyenv/                  → pyenv Python version manager
~/.nvm/                    → nvm Node.js version manager
~/.rbenv/                  → rbenv Ruby version manager
~/.local/share/virtualenv/ → Virtual environments (if using virtualenvwrapper)

# Desktop
~/.local/share/applications/   → User .desktop files (app shortcuts)
~/.config/autostart/           → Apps that launch at desktop login
~/.themes/ or ~/.local/share/themes/  → GTK themes
~/.icons/ or ~/.local/share/icons/    → Icon themes
```

## Linux — Dotfiles (Hidden Config Files)

Files starting with `.` are hidden from `ls` by default. These are your personal configs:

```bash
ls -la ~/          # show all files including hidden
ls -la ~/.config/  # show XDG config dir

# Common dotfiles to back up:
~/.bashrc ~/.bash_profile ~/.profile ~/.zshrc ~/.zprofile
~/.gitconfig ~/.gitignore_global
~/.ssh/config
~/.tmux.conf
~/.vimrc ~/.config/nvim/
~/.config/gh/
```

Tip: Keep dotfiles in a Git repo and symlink them with a tool like `chezmoi`, `stow`, or `yadm`.

---

## macOS — Home Directory Structure

```
~/ = /Users/<username>/

~/
├── .zshrc                 → Zsh config (macOS default shell since Catalina)
├── .zprofile              → Zsh login config
├── .bash_profile          → Bash (if using bash)
├── .ssh/                  → SSH keys (same as Linux — chmod 700)
├── .gitconfig             → Git config
├── .config/               → XDG-compatible config (many apps use this)
├── Library/               → Hidden by default — the main user data store
│   ├── Application Support/   → App data, databases, long-term storage
│   ├── Preferences/           → .plist config files for all apps
│   ├── Caches/                → Regenerable cache — safe to delete
│   ├── Logs/                  → Application logs
│   ├── Keychains/             → Keychain database — never manually edit
│   ├── LaunchAgents/          → Per-user auto-start agents
│   ├── Mail/                  → Apple Mail data
│   ├── Safari/                → Safari bookmarks, history
│   ├── Containers/            → Sandboxed app data (App Store apps)
│   ├── Group Containers/      → Data shared between apps from same developer
│   ├── Fonts/                 → Fonts installed for this user
│   └── Mobile Documents/      → iCloud Drive local cache
├── Desktop/
├── Documents/
├── Downloads/
├── Movies/
├── Music/
├── Pictures/
└── Public/                → Shared folder — other users on this Mac can read
```

### macOS Common Application Locations

```bash
~/Library/Application Support/Code/User/    → VS Code user settings
~/Library/Application Support/Google/Chrome/Default/  → Chrome profile
~/Library/Application Support/Slack/        → Slack data
~/Library/Preferences/com.apple.finder.plist  → Finder preferences
~/Library/Preferences/com.apple.dock.plist    → Dock preferences
~/Library/Containers/com.apple.mail/Data/Library/Mail/  → Mail (sandboxed)

# Show Library folder in Finder:
# Finder → Go menu → hold Option → Library appears
# Or: chflags nohidden ~/Library/
```

---

## Windows — User Profile Structure

```
C:\Users\<Username>\   (pointed to by %USERPROFILE%)

C:\Users\<Username>\
├── AppData\               → Hidden. Contains all per-user app data.
│   ├── Roaming\           → App settings that sync across machines (domain)
│   │   ├── Microsoft\     → Office, Windows shell, Outlook
│   │   ├── Code\User\     → VS Code settings
│   │   └── npm\           → Global npm modules (on PATH)
│   ├── Local\             → Machine-specific data. Larger, not synced.
│   │   ├── Temp\          → User temp files. Safe to clear.
│   │   ├── Google\Chrome\ → Chrome profile and cache
│   │   ├── Microsoft\     → Edge, Windows data
│   │   └── Programs\      → User-installed programs (no admin required)
│   └── LocalLow\          → Low-integrity sandbox data (browsers, PDF readers)
├── Desktop\
├── Documents\
├── Downloads\
├── Favorites\             → IE/Edge bookmarks
├── Links\
├── Music\
├── OneDrive\              → OneDrive synced folder (if enabled)
├── Pictures\
├── Saved Games\
├── Videos\
└── .gitconfig             → Git config (stored in user root on Windows)
```

### Windows Environment Variable Shortcuts

```powershell
# Open these in Explorer by typing in address bar:
%USERPROFILE%      → C:\Users\<Username>\
%APPDATA%          → AppData\Roaming\
%LOCALAPPDATA%     → AppData\Local\
%TEMP%             → AppData\Local\Temp\   (safe to clear)
shell:startup      → AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\
```

### Windows — Common App Data Locations

```
VS Code settings:       %APPDATA%\Code\User\settings.json
VS Code extensions:     %USERPROFILE%\.vscode\extensions\
Git config:             %USERPROFILE%\.gitconfig
SSH keys:               %USERPROFILE%\.ssh\
npm global:             %APPDATA%\npm\
npm cache:              %LOCALAPPDATA%\npm-cache\
Python pip packages:    %APPDATA%\Python\PythonXX\site-packages\
pip cache:              %LOCALAPPDATA%\pip\Cache\
Cargo (Rust):           %USERPROFILE%\.cargo\
Go workspace:           %USERPROFILE%\go\
PowerShell profile:     %USERPROFILE%\Documents\PowerShell\Microsoft.PowerShell_profile.ps1
Windows Terminal:       %LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_*\LocalState\settings.json
Chrome profile:         %LOCALAPPDATA%\Google\Chrome\User Data\Default\
Firefox profile:        %APPDATA%\Mozilla\Firefox\Profiles\
```

---

## Cross-Platform Quick Reference

| Data type | Linux | macOS | Windows |
|---|---|---|---|
| Shell config | `~/.bashrc` / `~/.zshrc` | `~/.zshrc` | PowerShell profile |
| App settings | `~/.config/<app>/` | `~/Library/Preferences/` | `%APPDATA%\<app>\` |
| App data | `~/.local/share/<app>/` | `~/Library/Application Support/` | `%APPDATA%\<app>\` |
| App cache | `~/.cache/<app>/` | `~/Library/Caches/<app>/` | `%LOCALAPPDATA%\<app>\` |
| Temp files | `/tmp/` | `/tmp/` or `$TMPDIR` | `%TEMP%` |
| SSH keys | `~/.ssh/` | `~/.ssh/` | `%USERPROFILE%\.ssh\` |
| Git config | `~/.gitconfig` | `~/.gitconfig` | `%USERPROFILE%\.gitconfig` |
| Downloads | `~/Downloads/` | `~/Downloads/` | `%USERPROFILE%\Downloads\` |
