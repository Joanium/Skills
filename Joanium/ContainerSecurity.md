---
name: Container Security
trigger: container security, docker security, kubernetes security, image scanning, k8s rbac, pod security, seccomp, network policy, image hardening, supply chain security, trivy, dockerfile security, container hardening, k8s secrets management
description: Harden Docker images and Kubernetes workloads against attacks. Covers secure Dockerfile patterns, image scanning, K8s RBAC, Pod Security Standards, NetworkPolicies, secret management, and supply chain security.
---

# ROLE
You are a platform security engineer. You design container environments that are secure by default — minimal attack surface, least-privilege execution, auditable supply chain. You treat every container as untrusted until proven otherwise.

# SECURE DOCKERFILE PATTERNS
```dockerfile
# ─── STAGE 1: Build ─────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app

# Copy only package files first (layer cache optimization)
COPY package*.json ./
RUN npm ci --only=production    # NOT npm install — ci is reproducible

COPY . .
RUN npm run build

# ─── STAGE 2: Runtime (MINIMAL IMAGE) ───────────────────────────
FROM node:20-alpine AS runtime   # alpine = ~5MB vs debian ~80MB

# Create non-root user BEFORE copying files
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -s /bin/sh -D appuser

WORKDIR /app

# Copy ONLY what's needed to run (not source, not dev tools)
COPY --from=builder --chown=appuser:appgroup /app/dist ./dist
COPY --from=builder --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:appgroup /app/package.json .

# Remove package manager to reduce attack surface
RUN rm -rf /usr/local/lib/node_modules/npm

# Switch to non-root user
USER appuser

# Document the port (informational — does not publish)
EXPOSE 3000

# Use array form (exec form) — not shell form
# Shell form: CMD node server.js      → runs as sh -c, can't receive signals
# Exec form:  CMD ["node", "server.js"] → PID 1, receives SIGTERM properly
CMD ["node", "dist/server.js"]

# Security metadata
LABEL org.opencontainers.image.source="https://github.com/myorg/myapp"
LABEL org.opencontainers.image.revision="${GIT_SHA}"
```

## What to NEVER do in Dockerfiles
```dockerfile
# ✗ Running as root (default if you don't set USER)
# ✗ Copying the whole repo into the image: COPY . .  (in final stage)
# ✗ Storing secrets in ENV or ARG (visible in image layers forever)
# ✗ Using :latest tag (not reproducible, may be compromised)
# ✗ Installing curl/wget/bash in production images (attack tools)
# ✗ Using SUID binaries (find / -perm /4000 -type f)
# ✗ Leaving build tools in final image (gcc, make, git)
```

# IMAGE SCANNING
```bash
# Trivy — scan for CVEs, misconfigs, secrets
trivy image myorg/myapp:1.4.2
trivy image --severity HIGH,CRITICAL myorg/myapp:1.4.2    # filter severity
trivy image --exit-code 1 --severity CRITICAL myorg/myapp:1.4.2  # fail CI on critical

# Scan filesystem (before build)
trivy fs --security-checks vuln,secret .

# Scan IaC (Kubernetes manifests, Helm charts)
trivy config ./k8s/

# In CI/CD (GitHub Actions)
- name: Scan image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'myorg/myapp:${{ github.sha }}'
    format: 'sarif'
    exit-code: '1'
    severity: 'CRITICAL,HIGH'

# Grype — alternative scanner
grype myorg/myapp:1.4.2

# Base image freshness — update regularly
# Use Renovate or Dependabot to auto-PR base image updates
```

# KUBERNETES POD SECURITY
```yaml
# Pod Security Standards — apply to namespaces
# Levels: privileged (anything) | baseline (minimal) | restricted (hardened)
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit:   restricted
    pod-security.kubernetes.io/warn:    restricted

---
# SecurityContext — apply to all pods
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      # Pod-level security
      securityContext:
        runAsNonRoot: true          # refuse to run as UID 0
        runAsUser: 1001
        runAsGroup: 1001
        fsGroup: 1001               # volume ownership
        seccompProfile:
          type: RuntimeDefault      # enable seccomp filtering
      
      containers:
        - name: app
          securityContext:
            allowPrivilegeEscalation: false   # cannot gain more privileges
            readOnlyRootFilesystem: true       # cannot write to container FS
            capabilities:
              drop: ["ALL"]                   # drop ALL linux capabilities
              add: ["NET_BIND_SERVICE"]       # add back ONLY what's needed
```

# NETWORK POLICIES — ZERO-TRUST NETWORKING
```yaml
# Default: deny all ingress and egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}      # applies to all pods in namespace
  policyTypes:
    - Ingress
    - Egress

---
# Allow: api-server can receive from ingress, send to postgres and redis only
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-server-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api-server
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
      ports:
        - port: 3000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - port: 5432
    - to:
        - podSelector:
            matchLabels:
              app: redis
      ports:
        - port: 6379
    - to:                       # allow DNS
        - namespaceSelector: {}
      ports:
        - port: 53
          protocol: UDP
```

# SECRET MANAGEMENT
```
Kubernetes Secrets are base64-encoded — NOT encrypted at rest by default.
Anyone with kubectl get secret access can read them.

Tier 1: Encrypt Secrets at rest (quick win)
  kubectl -n kube-system get configmap kubeadm-config -o yaml
  Enable EncryptionConfiguration with AES-GCM or KMS provider

Tier 2: Sealed Secrets (encrypt in git)
  kubeseal --format yaml < secret.yaml > sealed-secret.yaml
  Sealed Secrets controller decrypts at apply time
  Safe to commit sealed-secret.yaml to git

Tier 3: External Secrets Operator (production standard)
  Store secrets in AWS Secrets Manager / HashiCorp Vault / GCP Secret Manager
  ExternalSecret CR pulls secret → creates K8s Secret automatically
  
  apiVersion: external-secrets.io/v1beta1
  kind: ExternalSecret
  metadata:
    name: api-server-secrets
  spec:
    refreshInterval: 1h
    secretStoreRef:
      name: aws-secrets-manager
      kind: ClusterSecretStore
    target:
      name: api-server-secrets
    data:
      - secretKey: DATABASE_URL
        remoteRef:
          key: production/api-server
          property: database_url

NEVER do:
  - Store secrets in ConfigMaps
  - Print secrets in logs (kubectl logs leaks them)
  - Mount secrets as files if env vars suffice
  - Give applications access to list all secrets in a namespace
```

# RBAC — LEAST PRIVILEGE
```yaml
# Audit who has what access
kubectl auth can-i --list --as system:serviceaccount:production:api-server

# Avoid these dangerous permissions (can escalate to cluster-admin):
#   get/list/watch secrets (cluster-wide)
#   create/update pods (can mount any secret)
#   create rolebindings/clusterrolebindings
#   exec into pods (interactive shell)

# Scoped service account pattern
apiVersion: v1
kind: ServiceAccount
metadata:
  name: api-server
  namespace: production
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/api-server-role  # IRSA

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: api-server-role
  namespace: production
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    resourceNames: ["api-server-config"]   # specific resource, not all configmaps
    verbs: ["get"]                          # read-only, specific resource
```

# SUPPLY CHAIN SECURITY (SLSA / COSIGN)
```bash
# Sign images with cosign (keyless, using OIDC in CI)
cosign sign --yes myorg/myapp:1.4.2

# Verify signature before deploying
cosign verify \
  --certificate-identity="https://github.com/myorg/myapp/.github/workflows/release.yml@refs/heads/main" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  myorg/myapp:1.4.2

# Generate SBOM (Software Bill of Materials)
syft myorg/myapp:1.4.2 -o spdx-json > sbom.json
grype sbom:sbom.json    # scan SBOM for vulnerabilities

# Pin base images by digest (not just tag — tags are mutable)
FROM node:20-alpine@sha256:abc123...   # digest is immutable
```

# ADMISSION CONTROL — POLICY ENFORCEMENT
```yaml
# OPA/Gatekeeper — enforce policies cluster-wide
# Example: deny images not from approved registries

apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sAllowedRepos
metadata:
  name: allowed-repos
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
  parameters:
    repos:
      - "myorg.azurecr.io/"
      - "gcr.io/myproject/"
      # Blocks: docker.io, public images pulled without review
```

# SECURITY CHECKLIST
```
Image hardening:
[ ] Multi-stage build — no build tools in final image
[ ] Non-root user (USER directive)
[ ] Minimal base image (alpine or distroless)
[ ] No secrets in Dockerfile ENV/ARG
[ ] Image pinned by digest in production

Runtime security:
[ ] readOnlyRootFilesystem: true
[ ] allowPrivilegeEscalation: false
[ ] capabilities: drop ALL, add only needed
[ ] seccompProfile: RuntimeDefault
[ ] Pod Security Standard: restricted on production namespace

Networking:
[ ] Default-deny NetworkPolicy in each namespace
[ ] Allowlist per-service NetworkPolicies
[ ] No NodePort services in production
[ ] TLS between services (mTLS via Istio/Linkerd for sensitive services)

Secrets:
[ ] Secrets encrypted at rest (EncryptionConfiguration or KMS)
[ ] External Secrets Operator or Sealed Secrets for git safety
[ ] No secrets in ConfigMaps or environment variable plaintext in manifests

Supply chain:
[ ] Image signing with cosign in CI
[ ] Image scanning (Trivy) in CI — fail on CRITICAL
[ ] Admission controller blocks unsigned/unscanned images
[ ] SBOM generated and stored per release
[ ] Base images updated automatically (Renovate/Dependabot)
```
