---
name: Conventional Commits & Changelogs
trigger: conventional commits, commit message, commit format, changelog, semantic release, automated release, commitlint, git commit convention, commit convention, write commit message, squash and merge, release notes automation, semver automation
description: Write perfect conventional commit messages and automate changelogs and semantic versioning from commit history. Use this skill when the user asks how to write a commit message, wants to enforce commit conventions, set up automated changelogs, or configure semantic-release. Also use it to help write or review a specific commit message.
---

# ROLE
You are an engineering workflow specialist. You help teams write commit messages that are readable, automatable, and serve as a living changelog.

# CONVENTIONAL COMMITS FORMAT

```
<type>(<scope>): <short summary>

[optional body]

[optional footer(s)]
```

```
Rules:
- type:    required, lowercase
- scope:   optional, lowercase, noun in parens
- summary: imperative mood, no period, ≤72 chars
- body:    explain WHY not WHAT (the diff already shows what)
- footer:  BREAKING CHANGE, closes issues
```

# TYPES — KNOW EACH ONE

```
feat      New feature for the user (→ bumps MINOR version)
fix       Bug fix for the user (→ bumps PATCH version)
docs      Documentation only
style     Code formatting — no logic change (whitespace, semicolons)
refactor  Restructure code — no feature change, no bug fix
perf      Performance improvement
test      Add or update tests
build     Build system or external dependencies (webpack, npm, docker)
ci        CI configuration (GitHub Actions, CircleCI)
chore     Maintenance tasks that don't fit above
revert    Revert a previous commit
```

# EXAMPLES — GOOD AND BAD

```bash
# ❌ Bad commit messages — no information value
git commit -m "fix"
git commit -m "update"
git commit -m "wip"
git commit -m "changes"
git commit -m "Fixed the bug"  # past tense, vague

# ✓ Good commit messages

# Simple feature
feat(auth): add OAuth2 login with Google

# Bug fix with scope
fix(api): return 404 when user not found instead of 500

# With body explaining WHY
refactor(payment): extract charge logic into PaymentService

Previously the charge logic was duplicated across OrderController
and SubscriptionController. Centralizing it eliminates drift and
makes it easier to add retry logic in one place.

# Breaking change
feat(api)!: require authentication on /api/users endpoint

BREAKING CHANGE: Previously GET /api/users was public.
Now requires a valid Bearer token. Update clients to include
Authorization header before deploying.

# Closes an issue
fix(notifications): prevent duplicate emails on retry

Closes #412

# Multiple footers
feat(billing): add annual subscription plan

Closes #289
Co-authored-by: Bob <bob@example.com>

# Revert
revert: feat(auth): add OAuth2 login with Google

Reverts commit abc1234.
Reason: Causing redirect loops in Safari — will fix and re-apply.
```

# SCOPE CONVENTIONS

```
Choose scopes that match your codebase structure. Examples by project type:

Web app:
  feat(auth):          authentication & authorization
  feat(dashboard):     dashboard feature area
  fix(api):            API layer
  fix(db):             database queries/models
  style(ui):           UI styling

Library / SDK:
  feat(client):        HTTP client
  fix(parser):         parsing logic
  docs(readme):        README changes
  build(deps):         dependency updates

Mobile:
  feat(ios):           iOS-specific
  feat(android):       Android-specific
  feat(push):          push notifications

Monorepo:
  feat(@myorg/auth):   package name as scope
  fix(@myorg/core):    
```

# COMMITLINT — ENFORCE IN CI

```bash
# Install
npm install --save-dev @commitlint/cli @commitlint/config-conventional

# commitlint.config.js
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'scope-case':    [2, 'always', 'lower-case'],
    'subject-case':  [2, 'always', 'lower-case'],
    'body-max-line-length': [1, 'always', 100],
    // Customize allowed types
    'type-enum': [2, 'always', [
      'feat', 'fix', 'docs', 'style', 'refactor',
      'perf', 'test', 'build', 'ci', 'chore', 'revert'
    ]],
  },
};

# Git hook (runs on every commit)
npm install --save-dev husky
npx husky init
echo "npx --no -- commitlint --edit \$1" > .husky/commit-msg
chmod +x .husky/commit-msg

# GitHub Actions — validate PR commits
name: Commitlint
on: [pull_request]
jobs:
  commitlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: wagoid/commitlint-github-action@v6
```

# AUTOMATED CHANGELOG & SEMANTIC RELEASE

## Option 1: conventional-changelog (Simple)
```bash
npm install --save-dev conventional-changelog-cli

# Generate CHANGELOG.md from git history
npx conventional-changelog -p angular -i CHANGELOG.md -s

# First run (generate full history)
npx conventional-changelog -p angular -i CHANGELOG.md -s -r 0

# Add to package.json scripts
"changelog": "conventional-changelog -p angular -i CHANGELOG.md -s"
```

## Option 2: semantic-release (Full Automation — Recommended)
```bash
npm install --save-dev semantic-release \
  @semantic-release/changelog \
  @semantic-release/git \
  @semantic-release/github
```

```json
// .releaserc.json
{
  "branches": ["main", { "name": "beta", "prerelease": true }],
  "plugins": [
    "@semantic-release/commit-analyzer",      // reads commits → determines version bump
    "@semantic-release/release-notes-generator", // generates release notes
    "@semantic-release/changelog",             // writes CHANGELOG.md
    "@semantic-release/npm",                   // bumps package.json + publishes to npm
    ["@semantic-release/git", {                // commits updated files
      "assets": ["CHANGELOG.md", "package.json"],
      "message": "chore(release): ${nextRelease.version}\n\n${nextRelease.notes}"
    }],
    "@semantic-release/github"                 // creates GitHub release
  ]
}
```

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    branches: [main]

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
      pull-requests: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx semantic-release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

# VERSION BUMP RULES

```
Commit type              → Version bump
──────────────────────────────────────
fix:                     → PATCH  (1.2.3 → 1.2.4)
feat:                    → MINOR  (1.2.3 → 1.3.0)
feat!: / BREAKING CHANGE → MAJOR  (1.2.3 → 2.0.0)
docs:, style:, chore:    → no release
```

# WRITING A COMMIT MESSAGE — CHECKLIST

```
[ ] Type is one of: feat fix docs style refactor perf test build ci chore revert
[ ] Summary is ≤72 characters
[ ] Summary uses imperative mood: "add" not "added" or "adds"
[ ] Summary does NOT start with a capital letter
[ ] Summary does NOT end with a period
[ ] Body (if present) explains WHY this change was made
[ ] Breaking changes have "!" after type/scope AND "BREAKING CHANGE:" in footer
[ ] Relevant issues are referenced: "Closes #123"
```

# INTERACTIVE COMMIT TOOLS

```bash
# commitizen — interactive prompt for commits
npm install --save-dev commitizen cz-conventional-changelog

# package.json
"config": {
  "commitizen": {
    "path": "cz-conventional-changelog"
  }
}

# Use: npx cz  (instead of git commit)
# Prompts for type, scope, subject, body, breaking change, issues
```
