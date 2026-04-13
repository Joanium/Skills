---
name: Shell Profiles, Dotfiles & Shell Startup Order
trigger: .bashrc, .bash_profile, .zshrc, .profile, shell startup, shell config, dotfiles, source bashrc, interactive shell, login shell, shell not finding command, environment variable not set, terminal config, shell profile order, which profile loads, bash vs zsh startup
description: Understand the exact order shell config files load on Linux, macOS, and Windows — login vs interactive shells, .bashrc vs .bash_profile vs .profile, zsh equivalents, and PowerShell profiles. Use when troubleshooting missing environment variables, commands not found, or config not applying.
---

Shell configuration file confusion causes more "why isn't my variable set?" and "command not found" issues than almost anything else. Knowing exactly which file loads when — and in what order — solves these immediately.

## The Core Distinction: Login vs Interactive Shell

**Login shell:** Started when you authenticate — SSH session, console login, `su -`, `bash -l`.
→ Reads login-specific profile files.

**Interactive non-login shell:** A new terminal window, tab, or running `bash` from within a shell.
→ Reads the "rc" files, NOT the profile files.

**Non-interactive non-login shell:** A script run directly (`./myscript.sh`), cron jobs.
→ Reads almost nothing — only inherits the parent's environment.

This is why `export VAR=x` in `.bashrc` doesn't affect SSH sessions, and why `alias ls='ls --color'` in `.bash_profile` doesn't appear in your terminal.

---

## Bash Startup File Order

### Login Shell (SSH, console login, `bash --login`, `su -`)

```
1. /etc/profile              (system-wide — always read first)
   └── sources /etc/profile.d/*.sh  (distro-dependent)

2. First match from:
   a. ~/.bash_profile         (if it exists)
   b. ~/.bash_login           (if .bash_profile not found)
   c. ~/.profile              (if neither above found)

   Note: Most .bash_profile files source ~/.bashrc explicitly:
   [[ -f ~/.bashrc ]] && source ~/.bashrc
```

On logout: `~/.bash_logout` is read.

### Interactive Non-Login Shell (terminal window, `bash`)

```
1. /etc/bash.bashrc   (system-wide interactive config — Debian/Ubuntu)
   OR /etc/bashrc     (RHEL/CentOS/Fedora)

2. ~/.bashrc           (your personal interactive config)
```

### Non-Interactive (scripts, cron)

Only inherits the environment — does NOT read .bashrc, .bash_profile, or /etc/profile.

Exception: `BASH_ENV` variable — if set, bash reads that file.

### What to Put Where

```bash
# ~/.bash_profile — for login shells only:
#   - PATH modifications (already correct for SSH/login)
#   - Export DISPLAY, LANG, etc. for the session
#   - Source ~/.bashrc (so interactive shells also get your settings)

# ~/.bashrc — for interactive shells (and login shells via .bash_profile):
#   - Aliases: alias ll='ls -lah'
#   - Functions: function mkcd() { mkdir -p "$1" && cd "$1"; }
#   - Shell options: shopt -s globstar
#   - Prompt (PS1) customization
#   - PATH additions for interactive tools

# /etc/environment — for ALL sessions (PAM, login, scripts):
#   - System-wide environment variables
#   - NOT a shell script — no export keyword, no comments with #
```

---

## Zsh Startup File Order

Zsh is the default shell on macOS (since Catalina) and popular on Linux.

### Login Shell

```
1. /etc/zshenv       (always — even for non-interactive scripts)
2. ~/.zshenv         (always — use sparingly, loaded for scripts too)
3. /etc/zprofile     (login shell only)
4. ~/.zprofile       (login shell only — equivalent of .bash_profile)
5. /etc/zshrc        (interactive shell)
6. ~/.zshrc          (interactive shell — your main config)
7. /etc/zlogin       (login shell — after .zshrc, rarely used)
8. ~/.zlogin         (login shell — after .zshrc)
```

On logout: `~/.zlogout`, then `/etc/zlogout`.

### Interactive Non-Login Shell

```
1. /etc/zshenv → ~/.zshenv
2. /etc/zshrc  → ~/.zshrc
```

### What to Put Where (Zsh)

```zsh
# ~/.zshenv — Minimal. Only things needed for ALL shells including scripts:
export EDITOR="vim"
export LANG="en_US.UTF-8"

# ~/.zprofile — Login shell setup (like .bash_profile):
# Homebrew PATH setup goes here on macOS
eval "$(/opt/homebrew/bin/brew shellenv)"   # Apple Silicon
eval "$(/usr/local/bin/brew shellenv)"      # Intel

# ~/.zshrc — Main interactive config:
# Aliases, functions, prompt (oh-my-zsh, starship, pure, etc.)
# Completions, history settings, key bindings
```

---

## Common Shell Config Patterns

### Correct PATH Modification

```bash
# Always append or prepend — never overwrite $PATH
export PATH="$PATH:/new/directory"          # append (lower priority)
export PATH="/new/directory:$PATH"          # prepend (higher priority — takes precedence)

# Multiple additions
export PATH="$HOME/.local/bin:$HOME/go/bin:$PATH"

# Idempotent PATH (prevents duplicates when sourced multiple times)
add_to_path() {
    [[ ":$PATH:" != *":$1:"* ]] && export PATH="$1:$PATH"
}
add_to_path "$HOME/.local/bin"
add_to_path "/opt/myapp/bin"
```

### Common Aliases

```bash
# In ~/.bashrc or ~/.zshrc:
alias ll='ls -lah'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'
alias grep='grep --color=auto'
alias mkdir='mkdir -p'
alias df='df -h'
alias du='du -h'
alias free='free -h'

# Git shortcuts
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git log --oneline --graph --decorate'
```

### Shell Options (bash)

```bash
# In ~/.bashrc:
shopt -s histappend       # append to history file (don't overwrite)
shopt -s checkwinsize     # update LINES and COLUMNS after each command
shopt -s globstar         # ** matches any number of directories
shopt -s nocaseglob       # case-insensitive filename completion
shopt -s cdspell          # auto-correct minor typos in cd

# History settings
HISTSIZE=10000
HISTFILESIZE=20000
HISTCONTROL=ignoreboth    # ignore duplicates and lines starting with space
HISTIGNORE='ls:ll:la:cd:pwd:exit:clear'
```

### Shell Options (zsh)

```zsh
# In ~/.zshrc:
setopt APPEND_HISTORY        # append to history file
setopt SHARE_HISTORY         # share history between sessions
setopt HIST_IGNORE_DUPS      # ignore duplicate entries
setopt HIST_IGNORE_SPACE     # ignore commands starting with space
setopt AUTO_CD               # cd without typing cd (just directory name)
setopt EXTENDED_GLOB         # advanced glob patterns
setopt NO_CASE_GLOB          # case-insensitive glob

HISTSIZE=10000
SAVEHIST=10000
HISTFILE=~/.zsh_history
```

---

## macOS-Specific Shell Notes

```bash
# macOS changed default shell from bash to zsh in Catalina (10.15).
# If your shell shows "The default interactive shell is now zsh" — that's why.

# Check your current shell
echo $SHELL
$SHELL --version

# Change shell permanently
chsh -s /bin/zsh        # switch to zsh
chsh -s /bin/bash       # switch back to bash

# Apple's bash is ancient (version 3.2) due to GPL3 license.
# Install modern bash via Homebrew:
brew install bash
# Add to /etc/shells:
echo "$(brew --prefix)/bin/bash" | sudo tee -a /etc/shells
chsh -s "$(brew --prefix)/bin/bash"

# Homebrew PATH must be set before using brew in scripts
# Apple Silicon: /opt/homebrew/bin
# Intel: /usr/local/bin
# Add to ~/.zprofile (or .bash_profile):
eval "$(/opt/homebrew/bin/brew shellenv)"
```

---

## Windows PowerShell Profiles

PowerShell has the equivalent of `.bashrc` — profile scripts loaded at startup:

```powershell
# View profile paths (4 possible profile files)
$PROFILE | Select-Object *

# The files (in load order):
# 1. AllUsersAllHosts:      $PSHOME\Profile.ps1           → All users, all PS hosts
# 2. AllUsersCurrentHost:   $PSHOME\Microsoft.PowerShell_profile.ps1
# 3. CurrentUserAllHosts:   $HOME\Documents\PowerShell\Profile.ps1
# 4. CurrentUserCurrentHost: $HOME\Documents\PowerShell\Microsoft.PowerShell_profile.ps1
#    ↑ This is what $PROFILE resolves to by default

# Open your profile for editing
notepad $PROFILE
code $PROFILE   # VS Code

# Create if it doesn't exist
New-Item -ItemType File -Path $PROFILE -Force

# Example profile contents:
# Aliases
Set-Alias ll Get-ChildItem
function .. { Set-Location .. }
function ~ { Set-Location $HOME }

# Environment
$env:EDITOR = "code"

# Custom prompt
function prompt {
    "PS $($executionContext.SessionState.Path.CurrentLocation)$(if ($nestedPromptLevel -ge 1) { '>>' }) > "
}

# Oh My Posh / Starship for nice prompts
oh-my-posh init pwsh --config "$env:POSH_THEMES_PATH\jandedobbeleer.omp.json" | Invoke-Expression

# Reload profile without restarting PowerShell
. $PROFILE
```

### Execution Policy (Must Allow Profile to Load)

```powershell
# Check current policy
Get-ExecutionPolicy
Get-ExecutionPolicy -List

# Allow your personal scripts and signed scripts from others
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# Allow everything (less secure)
Set-ExecutionPolicy Unrestricted -Scope CurrentUser
```

---

## Troubleshooting: "Why Isn't My Variable Set?"

```bash
# 1. Which shell are you using?
echo $SHELL
echo $0

# 2. Is it a login or interactive shell?
shopt login_shell       # bash: shows "on" if login shell
[[ -o login ]]          # zsh: exit 0 if login shell

# 3. Which files are actually being sourced?
# Add to top of each file temporarily:
echo "Loading ~/.bashrc" 

# 4. Force reload a specific file
source ~/.bashrc
. ~/.zshrc

# 5. Check if a variable is exported (available to child processes)
export | grep MY_VAR
declare -x | grep MY_VAR

# 6. Trace shell startup (bash)
bash --login --norc -x 2>&1 | head -50   # see exactly what loads

# 7. Check if cron inherits your PATH
# Add to crontab:
* * * * * env > /tmp/cron-env.txt        # see cron's environment
```
