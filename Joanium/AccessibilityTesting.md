---
name: Accessibility Testing
trigger: accessibility testing, a11y testing, wcag audit, screen reader testing, axe, lighthouse accessibility, aria testing, keyboard navigation testing, color contrast testing, accessibility audit, a11y audit, accessibility compliance, wcag 2.1, wcag 2.2
description: Audit and fix web accessibility issues. Covers WCAG 2.2 compliance, automated testing with axe/Lighthouse, manual screen reader testing, keyboard navigation, color contrast, ARIA patterns, and accessible component checklists.
---

# ROLE
You are an accessibility engineer who makes digital products usable by everyone. You know WCAG guidelines by heart, can navigate a screen reader in the dark, and understand that accessibility is a spectrum — not a binary pass/fail. You catch issues before users do.

# WCAG 2.2 CONFORMANCE LEVELS
```
A   — minimum accessibility (must have)
AA  — standard for most legal requirements (target this)
AAA — enhanced accessibility (aspirational, context-dependent)

Four principles (POUR):
  Perceivable   — info presented in ways users can perceive
  Operable      — UI components operable by keyboard and assistive tech
  Understandable — info and UI operation is understandable
  Robust        — interpreted reliably by assistive technologies
```

# TESTING STRATEGY — USE ALL THREE LAYERS
```
1. Automated testing  → catches 30-40% of issues, fast, runs in CI
2. Manual testing     → catches issues automated tools miss
3. User testing       → catches usability gaps automated/manual miss
```

# AUTOMATED TESTING
## axe-core (Best Tool)
```javascript
// Playwright + axe — run in CI on every PR
import { test, expect } from '@playwright/test';
import { checkA11y, injectAxe } from 'axe-playwright';

test('homepage has no accessibility violations', async ({ page }) => {
    await page.goto('/');
    await injectAxe(page);
    
    await checkA11y(page, null, {
        detailedReport: true,
        detailedReportOptions: { html: true },
        runOnly: {
            type: 'tag',
            values: ['wcag2a', 'wcag2aa', 'wcag22aa']   // target AA
        }
    });
});

// Test interactive states — automated tools miss hidden content
test('modal dialog is accessible', async ({ page }) => {
    await page.goto('/');
    await page.click('[data-testid="open-modal"]');
    await page.waitForSelector('[role="dialog"]');
    
    await injectAxe(page);
    await checkA11y(page, '[role="dialog"]');   // scope to modal
});

// React: jest-axe for component-level testing
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);

it('Button has no accessibility violations', async () => {
    const { container } = render(<Button>Click me</Button>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
});
```

## Lighthouse CI
```yaml
# .github/workflows/a11y.yml
- name: Run Lighthouse CI
  run: |
    npm install -g @lhci/cli
    lhci autorun
  env:
    LHCI_GITHUB_APP_TOKEN: ${{ secrets.LHCI_GITHUB_APP_TOKEN }}

# lighthouserc.js
module.exports = {
  assert: {
    assertions: {
      'categories:accessibility': ['error', { minScore: 0.95 }]   // fail below 95
    }
  }
};
```

# KEYBOARD NAVIGATION TESTING
```
Test this manually — automated tools cannot reliably test keyboard UX.

Tab order test:
  1. Start at top of page
  2. Tab through every interactive element
  3. Verify focus goes in logical visual order (top to bottom, left to right)
  4. Every interactive element must receive focus
  5. Focus indicator must be visible (not outline: none without replacement)

Keyboard interactions by element:
  Links/Buttons:  Enter to activate; Space to activate buttons
  Dropdowns:      Enter to open; Arrow keys to navigate; Escape to close
  Modals:         Focus traps inside modal; Escape closes; focus returns to trigger
  Date pickers:   Arrow keys navigate dates; Page Up/Down for months
  Checkboxes:     Space to toggle
  Radio groups:   Arrow keys navigate between options
  Sliders:        Arrow keys change value; Home/End for min/max
  Tabs:           Arrow keys switch tabs; Tab moves into tab panel

Focus trap in modals:
```

```javascript
// Trap focus inside a modal — required for WCAG 2.1 Success Criterion 2.1.2
function trapFocus(element) {
    const focusableElements = element.querySelectorAll(
        'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
    );
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];
    
    element.addEventListener('keydown', (e) => {
        if (e.key !== 'Tab') return;
        
        if (e.shiftKey) {
            if (document.activeElement === firstFocusable) {
                e.preventDefault();
                lastFocusable.focus();
            }
        } else {
            if (document.activeElement === lastFocusable) {
                e.preventDefault();
                firstFocusable.focus();
            }
        }
    });
    
    firstFocusable.focus();   // move focus into modal on open
}
```

# SCREEN READER TESTING
```
Test with:
  macOS/iOS:   VoiceOver (built-in) — Cmd+F5 to enable
  Windows:     NVDA (free) or JAWS (most common enterprise)
  Android:     TalkBack (built-in)
  
  Test combinations: VoiceOver + Safari, NVDA + Chrome/Firefox, JAWS + Chrome

Key screen reader shortcuts (VoiceOver):
  VO = Ctrl+Option
  VO+A                → read all
  VO+H                → list all headings (navigation landmark)
  VO+U                → rotor (web navigation menu)
  Tab / VO+Right      → next interactive element
  VO+Space            → activate element

What to verify:
  [ ] Page title is descriptive and unique per page
  [ ] Heading hierarchy is logical (h1 → h2 → h3, no skipping)
  [ ] All images have meaningful alt text (or alt="" for decorative)
  [ ] Form inputs have associated labels (not just placeholder text)
  [ ] Error messages announce to screen reader (aria-live or focus on error)
  [ ] Dynamic content updates announced (aria-live regions)
  [ ] Icons/SVGs have accessible names (aria-label or visually-hidden text)
  [ ] Tables have headers (th with scope)
  [ ] Links have descriptive text (not "click here" or "read more")
```

# ARIA PATTERNS — USE CORRECTLY
```html
<!-- Only add ARIA when semantic HTML isn't sufficient -->
<!-- First, try native HTML: -->
<button> instead of <div role="button">
<nav>   instead of <div role="navigation">
<main>  instead of <div role="main">

<!-- aria-label — accessible name when visible label is absent -->
<button aria-label="Close dialog">✕</button>
<input type="search" aria-label="Search products">

<!-- aria-labelledby — reference visible label element -->
<h2 id="section-title">Recent Orders</h2>
<table aria-labelledby="section-title">...</table>

<!-- aria-describedby — additional description -->
<input type="password" 
       id="password" 
       aria-describedby="password-hint">
<span id="password-hint">Must be at least 8 characters</span>

<!-- aria-live — announce dynamic content changes -->
<div role="status" aria-live="polite">     <!-- non-urgent: "3 results found" -->
<div role="alert"  aria-live="assertive"> <!-- urgent: error messages -->

<!-- aria-expanded — for toggles and accordions -->
<button aria-expanded="false" aria-controls="menu">Menu</button>
<ul id="menu" hidden>...</ul>

<!-- aria-current — current item in navigation -->
<nav><ul>
  <li><a href="/home" aria-current="page">Home</a></li>
  <li><a href="/about">About</a></li>
</ul></nav>

<!-- Common ARIA mistakes: -->
<!-- ✗ role="button" on a <div> without tabindex="0" and keyboard handler -->
<!-- ✗ aria-label on a non-interactive element -->
<!-- ✗ Hiding content with visibility: hidden but keeping it in DOM for AT -->
<!-- ✗ Using aria-hidden="true" on focusable elements -->
```

# COLOR & VISUAL
```
Color contrast ratios (WCAG AA):
  Normal text (< 18pt):   4.5:1 minimum
  Large text (>= 18pt):   3:1 minimum
  UI components/borders:  3:1 minimum

Check contrast:
  Browser: Colour Contrast Analyser, Chrome DevTools → Rendering → Emulate vision
  Code: npm install color-contrast  
  Design: Figma plugins — Stark, Contrast

Don't rely on color alone:
  ✗ Red = error, green = success (colorblind users miss this)
  ✓ Error icon + red text + error message text
  ✓ Required fields: asterisk + "Required" label, not just red border

Focus indicators:
  Do NOT use: outline: none; or outline: 0; without replacement
  
  Replacement that meets WCAG 2.2 (3:1 contrast + 2px area):
    :focus-visible {
        outline: 3px solid #0066CC;
        outline-offset: 2px;
        border-radius: 2px;
    }

Motion/animation:
  @media (prefers-reduced-motion: reduce) {
      * { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
  }
```

# FORM ACCESSIBILITY PATTERNS
```html
<!-- Every input needs a label — placeholder is NOT a label -->
<div>
    <label for="email">Email address <span aria-hidden="true">*</span>
        <span class="sr-only">(required)</span>
    </label>
    <input type="email" 
           id="email" 
           name="email" 
           required
           aria-required="true"
           autocomplete="email"
           aria-describedby="email-error">
    <span id="email-error" role="alert" aria-live="polite">
        <!-- Error injected here when validation fails -->
    </span>
</div>

<!-- Error announcement pattern -->
// On submit, focus on first error:
document.querySelector('[aria-invalid="true"]').focus();

// Or announce errors via live region:
document.getElementById('form-errors').textContent = 
    'Please fix 2 errors: Email is invalid, Password is required';
```

# ACCESSIBILITY AUDIT CHECKLIST
```
Structure:
[ ] Single <h1> per page, logical heading hierarchy (no skipping)
[ ] Landmark regions: header, nav, main, footer
[ ] Skip navigation link at top of page
[ ] Page title is unique and descriptive per page

Interactive elements:
[ ] All interactive elements reachable by keyboard
[ ] Focus indicator visible on all focusable elements (not hidden)
[ ] Tab order is logical
[ ] Modals trap focus; focus returns to trigger on close
[ ] No keyboard traps (other than intentional modal traps)

Forms:
[ ] All inputs have associated <label> (not just placeholder)
[ ] Error messages programmatically associated (aria-describedby)
[ ] Required fields indicated (not color only)
[ ] Error state exposed to AT (aria-invalid="true")
[ ] Autocomplete attributes on personal data fields

Images & Media:
[ ] Meaningful images have descriptive alt text
[ ] Decorative images have alt=""
[ ] Complex images (charts) have text alternative
[ ] Videos have captions; audio has transcript

Color & Visual:
[ ] Text contrast >= 4.5:1 (normal), 3:1 (large)
[ ] UI component contrast >= 3:1
[ ] Color not the sole means of conveying information
[ ] prefers-reduced-motion respected

Dynamic content:
[ ] aria-live regions announce dynamic updates
[ ] Loading states announced to screen reader
[ ] Toast/notification messages announced
```
