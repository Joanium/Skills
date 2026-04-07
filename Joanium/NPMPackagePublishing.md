---
name: NPM Package Publishing
trigger: publish npm, npm package, create npm library, publish to npm, npm publish, package.json exports, npm registry, semver, npm release, library packaging, esm cjs, dual package, package bundling, tsup, rollup library
description: Create, bundle, and publish professional npm packages. Covers package.json setup, dual ESM/CJS output, TypeScript declarations, semantic versioning, GitHub Actions CI publishing, and npm best practices.
---

# ROLE
You are a senior library developer. Your job is to publish npm packages that work everywhere — ESM, CJS, TypeScript projects — without import errors, missing types, or broken peer deps. Most package bugs come from incorrect exports configuration and missing type declarations.

# CORE PRINCIPLES
```
DUAL FORMAT:      Ship both ESM and CJS — consumers are on different module systems
TYPES INCLUDED:   Always ship TypeScript declarations — even for JS packages
EXPORTS MAP:      Use package.json "exports" field — it's the modern standard
SEMVER STRICTLY:  Breaking changes = major bump, new features = minor, fixes = patch
TEST BEFORE PUB:  npm pack and install locally before publishing to registry
```

# PACKAGE.JSON STRUCTURE

## Complete package.json
```json
{
  "name": "@withinjoel/my-lib",
  "version": "1.0.0",
  "description": "A useful utility library",
  "keywords": ["utility", "helper", "tools"],
  "author": "Joel Jolly <joeljollyhere@gmail.com> (https://joeljolly.vercel.app)",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/withinjoel/my-lib.git"
  },
  "homepage": "https://github.com/withinjoel/my-lib#readme",
  "bugs": "https://github.com/withinjoel/my-lib/issues",

  "main": "./dist/index.cjs",
  "module": "./dist/index.js",
  "types": "./dist/index.d.ts",

  "exports": {
    ".": {
      "import": {
        "types": "./dist/index.d.ts",
        "default": "./dist/index.js"
      },
      "require": {
        "types": "./dist/index.d.cts",
        "default": "./dist/index.cjs"
      }
    },
    "./utils": {
      "import": "./dist/utils.js",
      "require": "./dist/utils.cjs"
    }
  },

  "files": ["dist", "README.md", "LICENSE"],

  "scripts": {
    "build": "tsup",
    "dev": "tsup --watch",
    "test": "vitest run",
    "lint": "eslint src",
    "prepublishOnly": "npm run build && npm run test",
    "release": "npm version patch && npm publish",
    "release:minor": "npm version minor && npm publish",
    "release:major": "npm version major && npm publish"
  },

  "engines": { "node": ">=18" },

  "devDependencies": {
    "tsup": "^8.0.0",
    "typescript": "^5.0.0",
    "vitest": "^1.0.0"
  },

  "peerDependencies": {
    "react": ">=18"
  },
  "peerDependenciesMeta": {
    "react": { "optional": true }
  }
}
```

# BUNDLING WITH TSUP

## tsup.config.ts (Recommended Bundler)
```typescript
import { defineConfig } from 'tsup';

export default defineConfig({
  entry: {
    index: 'src/index.ts',
    utils: 'src/utils.ts',     // separate entry points
  },
  format: ['esm', 'cjs'],      // dual format
  dts: true,                   // generate .d.ts files
  sourcemap: true,
  clean: true,                 // clean dist before each build
  minify: false,               // don't minify libraries — consumers may tree-shake
  splitting: true,             // code splitting for ESM
  treeshake: true,
  external: ['react', 'react-dom'],  // don't bundle peer deps
  esbuildOptions: (options) => {
    options.banner = {
      js: '"use client";',  // for Next.js client components (if relevant)
    };
  },
});
```

## Install tsup
```bash
npm install -D tsup typescript

# Build
npx tsup

# Output:
# dist/index.js      (ESM)
# dist/index.cjs     (CommonJS)
# dist/index.d.ts    (TypeScript declarations)
# dist/index.d.cts   (CTS declarations)
```

# SOURCE STRUCTURE

## src/index.ts
```typescript
// Export everything from your library
export { MyClass } from './my-class';
export { myFunction, anotherFunction } from './utils';
export type { MyOptions, MyResult } from './types';

// Named exports preferred over default — tree-shakeable
```

## src/types.ts
```typescript
export interface MyOptions {
  debug?: boolean;
  timeout?: number;
  onProgress?: (progress: number) => void;
}

export type MyResult<T> = {
  data: T;
  meta: {
    duration: number;
    cached: boolean;
  };
};
```

# VERSIONING

## Semantic Versioning Rules
```
MAJOR (1.0.0 → 2.0.0):
  - Removing exported functions/classes/types
  - Changing function signatures in breaking ways
  - Dropping Node.js version support
  - Changing behavior that consumers depend on

MINOR (1.0.0 → 1.1.0):
  - New exported functions/classes
  - New optional parameters
  - New features that are backwards compatible
  - Deprecating (but not removing) APIs

PATCH (1.0.0 → 1.0.1):
  - Bug fixes
  - Security patches
  - Documentation updates
  - Internal refactors with no API change

Pre-release:
  1.0.0-alpha.1   → early, potentially breaking
  1.0.0-beta.1    → feature complete, stabilizing
  1.0.0-rc.1      → release candidate
```

## CHANGELOG (IMPORTANT)
```markdown
# Changelog

## [2.0.0] - 2025-04-01
### BREAKING CHANGES
- `doThing()` now returns `Promise<Result>` instead of `Result`

### Added
- New `doThingSync()` for synchronous use cases

## [1.1.0] - 2025-03-15
### Added
- `options.timeout` parameter to `doThing()`

## [1.0.1] - 2025-03-01
### Fixed
- Fixed crash when input is empty string
```

# PUBLISHING

## First Publish
```bash
# Login to npm
npm login
# Enter: username, password, email, OTP

# Test your package locally first
npm pack
# Creates: withinjoel-my-lib-1.0.0.tgz

# Install it in another local project to test
cd /tmp && mkdir test-pkg && cd test-pkg
npm init -y
npm install /path/to/withinjoel-my-lib-1.0.0.tgz

# If tests pass — publish
npm publish --access public  # --access public required for scoped packages
```

## Updating
```bash
# Patch bump + publish
npm version patch  # 1.0.0 → 1.0.1
npm publish

# Or with conventional commits + auto versioning:
npx standard-version  # reads commit messages to determine bump
```

## Publishing Scoped vs Unscoped
```
Unscoped:  npm publish              → available as "my-lib"
Scoped:    npm publish --access public → available as "@withinjoel/my-lib"

Scoped advantages:
  - Namespace prevents name conflicts
  - Clearer authorship
  - Can be private (paid plan) or public (free)
```

# GITHUB ACTIONS AUTO-PUBLISH
```yaml
# .github/workflows/publish.yml
name: Publish to NPM

on:
  push:
    tags: ['v*']

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          registry-url: 'https://registry.npmjs.org'

      - run: npm ci
      - run: npm run build
      - run: npm test

      - run: npm publish --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
          # Generate NPM_TOKEN: npmjs.com → Access Tokens → Granular Access Token
```

# README ESSENTIALS
```markdown
# my-lib

One-sentence description of what it does.

## Install
\`\`\`bash
npm install @withinjoel/my-lib
\`\`\`

## Quick Start
\`\`\`ts
import { myFunction } from '@withinjoel/my-lib';

const result = await myFunction({ option: 'value' });
console.log(result);
\`\`\`

## API Reference

### myFunction(options)
**Parameters:**
- `options.debug` — boolean, enable debug logging (default: false)

**Returns:** Promise<MyResult>

## License
MIT
```

# COMMON MISTAKES
```
Missing "exports" field:
  → Node 12+ uses exports for resolution — without it, deep imports break

Bundling peer dependencies:
  → List react, vue etc. in peerDependencies, add to tsup external: []
  → Bundling them = two copies of React in consumer's app = hooks error

Wrong "main" pointing to ESM:
  → "main" must point to CJS (.cjs) — require() callers use it
  → "module" points to ESM — bundlers use it

Missing type declarations:
  → Always set dts: true in tsup — consumers need types
  → Verify dist/*.d.ts files exist before publishing

Publishing without testing:
  → Always npm pack and install the tarball before npm publish
  → Test both: import { x } from 'pkg' and const { x } = require('pkg')
```
