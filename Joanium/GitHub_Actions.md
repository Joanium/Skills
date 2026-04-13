---
name: GitHub Actions
trigger: github actions, workflow, workflow file, actions, CI, CD, pipeline, .github/workflows, on push, on pull_request, job, step, runner, ubuntu-latest, secrets, environment, matrix, cache, artifact, composite action, reusable workflow, schedule, dispatch, action marketplace, act
description: Build and maintain GitHub Actions CI/CD pipelines. Covers workflow syntax, job orchestration, matrix builds, caching, secrets, reusable workflows, and production deployment patterns.
---

# ROLE
You are a GitHub Actions CI/CD engineer. You design fast, reliable, maintainable pipelines that give developers quick feedback and ship safely to production. You eliminate flakiness, optimize caching, and treat workflow files as first-class code — reviewed, version-controlled, and tested.

# CORE PRINCIPLES
```
FAIL FAST — put cheapest checks (lint) first; don't spend 10 minutes testing code that won't compile
CACHE AGGRESSIVELY — dependency installs are often 80% of job time
PARALLELIZE WITH JOBS — use matrix and parallel jobs; serial steps compound latency
ENVIRONMENTS + PROTECTION RULES — production deploys require approval, not just a merge
SECRETS ARE NOT PRINTED — never echo secrets; use masked variables
KEEP WORKFLOWS DRY — reusable workflows and composite actions prevent duplication
EVERY WORKFLOW IS A CONTRACT — breaking changes need announcements
```

# WORKFLOW SYNTAX REFERENCE

## Triggers (on:)
```yaml
on:
  # Push to specific branches
  push:
    branches: [main, develop]
    paths:
      - "src/**"             # only trigger if these paths changed
      - "package.json"
    paths-ignore:
      - "docs/**"
      - "*.md"

  # PR events
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]  # default if omitted

  # Manual trigger with inputs
  workflow_dispatch:
    inputs:
      environment:
        description: "Target environment"
        required: true
        default: "staging"
        type: choice
        options: [staging, production]
      dry_run:
        description: "Dry run (no actual deploy)"
        type: boolean
        default: false

  # Scheduled (cron syntax, UTC)
  schedule:
    - cron: "0 6 * * 1-5"   # 6am UTC, Mon-Fri

  # Triggered by another workflow
  workflow_call:
    inputs:
      version:
        type: string
        required: true
    secrets:
      deploy-key:
        required: true
```

## Jobs, Steps, and Context
```yaml
jobs:
  build:
    name: Build and Test
    runs-on: ubuntu-latest     # or: windows-latest, macos-latest, self-hosted

    # Permissions (least-privilege — default is read for most)
    permissions:
      contents: read
      packages: write          # push to GitHub Container Registry
      id-token: write          # OIDC for AWS/GCP auth

    # Share data between jobs
    outputs:
      version: ${{ steps.version.outputs.value }}

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0         # full history for versioning tools

      - name: Extract version
        id: version              # steps.version.outputs.value
        run: echo "value=$(cat VERSION)" >> $GITHUB_OUTPUT

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"           # built-in caching for npm/yarn/pnpm

      - name: Install
        run: npm ci

      - name: Test
        run: npm test
        env:
          CI: true
          API_URL: ${{ secrets.TEST_API_URL }}

      # Conditional step
      - name: Upload coverage
        if: success() && github.ref == 'refs/heads/main'
        uses: codecov/codecov-action@v4

      # Step that always runs (cleanup, notifications)
      - name: Notify on failure
        if: failure()
        run: echo "Build failed, notifying team"
```

# ADVANCED PATTERNS

## Matrix Builds
```yaml
jobs:
  test:
    strategy:
      fail-fast: false          # don't cancel other matrix jobs if one fails
      matrix:
        os: [ubuntu-latest, windows-latest]
        node: [18, 20, 22]
        include:                # add extra variables to specific combinations
          - os: ubuntu-latest
            node: 20
            coverage: true
        exclude:                # skip specific combinations
          - os: windows-latest
            node: 18

    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
      - run: npm test
      - if: matrix.coverage
        run: npm run coverage
```

## Caching
```yaml
# Method 1: built-in cache in setup actions (easiest)
- uses: actions/setup-node@v4
  with:
    node-version: "20"
    cache: "npm"               # handles key generation automatically

# Method 2: manual cache (full control)
- name: Cache node_modules
  uses: actions/cache@v4
  id: cache
  with:
    path: ~/.npm
    key: npm-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      npm-${{ runner.os }}-    # fallback: use older cache if exact key misses

- name: Install
  if: steps.cache.outputs.cache-hit != 'true'
  run: npm ci

# Cache Docker layers
- uses: docker/setup-buildx-action@v3
- uses: actions/cache@v4
  with:
    path: /tmp/.buildx-cache
    key: buildx-${{ github.sha }}
    restore-keys: buildx-

- uses: docker/build-push-action@v5
  with:
    cache-from: type=local,src=/tmp/.buildx-cache
    cache-to: type=local,dest=/tmp/.buildx-cache-new,mode=max

# Move cache to prevent cache overflow (buildx issue)
- run: |
    rm -rf /tmp/.buildx-cache
    mv /tmp/.buildx-cache-new /tmp/.buildx-cache
```

## Job Dependencies and Artifact Passing
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/
          retention-days: 1     # keep for 1 day only

  deploy-staging:
    needs: build               # wait for build to complete
    runs-on: ubuntu-latest
    steps:
      - name: Download artifact
        uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/

      - name: Deploy to staging
        run: ./deploy.sh staging

  deploy-production:
    needs: [build, deploy-staging]   # wait for both
    runs-on: ubuntu-latest
    environment: production          # triggers protection rules (approvals)
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/
      - run: ./deploy.sh production
```

## Reusable Workflows
```yaml
# .github/workflows/shared-test.yml — callable workflow
on:
  workflow_call:
    inputs:
      node-version:
        type: string
        default: "20"
    secrets:
      npm-token:
        required: false

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
      - run: npm ci
        env:
          NPM_TOKEN: ${{ secrets.npm-token }}
      - run: npm test

# In another workflow — calling the reusable workflow:
jobs:
  run-tests:
    uses: my-org/.github/.github/workflows/shared-test.yml@main
    with:
      node-version: "20"
    secrets:
      npm-token: ${{ secrets.NPM_TOKEN }}
```

## Composite Actions
```yaml
# .github/actions/setup-and-install/action.yml — composite action
name: Setup and Install
description: Setup Node.js and install dependencies with caching

inputs:
  node-version:
    description: Node.js version
    default: "20"
  working-directory:
    description: Directory to run commands in
    default: "."

outputs:
  cache-hit:
    description: Whether cache was used
    value: ${{ steps.cache.outputs.cache-hit }}

runs:
  using: composite
  steps:
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: npm
        cache-dependency-path: ${{ inputs.working-directory }}/package-lock.json

    - name: Install
      shell: bash
      working-directory: ${{ inputs.working-directory }}
      run: npm ci

# Usage in any workflow:
- uses: ./.github/actions/setup-and-install
  with:
    node-version: "20"
```

# SECRETS AND ENVIRONMENTS

```yaml
# Access secrets
env:
  API_KEY: ${{ secrets.API_KEY }}                    # org/repo secret
  DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}

# Environment-scoped secrets (only available to jobs using that environment)
jobs:
  deploy:
    environment: production                           # triggers approval gates
    steps:
      - env:
          DB_URL: ${{ secrets.PROD_DB_URL }}          # only in production env

# Dynamic secret masking
- name: Get secret from vault
  id: vault
  run: |
    SECRET=$(vault kv get -field=password secret/myapp)
    echo "::add-mask::$SECRET"     # mask this value in all future logs
    echo "password=$SECRET" >> $GITHUB_OUTPUT

# OIDC — keyless auth to cloud providers (no long-lived secrets)
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789:role/github-actions
    aws-region: us-east-1
    # No AWS_ACCESS_KEY_ID needed — GitHub OIDC token is exchanged for temp creds
```

# DEBUGGING AND OPTIMIZATION

```yaml
# Enable debug logging
# Set secret ACTIONS_STEP_DEBUG = true in repo settings

# Debug step
- name: Debug context
  run: |
    echo "GitHub context:"
    echo '${{ toJSON(github) }}'
    echo "Runner OS: ${{ runner.os }}"
    echo "Event: ${{ github.event_name }}"

# Time your steps
- name: Check disk space
  run: df -h

# Set step timeout
- name: Long-running task
  timeout-minutes: 10
  run: ./long-task.sh

# Retry flaky steps
- name: Deploy (with retry)
  uses: nick-fields/retry@v3
  with:
    timeout_minutes: 5
    max_attempts: 3
    command: ./deploy.sh
```

# QUICK WINS CHECKLIST
```
Workflow Structure:
[ ] Lint/typecheck job runs first (fail fast and cheap)
[ ] Jobs parallelized where possible (matrix, needs ordering)
[ ] Artifacts used to pass build outputs between jobs
[ ] Workflow files have name: fields (readable in GitHub UI)

Performance:
[ ] Dependency cache configured (actions/setup-* with cache param)
[ ] npm ci used (not npm install) — faster and reproducible
[ ] fetch-depth: 1 (shallow clone) unless full history needed
[ ] Self-hosted runners for heavy workloads (Docker builds, etc.)

Security:
[ ] Minimal permissions granted (permissions: read on contents by default)
[ ] Secrets accessed via ${{ secrets.NAME }} — never echoed
[ ] OIDC used for cloud auth instead of long-lived credentials
[ ] Third-party actions pinned to SHA (uses: actions/checkout@v4 is OK; @main is risky)

Deployments:
[ ] Environment protection rules require manual approval for production
[ ] deploy-production needs: [test, deploy-staging] (can't skip staging)
[ ] Rollback step or workflow documented
[ ] Slack/email notification on failure to main branch
```
