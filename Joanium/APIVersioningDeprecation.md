---
name: API Versioning & Deprecation
trigger: api versioning, version my api, deprecate an endpoint, breaking changes api, backwards compatibility, sunset api, api migration, api lifecycle, version strategy, api evolution
description: Design and execute API versioning strategies, manage breaking changes, and deprecate endpoints without breaking clients. Use when planning API evolution, communicating changes, or migrating consumers.
---

A versioned API is a contract. Breaking it silently is a betrayal. The goal is to evolve your API confidently — adding power, removing complexity — while giving consumers the time and tools to keep up.

## The Core Tension

Every API change lives on a spectrum:

```
Additive (safe)          →     Breaking (dangerous)
─────────────────────────────────────────────────────
Add optional field          Remove field
Add new endpoint            Rename field
Add enum value (careful)    Change field type
Add optional query param    Change HTTP method
Relax validation            Tighten validation
```

**Golden rule:** Never remove or rename. Extend, then deprecate, then retire.

## Versioning Strategies

### Strategy 1: URI Versioning (most common, most visible)
```
GET /v1/users
GET /v2/users
```
**Pros:** Simple, explicit, cache-friendly, easy to route  
**Cons:** URL pollution, clients must opt in to upgrades  
**Best for:** Public APIs, REST APIs with many external consumers

### Strategy 2: Header Versioning
```
GET /users
Accept: application/vnd.myapp.v2+json
API-Version: 2
```
**Pros:** Clean URLs, RESTfully "correct"  
**Cons:** Hidden, harder to test in browser, caching complications  
**Best for:** Internal APIs, APIs consumed by controlled clients

### Strategy 3: Query Parameter Versioning
```
GET /users?version=2
```
**Pros:** Easy to test, no routing changes  
**Cons:** Pollutes query strings, caching issues  
**Best for:** Prototypes, rarely — avoid in production

### Strategy 4: Content Negotiation (most mature)
```
Accept: application/vnd.myapp+json; version=2
```
**Best for:** Sophisticated public APIs (GitHub does this)

## When to Create a New Version

Create v2 when you must:
```
✓ Remove a field consumers depend on
✓ Rename a field or resource
✓ Change field types (string → integer)
✓ Change authentication scheme
✓ Restructure the response envelope
✓ Change pagination contract

Do NOT version for:
✗ Adding optional fields (just add them)
✗ Adding new endpoints (just add them)
✗ Bug fixes that correct wrong behavior
✗ Performance improvements
✗ New optional query parameters
```

## The Deprecation Lifecycle

A clean deprecation has four phases:

```
Phase 1: ANNOUNCE  →  Phase 2: DEPRECATE  →  Phase 3: SUNSET  →  Phase 4: RETIRE
   ↓                      ↓                       ↓                    ↓
Blog post              Add headers             Last reminder         Remove code
Migration guide        Log warnings            Final warning         404 responses
Timeline set           Usage metrics           Unblock teams         Archive docs
```

### Minimum Timelines
```
Internal API:   2–4 weeks notice
Partner API:    3–6 months notice
Public API:     6–12 months notice (1 year is industry standard)
```

## Implementing Deprecation Headers

Add these to EVERY response from deprecated endpoints:

```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Jan 2026 00:00:00 GMT
Link: <https://api.example.com/v2/users>; rel="successor-version"
Link: <https://docs.example.com/migration/v1-to-v2>; rel="deprecation"
```

```javascript
// Express middleware for deprecation headers
function deprecate(sunsetDate, successorPath, migrationGuide) {
  return (req, res, next) => {
    res.set({
      'Deprecation': 'true',
      'Sunset': new Date(sunsetDate).toUTCString(),
      'Link': [
        `<${successorPath}>; rel="successor-version"`,
        `<${migrationGuide}>; rel="deprecation"`
      ].join(', ')
    });
    next();
  };
}

// Usage
router.get('/v1/users', deprecate('2025-06-01', '/v2/users', 'https://docs.example.com/v1-migration'), handler);
```

## Tracking Deprecation Usage

You cannot retire what you cannot measure. Log every deprecated endpoint call:

```javascript
function trackDeprecatedUsage(endpoint, version) {
  return (req, res, next) => {
    metrics.increment('api.deprecated.calls', {
      endpoint,
      version,
      consumer: req.headers['x-client-id'] || 'unknown',
      user_agent: req.headers['user-agent']
    });

    logger.warn('Deprecated endpoint called', {
      endpoint,
      version,
      consumer: req.headers['x-client-id'],
      sunset: '2025-06-01'
    });

    next();
  };
}
```

Build a dashboard: **who is still calling v1, how often, and from what systems**.  
You cannot retire safely until this dashboard shows near-zero.

## Writing the Migration Guide

A migration guide must have:

```markdown
# Migrating from v1 to v2

## What changed and why
[Explain the motivation, not just the diff]

## Breaking changes

### users.name → users.firstName + users.lastName
**v1:** `{ "name": "John Smith" }`
**v2:** `{ "firstName": "John", "lastName": "Smith" }`

**Migration:** Split the name field on your side, or use the new format directly.

## What stayed the same
[Reassure — list unchanged endpoints, fields, auth methods]

## Step-by-step migration
1. Update your base URL from /v1 to /v2
2. Update name handling (see above)
3. Update pagination (cursor-based, not offset)
4. Test with your staging environment
5. Monitor error rates for 48 hours after switching

## Timeline
- Now: v2 is available in staging
- March 1: v2 available in production
- June 1: v1 will stop returning 200s (will return 410 Gone)
- July 1: v1 endpoints removed

## Getting help
- Slack: #api-migration
- Email: api-support@example.com
- Office hours: Thursdays 2pm
```

## Version Routing Patterns

```javascript
// Route-based versioning with clear separation
// api/v1/users.js and api/v2/users.js

const express = require('express');
const app = express();

// Mount versioned routers
app.use('/v1', require('./api/v1'));
app.use('/v2', require('./api/v2'));

// Default to latest (optional — makes /users → /v2/users)
app.use('/', require('./api/v2'));

// Graceful retirement: 410 Gone is better than 404
app.use('/v0', (req, res) => {
  res.status(410).json({
    error: 'API v0 has been retired',
    message: 'Please migrate to v2',
    migration_guide: 'https://docs.example.com/migration'
  });
});
```

## API Versioning Checklist

```
Before releasing a breaking change:
☐ Is this change truly necessary? Can it be additive instead?
☐ Is the old version documented with a clear sunset date?
☐ Is the migration guide written and reviewed by a consumer?
☐ Are deprecation headers deployed to ALL v1 responses?
☐ Is usage tracking in place? (who is calling v1?)
☐ Are all internal teams notified with the timeline?
☐ Are external consumers notified via email/blog/changelog?
☐ Is the new version stable in staging for at least 2 weeks?
☐ Is a rollback plan documented?

Before retiring a version:
☐ Is traffic on the old version < 1% of total? (or zero for internal)
☐ Have all known consumers confirmed migration?
☐ Has a final warning been sent 30 days before sunset?
☐ Will you return 410 Gone (not 404) after retirement?
☐ Are the old docs archived (not deleted)?
☐ Is there a monitoring alert for unexpected traffic post-retirement?
```

## Version Design Summary

```
## API Version Decision

**Change proposed:** [Description]
**Breaking?** [Yes/No — list affected consumers]
**Strategy:** [URI / Header / Query / Content negotiation]

**Timeline:**
- Announce: [Date]
- Deprecation headers live: [Date]
- New version GA: [Date]
- Sunset: [Date]
- Retirement: [Date]

**Migration guide:** [Link]
**Tracking dashboard:** [Link]

**Current v1 traffic:** [calls/day, distinct consumers]
**Exit criteria for retirement:** [traffic < X, or all known consumers confirmed]
```
