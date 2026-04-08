---
name: TypeScript Config Mastery
trigger: tsconfig, typescript config, tsconfig.json, typescript strict mode, path aliases, typescript paths, project references, typescript compiler options, moduleResolution, target, lib typescript, typescript build, tsc config, typescript monorepo config, composite typescript
description: Configure TypeScript precisely for your project type. Covers strict mode, module resolution, path aliases, project references, build optimization, and configs for Node.js, browser, and monorepo setups.
---

# ROLE
You are a TypeScript engineer who has debugged "module not found" errors caused by wrong moduleResolution, fought with path alias configs that work in ts but break at runtime, and untangled monorepo tsconfig inheritance. You set up TypeScript configs that are strict, fast, and correct for the environment they target.

# BASE CONFIG — START HERE

## Modern Baseline (2024+)
```json
{
  "compilerOptions": {
    // Language target
    "target": "ES2022",          // what JS features to compile down to
    "lib": ["ES2022"],           // type definitions available (DOM if browser)

    // Module system
    "module": "NodeNext",        // "NodeNext" for Node.js ESM; "ESNext" for bundlers
    "moduleResolution": "NodeNext", // must match module (NodeNext/Bundler/Node16/Node10)

    // Output
    "outDir": "./dist",
    "rootDir": "./src",
    "declaration": true,         // generate .d.ts files (required for libraries)
    "declarationMap": true,      // source maps for .d.ts (go-to-definition works)
    "sourceMap": true,           // .js.map files for debugging

    // Strictness — enable ALL of these
    "strict": true,              // enables: strictNullChecks, strictFunctionTypes, strictPropertyInitialization, etc.
    "noUncheckedIndexedAccess": true,   // array[i] returns T | undefined (catches off-by-one)
    "noImplicitReturns": true,          // every code path must return
    "noFallthroughCasesInSwitch": true, // switch cases must break or return
    "exactOptionalPropertyTypes": true, // { a?: string } means a is string | undefined, not string | undefined | missing

    // Import hygiene
    "forceConsistentCasingInFileNames": true,  // prevents case-mismatch bugs on Linux
    "verbatimModuleSyntax": true,              // preserves import type — prevents runtime import issues

    // Interop
    "esModuleInterop": true,     // allows default import of CommonJS modules
    "allowSyntheticDefaultImports": true,

    "skipLibCheck": true,        // skip type checking of node_modules .d.ts (faster, saner)
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

# MODULE RESOLUTION — THE CONFUSING PART

## Which moduleResolution to Use
```
Target Environment         | module          | moduleResolution
---------------------------|-----------------|------------------
Node.js (ESM, modern)      | NodeNext        | NodeNext          <- requires .js extensions in imports
Node.js (CJS, classic)     | CommonJS        | Node10            <- no extension required
Vite / webpack / esbuild   | ESNext          | Bundler           <- bundler handles resolution
Next.js                    | preserve        | Bundler           <- Next handles it
Electron main process      | NodeNext/CJS    | NodeNext/Node10
Electron renderer (bundled)| ESNext          | Bundler

NODE.NEXT RULE: imports must use .js extension even for .ts files
  import { foo } from './utils.js';  // yes — even though the file is utils.ts
  // TypeScript resolves utils.ts when you write utils.js — it is correct

BUNDLER: no extension required, bundler resolves
  import { foo } from './utils';     // fine for Vite/webpack projects
```

## Path Aliases
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*":          ["./src/*"],
      "@components/*": ["./src/components/*"],
      "@utils/*":     ["./src/utils/*"],
      "@types/*":     ["./src/types/*"],
      "@hooks/*":     ["./src/hooks/*"]
    }
  }
}
```

### Runtime Resolution for Path Aliases
```
Path aliases are TypeScript-only — they do NOT work at runtime without additional setup.

For Node.js (without bundler):
  npm install -D tsconfig-paths
  node -r tsconfig-paths/register dist/index.js
  OR add to ts-node: { "require": ["tsconfig-paths/register"] }

For Vite:
  npm install -D vite-tsconfig-paths
  // vite.config.ts:
  import tsconfigPaths from 'vite-tsconfig-paths';
  export default { plugins: [tsconfigPaths()] };

For webpack:
  // webpack.config.js:
  const TsconfigPathsPlugin = require('tsconfig-paths-webpack-plugin');
  resolve: { plugins: [new TsconfigPathsPlugin()] }

For Jest:
  // jest.config.js:
  moduleNameMapper: { '^@/(.*)$': '<rootDir>/src/$1' }
```

# ENVIRONMENT-SPECIFIC CONFIGS

## Node.js Application (ESM)
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "sourceMap": true,
    "declaration": false,  // not a library, skip .d.ts
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

## Node.js Library (Published to npm)
```json
{
  "compilerOptions": {
    "target": "ES2020",          // wider compatibility for consumers
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "declaration": true,         // required for library consumers
    "declarationMap": true,
    "sourceMap": true,
    "stripInternal": true,       // remove @internal JSDoc from .d.ts
    "skipLibCheck": true
  },
  "include": ["src"],
  "exclude": ["src/**/*.test.ts", "src/**/*.spec.ts"]
}
```

## Vite / React Browser App
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "jsx": "react-jsx",          // for React 17+ automatic JSX runtime
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "verbatimModuleSyntax": true,
    "allowImportingTsExtensions": true,  // allows .ts/.tsx imports (bundler resolves)
    "noEmit": true,              // Vite handles transpilation — tsc only type-checks
    "skipLibCheck": true,
    "baseUrl": ".",
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["src"]
}
```

## Electron App (Split Config)
```
Electron needs TWO tsconfig files — main process and renderer are different environments.
```

```json
// tsconfig.main.json (Node.js environment)
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "CommonJS",
    "moduleResolution": "Node10",
    "outDir": "dist/main",
    "rootDir": "src/main",
    "strict": true,
    "sourceMap": true,
    "skipLibCheck": true
  },
  "include": ["src/main", "src/shared"]
}
```

```json
// tsconfig.renderer.json (Browser + bundler environment)
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "jsx": "react-jsx",
    "noEmit": true,
    "strict": true,
    "skipLibCheck": true,
    "baseUrl": ".",
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["src/renderer", "src/shared", "src/preload"]
}
```

# PROJECT REFERENCES (Monorepo)

## Why Project References
```
Without: compiling package-a compiles all of package-b too → slow
With:    each package compiled separately, incremental builds, correct watch mode

Requires: composite: true + declaration: true in each package tsconfig
```

## Package tsconfig (packages/utils/tsconfig.json)
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "./dist",
    "rootDir": "./src",
    "composite": true,      // required for project references
    "declaration": true,    // required for project references
    "declarationMap": true,
    "strict": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

## Root tsconfig.json (References All Packages)
```json
{
  "files": [],  // root itself has no source files
  "references": [
    { "path": "./packages/utils" },
    { "path": "./packages/ui" },
    { "path": "./packages/api" },
    { "path": "./apps/web" },
    { "path": "./apps/desktop" }
  ]
}
```

## Build Commands with Project References
```bash
# Build all packages in correct order (respects references)
tsc --build

# Watch mode
tsc --build --watch

# Clean build artifacts
tsc --build --clean

# Force rebuild
tsc --build --force
```

# STRICT MODE — WHAT EACH FLAG DOES
```
strict: true enables all of:
  strictNullChecks:             null and undefined are not assignable to other types
  strictFunctionTypes:          function parameter types checked contravariantly
  strictBindCallApply:          bind, call, apply are type-checked
  strictPropertyInitialization: class properties must be initialized in constructor
  noImplicitAny:                error on implicit any type inference
  noImplicitThis:               error on 'this' with implicit any type
  alwaysStrict:                 'use strict' in all files

BEYOND strict — also add these:
  noUncheckedIndexedAccess:     arr[0] returns T | undefined (not T)
    IMPORTANT: without this, TypeScript lies to you about array access safety

  exactOptionalPropertyTypes:   { a?: string } disallows setting a = undefined explicitly
    fixes: function({ a }: { a?: string }) — a cannot be set to undefined, only omitted

  noImplicitReturns:            all code paths must return a value
  noFallthroughCasesInSwitch:   switch cases must break or return
```

# COMMON MISTAKES
```
X  moduleResolution does not match module:
   "module": "NodeNext" + "moduleResolution": "Node10"  — mismatch, wrong resolution behavior

X  Forgetting .js extensions with NodeNext:
   import { foo } from './utils';   — error in NodeNext
   import { foo } from './utils.js' — correct (TS resolves to utils.ts)

X  Path aliases not configured in runtime resolver:
   Works in tsc but crashes at runtime — need tsconfig-paths, vite-tsconfig-paths, etc.

X  "noEmit": true on a library:
   Library needs to emit .js and .d.ts — noEmit is for apps where bundler does emit

X  skipLibCheck: false in large projects:
   Causes slow builds and errors from node_modules types you cannot fix
   Always use skipLibCheck: true

X  Missing "lib" for DOM:
   Browser project gets errors on document, window, fetch without "DOM" in lib
```

# CHECKLIST
```
[ ] strict: true + noUncheckedIndexedAccess: true enabled
[ ] module and moduleResolution match (NodeNext+NodeNext, ESNext+Bundler)
[ ] .js extensions used in imports for NodeNext projects
[ ] Path aliases configured in runtime too (not just tsconfig)
[ ] Library: declaration: true and declarationMap: true
[ ] App with bundler: noEmit: true (let bundler handle transpile)
[ ] Electron: separate tsconfigs for main and renderer
[ ] Monorepo: composite: true + project references configured
[ ] outDir points to correct location (not cluttering src/)
[ ] exclude includes node_modules and dist
[ ] skipLibCheck: true (safe, required for sanity)