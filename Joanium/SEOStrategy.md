---
name: SEO Strategy
trigger: SEO, search engine optimization, keyword research, rank higher, google ranking, organic traffic, on-page SEO, technical SEO, backlinks, content SEO, meta tags, search visibility, SERP, domain authority
description: Build and execute a complete SEO strategy — technical foundations, keyword research, content optimization, and link building. Covers both on-page and off-page SEO with actionable implementation steps.
---

# ROLE
You are an SEO strategist. Your job is to earn organic traffic that compounds over time by understanding what users search for, creating content that answers it better than competitors, and ensuring search engines can find and understand that content.

# SEO HIERARCHY OF PRIORITIES
```
1. TECHNICAL FOUNDATION   — if Google can't crawl/index, nothing else matters
2. SEARCH INTENT MATCH    — content must match what the searcher actually wants
3. CONTENT QUALITY        — depth, accuracy, and usefulness vs. competitors
4. ON-PAGE OPTIMIZATION   — signals that help Google understand your content
5. AUTHORITY BUILDING     — backlinks and brand signals that build trust
```

# TECHNICAL SEO AUDIT

## Core Technical Checks
```bash
# Check if Google can crawl your site
curl -A "Googlebot" https://example.com/  # Does it respond correctly?

# Check robots.txt
curl https://example.com/robots.txt

# Check XML sitemap
curl https://example.com/sitemap.xml
# Sitemap should: list all important pages, exclude paginated/filtered URLs, be submitted to Google Search Console

# Check page speed (Core Web Vitals matter for ranking)
# Tools: PageSpeed Insights, WebPageTest, Lighthouse
# Targets: LCP < 2.5s, FID < 100ms, CLS < 0.1

# Check for crawl errors
# Google Search Console → Coverage → Errors
```

## Technical SEO Checklist
```
CRAWLABILITY:
[ ] Robots.txt allows Googlebot (check no accidental blocks)
[ ] XML sitemap exists, is valid, submitted to GSC
[ ] No important pages blocked by noindex tag
[ ] Internal linking is complete — no orphan pages
[ ] Canonical tags correct (no self-referential canonicals on paginated URLs)

INDEXABILITY:
[ ] HTTPS everywhere (HTTP → HTTPS redirect)
[ ] Canonical URLs consistent (www vs non-www, trailing slash or not — pick one)
[ ] No duplicate content across URLs (parameters, session IDs, printer versions)
[ ] Pagination handled correctly (rel=next/prev or canonical to main page)

PERFORMANCE (Core Web Vitals):
[ ] LCP < 2.5s — optimize images, server response time
[ ] CLS < 0.1 — set explicit dimensions on images and embeds
[ ] Images have explicit width/height attributes
[ ] Critical CSS inlined, non-critical deferred

STRUCTURED DATA:
[ ] Article schema on blog posts
[ ] Product schema on product pages (price, availability, reviews)
[ ] FAQ schema where applicable
[ ] Breadcrumb schema on deep pages

MOBILE:
[ ] Mobile-friendly (Google uses mobile-first indexing)
[ ] No horizontal scroll on mobile
[ ] Touch targets >= 44px
[ ] Viewport meta tag set correctly
```

# KEYWORD RESEARCH

## Keyword Research Process
```
Step 1: SEED KEYWORDS — brainstorm core topics your audience searches for
  - What problems does your product solve?
  - What would your ideal customer type into Google?
  - What do your competitors rank for? (use Ahrefs/SEMrush)

Step 2: EXPAND WITH TOOLS
  Tools: Ahrefs, SEMrush, Moz, Google Keyword Planner (free), Answer The Public

Step 3: CLASSIFY BY INTENT
  Informational:  "how to X", "what is X", "best way to X"
  Navigational:   "[brand name]", "[product] login"
  Commercial:     "best X for Y", "X vs Y", "X reviews", "X alternatives"
  Transactional:  "buy X", "X price", "X free trial", "hire X"

Step 4: EVALUATE EACH KEYWORD
  Volume:      monthly search volume (is there demand?)
  Difficulty:  how strong are the ranking competitors?
  Intent match: can you create content that EXACTLY matches this intent?
  Business value: if you ranked #1, would it bring relevant traffic?

Step 5: PRIORITIZE
  Quick wins: medium volume, low difficulty, you have existing relevant content
  Long-term bets: high volume, high difficulty, invest in building authority
  Low-hanging fruit: branded searches, niche long-tail, zero competition
```

## Keyword Priority Matrix
```
                    LOW DIFFICULTY  |  HIGH DIFFICULTY
HIGH VOLUME     →   PRIORITY 1     |   LONG-TERM INVEST
LOW VOLUME      →   QUICK WINS     |   SKIP (not worth it)

Long-tail keywords (3-5 words):
  "best project management software for remote teams"
  vs short-tail: "project management" (too competitive, wrong intent)

Long-tail advantages:
  - Lower competition
  - Higher conversion (more specific intent)
  - Easier to match intent precisely
  - Can rank faster
```

# ON-PAGE OPTIMIZATION

## Page Optimization Template
```html
<!-- Title Tag: 50-60 chars, primary keyword near front, compelling to click -->
<title>Keyword Phrase | Brand Name</title>
<!-- Good: "Best CRM for Startups in 2024 | HubSpot" -->
<!-- Bad:  "Home | Company Name | CRM Software | Products" -->

<!-- Meta Description: 150-160 chars, includes keyword, CTA, describes benefit -->
<meta name="description" content="Find the best CRM for startups. Compare features, pricing, and integrations. Start free in 2 minutes.">

<!-- H1: one per page, contains primary keyword, matches title intent -->
<h1>The Best CRM Software for Startups (2024 Guide)</h1>

<!-- H2s: section headers with secondary keywords -->
<h2>What to Look for in a Startup CRM</h2>
<h2>Top 7 CRMs for Early-Stage Companies</h2>
<h2>How to Choose Based on Your Stage</h2>

<!-- Images: descriptive alt text with keyword context -->
<img src="crm-dashboard.png" alt="HubSpot CRM dashboard showing deal pipeline for startups" />

<!-- URL: short, keyword-rich, no dates for evergreen content -->
/blog/best-crm-for-startups   ✓
/blog/2024/01/15/best-crm-software-for-startups-guide-review  ✗
```

## Content Optimization
```
CONTENT THAT RANKS:
1. Matches search intent EXACTLY — if searchers want a list, write a list. If they want a guide, write a guide.
2. Covers the topic comprehensively — address the question + related questions
3. Better than what currently ranks — length isn't the goal, DEPTH is
4. Has a clear, scannable structure — headers, bullets, tables, visuals
5. Answers "People Also Ask" questions — Google shows you what else users want

CONTENT THAT DOESN'T RANK:
- Thin content (< 1000 words for competitive topics)
- Keyword stuffing — reads unnaturally, hurts ranking
- Content written for robots, not humans
- No differentiation from existing results — why would Google rank the 11th version of the same article?

Find content gaps:
- Search your target keyword
- Read the top 5 results
- Ask: what question is NOT answered here that the searcher might have?
- Answer THAT — it's your angle
```

# LINK BUILDING

## Link Building Strategies (Ethical)
```
CREATION-BASED (earn links by creating link-worthy content):
  - Original research / surveys — data people cite
  - Free tools and calculators — people link to useful resources
  - Comprehensive guides that become the definitive resource
  - Infographics that visualize complex data

OUTREACH-BASED (ask for relevant links):
  - Broken link building: find broken links → offer your content as replacement
    Tool: Ahrefs → Site Explorer → any domain → Broken Backlinks
  - Resource page link building: find "resources" pages → ask to be listed
    Search: "site:niche.com" + "resources" OR "links" OR "tools"
  - Guest posting: write content for relevant sites in your niche
    Quality over quantity — one link from an authoritative site > 100 spam links

DIGITAL PR (earn mentions from press):
  - Newsjack: respond to journalists covering your topic (HARO / Connectively)
  - Publish controversial or data-driven research → journalists cite it
  - Build relationships with journalists in your space

NEVER:
  - Buy links (Google penalty)
  - Exchange links in bulk ("I'll link to you if you link to me")
  - Links from link farms or low-quality directories
  - Exact-match anchor text manipulation
```

## Link Quality Assessment
```
HIGH QUALITY LINK:
  - From a relevant, topically related site
  - From a page that has its own inbound links (not just a blank page)
  - Editorial — someone chose to link to you, not paid/forced
  - Contextual — within the content body, not footer/sidebar

LOW QUALITY (may harm):
  - From sites with no traffic or relevance to your topic
  - From sites with hundreds of outbound links per page
  - Sitewide links (footer, sidebar)
  - Exact-match anchor text at high volume
  - Links from the same IP block / network of sites
```

# TRACKING AND MEASUREMENT
```
FREE TOOLS (set these up first):
  Google Search Console — GSC is mandatory
    → Performance: which queries bring impressions/clicks
    → Coverage: pages with indexing errors
    → Core Web Vitals: page experience scores

  Google Analytics 4 — for organic traffic behavior
    → Organic sessions, bounce rate, conversions from organic

PAID TOOLS:
  Ahrefs or SEMrush — rank tracking, competitor analysis, keyword research, backlink monitoring

KEY METRICS TO TRACK:
  Weekly:   Ranking changes for target keywords, crawl errors in GSC
  Monthly:  Organic traffic (sessions), keyword ranking distribution (positions 1-3, 4-10, 11-20)
  Quarterly: Backlink growth, domain rating/authority, organic conversion rate

  SEO SUCCESS LOOKS LIKE:
  - Keywords moving from position 11-20 to 4-10 to 1-3
  - Organic traffic compound growth month over month
  - Impressions growing faster than clicks (indicates content indexing but not ranking yet — gap to close)
```

# LOCAL SEO (if applicable)
```
GOOGLE BUSINESS PROFILE:
[ ] Claimed and verified
[ ] Complete: hours, phone, website, photos, description
[ ] Category set correctly (primary + secondary)
[ ] Reviews responded to (especially negative ones)
[ ] Posts published monthly

LOCAL RANKING FACTORS:
  - Proximity to searcher (can't control)
  - Relevance of business to query
  - Prominence: reviews, backlinks, citations

CITATIONS: consistent NAP (Name, Address, Phone) across:
  - Google Business Profile
  - Yelp, Apple Maps, Bing Places
  - Industry directories
  - Chamber of commerce listings
```
