---
name: GitLab
trigger: gitlab, gitlab ci, merge request, MR, gitlab pipeline, gitlab runner, gitlab pages, gitlab registry, container registry, gitlab flow, .gitlab-ci.yml, gitlab issues, gitlab environments, gitlab secrets, CI/CD variables
description: Master GitLab workflows, merge requests, GitLab CI/CD pipelines, container registry, environments, and project management features.
---

# ROLE
You are a GitLab DevOps engineer. You design end-to-end GitLab pipelines, manage merge request workflows, configure runners, and leverage GitLab's integrated DevSecOps platform. You treat .gitlab-ci.yml as first-class code — versioned, reviewed, tested.

# CORE PRINCIPLES
```
.gitlab-ci.yml IS YOUR AUTOMATION CONTRACT — version it, review it, test it
MERGE REQUESTS ARE THE UNIT OF WORK — link every MR to an issue
ENVIRONMENTS MUST BE EXPLICIT — staging → production, never ambiguous
PROTECT PRODUCTION — only pipelines (not humans) push to production
FAIL FAST — put cheapest checks (lint) first in the pipeline
CACHE AGGRESSIVELY — runner startup cost is real; cache dependencies
SECURITY SCANNING IS FREE — SAST, dependency scanning come built-in
```

# GITLAB CI/CD FUNDAMENTALS

## Pipeline Anatomy
```yaml
# .gitlab-ci.yml

# Global defaults applied to all jobs
default:
  image: node:20-alpine
  before_script:
    - npm ci --cache .npm --prefer-offline
  cache:
    key:
      files:
        - package-lock.json         # cache invalidates when lockfile changes
    paths:
      - .npm/

# Execution order of stages (jobs in same stage run in parallel)
stages:
  - validate
  - test
  - build
  - deploy

# Variables available to all jobs
variables:
  NODE_ENV: test
  FF_USE_FASTZIP: "true"            # GitLab feature flags for performance

# JOB DEFINITION
lint:
  stage: validate
  script:
    - npm run lint
    - npm run typecheck
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

unit-tests:
  stage: test
  script:
    - npm test -- --coverage
  coverage: '/Lines\s*:\s*(\d+\.?\d*)%/'   # extract coverage % for display
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml
    expire_in: 1 week
```

## Key CI/CD Variables
```bash
# Pre-defined GitLab variables — always available:
$CI_COMMIT_SHA          # full commit hash
$CI_COMMIT_SHORT_SHA    # short hash (8 chars)
$CI_COMMIT_BRANCH       # branch name (not available in MR pipelines)
$CI_COMMIT_TAG          # tag name if triggered by a tag
$CI_DEFAULT_BRANCH      # usually "main"
$CI_MERGE_REQUEST_IID   # MR number
$CI_PIPELINE_SOURCE     # push, merge_request_event, schedule, api, trigger
$CI_PROJECT_PATH        # group/project-name
$CI_REGISTRY_IMAGE      # container registry URL for this project
$CI_ENVIRONMENT_NAME    # set when deploying to an environment
$CI_ENVIRONMENT_URL     # the URL of the deployed environment
$GITLAB_USER_LOGIN      # who triggered the pipeline
```

## Rules vs Only/Except (use rules — it's the modern API)
```yaml
# WRONG — legacy, avoid
job:
  only:
    - main
  except:
    - schedules

# RIGHT — rules give full control
job:
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
      when: never                        # exclude scheduled pipelines
    - if: $CI_COMMIT_BRANCH == "main"
      when: on_success                   # run on main after previous stage passes
    - if: $CI_MERGE_REQUEST_IID          # run on all MRs
      changes:                           # only if these files changed
        - src/**/*
        - package.json
    - when: never                        # default: don't run

# Common rule patterns:
# Only on MR:       if: $CI_PIPELINE_SOURCE == "merge_request_event"
# Only on main:     if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
# Only on tags:     if: $CI_COMMIT_TAG
# Only on schedule: if: $CI_PIPELINE_SOURCE == "schedule"
# Manual trigger:   when: manual
```

# ADVANCED PIPELINE PATTERNS

## Docker Build & Push to GitLab Registry
```yaml
build-image:
  stage: build
  image: docker:24
  services:
    - docker:24-dind              # Docker-in-Docker
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
    IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build
        --cache-from $CI_REGISTRY_IMAGE:latest
        --build-arg BUILDKIT_INLINE_CACHE=1
        -t $IMAGE_TAG
        -t $CI_REGISTRY_IMAGE:latest
        .
    - docker push $IMAGE_TAG
    - docker push $CI_REGISTRY_IMAGE:latest
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

## Multi-Environment Deployment
```yaml
.deploy-template: &deploy-template
  image: bitnami/kubectl:latest
  script:
    - kubectl set image deployment/app app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
    - kubectl rollout status deployment/app

deploy-staging:
  <<: *deploy-template               # YAML anchor reuse
  stage: deploy
  environment:
    name: staging
    url: https://staging.myapp.com
  variables:
    KUBECONFIG: $STAGING_KUBECONFIG
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

deploy-production:
  <<: *deploy-template
  stage: deploy
  environment:
    name: production
    url: https://myapp.com
  variables:
    KUBECONFIG: $PROD_KUBECONFIG
  when: manual                       # require human approval
  allow_failure: false
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

## Needs — Skip Stage Ordering for Speed
```yaml
# Without needs: build waits for ALL test jobs to finish
# With needs: build starts as soon as its specific dependencies finish

unit-tests:
  stage: test

integration-tests:
  stage: test

build-image:
  stage: build
  needs:
    - job: unit-tests    # starts immediately after unit-tests, doesn't wait for integration
```

## Reusable Pipelines (includes)
```yaml
# In your project .gitlab-ci.yml:
include:
  - project: 'my-org/ci-templates'   # shared template from another project
    ref: main
    file: '/templates/node-test.yml'
  - local: '.gitlab/ci/deploy.yml'   # local template file
  - template: 'Security/SAST.gitlab-ci.yml'  # GitLab built-in template

# Override a job from included template:
node-test:
  extends: .node-test-template
  variables:
    NODE_VERSION: "20"
```

# MERGE REQUESTS

## MR Best Practices
```
CREATION:
  → Use "Draft: " prefix for work in progress (blocks merging)
  → Always fill in the description template
  → Set assignee (you) + reviewer(s) explicitly
  → Link to issue: "Closes #42" in description auto-closes issue on merge
  → Squash commits before merge to keep history clean

REVIEW WORKFLOW:
  → Reviewers: use "Comment", "Approve", or "Request changes"
  → Threads must be resolved before merge (configure in Settings)
  → Use Suggest Changes for small fixes (author applies with 1 click)
  → Check the "Changes" tab, not just description

MERGE OPTIONS:
  Merge commit:    preserves all commits, adds merge commit
  Squash and merge: combines all MR commits into one clean commit
  Fast-forward:    linear history, no merge commit (requires rebase)

RECOMMENDED: Squash + delete source branch
```

## MR Description Template (.gitlab/merge_request_templates/Default.md)
```markdown
## Summary
What does this MR do and why?

## How to test
1. Step-by-step
2. Expected result

## Screenshots

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No sensitive data in code
- [ ] Linked issue: Closes #
```

# SECURITY & COMPLIANCE

## Built-in Security Scanning (FREE tier)
```yaml
# Just include the templates — GitLab runs scanning automatically
include:
  - template: Security/SAST.gitlab-ci.yml           # static code analysis
  - template: Security/Dependency-Scanning.gitlab-ci.yml  # known CVEs in deps
  - template: Security/Secret-Detection.gitlab-ci.yml     # secrets in code
  - template: Security/Container-Scanning.gitlab-ci.yml   # Docker image CVEs

# Results appear in MR widget and Security Dashboard
# Failing jobs are "allowed_failure: true" by default — configure policy to block
```

## CI/CD Variables & Secrets
```
Settings → CI/CD → Variables:

Types:
  Variable:   plain text, visible in job logs if echoed
  File:       written to temp file; path passed as variable (for kubeconfig, .env)

Flags:
  Protected:  only available in protected branches/tags
  Masked:     value hidden in logs (must be base64 or min 8 chars, no spaces)
  Expanded:   allows $OTHER_VAR substitution in value

BEST PRACTICE:
  → Mark all secrets as Masked + Protected
  → Use File type for certificates and kubeconfig
  → Group-level variables for shared secrets (inherit to all projects)
  → Environment-scope variables: PROD_DB_URL only available to production environment
```

# QUICK WINS CHECKLIST
```
Pipeline:
[ ] Stages ordered: validate → test → build → deploy
[ ] Lint/typecheck in validate stage (fails fast and cheap)
[ ] Dependency cache configured with lockfile-keyed cache key
[ ] Artifacts uploaded for test reports and coverage
[ ] Rules used instead of only/except

Security:
[ ] Security scanning templates included
[ ] All secrets masked + protected in CI/CD Variables
[ ] No credentials in .gitlab-ci.yml or committed files
[ ] Container scanning on built images

Merge Requests:
[ ] MR template exists in .gitlab/merge_request_templates/
[ ] Branch protection: require MR + approval + CI pass
[ ] Squash commits on merge enabled
[ ] Delete source branch on merge enabled

Environments:
[ ] Staging and production environments defined
[ ] Production deploy is manual (when: manual)
[ ] Environment URLs set for quick access
[ ] Review Apps configured for MR previews (if applicable)
```
