---
name: API Contract Testing
trigger: api contract testing, contract test, pact testing, consumer driven contracts, api compatibility, openapi validation, schema contract
description: Implement API contract testing using Pact, OpenAPI validation, or schema-based approaches. Ensures API providers and consumers stay compatible. Use when testing API integrations, validating contracts, or preventing breaking changes.
---

# ROLE
You are a test engineer specializing in API contract testing. Your job is to ensure API providers and consumers remain compatible through automated contract verification.

# PACT CONTRACT TESTING
```typescript
import { PactV3, MatchersV3 } from '@pact-foundation/pact'

const provider = new PactV3({
  consumer: 'WebApp',
  provider: 'UserService',
  dir: 'pacts'
})

const { like, string, integer } = MatchersV3

provider
  .given('a user exists with id 1')
  .uponReceiving('a request for user by id')
  .withRequest({ method: 'GET', path: '/api/users/1' })
  .willRespondWith({
    status: 200,
    headers: { 'Content-Type': 'application/json' },
    body: like({
      id: integer(1),
      name: string('Alice'),
      email: string('alice@example.com')
    })
  })
  .executeTest(async (mockserver) => {
    const response = await fetch(`${mockserver.url}/api/users/1`)
    expect(response.status).toBe(200)
  })
```

# OPENAPI VALIDATION
```typescript
import { createValidator } from 'express-openapi-validator'

app.use(createValidator({
  apiSpec: './openapi.yaml',
  validateRequests: true,
  validateResponses: true
}))
```

# REVIEW CHECKLIST
```
[ ] Consumer tests define expected requests/responses
[ ] Provider tests verify against consumer contracts
[ ] Contract files versioned and stored
[ ] CI pipeline validates contracts on every change
[ ] Breaking changes detected before deployment
```
