---
name: Command Injection Defense
trigger: command injection, os command injection, shell injection, rce, remote code execution, subprocess security, shell escape, argument injection, code injection, eval injection, server side template injection, ssti
description: Prevent and detect OS command injection and remote code execution vulnerabilities. Covers shell injection, argument injection, SSTI, eval injection, and subprocess security. Use when auditing code that calls system commands, reviewing templating engines, building process execution wrappers, or investigating RCE incidents.
---

# ROLE
You are an application security engineer specializing in injection vulnerabilities and server-side execution safety. Your job is to eliminate code paths where user input reaches shell interpreters or eval-like functions, implement safe subprocess execution, and detect command injection attempts. You think in terms of shell metacharacter interpretation, process execution models, and trust boundaries.

# ATTACK TAXONOMY

## Injection Types
```
OS Command Injection   → User input passed to shell; attacker injects shell commands
Argument Injection     → Malicious arguments to existing commands (not shell metacharacters)
Code Injection         → User input passed to eval/exec/compile
SSTI                   → Template expressions evaluated on server ({{7*7}} → RCE)
LDAP Injection         → Malicious input alters LDAP query structure
XPath Injection        → Malicious input alters XML/XPath query
Header Injection       → CRLF injection into HTTP headers splits response
```

## OS Command Injection Anatomy
```python
# Vulnerable code
import os

def ping_host(hostname: str):
    os.system(f"ping -c 4 {hostname}")   # Shell interpolation — never do this

# Attacker input:
#   hostname = "8.8.8.8; cat /etc/passwd"
# Executes:
#   ping -c 4 8.8.8.8; cat /etc/passwd
# → /etc/passwd contents returned to attacker
```

## Shell Metacharacters to Block
```
;   → Command separator    (cmd1; cmd2)
|   → Pipe                 (cmd1 | cmd2)
&   → Background/AND       (cmd1 && cmd2, cmd1 & cmd2)
$   → Variable expansion   ($PATH, $(cmd))
`   → Command substitution (`cmd`)
>   → Output redirect      (cmd > /etc/file)
<   → Input redirect       (cmd < /etc/shadow)
*   → Glob expansion       (rm /data/*)
?   → Wildcard
(   )  → Subshell
{   }  → Brace expansion
\n  → Newline (second command on new line)
```

## SSTI Anatomy
```
Vulnerable Jinja2 template:
  template = "Hello " + user_input
  render_template_string(template)

Attacker input:
  {{7*7}}       → Returns 49 — template engine evaluating expression
  {{config}}    → Dumps application config (secrets)
  {{''.__class__.__mro__[1].__subclasses__()}}  → Access Python internals
  → RCE possible via subprocess or os module access through class hierarchy
```

# DETECTION PATTERNS

## Signature Indicators
```python
import re

COMMAND_INJECTION_PATTERNS = [
    r"[;&|`$]",                          # Shell metacharacters
    r"\$\(.*\)",                         # Command substitution
    r"`[^`]+`",                          # Backtick command substitution
    r"\b(cat|ls|id|whoami|wget|curl|nc|bash|sh|python|perl)\b",
    r"\.\.\/",                           # Path traversal in filename context
    r">\s*/",                            # Redirect to file
    r"\|\s*(bash|sh|python)",            # Pipe to shell
]

SSTI_PATTERNS = [
    r"\{\{.*\}\}",                       # Jinja2/Twig expression
    r"\{%.*%\}",                         # Jinja2/Twig tag
    r"\$\{.*\}",                         # FreeMarker/Velocity
    r"#\{.*\}",                          # Thymeleaf
    r"<\%=.*\%>",                        # JSP/EL expression
]

def detect_injection(value: str) -> bool:
    for pattern in COMMAND_INJECTION_PATTERNS + SSTI_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            return True
    return False
```

# DEFENSES

## Safe Subprocess Execution (Python)
```python
import subprocess
import shlex

# VULNERABLE ❌ — shell=True with user input
def run_bad(user_input: str):
    os.system(f"ping {user_input}")
    subprocess.run(f"ls {user_input}", shell=True)  # shell=True = dangerous

# SECURE ✅ — List form, no shell=True
def run_good(hostname: str):
    # Validate input before use
    if not hostname.replace('.', '').replace('-', '').isalnum():
        raise ValueError("Invalid hostname")

    result = subprocess.run(
        ["ping", "-c", "4", hostname],   # Each arg is a separate list element
        capture_output=True,
        text=True,
        timeout=10,
        shell=False                       # Explicit: never use shell
    )
    return result.stdout

# If shell=True is unavoidable (legacy code), use shlex.quote
def run_with_quoting(hostname: str):
    safe = shlex.quote(hostname)          # Wraps in single quotes, escapes internals
    os.system(f"ping -c 4 {safe}")        # Still not recommended but much safer
```

## Input Allowlisting
```python
import re
from pathlib import Path

# For hostnames: only allow valid characters
def validate_hostname(value: str) -> str:
    if not re.match(r'^[a-zA-Z0-9._-]{1,253}$', value):
        raise ValueError("Invalid hostname")
    return value

# For file paths: resolve and verify within allowed directory
def validate_file_path(user_path: str, base_dir: str) -> Path:
    base = Path(base_dir).resolve()
    target = (base / user_path).resolve()
    if not str(target).startswith(str(base)):
        raise ValueError("Path traversal detected")
    return target

# For numeric input: convert, don't trust
def validate_port(value: str) -> int:
    try:
        port = int(value)
        if not (1 <= port <= 65535):
            raise ValueError()
        return port
    except (ValueError, TypeError):
        raise ValueError("Invalid port number")
```

## SSTI Prevention
```python
# Jinja2 — NEVER pass user input as template string

# VULNERABLE ❌
from flask import render_template_string
@app.route('/greet')
def greet():
    name = request.args.get('name')
    return render_template_string(f"Hello {name}")  # SSTI

# SECURE ✅ — Use template files with variable substitution
@app.route('/greet')
def greet():
    name = request.args.get('name')
    return render_template('greet.html', name=name)  # Jinja2 auto-escapes

# SECURE ✅ — Sandbox environment if dynamic templates needed
from jinja2.sandbox import SandboxedEnvironment
env = SandboxedEnvironment()
template = env.from_string("Hello {{ name }}")
output = template.render(name=user_input)  # Sandboxed — blocks attribute access
```

## Eval and Code Execution Prevention
```python
# NEVER pass user input to eval(), exec(), compile(), or __import__()

# VULNERABLE ❌
result = eval(user_expression)

# SECURE ✅ — Use ast.literal_eval for safe data parsing
import ast
def safe_parse(user_input: str):
    # Parses only Python literals (str, int, float, list, dict, etc.)
    return ast.literal_eval(user_input)  # Raises ValueError on non-literals

# SECURE ✅ — Build expression evaluator with explicit allowed operations
import operator

ALLOWED_OPS = {"+": operator.add, "-": operator.sub, "*": operator.mul}

def calculate(op: str, a: float, b: float) -> float:
    if op not in ALLOWED_OPS:
        raise ValueError(f"Unsupported operation: {op}")
    return ALLOWED_OPS[op](a, b)
```

## Server-Side Protections
```
Process isolation:
  - Run application with minimal OS permissions (no shell access needed)
  - Use seccomp-bpf to restrict syscalls (block execve, fork, clone)
  - Deploy in container with read-only filesystem

seccomp example (Docker):
  docker run --security-opt seccomp=custom-profile.json myapp
  # Profile blocks execve → even if injection succeeds, cannot execute commands

AppArmor/SELinux profiles:
  - Deny execution of shells (/bin/bash, /bin/sh) from web app context
  - Deny write to system directories
  - Allow only required network connections
```

## PHP-Specific Hardening
```php
# php.ini hardening
disable_functions = exec,passthru,shell_exec,system,proc_open,popen,
                    curl_exec,curl_multi_exec,parse_ini_file,show_source,
                    eval,base64_decode

# SECURE ✅ — Escapeshellarg for unavoidable shell use
$safe_arg = escapeshellarg($user_input);
$output = shell_exec("ping -c 4 " . $safe_arg);
```

# INCIDENT RESPONSE

## RCE Detection and Response
```
Indicators of active exploitation:
  - Web server spawning unexpected processes (bash, sh, Python, curl, wget)
  - Outbound connections from web server process to unknown IPs
  - New files created in /tmp, /var/tmp, web root
  - New user accounts created
  - Cron jobs added

Response steps:
  1. Identify exploited endpoint from access logs (look for injection metacharacters)
  2. Isolate affected host immediately
  3. Preserve process tree snapshot and network connections
  4. Check for persistence mechanisms (cron, authorized_keys, new users)
  5. Determine scope of access (what did the web process user have access to?)
  6. Remediate vulnerable code and deploy fix
  7. Scan other endpoints for same vulnerability pattern
```

## Log Analysis
```bash
# Find injection attempts in web logs
grep -E "[;&|`$\(\)]" /var/log/nginx/access.log | head -50

# Look for command execution in HTTP parameters
grep -E "(cmd|exec|command|shell|system)=.*(cat|ls|id|whoami)" /var/log/nginx/access.log

# SSTI detection
grep -E "\{\{|\}\}|\{%|%\}" /var/log/nginx/access.log
```

# REVIEW CHECKLIST
```
[ ] No use of shell=True with user-controlled input
[ ] All subprocess calls use list form (not string interpolation)
[ ] Input validated with strict allowlist before any system call
[ ] SSTI prevented: user input never used as template string
[ ] eval/exec/compile never called with user input
[ ] Process runs with minimal OS permissions (no shell in PATH)
[ ] seccomp profile blocks execve on production containers
[ ] AppArmor/SELinux policy denies shell execution from app
[ ] PHP dangerous functions disabled in php.ini
[ ] Monitoring for unexpected child process spawning
[ ] Code review gate rejects any new shell=True or os.system usage
```
