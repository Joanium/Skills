---
name: Git Guardrails for Claude Code
trigger: git guardrails, block git push, prevent git reset, git safety hooks, dangerous git commands, block destructive git
description: Set up Claude Code hooks to block dangerous git commands (push, reset --hard, clean, branch -D, etc.) before they execute.
---

Agents and automation are powerful — and dangerous when they can run `git push --force` or `git reset --hard` without human review. This skill sets up a PreToolUse hook that intercepts and blocks destructive git commands before Claude executes them.

## What Gets Blocked

- `git push` (all variants including `--force`)
- `git reset --hard`
- `git clean -f` / `git clean -fd`
- `git branch -D`
- `git checkout .` / `git restore .`

When blocked, Claude sees a message: _"The user has prevented you from doing this."_

---

## Process

### Step 1: Choose scope

Ask the user:

- **This project only** → `.claude/settings.json`
- **All projects globally** → `~/.claude/settings.json`

### Step 2: Create the hook script

**Project:** `.claude/hooks/block-dangerous-git.sh`
**Global:** `~/.claude/hooks/block-dangerous-git.sh`

```bash
#!/bin/bash

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')

DANGEROUS_PATTERNS=(
  "git push"
  "git reset --hard"
  "git clean -fd"
  "git clean -f"
  "git branch -D"
  "git checkout \."
  "git restore \."
  "push --force"
  "reset --hard"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qE "$pattern"; then
    echo "BLOCKED: '$COMMAND' matches dangerous pattern '$pattern'. The user has prevented you from doing this." >&2
    exit 2
  fi
done

exit 0
```

Make it executable:

```bash
chmod +x <path-to-script>
```

### Step 3: Add hook to settings

**Project** (`.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-dangerous-git.sh"
          }
        ]
      }
    ]
  }
}
```

**Global** (`~/.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block-dangerous-git.sh"
          }
        ]
      }
    ]
  }
}
```

If the settings file already exists, **merge** — don't overwrite other settings.

### Step 4: Ask about customization

Ask if the user wants to add or remove any blocked patterns. Edit the script accordingly.

### Step 5: Verify

```bash
echo '{"tool_input":{"command":"git push origin main"}}' | <path-to-script>
```

Should exit with code `2` and print a BLOCKED message to stderr.

---

## Common Mistakes

**[CRITICAL]** Overwriting existing `settings.json` — always merge, never replace. Check for existing hooks before writing.

**[CRITICAL]** Forgetting `chmod +x` — the hook won't execute without it.

**[IMPORTANT]** Setting up globally when only needed for one project — global hooks run on every Claude Code session. Start with project scope.

**[SUGGESTION]** The hook patterns use `grep -qE` (extended regex). Test your patterns before adding them.
