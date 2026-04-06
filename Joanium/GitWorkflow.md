---
name: Git Workflow
trigger: git workflow, branching strategy, git rebase, git merge, pull request, commit message, git flow, trunk based development, git cherry-pick, git bisect, git stash, git reset, git reflog, resolve merge conflict, git best practices
description: Master Git for professional team development. Covers branching strategies (Git Flow vs trunk-based), commit message conventions, rebase vs merge, pull request workflow, conflict resolution, and power commands for history manipulation and debugging.
---

# ROLE
You are a Git expert and version control architect. Your job is to keep project history clean, make collaboration smooth, and help teams ship confidently. Good Git history is documentation — future you will thank past you.

# BRANCHING STRATEGIES

## Trunk-Based Development (Recommended for Most Teams)
```
main ─────────────────────────────────────────── (always deployable)
       │          │          │
   feature/A  feature/B  feature/C
   (< 2 days) (< 2 days) (< 2 days)

Rules:
- feature branches live max 1-2 days
- merge to main frequently (at least daily)
- use feature flags for incomplete features
- CI must pass before merge
- no long-lived branches
```

## Git Flow (For Scheduled Releases / Libraries)
```
main     ──────────────────────────────────── (production releases only)
           ↑ merge via PR         ↑ hotfix
develop  ───────────────────────────────────  (integration branch)
           │         │
       feature/A  feature/B
                      │
                  release/1.2    (stabilization branch — only bugfixes)
```

## Branch Naming Conventions
```bash
feature/JIRA-123-add-user-auth
feature/add-oauth-login
fix/JIRA-456-null-pointer-on-login
fix/email-validation-edge-case
chore/update-dependencies
chore/upgrade-node-20
docs/api-authentication-guide
refactor/extract-payment-service
release/v1.4.0
hotfix/JIRA-789-payment-crash
```

# COMMIT MESSAGES — CONVENTIONAL COMMITS

## Format
```
<type>(<scope>): <short description>

[optional body — what and why, not how]

[optional footer: BREAKING CHANGE, closes #123]
```

## Types
```
feat:     new feature
fix:      bug fix
chore:    maintenance, dependency updates (no production code change)
docs:     documentation only
style:    formatting, whitespace (no logic change)
refactor: code restructure (no feature/fix)
test:     adding or fixing tests
perf:     performance improvement
ci:       CI/CD pipeline changes
build:    build system changes
revert:   reverts a previous commit
```

## Examples
```bash
# Good commits
feat(auth): add JWT refresh token rotation
fix(payments): handle null card expiry in Stripe webhook
chore(deps): upgrade express from 4.18 to 4.19
refactor(users): extract email validation into utility function
perf(db): add index on orders.user_id for faster lookups
test(auth): add unit tests for token expiry edge cases

# Good commit with body
feat(notifications): add email digest for weekly summaries

Users can now opt-in to weekly digest emails summarizing
their activity. Respects existing email preferences.

Closes #234

# Breaking change
feat(api)!: change /users response to include pagination wrapper

BREAKING CHANGE: /users now returns { data: User[], pagination: {...} }
instead of User[] directly. Update all API consumers.

# Bad commits — don't do this
fix stuff
WIP
asdfgh
Updated files
Fixing the bug from yesterday
```

# REBASE VS MERGE

## Rebase — Clean Linear History
```bash
# Scenario: main has moved on while you worked on feature branch
#
# Before:
# main:    A─B─C─D
#               └─E─F (your feature branch)
#
# After merge:
# main:    A─B─C─D───G   (G is a merge commit)
#               └─E─F─┘
#
# After rebase:
# main:    A─B─C─D─E'─F'  (clean linear history, E and F replayed on top of D)

# Rebase your feature branch onto main
git checkout feature/my-feature
git rebase main

# If conflicts arise, resolve then:
git add .
git rebase --continue

# Or abort and go back:
git rebase --abort

# Interactive rebase — rewrite last 3 commits
git rebase -i HEAD~3
# Opens editor:
# pick abc123 add login form
# pick def456 fix typo
# pick ghi789 add validation
#
# Commands:
# pick   = keep as-is
# reword = keep but edit message
# edit   = stop and amend
# squash = melt into previous commit
# fixup  = like squash but discard this message
# drop   = remove this commit entirely
```

## When to Use What
```
MERGE:
  ✓ Merging feature branches into main/develop (preserves context)
  ✓ When branch is shared with others (rewriting shared history = bad)
  ✓ When you want to preserve exact timeline

REBASE:
  ✓ Syncing your local feature branch with upstream main
  ✓ Cleaning up commits before PR (squash WIP commits)
  ✓ Keeping feature branch history linear and readable
  ✗ Never rebase commits already pushed to shared branches
  ✗ Never rebase main or develop

GOLDEN RULE: Never rewrite history that others have based work on
```

# RESOLVING MERGE CONFLICTS
```bash
# When a merge conflict occurs:
git merge main
# CONFLICT (content): Merge conflict in src/auth.ts

# See all conflicted files
git status

# A conflicted file looks like:
# <<<<<<< HEAD (your changes)
# const timeout = 5000
# =======
# const timeout = 3000
# >>>>>>> main (incoming changes)

# Resolution options:
git checkout --ours src/auth.ts     # keep your version entirely
git checkout --theirs src/auth.ts   # keep incoming version entirely
# Or manually edit the file, then:
git add src/auth.ts

# Use a visual merge tool
git mergetool    # opens configured tool (VS Code, vimdiff, etc.)

# After resolving all conflicts:
git merge --continue   # or git commit

# Configure VS Code as merge tool
git config --global merge.tool vscode
git config --global mergetool.vscode.cmd 'code --wait $MERGED'
```

# UNDOING MISTAKES

## The Undo Toolkit
```bash
# ─── Undo staged changes (unstage, keep in working tree) ──────────────────
git restore --staged src/file.ts    # specific file
git restore --staged .              # everything

# ─── Discard working tree changes (DESTRUCTIVE — unrecoverable) ──────────
git restore src/file.ts             # specific file
git restore .                       # everything

# ─── Amend last commit (not pushed yet) ───────────────────────────────────
git add forgotten-file.ts
git commit --amend                  # edit message too
git commit --amend --no-edit        # keep message, just add file

# ─── Undo commits (keep changes staged) ───────────────────────────────────
git reset --soft HEAD~1             # undo 1 commit, keep changes staged
git reset --soft HEAD~3             # undo 3 commits

# ─── Undo commits (keep changes in working tree, unstaged) ────────────────
git reset --mixed HEAD~1            # default behavior of git reset HEAD~1

# ─── Undo commits (DESTRUCTIVE — discard changes entirely) ───────────────
git reset --hard HEAD~1             # CAREFUL: changes are gone

# ─── Safe undo for pushed commits ─────────────────────────────────────────
git revert abc123                   # creates new commit that undoes abc123
git revert HEAD~3..HEAD             # revert last 3 commits

# ─── The lifeline: reflog ─────────────────────────────────────────────────
git reflog                          # every HEAD movement is recorded
git reset --hard HEAD@{3}           # go back 3 HEAD positions
# Even after git reset --hard, you can recover via reflog for ~30 days
```

# POWER COMMANDS

## Stash
```bash
git stash                           # stash all tracked changes
git stash push -m "WIP: payment UI" # with description
git stash push -u                   # include untracked files
git stash list                      # see all stashes
git stash pop                       # apply most recent + remove from stash
git stash apply stash@{2}           # apply specific stash (keep in stash list)
git stash drop stash@{1}            # remove specific stash
git stash branch feature/new        # create branch from stash
```

## Cherry-Pick
```bash
# Apply a specific commit to current branch
git cherry-pick abc123              # single commit
git cherry-pick abc123..def456      # range of commits
git cherry-pick abc123 --no-commit  # apply changes but don't commit yet

# Use case: hotfix needs to go to main AND release branch
git checkout release/1.2
git cherry-pick hotfix-commit-sha
```

## Bisect — Find Which Commit Introduced a Bug
```bash
git bisect start
git bisect bad                      # current commit is bad
git bisect good v1.3.0              # last known good commit/tag

# Git checks out a midpoint commit — test if bug exists
# If bug present:
git bisect bad
# If bug not present:
git bisect good

# Repeat until git identifies the culprit commit
# When done:
git bisect reset

# Automate with a test script:
git bisect start HEAD v1.3.0
git bisect run npm test             # runs tests; non-zero exit = bad
```

## Other Useful Commands
```bash
# See who changed each line in a file
git blame src/payments.ts
git blame -L 50,80 src/payments.ts  # only lines 50-80

# Search commit history for when a string appeared
git log -S "stripeSecretKey" --source --all

# See all branches containing a commit
git branch --contains abc123
git branch -r --contains abc123     # remote branches

# Clean untracked files
git clean -fd                       # remove untracked files and dirs
git clean -fdn                      # dry run first (see what would be removed)

# Partial staging — stage specific lines
git add -p src/file.ts              # interactively stage hunks

# See diff of staged changes
git diff --staged

# Compact log with graph
git log --oneline --graph --decorate --all
```

# PULL REQUEST CHECKLIST
```
Before opening a PR:
[ ] Self-review the diff — read every line as if you're the reviewer
[ ] PR title follows conventional commit format
[ ] Description explains WHAT changed and WHY (not HOW — that's in the code)
[ ] Tests added or updated for changed behavior
[ ] No debug logs, commented-out code, or TODOs without tickets
[ ] All CI checks pass locally (lint, test, build)
[ ] Branch is up-to-date with main (rebased or merged)
[ ] Breaking changes documented
[ ] Screenshots/screen recording for UI changes

Good PR description template:
## What
Brief description of what this changes.

## Why
The problem this solves or the reason for the change.

## How (optional)
Any non-obvious implementation details the reviewer should know.

## Testing
How to test this manually, if applicable.

## Checklist
- [ ] Tests added
- [ ] Docs updated
- [ ] No breaking changes (or documented)
```
