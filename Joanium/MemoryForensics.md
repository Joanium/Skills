---
name: Memory Forensics
trigger: memory forensics, RAM dump, volatility, memory analysis, process memory, heap analysis, malware analysis, memory artifacts, DRAM forensics, kernel structures, process hollowing, code injection, memory image, forensic analysis, incident response, digital forensics, memory acquisition
description: Acquire and analyze memory dumps to detect malware, reconstruct attacker activity, and extract forensic artifacts. Covers memory acquisition, Volatility 3 framework, process analysis, code injection detection, network artifact extraction, and timeline reconstruction.
---

# ROLE
You are a memory forensics analyst and incident responder. When an endpoint is compromised, you extract and analyze RAM to find what was running, what was hidden, and what the attacker did — before it's gone forever.

# CORE PRINCIPLES
```
MEMORY IS VOLATILE — acquire before rebooting; every second counts
MEMORY CONTAINS WHAT DISK HIDES — encrypted containers, fileless malware, network connections
PROCESS LIST LIES — rootkits hide processes; cross-reference multiple sources
ALWAYS VERIFY HASHES — document the memory image hash before any analysis
TIMELINE EVERYTHING — DKOM, code injection, and network artifacts tell a story
GOLD STANDARD = BASELINE — compare suspicious artifacts against clean image of same OS
```

# MEMORY ACQUISITION

## Live Acquisition (System Running)
```bash
# Linux — LiME (Linux Memory Extractor)
# Load LiME kernel module (must build for target kernel version)
sudo insmod lime-$(uname -r).ko "path=/mnt/usb/memory.lime format=lime"
# Creates a raw memory dump in LiME format

# Alternative: via TCP (avoids writing to disk on target)
sudo insmod lime.ko "path=tcp:4444 format=lime"
# On analyst machine:
nc <target_ip> 4444 > memory.lime

# Windows — WinPmem (free, open source)
winpmem_mini_x64.exe memory.raw

# Windows — DumpIt (commercial, widely used in IR)
DumpIt.exe /O memory.dmp

# macOS — osxpmem (must disable SIP)
osxpmem.app/osxpmem -o memory.dump

# HASH IMMEDIATELY AFTER ACQUISITION:
sha256sum memory.lime > memory.lime.sha256
```

## Virtual Machine Snapshots
```
VMware: VM → Snapshot → suspend VM → .vmem + .vmsn files
VirtualBox: machine directory → .sav file (saved state)
Hyper-V: checkpoint → .bin file

VMware .vmem is raw memory — Volatility reads it directly
VirtualBox .sav requires conversion: vboxmanage debugvm snapshot memdump
```

# VOLATILITY 3 FRAMEWORK

## Setup
```bash
pip install volatility3

# Volatility 3 auto-detects OS; no profile needed (unlike Volatility 2)
# For Windows: needs PDB symbols (downloads automatically from Microsoft)
# For Linux: provide ISF (symbol table) or use linux.symbols plugin

# Basic syntax:
vol -f memory.lime <plugin>
vol -f memory.raw windows.<plugin>
vol -f memory.lime linux.<plugin>
```

## Process Analysis
```bash
# Process list (from EPROCESS linked list)
vol -f memory.raw windows.pslist

# Process tree (parent-child relationships)
vol -f memory.raw windows.pstree

# DKOM-hidden processes (compares PsActiveProcessHead vs pool scanning)
vol -f memory.raw windows.psscan
# Compare psscan output vs pslist — processes in psscan but NOT pslist = likely hidden

# Process command lines (reveals what was executed)
vol -f memory.raw windows.cmdline

# Environment variables (can reveal attacker tools and paths)
vol -f memory.raw windows.envars

# DLLs loaded by each process
vol -f memory.raw windows.dlllist --pid 1234

# Handles (files, registry keys, network connections open per process)
vol -f memory.raw windows.handles --pid 1234
```

## Network Artifacts
```bash
# Active and recently closed network connections
vol -f memory.raw windows.netscan
# Shows: protocol, local addr:port, remote addr:port, state, PID, process name

# Suspicious patterns:
#   powershell.exe or cmd.exe with established network connections
#   Connections to foreign IPs on unusual ports (not 80/443)
#   CLOSE_WAIT connections (remote end closed, still in memory)
#   Multiple processes connecting to same C2 IP

# Extract connection artifacts even after connections were closed:
vol -f memory.raw windows.netstat
```

## Code Injection Detection
```bash
# Find memory regions that are executable AND not backed by a file on disk
# = classic code injection / shellcode signature
vol -f memory.raw windows.malfind

# malfind looks for:
#   VadNode with PAGE_EXECUTE_READWRITE (unusual; legitimate code is rarely RWX)
#   MZ/PE header at beginning of region (injected DLL/PE)
#   No mapped file backing the region

# Dump suspicious memory region for further analysis
vol -f memory.raw windows.malfind --dump --pid 1234 -o /output/

# Then analyze dump: 
strings suspicious_region.dmp | grep -i "http\|cmd\|powershell\|beacon"
file suspicious_region.dmp   # detect PE header
```

## Detecting Common Injection Techniques
```bash
# PROCESS HOLLOWING (replace legitimate process memory with malicious code):
# 1. Legitimate process starts (e.g., svchost.exe)
# 2. Original code is unmapped
# 3. Malicious code is written in
# Indicators: process has no mapped executable backing its main code region
vol -f memory.raw windows.malfind --pid <svchost_pid>
# Look for: MZ header in memory at base address, but no file mapping

# DLL INJECTION (LoadLibrary / reflective):
# Indicators: DLL in process that has no corresponding disk file
vol -f memory.raw windows.dlllist --pid <pid>
# Unmapped DLL (path is empty or \\?\) = suspicious

# PROCESS DOPPELGANGING / GHOSTING:
# Uses TxF transactions to load malicious PE via legit file handle
# Indicators: section object without backing file in filesystem
vol -f memory.raw windows.vadinfo --pid <pid>
# Look for VAD entries with Type=VadImageMap but empty file path

# SHELLCODE (no PE header):
# Run malfind; dump regions without MZ header; disassemble
ndisasm -b 32 shellcode.bin | head -50
# or use Speakeasy/libemu for emulation
```

## Registry Artifacts
```bash
# Loaded registry hives
vol -f memory.raw windows.registry.hivelist

# Read registry key from memory
vol -f memory.raw windows.registry.printkey \
  --key "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"

# Scan for registry keys by name (even partially unloaded hives)
vol -f memory.raw windows.registry.hivescan

# Common keys for persistence:
# HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
# HKLM\SYSTEM\CurrentControlSet\Services  (services)
# HKCU\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon (userinit)
```

## Linux Memory Forensics
```bash
# Process list
vol -f memory.lime linux.pslist
vol -f memory.lime linux.pstree

# Network connections
vol -f memory.lime linux.sockstat

# Loaded kernel modules (rootkits hide here)
vol -f memory.lime linux.lsmod

# Detect hidden kernel modules (compare lsmod vs module struct scan)
vol -f memory.lime linux.check_modules

# Bash history in memory (commands run, even if history file was cleared)
vol -f memory.lime linux.bash

# Open files per process
vol -f memory.lime linux.lsof --pid 1234

# Detect syscall table hooks (classic rootkit technique)
vol -f memory.lime linux.check_syscall
```

# INVESTIGATION WORKFLOW

## Initial Triage (First 15 Minutes)
```bash
# 1. Identify OS and build info
vol -f memory.raw windows.info

# 2. Process list — look for unusual names, parent-child anomalies
vol -f memory.raw windows.pstree > processes.txt
# Suspicious: cmd.exe/powershell.exe child of browser; svchost not under services.exe

# 3. Network connections — look for C2
vol -f memory.raw windows.netscan > network.txt
# Check foreign IPs with threat intel: VirusTotal, AbuseIPDB

# 4. Injected code
vol -f memory.raw windows.malfind > malfind.txt

# 5. Command lines — what was run?
vol -f memory.raw windows.cmdline > cmdlines.txt
# Suspicious: encoded powershell, certutil downloads, bitsadmin, regsvr32

# 6. Cross-reference hidden processes
vol -f memory.raw windows.pslist > pslist.txt
vol -f memory.raw windows.psscan > psscan.txt
diff <(awk '{print $2}' pslist.txt | sort) <(awk '{print $2}' psscan.txt | sort)
```

## Suspicious Indicator Checklist
```
PROCESSES:
[ ] Process name mimics legit (svch0st.exe, lsas.exe, svchost.exe not from C:\Windows\System32)
[ ] Unexpected parent (powershell.exe → chrome.exe)
[ ] svchost.exe without -k parameter
[ ] Process with no command line (DKOM manipulation)
[ ] explorer.exe running multiple times

NETWORK:
[ ] Browser / office app making DNS requests to random domains (DGA)
[ ] Beaconing: regular intervals to same IP
[ ] PowerShell / cmd.exe with established network connection
[ ] High-entropy domain names (random looking = likely DGA)

INJECTION:
[ ] RWX memory not backed by file
[ ] PE header in unexpected memory region
[ ] DLL without path (in-memory only)
[ ] Process with abnormally large working set

PERSISTENCE:
[ ] New services installed
[ ] Run keys with encoded commands
[ ] Scheduled tasks (check TaskScheduler registry key)
```

# STRING EXTRACTION AND YARA SCANNING
```bash
# Extract strings from memory image
strings -a -t d memory.raw > strings_decimal.txt
strings -a -t x memory.raw > strings_hex.txt

# Search for specific IoCs
grep -i "c2domain.com\|192.168.1.100\|beacon\|cobalt" strings_decimal.txt

# YARA scan memory dump (or individual process dumps)
yara -r malware_rules.yar memory.raw

# Popular YARA rule sets:
# Yara-Rules (GitHub)
# Neo23x0/signature-base (Florian Roth)
# CAPE sandbox rules for specific families
```
