---
name: GitHub Actions CI/CD
trigger: github actions, workflow yaml, ci pipeline, github workflow, actions runner, on push, on pull_request, workflow dispatch, github secrets, matrix build, deploy action, build and test, actions job steps
description: Write robust GitHub Actions workflows for CI/CD — covering test pipelines, build matrices, Docker builds, deployments, secrets management, reusable workflows, and caching strategies.
---

# ROLE
You are a senior DevOps engineer who writes GitHub Actions workflows that are fast, reliable, secure, and easy to debug. You treat CI pipelines as production code.

# CORE CONCEPTS
```
WORKFLOW:    YAML file in .github/workflows/ — triggered by events
JOB:         Unit of work that runs on a runner (can run in parallel or sequence)
STEP:        Individual task within a job — shell command or action
ACTION:      Reusable step — from marketplace or local ./action.yml
RUNNER:      VM that executes a job — ubuntu-latest, windows-latest, macos-latest
SECRET:      Encrypted variable stored in repo/org settings
CONTEXT:     Objects with info — github, env, secrets, steps, runner, matrix
```

# WORKFLOW TRIGGERS
```yaml
on:
  push:
    branches: [main, develop]
    paths:
      - 'src/**'          # only run if src/ changed
      - 'package.json'
    paths-ignore:
      - '**.md'           # skip if only markdown changed

  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]

  release:
    types: [published]    # fires when a release is published

  workflow_dispatch:      # manual trigger via GitHub UI
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'staging'
        type: choice
        options: [staging, production]

  schedule:
    - cron: '0 2 * * 1'  # every Monday at 2am UTC (dependency audit, etc.)
```

# FULL NODE.JS CI PIPELINE
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'

jobs:
  test:
    name: Test (${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false      # don't cancel other matrix jobs on failure
      matrix:
        os: [ubuntu-latest, windows-latest]

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'          # cache node_modules between runs

      - name: Install dependencies
        run: npm ci             # always ci, never install in pipelines

      - name: Lint
        run: npm run lint

      - name: Type check
        run: npm run typecheck

      - name: Unit tests
        run: npm run test -- --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        if: matrix.os == 'ubuntu-latest'   # upload once, not from every OS
        with:
          token: ${{ secrets.CODECOV_TOKEN }}

  build:
    name: Build
    runs-on: ubuntu-latest
    needs: test            # only runs if test job succeeds

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - run: npm ci
      - run: npm run build

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
          retention-days: 7
```

# DOCKER BUILD + PUSH
```yaml
  docker:
    name: Docker Build & Push
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'    # only on main branch

    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}    # built-in, no setup needed

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=sha,prefix=sha-
            type=semver,pattern={{version}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha            # GitHub Actions cache
          cache-to: type=gha,mode=max
```

# DEPLOYMENT WORKFLOW
```yaml
  deploy:
    name: Deploy to ${{ inputs.environment || 'staging' }}
    runs-on: ubuntu-latest
    needs: docker
    environment:
      name: ${{ inputs.environment || 'staging' }}
      url: https://${{ inputs.environment || 'staging' }}.myapp.com

    steps:
      - name: Download artifact
        uses: actions/download-artifact@v4
        with:
          name: dist

      - name: Deploy to server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_SSH_KEY }}
          script: |
            cd /app
            docker pull ghcr.io/${{ github.repository }}:sha-${{ github.sha }}
            docker-compose up -d --no-deps app
```

# SECRETS MANAGEMENT
```yaml
# Access secrets
steps:
  - name: Use secret
    env:
      API_KEY: ${{ secrets.API_KEY }}       # from repo/org settings
      DB_PASS: ${{ secrets.DB_PASSWORD }}
    run: ./deploy.sh

# GITHUB_TOKEN — built-in, no setup, scoped to the repo
- name: Create release
  uses: softprops/action-gh-release@v1
  with:
    token: ${{ secrets.GITHUB_TOKEN }}

# Pass secrets to reusable workflows
uses: ./.github/workflows/deploy.yml
secrets:
  DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
# OR pass all secrets:
secrets: inherit
```

# REUSABLE WORKFLOWS
```yaml
# .github/workflows/reusable-test.yml
on:
  workflow_call:
    inputs:
      node-version:
        required: false
        type: string
        default: '20'
    secrets:
      NPM_TOKEN:
        required: true

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
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
      - run: npm test

# Caller workflow
jobs:
  call-test:
    uses: ./.github/workflows/reusable-test.yml
    with:
      node-version: '20'
    secrets:
      NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

# CACHING STRATEGIES
```yaml
# npm
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
    restore-keys: ${{ runner.os }}-npm-

# pip (Python)
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements*.txt') }}

# Gradle (Java)
- uses: actions/cache@v4
  with:
    path: |
      ~/.gradle/caches
      ~/.gradle/wrapper
    key: ${{ runner.os }}-gradle-${{ hashFiles('**/*.gradle*') }}

# Build output — share between jobs
- uses: actions/upload-artifact@v4
  with:
    name: build-output
    path: dist/

- uses: actions/download-artifact@v4
  with:
    name: build-output
    path: dist/
```

# CONCURRENCY — Prevent Redundant Runs
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true   # cancel previous run on same branch/PR when new push arrives
```

# CONDITIONALS
```yaml
# Run step only on failure
- name: Notify Slack on failure
  if: failure()
  uses: slackapi/slack-github-action@v1.26.0
  with:
    payload: '{"text": "Build failed on ${{ github.ref }}"}'
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}

# Skip draft PRs
- name: Run tests
  if: github.event.pull_request.draft == false

# Only on specific branch
- name: Deploy
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'

# Continue even if step fails
- name: Run optional step
  continue-on-error: true
  run: npm run optional-check
```

# SECURITY BEST PRACTICES
```yaml
# Permissions — always specify minimal required
permissions:
  contents: read
  packages: write
  pull-requests: write

# Pin action versions to SHA (not tag — tags can be moved)
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2

# Never print secrets
- run: echo "${{ secrets.API_KEY }}"   # ✗ — will be masked but still bad practice

# Use environment protection rules for production
environment:
  name: production    # requires approval in GitHub settings

# Dependabot for action version updates
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

# COMMON MISTAKES TO AVOID
```
✗ Using npm install instead of npm ci in CI — install mutates lockfile
✗ Hardcoding secrets in YAML — always use ${{ secrets.NAME }}
✗ No concurrency group — runs pile up on fast push branches
✗ Using latest tags for actions — pin to SHA for reproducibility
✗ Running all jobs sequentially — use needs: to express real dependencies
✗ No artifact retention — set retention-days to avoid bloating storage
✗ Downloading artifacts in every job — share only what's needed
✗ Skipping fail-fast: false on matrix — investigate all platform failures
```
