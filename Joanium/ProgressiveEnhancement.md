---
name: Progressive Enhancement
trigger: progressive enhancement, graceful degradation, works without JavaScript, resilient web, baseline HTML, server-side rendering fallback, no-JS fallback, enhance progressively, web fundamentals, HTML first, core functionality without JS
description: Build resilient web applications using progressive enhancement. Covers HTML-first architecture, layered JavaScript enhancement, CSS feature queries, performance budgets, and testing strategies.
---

# ROLE
You are a senior front-end architect. Progressive enhancement is not about supporting ancient browsers — it's about building resilient systems that deliver core value under any conditions, then enhance with capabilities when available.

# THE PRINCIPLE
```
PROGRESSIVE ENHANCEMENT LAYERS:
  Layer 1: CONTENT    → HTML structure — works in any browser, screen reader, bot
  Layer 2: PRESENTATION → CSS — enhances visual experience, degrades if unavailable
  Layer 3: BEHAVIOR   → JavaScript — adds interactivity, not required for core value

WRONG WAY TO THINK ABOUT IT:
  "Support old browsers" → defensive, limiting mindset
  "Start with JS, make it accessible as an afterthought" → backwards

RIGHT WAY:
  "What is the core value this feature delivers?"
  "Can a user get that value with just HTML and a form POST?"
  "Now layer JS on top to make it better, not to make it work at all."

PRACTICAL IMPACT:
  → Works when JS fails (CDN down, parsing error, extension blocking)
  → Works on slow connections before JS has loaded
  → Works for screen readers, search bots, RSS readers
  → Works in environments that don't run JS (email, some apps)
  → Naturally more performant baseline
```

# HTML FIRST

## Forms That Work Without JS
```html
<!-- BAD: Form that only works with JS -->
<div class="signup-form">
  <input id="email" type="text">
  <button onclick="handleSubmit()">Subscribe</button>
</div>

<!-- GOOD: Real HTML form — works without JS, enhanced with JS -->
<form
  method="POST"
  action="/api/subscribe"
  id="subscribe-form"
  novalidate    <!-- we'll handle validation in JS; browser handles fallback -->
>
  <label for="email">Email address</label>
  <input
    id="email"
    name="email"
    type="email"
    required
    autocomplete="email"
    aria-describedby="email-hint"
  >
  <p id="email-hint">We'll never share your email.</p>

  <button type="submit">Subscribe</button>
</form>

<!-- JS enhancement: intercept submit for better UX -->
<script>
  const form = document.getElementById('subscribe-form');

  // Only enhance if JS is available
  form?.addEventListener('submit', async (e) => {
    e.preventDefault();  // only prevent default when we can handle it ourselves

    const formData = new FormData(form);
    const button = form.querySelector('button');

    try {
      button.disabled = true;
      button.textContent = 'Subscribing...';

      const response = await fetch(form.action, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        showSuccessMessage();
      } else {
        form.submit();  // fallback to native form submit on API error
      }
    } catch {
      form.submit();  // network error: fall through to native POST
    }
  });
</script>
```

## Navigation That Works Without JS
```html
<!-- Disclosure widget — works as linked sections without JS -->
<nav>
  <ul>
    <li>
      <!-- Works as a link to #products without JS -->
      <a href="#products" id="products-toggle">Products</a>

      <ul id="products" class="submenu">
        <li><a href="/products/widget">Widget</a></li>
        <li><a href="/products/gadget">Gadget</a></li>
      </ul>
    </li>
  </ul>
</nav>

<!-- CSS makes it look like a dropdown without JS -->
<style>
  .submenu { display: none; }
  /* Show when parent link is focused or when JS adds aria-expanded -->
  a[aria-expanded="true"] + .submenu,
  a:focus + .submenu { display: block; }
  /* :target fallback for no-JS */
  :target { display: block !important; }
</style>

<script>
  /* Enhance navigation to proper ARIA dropdown */
  document.querySelectorAll('nav a[href^="#"]').forEach(toggle => {
    const target = document.querySelector(toggle.getAttribute('href'));
    if (!target) return;

    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-haspopup', 'true');

    toggle.addEventListener('click', (e) => {
      e.preventDefault();
      const expanded = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!expanded));
    });
  });
</script>
```

# CSS PROGRESSIVE ENHANCEMENT

## Feature Queries
```css
/* Baseline: all browsers */
.card-grid {
  display: block;  /* stack vertically */
}

.card {
  margin-bottom: 1rem;
}

/* Enhance with flexbox where supported */
@supports (display: flex) {
  .card-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .card {
    flex: 1 1 280px;
    margin-bottom: 0;  /* gap handles spacing now */
  }
}

/* Enhance further with grid where supported */
@supports (display: grid) {
  .card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1rem;
  }
}

/* Container queries for truly responsive components */
@supports (container-type: inline-size) {
  .card-container {
    container-type: inline-size;
  }

  @container (min-width: 400px) {
    .card { flex-direction: row; }
  }
}
```

## Has Selector with Fallback
```css
/* Baseline: always show the label */
.field-label { display: block; }

/* Enhance: float label when input has value */
@supports selector(:has(input:not(:placeholder-shown))) {
  .field-label {
    transition: transform 0.2s, font-size 0.2s;
  }

  .field:has(input:not(:placeholder-shown)) .field-label {
    transform: translateY(-100%);
    font-size: 0.75em;
  }
}
```

# JAVASCRIPT ENHANCEMENT PATTERNS

## Feature Detection (Not Browser Detection)
```javascript
// BAD: browser sniffing
if (navigator.userAgent.includes('Chrome')) { useNewAPI(); }

// GOOD: feature detection
if ('IntersectionObserver' in window) {
  setupLazyLoading();
} else {
  // Eager load everything — less optimal but works
  document.querySelectorAll('img[data-src]').forEach(img => {
    img.src = img.dataset.src;
  });
}

// Pattern for optional enhancement:
function enhance(feature, implementation, fallback = () => {}) {
  if (feature in window || feature in document) {
    implementation();
  } else {
    fallback();
  }
}

enhance('ResizeObserver', () => {
  new ResizeObserver(handleResize).observe(container);
}, () => {
  window.addEventListener('resize', debounce(handleResize, 100));
});
```

## Cutting the Mustard (Baseline Check)
```javascript
// Establish a baseline of capabilities your enhancement requires
// Everything below this line is enhancement — not core functionality

const supportsModernFeatures = (
  'querySelector' in document &&
  'addEventListener' in window &&
  'fetch' in window &&
  'Promise' in window
);

if (supportsModernFeatures) {
  // Safe to load and execute enhancement code
  import('./enhanced-features.js')
    .then(({ initEnhancements }) => initEnhancements())
    .catch(() => {
      // Enhancement failed to load — core HTML still works
      console.warn('Enhancement failed to load');
    });
}
// If mustard not cut: user gets HTML-only experience — still functional
```

## Non-Blocking Script Loading
```html
<!-- Bad: blocks rendering while downloading and executing -->
<script src="app.js"></script>

<!-- Better: downloads in parallel, executes after HTML parsed -->
<script defer src="app.js"></script>

<!-- Best for independent modules: download and execute ASAP, non-blocking -->
<script type="module" src="app.js"></script>
<!-- module scripts are deferred by default -->

<!-- Async: download in parallel, execute immediately when ready (use for analytics) -->
<script async src="analytics.js"></script>

<!-- Inline critical, defer non-critical -->
<script>
  // Tiny inline script for immediate critical enhancement
  document.documentElement.classList.add('js');
</script>
<link rel="stylesheet" href="styles.css">
<script defer src="non-critical-enhancement.js"></script>
```

# SERVER-SIDE RENDERING + ENHANCEMENT

## Islands Architecture
```
CONCEPT: Server renders full HTML for initial load.
         "Islands" of interactivity are hydrated selectively.
         Most of the page is static HTML — zero JS needed.

                 ┌────────────────────────────────────┐
                 │  Static HTML (no JS, fast)         │
                 │  ┌────────────┐  ┌──────────────┐  │
                 │  │ 🏝 Island  │  │ 🏝 Island    │  │
                 │  │ Search     │  │ Cart (React) │  │
                 │  │ (JS)       │  │              │  │
                 │  └────────────┘  └──────────────┘  │
                 └────────────────────────────────────┘

FRAMEWORKS: Astro (best), Eleventy + Alpine.js, Qwik, Fresh (Deno)

Astro example:
```

```astro
---
// ProductPage.astro — rendered to static HTML on server
import Cart from './Cart.jsx';   // interactive island
import SearchBar from './SearchBar.jsx';  // interactive island

const product = await fetchProduct(Astro.params.id);
---

<html>
  <body>
    <!-- Static content — zero JS shipped -->
    <h1>{product.name}</h1>
    <p>{product.description}</p>
    <img src={product.image} alt={product.name}>

    <!-- Interactive islands — JS only for these components -->
    <SearchBar client:idle />           <!-- hydrate when browser is idle -->
    <Cart productId={product.id} client:visible />  <!-- hydrate when visible -->
  </body>
</html>
```

# TESTING PROGRESSIVE ENHANCEMENT

## Test Without JavaScript
```javascript
// Playwright — disable JS and verify core function still works
import { test, expect } from '@playwright/test';

test('subscribe form works without JavaScript', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();

  await page.goto('/subscribe');

  // Fill and submit form — must work via native HTML POST
  await page.fill('input[type="email"]', 'test@example.com');
  await page.click('button[type="submit"]');

  // Should redirect to success page (server-side response)
  await expect(page).toHaveURL('/subscribe/success');
  await expect(page.locator('h1')).toContainText('Subscribed!');
});

test('subscribe form enhances with JavaScript', async ({ page }) => {
  await page.goto('/subscribe');

  await page.fill('input[type="email"]', 'test@example.com');
  await page.click('button[type="submit"]');

  // JS version shows inline success message (no page reload)
  await expect(page.locator('.success-message')).toBeVisible();
  await expect(page).toHaveURL('/subscribe');  // URL didn't change
});
```

## Throttled Network Testing
```javascript
// Test the experience on slow connections (JS not yet loaded)
test('page is usable before JavaScript loads', async ({ page, context }) => {
  // Simulate 3G connection
  await context.route('**/*.js', route => route.abort());  // block all JS

  await page.goto('/');

  // Core content must be visible immediately
  await expect(page.locator('h1')).toBeVisible();
  await expect(page.locator('nav')).toBeVisible();

  // Forms must be submittable
  const form = page.locator('form');
  await expect(form).toHaveAttribute('method');
  await expect(form).toHaveAttribute('action');
});
```

# PERFORMANCE BUDGET
```
PROGRESSIVE ENHANCEMENT = PERFORMANCE BY DEFAULT

HTML budget:       < 14KB first response (fits in one TCP window, no JS needed)
CSS budget:        < 50KB total, < 15KB critical path (inline in <style>)
JS budget:         0KB for core functionality
                   < 100KB for enhancement (compressed)
                   < 300KB total JS (all enhancements combined)

MEASUREMENT:
  WebPageTest: "Start render" should be < 1.5s on 3G
  Lighthouse: TTI (Time to Interactive) < 5s on mobile
  Core Web Vitals: LCP < 2.5s, INP < 200ms, CLS < 0.1

If your HTML-only experience fails at the network budget → your HTML is too heavy.
If your page is non-functional without JS → you skipped Layer 1.
```

# CHECKLIST
```
HTML LAYER:
  [ ] All forms have action + method attributes (work without JS)
  [ ] Navigation works as links (not JS onclick)
  [ ] Images have alt text
  [ ] Semantic elements used (button, nav, main, article, etc.)
  [ ] Content is readable without CSS

CSS LAYER:
  [ ] @supports used for modern CSS features
  [ ] Flexbox/Grid have block layout fallback
  [ ] Font loading doesn't block text rendering (font-display: swap)

JS LAYER:
  [ ] Scripts are defer or type="module"
  [ ] Feature detection used (not browser detection)
  [ ] Graceful failure: catch blocks fall back to native behavior
  [ ] Core user journeys tested with JS disabled
  [ ] No event listeners on elements that don't have native semantics without them
```
