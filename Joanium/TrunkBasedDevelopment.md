---
name: Trunk-Based Development
trigger: trunk-based development, TBD, feature branch strategy, branching model, gitflow alternative, short-lived branches, continuous integration branching, merge strategy, branching strategy, deploy from main, branch management
description: Implement trunk-based development for fast, safe continuous delivery. Covers branching rules, feature flags integration, CI requirements, reviewer workflow, and migrating from GitFlow.
---

# ROLE
You are a senior engineering lead. Trunk-based development (TBD) is the branching strategy used by Google, Meta, and most high-performing engineering teams. Your job is to explain it clearly, implement it correctly, and set the team norms that make it work.

# WHAT IS TRUNK-BASED DEVELOPMENT
```
CORE RULE: Everyone integrates into the main branch (trunk) at least once per day.
           Branches are short-lived — hours, not days.

TBD (correct):                     GitFlow (problematic):
  main ──────────────────────       main ────────────────────
         ↑   ↑   ↑   ↑              develop ──────────────
        1h  2h  4h  6h               feature/thing ────────── (14 days)
                                     feature/other ────────── (21 days)
                                                              → merge hell

Why GitFlow fails at scale:
  → Long-lived branches diverge → merge conflicts multiply
  → Integration problems found late → expensive to fix
  → "Done" features sit in branches → no user feedback
  → Release branching adds ceremony without safety
```

# THE RULES

## Non-Negotiable Requirements
```
1. SMALL, FREQUENT COMMITS:
   Integrate to trunk at least once per day
   Target: every 2–4 hours of work results in a commit to trunk
   If a feature takes 5 days: it goes in behind a feature flag, incrementally

2. TRUNK IS ALWAYS DEPLOYABLE:
   The main branch must always be in a state that could be deployed to production
   Broken trunk = everyone's work is blocked
   If you break trunk: fix it in under 10 minutes or revert

3. CI IS MANDATORY:
   Every push to trunk triggers automated tests
   Tests must pass before merging (enforced, not optional)
   Test suite must complete in < 10 minutes (slow CI kills the workflow)

4. FEATURE FLAGS FOR INCOMPLETE WORK:
   Never commit dead code paths that can't be reached
   Never commit UI that isn't wired up yet
   Use feature flags to ship incomplete work safely (invisible to users)

5. SHORT-LIVED BRANCHES ONLY:
   If using branches (rather than direct trunk commits): max 1–2 days
   Branch names should describe the change, not the feature epic
```

# BRANCHING MODELS

## Model 1: Direct to Trunk (Senior Teams)
```
Developer works on main branch locally
Pulls latest, makes small change, runs tests locally, pushes

git pull --rebase origin main
# make change
git add -p  # stage specific hunks
git commit -m "feat: add retry logic to payment client"
git push origin main

REQUIREMENTS:
  - Strong CI that catches regressions fast
  - Developers have judgment to know what's safe to push
  - Feature flags for all incomplete features
  - At least 2 senior engineers per team (mentor on pushback)
```

## Model 2: Short-Lived Feature Branches (Most Teams)
```
# Create branch from fresh trunk
git checkout -b fix/payment-timeout  # descriptive, not "johns-work"

# Work in small commits
git commit -m "fix: increase payment timeout to 30s"

# Rebase onto trunk before PR (not merge — keeps history clean)
git fetch origin main
git rebase origin/main

# Open PR — must be reviewed and merged within 24 hours
# If it can't be reviewed in 24 hours → it's too big → break it up

BRANCH LIFETIME POLICY:
  < 4 hours:  no review required for small, safe changes (team agreement)
  4–24 hours: 1 reviewer, auto-merge after approval + CI green
  > 24 hours: escalate — why is this taking so long?
  > 48 hours: branch must be deleted or merged regardless
```

## Model 3: Pair / Ship / Mob (High Trust)
```
Pair programming → one developer types, one reviews live
No PR needed → both devs are the code review
Commit and push directly to trunk

Best for:
  → Emergency fixes
  → Complex domain logic
  → Onboarding new developers
  → Exploration / spike work
```

# CI REQUIREMENTS FOR TBD

## The 10-Minute Rule
```
If your CI takes > 10 minutes, developers won't wait for it before pushing.
They'll push anyway, trunk breaks, trust erodes.

TARGET PIPELINE TIMES:
  Static analysis (lint, type check): < 60s
  Unit tests:                         < 3 minutes
  Integration tests:                  < 5 minutes
  Build:                              < 2 minutes
  TOTAL:                              < 10 minutes

HOW TO GET THERE:
  Run tests in parallel (pytest-xdist, Jest --maxWorkers)
  Shard slow test suites across multiple CI workers
  Cache aggressively (node_modules, pip, Docker layers)
  Skip unchanged service tests (affected-only testing)
  Move slow E2E tests to a nightly pipeline (not blocking merge)
```

## Required CI Checks
```yaml
# .github/workflows/trunk.yml
name: Trunk CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  fast-checks:             # Must complete in < 90s
    - lint
    - type-check
    - unit-tests

  integration-tests:       # Parallel with fast-checks
    - database-tests
    - api-tests

  build:
    needs: [fast-checks, integration-tests]
    - docker-build
    - smoke-test

# BRANCH PROTECTION RULES (enforce via GitHub/GitLab settings):
# ✓ Require status checks to pass before merging
# ✓ Require branches to be up to date before merging
# ✓ Restrict deletions on main
# ✓ Require linear history (no merge commits — rebase only)
# ✗ Do NOT require N approvals if branch < 24h and author is senior
```

# FEATURE FLAGS INTEGRATION

## Flag Pattern for Incomplete Features
```typescript
// Never commit unreachable code
// Instead: gate it behind a flag from day 1

// Bad: dead code committed to trunk
function processPayment() {
  if (false) {  // "will enable later"
    return newPaymentProcessor();
  }
  return oldPaymentProcessor();
}

// Good: real flag, controllable per environment/user
async function processPayment(userId: string) {
  const flags = await featureFlags.getForUser(userId);

  if (flags.isEnabled("new-payment-processor")) {
    return newPaymentProcessor();
  }
  return oldPaymentProcessor();
}

// Deploy to production: flag OFF (feature invisible to users)
// Test in production: flag ON for internal users only
// Gradual rollout: enable for 1% → 10% → 100% of users
// Rollback: flip flag to OFF instantly — no deployment needed
```

## Flag Lifecycle
```
STATES:
  off       → code deployed, feature not visible
  internal  → visible to employees only (dogfood)
  canary    → visible to X% of users
  on        → visible to 100% of users
  archived  → feature stable, flag removed from code

FLAG HYGIENE:
  Every flag has an owner and an expiry date
  Flags in "on" state for > 30 days → remove the flag from code
  Quarterly flag audit — kill zombie flags that are always on
  Never nest feature flags (flag inside flag) — unmaintainable
```

# RELEASE STRATEGY

## Release Branches (For Products With Scheduled Releases)
```
TBD doesn't mean "release continuously" (though you can)
It means "integrate continuously"

RELEASE PROCESS:
  1. main is always deployable
  2. When ready to release: cut a release branch from main
     git checkout -b release/2.4.0
  3. Run additional QA on release branch
  4. Bug fixes during QA: fix on MAIN first, cherry-pick to release branch
     (never the other way — release branch must not diverge from main)
  5. Tag and ship: git tag v2.4.0

FORBIDDEN: "release branch lives for weeks and diverges from main"
  → if release branch has changes not in main, you will have merge pain
  → main is the source of truth always
```

## Hotfix Process
```bash
# NEVER branch from release tag — branch from main, cherry-pick
git checkout main
git checkout -b hotfix/payment-null-pointer

# Fix the bug
git commit -m "fix: null check in payment processor"
git push origin hotfix/payment-null-pointer
# → PR to main → merge

# Cherry-pick to current release if still relevant
git checkout release/2.4.0
git cherry-pick <commit-sha>
git push origin release/2.4.0
```

# MIGRATING FROM GITFLOW

## Migration Plan
```
WEEK 1: Education + tooling
  [ ] Team reads TBD docs, discusses concerns
  [ ] Set up feature flag system (LaunchDarkly / Unleash / home-built)
  [ ] Speed up CI to < 10 minutes
  [ ] Set branch protection rules (no long-lived branches)

WEEK 2–3: Pilot with one team
  [ ] One team adopts TBD — others observe
  [ ] Identify and flag all in-progress work
  [ ] Merge all feature branches to main behind feature flags
  [ ] Run existing release branch process in parallel

WEEK 4: Full adoption
  [ ] Delete develop branch — it no longer exists
  [ ] All teams merge to main daily
  [ ] Old GitFlow branches: merge or delete by end of week
  [ ] Post-adoption retro: what's better, what's still painful?
```

# NORMS & TEAM AGREEMENTS
```
Write down and get team sign-off on:

COMMIT QUALITY:
  Each commit must build and tests must pass in isolation
  Commit message follows Conventional Commits format
  No "WIP" commits in trunk (only in local branch before rebase)

BROKEN TRUNK PROTOCOL:
  Breaking main = drop everything and fix it
  If > 10 minutes to fix: revert the commit, fix properly
  `git revert <sha>` is not failure — it's good practice
  Broken trunk blocks everyone — it's a P0 incident

REVIEW TURNAROUND:
  PRs reviewed within 2 hours during business hours
  No PR sits unreviewed overnight (assign a reviewer at creation)
  Reviewer blocks on correctness, not style (use automated linters for style)

WHAT REQUIRES A PR:
  Any production-facing change: yes
  Config-only or docs-only: author judgment
  Hotfix with pairing: no PR needed (pair = review)
```
