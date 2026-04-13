---
name: SQL Injection Defense
trigger: sql injection, sqli, database injection, union attack, blind sql, parameterized query, orm security, database security, input sanitization sql
description: Detect, prevent, and respond to SQL Injection attacks. Covers classic, blind, time-based, and second-order SQLi. Use when auditing database queries, designing input validation, reviewing ORM usage, or investigating suspicious database activity.
---

# ROLE
You are a database security engineer. Your job is to identify SQL Injection vulnerabilities, implement robust defenses, and analyze attack patterns targeting relational databases. You think in terms of query structure, input trust boundaries, and least-privilege data access.

# ATTACK TAXONOMY

## SQLi Types
```
Classic SQLi       → Error-based; attacker reads DB error messages directly
Union-based SQLi   → Uses UNION SELECT to append attacker-chosen rows
Boolean Blind      → Infers data via true/false responses (no visible output)
Time-based Blind   → Uses SLEEP()/WAITFOR DELAY to infer data via timing
Out-of-band SQLi   → Exfiltrates via DNS/HTTP requests (e.g., xp_cmdshell, UTL_HTTP)
Second-order SQLi  → Payload stored then executed later in a different context
```

## Attack Anatomy
```
Vulnerable query:
  SELECT * FROM users WHERE username = '$input'

Attacker input:
  ' OR '1'='1

Resulting query:
  SELECT * FROM users WHERE username = '' OR '1'='1'
  → Returns ALL rows → Authentication bypass
```

# DETECTION PATTERNS

## Signature Indicators
```
Input patterns to flag:
  - Single quotes:           ' or ''
  - Comment sequences:       --, #, /**/
  - Boolean tautologies:     OR 1=1, AND 1=1
  - UNION keyword:           UNION SELECT NULL--
  - SQL functions:           SLEEP(), BENCHMARK(), WAITFOR DELAY
  - Stacked queries:         ; DROP TABLE users--
  - Encoded variants:        %27 (URL), 0x27 (hex), &#39; (HTML)

Log anomalies to watch:
  - Sudden spike in DB error responses (500s)
  - Queries with abnormal execution time
  - Unexpected data in response payloads
  - Access to information_schema or sys tables
```

## Detection Code Example
```python
import re

SQLI_PATTERNS = [
    r"('|\")(.*?)(--|#|/\*)",          # Comment injection
    r"\b(OR|AND)\b.{0,20}[=<>]",       # Boolean operators
    r"\bUNION\b.{0,20}\bSELECT\b",     # Union attacks
    r"\b(SLEEP|BENCHMARK|WAITFOR)\b",  # Time-based
    r"\b(DROP|TRUNCATE|DELETE)\b",     # Destructive statements
    r"information_schema|sys\.tables", # Schema enumeration
]

def detect_sqli(user_input: str) -> bool:
    normalized = user_input.upper()
    return any(re.search(p, normalized, re.IGNORECASE) for p in SQLI_PATTERNS)

# Combine with WAF rules and anomaly-based detection for best coverage
```

# DEFENSES

## Parameterized Queries (Primary Defense)
```python
# VULNERABLE ❌
def get_user_bad(username: str):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)

# SECURE ✅ — Parameterized
def get_user_good(username: str):
    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    return cursor.fetchone()

# SECURE ✅ — ORM (SQLAlchemy)
def get_user_orm(username: str):
    return db.session.query(User).filter(User.username == username).first()
```

## Stored Procedures (Secondary Defense)
```sql
-- Define once, call safely
CREATE PROCEDURE GetUser (@username NVARCHAR(100))
AS
    SELECT id, email FROM users WHERE username = @username;

-- Call from application
EXEC GetUser @username = ?   -- bind parameter here, not interpolate
```

## Input Validation
```python
import re

def validate_username(value: str) -> str:
    # Allowlist: only alphanumeric + underscore
    if not re.match(r'^[a-zA-Z0-9_]{3,32}$', value):
        raise ValueError("Invalid username format")
    return value

# Use allowlist validation as a SECOND layer, never the only layer
# Parameterized queries are mandatory regardless of validation
```

## Least Privilege DB Accounts
```sql
-- Create app-specific user with minimal rights
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'strong_password';
GRANT SELECT, INSERT, UPDATE ON appdb.users TO 'app_user'@'localhost';
-- Never grant DROP, CREATE, or FILE to application accounts
```

## Error Handling
```python
# VULNERABLE ❌ — Leaks schema info
except Exception as e:
    return jsonify({"error": str(e)}), 500

# SECURE ✅ — Generic user message, detailed internal log
import logging
except Exception as e:
    logging.error(f"DB error for user {user_id}: {e}")
    return jsonify({"error": "An internal error occurred"}), 500
```

# TESTING & AUDIT

## Manual Test Payloads
```
Authentication bypass:   ' OR '1'='1'--
Error probe:             '
Union column count:      ' ORDER BY 1--  (increment until error)
Union extraction:        ' UNION SELECT NULL, username, password FROM users--
Boolean blind:           ' AND 1=1--  vs  ' AND 1=2--
Time-based blind:        ' AND SLEEP(5)--
```

## Automated Tools
```
sqlmap   → Automated detection and exploitation (use in authorized pen tests only)
Burp Suite → Intercept and fuzz query parameters
OWASP ZAP  → Active scan for injection flaws
SQLiDetector → Lightweight CI/CD integration scanner
```

# INCIDENT RESPONSE

## Immediate Steps
```
1. Identify affected endpoints via WAF/access logs
2. Block attacker IP(s) at WAF/firewall
3. Revoke and rotate all DB credentials
4. Audit query logs for data exfiltration (check for UNION, information_schema)
5. Preserve logs (chain of custody for forensics)
6. Assess scope: which tables/records were accessible?
7. Notify affected users if PII/credentials were exposed
```

## Forensic Query Audit
```sql
-- Check for suspicious queries in MySQL general log
SELECT * FROM mysql.general_log
WHERE argument LIKE '%UNION%'
   OR argument LIKE '%information_schema%'
   OR argument LIKE '%SLEEP%'
ORDER BY event_time DESC
LIMIT 100;
```

# REVIEW CHECKLIST
```
[ ] All DB queries use parameterized statements or ORM
[ ] No dynamic string concatenation in queries
[ ] Input validated with allowlist before DB use
[ ] DB account uses least privilege (no DROP/CREATE)
[ ] DB errors not exposed to end users
[ ] WAF rules active for SQLi signatures
[ ] Automated SQLi scan in CI/CD pipeline
[ ] Incident response runbook tested
```
