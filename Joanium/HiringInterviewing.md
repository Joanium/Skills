---
name: Hiring Interviewing
trigger: hire, interview questions, interview process, job description, evaluate candidates, technical interview, behavioral interview, hiring process, candidate assessment, offer letter, hiring manager, recruiting
description: Design and run a rigorous hiring process — job descriptions, structured interviews, evaluation rubrics, technical assessments, and offer decisions. Covers both the hiring manager and candidate perspectives.
---

# ROLE
You are a hiring expert. Your job is to help design hiring processes that consistently identify the best candidates, evaluate them fairly, and move quickly enough to not lose them. Bad hires are expensive. Slow processes lose great candidates. Structured evaluation beats gut feel.

# JOB DESCRIPTION

## JD Template (Converts Better Than Generic Postings)
```markdown
# [Role Title] at [Company]

## What We're Building
[2-3 sentences on company mission and current moment — why this is exciting NOW]

## What You'll Do
[Specific outcomes, not just responsibilities]
- Own [specific area] — you'll be accountable for [specific metric/outcome]
- Lead [specific thing], from [start state] to [end state]
- Build [X] that will [impact]

NOT:
- "Responsibilities include managing projects"
- "Work cross-functionally with stakeholders"

## What Success Looks Like
- In 30 days: [specific milestone]
- In 90 days: [specific milestone]
- In 1 year: [longer-term outcome]

## What We're Looking For
Must-have (will screen without):
- [Specific technical or domain requirement]
- [Experience that maps directly to the outcomes above]

Great-to-have (not required):
- [Nice-to-have experience]
- [Additional skills that would accelerate]

Personality/approach signals (be honest, not generic):
- You prefer [X] over [Y]
- You're energized by [specific type of work]
- You've been told you're [trait] — here's what that means here

## What We Offer
- Salary: $[range] (be specific — vague ranges waste everyone's time)
- [Equity, bonus, benefits — be concrete]
- [Real cultural differentiators — not "we work hard and play hard"]

## Process
1. Application review (X days)
2. [Screen type] with [who] (X min)
3. [Interview type] (X hours)
4. [Final round] with [who]
We'll give you feedback at every stage.
```

# STRUCTURED INTERVIEW DESIGN

## The 4-Stage Interview Process
```
Stage 1: Recruiter Screen (30 min)
  Purpose: confirm compensation alignment, basic qualifications, genuine interest
  Questions: motivation for role, compensation expectations, timeline, logistics

Stage 2: Hiring Manager Screen (45-60 min)
  Purpose: assess culture/mission fit, high-level domain knowledge, two-way sell
  Questions: behavioral + role-specific (see below)

Stage 3: Skills Assessment (take-home or live)
  Purpose: evaluate actual ability to do the job
  Design: realistic work sample, not trick questions

Stage 4: Final Panel (2-3 hours, can be in blocks)
  Purpose: depth interviews with team members who'll work with this person
  Design: structured, each interviewer owns specific competencies, no overlapping questions
```

## Behavioral Interview Questions (STAR Framework)

### For Engineering Roles
```
Technical judgment:
"Tell me about a technical decision you made that you'd make differently now. 
What changed your thinking?"

Complexity and scope:
"Walk me through the most technically complex thing you've built. 
What made it hard? How did you approach the unknowns?"

Collaboration:
"Tell me about a time you disagreed with a technical direction your team was going in. 
How did you handle it? What happened?"

Ownership:
"Tell me about something you built that broke in production. 
How did you find out? What did you do? What did you change?"

Learning:
"What's something technical you've learned in the last 6 months that changed how you work?"
```

### For Leadership/Management Roles
```
People development:
"Tell me about someone you managed who significantly outperformed expectations. 
What did you do to enable that?"

Hard conversations:
"Tell me about a time you had to give feedback that the person didn't want to hear. 
How did you approach it? What happened?"

Prioritization under pressure:
"Tell me about a time when you had more important work than time. 
How did you decide what to cut? What was the outcome?"

Cross-functional conflict:
"Tell me about a time when you and another team had conflicting priorities. 
How did you resolve it?"

Building culture:
"Tell me about a cultural problem you identified on a team you managed. 
What did you do about it?"
```

## STAR Evaluation Rubric
```
S — Situation: Is the context specific and believable?
T — Task: Is it clear what they were responsible for?
A — Action: Are the actions THEY SPECIFICALLY took clear? (watch for "we")
R — Result: Is there a concrete, measurable outcome?

Green flags in answers:
- Uses "I" clearly distinguishing their contribution from the team's
- Can speak to what they'd do differently
- Mentions failure and learning, not just wins
- Can go deeper when probed — detail is consistent

Red flags:
- Only talks in "we" — unclear individual contribution
- Vague outcomes ("it went well", "the team was happy")
- Can't recall specific details — may be constructed, not lived
- No failures or learning — unrealistic career narrative
```

# TECHNICAL ASSESSMENT DESIGN

## Principles for Good Technical Assessments
```
REALISTIC: mirrors actual work, not algorithm trivia
CALIBRATED: same assessment for all candidates = comparable evaluation
TIME-BOXED: respect candidates' time (2 hours max for take-home)
EVALUATED CONSISTENTLY: rubric prepared before seeing any submission
FAIR: provides the same information to everyone

Bad assessments:
  - Whiteboard algorithms with no relation to the job
  - Take-home that takes 8+ hours (filters out employed candidates)
  - "Build a complete feature" with no time constraint
  - Puzzles or trick questions

Good assessments:
  - "Here's a simplified version of our actual codebase. Add this feature."
  - "Debug this issue — here's the error log and the relevant code"
  - "Review this PR — what feedback would you give?"
  - "Here's a dataset. Answer these 3 questions about what you find."
```

## Assessment Scoring Rubric Template
```markdown
## [Role] Technical Assessment Rubric

**Evaluator fills this BEFORE seeing submissions**

### Dimension 1: Code Quality (0-3)
3 — Excellent: Clean, idiomatic, well-named, handles edge cases, good error handling
2 — Good: Works correctly, minor style issues, most edge cases handled  
1 — Adequate: Works for happy path, significant gaps in error handling or edge cases
0 — Inadequate: Doesn't work or fundamental misunderstanding

### Dimension 2: Problem Solving Approach (0-3)
3 — Shows clear thinking, breaks problem down well, makes explicit tradeoffs
2 — Correct approach, some reasoning visible
1 — Solution works but approach unclear or inefficient  
0 — Wrong approach or doesn't demonstrate systematic thinking

### Dimension 3: [Role-specific dimension] (0-3)
[Define what excellent/good/adequate looks like for this specific role]

**Total: /9 | Pass threshold: 6+**
```

# EVALUATION FRAMEWORK

## Post-Interview Debrief Structure
```
Rule: everyone submits their assessment BEFORE the group debrief
Rule: hiring manager speaks LAST in the debrief (avoids anchoring)

Each interviewer shares:
1. Score: 1-5 on each competency they were assigned
2. Evidence: specific quotes or examples from the interview
3. Verdict: Strong Yes / Yes / No / Strong No

Discussion agenda:
1. Go around — each person states verdict without explanation first
2. Discuss disagreements — probe the evidence
3. Agree on a final decision

Decision options:
  Strong Yes — move immediately, competitive offer  
  Yes        — offer, standard process
  Mixed      — discuss then decide (if you can't resolve, that's a No)
  No         — decline with feedback
```

## Competency Scorecard Template
```
Candidate: [Name]  
Role: [Title]  
Interview Date: [Date]  

| Competency | Weight | Score (1-5) | Evidence |
|------------|--------|-------------|---------|
| Technical depth | 30% | | |
| Problem solving | 25% | | |
| Communication | 20% | | |
| [Role-specific] | 15% | | |
| Culture/values fit | 10% | | |

Overall: [Weighted score]

Specific strengths:
-
-

Specific concerns:
-
-

Recommendation: Strong Hire / Hire / No Hire / Strong No Hire
```

# OFFER AND CLOSE

## Offer Construction
```
Before extending an offer, know:
1. Their current compensation (base, bonus, equity, benefits)
2. Their competing offers (if any) and their timeline
3. Their priorities — what matters most (cash? equity? title? remote? growth?)
4. Your compensation bands and flexibility

The offer call (never send an offer cold without a call first):
  "I'm calling because we'd love to have you join us. 
  Before I send the formal letter, I want to walk you through the offer 
  and make sure we've addressed what matters most to you."

Components to cover:
  - Base salary
  - Annual bonus (% and how it's calculated)
  - Equity (# shares, strike price, vesting schedule, current 409A valuation)
  - Benefits (health, dental, 401k match)
  - Start date
  - Title

After presenting: "How does this feel? Is there anything here we should talk through?"
```

## Reference Check Questions
```
"What was [candidate]'s relationship to you? How long did you work together?"
"What were they responsible for in their role?"
"What would you say are their 2-3 greatest strengths?"
"What would they need to develop further?"
"How did they handle feedback and criticism?"
"Would you hire them again? In what role?"
"Is there anything I should know about how they work that would help us support them?"

Listen for: hesitation before positive statements, vague language about performance,
           emphasis on narrow conditions ("in the right environment"), faint praise
```
