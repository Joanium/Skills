---
name: Consumer-Driven Contract Testing
trigger: contract testing, consumer-driven contracts, Pact, pact testing, API contract test, integration testing contracts, provider verification, consumer contract, microservices testing, avoid integration tests, schema contract
description: Implement consumer-driven contract testing to safely evolve APIs without breaking consumers. Covers Pact framework, writing consumer tests, provider verification, broker setup, and fitting contracts into CI/CD.
---

# ROLE
You are a senior engineer specializing in microservices testing strategy. Consumer-driven contract testing replaces the brittle, slow, expensive integration test environment with fast, isolated, trustworthy tests. Your job is to implement it correctly and get teams to actually use it.

# WHY CONTRACT TESTING

## The Problem with Integration Tests
```
TYPICAL MICROSERVICES TESTING PYRAMID (wrong):
                 /\
                /E2E\         ← slow, flaky, expensive
               /------\
              /  Integ  \     ← shared test environment, breaks constantly
             /  (API/DB)  \
            /--------------\
           /   Unit Tests    \

PROBLEMS:
  Shared test environment → flaky, unavailable, wrong version, costs money
  One team breaks the env → everyone's CI is red
  E2E tests take hours → slow feedback loop
  "It works in staging" then breaks in prod anyway
  You're testing the whole system, not the interface
```

## What Contract Testing Solves
```
CONSUMER-DRIVEN CONTRACTS:
  Consumer defines what it expects from the provider
  Provider verifies it can meet those expectations
  Both sides tested in isolation (no running services needed)

                    ┌─────────────────────────────────────────┐
                    │          Pact Broker                    │
                    └──────────────┬──────────────────────────┘
                                   │ stores contracts
                    ┌──────────────▼──────────────┐
  ┌──────────────┐  │    Contract (Pact file)     │  ┌──────────────┐
  │  Consumer    │  │ "GET /users/123 returns      │  │  Provider    │
  │  (Frontend,  │──│  { id, name, email }"        │──│  (User API)  │
  │   Mobile,    │  │                              │  │              │
  │   Service B) │  │                              │  │              │
  └──────────────┘  └──────────────────────────────┘  └──────────────┘
   writes consumer    contract is the shared artifact   verifies against
   tests, generates                                     real implementation
   pact file
```

# PACT FRAMEWORK

## Consumer Test (JavaScript/TypeScript)
```typescript
// consumer/src/__tests__/userApi.pact.test.ts
import { PactV3, MatchersV3 } from '@pact-foundation/pact';
import { UserApiClient } from '../userApiClient';
import path from 'path';

const { like, string, integer, timestamp } = MatchersV3;

// 1. Define the Pact (contract)
const provider = new PactV3({
  consumer: 'FrontendApp',
  provider: 'UserService',
  log: path.resolve(process.cwd(), 'logs', 'pact.log'),
  dir: path.resolve(process.cwd(), 'pacts'),  // where Pact files are saved
  logLevel: 'info',
});

describe('User API Contract', () => {
  // 2. Define an interaction (what consumer expects from provider)
  describe('GET /users/:id', () => {
    it('returns a user when they exist', async () => {
      await provider
        .given('a user with id 123 exists')     // provider state
        .uponReceiving('a request for user 123') // interaction description
        .withRequest({
          method: 'GET',
          path: '/users/123',
          headers: {
            Accept: 'application/json',
            Authorization: like('Bearer token123'),  // like() = match type, not exact value
          },
        })
        .willRespondWith({
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: {
            id: integer(123),                // matches any integer
            name: string('Alice'),           // matches any string
            email: string('alice@ex.com'),   // matches any string
            createdAt: timestamp("yyyy-MM-dd'T'HH:mm:ssX"),  // matches timestamp format
            // NOTE: don't include fields the consumer doesn't use
            // If consumer doesn't use `role`, don't put it here
            // Adding extra fields to provider won't break this contract
          },
        })
        .executeTest(async (mockProvider) => {
          // 3. Test the consumer code against the mock provider
          const client = new UserApiClient({ baseUrl: mockProvider.url });
          const user = await client.getUser(123);

          expect(user.id).toBe(123);
          expect(user.name).toBe('Alice');
          expect(user.email).toBe('alice@ex.com');
        });
    });

    it('returns 404 when user does not exist', async () => {
      await provider
        .given('a user with id 999 does not exist')
        .uponReceiving('a request for non-existent user 999')
        .withRequest({
          method: 'GET',
          path: '/users/999',
          headers: { Accept: 'application/json' },
        })
        .willRespondWith({
          status: 404,
          body: {
            error: { code: string('USER_NOT_FOUND') },
          },
        })
        .executeTest(async (mockProvider) => {
          const client = new UserApiClient({ baseUrl: mockProvider.url });
          await expect(client.getUser(999)).rejects.toThrow('User not found');
        });
    });
  });
});
```

## Provider Verification (Node.js/Express)
```typescript
// provider/src/__tests__/pact.provider.test.ts
import { Verifier } from '@pact-foundation/pact';
import { app } from '../app';
import { db } from '../database';
import http from 'http';

describe('Pact Provider Verification', () => {
  let server: http.Server;

  beforeAll(async () => {
    server = app.listen(4000);
  });

  afterAll(async () => {
    server.close();
    await db.destroy();
  });

  it('validates the expectations of FrontendApp', async () => {
    const verifier = new Verifier({
      provider: 'UserService',
      providerBaseUrl: 'http://localhost:4000',

      // Where to get contracts from:
      // Option A: Pact Broker (recommended for teams)
      pactBrokerUrl: process.env.PACT_BROKER_URL,
      pactBrokerToken: process.env.PACT_BROKER_TOKEN,
      consumerVersionSelectors: [
        { mainBranch: true },     // contracts from consumer's main branch
        { deployedOrReleased: true },  // contracts from deployed consumer versions
      ],

      // Option B: Local pact files (for development)
      // pactUrls: [path.resolve(__dirname, '../../consumer/pacts/FrontendApp-UserService.json')],

      // Provider states: set up database state for each interaction
      stateHandlers: {
        'a user with id 123 exists': async () => {
          await db.query(
            `INSERT INTO users (id, name, email) VALUES (123, 'Alice', 'alice@ex.com')
             ON CONFLICT (id) DO UPDATE SET name = 'Alice', email = 'alice@ex.com'`
          );
        },
        'a user with id 999 does not exist': async () => {
          await db.query(`DELETE FROM users WHERE id = 999`);
        },
        // The empty string state: no setup needed
        '': async () => {},
      },

      publishVerificationResult: true,
      providerVersion: process.env.GIT_SHA || '1.0.0',
      providerVersionBranch: process.env.GIT_BRANCH || 'main',
    });

    await verifier.verifyProvider();
  });
});
```

## Provider State Endpoint (Alternative Approach)
```typescript
// Add a /_pact/provider-states endpoint to your provider
// Pact calls this to set up state before each interaction

app.post('/_pact/provider-states', async (req, res) => {
  const { state } = req.body as { state: string; params?: Record<string, unknown> };

  switch (state) {
    case 'a user with id 123 exists':
      await db.users.upsert({ id: 123, name: 'Alice', email: 'alice@ex.com' });
      break;

    case 'a user with id 999 does not exist':
      await db.users.delete({ where: { id: 999 } });
      break;
  }

  res.json({ state });
});

// Only enable in test mode:
if (process.env.PACT_TEST_MODE === 'true') {
  app.use('/_pact', pactStateRouter);
}
```

# PACT BROKER SETUP

## Self-Hosted (Docker)
```yaml
# docker-compose.pact.yml
version: '3'
services:
  pact-broker:
    image: pactfoundation/pact-broker:latest
    ports:
      - "9292:9292"
    environment:
      PACT_BROKER_DATABASE_URL: "postgres://pact:pact@postgres/pact"
      PACT_BROKER_BASIC_AUTH_USERNAME: admin
      PACT_BROKER_BASIC_AUTH_PASSWORD: password
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: pact
      POSTGRES_PASSWORD: pact
      POSTGRES_DB: pact
    volumes:
      - pact-db:/var/lib/postgresql/data

volumes:
  pact-db:
```

## PactFlow (Managed — Recommended)
```bash
# PactFlow: managed Pact Broker by SmartBear
# Free tier: 5 integrations

# Publish pacts after consumer test run:
npx pact-broker publish ./pacts \
  --consumer-app-version $GIT_SHA \
  --branch $GIT_BRANCH \
  --broker-base-url $PACT_BROKER_URL \
  --broker-token $PACT_BROKER_TOKEN

# Check if safe to deploy:
npx pact-broker can-i-deploy \
  --pacticipant FrontendApp \
  --version $GIT_SHA \
  --to-environment production \
  --broker-base-url $PACT_BROKER_URL \
  --broker-token $PACT_BROKER_TOKEN
```

# CI/CD INTEGRATION

## Consumer Pipeline
```yaml
# .github/workflows/consumer-ci.yml
name: Consumer CI
on: [push, pull_request]

jobs:
  test-and-publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run consumer pact tests
        run: npm test
        # This generates pact files in ./pacts/

      - name: Publish pact to broker
        run: |
          npx pact-broker publish ./pacts \
            --consumer-app-version ${{ github.sha }} \
            --branch ${{ github.ref_name }} \
            --broker-base-url ${{ vars.PACT_BROKER_URL }} \
            --broker-token ${{ secrets.PACT_BROKER_TOKEN }}

  deploy:
    needs: test-and-publish
    steps:
      - name: Check if safe to deploy
        run: |
          npx pact-broker can-i-deploy \
            --pacticipant FrontendApp \
            --version ${{ github.sha }} \
            --to-environment production \
            --broker-base-url ${{ vars.PACT_BROKER_URL }} \
            --broker-token ${{ secrets.PACT_BROKER_TOKEN }}

      - name: Deploy to production
        run: ./deploy.sh production
```

## Provider Pipeline
```yaml
# .github/workflows/provider-ci.yml
name: Provider CI
on: [push, pull_request]

jobs:
  verify-contracts:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: testdb
          POSTGRES_PASSWORD: test

    steps:
      - uses: actions/checkout@v4

      - name: Verify pact contracts
        run: npm run test:pact
        env:
          PACT_BROKER_URL: ${{ vars.PACT_BROKER_URL }}
          PACT_BROKER_TOKEN: ${{ secrets.PACT_BROKER_TOKEN }}
          GIT_SHA: ${{ github.sha }}
          GIT_BRANCH: ${{ github.ref_name }}
        # Verification results published to broker automatically

  deploy:
    needs: verify-contracts
    steps:
      - name: Check if safe to deploy
        run: |
          npx pact-broker can-i-deploy \
            --pacticipant UserService \
            --version ${{ github.sha }} \
            --to-environment production \
            --broker-base-url ${{ vars.PACT_BROKER_URL }} \
            --broker-token ${{ secrets.PACT_BROKER_TOKEN }}
```

# WHAT TO CONTRACT TEST VS WHAT NOT TO

## Contract Testing Is For
```
✓ HTTP APIs between services (REST, GraphQL)
✓ Message queue schemas (Kafka, SQS — use async Pact)
✓ APIs used by mobile apps or browser frontends
✓ Third-party APIs you depend on (verifying their promises)

DO NOT CONTRACT TEST:
✗ Internal implementation — contract tests are about the public interface
✗ Business logic — that's unit testing
✗ Things that don't cross a service boundary
✗ Database schemas (use DB migration tests instead)
```

## What Goes in a Contract (and What Doesn't)
```
INCLUDE in consumer contract:
  ✓ Only fields the consumer actually uses
  ✓ Required HTTP headers consumer sends
  ✓ Status codes consumer handles (200, 404, 401, etc.)
  ✓ Error response shapes consumer parses

DO NOT include:
  ✗ Fields provider has but consumer ignores
  ✗ Response time requirements (that's load testing)
  ✗ Exact values for dynamic fields (use matchers)
  ✗ Provider-internal validation logic
```

# MATCHER REFERENCE
```typescript
// Structural matchers (verify type/structure, not exact value)
like('hello')           // any string
like(42)                // any number
like(true)             // any boolean

// Type matchers
string('Alice')         // any string
integer(42)            // any integer
decimal(9.99)          // any decimal number
boolean(true)          // any boolean

// Array matchers
eachLike({ id: like(1), name: like('Alice') })  // array of objects with this shape
atLeastOneLike({ id: like(1) })                  // non-empty array

// Format matchers
timestamp("yyyy-MM-dd'T'HH:mm:ssX")  // ISO timestamp format
date('yyyy-MM-dd')                    // date format
uuid()                                // UUID format
email()                               // email format
url()                                 // URL format

// Regex
regex(/^\d{3}-\d{4}$/, '555-1234')   // matches pattern
```

# COMMON PITFALLS
```
MISTAKE: Consumer test matches exact values instead of types
FIX: Use matchers. "name: string('Alice')" not "name: 'Alice'"
     Exact matches break when test data changes.

MISTAKE: Consumer requests fields it doesn't use
FIX: Contract includes ONLY fields the consumer code actually reads.
     Extra provider fields don't break existing contracts.

MISTAKE: No provider states
FIX: Every interaction needs a provider state. State = database setup.
     Without state, provider tests are flaky.

MISTAKE: Testing provider logic via contracts
FIX: Contracts test the interface. Unit tests test the logic.
     "User with invalid email returns 422" → probably don't need a contract for this.

MISTAKE: Skipping can-i-deploy
FIX: Without can-i-deploy, you lose the main safety guarantee.
     Always check before deploying both consumer and provider.

MISTAKE: Manual pact file sharing (Slack, git commit)
FIX: Use a Pact Broker. Manual sharing doesn't scale and can't do can-i-deploy.
```
