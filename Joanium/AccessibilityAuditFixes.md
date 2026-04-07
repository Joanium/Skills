---
name: Accessibility Audit & Fixes
trigger: accessibility audit, wcag, a11y, screen reader, aria labels, keyboard navigation, color contrast, focus management, accessible form, alt text, accessibility issues, axe audit, lighthouse accessibility, accessible modal, skip link, accessible table
description: Audit web interfaces for accessibility issues and provide concrete fixes that meet WCAG 2.1 AA. Use this skill when the user shares HTML/JSX code for accessibility review, asks about ARIA usage, keyboard navigation, color contrast, screen reader support, or wants to make any UI component accessible. Goes beyond generic checklists — provides working code fixes.
---

# ROLE
You are a web accessibility specialist. You audit code against WCAG 2.1 AA, identify real barriers for users with disabilities, and provide working code fixes — not just checklist items.

# AUDIT PROCESS

When given code to audit:
1. **Perceivable** — can all users perceive the content? (images, color, audio)
2. **Operable** — can all users operate the UI? (keyboard, focus, timing)
3. **Understandable** — is the UI clear and predictable? (labels, errors, instructions)
4. **Robust** — does it work with assistive technology? (valid HTML, ARIA, roles)

# PERCEIVABLE

## Images and Non-Text Content
```html
<!-- Informative image: describe the content and function -->
<img src="revenue-chart.png" alt="Q3 2024 revenue: $2.4M, up 18% from Q2">

<!-- Decorative image: empty alt (screen reader skips it) -->
<img src="divider.png" alt="">

<!-- Icon button: label the function, not the icon -->
<!-- ❌ Bad: screen reader says "image, button" -->
<button><img src="trash.svg"></button>

<!-- ✓ Good: screen reader says "Delete item, button" -->
<button aria-label="Delete item">
  <img src="trash.svg" alt="">  <!-- empty alt — label is on button -->
</button>

<!-- SVG icon: hide from AT or label it -->
<svg aria-hidden="true" focusable="false">...</svg>  <!-- decorative -->
<svg role="img" aria-label="Warning"><title>Warning</title>...</svg>  <!-- informative -->
```

## Color and Contrast
```
WCAG AA minimums:
  Normal text (<18pt / <14pt bold): contrast ratio ≥ 4.5:1
  Large text (≥18pt / ≥14pt bold): contrast ratio ≥ 3:1
  UI components and focus indicators: contrast ratio ≥ 3:1

Tools:
  Browser: DevTools > Inspect element > contrast ratio shown in color picker
  Online: webaim.org/resources/contrastchecker
  VS Code: Colour Contrast Analyzer extension

Never convey information by color alone:
  ❌ <span style="color:red">Required field</span>
  ✓ <span>Required field <span aria-hidden="true">*</span></span>
    <!-- "required" conveyed via text AND marked in form field -->
```

# OPERABLE

## Keyboard Navigation
```html
<!-- All interactive elements must be keyboard-focusable and operable -->

<!-- ❌ Click handler on a div — keyboard users can't activate it -->
<div onclick="handleClick()">Click me</div>

<!-- ✓ Use semantic button — free keyboard support -->
<button onclick="handleClick()">Click me</button>

<!-- ✓ If you must use a div, add role + tabindex + keyboard handler -->
<div role="button" tabindex="0"
     onclick="handleClick()"
     onkeydown="e.key === 'Enter' || e.key === ' ' ? handleClick() : null">
  Click me
</div>

<!-- tabindex values:
  tabindex="0"   → in natural tab order
  tabindex="-1"  → focusable via JS (focus()), but not in tab order
  tabindex="1+"  → AVOID — breaks expected tab order for all users -->
```

## Focus Management
```javascript
// When content changes, move focus to make it discoverable

// Modal open: move focus to modal container or first focusable element
function openModal() {
  modal.removeAttribute('hidden');
  modal.setAttribute('aria-modal', 'true');
  // Move focus to modal
  const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
  firstFocusable?.focus();
}

// Modal close: return focus to the trigger
function closeModal(triggerEl) {
  modal.setAttribute('hidden', '');
  triggerEl.focus();  // return focus to what opened the modal
}

// Focus trap inside modal
modal.addEventListener('keydown', (e) => {
  if (e.key !== 'Tab') return;
  const focusableElements = modal.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  const first = focusableElements[0];
  const last = focusableElements[focusableElements.length - 1];

  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault();
    last.focus();
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault();
    first.focus();
  }
});
```

## Skip Links
```html
<!-- Always provide a skip link — first focusable element on the page -->
<a href="#main-content" class="skip-link">Skip to main content</a>

<nav><!-- navigation --></nav>
<main id="main-content" tabindex="-1"><!-- main content --></main>

<style>
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: #000;
  color: #fff;
  padding: 8px;
  z-index: 9999;
  text-decoration: none;
}
.skip-link:focus {
  top: 0;  /* visible when focused */
}
</style>
```

# UNDERSTANDABLE

## Forms — Labels and Errors
```html
<!-- ❌ Placeholder is NOT a label — disappears, low contrast, screen reader issues -->
<input type="email" placeholder="Email address">

<!-- ✓ Visible label associated with input -->
<label for="email">Email address</label>
<input type="email" id="email" name="email"
       required
       aria-describedby="email-error email-hint">
<p id="email-hint">We'll send a confirmation link here.</p>
<p id="email-error" role="alert" aria-live="polite">
  <!-- dynamically populated on error -->
</p>

<!-- Error state -->
<input type="email" id="email"
       aria-invalid="true"
       aria-describedby="email-error">
<p id="email-error" role="alert">
  Please enter a valid email address.
</p>

<!-- Fieldset for grouped controls -->
<fieldset>
  <legend>Notification preferences</legend>
  <label><input type="checkbox" name="email"> Email</label>
  <label><input type="checkbox" name="sms"> SMS</label>
</fieldset>
```

## Live Regions — Dynamic Content
```html
<!-- Announce dynamic changes to screen readers -->

<!-- Polite: wait for user to finish what they're doing -->
<div aria-live="polite" aria-atomic="true">
  <!-- Status messages, search results count, filter results -->
  3 results found
</div>

<!-- Assertive: interrupt immediately (use sparingly) -->
<div role="alert" aria-live="assertive">
  <!-- Error messages, important warnings -->
</div>

<!-- Status role: "3 items added to cart" (implied aria-live="polite") -->
<div role="status">Item added to cart</div>
```

# ROBUST

## Accessible Modal (Complete Example)
```html
<button id="open-modal" onclick="openModal()">Open settings</button>

<div id="modal" 
     role="dialog" 
     aria-modal="true" 
     aria-labelledby="modal-title"
     aria-describedby="modal-description"
     hidden>
  <h2 id="modal-title">Account Settings</h2>
  <p id="modal-description">Update your profile information below.</p>
  
  <form>
    <label for="name">Display name</label>
    <input type="text" id="name" name="name">
    
    <button type="submit">Save changes</button>
    <button type="button" onclick="closeModal()">Cancel</button>
  </form>
</div>

<div id="modal-overlay" hidden onclick="closeModal()"></div>
```

## Accessible Data Table
```html
<table>
  <caption>Q3 2024 Sales by Region</caption>  <!-- table label -->
  <thead>
    <tr>
      <th scope="col">Region</th>       <!-- scope="col" or "row" -->
      <th scope="col">Revenue</th>
      <th scope="col">Change</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">North America</th>  <!-- row header -->
      <td>$1.2M</td>
      <td>
        <span aria-label="Up 12%">↑ 12%</span>  <!-- icon + text -->
      </td>
    </tr>
  </tbody>
</table>
```

## Accessible Disclosure / Accordion
```html
<button 
  aria-expanded="false" 
  aria-controls="faq-1-content"
  onclick="toggleSection(this)">
  What is your return policy?
</button>
<div id="faq-1-content" hidden>
  <p>You can return items within 30 days...</p>
</div>

<script>
function toggleSection(btn) {
  const expanded = btn.getAttribute('aria-expanded') === 'true';
  btn.setAttribute('aria-expanded', !expanded);
  const content = document.getElementById(btn.getAttribute('aria-controls'));
  content.hidden = expanded;
}
</script>
```

# AUTOMATED TESTING

```bash
# axe-core — best automated scanner (catches ~40% of issues)
npm install --save-dev @axe-core/playwright

# playwright test
import { checkA11y, injectAxe } from 'axe-playwright';

test('home page is accessible', async ({ page }) => {
  await page.goto('/');
  await injectAxe(page);
  await checkA11y(page, null, {
    detailedReport: true,
    detailedReportOptions: { html: true },
  });
});
```

# COMMON VIOLATIONS QUICK-FIX TABLE

```
Issue                     Fix
─────────────────────────────────────────────────────────────
Missing alt text          Add descriptive alt, or alt="" for decorative
Low contrast              Adjust color — use contrast checker tool
Missing label             <label for="id"> or aria-label or aria-labelledby
Click handler on div      Change to <button> or add role/tabindex/keyboard handler
Modal not trapping focus  Add focus trap (see code above)
aria-hidden on focusable  Remove aria-hidden or remove from tab order (tabindex="-1")
Missing form error link   aria-describedby pointing to error message element
Icon-only button          aria-label="action description" on button
Table missing headers     Add <th scope="col/row"> and <caption>
No skip link              Add <a href="#main"> as first focusable element
```
