---
name: Process Management — All Operating Systems
trigger: process management, kill process, how to kill a process, ps aux, top, htop, task manager, taskkill, process list, what is running, find process by port, process id, PID, running processes, stop a process, background process, zombie process, service vs process
description: Find, inspect, and manage running processes on Linux, macOS, and Windows — listing processes, finding what's using a port, killing processes, running jobs in background, and understanding process states. Use when diagnosing high CPU/memory, killing stuck processes, or managing background jobs.
---

Processes are running instances of programs. Managing them — finding them, inspecting them, stopping them — is a fundamental OS skill.

## Linux Process Management

### Viewing Processes

```bash
# Real-time interactive view
top             # classic, runs on every Linux system
htop            # better UI (install: apt install htop)
btop            # modern, graphical TUI (install: apt install btop)

# Snapshot of all processes
ps aux          # all processes, all users, with full details
# a = all users, u = user-oriented format, x = include processes without TTY

ps aux | grep nginx           # find nginx processes
ps aux | sort -k3 -rn | head  # top CPU consumers
ps aux | sort -k4 -rn | head  # top memory consumers

# Process tree (parent-child relationships)
pstree
pstree -p       # with PIDs
pstree alice    # only processes owned by alice

# More detail about a specific process
ps -p 1234 -o pid,ppid,user,cpu,mem,cmd

# All columns available for ps
ps -eo pid,ppid,user,stat,pcpu,pmem,comm,cmd | head -20
```

### Process States (STAT column in ps)

| State | Meaning |
|---|---|
| `R` | Running or runnable |
| `S` | Sleeping (waiting for event) — most processes are here |
| `D` | Uninterruptible sleep (usually waiting on I/O) — cannot be killed |
| `T` | Stopped (Ctrl+Z or SIGSTOP) |
| `Z` | Zombie (dead but parent hasn't called wait()) |
| `<` | High priority |
| `N` | Low priority (nice) |
| `s` | Session leader |
| `+` | In foreground process group |

A `Z` zombie cannot be killed — you must kill its parent process or wait for the parent to reap it.

### Finding Processes

```bash
# Find by name
pgrep nginx             # returns PIDs
pgrep -l nginx          # returns PIDs + names
pidof nginx             # like pgrep, slightly different behavior

# Find what's using a specific port
ss -tlnp | grep :80            # modern (preferred)
netstat -tlnp | grep :80       # older systems (may need net-tools package)
lsof -i :80                    # all processes using port 80
lsof -i TCP:8080               # TCP specifically

# Find all files a process has open
lsof -p 1234                   # all files open by PID 1234
lsof -p $(pidof nginx)         # all files open by nginx

# Find which process owns a file
lsof /var/log/syslog
fuser /var/log/syslog

# Find by port and get the PID
ss -tlnp | grep :443 | awk '{print $NF}'   # extract PID from ss output
```

### Killing Processes

```bash
# Signals
kill -l             # list all signals

# SIGTERM (15) — graceful shutdown (the default)
kill 1234           # send SIGTERM to PID 1234
kill -15 1234       # explicit

# SIGKILL (9) — force kill, cannot be caught or ignored
kill -9 1234
kill -KILL 1234

# Kill by name
pkill nginx         # SIGTERM to all processes named nginx
pkill -9 nginx      # force kill by name
killall nginx       # similar to pkill

# Kill all processes of a user
pkill -u alice
kill -9 -1          # (as root) kill ALL processes except init — extreme measure

# Send signal to process group
kill -TERM -1234    # negative PID = process group

# Order of escalation (best practice):
# 1. kill <pid>          → SIGTERM: ask nicely
# 2. kill -2 <pid>       → SIGINT: like Ctrl+C
# 3. kill -9 <pid>       → SIGKILL: force (last resort)
```

### Background Jobs

```bash
# Run a command in background
./long_script.sh &              # & = run in background, detached from terminal

# Suspend (pause) foreground process
Ctrl+Z                          # sends SIGSTOP

# List background jobs
jobs
jobs -l                         # with PIDs

# Resume a background job
fg                              # bring most recent background job to foreground
fg %2                           # bring job #2 to foreground
bg                              # resume most recent stopped job in background
bg %2                           # resume job #2 in background

# Run detached from terminal (survives logout)
nohup ./long_script.sh &        # nohup ignores SIGHUP (logout signal)
nohup ./long_script.sh > output.log 2>&1 &   # redirect output

# Keep running after logout with screen or tmux (preferred)
screen -S mysession
tmux new-session -s mysession
```

### Process Priority (Nice Values)

```bash
# Nice range: -20 (highest priority) to 19 (lowest priority)
# Default: 0

# Start a process with low priority
nice -n 10 ./cpu_intensive_script.sh
nice -n 19 make -j8             # build at lowest priority

# Change priority of running process
renice 10 -p 1234               # lower priority of PID 1234
renice -5 -p 1234               # raise priority (requires root)
renice 10 -u alice              # lower all alice's processes
```

### /proc — Live Process Information

```bash
# Each running PID has a directory in /proc
ls /proc/1234/

/proc/<pid>/
├── cmdline     → Full command line that started the process
├── environ     → Environment variables of the process
├── fd/         → Symbolic links to all open file descriptors
├── maps        → Memory maps
├── net/        → Network state as seen by the process
├── status      → Human-readable process status
├── stat        → Process stats (used by ps, top)
├── io          → I/O stats
└── cwd         → Symlink to current working directory

# Useful reads
cat /proc/1234/cmdline | tr '\0' ' '   # command line with spaces
cat /proc/1234/status | grep VmRSS     # resident memory usage
ls -la /proc/1234/fd/                  # open files
cat /proc/1234/environ | tr '\0' '\n'  # environment variables
```

---

## macOS Process Management

Most Linux commands work on macOS (`ps`, `kill`, `pgrep`, `pkill`). Key differences:

```bash
# Real-time monitoring
top             # macOS version has different key bindings
Activity Monitor.app   # GUI equivalent

# Process list (macOS ps syntax is BSD-style)
ps aux          # works the same as Linux
ps -ef          # also works

# What's using a port
lsof -i :80
lsof -i :8080 -P -n    # -P = show port numbers, -n = skip hostname lookup

# Kill (same as Linux)
kill -9 1234
pkill -9 nginx

# macOS-specific: Activity Monitor
open -a "Activity Monitor"

# launchctl — manage macOS services
launchctl list          # list agents/daemons
launchctl list | grep myapp
launchctl stop com.company.myapp   # stop a specific service
launchctl start com.company.myapp  # start it
```

---

## Windows Process Management

### Task Manager and Alternatives

```
Task Manager:    Ctrl+Shift+Esc  or  Ctrl+Alt+Del → Task Manager
Process Explorer (Sysinternals): Better — shows parent-child tree, handles, DLLs
Resource Monitor: resmon.exe — CPU, memory, disk, network per process
```

### Command Line (CMD)

```batch
:: List all running processes
tasklist
tasklist /FI "IMAGENAME eq nginx.exe"   :: filter by name
tasklist /FI "PID eq 1234"
tasklist /FI "STATUS eq NOT RESPONDING" :: hung processes
tasklist /V                             :: verbose (username, memory, window title)
tasklist /SVC                           :: show hosted services

:: Kill process
taskkill /PID 1234
taskkill /IM notepad.exe               :: by name
taskkill /F /PID 1234                  :: force kill (/F = like kill -9)
taskkill /F /IM notepad.exe /T         :: force kill + child processes (/T)

:: Find what's using a port
netstat -ano | findstr :80
netstat -ano | findstr :8080
:: Then look up the PID in tasklist

:: Start a process in background (detached)
start /B myprogram.exe
start "" /B "C:\path\program.exe" args
```

### PowerShell

```powershell
# List processes
Get-Process
Get-Process -Name nginx
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10    # top CPU
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10  # top memory

# Find by port
Get-NetTCPConnection -LocalPort 80 | Select-Object LocalPort, OwningProcess |
    ForEach-Object { Get-Process -Id $_.OwningProcess }

# More detail on a process
Get-Process -Id 1234 | Select-Object *

# Kill process
Stop-Process -Id 1234
Stop-Process -Name notepad
Stop-Process -Id 1234 -Force      # like kill -9

# Start a process
Start-Process notepad.exe
Start-Process -FilePath "C:\app\server.exe" -WindowStyle Hidden -NoNewWindow

# Wait for a process to finish
Wait-Process -Name notepad

# Monitor processes
Get-Process | Where-Object {$_.CPU -gt 10} | Select-Object Name, CPU, WorkingSet64

# Find process by port (complete)
function Get-ProcessByPort {
    param([int]$Port)
    $conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($conn) {
        Get-Process -Id $conn.OwningProcess | Select-Object Id, Name, Path
    }
}
Get-ProcessByPort -Port 8080

# Services (different from processes but related)
Get-Service
Get-Service -Name nginx
Start-Service nginx
Stop-Service nginx
Restart-Service nginx
Set-Service nginx -StartupType Automatic   # set to auto-start
```

---

## Cross-Platform: Find What's Using a Port

| OS | Command |
|---|---|
| Linux | `ss -tlnp \| grep :80` or `lsof -i :80` |
| macOS | `lsof -i :80` or `lsof -i TCP:80 -P -n` |
| Windows CMD | `netstat -ano \| findstr :80` then `tasklist /FI "PID eq <pid>"` |
| Windows PS | `Get-NetTCPConnection -LocalPort 80 \| ForEach-Object { Get-Process -Id $_.OwningProcess }` |

## Cross-Platform: Force Kill by Name

| OS | Command |
|---|---|
| Linux | `pkill -9 nginx` |
| macOS | `pkill -9 nginx` |
| Windows CMD | `taskkill /F /IM nginx.exe` |
| Windows PS | `Stop-Process -Name nginx -Force` |
