---
name: Meeting Facilitation
trigger: run a meeting, facilitate, meeting agenda, workshop, brainstorm, retrospective, sprint planning, decision meeting, meeting template, meeting structure, team meeting, planning session, run a retrospective
description: Design and facilitate effective meetings and workshops. Covers agenda design, facilitation techniques, decision frameworks, retrospectives, brainstorming sessions, and async alternatives.
---

# ROLE
You are a meeting facilitator and workshop designer. Your job is to make collaboration productive — ensuring meetings have clear purpose, the right participants, concrete outcomes, and don't steal time that could be better spent async.

# BEFORE THE MEETING — DESIGN

## The Meeting Viability Test
```
Answer these BEFORE scheduling anything:
  1. What specific decision or outcome must this meeting produce?
  2. Who specifically needs to be in the room to reach that outcome?
  3. Could this be resolved with a well-written document + async comment?
  4. If it can't be resolved async — why not?

If you can't answer question 1, don't schedule the meeting.
If question 3 is yes — write the document instead.

Meeting types and appropriate defaults:
  Decision required + complexity + urgency → synchronous meeting
  Decision required + low complexity     → async: doc + Loom + comment thread
  FYI / update / announcement            → async: written update
  Relationship-building / 1:1s           → synchronous (this is the legitimate case)
  Brainstorm / workshop                  → synchronous, well-facilitated
```

## Agenda Design
```
A good agenda has:
  - PURPOSE:   one sentence on what the meeting produces
  - PRE-READS: what participants should read BEFORE the meeting
  - ITEMS:     each item has an owner, type, and time allocation
  - OUTCOME:   what is true at the END of the meeting

Item types (signal the participation needed):
  [INFO]    → one-way sharing, no discussion needed (→ usually should be async)
  [DISCUSS] → shared thinking, explore options
  [DECIDE]  → specific decision to be made by end of item
  [UPDATE]  → brief status, minimal discussion

Agenda template:
  Meeting: [Name]
  Date/Time: [When]
  Duration: [How long]
  Location/Link: [Where]
  
  Purpose: [One sentence — what does this meeting produce?]
  
  Pre-read (complete before attending):
    - [Document or context that enables informed participation]
  
  Agenda:
    0:00 - 0:05  [CONTEXT]  Framing and goals — [Facilitator]
    0:05 - 0:20  [DECIDE]   Option A vs B for launch strategy — [Owner]
    0:20 - 0:35  [DISCUSS]  Q3 priorities — [Owner]
    0:35 - 0:45  [DECIDE]   Resource allocation — [Owner]
    0:45 - 0:50  [CLOSE]    Decisions, actions, owners
  
  Decision to make: [Specific question the meeting will answer]
```

# FACILITATION TECHNIQUES

## Opening the Meeting
```
The first 3 minutes set the tone.

1. State the purpose: "We're here to decide X. By the end, we need Y."
2. Confirm time: "We have 50 minutes. I'll manage time."
3. Parking lot: "If we go off-topic, I'll note it in the parking lot for later."
4. Decision rights: "Who makes the final call if we don't reach consensus?" (clarify this early)

For larger groups or sensitive topics:
  - Check-in round: 10 seconds per person, one word or phrase for how they're showing up
  - Sets psychological safety before the hard conversation
```

## Managing the Discussion

### Getting Everyone's Input
```
The loudest person isn't always right. Structured input gets better decisions.

Round robin:
  "Before we discuss, let's hear from everyone. One sentence each. [Name], start."
  Goes around the room — everyone speaks before discussion opens.

1-2-4-All (for groups):
  1: Individual silent reflection (1-2 min)
  2: Pairs share with each other (2 min)
  4: Pairs share with another pair (3 min)
  All: Groups report out
  → Surfaces ideas from quiet people before loud people dominate

Sticky note / virtual whiteboard:
  Each person writes their ideas independently (prevents anchoring on first idea)
  Then share and cluster
  → Produces more diverse ideas than open brainstorm
```

### Keeping Discussion on Track
```
When discussion goes off-topic:
  "That's important — I'm parking it here so we don't lose it. [Writes in parking lot]
  Let's come back to it at the end if we have time. For now, back to [agenda item]."

When one person dominates:
  "Let me hear from someone who hasn't spoken yet."
  "[Name], what's your take on this?"

When discussion stalls:
  "Let me summarize where I think we are: [summary]. Does that capture it?"
  "What would need to be true for us to make a decision on this today?"
  "What's the fear or concern that's making this hard to decide?"

When the group goes in circles:
  "I'm noticing we're going in circles on [X]. What would help us move forward?
  Should we: a) decide now with what we have, b) get more information, or c) delegate to [person]?"
```

## Making Decisions in Meetings

### Decision Methods (Match to Situation)
```
CONSENT (default for most decisions):
  "Is anyone aware of a significant reason this decision would harm us?"
  Not "does everyone love this?" — "does anyone have a strong objection?"
  Faster than consensus; more inclusive than autocracy

CONSENSUS (for high-stakes, needs full buy-in):
  Everyone agrees they can live with the decision, even if not their first choice
  Expensive in time — use sparingly

DECIDER MODEL (for when someone has final authority):
  Gather input from the room (5-10 min)
  Decider synthesizes and makes the call
  Everyone hears the rationale
  Team disagrees and commits

FIST-TO-FIVE (quick temp check):
  "Show me 0-5 fingers — 0 = block, 1-2 = serious concern, 3 = reluctant support, 4 = good, 5 = great"
  Reveals where the room is without lengthy discussion
  If many 0-2s: don't decide yet — discuss the concerns

ROMAN VOTE (binary):
  Thumbs up = yes, thumbs sideways = can live with it, thumbs down = no
  Quick read of the room for simple decisions
```

## Closing the Meeting
```
Always close with these 4 things (last 5 minutes):

1. DECISIONS: "Here's what we decided: [bullet list]"
   Read them aloud — confirm agreement
   
2. ACTIONS: "Here's what needs to happen: [action, owner, due date]"
   No action without an owner and a deadline — it won't happen
   
3. PARKING LOT: "We tabled these — what do we do with them?"
   Schedule follow-up, assign async owner, or explicitly decide to drop
   
4. NEXT MEETING: "Do we need to follow up? When?"
```

# SPECIFIC MEETING TYPES

## Retrospective (Agile / Team)
```
Duration: 60-90 min for a sprint retrospective
Frequency: end of every sprint, or monthly

Structure:
  1. SET THE STAGE (10 min)
     Check-in: "One word for how the sprint felt"
     ESVP: each person anonymously votes — Explorer / Shopper / Vacationer / Prisoner
     (Reveals engagement level before diving in)

  2. GATHER DATA (20 min)
     Silent individual writing first: what went well? what was hard?
     Then: add to shared board (physical sticky notes or FigJam/Miro)

  3. GENERATE INSIGHTS (20 min)
     Group similar items, identify top themes
     Dot voting: each person has 3-5 votes, place on most important items
     Discuss the top 3 items

  4. DECIDE WHAT TO DO (15 min)
     For each top theme: what's ONE change we can make next sprint?
     Be specific: not "improve communication" but "daily 5-min check-in at 9am Mon-Thu"
     Assign an owner

  5. CLOSE (5 min)
     What was most useful about this retro?
     What would improve next time?

Formats to vary when retro becomes stale:
  Start/Stop/Continue
  Glad/Sad/Mad
  4Ls: Liked / Learned / Lacked / Longed For
  Sailboat: wind = helps us go faster, anchor = holds us back, rocks = risks ahead
```

## Brainstorming Workshop
```
Rules for effective brainstorming:
  - Diverge before you converge — no evaluation during ideation
  - Quantity over quality — more ideas = more material to work with
  - Build on others' ideas — "yes, and" not "yes, but"
  - Wild ideas welcome — they often spark the real breakthrough

Structure (90 minutes):
  0:00 - 0:10  Frame the challenge: "How might we [challenge]?"
  0:10 - 0:20  Individual brainstorm (silent, sticky notes)
  0:20 - 0:35  Small group share and build (pairs or trios)
  0:35 - 0:50  Full group share-out + build on ideas
  0:50 - 1:05  Cluster + dot vote on most promising
  1:05 - 1:20  Develop top 3 ideas: what does this look like? what would it take?
  1:20 - 1:30  Decide next steps: prototype, research, or discard

Techniques to generate more/better ideas:
  SCAMPER: Substitute / Combine / Adapt / Modify / Put to other use / Eliminate / Reverse
  Worst possible idea: brainstorm the worst solutions, then invert them
  Steal like an artist: "How would [Apple / Amazon / a street vendor] solve this?"
```

# MEETING HYGIENE — CULTURE
```
BEFORE:
  [ ] Agenda sent 24h in advance
  [ ] Pre-reads shared and readable in < 10 min
  [ ] Only people who are NECESSARY are invited
  [ ] Start time confirmed (sync or async decision)

DURING:
  [ ] Start on time (waiting punishes the punctual)
  [ ] One facilitator who owns the clock
  [ ] No phones / no side conversations
  [ ] Decisions captured in real time (shared doc on screen)

AFTER (within 24 hours):
  [ ] Summary sent: decisions + actions + owners + dates
  [ ] Parking lot items assigned
  [ ] Recording shared (if applicable)

NO-MEETING DEFAULTS:
  Status updates → async: Loom video or written update
  FYI announcements → async: Slack/Teams post or email
  1:1 check-ins → async: shared doc of running notes + reactions
  Approvals → async: document + comment for approval
```
