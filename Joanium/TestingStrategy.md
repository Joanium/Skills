---
name: Testing Strategy
trigger: write tests, unit test, integration test, e2e test, test coverage, testing strategy, jest, pytest, vitest, cypress, playwright, TDD, test this function, how to test, test suite
description: Design and write high-quality tests across all levels — unit, integration, and end-to-end. Covers Jest/Vitest, pytest, Playwright/Cypress, TDD, mocking strategy, coverage, and what NOT to test.
---

# ROLE
You are a senior test engineer. Your job is to help design a testing strategy and write tests that are fast, reliable, meaningful, and maintainable. You distinguish between tests that provide real confidence and tests that just inflate coverage numbers.

# CORE PHILOSOPHY
```
TEST BEHAVIOR, NOT IMPLEMENTATION
  - Test what the code does, not how it does it
  - Tests that break when you refactor (without changing behavior) are bad tests

THE TEST PYRAMID
  Unit (70%):        Fast, isolated, many — test pure logic
  Integration (20%): Test how units work together — DB, API, services
  E2E (10%):         Slow, brittle, few — test critical user journeys only

A GOOD TEST IS:
  Fast    → runs in milliseconds (unit), seconds (integration), minutes (e2e max)
  Isolated → doesn't depend on other tests, doesn't share mutable state
  Repeatable → same result every run, regardless of environment
  Self-documenting → test name describes exactly what's being verified
  Meaningful → failure means something real is broken
```

# UNIT TESTING

## Anatomy of a Good Test (AAA Pattern)
```javascript
// Jest / Vitest
describe('calculateDiscount', () => {
  it('applies 20% discount for premium users', () => {
    // ARRANGE — set up inputs and expected outputs
    const user = { tier: 'premium' }
    const price = 100

    // ACT — call the thing being tested
    const result = calculateDiscount(price, user)

    // ASSERT — verify the output
    expect(result).toBe(80)
  })

  it('applies no discount for free users', () => {
    const user = { tier: 'free' }
    expect(calculateDiscount(100, user)).toBe(100)
  })

  it('throws when price is negative', () => {
    expect(() => calculateDiscount(-10, { tier: 'free' }))
      .toThrow('Price must be non-negative')
  })
})
```

```python
# pytest
def test_calculate_discount_for_premium_user():
    # Arrange
    user = User(tier='premium')
    price = 100

    # Act
    result = calculate_discount(price, user)

    # Assert
    assert result == 80

def test_calculate_discount_raises_on_negative_price():
    with pytest.raises(ValueError, match="Price must be non-negative"):
        calculate_discount(-10, User(tier='free'))
```

## Test Naming — Name the Behavior
```
Pattern: [unit]_[scenario]_[expected outcome]
Good:  "calculateDiscount_premiumUser_returns20PercentOff"
Good:  "should apply 20% discount for premium users"
Bad:   "test1", "testDiscount", "discountTest"

The test name should be readable as a spec:
  it('returns null when user is not found')
  it('sends email when order is placed')
  it('rejects invalid email format')
```

## Mocking Strategy
```javascript
// Mock external dependencies — NOT the thing being tested
// WRONG: mocking the unit under test defeats the purpose
// RIGHT: mock DB, HTTP calls, time, random values

// Jest: mock a module
jest.mock('./emailService', () => ({
  sendEmail: jest.fn().mockResolvedValue({ success: true })
}))

// Verify mock was called correctly
expect(emailService.sendEmail).toHaveBeenCalledWith({
  to: 'user@example.com',
  subject: 'Welcome'
})
expect(emailService.sendEmail).toHaveBeenCalledTimes(1)

// Mock time — don't let tests depend on system clock
jest.useFakeTimers()
jest.setSystemTime(new Date('2024-01-15'))
// ... test code that uses Date.now() or new Date()
jest.useRealTimers()

// Mock environment variables
const OLD_ENV = process.env
beforeEach(() => {
  process.env = { ...OLD_ENV, API_KEY: 'test-key' }
})
afterEach(() => {
  process.env = OLD_ENV
})
```

```python
# pytest mocking with unittest.mock
from unittest.mock import patch, MagicMock

def test_order_sends_confirmation_email():
    with patch('app.services.email.send_email') as mock_send:
        mock_send.return_value = True
        
        result = place_order(user_id=1, product_id=42)
        
        assert result.success is True
        mock_send.assert_called_once_with(
            to='user@example.com',
            subject='Order Confirmed'
        )

# pytest fixtures — reusable setup
@pytest.fixture
def db_session():
    session = create_test_session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def sample_user(db_session):
    user = User(email='test@example.com', tier='premium')
    db_session.add(user)
    db_session.commit()
    return user

def test_user_has_premium_discount(sample_user):
    assert calculate_discount(100, sample_user) == 80
```

## Edge Cases to Always Test
```
Numeric:    0, negative, max value, floating point precision
String:     empty string, whitespace only, unicode, very long string
Collection: empty list/array, single item, large collection
Null/None:  null inputs, null returns, undefined properties
Async:      resolved, rejected, timeout
Errors:     expected errors thrown, error messages correct
Boundaries: first item, last item, just inside/outside a limit
```

# INTEGRATION TESTING

## Database Integration Tests
```javascript
// Use a real test database — never mock the DB in integration tests
// Jest + Prisma example

beforeAll(async () => {
  await prisma.$connect()
})

afterAll(async () => {
  await prisma.$disconnect()
})

beforeEach(async () => {
  // Clean slate before each test
  await prisma.order.deleteMany()
  await prisma.user.deleteMany()
})

it('creates order and updates inventory', async () => {
  const user = await prisma.user.create({ data: { email: 'test@test.com' } })
  const product = await prisma.product.create({ data: { name: 'Widget', stock: 10 } })

  const order = await createOrder({ userId: user.id, productId: product.id, quantity: 3 })

  const updatedProduct = await prisma.product.findUnique({ where: { id: product.id } })
  expect(updatedProduct.stock).toBe(7)
  expect(order.status).toBe('confirmed')
})
```

## API Integration Tests
```javascript
// Test the full request/response cycle with supertest
import request from 'supertest'
import app from '../app'

describe('POST /api/users', () => {
  it('creates a user and returns 201 with user data', async () => {
    const res = await request(app)
      .post('/api/users')
      .send({ email: 'new@example.com', name: 'Alice' })
      .set('Authorization', `Bearer ${testToken}`)

    expect(res.status).toBe(201)
    expect(res.body).toMatchObject({
      id: expect.any(String),
      email: 'new@example.com',
      name: 'Alice'
    })
    expect(res.body.password).toBeUndefined()  // sensitive fields not leaked
  })

  it('returns 422 when email is missing', async () => {
    const res = await request(app).post('/api/users').send({ name: 'Alice' })
    expect(res.status).toBe(422)
    expect(res.body.errors).toContainEqual(
      expect.objectContaining({ field: 'email' })
    )
  })
})
```

# END-TO-END TESTING

## Playwright (preferred over Cypress for modern projects)
```typescript
// playwright.config.ts
export default {
  testDir: './e2e',
  use: {
    baseURL: 'http://localhost:3000',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'Mobile Safari', use: { ...devices['iPhone 13'] } },
  ]
}

// e2e/checkout.spec.ts — test critical user journeys
import { test, expect } from '@playwright/test'

test.describe('Checkout flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('[data-testid="email"]', 'test@example.com')
    await page.fill('[data-testid="password"]', 'password')
    await page.click('[data-testid="login-btn"]')
    await expect(page).toHaveURL('/dashboard')
  })

  test('user can complete purchase', async ({ page }) => {
    await page.goto('/products/widget-123')
    await page.click('[data-testid="add-to-cart"]')
    await page.goto('/cart')
    await page.click('[data-testid="checkout-btn"]')

    await page.fill('[data-testid="card-number"]', '4242424242424242')
    await page.fill('[data-testid="expiry"]', '12/26')
    await page.fill('[data-testid="cvv"]', '123')
    await page.click('[data-testid="place-order"]')

    await expect(page.locator('[data-testid="order-confirmation"]')).toBeVisible()
    await expect(page.locator('[data-testid="order-id"]')).toContainText('ORD-')
  })
})
```

## data-testid Strategy
```html
<!-- Add data-testid to interactive and key elements -->
<!-- Never select by CSS class or text — both change frequently -->
<button data-testid="submit-order">Place Order</button>
<input data-testid="email-input" type="email" />
<div data-testid="order-confirmation">Order Confirmed!</div>

<!-- Pattern: component-element-variant -->
data-testid="user-profile-avatar"
data-testid="product-card-price"
data-testid="nav-mobile-menu"
```

# COVERAGE — WHAT IT MEANS AND DOESN'T

```
Coverage measures: which lines ran during tests
Coverage does NOT measure: whether those tests are meaningful

80% meaningful coverage >> 100% trivial coverage

Target coverage by layer:
  Business logic / services:  90%+ (critical — test exhaustively)
  API handlers:               80%+ (test happy path + error cases)
  UI components:              60-70% (focus on behavior, not rendering)
  Config / boilerplate:       skip — no business logic here

What to NOT test:
  - Third-party library internals
  - Simple getters/setters with no logic
  - Framework magic (ORM generated methods, etc.)
  - Config files
  - Type definitions (TypeScript handles this)
```

# TDD WORKFLOW
```
RED:   Write a failing test for the behavior you want to add
GREEN: Write the minimum code to make it pass (don't over-engineer)
REFACTOR: Clean up the code — tests protect you from breaking it

Practical TDD for a new feature:
1. Write the test for the simplest happy path first
2. Make it pass with naive code
3. Write edge case tests — they'll fail
4. Make them pass
5. Refactor with confidence — tests catch regressions
```

# TEST CONFIGURATION

## Jest / Vitest Setup
```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'node',
  setupFilesAfterFramework: ['./src/test/setup.ts'],
  coverageThreshold: {
    global: { branches: 70, functions: 80, lines: 80, statements: 80 }
  },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1'
  },
  testPathIgnorePatterns: ['/node_modules/', '/e2e/']
}
```

## pytest Setup
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests (require DB)
    slow: Tests that take > 1 second
```
