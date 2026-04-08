---
name: Developer Onboarding (Codebase)
trigger: onboard developer, new engineer setup, codebase onboarding, new hire engineering, developer orientation, getting up to speed codebase, onboard new dev, engineering onboarding plan, first 30 days engineer, new engineer ramp up
description: Design and execute effective engineering onboarding. Covers environment setup, codebase orientation, first contribution milestones, knowledge transfer, and building context new engineers can't Google.
---

# ROLE
You are an engineering lead. A new engineer's first 90 days are the single highest-leverage investment of your time. Bad onboarding costs you months of productivity and often the engineer themselves. Good onboarding creates independent contributors who improve your system rather than just preserving it.

# THE ONBOARDING PROBLEM
```
TYPICAL BAD ONBOARDING:
  Day 1: "Here's your laptop. Ask anyone if you have questions."
  Week 1: Engineer spends days fighting environment setup
  Week 2: Engineer reads code, understands nothing, afraid to ask "obvious" questions
  Month 1: First PR is a small CSS change after 4 rounds of review
  Month 3: Engineer still hasn't touched the core systems. Team wonders if it's a fit issue.

WHAT'S ACTUALLY HAPPENING:
  New engineers have no context for WHY decisions were made
  They don't know what they don't know
  They're afraid to look stupid by asking questions
  No one has systematically documented the implicit knowledge

GOOD ONBOARDING GOAL:
  Day 30:  Engineer has shipped their first meaningful feature end-to-end
  Day 60:  Engineer can work independently on well-scoped tasks
  Day 90:  Engineer is improving the system, not just maintaining it
```

# DAY 1 CHECKLIST (Complete Before New Hire Arrives)

## Accounts & Access
```
[ ] Laptop provisioned and set up (never on day 1)
[ ] All accounts created: GitHub, Slack, email, cloud consoles, Jira/Linear
[ ] 1Password / secrets manager access
[ ] VPN or zero-trust client configured
[ ] Dev environment working (they should be able to run the app on day 1)
[ ] On-call schedule: not before 90 days

REPOSITORY ACCESS:
[ ] Read access to all relevant repos (don't make them ask for each one)
[ ] Write access to their team's repos
[ ] Can they clone, install deps, and run tests? Verify this before they arrive.
```

## First Day Schedule
```
9:00  Team lead: welcome + context (what does this team build? why does it matter?)
10:00 HR/admin essentials (30 min — not 3 hours)
10:30 Assigned buddy: walk through environment setup together
12:00 Lunch with the team
13:00 Codebase overview (architecture walkthrough — 90 minutes)
14:30 First task: very small, well-defined, buddy available
16:00 End of day check-in: what was confusing? what do they need?
```

# THE ENVIRONMENT SETUP DOCUMENT

## What It Must Include
```markdown
# Getting Your Environment Running

## Prerequisites
- macOS 14+ / Ubuntu 22.04+
- Homebrew: /bin/bash -c "$(curl -fsSL https://brew.sh/install.sh)"
- [Exact version] Node.js v20.11.0 (use nvm: `nvm install 20.11.0`)
- [Exact version] Python 3.11.8

## Clone and Install
```bash
git clone git@github.com:org/repo.git
cd repo
cp .env.example .env
# Fill in values from 1Password → "Development Secrets" vault
npm install
```

## Running the App Locally
```bash
npm run db:migrate    # always run after pulling
npm run dev           # starts everything: API, workers, frontend hot-reload
```
App at: http://localhost:3000
API at: http://localhost:3001/api

## Running Tests
```bash
npm test                    # full suite
npm test -- --grep "auth"   # specific tests
npm run test:watch          # watch mode
```

## Common Setup Problems
**"Cannot connect to database"**
→ Docker not running. Run: docker compose up -d postgres redis

**"Error: ENOENT .env file"**
→ cp .env.example .env and fill in secrets from 1Password

**"Port 3000 already in use"**
→ lsof -i :3000 → kill <PID>
```

REQUIREMENT: A BRAND NEW ENGINEER SHOULD BE ABLE TO FOLLOW THIS DOCUMENT
WITH ZERO HELP AND HAVE EVERYTHING RUNNING.
Test it quarterly by onboarding yourself in a fresh environment.
```

# THE CODEBASE ORIENTATION (90 MINUTES)

## What to Cover
```
FORMAT: Talk + live code walkthrough (not slides)

SECTION 1 — The big picture (20 min):
  - What problem does this product solve?
  - Who are the users? What do they care about?
  - What is this team responsible for?
  - Show the architecture diagram (if it doesn't exist: draw it now)

SECTION 2 — Repository structure (20 min):
  - Walk the directory tree out loud
  - "This folder is X. This is important because Y."
  - Which directories are actively worked on? Which are legacy/stable?
  - What is the testing strategy? Where are tests?

SECTION 3 — A request end-to-end (30 min):
  - Pick ONE user action (e.g., "user logs in") and trace it through the code
  - Start from the HTTP request → router → middleware → handler → DB → response
  - Show them how to use the debugger / log output to follow execution
  - Don't show everything — show the pattern. They'll apply it everywhere.

SECTION 4 — How we ship (20 min):
  - Branch strategy (trunk-based? GitFlow?)
  - How to open a PR and what the review process looks like
  - CI/CD pipeline: what runs? how long does it take?
  - How to deploy: who can deploy? what are the steps?
  - How do we handle incidents on this team?
```

# THE FIRST 90 DAYS PLAN

## Week 1–2: Orient and Ship Something Small
```
GOAL: Remove the mystery of "how do I contribute here?"

TASKS:
  [ ] Complete environment setup
  [ ] Read the top 3 most important RFCs / architecture decisions
  [ ] Fix a small bug or improve a small thing (assigned, not self-discovered)
  [ ] Open a PR and go through the full review + merge + deploy process
  [ ] Meet every member of the team (15 min 1:1 each)
  [ ] Shadow on-call for 1 week (observe, don't carry pages)

"FIRST ISSUE" CRITERIA:
  ✓ Well-defined scope — no ambiguity about what done looks like
  ✓ Touches real production code (not just scripts or docs)
  ✓ Has a reviewer who will give timely, kind feedback
  ✓ Not so small it's meaningless, not so large it's overwhelming
  ✓ They should be able to ship it within their first week
```

## Week 3–4: First Real Feature
```
GOAL: Build confidence through ownership

TASKS:
  [ ] Implement a small but real feature (estimated 3–5 days)
  [ ] Write tests for it themselves
  [ ] Write the PR description explaining what they did and why
  [ ] Handle the deploy themselves (with buddy available)

SIGNALS THEY'RE ON TRACK:
  ✓ Asking questions before getting stuck (not after 2 days)
  ✓ PR descriptions are getting clearer
  ✓ They're starting to predict how reviewers will respond
  ✓ They can describe the architecture to someone else
```

## Month 2–3: Independent Contribution
```
GOAL: Self-directed within a well-scoped area

TASKS:
  [ ] Lead a full feature from design to deployment
  [ ] Write an RFC or design doc for something they're building
  [ ] Do their first code review on someone else's PR
  [ ] Present a short demo at team meeting

SIGNALS THEY'RE ON TRACK:
  ✓ PRs approved with few or no change requests
  ✓ They're asking "why do we do it this way?" questions
  ✓ They've started improving things, not just implementing specs
  ✓ Other engineers are coming to them for questions about their area
```

# THE BUDDY SYSTEM

## Buddy Responsibilities
```
WHAT A BUDDY IS:
  A peer engineer (not the manager) assigned for the first 90 days.
  Their job: be the first person the new hire asks before asking the wider team.

BUDDY COMMITMENTS:
  [ ] 30-minute daily check-in for week 1
  [ ] 30-minute weekly check-in for months 2–3
  [ ] Respond to messages within 2 hours during business hours
  [ ] Introduce the new hire to people they should know
  [ ] Tell them about unwritten norms ("we don't deploy on Fridays")
  [ ] Proactively share context: "you'll want to know about this"

WHAT A BUDDY IS NOT:
  ✗ A source of all answers — they should also say "I don't know, let's find out"
  ✗ An obstacle to asking others — encourage wide network building
  ✗ A babysitter — escalate if new hire seems lost after week 2
```

# THE IMPLICIT KNOWLEDGE PROBLEM

## Document the Stuff That Isn't Documented
```
Every codebase has knowledge that lives only in senior engineers' heads.
The cost of this is: new engineers can't be independent; seniors answer the same
questions every few months; the knowledge leaves with the engineer.

COMMON UNDOCUMENTED KNOWLEDGE:
  - "We tried X in 2022 and it caused Y, that's why we do Z"
  - "This module is a mess but we can't refactor it because..."
  - "If you see error FOO, it always means BAR"
  - "Never touch the payment module without pinging @senior first"
  - "The staging environment is permanently broken for this use case"
  - "We use Approach A not Approach B for historical reasons explained in RFC-007"

HOW TO CAPTURE IT:
  Weekly "things I learned" section in team Slack
  Architecture Decision Records (ADRs) for WHY decisions
  Runbooks for HOW to operate the system
  "Gotchas" section in each major module's README
  Ask the onboarding engineer to document everything confusing they encountered
```

# ONBOARDING METRICS
```
MEASURE THESE:
  Time to first PR merged          (target: < 1 week)
  Time to first independent feature shipped  (target: < 30 days)
  30-day / 60-day / 90-day satisfaction survey (anonymous)
  Retention at 6 months and 12 months
  How often new engineer asks "where is this documented?" (target: decreasing)

RED FLAGS AT 30 DAYS:
  ✗ No PR merged yet
  ✗ Engineer can't explain the system architecture in their own words
  ✗ Engineer says "I don't want to bother anyone with my questions"
  ✗ Manager is surprised by anything in this list (more 1:1 time needed)

CONTINUOUS IMPROVEMENT:
  End-of-onboarding retro: 30 minutes with new engineer after 90 days
  Ask: "What was hardest? What was missing? What would have helped most?"
  Update onboarding docs immediately based on their feedback
  Onboarding docs should be a living document, not a yearly project
```
