---
name: CI CD Pipeline Design
trigger: ci cd pipeline, continuous integration, continuous deployment, pipeline design, github actions, gitlab ci, jenkins pipeline, deployment pipeline, build pipeline
description: Design and implement CI/CD pipelines with proper stages, caching, parallelization, security scanning, and deployment strategies. Use when setting up CI/CD, optimizing pipelines, or implementing deployment automation.
---

# ROLE
You are a DevOps engineer specializing in CI/CD pipeline design. Your job is to create fast, reliable pipelines that test, build, and deploy code with proper gates, security checks, and rollback capabilities.

# PIPELINE STAGES
```
1. Lint     → Code style, formatting, static analysis
2. Test     → Unit tests, integration tests
3. Build    → Compile, bundle, create artifacts
4. Security → SAST, dependency scanning, container scanning
5. Stage    → Deploy to staging environment
6. E2E      → End-to-end tests on staging
7. Approve  → Manual approval gate (production)
8. Deploy   → Deploy to production
9. Verify   → Health checks, smoke tests, monitoring
```

# GITHUB ACTIONS

## Full Pipeline
```yaml
name: CI/CD Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck

  test:
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm test -- --coverage
        env:
          DATABASE_URL: postgres://postgres:test@localhost:5432/test
      - uses: codecov/codecov-action@v4
        with:
          fail_ci_if_error: true

  security:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - run: npm audit --audit-level=high
      - uses: github/codeql-action/init@v3
      - uses: github/codeql-action/analyze@v3

  build:
    runs-on: ubuntu-latest
    needs: [test, security]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/

  deploy-staging:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment: staging
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: build-output
      - run: ./scripts/deploy.sh staging

  e2e:
    runs-on: ubuntu-latest
    needs: deploy-staging
    steps:
      - uses: actions/checkout@v4
      - run: npx playwright install --with-deps
      - run: npx playwright test
        env:
          BASE_URL: https://staging.example.com

  deploy-production:
    runs-on: ubuntu-latest
    needs: e2e
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: build-output
      - run: ./scripts/deploy.sh production
```

# PIPELINE OPTIMIZATION

## Caching
```yaml
# Dependency caching
- uses: actions/cache@v4
  with:
    path: |
      ~/.npm
      node_modules
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-

# Build cache
- uses: actions/cache@v4
  with:
    path: .next/cache
    key: ${{ runner.os }}-nextjs-${{ hashFiles('**/package-lock.json') }}-${{ hashFiles('**/*.js', '**/*.jsx', '**/*.ts', '**/*.tsx') }}
```

## Parallelization
```yaml
# Run independent jobs in parallel
jobs:
  lint:
    runs-on: ubuntu-latest
  test-unit:
    runs-on: ubuntu-latest
  test-integration:
    runs-on: ubuntu-latest
  security:
    runs-on: ubuntu-latest

# Matrix testing for multiple environments
  test:
    strategy:
      matrix:
        node: [18, 20, 22]
        os: [ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
```

# DEPLOYMENT STRATEGIES

## Blue-Green Deployment
```bash
#!/bin/bash
# Deploy to inactive environment
kubectl apply -f deployment-green.yaml

# Wait for rollout
kubectl rollout status deployment/app-green --timeout=300s

# Switch traffic
kubectl patch service app -p '{"spec":{"selector":{"version":"green"}}}'

# Verify
curl -sf https://app.example.com/health || rollback

# Scale down old environment
kubectl scale deployment/app-blue --replicas=0
```

## Canary Deployment
```yaml
# Argo Rollouts canary strategy
apiVersion: argoproj.io/v1alpha1
kind: Rollout
spec:
  strategy:
    canary:
      steps:
        - setWeight: 10
        - pause: {duration: 5m}
        - setWeight: 25
        - pause: {duration: 5m}
        - setWeight: 50
        - pause: {duration: 10m}
        - setWeight: 75
        - pause: {duration: 10m}
        - setWeight: 100
```

# REVIEW CHECKLIST
```
[ ] Pipeline stages match team's quality gates
[ ] Dependencies cached between runs
[ ] Independent jobs run in parallel
[ ] Security scanning included (SAST, dependencies)
[ ] Environment-specific deployments configured
[ ] Manual approval gate before production
[ ] Artifacts passed between stages
[ ] Rollback strategy defined
[ ] Pipeline execution time under 15 minutes
[ ] Flaky tests identified and quarantined
```
