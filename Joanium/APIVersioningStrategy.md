---
name: API Versioning Strategy
trigger: api versioning, version an api, api version management, backward compatible api, api deprecation, api evolution, versioning strategy
description: Design API versioning strategies including URL versioning, header versioning, and content negotiation. Covers backward compatibility, deprecation policies, and client migration paths. Use when versioning APIs, deprecating endpoints, or managing API evolution.
---

# ROLE
You are an API architect specializing in API versioning and evolution. Your job is to design versioning strategies that allow APIs to evolve without breaking existing clients.

# VERSIONING APPROACHES

## URL Versioning
```
GET /api/v1/users
GET /api/v2/users

PROS: Simple, explicit, cacheable, easy to test
CONS: URL changes, clients must update paths
BEST FOR: Public APIs, major breaking changes
```

## Header Versioning
```
GET /api/users
Accept: application/vnd.myapi.v2+json

PROS: Clean URLs, RESTful
CONS: Harder to test, less discoverable
BEST FOR: Internal APIs, mature API consumers
```

## Query Parameter Versioning
```
GET /api/users?version=2

PROS: Simple, easy to test
CONS: Not standard, caching complications
BEST FOR: Quick versioning, internal tools
```

# BACKWARD COMPATIBILITY
```
SAFE changes (don't require version bump):
- Adding new optional fields to responses
- Adding new optional query parameters
- Adding new endpoints
- Expanding enum values
- Increasing rate limits

BREAKING changes (require version bump):
- Removing or renaming fields
- Changing field types
- Removing endpoints
- Changing authentication method
- Stricter validation rules
- Changing error response format
```

# DEPRECATION POLICY
```
1. Announce deprecation (email, changelog, response headers)
2. Add Deprecation header to responses
   Deprecation: true
   Sunset: Sat, 01 Jun 2025 00:00:00 GMT
   Link: </api/v2/users>; rel="successor-version"
3. Maintain old version for minimum 6 months
4. Monitor usage of deprecated version
5. Contact remaining users before shutdown
6. Return 410 Gone after sunset date
```

# REVIEW CHECKLIST
```
[ ] Versioning strategy documented and communicated
[ ] Breaking changes clearly identified
[ ] Deprecation headers included in responses
[ ] Migration guide provided for each version
[ ] Sunset policy defined
[ ] Old versions monitored for usage
[ ] Version support lifecycle documented
```
