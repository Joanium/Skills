---
name: Environment Variables — All Operating Systems
trigger: environment variables, env vars, PATH variable, $PATH, set environment variable, how to set env var, environment variable linux, environment variable windows, environment variable mac, printenv, echo $PATH, .env file, persistent environment variable, shell variables
description: Understand, read, set, and persist environment variables on Linux, macOS, and Windows — in the current session, for a user, for all users, or for services. Know common important variables and how they interact with shells, scripts, and services.
---

Environment variables are key-value pairs that configure the runtime environment for processes. Every process inherits the environment of its parent. Getting them right is critical for tools, services, and scripts.

## Reading Environment Variables

```bash
# Linux / macOS
printenv                    # list all environment variables
printenv PATH               # specific variable
echo $PATH                  # print in shell
echo $HOME $USER $SHELL     # multiple
env                         # list all (like printenv)

# Show a single variable
echo "$JAVA_HOME"

# Windows CMD
set                         # list all
set PATH                    # specific variable
echo %PATH%                 # print

# Windows PowerShell
Get-ChildItem Env:           # list all
$env:PATH                   # specific variable
[System.Environment]::GetEnvironmentVariables()   # all three scopes
```

## Setting Variables — Session vs Persistent

### Linux / macOS

**Current session only (lost when terminal closes):**
```bash
export MY_VAR="hello"
export PATH="$PATH:/my/new/bin"
```

**Persistent for current user (survives sessions):**
```bash
# Add to ~/.bashrc (bash interactive shells)
echo 'export MY_VAR="hello"' >> ~/.bashrc
source ~/.bashrc             # apply now

# Or ~/.zshrc (zsh — macOS default)
echo 'export MY_VAR="hello"' >> ~/.zshrc

# Or ~/.profile (login shells, all POSIX shells)
echo 'export MY_VAR="hello"' >> ~/.profile
```

**Persistent for all users (requires root):**
```bash
# /etc/environment — parsed by PAM, NOT a shell script, no export keyword
echo 'MY_VAR="hello"' >> /etc/environment    # takes effect at next login

# /etc/profile.d/ — shell scripts, sourced for all login shells
cat > /etc/profile.d/myapp.sh << 'EOF'
export MY_APP_HOME="/opt/myapp"
export PATH="$PATH:$MY_APP_HOME/bin"
EOF
chmod +x /etc/profile.d/myapp.sh
```

**For systemd services (environment in the service unit):**
```ini
# /etc/systemd/system/myservice.service
[Service]
Environment="DB_HOST=localhost"
Environment="DB_PORT=5432"
EnvironmentFile=/etc/myservice/environment    # or from a file
```

```bash
# Environment file format (no export keyword)
DB_HOST=localhost
DB_PORT=5432
API_KEY=secret
```

### Windows CMD

**Current session:**
```batch
set MY_VAR=hello
set PATH=%PATH%;C:\my\new\bin
```

**Persistent (user-level):**
```batch
setx MY_VAR "hello"
setx PATH "%PATH%;C:\my\new\bin"   # ⚠️ setx reads the SAVED PATH, not the live one
```

**Persistent (system-level — requires elevation):**
```batch
setx MY_VAR "hello" /M
```

### Windows PowerShell

**Current session:**
```powershell
$env:MY_VAR = "hello"
$env:PATH += ";C:\my\new\bin"
```

**Persistent (user-level):**
```powershell
[System.Environment]::SetEnvironmentVariable("MY_VAR", "hello", "User")
```

**Persistent (system-level — run as Administrator):**
```powershell
[System.Environment]::SetEnvironmentVariable("MY_VAR", "hello", "Machine")
```

**Read from a specific scope:**
```powershell
[System.Environment]::GetEnvironmentVariable("PATH", "Machine")
[System.Environment]::GetEnvironmentVariable("PATH", "User")
[System.Environment]::GetEnvironmentVariable("PATH", "Process")   # current session
```

**Via Registry directly (same as above, different view):**
```
HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment  → System
HKCU\Environment                                                   → User
```

## The PATH Variable — Most Critical

`PATH` is a list of directories the shell searches for executable files. Wrong PATH = commands not found.

```bash
# Linux/macOS — colon-separated
echo $PATH
# /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games

# Add to PATH safely (don't overwrite)
export PATH="$PATH:/new/directory"          # append
export PATH="/new/directory:$PATH"          # prepend (higher priority)

# Check which binary will run for a command
which python3
type python3
command -v python3

# See all instances of a binary across PATH
which -a python
```

```powershell
# Windows — semicolon-separated
$env:PATH -split ";"      # list each directory

# Find where a command comes from
Get-Command python | Select-Object Source
where.exe python
```

### PATH Precedence Rules

- **Linux/macOS:** Left to right — first match wins. `/usr/local/bin` before `/usr/bin` means local installs take priority.
- **Windows:** Left to right — first match wins. User PATH is appended AFTER System PATH when both are set.

## Common Important Variables

### Linux / macOS

| Variable | Meaning | Example |
|---|---|---|
| `PATH` | Directories to search for commands | `/usr/local/bin:/usr/bin:/bin` |
| `HOME` | Current user's home directory | `/home/alice` |
| `USER` | Current username | `alice` |
| `SHELL` | Current shell | `/bin/bash` |
| `LANG` / `LC_ALL` | Locale (language, encoding) | `en_US.UTF-8` |
| `EDITOR` / `VISUAL` | Default text editor | `vim` |
| `PAGER` | Default pager (for man pages etc.) | `less` |
| `TERM` | Terminal type | `xterm-256color` |
| `PS1` | Shell prompt format | `\u@\h:\w\$` |
| `TMPDIR` | Temp directory for this user | `/tmp` |
| `XDG_CONFIG_HOME` | User config directory (XDG spec) | `~/.config` |
| `XDG_DATA_HOME` | User data directory | `~/.local/share` |
| `XDG_CACHE_HOME` | User cache directory | `~/.cache` |
| `LD_LIBRARY_PATH` | Extra dirs to search for shared libraries | `/opt/myapp/lib` |
| `JAVA_HOME` | JDK installation path | `/usr/lib/jvm/java-17-openjdk` |
| `PYTHONPATH` | Extra Python module search paths | `/opt/myapp/lib/python` |
| `NODE_PATH` | Extra Node.js module search paths | `/usr/local/lib/node_modules` |
| `GOPATH` | Go workspace | `~/go` |
| `GOROOT` | Go installation | `/usr/local/go` |
| `VIRTUAL_ENV` | Active Python virtualenv path | `/home/alice/myenv` |
| `npm_config_prefix` | Global npm prefix | `/usr/local` |

### Windows

| Variable | Meaning | Example |
|---|---|---|
| `%PATH%` | Executable search path | `C:\Windows\system32;C:\Windows;...` |
| `%USERPROFILE%` | Current user's profile folder | `C:\Users\Alice` |
| `%APPDATA%` | AppData\Roaming | `C:\Users\Alice\AppData\Roaming` |
| `%LOCALAPPDATA%` | AppData\Local | `C:\Users\Alice\AppData\Local` |
| `%TEMP%` / `%TMP%` | Temp directory | `C:\Users\Alice\AppData\Local\Temp` |
| `%SystemRoot%` | Windows directory | `C:\Windows` |
| `%ProgramFiles%` | 64-bit program files | `C:\Program Files` |
| `%ProgramFiles(x86)%` | 32-bit program files | `C:\Program Files (x86)` |
| `%ProgramData%` | All-users app data | `C:\ProgramData` |
| `%ComSpec%` | Path to cmd.exe | `C:\Windows\System32\cmd.exe` |
| `%USERNAME%` | Current username | `Alice` |
| `%COMPUTERNAME%` | Machine name | `WORKSTATION01` |
| `%USERDOMAIN%` | Domain name | `CORP` |
| `%OS%` | Operating system | `Windows_NT` |
| `%PROCESSOR_ARCHITECTURE%` | CPU arch | `AMD64` |
| `%NUMBER_OF_PROCESSORS%` | CPU count | `8` |
| `%JAVA_HOME%` | JDK path | `C:\Program Files\Java\jdk-17` |
| `%PYTHON_HOME%` | Python install | `C:\Python311\` |

## .env Files (Application-Level)

`.env` files are used by applications (especially Node.js, Python/Django, Docker) to load variables at runtime — NOT by the OS:

```bash
# .env file format
DATABASE_URL=postgres://localhost/mydb
SECRET_KEY=supersecretvalue123
DEBUG=false
PORT=3000
```

**They are NOT automatically loaded by the shell.** Apps use libraries like `dotenv` (Node.js), `python-dotenv` (Python), or `--env-file` (Docker) to load them.

```bash
# Manually load a .env file into the current shell
set -o allexport; source .env; set +o allexport

# Or one-liner
export $(grep -v '^#' .env | xargs)
```

⚠️ **Security:** Never commit `.env` files to Git. Add to `.gitignore`. Use secrets managers for production.

## Scoping — When Variables Take Effect

```
Linux variable scope, from narrowest to widest:
1. Current command:     MY_VAR=hello command  (only for that command)
2. Current session:     export MY_VAR=hello   (until terminal closes)
3. User login:          ~/.bashrc / ~/.profile (user sessions)
4. All users:           /etc/environment      (requires root)
5. Service:             systemd EnvironmentFile or Environment=

Windows variable scope:
1. Current session:     $env:VAR = "value" or set VAR=value
2. User (persisted):    setx VAR value   or   HKCU\Environment
3. System (persisted):  setx VAR value /M or  HKLM\System\...\Environment
```

New processes inherit variables from their parent at the moment of launch — changing a variable after a process starts does NOT affect running processes.
