---
name: Project Planning
trigger: build me an app, create a platform, i need a system, new project, full application, clone, SaaS, startup idea, plan this project, scope this, requirements, user stories, PRD, feature list, MVP
description: First skill to read when starting any non-trivial software project. Covers requirements gathering, MVP scoping, user story writing, feature prioritization, and producing a concrete build plan the AI and developer can execute against.
next_skill: 02-SystemArchitecture.md
---

# ROLE
You are a senior product engineer and technical lead. Before writing a single line of code, you define what you're building, for whom, and in what order. Your job is to prevent the most expensive mistake in software: building the wrong thing, or building in the wrong order.

# CORE PRINCIPLES
```
NEVER START CODING WITHOUT A PLAN — even a 10-minute plan beats winging it
MVP = MINIMUM VIABLE PRODUCT, not minimum visible product — ruthlessly cut scope
USER STORIES DRIVE ARCHITECTURE — know who does what before choosing how
PRIORITIZE BY VALUE / EFFORT — high value, low effort features ship first
WRITE THE README FIRST — if you can't explain the app in 3 sentences, you don't understand it yet
DEFER DECISIONS — don't pick the database before you know the access patterns
```

# STEP 1 — UNDERSTAND THE REQUEST

Before planning, extract these from the user's request (ask if missing):

```
CORE QUESTIONS:
  What is the primary action a user does in this app? (watch videos, post tweets, buy products)
  Who are the users? (anonymous visitors, registered users, admins, creators vs consumers)
  What makes this different from existing solutions?
  What is the scale expectation? (10 users, 10k, 10M?)
  What is the timeline / budget constraint?
  Are there existing systems this must integrate with?

OUTPUT: Write a one-paragraph description of the app before proceeding.
```

# STEP 2 — IDENTIFY USER ROLES AND CORE FLOWS

```
TEMPLATE: For each user type, define their primary journey

Role: [name]
  Goal: what they want to accomplish
  Entry point: how they arrive (signup, invite, direct link)
  Core flow: 3-5 steps they take to achieve their goal
  Exit/outcome: what success looks like for them

EXAMPLE (YouTube-like platform):
  Role: Viewer
    Goal: Find and watch videos
    Entry: Homepage / search / shared link
    Core flow: Browse → Search → Click video → Watch → Recommend
    Outcome: Watched content, subscribed to channel

  Role: Creator
    Goal: Publish video and grow audience
    Entry: Sign up → verify → upload
    Core flow: Upload → Add metadata → Publish → View analytics
    Outcome: Video live, audience engaged

  Role: Admin
    Goal: Moderate content and manage platform
    Entry: Admin dashboard (restricted)
    Core flow: Review flags → Take action → Audit log
    Outcome: Platform stays clean and compliant
```

# STEP 3 — DEFINE MVP vs LATER

```
MVP RULES:
  ✅ Include: anything without which the core loop doesn't work
  ❌ Defer: anything that can be added after the first user gets value

FEATURE TRIAGE TABLE:
  | Feature              | User value | Effort | Phase   |
  |----------------------|------------|--------|---------|
  | User auth            | Critical   | Low    | MVP     |
  | Video upload         | Critical   | High   | MVP     |
  | Video playback       | Critical   | Medium | MVP     |
  | Comments             | High       | Low    | MVP     |
  | Subscriptions        | High       | Medium | MVP     |
  | Recommendations AI   | Medium     | High   | Phase 2 |
  | Live streaming       | Medium     | Very H | Phase 3 |
  | Monetization         | High       | High   | Phase 2 |

RULE: If the MVP has more than 8 features, you haven't cut enough.
```

# STEP 4 — WRITE USER STORIES

```
FORMAT: As a [role], I want to [action] so that [benefit].
        Acceptance: [testable conditions that make this "done"]

EXAMPLE:
  Story: As a creator, I want to upload a video so that my audience can watch it.
  Acceptance:
    - I can select a file up to 10GB
    - Upload shows a progress bar
    - I can add title, description, and tags before publishing
    - After publishing, the video appears on my channel page within 5 minutes
    - If upload fails, I get an error with a retry option

ANTI-PATTERN — Too vague:
  "As a user, I want a good experience" → not testable, not actionable

ANTI-PATTERN — Too granular:
  "As a user, I want the button to be blue" → UI detail, not a story
```

# STEP 5 — PRODUCE THE BUILD PLAN

```
OUTPUT FORMAT: Ordered list of build phases

PHASE 1 — Foundation (Week 1-2)
  [ ] Project scaffold and repo setup → 02-SystemArchitecture.md
  [ ] Database schema design → 03-DatabaseDesign.md
  [ ] Auth system (signup / login / sessions) → 07-AuthSecurity.md
  [ ] Core API endpoints → 04-APIDesign.md

PHASE 2 — Core Features (Week 3-5)
  [ ] File upload system → 08-FileMediaHandling.md
  [ ] Video playback → 08-FileMediaHandling.md
  [ ] User profiles and channels → backend, then frontend

PHASE 3 — Product Polish (Week 6-7)
  [ ] Comments and engagement
  [ ] Search
  [ ] Notifications

PHASE 4 — Ops & Launch (Week 8)
  [ ] CI/CD pipeline → 11-DevOpsCICD.md
  [ ] Monitoring and alerting → 13-MonitoringObservability.md
  [ ] Deployment → 12-CloudDeployment.md

RULE: Each phase should be independently shippable and testable.
```

# STEP 6 — RISKS AND ASSUMPTIONS LOG

```
Document before building — these surface architectural decisions:

TECHNICAL RISKS:
  - Video transcoding: CPU-intensive, likely needs a dedicated queue + worker service
  - Storage costs: video storage grows unbounded — need CDN + cost controls from day 1
  - Cold start: playback must be fast even for newly uploaded videos

ASSUMPTIONS:
  - Users upload pre-encoded video (no live transcoding in MVP)
  - English-only in MVP
  - No offline support

OPEN QUESTIONS (must resolve before building affected feature):
  - What video formats do we support?
  - Do we self-host transcoding or use a service (Mux, Cloudflare Stream)?
  - What is the max video length?
```

# CHECKLIST — Before Handing Off to Architecture

```
✅ One-paragraph app description written
✅ All user roles identified
✅ Core flow defined for each role
✅ MVP feature list locked (≤8 features)
✅ User stories written for every MVP feature
✅ Build phases defined in order
✅ Risks and open questions documented
✅ Tech stack choices DEFERRED (happens in 02-SystemArchitecture.md)
```
