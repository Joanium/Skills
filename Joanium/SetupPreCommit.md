---
name: Setup Pre-Commit Hooks
trigger: setup pre-commit, add pre-commit hooks, husky, lint-staged, commit hooks, pre commit formatting, typecheck on commit
description: Set up Husky pre-commit hooks with lint-staged (Prettier), type checking, and tests in the current repo.
---

A great pre-commit setup catches problems at the moment of commit — formatting issues before they hit PR, type errors before they hit CI, broken tests before they hit main. The goal is fast, targeted checks on staged files only.

## What This Sets Up

- **Husky** — pre-commit hook runner
- **lint-staged** — runs Prettier on staged files only (fast)
- **typecheck** — full type check on commit
- **tests** — test suite run on commit

---

## Steps

### Step 1: Detect package manager

Check for lockfiles:

- `package-lock.json` → npm
- `pnpm-lock.yaml` → pnpm
- `yarn.lock` → yarn
- `bun.lockb` → bun

Default to npm if unclear.

### Step 2: Install dependencies

```bash
# npm
npm install --save-dev husky lint-staged prettier

# pnpm
pnpm add -D husky lint-staged prettier

# yarn
yarn add -D husky lint-staged prettier
```

### Step 3: Initialize Husky

```bash
npx husky init
```

This creates `.husky/` and adds `"prepare": "husky"` to `package.json`.

### Step 4: Create `.husky/pre-commit`

```bash
npx lint-staged
npm run typecheck
npm run test
```

**Adapt to detected package manager.** If the repo has no `typecheck` or `test` script in `package.json`, omit those lines and tell the user.

### Step 5: Create `.lintstagedrc`

```json
{
  "*": "prettier --ignore-unknown --write"
}
```

### Step 6: Create `.prettierrc` (only if missing)

Do NOT overwrite an existing Prettier config.

```json
{
  "useTabs": false,
  "tabWidth": 2,
  "printWidth": 80,
  "singleQuote": false,
  "trailingComma": "es5",
  "semi": true,
  "arrowParens": "always"
}
```

### Step 7: Verify

```
[ ] .husky/pre-commit exists and is executable
[ ] .lintstagedrc exists
[ ] "prepare": "husky" is in package.json scripts
[ ] Prettier config exists
[ ] npx lint-staged runs without errors
```

### Step 8: Commit

Stage all new/changed files and commit:

```
Add pre-commit hooks (husky + lint-staged + prettier)
```

This runs through the new hooks — a good smoke test that everything works.

---

## Common Mistakes

**[CRITICAL]** Using a shebang (`#!/bin/sh`) in Husky v9 hook files — Husky v9+ doesn't need or want shebangs.

**[CRITICAL]** Overwriting an existing Prettier config — always check before creating `.prettierrc`.

**[IMPORTANT]** Adding `typecheck` or `test` to the hook when those scripts don't exist — this will break every commit. Check `package.json` first.

**[SUGGESTION]** `prettier --ignore-unknown` skips files Prettier can't parse (images, binaries). Always include this flag.

---

## Review Summary

**Overall:** Pre-commit hooks are only useful if they're fast. lint-staged on staged files only is the key to keeping them snappy.

**Must verify before done:**

- Running `git commit` actually triggers the hooks
- `npx lint-staged` runs without errors on the current staged files
- typecheck/test scripts exist if referenced in the hook
