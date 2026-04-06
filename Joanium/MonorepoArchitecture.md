---
name: Monorepo Architecture
trigger: monorepo, turborepo, nx, pnpm workspaces, yarn workspaces, monorepo setup, shared packages, shared code, multiple apps one repo, internal packages, workspace, package sharing, monorepo tooling, build caching, affected packages
description: Design and manage a monorepo — sharing code between apps, configuring build pipelines with caching, managing internal packages, and keeping the repo fast as it scales. Use when setting up a monorepo, adding a new app to an existing one, or improving build performance.
---

A monorepo puts multiple apps and packages in one repository. Done right, it means sharing a component library across a web and mobile app, running a single `git blame` to understand a change across the stack, and atomically shipping features that span frontend and backend. Done wrong, it's slow, tangled, and hard to understand. The tooling matters enormously.

## When to Use a Monorepo

```
Monorepo makes sense when:
✓ Multiple apps share code (component library, utilities, types, API clients)
✓ You want atomic commits that span frontend and backend
✓ You want a single PR to update both apps and the shared library
✓ You want unified tooling (one lint config, one test setup, one CI)
✓ Teams are small enough to share conventions

Monorepo is wrong when:
✗ Apps are completely unrelated (different domains, different stacks)
✗ Teams need total independence (separate deploy pipelines, different release cycles)
✗ The repo would have hundreds of packages — needs very mature tooling
✗ You're just starting out — start simple, extract later when you feel the pain
```

## The Anatomy of a Monorepo

```
my-monorepo/
├── apps/                    # Deployable applications
│   ├── web/                 # Next.js frontend
│   ├── api/                 # Express/Fastify backend
│   ├── mobile/              # React Native app
│   └── admin/               # Internal admin dashboard
│
├── packages/                # Shared internal packages
│   ├── ui/                  # Shared component library
│   ├── types/               # Shared TypeScript types
│   ├── utils/               # Shared utility functions
│   ├── api-client/          # Generated/handwritten API client
│   ├── config/              # Shared configs (eslint, tsconfig, jest)
│   └── database/            # Prisma schema + generated client
│
├── package.json             # Root — workspace definition
├── turbo.json               # Turborepo pipeline config
├── pnpm-workspace.yaml      # pnpm workspace config
└── tsconfig.base.json       # Base TypeScript config
```

## Tooling Choice

```
Turborepo + pnpm — recommended for most teams
  pnpm: fast installs, strict dependency isolation, disk-efficient
  Turborepo: build caching, task pipelines, remote caching
  Best for: TypeScript/JavaScript monorepos

Nx — more powerful, more complex
  Built-in code generation, project graph, affected analysis
  Best for: Large organizations, Angular/React mixed stacks, enterprise
  
Yarn Workspaces — minimal, widely used
  Less tooling, works with Yarn PnP
  Best for: Simple setups without complex build pipelines

Lerna — legacy, now uses Nx under the hood
```

## Setting Up a Turborepo

### Root package.json
```json
{
  "name": "my-monorepo",
  "private": true,
  "scripts": {
    "build": "turbo build",
    "dev": "turbo dev",
    "lint": "turbo lint",
    "test": "turbo test",
    "type-check": "turbo type-check"
  },
  "devDependencies": {
    "turbo": "^2.0.0"
  }
}
```

### pnpm-workspace.yaml
```yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

### turbo.json — the pipeline definition
```json
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],  // Build dependencies first
      "outputs": [".next/**", "dist/**", "build/**"]
    },
    "dev": {
      "cache": false,           // Don't cache dev servers
      "persistent": true        // Long-running process
    },
    "lint": {
      "outputs": []
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": ["coverage/**"]
    },
    "type-check": {
      "dependsOn": ["^build"]
    }
  },
  "remoteCache": {
    "signature": true
  }
}
```

```bash
# Install everything
pnpm install

# Build all packages (respects dependency order, uses cache)
pnpm turbo build

# Build only affected packages (changed since last build)
pnpm turbo build --filter=...[HEAD^1]

# Run only web app and its dependencies
pnpm turbo dev --filter=web...

# Run tests for changed packages only
pnpm turbo test --filter=...[origin/main]
```

## Creating Internal Packages

### packages/ui — shared component library
```json
// packages/ui/package.json
{
  "name": "@repo/ui",
  "version": "0.0.0",
  "private": true,
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "exports": {
    ".": "./src/index.ts"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "react": "^18.0.0"
  },
  "peerDependencies": {
    "react": "^18.0.0"
  }
}
```

```typescript
// packages/ui/src/index.ts — the public API of the package
export { Button } from './components/Button';
export { Input } from './components/Input';
export { Modal } from './components/Modal';
export type { ButtonProps, InputProps, ModalProps } from './types';
```

### packages/types — shared TypeScript types
```typescript
// packages/types/src/index.ts
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'member' | 'viewer';
  createdAt: Date;
}

export interface Order {
  id: string;
  userId: string;
  status: 'pending' | 'paid' | 'shipped' | 'delivered';
  totalCents: number;
  currency: string;
}

// This package has no dependencies — it's always safe to import
```

### packages/config — shared tooling config
```javascript
// packages/config/eslint/index.js
module.exports = {
  extends: ['next', 'prettier'],
  rules: {
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    '@typescript-eslint/no-explicit-any': 'error',
  }
};

// packages/config/tsconfig/base.json
{
  "$schema": "https://json.schemastore.org/tsconfig",
  "compilerOptions": {
    "strict": true,
    "target": "ES2022",
    "lib": ["ES2022"],
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  }
}
```

## Using Internal Packages in Apps

```json
// apps/web/package.json
{
  "name": "web",
  "dependencies": {
    "@repo/ui": "workspace:*",
    "@repo/types": "workspace:*",
    "@repo/utils": "workspace:*"
  }
}
```

```typescript
// apps/web/src/pages/dashboard.tsx
import { Button, Modal } from '@repo/ui';
import type { User, Order } from '@repo/types';
import { formatCurrency } from '@repo/utils';

export function Dashboard({ user, orders }: { user: User; orders: Order[] }) {
  return (
    <div>
      <h1>Welcome {user.name}</h1>
      {orders.map(order => (
        <div key={order.id}>
          {formatCurrency(order.totalCents, order.currency)}
        </div>
      ))}
      <Button variant="primary">New Order</Button>
    </div>
  );
}
```

## TypeScript Path Aliases (no build step required)

For source-code-first packages (no compilation step), configure TypeScript to resolve them directly:

```json
// tsconfig.base.json
{
  "compilerOptions": {
    "paths": {
      "@repo/ui": ["../../packages/ui/src/index.ts"],
      "@repo/types": ["../../packages/types/src/index.ts"],
      "@repo/utils": ["../../packages/utils/src/index.ts"]
    }
  }
}
```

```json
// apps/web/tsconfig.json
{
  "extends": "../../tsconfig.base.json",
  "include": ["src", "../../packages/ui/src", "../../packages/types/src"]
}
```

## Remote Caching (Turborepo)

Without remote caching, every CI run rebuilds everything. With it, CI shares cache across branches and machines.

```bash
# Vercel Remote Cache (free for open source, paid for private)
npx turbo login
npx turbo link  # Links to your Vercel team

# Self-hosted with Turborepo Remote Cache
# docker run -p 3000:3000 ducktors/turborepo-remote-cache

# In turbo.json:
{
  "remoteCache": {
    "apiUrl": "https://your-cache-server.com"
  }
}

# Set in CI:
TURBO_TOKEN=<token> TURBO_TEAM=<team> pnpm turbo build
```

## CI/CD for Monorepos

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2  # Turborepo needs git history for affected

      - uses: pnpm/action-setup@v4
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'

      - run: pnpm install --frozen-lockfile

      # Only build/test what changed
      - run: pnpm turbo build test lint --filter=...[HEAD^1]
        env:
          TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
          TURBO_TEAM: ${{ secrets.TURBO_TEAM }}

  # Deploy only if the affected app changed
  deploy-web:
    needs: build
    if: contains(needs.build.outputs.affected, 'web')
    runs-on: ubuntu-latest
    steps:
      - run: pnpm turbo deploy --filter=web
```

## Monorepo Pitfalls

```
PITFALL: Circular dependencies between packages
  packages/ui imports from packages/utils
  packages/utils imports from packages/ui → CIRCULAR
FIX: Draw the dependency graph. It must be a DAG (no cycles).
  ui → utils → types
  api → types
  web → ui, utils, types

PITFALL: Internal package versions diverging
  apps/web uses React 17, apps/mobile uses React 18
FIX: Hoist shared dependencies to root package.json
  All apps use the same React version via workspace root

PITFALL: Slow CI because everything rebuilds
FIX: Enable remote caching + use --filter=...[HEAD^1]

PITFALL: Over-extracting to packages too early
  "We might reuse this someday" → 20 packages with 1 consumer each
FIX: Extract when you have 2+ actual consumers.
  Duplication is cheaper than a wrong abstraction.

PITFALL: No clear ownership of shared packages
FIX: Assign a team or individual as CODEOWNER for each package.
  # .github/CODEOWNERS
  packages/ui/    @frontend-team
  packages/types/ @platform-team
  packages/database/ @backend-team
```

## Monorepo Setup Checklist

```
Foundation:
☐ pnpm workspaces configured (pnpm-workspace.yaml)?
☐ Turborepo installed and turbo.json defines the pipeline?
☐ Task dependency order correct (build before test, ^build for deps)?
☐ Shared tsconfig.base.json with strict mode?
☐ Shared eslint config in packages/config?

Packages:
☐ package.json names use a consistent scope (@repo/ or @company/)?
☐ Internal packages marked "private: true"?
☐ Public API exported cleanly from index.ts?
☐ No circular dependencies between packages?
☐ CODEOWNERS defined per package?

CI:
☐ --filter=...[HEAD^1] used to only build affected packages?
☐ Remote caching configured (Turborepo or self-hosted)?
☐ Deployment steps filter to affected apps?
☐ pnpm install --frozen-lockfile (not npm install) in CI?
```
