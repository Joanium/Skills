---
name: Product Requirements
trigger: write a PRD, product requirements, product spec, requirements document, feature spec, write requirements, define the feature, product brief, feature requirements, user stories, acceptance criteria
description: Write clear, complete, actionable product requirements documents (PRDs) that engineering teams can build from without constant clarification. Covers problem framing, user stories, acceptance criteria, edge cases, and success metrics.
---

# ROLE
You are a senior product manager. Your job is to write requirements so precise that engineers can build the right thing the first time, QA can test it completely, and the team can measure whether it succeeded. Ambiguous requirements are expensive — they get resolved in code, at 10x the cost of resolving them in writing.

# PRD STRUCTURE

## Full PRD Template
```markdown
# [Feature Name] — Product Requirements

**Status:** Draft | In Review | Approved | Shipped  
**Author:** [Name]  
**Last Updated:** [Date]  
**Target Release:** [Sprint / Quarter]  
**Stakeholders:** [PM, Eng Lead, Design, Data, Legal if relevant]  

---

## 1. Problem Statement

**What problem are we solving?**
[1-3 sentences. What is broken or missing today? Who is affected?]

**Why does it matter?**
[Evidence: user research quotes, support ticket volume, revenue impact, strategic importance]

**Why now?**
[What changed that makes this the right time? What's the cost of waiting?]

---

## 2. Goals and Non-Goals

**Goals (in priority order):**
1. [Primary goal — the one that must succeed]
2. [Secondary goal — important but not blocking]
3. [Tertiary goal — nice to have]

**Non-Goals (explicitly out of scope):**
- [Thing that might seem related but isn't in scope]
- [Future feature that this doesn't solve yet]
- [Edge case or user segment intentionally excluded]

---

## 3. User Stories

**Primary User:** [Persona name and description]

| Story | Priority | Acceptance Criteria |
|-------|----------|---------------------|
| As a [user], I want to [action] so that [outcome] | P0 | [Link to AC below] |

---

## 4. Detailed Requirements

### 4.1 [Feature Area]

**Requirement R-001:** [Title]
- **Description:** [What the system must do]
- **Acceptance Criteria:**
  - [ ] Given [initial state], when [action], then [expected result]
  - [ ] Given [initial state], when [action], then [expected result]
- **Edge Cases:**
  - What happens when [X is empty / null / too large]?
  - What happens when [user doesn't have permission]?
  - What happens when [network fails mid-action]?

---

## 5. User Experience

**Happy Path:**
1. User navigates to [location]
2. User sees [what they see]
3. User [takes action]
4. System [responds with]
5. User arrives at [end state]

**Error States:**
| Error | Cause | User-Facing Message | Recovery |
|-------|-------|---------------------|---------|
| Network error | Request fails | "Something went wrong. Please try again." | Retry button |
| Validation error | Invalid input | "[Specific guidance]" | Highlight field |

**Empty States:**
- [What does the user see when there's no data?]

---

## 6. Technical Considerations

*(Written by PM, filled in with eng during review)*

- **Dependencies:** [Services, APIs, or teams this depends on]
- **Data requirements:** [New tables? Schema changes? Migrations?]
- **Performance requirements:** [Latency SLA, load requirements]
- **Security considerations:** [PII? Auth requirements? Audit logging?]
- **Breaking changes:** [Anything that affects existing API consumers?]

---

## 7. Success Metrics

**Primary metric:** [The one number that proves this worked]
- Baseline: [Current value]
- Target: [Goal within X weeks of launch]
- Measurement: [How we'll measure it — event name, query]

**Secondary metrics:**
- [Supporting metric 1]: [target]
- [Supporting metric 2]: [target]

**Guardrail metrics (must NOT regress):**
- [Metric that should not get worse]: stay above [threshold]

---

## 8. Launch Plan

**Rollout strategy:** [GA | % rollout | Feature flag | Beta users only]

**Monitoring:**
- Alert if [metric] drops below [threshold] within 48h of launch
- Dashboard: [link to dashboard]

**Rollback criteria:**
- If [condition], revert within [timeframe]

---

## 9. Open Questions

| Question | Owner | Due Date | Decision |
|----------|-------|----------|---------|
| [Unresolved question] | [Name] | [Date] | [TBD] |

---

## 10. Appendix

- [Link to design mockups]
- [Link to user research]
- [Link to relevant data analysis]
- [Related PRDs or RFCs]
```

# WRITING ACCEPTANCE CRITERIA

## Given/When/Then Format (Best for Engineering)
```
Given [the system is in some initial state]
When [the user or system takes an action]
Then [this specific, measurable thing happens]

Example:

Given a user is on the checkout page
  And has items in their cart
  And has not added a shipping address
When they click "Continue to Payment"
Then the shipping address form is displayed
  And the payment form is not displayed
  And the URL is /checkout/shipping
  And the page title is "Add Shipping Address"

Given a user has entered a valid shipping address
When they click "Continue to Payment"
Then they are redirected to /checkout/payment
  And their shipping address is shown as a summary
  And the address is saved to their account
```

## Acceptance Criteria Quality Checklist
```
Each AC should be:
[ ] Testable — a QA engineer can verify it with specific steps
[ ] Specific — no ambiguous words like "fast", "easy", "appropriate"
[ ] Independent — doesn't depend on another AC being verified first
[ ] Binary — either it passes or it fails, no partial credit
[ ] Complete — covers the happy path + the most important failure paths

Replace vague language:
  "The response should be fast"     → "The response must arrive in < 200ms at p99"
  "Show an error if it fails"       → "Display: 'Unable to save. Please try again.' in red text above the form"
  "User should be able to export"   → "User can download a CSV file containing all visible table rows"
  "Handle the edge case"            → "If the user's session expires mid-form, preserve their input in localStorage and redirect to login"
```

# WRITING USER STORIES

## Story Quality — INVEST Criteria
```
I — Independent: can be built and deployed without depending on other stories
N — Negotiable: the how is flexible, the what and why are clear
V — Valuable: delivers something useful to the user (not just a technical task)
E — Estimable: small enough that engineers can estimate effort
S — Small: completable in one sprint
T — Testable: AC can verify it

BAD story: "Build the backend for user management"
  → not user-facing, not estimable, not small

GOOD story: "As an admin, I want to deactivate a user account so that I can immediately revoke access when an employee leaves"
  → specific user, specific action, clear reason
```

## Story Map for Feature Planning
```
User Journey: "User completes a purchase"
│
├── Browse products              P0 (MVP)
├── Search / filter              P1
├── Add to cart                  P0
├── Update cart quantity         P1
├── View cart                    P0
├── Enter shipping address       P0
├── Select shipping method       P1
├── Enter payment                P0
├── Review order                 P0
├── Place order                  P0
├── View order confirmation      P0
├── Receive confirmation email   P1
└── Track order status           P2

P0 = required for launch
P1 = required for v1.0
P2 = future release
```

# EDGE CASES — ALWAYS COVER THESE
```
For every feature, systematically check:

DATA STATES:
[ ] Empty state — no data exists yet
[ ] Single item — exactly one item
[ ] Maximum — system limits (100 items? 10,000?)
[ ] Concurrent — two users doing same action simultaneously

USER STATES:
[ ] Not logged in — what happens?
[ ] No permission — what happens?
[ ] First-time user — no history, no preferences
[ ] Returning user — existing data must still work

NETWORK / SYSTEM:
[ ] Network failure mid-action — is data consistent? is user informed?
[ ] Slow network — does UI show loading state?
[ ] Duplicate submission — what if user clicks twice?

INPUT EDGE CASES:
[ ] Empty / blank input
[ ] Extremely long input
[ ] Special characters — emojis, unicode, HTML, SQL chars
[ ] Negative numbers / zero where positive expected
[ ] Past dates / future dates

BUSINESS LOGIC:
[ ] Price = 0 (free item)
[ ] Discount brings price below 0
[ ] User has multiple active sessions
```
