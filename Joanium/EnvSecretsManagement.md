---
name: Environment & Secrets Management
trigger: environment variables, secrets management, .env file, secrets vault, aws secrets manager, doppler, vault hashicorp, secret rotation, 12 factor app, config management, api keys management, secret leak, dotenv, environment config, secrets in production
description: Design and implement a secure secrets management strategy for any environment (local dev, staging, production). Use this skill when the user asks about environment variables, storing secrets, secret rotation, integrating with secret managers (AWS Secrets Manager, Vault, Doppler), or preventing secret leaks. Covers the full lifecycle from dev to production.
---

# ROLE
You are a security-focused platform engineer. You design secrets management that is secure, auditable, and developer-friendly — the two don't have to be in conflict.

# GOLDEN RULES

```
1. NEVER commit secrets to git — ever, even in private repos
2. NEVER put secrets in Docker images or build artifacts
3. NEVER log secrets (check logging libraries strip them)
4. NEVER pass secrets as command-line arguments (appear in ps aux)
5. Always rotate leaked secrets immediately, then investigate
```

# LOCAL DEVELOPMENT

```bash
# .env file — gitignored, for local development ONLY
DATABASE_URL=postgres://user:password@localhost:5432/myapp
REDIS_URL=redis://localhost:6379
STRIPE_SECRET_KEY=sk_test_abc123
JWT_SECRET=local-dev-secret-change-in-prod

# .env.example — committed to git (template, no real values)
DATABASE_URL=postgres://user:password@localhost:5432/myapp_dev
REDIS_URL=redis://localhost:6379
STRIPE_SECRET_KEY=sk_test_REPLACE_ME
JWT_SECRET=REPLACE_ME_WITH_RANDOM_STRING

# .gitignore — always have this
.env
.env.local
.env.*.local
*.env
```

## Node.js — Loading Environment Variables
```javascript
// Use dotenv for local dev
// Install: npm install dotenv

// At the top of your entry point (index.ts / server.ts)
import 'dotenv/config';     // ES modules
// OR
require('dotenv').config(); // CommonJS

// Validate required vars on startup (fail fast)
const requiredEnvVars = [
  'DATABASE_URL',
  'STRIPE_SECRET_KEY',
  'JWT_SECRET',
];
for (const varName of requiredEnvVars) {
  if (!process.env[varName]) {
    throw new Error(`Missing required environment variable: ${varName}`);
  }
}

// Type-safe config object (don't scatter process.env throughout the code)
export const config = {
  database: { url: process.env.DATABASE_URL! },
  stripe:   { secretKey: process.env.STRIPE_SECRET_KEY! },
  jwt:      { secret: process.env.JWT_SECRET!, expiresIn: '7d' },
  port:     parseInt(process.env.PORT ?? '3000', 10),
  isDev:    process.env.NODE_ENV !== 'production',
} as const;
```

```python
# Python — pydantic-settings for validation
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    stripe_secret_key: str
    jwt_secret: str
    port: int = 3000
    debug: bool = False

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()  # raises ValidationError if required vars missing
```

# PRODUCTION SECRET MANAGERS

## AWS Secrets Manager
```javascript
import { SecretsManagerClient, GetSecretValueCommand } from "@aws-sdk/client-secrets-manager";

const client = new SecretsManagerClient({ region: "us-east-1" });

// Fetch secret (cache the result — don't call on every request)
async function getSecret(secretId: string): Promise<Record<string, string>> {
  const response = await client.send(
    new GetSecretValueCommand({ SecretId: secretId })
  );
  return JSON.parse(response.SecretString!);
}

// Usage at app startup
const dbSecret = await getSecret("myapp/prod/database");
const stripeSecret = await getSecret("myapp/prod/stripe");

// Cache in module-level variable — refresh every hour
let cachedSecrets: Record<string, string> | null = null;
let lastFetchTime = 0;

async function getSecrets() {
  if (!cachedSecrets || Date.now() - lastFetchTime > 3600000) {
    cachedSecrets = await getSecret("myapp/prod/all");
    lastFetchTime = Date.now();
  }
  return cachedSecrets;
}
```

```bash
# AWS CLI — create and retrieve secrets
aws secretsmanager create-secret \
  --name "myapp/prod/database" \
  --secret-string '{"url":"postgres://...","password":"..."}'

aws secretsmanager get-secret-value --secret-id "myapp/prod/database"

# Rotate a secret
aws secretsmanager rotate-secret --secret-id "myapp/prod/database"
```

## HashiCorp Vault
```bash
# Store secret
vault kv put secret/myapp/prod/database url="postgres://..." password="..."

# Read secret
vault kv get secret/myapp/prod/database
vault kv get -field=password secret/myapp/prod/database

# AppRole auth for services (not user auth)
vault auth enable approle
vault write auth/approle/role/myapp \
  token_policies="myapp-policy" \
  token_ttl=1h \
  token_max_ttl=4h
```

```javascript
// Vault SDK in Node.js
import vault from "node-vault";

const client = vault({
  apiVersion: "v1",
  endpoint: process.env.VAULT_ADDR,
  token: process.env.VAULT_TOKEN,
});

const secret = await client.read("secret/data/myapp/prod/database");
const dbPassword = secret.data.data.password;
```

## Doppler (Developer-Friendly)
```bash
# Doppler syncs secrets to your app — no SDK needed for many use cases
npm install -g doppler
doppler login
doppler setup   # link to your project

# Run app with secrets injected as env vars
doppler run -- node dist/server.js

# In CI/CD
doppler run --token $DOPPLER_TOKEN -- npm test
```

# KUBERNETES SECRETS

```yaml
# Create a secret
kubectl create secret generic db-credentials \
  --from-literal=url=postgres://user:pass@host/db \
  --from-literal=password=supersecret

# Better: use External Secrets Operator (sync from AWS/Vault/Doppler)
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-credentials
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretsmanager
    kind: ClusterSecretStore
  target:
    name: db-credentials        # creates a K8s Secret with this name
  data:
    - secretKey: DATABASE_URL
      remoteRef:
        key: myapp/prod/database
        property: url

# Mount secret as environment variable in pod
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: db-credentials
        key: DATABASE_URL
```

# SECRET ROTATION

```
Rotation strategy:
1. Generate new credentials in secret manager
2. Add new credentials to app config (dual-write period)
3. Update app to use new credentials (rolling deploy)
4. Revoke old credentials
5. Alert on failure

Rotation intervals by type:
  API keys (third-party)  → every 90 days or on personnel change
  Database passwords      → every 90 days
  JWT signing secrets     → every 30 days (support old + new briefly)
  Encryption keys         → annually (with key versioning, not full rotation)
```

# DETECTING SECRET LEAKS

```bash
# Scan repo for secrets before commit
# Install: brew install gitleaks
gitleaks detect --source . --verbose

# Add to pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
gitleaks protect --staged --verbose
if [ $? -ne 0 ]; then
  echo "❌ Potential secrets detected. Commit blocked."
  exit 1
fi
EOF
chmod +x .git/hooks/pre-commit

# Scan git history (use after suspected leak)
gitleaks detect --source . --log-opts="HEAD~50..HEAD"

# GitHub secret scanning — enable in repo settings
# GitHub will alert you if a known secret format is pushed
```

## If a Secret Leaks
```
1. REVOKE immediately — don't wait to investigate
2. Rotate — generate a new secret and deploy
3. Audit — check access logs for misuse during the window
4. Remove from git history (use BFG Repo Cleaner, not git filter-branch)
   bfg --delete-files .env --no-blob-protection .
   git push --force-with-lease

4. Postmortem — how did it leak? Add detection to prevent recurrence
```

# CHECKLIST
```
[ ] .env in .gitignore, .env.example committed
[ ] Startup fails loudly if required env vars are missing
[ ] Config centralized in one module (not process.env scattered everywhere)
[ ] Production uses a secret manager (not .env files on server)
[ ] gitleaks or similar pre-commit hook installed
[ ] Secret rotation schedule documented
[ ] Secrets not logged (check logging config strips Authorization headers)
[ ] K8s secrets sourced from external secret store (not manually created)
```
