---
name: Technical Debt Management
trigger: technical debt, code quality, refactoring strategy, legacy code, debt tracking, codebase health, architectural debt, cleanup sprint, pay down debt, code rot, software entropy, modernization
description: A framework for identifying, measuring, prioritizing, and systematically paying down technical debt without halting product development. Use for debt inventories, making the business case, planning cleanup work, and building sustainable engineering practices.
---

Technical debt is the accumulated cost of shortcuts, outdated decisions, and deferred improvements in a codebase. Like financial debt, it accrues interest — every feature built on a shaky foundation costs more than it should. Unlike financial debt, it's invisible to stakeholders until the interest payment arrives in the form of outages, missed deadlines, or engineer burnout.

## Types of Technical Debt

Not all debt is equal. Understand what you're dealing with before planning.

```
Deliberate (strategic) debt — chosen consciously
  "We'll use a simple polling loop for now and move to WebSockets after launch."
  → Tracked, time-bounded, acceptable if you actually pay it back

Inadvertent debt — accrued unknowingly
  "I didn't know there was a race condition in this pattern."
  → Usually discovered when it bites you; fix promptly

Bit rot — entropy over time
  Working code that becomes debt as the ecosystem moves on
  (e.g., unmaintained dependencies, deprecated APIs, outdated auth patterns)
  → Requires regular maintenance cycles, not just feature sprints

Architectural debt — structural design decisions
  Monolith that should be services; synchronous flows that should be async
  → Hardest to pay back; must be planned, not patched

Test debt — insufficient test coverage
  Makes refactoring dangerous and slows feature velocity
  → Often the first investment to make; unlocks everything else
```

## Phase 1: Inventory the Debt

You can't manage what you haven't named. Build a shared debt register.

**Code health signals:**
```bash
# Lines of code per file (complexity proxy)
find src -name "*.ts" -exec wc -l {} + | sort -rn | head -20

# Duplicate code detection
npx jscpd src --min-lines 10 --reporters console

# Cyclomatic complexity
npx complexity-report src --format plain | sort -rn | head -20

# Dependency staleness
npm outdated  # Node.js
pip list --outdated  # Python

# Test coverage gaps
npx jest --coverage --coverageReporters=text-summary
```

**Debt categorization template:**
```
Debt Item Template:
  ID:           DEBT-042
  Title:        User authentication uses deprecated JWT library
  Type:         Bit rot / Security
  Location:     src/auth/*, all 47 files that import from it
  Age:          ~18 months
  Principal:    3 days to migrate
  Interest:     +15% overhead on every auth-related feature
  Risk:         HIGH — library has 2 unpatched CVEs
  Business Case: Security audit flagged this; blocks SOC2 certification
  Owner:        @alice
  Status:       Prioritized Q2
```

**Debt register (maintain in a shared doc or project board):**
```
| ID       | Title                     | Type         | Size | Risk | Priority |
|----------|---------------------------|--------------|------|------|----------|
| DEBT-001 | Legacy auth library       | Security     | M    | High | P1       |
| DEBT-002 | No integration test suite | Test debt    | L    | High | P1       |
| DEBT-003 | 3 services share one DB   | Architecture | XL   | Med  | P2       |
| DEBT-004 | Hardcoded config in 40+ files | Bit rot  | M    | Low  | P3       |

Size: S=<1 day, M=1-3 days, L=1 week, XL=>1 week
```

## Phase 2: Measure and Track

Tracking debt is how you make it visible to leadership and prevent it from growing silently.

```python
# Debt metrics to track over time (add to your engineering dashboard)
metrics = {
  # Code quality
  "avg_file_complexity":    "cyclomatic complexity per file",
  "large_file_count":       "files > 500 lines",
  "test_coverage_pct":      "line/branch coverage %",
  "duplicate_code_pct":     "% of code that is duplicated",
  
  # Dependency health  
  "outdated_deps":          "# packages > 2 major versions behind",
  "critical_cve_count":     "# dependencies with CVSS score > 7",
  
  # Operational signals
  "mttr_minutes":           "mean time to resolve incidents",
  "deploy_frequency":       "deploys per week",
  "build_time_minutes":     "CI pipeline duration",
  "flaky_test_count":       "tests that fail non-deterministically",
  
  # Velocity proxy
  "lead_time_days":         "idea to production average"
}

# Track weekly and visualize trend — deterioration is the warning sign
# The goal isn't a perfect score; it's a stable or improving trend
```

## Phase 3: Prioritize — The Interest Rate Framework

Not all debt should be paid. Prioritize by interest rate: how much does carrying this debt cost per sprint?

```
High interest (fix first):
  ✓ Security vulnerabilities with known CVEs
  ✓ Blocking feature development (multiple teams hit this weekly)
  ✓ Causing production incidents (paying interest in downtime)
  ✓ Making onboarding painful for new engineers
  ✓ Flaky tests (slow every CI run, erode test confidence)

Medium interest (schedule in next quarter):
  ✓ Outdated patterns that slow feature development
  ✓ Missing test coverage in frequently-changed modules
  ✓ APIs that generate constant confusion and mistakes

Low interest (maybe never):
  ✗ Code that "feels ugly" but works and is rarely touched
  ✗ Rewriting things just to use newer technology
  ✗ Perfectly functional but old code in stable, rarely-changed modules

Rule: If you touched it twice in the last sprint, it's high interest.
      If you haven't touched it in 6 months, leave it alone.
```

**The 2x2 prioritization matrix:**
```
                  HIGH IMPACT
                      |
    Fix now:          |    Plan carefully:
    High interest,    |    Large scope, high interest —
    quick to fix      |    needs dedicated project
                      |
LOW EFFORT ———————————+——————————— HIGH EFFORT
                      |
    Nice to have:     |    Don't bother:
    Easy but low      |    Hard AND low return
    impact            |    
                      |
                  LOW IMPACT
```

## Phase 4: Strategies for Paying Down Debt

**The Boy Scout Rule (continuous):**
```
Every PR should leave the code a little better than it found it.
Not a rewrite — just small improvements:
  - Add a test for a bug you fixed
  - Extract a magic number into a named constant
  - Rename a confusing variable while you're in the file
  - Fix a minor code smell you spot

This is the most sustainable debt payment strategy.
"Leave it better than you found it" → compounding improvement over time.
```

**20% time allocation (structured):**
```
Reserve 10-20% of every sprint for debt work.
Protect it like product features — put it in the sprint, estimate it, demo it.
Teams that say "we'll do tech debt after the launch" never do.

Sprint structure example:
  70% — Feature work (committed to stakeholders)
  20% — Debt/quality work (committed to engineering health)
  10% — Spikes, learning, tooling (committed to team growth)
```

**Debt sprints (periodic):**
```
Dedicated cleanup sprint every 6-8 sprints.
When to use:
  - Debt has accumulated faster than continuous cleanup can handle
  - Preparing for a major new product phase
  - Post-launch breathing room

How to run one:
  1. Pre-select debt items from register; scope to fit the sprint
  2. Have each engineer pick items aligned to their expertise
  3. Daily check-in: blockers only, no status updates
  4. End of sprint: measure metrics (did coverage go up? complexity go down?)
  5. Document decisions — future engineers need to know WHY things changed
```

**The Strangler Fig Pattern (for architectural debt):**
```
Never attempt a "big bang" rewrite. They almost always fail.
Instead: strangle the old system by replacing it piece by piece.

1. Identify a seam in the legacy system (a well-defined API or data boundary)
2. Build the new implementation behind a routing layer
3. Route a small % of traffic to new implementation
4. Validate, expand routing, monitor
5. When new system handles 100%, remove old code
6. Repeat for the next seam

Legacy monolith → microservices migration example:
  Month 1: Extract user authentication service (lowest risk, well-defined)
  Month 2: Extract email notifications
  Month 3: Extract billing
  ...
  Year 1: Core order processing (most complex, highest risk — do last)
```

## Phase 5: Making the Business Case

Engineering leaders need to communicate debt in business terms.

```
DON'T say: "We need to refactor our service layer because the coupling is too tight 
            and our cyclomatic complexity is averaging 23."

DO say:    "Our customer data pipeline has caused 3 production incidents this 
            quarter, each taking 4 hours to resolve. Every new report takes 
            twice as long to build as it should. Investing 2 weeks now will 
            eliminate ~90% of incident risk here and cut feature time in half 
            for the next 12 months — saving roughly 160 engineering hours."

Translation formula:
  Incidents × MTTR hours × engineer cost/hour = current annual interest
  Project size × engineer cost/day = principal
  ROI = annual interest / principal  (> 1x in year 1 = easy sell)
```

**Debt communication to stakeholders:**
```
Monthly engineering health report (keep it short):
  → Metric trend: test coverage 61% → 68% (+7pp this quarter)
  → Debt items closed: 4
  → New debt items added: 2
  → Incidents attributable to known debt: 1 (checkout service, 2h MTTR)
  → Focus this quarter: authentication modernization (security compliance)
  → Ask: Reserve 2 sprints for payment processing refactor in Q3
```

## Anti-Patterns to Avoid

```
❌ Declaring "debt bankruptcy" — rewriting everything from scratch
   Almost always takes 3x longer than estimated and results in new debt
   
❌ Debt-shaming — "who wrote this?" culture
   Causes engineers to hide problems; kills psychological safety

❌ Treating all debt as equally urgent
   Leads to working on low-impact cleanup while high-interest debt burns

❌ Not tracking new debt as it's created
   Untracked deliberate shortcuts become forgotten landmines

❌ Using "technical debt" to mean "things I don't like"
   Conflating personal preferences with actual debt inflates the register
   and makes it impossible to prioritize
```
