---
name: Package Managers — All Operating Systems
trigger: package manager, apt, yum, dnf, brew, homebrew, winget, chocolatey, pacman, install package, update packages, remove package, how to install software linux, how to install software mac, how to install software windows, pip, npm, snap, flatpak
description: Use the right package manager commands on any OS — apt, dnf/yum, pacman, brew, winget, chocolatey, snap, flatpak. Know where packages install to, how to update the system, find packages, remove software, and manage package sources. Use when installing/removing software, scripting setup, or troubleshooting install failures.
---

Every OS has one (or several) package managers. Using the native package manager is almost always better than downloading installers manually — it handles dependencies, updates, and clean uninstalls.

## Linux — System Package Managers

### APT (Debian, Ubuntu, Mint, Raspberry Pi OS)

```bash
# Update package list (always do this before installing)
sudo apt update

# Upgrade installed packages
sudo apt upgrade               # upgrade packages (won't remove old ones)
sudo apt full-upgrade          # upgrade + handle dependency changes (may remove packages)
sudo apt dist-upgrade          # same as full-upgrade (older alias)

# Install
sudo apt install nginx
sudo apt install -y nginx git curl   # -y skips confirmation prompt
sudo apt install ./mypackage.deb     # install local .deb file

# Remove
sudo apt remove nginx          # remove binary, keep config files
sudo apt purge nginx           # remove binary AND config files
sudo apt autoremove            # remove unused dependency packages

# Search
apt search "web server"
apt show nginx                 # show detailed package info

# List
apt list --installed           # all installed packages
apt list --installed | grep nginx

# Fix broken installs
sudo apt --fix-broken install
sudo dpkg --configure -a       # complete interrupted installs

# Where packages install:
# Binaries:    /usr/bin/, /usr/sbin/
# Libraries:   /usr/lib/
# Config:      /etc/<package>/
# Data:        /usr/share/<package>/
# Cache:       /var/cache/apt/archives/
# Package DB:  /var/lib/dpkg/
```

**Sources:** `/etc/apt/sources.list` and `/etc/apt/sources.list.d/*.list`

### DNF (Fedora, RHEL 8+, CentOS Stream 8+)

```bash
sudo dnf update                # update all packages
sudo dnf install nginx
sudo dnf install -y nginx
sudo dnf remove nginx
sudo dnf autoremove            # remove orphaned packages
dnf search "web server"
dnf info nginx
dnf list installed
dnf history                    # transaction history
dnf history undo <ID>          # undo a transaction

# Sources: /etc/yum.repos.d/*.repo
# Package DB: /var/lib/dnf/
```

### YUM (RHEL 7, CentOS 7, older RHEL)

```bash
sudo yum update
sudo yum install nginx
sudo yum remove nginx
yum search nginx
yum info nginx
yum list installed
sudo yum-complete-transaction  # complete interrupted transactions

# Sources: /etc/yum.repos.d/*.repo
```

### Pacman (Arch Linux, Manjaro, EndeavourOS)

```bash
sudo pacman -Syu               # sync + upgrade all (do this before installing)
sudo pacman -S nginx           # install
sudo pacman -Rs nginx          # remove + unused deps
sudo pacman -Rns nginx         # remove + deps + config files
pacman -Ss "web server"        # search
pacman -Si nginx               # show info
pacman -Q                      # list installed
pacman -Qe                     # list explicitly installed (not pulled as dep)
pacman -Qdt                    # list orphaned packages (safe to remove)
sudo pacman -Rns $(pacman -Qdtq)  # remove all orphans

# Sources: /etc/pacman.conf, /etc/pacman.d/mirrorlist
# Cache: /var/cache/pacman/pkg/
```

### Snap (Ubuntu, many distros)

```bash
snap find nginx
snap install node --channel=20/stable
snap install code --classic    # --classic allows full system access
snap remove node
snap list                      # list installed snaps
snap refresh                   # update all snaps
snap info node

# Snap installs to: /snap/<package>/
# Data stored at: /var/snap/<package>/  and  ~/snap/<package>/
```

### Flatpak (Universal, desktop apps)

```bash
flatpak install flathub com.spotify.Client
flatpak run com.spotify.Client
flatpak uninstall com.spotify.Client
flatpak update
flatpak list
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo

# Installs to: /var/lib/flatpak/  (system) or ~/.local/share/flatpak/  (user)
```

---

## macOS — Homebrew

The de facto standard package manager for macOS.

```bash
# Installation:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Location: /opt/homebrew/ (Apple Silicon) or /usr/local/ (Intel)

# Update Homebrew itself
brew update

# Upgrade installed packages
brew upgrade                   # upgrade all
brew upgrade nginx             # upgrade specific

# Install CLI tools (formulae)
brew install nginx
brew install git node python@3.12

# Install GUI apps (casks)
brew install --cask firefox
brew install --cask visual-studio-code
brew install --cask docker

# Remove
brew uninstall nginx
brew uninstall --cask firefox

# Search
brew search nginx
brew info nginx

# List installed
brew list                      # all installed formulae
brew list --cask               # installed casks

# Maintenance
brew cleanup                   # remove old versions
brew doctor                    # diagnose issues
brew autoremove                # remove unused dependencies

# Where things install:
# Binaries:    $(brew --prefix)/bin/
# Libraries:   $(brew --prefix)/lib/
# Casks:       $(brew --prefix)/Caskroom/
# Cellar:      $(brew --prefix)/Cellar/  (actual files, symlinked into bin/lib)
# Config:      /etc/ or ~/Library/Application Support/<app>/
```

**Sources:** `/opt/homebrew/Library/Taps/` (or `/usr/local/Homebrew/Library/Taps/`)
Common taps: `homebrew/core`, `homebrew/cask`, `homebrew/cask-fonts`

```bash
brew tap homebrew/cask-fonts
brew install --cask font-fira-code
```

---

## Windows — Package Managers

### winget (Built-in, Windows 10 1709+)

```powershell
# Search
winget search firefox
winget show Mozilla.Firefox

# Install
winget install Mozilla.Firefox
winget install -e --id Mozilla.Firefox    # exact match
winget install -e --id Microsoft.VisualStudioCode --silent

# Upgrade
winget upgrade --all           # upgrade everything
winget upgrade Mozilla.Firefox

# Uninstall
winget uninstall Mozilla.Firefox

# List installed
winget list

# Export/import (useful for new machine setup)
winget export -o packages.json
winget import -i packages.json

# Sources: WinGet repo + Microsoft Store
# Installs to: default installer location (Program Files, etc.)
```

### Chocolatey (Community, more packages)

```powershell
# Install Chocolatey first (run as Administrator):
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install
choco install firefox
choco install googlechrome git nodejs -y    # -y skips prompts

# Upgrade
choco upgrade all -y
choco upgrade firefox

# Uninstall
choco uninstall firefox

# Search
choco search firefox
choco info firefox

# List installed
choco list

# Where packages install:
# Tools/CLI: C:\ProgramData\chocolatey\bin\ (added to PATH)
# Apps: C:\Program Files\ or C:\Program Files (x86)\
# Chocolatey data: C:\ProgramData\chocolatey\
```

### Scoop (User-Level, No Admin Required)

```powershell
# Install Scoop (no admin required):
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression

# Install
scoop install git
scoop install curl wget jq

# Add buckets (extra repos)
scoop bucket add extras
scoop bucket add nerd-fonts
scoop install extras/vscode
scoop install nerd-fonts/FiraCode-NF

# Upgrade
scoop update *

# Uninstall
scoop uninstall git

# Where things install: C:\Users\<Username>\scoop\
# Apps: ~\scoop\apps\<app>\
# Shims (commands): ~\scoop\shims\ (added to PATH)
```

---

## Language-Specific Package Managers

### pip (Python)

```bash
pip install requests           # current user
pip install --user requests    # explicit user install (when not in venv)
pip install requests==2.31.0  # specific version
pip uninstall requests
pip list                       # installed packages
pip freeze > requirements.txt  # export
pip install -r requirements.txt # install from file
pip show requests              # info + location
pip cache purge                # clear cache

# Install locations:
# System:  /usr/lib/python3/dist-packages/  (avoid installing here)
# User:    ~/.local/lib/python3.x/site-packages/
# Venv:    <venv>/lib/python3.x/site-packages/

# ALWAYS use virtual environments:
python3 -m venv .venv
source .venv/bin/activate      # activate (Linux/macOS)
.venv\Scripts\activate         # activate (Windows)
pip install requests           # installs into venv only
```

### npm (Node.js)

```bash
# Project-local (recommended — installs to ./node_modules/)
npm install express
npm install --save-dev jest    # dev dependency
npm uninstall express
npm list                       # show tree
npm outdated                   # check for updates
npm update

# Global (for CLI tools)
npm install -g typescript
npm install -g nodemon
npm list -g --depth=0          # list global packages
npm uninstall -g typescript

# Global install location:
# Linux/macOS: $(npm root -g) → /usr/local/lib/node_modules/ or /opt/homebrew/lib/node_modules/
# Windows: %APPDATA%\npm\node_modules\
```

### Cargo (Rust)

```bash
cargo install ripgrep           # install a binary tool
cargo install --path .          # install from local project
cargo uninstall ripgrep
cargo install-update -a         # update all (requires cargo-update)

# Install location: ~/.cargo/bin/ (added to PATH)
# Registry cache: ~/.cargo/registry/
```

---

## Package Manager Quick Reference

| OS | Native PM | Command pattern | Install location |
|---|---|---|---|
| Debian/Ubuntu | apt | `sudo apt install <pkg>` | `/usr/bin/`, `/usr/lib/` |
| RHEL/Fedora | dnf | `sudo dnf install <pkg>` | `/usr/bin/`, `/usr/lib/` |
| Arch | pacman | `sudo pacman -S <pkg>` | `/usr/bin/`, `/usr/lib/` |
| macOS | brew | `brew install <pkg>` | `/opt/homebrew/bin/` |
| Windows | winget | `winget install <id>` | `C:\Program Files\` |
| Windows | choco | `choco install <pkg> -y` | `C:\ProgramData\chocolatey\` |
| Windows | scoop | `scoop install <pkg>` | `~\scoop\apps\` |
| Any | pip | `pip install <pkg>` | `site-packages/` |
| Any | npm (global) | `npm install -g <pkg>` | `node_modules/` |
