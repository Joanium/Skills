---
name: Package Scripts Automation
trigger: npm scripts, package.json scripts, build automation, npm run, cross-platform scripts, concurrently, npm-run-all, task automation, pre and post scripts, script hooks, package scripts patterns, makefile npm, build scripts
description: Design clean, cross-platform npm script workflows. Covers script composition, pre/post hooks, parallel execution, environment handling, and patterns for build, test, and release pipelines.
---

# ROLE
You are an automation engineer who knows that a well-designed package.json scripts section is documentation, a task runner, and a CI/CD contract all in one. You write scripts that work the same on Windows, macOS, and Linux, that new developers understand immediately, and that CI can rely on without Makefile complexity.

# ANATOMY OF A GOOD SCRIPTS SECTION
```json
{
  "scripts": {
    "// DEV": "──────── Development ────────",
    "dev":         "vite",
    "dev:debug":   "DEBUG=* vite",

    "// BUILD": "──────── Build ────────",
    "build":       "tsc && vite build",
    "build:watch": "tsc --watch",
    "build:analyze": "ANALYZE=true vite build",

    "// TEST": "──────── Testing ────────",
    "test":        "vitest run",
    "test:watch":  "vitest",
    "test:coverage": "vitest run --coverage",
    "test:e2e":    "playwright test",

    "// QUALITY": "──────── Code Quality ────────",
    "lint":        "eslint src --ext .ts,.tsx",
    "lint:fix":    "eslint src --ext .ts,.tsx --fix",
    "format":      "prettier --write \"src/**/*.{ts,tsx,css}\"",
    "format:check": "prettier --check \"src/**/*.{ts,tsx,css}\"",
    "typecheck":   "tsc --noEmit",

    "// RELEASE": "──────── Release ────────",
    "clean":       "rimraf dist",
    "prebuild":    "npm run clean && npm run typecheck",
    "release":     "npm run build && npm publish"
  }
}
```

# PRE AND POST HOOKS

## Automatic Hook Execution
```json
{
  "scripts": {
    "prebuild":    "npm run clean",          // runs BEFORE 'build' automatically
    "build":       "tsc && vite build",
    "postbuild":   "npm run compress-assets", // runs AFTER 'build' automatically

    "pretest":     "npm run typecheck",
    "test":        "vitest run",
    "posttest":    "npm run coverage-report",

    "preinstall":  "node scripts/check-node-version.js",
    "postinstall": "electron-builder install-app-deps",  // for Electron
    "prepare":     "husky"                               // runs after npm install
  }
}
```

# PARALLEL AND SEQUENTIAL EXECUTION

## concurrently — Run Multiple Scripts at Once
```bash
npm install -D concurrently
```

```json
{
  "scripts": {
    "dev": "concurrently --names VITE,TS --prefix-colors cyan,yellow \"vite\" \"tsc --watch\"",
    "dev:electron": "concurrently --kill-others-on-fail \"npm:dev:main\" \"npm:dev:renderer\"",
    "dev:main":     "tsc -p tsconfig.main.json --watch",
    "dev:renderer": "vite"
  }
}
```

## npm-run-all — Sequential or Parallel
```bash
npm install -D npm-run-all2
```

```json
{
  "scripts": {
    // Sequential (run-s = run serial)
    "ci": "run-s typecheck lint test build",

    // Parallel (run-p = run parallel)
    "check": "run-p typecheck lint format:check",

    // Mix: sequential with parallel step
    "validate": "run-s clean typecheck run-p:lint+test build",

    // Glob matching — runs all scripts matching pattern
    "build:all": "run-s \"build:*\"",
    "test:all":  "run-p \"test:unit\" \"test:integration\""
  }
}
```

# CROSS-PLATFORM SCRIPTS

## The Problem
```bash
# These do NOT work on Windows:
"clean": "rm -rf dist"                  # Windows has no rm
"dev": "NODE_ENV=development vite"     # Windows cannot set env vars inline
"copy": "cp -r src/assets dist/"       # Windows has no cp

# Use cross-platform alternatives instead:
```

## Solutions
```bash
npm install -D rimraf cross-env copyfiles mkdirp
```

```json
{
  "scripts": {
    // File operations — cross-platform
    "clean":       "rimraf dist",
    "clean:all":   "rimraf dist coverage .turbo",
    "mkdir":       "mkdirp dist/assets",
    "copy:assets": "copyfiles -u 1 \"src/assets/**/*\" dist/",

    // Environment variables — cross-platform
    "dev":         "cross-env NODE_ENV=development vite",
    "build:prod":  "cross-env NODE_ENV=production vite build",
    "test":        "cross-env CI=true vitest run",

    // Alternative: use .env files + dotenv-cli
    "dev:staging": "dotenv -e .env.staging -- vite"
  }
}
```

## Node.js Script for Complex Operations
```javascript
// scripts/clean.js — use when shell scripts get complicated
const fs = require('fs');
const path = require('path');

const dirs = ['dist', 'coverage', '.turbo', 'node_modules/.cache'];

for (const dir of dirs) {
  const resolved = path.resolve(process.cwd(), dir);
  if (fs.existsSync(resolved)) {
    fs.rmSync(resolved, { recursive: true, force: true });
    console.log(`Removed: ${dir}`);
  }
}
```

```json
{ "scripts": { "clean": "node scripts/clean.js" } }
```

# ENVIRONMENT HANDLING

## .env Files Convention
```
.env                  # loaded always (base values)
.env.local            # local overrides, gitignored
.env.development      # development mode
.env.production       # production mode
.env.test             # test mode
.env.*.local          # local mode-specific overrides, gitignored
```

```json
{
  "scripts": {
    "dev":        "vite",                              // Vite loads .env automatically
    "test":       "vitest run",                        // Vitest loads .env.test
    "dev:staging":"dotenv -e .env.staging -- vite",    // custom env file
    "build:prod": "dotenv -e .env.production -- vite build"
  }
}
```

# VERSION AND RELEASE SCRIPTS

## Semantic Versioning Workflow
```json
{
  "scripts": {
    "version:patch": "npm version patch -m \"chore: release %s\"",
    "version:minor": "npm version minor -m \"chore: release %s\"",
    "version:major": "npm version major -m \"chore: release %s\"",

    "preversion":  "npm run validate",
    "postversion": "git push && git push --tags",

    "release":     "run-s build release:publish",
    "release:publish": "npm publish --access public",
    "release:dry":     "npm publish --dry-run"
  }
}
```

## Changelog Generation
```json
{
  "scripts": {
    "changelog": "conventional-changelog -p angular -i CHANGELOG.md -s",
    "release:full": "run-s version:patch changelog release"
  }
}
```

# UTILITY SCRIPTS

## Useful One-Liners
```json
{
  "scripts": {
    // List all outdated packages
    "deps:check":  "npm outdated",
    // Update all packages (interactive)
    "deps:update": "npx npm-check-updates -i",
    // Check for security vulnerabilities
    "deps:audit":  "npm audit --audit-level=moderate",
    // Fix vulnerabilities automatically
    "deps:fix":    "npm audit fix",

    // Print all script names (self-documenting)
    "help":        "node -e \"const s=require('./package.json').scripts;Object.keys(s).filter(k=>!k.startsWith('//') && !k.startsWith('pre') && !k.startsWith('post')).forEach(k=>console.log(k))\"",

    // Bundle size analysis
    "size":        "bundlesize",
    "size:why":    "npx why-is-node-running",

    // Generate types from OpenAPI spec
    "gen:types":   "openapi-typescript api/spec.yaml -o src/types/api.ts",
    // Sync Prisma schema
    "db:generate": "prisma generate",
    "db:migrate":  "prisma migrate dev",
    "db:studio":   "prisma studio",
    "db:seed":     "tsx src/db/seed.ts",
    "db:reset":    "prisma migrate reset"
  }
}
```

# MONOREPO SCRIPTS

## Workspaces Pattern
```json
{
  "scripts": {
    // Run script in specific workspace
    "build:api":  "npm run build --workspace=packages/api",
    "build:ui":   "npm run build --workspace=packages/ui",

    // Run same script in all workspaces
    "build:all":  "npm run build --workspaces --if-present",
    "test:all":   "npm run test --workspaces --if-present",
    "lint:all":   "npm run lint --workspaces --if-present",

    // Turbo (if using Turborepo)
    "build":      "turbo run build",
    "dev":        "turbo run dev --parallel",
    "test":       "turbo run test",
    "lint":       "turbo run lint"
  }
}
```

# ELECTRON-SPECIFIC SCRIPTS
```json
{
  "scripts": {
    "// ELECTRON": "──────── Electron ────────",
    "dev":              "concurrently \"npm:dev:main\" \"npm:dev:renderer\" \"wait-on http://localhost:5173 && electron .\"",
    "dev:main":         "cross-env NODE_ENV=development tsc -p tsconfig.main.json --watch",
    "dev:renderer":     "vite",

    "build":            "run-s build:renderer build:main",
    "build:renderer":   "vite build",
    "build:main":       "tsc -p tsconfig.main.json",

    "dist":             "run-s build dist:pack",
    "dist:pack":        "electron-builder",
    "dist:win":         "electron-builder --win",
    "dist:mac":         "electron-builder --mac",
    "dist:linux":       "electron-builder --linux",
    "dist:dir":         "electron-builder --dir",  // unpackaged build for testing

    "postinstall":      "electron-builder install-app-deps"
  }
}
```

# SCRIPT DOCUMENTATION PATTERN
```json
{
  "scripts": {
    "//": "Run 'npm run help' to list all available scripts",

    "// === DEVELOPMENT ===": "",
    "dev":  "Start development server (http://localhost:5173)",
    "// PRODUCTION": "Use 'npm run build' then serve dist/",

    "// === QUALITY ===": "",
    "ci":   "run-s typecheck lint test build | Full CI pipeline",
    "fix":  "run-s lint:fix format       | Auto-fix all lint and format issues"
  }
}
```

# CHECKLIST
```
[ ] Cross-platform: rimraf not rm -rf, cross-env not VAR=value inline
[ ] Lifecycle hooks: prebuild cleans, pretest typechecks
[ ] Parallel where possible: typecheck + lint + format:check together with run-p
[ ] Sequential for CI: typecheck then test then build with run-s
[ ] ci script: one command that does everything needed in CI
[ ] clean script defined and called before every fresh build
[ ] Common scripts named consistently: dev, build, test, lint, format, typecheck
[ ] Electron: separate build:main and build:renderer scripts
[ ] .env loading handled (Vite/Vitest auto-load, custom use dotenv-cli)
[ ] No platform-specific commands (rm, cp, export) — use Node scripts or cross-platform tools