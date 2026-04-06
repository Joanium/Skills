---
name: Tech Stack Selection
trigger: what tech stack, choose a framework, which database should i use, build vs buy, which language should i use, pick a tech stack, technology choice, framework comparison, what should i use for, tech decision, technology evaluation, language choice
description: Evaluate and select technology stacks, frameworks, databases, and tools using a structured decision framework. Use when starting a new project, evaluating a major technology change, or making a build vs. buy decision.
---

The worst tech decisions aren't made because engineers are incompetent — they're made because engineers are excited. A new framework is interesting. An old reliable one is boring. Boring is usually right. Choose technology that solves today's problem without creating tomorrow's complexity.

## The Meta-Principle: Boring is Beautiful

Before evaluating options, internalize this:

```
The best stack is the one your team can:
1. Build with quickly
2. Debug at 2am
3. Hire for
4. Maintain for 5 years

"Exciting" new technology fails every one of these criteria 
more often than "boring" established technology.

Choose boring technology (Dan McKinley's law):
https://mcfarlane.tech/choose-boring-technology
```

## The Decision Framework

### Step 1: Define your constraints FIRST

Write these down before looking at options:

```
Team constraints:
- Team size: [n engineers]
- Existing expertise: [languages/frameworks the team knows well]
- Hiring market: [can you hire for this in your city/remote?]
- Budget for learning curve: [weeks/months, not years]

Product constraints:
- Expected scale at launch: [users, req/s, data volume]
- Expected scale in 2 years: [realistic, not aspirational]
- Primary data access patterns: [reads? writes? search? analytics?]
- Latency requirements: [real-time? < 100ms? < 1s is fine?]
- Compliance requirements: [HIPAA? PCI? SOC2? data residency?]

Business constraints:
- Time to first deployment: [weeks? months?]
- Long-term vendor risk tolerance: [proprietary vs open source?]
- Cloud provider preference: [AWS/GCP/Azure/agnostic?]
- Cost sensitivity: [startup scraping by vs well-funded?]
```

### Step 2: Establish evaluation criteria with weights

Don't evaluate everything equally. Decide what matters most:

```
Example weights for an early-stage startup:
40% — Team productivity (ship fast)
25% — Ecosystem maturity (libraries, tools exist)
20% — Hiring market (can we grow the team?)
10% — Performance at scale (you don't have scale yet)
5%  — Cost

Example weights for a high-traffic consumer app:
25% — Performance at scale (you have the scale)
25% — Operational maturity (battle-tested in production)
20% — Ecosystem maturity
20% — Team productivity
10% — Cost
```

### Step 3: Eliminate before you evaluate

```
Eliminate any option that:
✗ Your team has no expertise in AND it takes > 6 months to learn
✗ Has no established hiring market in your area
✗ Is owned by a single company with a history of pivoting (vendor risk)
✗ Doesn't have production usage at your expected scale
✗ Has known deal-breaking limitations for your use case
  (e.g., "doesn't support transactions" for a financial system)
```

## Build vs. Buy Framework

For any significant capability, ask in order:

```
1. USE what you have → Can an existing tool/service do this?
2. BUY → Is there a SaaS/managed service that's cheaper than building?
3. OPEN SOURCE → Is there a well-maintained open source solution?
4. BUILD → Only if the above fail, or if it's your core differentiator

Build only when:
- It IS your product's differentiation
- No existing solution meets your requirements (not "preferences")
- The cost of a vendor failure would be catastrophic
- Data sensitivity prevents using third-party services

Buy when:
- It's not your core business
- The vendor's focus means they'll always be ahead of you
- The integration cost < 3 months of an engineer's salary (usually)
- The capability is genuinely hard to build correctly
  (email deliverability, payment security, search ranking, auth)
```

## Framework: Database Selection

This decision has the highest switching cost. Get it right.

```
Start with: What are your primary access patterns?

Relational data (entities with relationships, complex queries):
→ PostgreSQL (default choice — rich types, JSONB, extensions)
→ MySQL/MariaDB (if team expertise or specific cloud integration)

Document / flexible schema (nested objects, schema evolution):
→ MongoDB (mature, widely understood)
→ Firestore (if on GCP, real-time sync needed, small team)
→ But: consider PostgreSQL JSONB first — you may not need a document DB

Key-value / session / cache:
→ Redis (the obvious choice — also does pub/sub, queues, sorted sets)

Search:
→ Elasticsearch / OpenSearch (powerful, complex to operate)
→ Typesense (simpler to operate, great for product search)
→ Meilisearch (developer-friendly, good for most use cases)
→ PostgreSQL full-text search (good enough for < 10M documents)

Analytics / OLAP (aggregation over large datasets):
→ ClickHouse (fast, open source, excellent for time-series)
→ BigQuery (managed, pay per query — great for small teams)
→ Redshift (if committed to AWS ecosystem)

Graph data (social networks, recommendation engines):
→ Neo4j (mature, good tooling)
→ Only adopt if your data is FUNDAMENTALLY graph-shaped
→ PostgreSQL recursive CTEs handle surprising amounts of graph work

Time series:
→ TimescaleDB (PostgreSQL extension — easy if you already use PG)
→ InfluxDB (purpose-built, good ecosystem)
→ ClickHouse (also excels at time series)

Vector / embeddings:
→ pgvector (PostgreSQL extension — choose if already on PG)
→ Pinecone (managed, no ops overhead)
→ Weaviate / Qdrant (self-hosted, more control)
```

## Framework: Backend Language Selection

```
Python:
  Best for: ML/AI, data pipelines, internal tools, scripting
  Production web: FastAPI (async, high-performance), Django (batteries-included)
  Avoid for: High-concurrency real-time systems (use Go instead)

Node.js / TypeScript:
  Best for: API servers, BFF layers, real-time apps, full-stack JS shops
  Framework: Express (simple), Fastify (performance), NestJS (structured)
  Avoid for: CPU-intensive work, ML

Go:
  Best for: High-performance services, CLIs, systems programming
  Excellent for: Microservices, API gateways, anything with >10K req/s
  Avoid for: Teams with no Go experience (learning curve is real)

Java / Kotlin:
  Best for: Enterprise, financial services, teams with existing JVM expertise
  Framework: Spring Boot (standard), Micronaut (cloud-native)
  Avoid for: Small teams, startups (operational overhead)

Rust:
  Best for: Performance-critical systems, safety-critical software
  Avoid for: Most web applications (productivity cost too high)
```

## Scoring Scorecard Template

```markdown
## Technology Evaluation: [Decision]

**Decision date:** [Date]
**Deciders:** [Names]
**Context:** [1-2 sentences on why this decision matters now]

### Criteria and Weights
| Criterion             | Weight |
|-----------------------|--------|
| Team productivity     | 40%    |
| Ecosystem maturity    | 25%    |
| Hiring market         | 20%    |
| Performance at scale  | 10%    |
| Cost                  | 5%     |

### Options Evaluated

| Criterion (weight)      | Option A | Option B | Option C |
|-------------------------|----------|----------|----------|
| Team productivity (40%) | 9/10     | 6/10     | 7/10     |
| Ecosystem maturity (25%)| 9/10     | 8/10     | 6/10     |
| Hiring market (20%)     | 9/10     | 7/10     | 5/10     |
| Performance (10%)       | 7/10     | 9/10     | 8/10     |
| Cost (5%)               | 8/10     | 7/10     | 9/10     |
| **Weighted Score**      | **8.6**  | **7.1**  | **6.6**  |

### Decision
**We will use [Option A].**

Reason: [1 paragraph explaining the most important factors, not just restating scores]

### Known risks
- [Risk 1 and how we'll mitigate it]
- [Risk 2 and how we'll mitigate it]

### Review trigger
We will revisit this decision if: [e.g., "team grows beyond 20 engineers" or 
"we regularly process > 1M events/day"]
```

## Checklist: Before Committing to a Technology

```
☐ Have we written down our constraints? (team, scale, compliance)
☐ Have we eliminated options that don't meet hard requirements?
☐ Is this technology in production at similar scale? (references, case studies)
☐ Can we hire for it in our market?
☐ Does the team have hands-on time with it (not just docs)?
☐ Have we done a 1-week spike/prototype to validate assumptions?
☐ Do we have a way out? (migration path if this proves wrong)
☐ Have we documented this in an ADR?
☐ Have we set a review trigger for revisiting the decision?
```
