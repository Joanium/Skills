---
name: Supply Chain Security (SBOM & Dependency Security)
trigger: supply chain security, SBOM, software bill of materials, dependency security, dependency vulnerability, CVE scanning, npm audit, dependabot, SLSA, software supply chain, malicious package, typosquatting, dependency confusion, sigstore, provenance
description: Secure your software supply chain. Covers SBOM generation, dependency scanning, SLSA provenance, artifact signing, policy enforcement, and responding to supply chain attacks like log4shell.
---

# ROLE
You are a senior security engineer. The software supply chain is now the most common attack vector for sophisticated adversaries. Your job is to know what you're running, verify it's trustworthy, and detect when something unexpected appears.

# WHY SUPPLY CHAIN SECURITY MATTERS
```
RECENT SUPPLY CHAIN ATTACKS:
  Log4Shell (2021):     Log4j vulnerability in millions of Java apps via transitive dep
  SolarWinds (2020):    Build system compromised → malicious update shipped to 18,000 orgs
  XZ Utils (2024):      Malicious maintainer backdoored SSH compression library
  colors.js (2022):     Maintainer intentionally broke their own package → broke CI everywhere
  event-stream (2018):  Malicious code injected by new maintainer to steal Bitcoin wallets

YOUR RISK SURFACE:
  A typical Node.js app has:
    ~30 direct dependencies
    ~600–1500 transitive dependencies (deps of deps)
    Each is a potential attack vector
```

# STEP 1: KNOW WHAT YOU'RE RUNNING (SBOM)

## Software Bill of Materials
```
An SBOM is a formal list of components in your software:
  - Package name, version, license, source URL
  - Dependency relationships (direct vs transitive)
  - Known vulnerabilities as of generation time

SBOM FORMATS:
  SPDX:      Linux Foundation standard — widely supported
  CycloneDX: OWASP standard — better tooling for security use cases (prefer this)

WHY YOU NEED ONE:
  ✓ Log4Shell: with an SBOM, answer "are we vulnerable?" in minutes, not days
  ✓ License compliance: "do we ship any GPL code in our proprietary product?"
  ✓ Procurement: enterprise customers increasingly require SBOMs
  ✓ Legal: CISA/EO 14028 requires SBOMs for federal software vendors
```

## Generating SBOMs
```bash
# Node.js / npm — CycloneDX
npm install -g @cyclonedx/cyclonedx-npm
cyclonedx-npm --output-file sbom.json --output-format JSON

# Python — Syft (universal SBOM generator)
syft python:requirements.txt -o cyclonedx-json=sbom.json
# Or from a container image:
syft my-app:latest -o spdx-json=sbom.spdx.json

# Java / Maven
mvn org.cyclonedx:cyclonedx-maven-plugin:makeBom

# Go
syft . -o cyclonedx-json=sbom.json
# Or: go list -m -json all | nancy sleuth

# Container images (catches everything including OS packages)
syft registry:myapp:1.2.3 -o cyclonedx-json=sbom.json
grype sbom:sbom.json  # scan SBOM for vulnerabilities
```

## SBOM in CI/CD
```yaml
# .github/workflows/sbom.yml
name: Generate and Scan SBOM
on:
  push:
    branches: [main]
  release:
    types: [published]

jobs:
  sbom:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Generate SBOM
        uses: anchore/sbom-action@v0
        with:
          format: cyclonedx-json
          output-file: sbom.cyclonedx.json

      - name: Scan SBOM for vulnerabilities
        uses: anchore/scan-action@v3
        with:
          sbom: sbom.cyclonedx.json
          fail-build: true
          severity-cutoff: high    # fail on HIGH and CRITICAL CVEs

      - name: Attach SBOM to release
        if: github.event_name == 'release'
        uses: actions/upload-release-asset@v1
        with:
          upload_url: ${{ github.event.release.upload_url }}
          asset_path: sbom.cyclonedx.json
          asset_name: sbom.cyclonedx.json
```

# STEP 2: VULNERABILITY SCANNING

## Automated Scanning
```yaml
# Dependabot (GitHub) — automatic PRs for vulnerable dependencies
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: npm
    directory: "/"
    schedule:
      interval: daily
    open-pull-requests-limit: 10
    groups:
      dependencies:
        patterns: ["*"]
    ignore:
      - dependency-name: "lodash"
        update-types: ["version-update:semver-patch"]  # skip patch for specific packages

  - package-ecosystem: docker
    directory: "/"
    schedule:
      interval: weekly

  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: weekly
```

```bash
# Trivy — container + filesystem scanner (fast, accurate)
trivy image myapp:latest
trivy fs .               # scan local filesystem
trivy repo .             # scan git repo

# Grype — vulnerability scanner by Anchore
grype myapp:latest
grype .                  # scan directory

# Snyk — commercial, good IDE integration
snyk test                # scan project
snyk container test myapp:latest
snyk monitor             # continuous monitoring

# OSV-Scanner — Google's open-source vuln scanner (uses OSV database)
osv-scanner --lockfile=package-lock.json
osv-scanner -r .         # recursive scan
```

## Vulnerability Triage Policy
```
CRITICAL (CVSS 9.0–10.0):
  Response time: fix within 24 hours (business hours)
  If no fix available: temporary workaround or disable feature
  Escalate to security team immediately

HIGH (CVSS 7.0–8.9):
  Response time: fix within 7 days
  Schedule in next sprint if no immediate fix
  Document risk acceptance if deferring

MEDIUM (CVSS 4.0–6.9):
  Response time: fix within 30 days
  Include in regular dependency update cycle

LOW (CVSS < 4.0):
  Include in quarterly dependency maintenance
  May accept risk if exploitability is low

CRITERIA FOR IGNORING A CVE:
  Document in .grype.yaml / .trivyignore with:
    - CVE ID
    - Reason (not exploitable in our context / no attack vector in our usage)
    - Expiry date (re-evaluate in 90 days)
    - Owner (who is responsible for re-evaluation)
```

# STEP 3: ARTIFACT SIGNING & PROVENANCE

## Sigstore / Cosign (Container Image Signing)
```bash
# Sign a container image (keyless — uses OIDC identity from CI)
cosign sign --yes myregistry/myapp:1.2.3

# In GitHub Actions (keyless signing with OIDC):
- name: Sign container image
  uses: sigstore/cosign-installer@v3

- run: |
    cosign sign --yes \
      --rekor-url=https://rekor.sigstore.dev \
      myregistry/myapp:${{ github.sha }}

# Verify before deploying:
cosign verify \
  --certificate-identity-regexp="https://github.com/myorg/myrepo" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  myregistry/myapp:1.2.3
```

## SLSA (Supply-chain Levels for Software Artifacts)
```
SLSA LEVELS:
  Level 1:  Provenance exists (build process documented)
  Level 2:  Hosted build service (GitHub Actions, not local build)
  Level 3:  Hardened build (no secrets in build env, isolated)
  Level 4:  Two-person review, hermetic build (reproducible)

TARGET: SLSA Level 2 for most projects (achievable with GitHub Actions)
        SLSA Level 3+ for security-critical components

IMPLEMENTATION (GitHub Actions SLSA generator):
```

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      digests: ${{ steps.hash.outputs.digests }}
    steps:
      - uses: actions/checkout@v4
      - name: Build artifact
        run: make build
      - name: Generate SHA256 hash
        id: hash
        run: |
          sha256sum artifact.tar.gz > SHA256SUMS
          echo "digests=$(base64 -w0 SHA256SUMS)" >> $GITHUB_OUTPUT

  provenance:
    needs: [build]
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v2
    with:
      base64-subjects: ${{ needs.build.outputs.digests }}
```

# STEP 4: DEPENDENCY HYGIENE

## Lock Files (Always Commit)
```
ALWAYS commit lock files:
  package-lock.json / yarn.lock  (Node.js)
  Pipfile.lock / poetry.lock     (Python)
  Gemfile.lock                   (Ruby)
  go.sum                         (Go)
  Cargo.lock                     (Rust)

WHY: lock files pin exact versions of all transitive deps
     without them: `npm install` today ≠ `npm install` tomorrow
     transitive dep can silently update to a malicious version

VERIFYING INTEGRITY:
  npm ci                    # uses lock file, fails if it doesn't match package.json
  pip install --require-hashes  # fail if hashes don't match
  bundle install --frozen   # Ruby
```

## Avoiding Dependency Confusion & Typosquatting
```
DEPENDENCY CONFUSION:
  Attack: publish a malicious package with the same name as your internal package
          to a public registry (npm, PyPI). Build systems may pull the public one.

MITIGATIONS:
  [ ] Register your internal package names on public registries (reserve namespace)
  [ ] Use a private registry with explicit scoping: @mycompany/mypackage
  [ ] Set up registry mirroring with allowlist (only approved packages)
  [ ] Nexus / Artifactory: configure to prefer internal over public

TYPOSQUATTING:
  Attack: publish `reqeusts` (typo of `requests`) hoping developers mistype

MITIGATIONS:
  [ ] Audit new dependencies added in PRs (review package.json diffs carefully)
  [ ] Verify package authors and download counts before adding a new dep
  [ ] Use tools: OSS Fuzz, socket.dev (analyzes package behavior, not just CVEs)
  [ ] Prefer well-known packages from established organizations
```

## Minimal Dependency Policy
```
BEFORE ADDING A DEPENDENCY, ASK:
  1. Is this actually needed, or can we implement it in <50 lines?
  2. Is the package actively maintained? (last commit, open issues, maintainer count)
  3. How many transitive dependencies does it add? (`npm why <package>`)
  4. What's its weekly download count? (higher = more scrutiny from the community)
  5. Has it had security incidents before?

RED FLAGS:
  ✗ New package (< 6 months old) with no community
  ✗ Single maintainer with no backup
  ✗ Unusual install scripts (preinstall, postinstall) in package.json
  ✗ Requests unnecessary permissions (network access for a JSON parser)
  ✗ Package name very similar to a popular package

TOOLS:
  socket.dev      — analyzes supply chain risk per package
  deps.dev        — Google's package metadata and dependency graph
  snyk advisor    — package health score
```

# RESPONDING TO A SUPPLY CHAIN INCIDENT

## Incident Response Playbook
```
WHEN A CRITICAL CVE DROPS (like Log4Shell):

HOUR 1 — DETECTION:
  [ ] Search SBOM for vulnerable package: grep -r "log4j" sbom.json
  [ ] Or: grype --output json . | jq '.matches[] | select(.vulnerability.id == "CVE-2021-44228")'
  [ ] Identify ALL services using the affected package (not just direct deps)

HOUR 2–4 — TRIAGE:
  [ ] Is the vulnerable code path reachable in our usage?
  [ ] Is the service internet-facing or internal-only?
  [ ] Are there WAF rules or other mitigations we can apply immediately?

HOUR 4–24 — REMEDIATION:
  [ ] Update to patched version in all affected services
  [ ] Deploy urgently (skip normal release cadence if necessary)
  [ ] Apply WAF temporary mitigation while fix is in progress

POST-INCIDENT:
  [ ] Document timeline and affected services
  [ ] Improve SBOM generation and scanning if it was slow to detect
  [ ] Review dependency update policies
```

# POLICY ENFORCEMENT
```yaml
# OPA/Gatekeeper policy: block deployment of images with critical CVEs
# (Applied at Kubernetes admission control)
package main

deny[msg] {
    input.request.object.metadata.annotations["trivy.aquasec.com/critical-vulns"]
    count := to_number(input.request.object.metadata.annotations["trivy.aquasec.com/critical-vulns"])
    count > 0
    msg := sprintf("Image has %v critical vulnerabilities. Fix before deploying.", [count])
}
```

# MINIMUM SECURITY BASELINE
```
TIER 1 — Do these immediately:
  [ ] Commit all lock files
  [ ] Enable Dependabot or Renovate
  [ ] Add Trivy/Grype scan to CI (fail on CRITICAL)
  [ ] Generate SBOM in release pipeline

TIER 2 — Do these within 30 days:
  [ ] Sign container images with Cosign
  [ ] Private registry with mirroring and allowlist
  [ ] Dependency audit policy (document before adding new deps)
  [ ] Incident response playbook for critical CVEs

TIER 3 — Do these within 90 days:
  [ ] SLSA Level 2 provenance for all releases
  [ ] Hermetic builds (no internet access during build)
  [ ] Reproducible builds verification
  [ ] Quarterly SBOM review with security team
```
