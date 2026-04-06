---
name: Dependency Management
trigger: update dependencies, dependency management, npm audit, outdated packages, security vulnerability dependency, upgrade packages, dependency update, lock file, package security, dependabot, renovate, third party packages, supply chain
description: Strategically manage third-party dependencies — auditing security vulnerabilities, planning upgrades, reducing dependency risk, and automating update workflows. Use when auditing packages, planning a major version upgrade, or setting up automated dependency management.
---

Every dependency is a trust decision. You're inviting someone else's code — and everyone they've invited — into your production system. Most of the time it's fine. Sometimes it isn't. Good dependency management is the difference between discovering a vulnerability in your security review and discovering it in a breach report.

## Audit: Know What You Have

### npm / Node.js
```bash
# See what's outdated
npm outdated

# Audit for known vulnerabilities
npm audit

# Audit with JSON output (for scripting / CI)
npm audit --json

# Fix automatically (patch and minor only — be careful)
npm audit fix

# Show dependency tree (who's bringing in that package?)
npm ls lodash
npx depcheck  # finds unused dependencies
```

### Python
```bash
pip list --outdated
pip-audit  # like npm audit for Python (pip install pip-audit)
safety check  # alternative (pip install safety)
```

### Ruby
```bash
bundle outdated
bundle audit  # gem install bundler-audit
```

### Go
```bash
go list -u -m all  # outdated modules
govulncheck ./...   # official vulnerability scanner
```

## Risk-Stratifying Your Dependencies

Not all dependencies are equal. Build a mental model:

```
CRITICAL (break glass if compromised):
- Authentication libraries (passport, jsonwebtoken, bcrypt)
- Encryption / TLS libraries
- Database drivers
- Payment SDK
- Any package with production secrets access

HIGH (patch within 48h of critical CVE):
- Web framework (express, fastapi, rails)
- ORM / query builder
- Session management
- File upload / parsing libraries (multer, busboy)
- XML/YAML/HTML parsers (historically risky)

MEDIUM (patch in next sprint):
- Utility libraries with network access
- Logging frameworks
- Serialization / deserialization libraries
- Date/time libraries

LOW (update quarterly):
- Dev dependencies (jest, eslint, prettier)
- Type definitions (@types/*)
- Build tools (webpack, vite, esbuild)
```

## Evaluating a New Dependency

Before adding a package, answer these questions:

```
Health signals:
☐ Downloads/week: > 100K for production use (not toy)
☐ Last published: within the last 6 months (maintained?)
☐ Open issues: are critical bugs being addressed?
☐ Stars: community signal — but not definitive
☐ License: compatible with your project? (MIT/Apache = fine, GPL = careful)

Security signals:
☐ npm audit / pip-audit: any existing CVEs?
☐ Author: who published it? reputable maintainer or individual?
☐ Install scripts: does the package run scripts on install? (red flag)
☐ Published on npm: matches GitHub source? (run npx npq <package>)

Size and scope:
☐ Bundle size: check bundlephobia.com for JS packages
☐ Dependencies: how many transitive dependencies does it pull in?
☐ Does this package do ONE thing you could write in < 50 lines?
  → If yes, consider writing it yourself instead (zero deps = zero risk)

The "left-pad test":
☐ If this package disappeared tomorrow, what would break?
☐ Is there a fallback or alternative ready?
```

### The "do I really need this?" rule
```javascript
// Before adding a package, check:
// Is this 50 lines of code? Write it yourself.
// Does it have > 10 transitive dependencies? Reconsider.
// Is it owned by a single unknown maintainer? Proceed carefully.

// Famous examples that should be local code:
// - is-odd / is-even (1 line of math)
// - left-pad (one Array.join call)
// - pad-left (same)

// Packages worth their dependencies:
// - zod (validation — complex to get right)
// - date-fns (dates — genuinely hard)
// - axios (HTTP — cross-browser/node normalization)
```

## Upgrade Strategy

### The spectrum of upgrade risk
```
Patch (1.0.X → 1.0.Y): Bug fixes, usually safe
Minor (1.X.0 → 1.Y.0): New features, backward-compatible (mostly)
Major (X.0.0 → Y.0.0): Breaking changes guaranteed, plan carefully
```

### Batch update workflow
```bash
# Step 1: See what can be updated
npm outdated

# Step 2: Update patch and minor versions automatically
npx npm-check-updates -u --target minor
npm install

# Step 3: Run full test suite
npm test

# Step 4: Major versions — one at a time, with a PR per package
npx npm-check-updates -u --filter react
npm install
# Read the changelog! Every major version.
npm test
git commit -m "chore: upgrade react 17 → 18"
```

### The CHANGELOG rule
Before any major version upgrade, read the CHANGELOG or MIGRATION GUIDE. Don't skip this. The 10 minutes you spend reading saves hours of debugging.

```bash
# Find the changelog
# GitHub: /releases or CHANGELOG.md
# npm: npmjs.com/package/<name>

# For React 18 specifically:
# https://react.dev/blog/2022/03/29/react-v18

# Check for breaking changes that affect your usage patterns, not all of them
```

## Automating Dependency Updates

### Renovate (recommended over Dependabot for teams)
```json
// renovate.json — put in repo root
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  
  // Group all patch updates into one weekly PR
  "packageRules": [
    {
      "matchUpdateTypes": ["patch"],
      "groupName": "all patch dependencies",
      "schedule": ["before 6am on Monday"]
    },
    {
      "matchUpdateTypes": ["minor"],
      "groupName": "all minor dependencies",
      "schedule": ["before 6am on first day of the month"]
    },
    {
      "matchPackageNames": ["react", "react-dom", "next"],
      "groupName": "React ecosystem",
      "reviewers": ["team:frontend"]
    }
  ],
  
  // Auto-merge patch updates that pass CI
  "automerge": true,
  "automergeType": "pr",
  "automergeStrategy": "squash",
  "matchUpdateTypes": ["patch"],
  
  // Security updates — always urgent
  "vulnerabilityAlerts": {
    "labels": ["security"],
    "assignees": ["security-team"]
  }
}
```

### Dependabot (GitHub native, simpler)
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    groups:
      dev-dependencies:
        patterns: ["eslint*", "prettier*", "@types/*", "jest*"]
      production-dependencies:
        update-types:
          - "minor"
          - "patch"
    ignore:
      - dependency-name: "aws-sdk"  # pinned intentionally
        versions: ["*"]
```

## Lock Files — Non-Negotiable Rules

```
ALWAYS commit lock files. No exceptions.
- package-lock.json  (npm)
- yarn.lock          (Yarn)
- pnpm-lock.yaml     (pnpm)
- Pipfile.lock       (Python Pipenv)
- poetry.lock        (Python Poetry)
- Gemfile.lock       (Ruby)
- go.sum             (Go)

Why: Lock files guarantee everyone on the team — and CI — installs 
the exact same versions. Without them, "works on my machine" becomes 
a regular occurrence.

NEVER commit node_modules / vendor directories.
```

## Security Vulnerability Response

When a critical CVE drops for a package you use:

```
Hour 0: Triage
  1. Read the CVE — is your usage pattern actually affected?
  2. Is there a patched version available?
  3. Is there a workaround until you can patch?

Hour 1-4 (critical CVE in production code):
  1. Update to patched version
  2. Run full test suite
  3. Deploy to staging, verify
  4. Deploy to production
  5. Confirm with npm audit / pip-audit: no critical vulns remaining

Day 1-3 (high CVE):
  Same process, but scheduled as next-day urgent work

Next sprint (medium/low CVE):
  Add to normal dependency update batch
```

## Dependency Management Checklist

```
Weekly/automated:
☐ Dependabot / Renovate PRs reviewed and merged (patch)
☐ npm audit / pip-audit passes with no critical/high CVEs

Monthly:
☐ Minor version updates reviewed and merged in batch
☐ Unused dependencies removed (npx depcheck)
☐ New packages added this month reviewed for health/security

Quarterly:
☐ Major version upgrades planned on the roadmap
☐ Transitive dependency tree reviewed for surprises
☐ License audit for new packages

Before any new production dependency:
☐ Evaluated the "do I need this?" checklist above
☐ Checked downloads, maintenance, license, and vulnerabilities
☐ Considered writing it locally if it's < 50 lines
☐ Added to the high/critical watch list if it has system access
```
