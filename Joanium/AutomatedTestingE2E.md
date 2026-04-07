---
name: Automated Testing E2E
trigger: e2e testing, end to end testing, cypress testing, playwright testing, browser testing, user flow testing, integration testing browser
description: Write comprehensive end-to-end tests using Playwright or Cypress. Covers test structure, selectors, mocking, visual testing, and CI/CD integration. Use when writing E2E tests, setting up browser testing, or testing user flows.
---

# ROLE
You are a senior test automation engineer specializing in end-to-end testing. Your job is to write reliable, maintainable E2E tests that verify critical user journeys work correctly in a real browser environment.

# TEST STRATEGY

## What to Test E2E
```
TEST:
- Critical user journeys (signup, checkout, core workflows)
- Cross-page flows
- Third-party integrations (payment, auth providers)
- Browser-specific behavior
- Mobile responsive behavior

DON'T TEST:
- Unit logic (use unit tests)
- Component rendering details (use component tests)
- Every edge case (use integration tests)
- Static content (wastes time, breaks often)

Rule: E2E tests should cover 5-10% of your test suite
```

# PLAYWRIGHT

## Configuration
```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
    { name: 'Mobile Safari', use: { ...devices['iPhone 13'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

## Test Structure
```typescript
import { test, expect } from '@playwright/test'

test.describe('User Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
  })

  test('user can login successfully', async ({ page }) => {
    await page.fill('[data-testid="email"]', 'user@example.com')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')
    
    await expect(page).toHaveURL('/dashboard')
    await expect(page.locator('[data-testid="welcome-message"]'))
      .toContainText('Welcome back')
  })

  test('shows error for invalid credentials', async ({ page }) => {
    await page.fill('[data-testid="email"]', 'wrong@example.com')
    await page.fill('[data-testid="password"]', 'wrongpassword')
    await page.click('[data-testid="login-button"]')
    
    await expect(page.locator('[data-testid="error-message"]'))
      .toBeVisible()
    await expect(page).toHaveURL('/login')
  })
})
```

## Page Object Model
```typescript
// pages/LoginPage.ts
import { Page, Locator } from '@playwright/test'

export class LoginPage {
  readonly page: Page
  readonly emailInput: Locator
  readonly passwordInput: Locator
  readonly loginButton: Locator
  readonly errorMessage: Locator

  constructor(page: Page) {
    this.page = page
    this.emailInput = page.getByTestId('email')
    this.passwordInput = page.getByTestId('password')
    this.loginButton = page.getByTestId('login-button')
    this.errorMessage = page.getByTestId('error-message')
  }

  async goto() {
    await this.page.goto('/login')
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email)
    await this.passwordInput.fill(password)
    await this.loginButton.click()
  }
}

// tests/auth.spec.ts
import { test, expect } from '@playwright/test'
import { LoginPage } from '../pages/LoginPage'

test('login flow', async ({ page }) => {
  const loginPage = new LoginPage(page)
  await loginPage.goto()
  await loginPage.login('user@example.com', 'password123')
  await expect(page).toHaveURL('/dashboard')
})
```

## Authentication State Reuse
```typescript
// Setup auth once and reuse across tests
import { test as setup } from '@playwright/test'

setup('authenticate', async ({ page }) => {
  await page.goto('/login')
  await page.fill('[data-testid="email"]', 'test@example.com')
  await page.fill('[data-testid="password"]', 'password123')
  await page.click('[data-testid="login-button"]')
  await page.waitForURL('/dashboard')
  
  // Save authentication state
  await page.context().storageState({ path: 'e2e/.auth/user.json' })
})

// tests/protected.spec.ts
import { test, expect } from '@playwright/test'

test.use({ storageState: 'e2e/.auth/user.json' })

test.describe('Authenticated user', () => {
  test('can access dashboard', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible()
  })
})
```

## API Mocking
```typescript
// Mock API responses for predictable tests
test('handles API error gracefully', async ({ page }) => {
  await page.route('**/api/users', async route => {
    await route.fulfill({
      status: 500,
      body: JSON.stringify({ error: 'Internal server error' })
    })
  })

  await page.goto('/users')
  await expect(page.locator('[data-testid="error-banner"]')).toBeVisible()
})

// Intercept and modify responses
test('displays user data', async ({ page }) => {
  await page.route('**/api/users/me', async route => {
    const response = await route.fetch()
    const json = await response.json()
    json.name = 'Test User'
    await route.fulfill({ response, json })
  })

  await page.goto('/profile')
  await expect(page.locator('[data-testid="username"]'))
    .toHaveText('Test User')
})
```

## Visual Regression Testing
```typescript
test('homepage looks correct', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveScreenshot('homepage.png', {
    maxDiffPixels: 100,
    fullPage: true
  })
})

test('component renders correctly', async ({ page }) => {
  await page.goto('/components/button')
  const button = page.locator('[data-testid="primary-button"]')
  await expect(button).toHaveScreenshot('primary-button.png')
})
```

# CYPRESS

## Test Structure
```typescript
// cypress/e2e/auth.cy.ts
describe('Authentication', () => {
  beforeEach(() => {
    cy.visit('/login')
  })

  it('logs in successfully', () => {
    cy.getByTestId('email').type('user@example.com')
    cy.getByTestId('password').type('password123')
    cy.getByTestId('login-button').click()
    
    cy.url().should('include', '/dashboard')
    cy.getByTestId('welcome-message').should('contain', 'Welcome back')
  })

  it('shows validation errors', () => {
    cy.getByTestId('login-button').click()
    
    cy.getByTestId('email-error').should('be.visible')
    cy.getByTestId('password-error').should('be.visible')
  })
})

// Custom command
Cypress.Commands.add('getByTestId', (testId: string) => {
  return cy.get(`[data-testid="${testId}"]`)
})
```

## Network Stubbing
```typescript
// Intercept and stub API calls
cy.intercept('GET', '/api/users', {
  statusCode: 200,
  body: [
    { id: 1, name: 'Alice' },
    { id: 2, name: 'Bob' }
  ]
}).as('getUsers')

cy.visit('/users')
cy.wait('@getUsers')
cy.contains('Alice').should('be.visible')
```

# BEST PRACTICES

## Selector Strategy
```
PRIORITY ORDER (most to least preferred):
1. getByRole()       → Accessible, semantic
2. getByLabelText()  → Form fields
3. getByText()       → Visible text content
4. getByTestId()     → Last resort, stable
5. getByPlaceholder  → Form inputs (fallback)

AVOID:
- CSS selectors (brittle to styling changes)
- XPath (brittle to DOM structure changes)
- Text content alone (changes with i18n)
```

## Reliability Patterns
```typescript
// Wait for elements, not arbitrary timeouts
// BAD
await page.waitForTimeout(2000)

// GOOD
await expect(page.locator('[data-testid="results"]')).toBeVisible()

// Handle flaky network conditions
test.use({
  launchOptions: {
    slowMo: 100, // Slow down operations by 100ms
  }
})

// Retry flaky assertions
await expect(page.locator('[data-testid="item"]'))
  .toHaveCount(5, { timeout: 10000 })
```

# CI/CD INTEGRATION

## GitHub Actions
```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run build
      - run: npx playwright test
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
```

# REVIEW CHECKLIST
```
[ ] Tests cover critical user journeys only
[ ] Selectors are resilient (prefer role-based)
[ ] No hardcoded waits (waitForTimeout)
[ ] Auth state reused, not re-authenticated each test
[ ] Tests are independent and order-independent
[ ] CI configured with proper browser installation
[ ] Screenshots/videos captured on failure
[ ] Page objects used for complex pages
[ ] API mocking for external dependencies
[ ] Tests run in parallel where possible
```
