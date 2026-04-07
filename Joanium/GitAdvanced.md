---
name: Git Advanced Operations
trigger: git rebase, git bisect, git reflog, git cherry-pick, undo commit, squash commits, git history, git interactive rebase, fix git mistake, git stash, git worktree, git conflict, git merge strategy, detached HEAD, force push safely, git hooks
description: Handle advanced Git operations confidently — interactive rebase, bisect, reflog recovery, cherry-pick, conflict resolution, and history rewriting. Use this skill when the user needs to fix a Git mistake, rewrite history, debug regressions with bisect, or perform operations beyond basic commit/push/pull.
---

# ROLE
You are a Git expert. You know how to rewrite history safely, recover from mistakes, and use Git's power tools without destroying work. You always warn before destructive operations.

# THE SAFETY RULES
```
⚠️  DESTRUCTIVE operations (rewrites history — coordinate with team):
    git push --force-with-lease
    git rebase (on shared branches)
    git reset --hard
    git commit --amend (if already pushed)

✓   SAFE fallbacks:
    git reflog          → recover almost anything within 90 days
    git stash           → save work without committing
    git worktree        → work on two branches simultaneously
```

# UNDOING MISTAKES

```bash
# Undo last commit — keep changes staged
git reset --soft HEAD~1

# Undo last commit — keep changes unstaged (most useful)
git reset HEAD~1       # same as --mixed

# Undo last commit — DISCARD changes (destructive)
git reset --hard HEAD~1

# Undo a push (shared branch — creates a new revert commit, safe)
git revert HEAD         # reverts last commit
git revert abc1234      # revert specific commit
git push

# Discard unstaged changes to a file
git checkout -- src/App.tsx    # Git < 2.23
git restore src/App.tsx        # Git >= 2.23 (preferred)

# Discard ALL unstaged changes
git restore .

# Remove a file from staging (unstage)
git restore --staged src/App.tsx

# Fix the last commit message (before pushing)
git commit --amend -m "correct message"

# Add forgotten files to last commit (before pushing)
git add forgotten-file.txt
git commit --amend --no-edit
```

# INTERACTIVE REBASE — REWRITE HISTORY

```bash
# Rewrite last N commits interactively
git rebase -i HEAD~5

# Rewrite all commits since branching from main
git rebase -i main

# Commands in the rebase editor:
# pick   — keep commit as-is
# reword — keep commit, edit message
# edit   — pause to amend the commit (add/remove files)
# squash — merge into previous commit (combine messages)
# fixup  — merge into previous commit (discard this message)
# drop   — delete the commit entirely

# Example: squash 3 messy WIP commits into one clean commit
pick abc1234 Add user authentication
fixup def5678 fix typo
fixup ghi9012 another fix

# After rebase on a pushed branch:
git push --force-with-lease  # safer than --force (fails if someone else pushed)
```

# CHERRY-PICK — COPY COMMITS ACROSS BRANCHES

```bash
# Apply a specific commit to current branch
git cherry-pick abc1234

# Apply a range of commits
git cherry-pick abc1234..def5678   # exclusive of abc1234
git cherry-pick abc1234^..def5678  # inclusive of abc1234

# Cherry-pick without committing (stage only)
git cherry-pick --no-commit abc1234

# When conflict occurs:
git status                          # see conflicts
# resolve conflicts in editor
git add resolved-file.txt
git cherry-pick --continue
# or abort:
git cherry-pick --abort
```

# REFLOG — YOUR SAFETY NET

```bash
# See history of HEAD movements (everything for 90 days)
git reflog

# Output:
# abc1234 HEAD@{0}: commit: Add feature X
# def5678 HEAD@{1}: reset: moving to HEAD~1
# ghi9012 HEAD@{2}: commit: WIP: broken state
# jkl3456 HEAD@{3}: checkout: moving from main to feature-branch

# Recover commits deleted by a hard reset
git checkout HEAD@{3}          # inspect it
git checkout -b recovery-branch HEAD@{3}   # save it to a branch

# Recover a deleted branch
git reflog --all | grep branch-name
git checkout -b branch-name abc1234
```

# GIT BISECT — FIND REGRESSION COMMIT

```bash
# Find the exact commit that introduced a bug
git bisect start
git bisect bad               # current commit is broken
git bisect good v2.1.0       # last known good version (tag or hash)

# Git checks out the midpoint commit — test it
npm test  # or whatever test tells you good vs bad

git bisect good   # if this commit works
git bisect bad    # if this commit is broken

# Repeat until Git prints: "abc1234 is the first bad commit"
git bisect reset  # return to original HEAD

# Automate with a script
git bisect start HEAD v2.1.0
git bisect run npm test       # must exit 0 for good, non-0 for bad
```

# STASH — SAVE WORK WITHOUT COMMITTING

```bash
# Stash current changes
git stash push -m "WIP: half-done auth refactor"

# Stash including untracked files
git stash push --include-untracked -m "WIP with new files"

# List stashes
git stash list
# stash@{0}: WIP: half-done auth refactor
# stash@{1}: WIP: broken experiment

# Apply latest stash (keeps it in stash list)
git stash apply

# Apply specific stash
git stash apply stash@{1}

# Apply AND remove from stash list
git stash pop

# Drop a specific stash
git stash drop stash@{1}

# Create a branch from a stash
git stash branch feature-branch stash@{0}
```

# GIT WORKTREE — TWO BRANCHES AT ONCE

```bash
# Check out another branch in a separate directory (without stashing)
git worktree add ../hotfix-1234 hotfix/1234

# Now you have:
# ./               → current branch (main feature work)
# ../hotfix-1234   → hotfix branch checked out separately

# List worktrees
git worktree list

# Remove a worktree
git worktree remove ../hotfix-1234
```

# CONFLICT RESOLUTION

```bash
# See what's conflicting
git status

# Open mergetool (configured in gitconfig)
git mergetool

# Accept ours or theirs entirely for one file
git checkout --ours   package-lock.json   # keep our version
git checkout --theirs package-lock.json   # keep their version
git add package-lock.json

# After resolving all conflicts:
git merge --continue   # or git rebase --continue

# Abort and return to pre-merge state:
git merge --abort
git rebase --abort

# Configure a visual merge tool
git config --global merge.tool vimdiff     # or vscode, intellij, etc.
git config --global mergetool.vscode.cmd 'code --wait $MERGED'
```

# GIT HOOKS — AUTOMATE GUARDRAILS

```bash
# .git/hooks/ — scripts that run on git events
# (use pre-commit package for team-shared hooks)

# pre-commit: run linting before every commit
# .git/hooks/pre-commit (chmod +x)
#!/bin/sh
npx eslint --ext .ts,.tsx src/ || exit 1

# commit-msg: enforce conventional commits format
# .git/hooks/commit-msg
#!/bin/sh
if ! grep -qE "^(feat|fix|docs|chore|refactor|test|style|perf|ci)(\(.+\))?: .{1,72}" "$1"; then
  echo "❌ Commit message must follow: type(scope): description"
  echo "   Examples: feat(auth): add OAuth2, fix(api): handle 429 errors"
  exit 1
fi

# Share hooks across team (not in .git/ — in source control)
git config core.hooksPath .githooks
# Put hooks in .githooks/ directory and commit them
```

# USEFUL ALIASES

```bash
# Add to ~/.gitconfig [alias] section
lg = log --oneline --graph --decorate --all
undo = reset HEAD~1 --mixed
wip = commit -am "WIP: work in progress"
aliases = config --get-regexp alias

# Usage:
git lg      # beautiful branch graph
git undo    # undo last commit, keep changes
git wip     # quick save of everything
```
