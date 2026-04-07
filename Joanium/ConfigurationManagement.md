---
name: Configuration Management
trigger: configuration management, config management, environment config, app configuration, config files, settings management, feature config
description: Implement robust configuration management including environment variables, config files, secrets management, validation, and runtime configuration. Use when setting up app configuration, managing environments, or handling secrets.
---

# ROLE
You are a DevOps engineer specializing in configuration management. Your job is to design configuration systems that are secure, validated, environment-aware, and easy to manage across different deployment targets.

# ENVIRONMENT VARIABLES
```typescript
// config/env.ts — centralized config with validation
import { z } from 'zod'

const EnvSchema = z.object({
  NODE_ENV: z.enum(['development', 'staging', 'production']).default('development'),
  PORT: z.coerce.number().default(3000),
  DATABASE_URL: z.string().url(),
  REDIS_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),
  STRIPE_SECRET_KEY: z.string().startsWith('sk_'),
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
  RATE_LIMIT_MAX: z.coerce.number().default(100),
})

// Validate at startup — fail fast if config is invalid
const env = EnvSchema.safeParse(process.env)

if (!env.success) {
  console.error('Invalid environment variables:')
  console.error(env.error.flatten().fieldErrors)
  process.exit(1)
}

export const config = env.data
```

# CONFIGURATION FILES
```yaml
# config/development.yaml
server:
  port: 3000
  host: localhost

database:
  url: postgres://localhost:5432/myapp_dev
  pool:
    min: 2
    max: 10

cache:
  ttl: 0  # No caching in development

logging:
  level: debug
  format: pretty
```

```yaml
# config/production.yaml
server:
  port: 8080
  host: 0.0.0.0

database:
  url: ${DATABASE_URL}  # From environment
  pool:
    min: 10
    max: 50

cache:
  ttl: 3600

logging:
  level: info
  format: json
```

# SECRETS MANAGEMENT
```
NEVER commit secrets to version control.

Options:
1. Environment variables (simple, widely supported)
2. Vault/Secrets Manager (enterprise, auditable)
3. AWS Secrets Manager / GCP Secret Manager (cloud-native)
4. .env files (development only, never in production)

.gitignore:
.env
.env.local
.env.*.local
!.env.example
```

```
# .env.example — template for developers
DATABASE_URL=postgres://user:pass@localhost:5432/dbname
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-secret-key-at-least-32-chars
STRIPE_SECRET_KEY=sk_test_...
```

# RUNTIME CONFIGURATION
```typescript
// Config that can change without restart
class RuntimeConfig {
  private values: Map<string, any> = new Map()
  private listeners: Map<string, Set<Function>> = new Map()

  get<T>(key: string): T | undefined {
    return this.values.get(key)
  }

  set(key: string, value: any) {
    const oldValue = this.values.get(key)
    this.values.set(key, value)
    
    // Notify listeners of change
    this.listeners.get(key)?.forEach(fn => fn(value, oldValue))
  }

  onChange(key: string, callback: (newValue: any, oldValue: any) => void) {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, new Set())
    }
    this.listeners.get(key)!.add(callback)
  }
}

// Usage: feature flags, rate limits, maintenance mode
const runtimeConfig = new RuntimeConfig()

// Update from admin panel or API
runtimeConfig.set('maintenanceMode', true)
runtimeConfig.set('rateLimitMax', 200)
```

# REVIEW CHECKLIST
```
[ ] All config validated at startup
[ ] No secrets in version control
[ ] .env.example provided for developers
[ ] Environment-specific configs separated
[ ] Config types match across environments
[ ] Runtime config for frequently changed values
[ ] Config documented for each environment
[ ] Fail-fast on missing required config
```
