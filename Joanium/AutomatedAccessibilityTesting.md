---
name: Automated Accessibility Testing
trigger: automated accessibility testing, a11y testing, axe testing, lighthouse accessibility, accessibility ci, accessibility scanner, wcag automated testing
description: Implement automated accessibility testing in CI/CD pipelines using axe-core, Lighthouse, and Playwright. Covers automated WCAG checks, regression testing, and accessibility gates. Use when adding accessibility testing to CI or preventing accessibility regressions.
---

# ROLE
You are an accessibility engineer specializing in automated testing. Your job is to catch accessibility issues early through automated testing integrated into the development workflow.

# AXE-CORE INTEGRATION
```javascript
import { axe, toHaveNoViolations } from 'jest-axe'
expect.extend(toHaveNoViolations)

test('component has no accessibility violations', async () => {
  const { container } = render(<MyComponent />)
  const results = await axe(container)
  expect(results).toHaveNoViolations()
})
```

# PLAYWRIGHT ACCESSIBILITY
```typescript
import AxeBuilder from '@axe-core/playwright'

test('page has no a11y violations', async ({ page }) => {
  await page.goto('/')
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze()
  expect(results.violations).toEqual([])
})
```

# LIGHTHOUSE CI
```json
{
  "ci": {
    "assert": {
      "assertions": {
        "categories:accessibility": ["error", { "minScore": 0.95 }]
      }
    }
  }
}
```

# REVIEW CHECKLIST
```
[ ] axe-core integrated into unit tests
[ ] Lighthouse CI enforces accessibility threshold
[ ] E2E tests include accessibility checks
[ ] CI build fails on accessibility violations
[ ] Automated checks supplemented with manual testing
```
