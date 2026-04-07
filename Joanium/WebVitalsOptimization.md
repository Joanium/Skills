---
name: Web Vitals Optimization
trigger: core web vitals, LCP, CLS, INP, FID, performance score, lighthouse score, slow page, improve web vitals, page speed, time to interactive, cumulative layout shift, largest contentful paint
description: Diagnose and fix Core Web Vitals (LCP, INP, CLS) to hit green scores in Lighthouse and CrUX. Use this skill whenever the user mentions sluggish page loads, poor Lighthouse scores, layout shifts, input lag, or wants to improve any performance metric measured by Google. Covers measurement, root-cause analysis, and concrete code fixes.
---

# ROLE
You are a web performance engineer. Your job is to diagnose Core Web Vitals failures, find their root cause, and prescribe surgical fixes — not generic advice.

# THE THREE METRICS THAT MATTER (2024+)

```
LCP  Largest Contentful Paint   → loading speed    target: < 2.5s
INP  Interaction to Next Paint  → responsiveness   target: < 200ms
CLS  Cumulative Layout Shift     → visual stability target: < 0.1

(FID is retired — INP replaced it March 2024)
```

# STEP 1 — MEASURE FIRST, FIX SECOND

## Tools
```
Field data (real users):
  Chrome User Experience Report (CrUX) — search.google.com/search-console
  PageSpeed Insights → pagespeed.web.dev (shows both lab + field)

Lab data (reproducible):
  Lighthouse  → DevTools > Lighthouse tab (throttled mobile)
  WebPageTest → webpagetest.org (multi-location, filmstrip)
  web-vitals JS library → measure in production

# Install web-vitals to measure real user data
npm install web-vitals

import { onLCP, onINP, onCLS } from 'web-vitals';
onLCP(console.log);
onINP(console.log);
onCLS(console.log);
```

# LCP — LARGEST CONTENTFUL PAINT

## Common Causes & Fixes

### 1. Render-blocking resources
```html
<!-- BAD: blocks parser -->
<link rel="stylesheet" href="/big.css">
<script src="/analytics.js"></script>

<!-- GOOD: preload LCP image, defer non-critical scripts -->
<link rel="preload" as="image" href="/hero.webp" fetchpriority="high">
<link rel="stylesheet" href="/critical.css">          <!-- inline critical CSS instead -->
<script src="/analytics.js" defer></script>
```

### 2. LCP image not prioritized
```html
<!-- Hero image above fold — NEVER lazy-load it -->
<img src="/hero.webp" 
     fetchpriority="high"    <!-- signals browser: load me first -->
     loading="eager"         <!-- NOT lazy -->
     decoding="async"
     width="1200" height="600"
     alt="Hero">

<!-- All other images below fold -->
<img src="/card.webp" loading="lazy" decoding="async" width="400" height="300">
```

### 3. Slow server / no CDN
```
Target: TTFB < 800ms
- Use a CDN for static assets (Cloudflare, Fastly, CloudFront)
- Enable HTTP/2 or HTTP/3
- Cache HTML at edge with stale-while-revalidate

Cache-Control: public, max-age=0, stale-while-revalidate=86400
```

### 4. Unoptimized images
```bash
# Convert to WebP/AVIF, resize to actual display size
npx sharp-cli --input hero.jpg --output hero.webp --format webp --quality 80
npx sharp-cli --input hero.jpg --output hero.avif --format avif --quality 65

# Always serve responsive images
<picture>
  <source srcset="/hero.avif" type="image/avif">
  <source srcset="/hero.webp" type="image/webp">
  <img src="/hero.jpg" width="1200" height="600" fetchpriority="high" alt="Hero">
</picture>
```

# INP — INTERACTION TO NEXT PAINT

## Diagnosing Long Tasks
```javascript
// Find long tasks in DevTools Performance tab
// Or use PerformanceObserver
new PerformanceObserver((list) => {
  list.getEntries().forEach(entry => {
    if (entry.duration > 50) {
      console.warn('Long task:', entry.duration, entry.name);
    }
  });
}).observe({ type: 'longtask', buffered: true });
```

## Fixes

### 1. Break up long synchronous work
```javascript
// BAD: blocks main thread
function processItems(items) {
  items.forEach(item => heavyWork(item)); // 500ms of work
}

// GOOD: yield to browser between chunks
async function processItems(items) {
  for (let i = 0; i < items.length; i++) {
    heavyWork(items[i]);
    if (i % 50 === 0) {
      await scheduler.yield();  // or: await new Promise(r => setTimeout(r, 0))
    }
  }
}
```

### 2. Move work off main thread
```javascript
// Web Worker for CPU-heavy tasks
const worker = new Worker('/heavy-worker.js');
worker.postMessage({ data: largeDataset });
worker.onmessage = (e) => updateUI(e.data);

// heavy-worker.js
self.onmessage = (e) => {
  const result = heavyComputation(e.data.data);
  self.postMessage(result);
};
```

### 3. Debounce/throttle event handlers
```javascript
// BAD: recalculates on every keystroke
input.addEventListener('input', expensiveSearch);

// GOOD: wait for user to stop typing
import { debounce } from 'lodash-es';
input.addEventListener('input', debounce(expensiveSearch, 300));
```

# CLS — CUMULATIVE LAYOUT SHIFT

## Root Causes & Fixes

### 1. Images without dimensions (most common)
```html
<!-- BAD: browser doesn't know size until image loads → layout shift -->
<img src="/photo.jpg" alt="...">

<!-- GOOD: reserve space with width/height or aspect-ratio -->
<img src="/photo.jpg" width="800" height="600" alt="...">

/* Or with CSS */
img { aspect-ratio: 4/3; width: 100%; }
```

### 2. Dynamic content injection above existing content
```javascript
// BAD: banner appears and pushes content down
document.body.prepend(cookieBanner);

// GOOD: reserve space in layout, fill it in
// HTML: <div id="banner-slot" style="min-height: 60px"></div>
document.getElementById('banner-slot').replaceWith(cookieBanner);
```

### 3. Web fonts causing FOUT/FOIT
```css
/* Prevent invisible text flash */
@font-face {
  font-family: 'MyFont';
  src: url('/font.woff2') format('woff2');
  font-display: optional;  /* or 'swap' — no invisible text */
}

/* Preload critical fonts */
/* <link rel="preload" as="font" href="/font.woff2" crossorigin> */
```

### 4. Animations that trigger layout
```css
/* BAD: animating properties that cause reflow */
.box { transition: width 0.3s, height 0.3s, top 0.3s; }

/* GOOD: animate only transform and opacity (compositor-only) */
.box { transition: transform 0.3s, opacity 0.3s; }
.box.expanded { transform: scale(1.2); }
```

# QUICK WINS CHECKLIST
```
LCP:
[ ] Hero image has fetchpriority="high" and no lazy loading
[ ] Critical CSS inlined, rest deferred
[ ] Images served as WebP/AVIF at correct size
[ ] TTFB < 800ms (CDN + caching)
[ ] No render-blocking scripts above fold

INP:
[ ] No synchronous tasks > 50ms in event handlers
[ ] Heavy computation moved to Web Workers
[ ] Input handlers debounced
[ ] React: avoid re-rendering entire tree on input

CLS:
[ ] All images have explicit width + height attributes
[ ] Fonts use font-display: swap or optional
[ ] No content injected above the fold after load
[ ] Animations use transform/opacity only
[ ] Skeleton screens instead of content jumping in
```
