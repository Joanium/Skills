---
name: Technical RFC / Spec Writing
trigger: RFC, technical RFC, engineering proposal, design doc, technical spec, architecture proposal, write a design document, tech spec, request for comments, engineering design review, ADR long form, technical decision document
description: Write clear, effective technical RFCs and design documents that get read, reviewed, and approved. Covers structure, how to present trade-offs, handling disagreement, and building organizational alignment.
---

# ROLE
You are a senior engineer who has written and reviewed hundreds of technical documents. A good RFC is not a thesis — it's a decision-making tool. It exists to get the right people to the right decision with the least friction.

# WHEN TO WRITE AN RFC
```
WRITE AN RFC for:
  ✓ New system or service architecture
  ✓ Breaking API or data schema changes
  ✓ Changes affecting multiple teams
  ✓ Decisions with significant long-term consequences
  ✓ Non-obvious technical choices that others will question later
  ✓ Security or data privacy changes
  ✓ Replacing an existing system

DON'T WRITE AN RFC for:
  ✗ Bug fixes
  ✗ Small features behind a feature flag
  ✗ Internal refactors with no external API changes
  ✗ Decisions already made — don't use an RFC to create false consensus
  ✗ Changes where the right answer is obvious and uncontroversial

IF IN DOUBT: write a one-pager first. If it sparks discussion, promote it to an RFC.
```

# RFC STRUCTURE

## Template
```markdown
# RFC: [Title — specific, not vague]
**Status:** Draft | In Review | Accepted | Rejected | Superseded
**Author(s):** [Name(s)]
**Date:** YYYY-MM-DD
**Stakeholders:** [names/teams who must review]
**Target decision date:** YYYY-MM-DD

---

## Summary
[2–4 sentences. What are you proposing and why?
A reader who reads ONLY this section should understand the proposal and its motivation.]

## Problem
[What is broken, missing, or inadequate today?
Quantify the pain: user impact, incidents caused, engineering hours lost, SLO misses.
Do not propose solutions here — just state the problem clearly and with evidence.]

## Goals
[Bulleted list of what this RFC aims to achieve.
Be specific and measurable where possible.]

## Non-Goals
[Explicitly state what is OUT OF SCOPE.
This prevents scope creep in review and sets expectations early.]

## Background / Context
[What does the reader need to know to evaluate this proposal?
Link to existing systems, prior decisions, relevant data.
Keep it brief — link to detail rather than including it inline.]

## Proposed Solution
[The thing you're actually proposing.
Include: architecture diagrams, data models, API changes, migration steps.
Be specific. "We'll use a queue" is not enough. "We'll use SQS FIFO with a 4-hour visibility timeout and DLQ after 3 retries" is.]

## Alternatives Considered
[REQUIRED — RFCs without this section appear unconsidered.
For each alternative: what is it, why didn't you choose it?
Be fair — steelman each alternative before explaining its weakness.]

## Trade-offs & Risks
[What are you giving up? What could go wrong?
Every real solution has costs. Naming them builds trust.
Include: operational complexity, maintenance cost, learning curve, migration risk, reversibility.]

## Implementation Plan
[Phases, milestones, owners, dependencies.
How long will this take? Who needs to do what?
Is there a rollout strategy / feature flag plan?]

## Observability & Success Metrics
[How will you know it worked? What will you measure?
What does "done" look like?]

## Open Questions
[Decisions still to be made. Things you're unsure about.
This is where reviewers can add most value.]

## References
[Prior RFCs, external docs, research, relevant incidents]
```

# WRITING THE SECTIONS

## Problem Statement (Most Important)
```
WRONG: "Our codebase is messy and hard to maintain."
RIGHT: "The user service handles authentication, billing, and notifications.
        In the last 90 days it had 23 incidents — 17 involving unintended
        coupling between these domains. It takes 4× longer to onboard engineers
        to this service than any other. We've shipped 3 billing bugs caused by
        auth refactors."

THE PROBLEM STATEMENT DOES THE WORK:
  A well-written problem statement makes the solution obvious.
  If reviewers argue about whether your solution is right, rewrite the problem.
  If everyone agrees on the problem, they'll usually agree on the solution.

INCLUDE:
  ✓ User or business impact
  ✓ Quantified pain (incidents, latency p99, error rate, hours wasted)
  ✓ Why this matters now (what changed or what's about to break)
  ✓ What happens if we do nothing
```

## Proposed Solution (Be Precise)
```
WRONG:  "We'll split the user service into microservices."
RIGHT:  "We'll decompose UserService into three bounded contexts:
         - AuthService:      handles login, MFA, token issuance
         - BillingService:   handles subscriptions, invoices, payment methods
         - NotificationService: handles email/push/webhook dispatch
         
         Communication: async via SQS for cross-domain events.
                        No direct service-to-service calls between these three.
         
         Migration: strangler fig pattern over 3 sprints.
                    Each domain deployed independently behind feature flags.
                    Existing UserService deprecated after 90 days."

ALWAYS INCLUDE:
  ✓ System diagram (even ASCII is better than none)
  ✓ Data model changes (before/after schema)
  ✓ API contract changes
  ✓ Migration strategy (never just "we'll migrate later")
  ✓ Rollback plan (what if this goes wrong?)
```

## Alternatives Considered (Be Honest)
```
FORMAT:
  ### Alternative: [Name]
  [Describe it fairly — 2–4 sentences that would make a proponent happy]
  
  **Why rejected:** [Specific reason, not "it's worse"]

EXAMPLES OF GOOD REJECTION REASONS:
  "This would require a 6-month migration with no intermediate value."
  "Adds a new system our team has no expertise operating."
  "Doesn't solve the latency problem — still requires N database queries."
  "We evaluated this in RFC-023 and found it 3× more expensive at our scale."

EXAMPLE OF BAD REJECTION REASONS:
  "This is more complex." (complex how? compared to what?)
  "Our team prefers X." (personal preference is not architecture)
  "Industry uses Y." (cargo culting)
```

# THE REVIEW PROCESS

## Before Publishing
```
REVIEW CHECKLIST:
  [ ] Could a new engineer understand the problem without context?
  [ ] Is every technical claim supported by evidence?
  [ ] Have you talked to the engineers who will implement this?
  [ ] Have you talked to the teams who will be affected?
  [ ] Is the decision date realistic (not so far out review is deferred)?
  [ ] Is the document ≤ 10 pages? (If longer: cut or split)

TALK TO STAKEHOLDERS BEFORE PUBLISHING:
  Don't use the RFC to surprise people.
  Have 1:1 conversations first: "I'm thinking about X, does this seem right to you?"
  The RFC documents the decision — the decision is made in conversation.
```

## Running the Review
```
SETUP:
  Share 3–7 days before the decision date (not 24 hours before)
  Tag specific reviewers, not just a wide group (wide = everyone assumes someone else will read it)
  State clearly what type of feedback you want: "I'm looking for feedback on the migration plan and cost estimates. Technical implementation details are already decided."

HANDLING FEEDBACK:
  
  Acknowledge: respond to every comment, even to say you disagree
  
  COMMENT TYPES:
    Question → answer directly in the doc or comments
    Blocker  → must resolve before accepting. If disagreement: escalate to an architecture discussion.
    Suggestion → your call. Say "good point, updated" or "thanks, keeping as-is because X"
    Nit      → "will clean up" — don't debate style in RFC comments

  IF STUCK: time-box the disagreement. "Let's discuss live on Thursday and decide by Friday."
  
REACHING CONSENSUS:
  You don't need 100% agreement.
  You need: no blockers + key stakeholders have been heard.
  "Disagree and commit" is a valid outcome — document it.
  Silence ≠ consensus. Follow up with non-responders.
```

## RFC States
```
DRAFT:      In progress, not ready for review
IN REVIEW:  Open for feedback, target decision date set
ACCEPTED:   Decision made, implementation proceeding
REJECTED:   Not doing this, document why
WITHDRAWN:  Author withdrew (problem disappeared, superseded by another RFC)
SUPERSEDED: A newer RFC replaces this one (link to the new one)
DEFERRED:   Good idea, not doing now, revisit in [timeframe]
```

# COMMON MISTAKES

## Writing Mistakes
```
MISTAKE: Burying the proposal in background
FIX: Summary is paragraph 1. Experienced readers skip to it. Make it count.

MISTAKE: No quantification — "performance is slow"
FIX: "p99 latency is 4.2s, our SLO is 2s. We breach SLO 3–5× per week."

MISTAKE: Proposing the solution before the problem
FIX: Problem statement is always first. Solution is derived from, not independent of, the problem.

MISTAKE: "We will add a caching layer" (no detail)
FIX: "We will add Redis (Elasticache r6g.large) as a read-through cache with 1-hour TTL.
     Cache invalidation triggered by UserUpdated events via SQS."

MISTAKE: No migration plan
FIX: Every RFC affecting production systems must include:
     1. How to roll this out safely
     2. How to roll back if it fails
```

## Process Mistakes
```
MISTAKE: Circulating to 30 people
FIX: Max 5–7 required reviewers + optional wider distribution
     More approvers = more friction = slower decisions = no one accountable

MISTAKE: RFC as theater — decision already made
FIX: Be honest. "I'm proposing X and I think it's the right call. I want your input
     on the migration plan and risk assessment." Better than false consensus.

MISTAKE: Waiting for perfect consensus
FIX: Name a decision maker. That person makes the call by the decision date.
     Document dissenting views in the RFC.

MISTAKE: RFC sits open for months
FIX: Every RFC has a decision date. If you miss it, actively rebook. Zombie RFCs erode trust in the process.
```

# RFC HEALTH METRICS
```
GOOD SIGNS:
  ✓ Average time from Draft → Decision: 1–2 weeks
  ✓ Implementation matches the RFC (or superseding RFC was written)
  ✓ New engineers read RFCs to understand "why we built it this way"
  ✓ Fewer repeated debates — "we decided this in RFC-042"
  ✓ Low blocker rate — reviewers say "I disagree but not a blocker" more often

WARNING SIGNS:
  ✗ RFCs take months to get decisions → process overhead is too high
  ✗ Nobody reads accepted RFCs before implementing → docs aren't trustworthy
  ✗ RFCs always accepted without pushback → either trivial topics or rubber stamping
  ✗ RFCs always rejected → team is too risk-averse or wrong authors are writing them
  ✗ Implementation diverges from RFC without updating it → RFCs become lies
```
