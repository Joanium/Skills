---
name: Code Splitting and Lazy Loading
trigger: code splitting, lazy loading, dynamic import, bundle splitting, route-based splitting, React.lazy, Suspense, webpack chunks, vite chunks, lazy components, prefetching, preloading, bundle size optimization, tree shaking, dynamic imports javascript
description: Reduce initial bundle size and time-to-interactive by splitting code at route, component, and library boundaries. Covers dynamic imports, React.lazy, Suspense, prefetching, and Vite/Webpack configuration.
---

# ROLE
You are a frontend performance engineer. You know that a 5MB JavaScript bundle shipped to every user is not a "we'll fix it later" issue — it is a decision that costs load time, CPU parse time, and user retention. Your job is to deliver only the code users need, when they need it.

# CORE CONCEPTS
```
BUNDLING:         All JS merged into one file → simple, but huge initial download
CODE SPLITTING:   Break bundle into chunks → load only what is needed now
LAZY LOADING:     Defer loading of non-critical code until it is actually needed
PREFETCHING:      Download future chunks during idle time (user has not navigated yet)
PRELOADING:       Download critical chunks for current route before they are needed
TREE SHAKING:     Remove unused exports at build time (import { only, what, you, use })
```

# DYNAMIC IMPORTS (The Foundation)

## Basic Syntax
```javascript
// Static import — loaded at module parse time (goes into main bundle)
import { heavyUtility } from './heavy';

// Dynamic import — loaded on demand (split into separate chunk)
const { heavyUtility } = await import('./heavy');

// Conditional loading
async function loadPolyfill() {
  if (!window.IntersectionObserver) {
    await import('intersection-observer');
  }
}

// Load on user action — keeps initial bundle lean
button.addEventListener('click', async () => {
  const { exportToPDF } = await import('./exporters/pdf');
  await exportToPDF(data);
});

// Named chunk (Vite/Webpack magic comment for bundle naming)
const { Chart } = await import(/* webpackChunkName: "charts" */ 'chart.js');
const MapboxGL = await import(/* vite-chunk: "map" */ 'mapbox-gl');
```

# REACT.LAZY AND SUSPENSE

## Route-Based Splitting (Most Impactful)
```tsx
import React, { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';

// Each route becomes its own chunk — users download only what they visit
const Home      = lazy(() => import('./pages/Home'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings  = lazy(() => import('./pages/Settings'));
const AdminPanel = lazy(() => import('./pages/AdminPanel'));  // heavy, rarely visited

function App() {
  return (
    <Suspense fallback={<PageLoadingSpinner />}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/admin" element={<AdminPanel />} />
      </Routes>
    </Suspense>
  );
}
```

## Component-Level Lazy Loading
```tsx
// Heavy components — modals, rich text editors, charts, maps
const RichTextEditor = lazy(() => import('./components/RichTextEditor'));
const MapView        = lazy(() => import('./components/MapView'));
const DataGrid       = lazy(() => import('./components/DataGrid'));

// Only loaded when rendered
function PostEditor({ isEditing }: { isEditing: boolean }) {
  if (!isEditing) return <PostPreview />;
  return (
    <Suspense fallback={<div className="skeleton-editor" />}>
      <RichTextEditor />
    </Suspense>
  );
}
```

## Error Boundary + Suspense Combo
```tsx
class ChunkErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div>
          Failed to load this section.{' '}
          <button onClick={() => this.setState({ hasError: false })}>Retry</button>
        </div>
      );
    }
    return this.props.children;
  }
}

// Wrap any lazy component
function SafeLazy({ component: LazyComponent, fallback, errorFallback, ...props }) {
  return (
    <ChunkErrorBoundary fallback={errorFallback}>
      <Suspense fallback={fallback ?? <Spinner />}>
        <LazyComponent {...props} />
      </Suspense>
    </ChunkErrorBoundary>
  );
}
```

# PREFETCHING AND PRELOADING

## Prefetch on Hover (Anticipate Navigation)
```tsx
import { useEffect } from 'react';

// Preload chunk when user hovers over a link
function PrefetchLink({ to, children, ...props }) {
  const handleMouseEnter = () => {
    // Trigger dynamic import to download chunk now
    // By the time user clicks, chunk is already in cache
    switch (to) {
      case '/dashboard': import('./pages/Dashboard'); break;
      case '/settings':  import('./pages/Settings');  break;
    }
  };

  return (
    <Link to={to} onMouseEnter={handleMouseEnter} {...props}>
      {children}
    </Link>
  );
}

// Generic prefetch hook
function usePrefetch(importFn: () => Promise<unknown>) {
  return () => { importFn(); };  // returns a trigger function
}

// Usage:
const prefetchDashboard = usePrefetch(() => import('./pages/Dashboard'));
<NavItem onMouseEnter={prefetchDashboard}>Dashboard</NavItem>
```

## Prefetch After Page Load (Idle Time)
```javascript
// Load non-critical chunks after page is interactive
if ('requestIdleCallback' in window) {
  requestIdleCallback(() => {
    import('./features/analytics');
    import('./features/helpCenter');
  }, { timeout: 3000 });
} else {
  setTimeout(() => {
    import('./features/analytics');
  }, 2000);
}
```

## Preload Critical Chunks in HTML Head
```html
<!-- Tell browser to fetch these chunks early (still parsed by browser, not blocking) -->
<link rel="preload" href="/assets/Dashboard-abc123.js" as="script">
<link rel="prefetch" href="/assets/Settings-def456.js">

<!-- preload:  high priority, current navigation needs it -->
<!-- prefetch: low priority, future navigation might need it -->
```

# VITE CONFIGURATION

## Manual Chunk Splitting
```typescript
// vite.config.ts
import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor libraries rarely change — split for long-term caching
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-ui':    ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
          'vendor-charts': ['recharts', 'd3'],
          'vendor-editor': ['@tiptap/core', '@tiptap/react'],
          'vendor-utils':  ['date-fns', 'lodash-es', 'zod']
        },

        // OR — dynamic chunk assignment function
        manualChunks(id) {
          if (id.includes('node_modules')) {
            // Group all node_modules into vendor chunk
            return 'vendor';
          }
          if (id.includes('/pages/admin/')) {
            return 'admin-bundle';
          }
        }
      }
    },

    // Warn when chunk exceeds this size
    chunkSizeWarningLimit: 500,  // KB
  }
});
```

## Analyze Your Bundle
```bash
# Install rollup-plugin-visualizer
npm install -D rollup-plugin-visualizer

# vite.config.ts:
import { visualizer } from 'rollup-plugin-visualizer';
plugins: [
  visualizer({ open: true, filename: 'stats.html', gzipSize: true })
]

# Run build — opens interactive treemap showing what is in each chunk
npm run build
```

# TREE SHAKING — WHAT KILLS IT

## Common Tree Shaking Failures
```javascript
// BAD — imports entire lodash (70KB+)
import _ from 'lodash';
const result = _.groupBy(items, 'category');

// GOOD — imports only groupBy (~3KB)
import groupBy from 'lodash-es/groupBy';
// OR with lodash-es (ESM build, fully tree-shakable):
import { groupBy } from 'lodash-es';

// BAD — side-effect imports defeat tree shaking
import 'some-library';  // library might add things to window, cannot be tree-shaken

// BAD — dynamic keys defeat tree shaking
import * as utils from './utils';
const fn = utils[dynamicKey]();  // bundler cannot know which exports are used

// GOOD — explicit named imports
import { formatDate, parseDate } from './utils';

// BAD — CommonJS modules (require) are not tree-shakable
const { something } = require('library');  // entire library included

// GOOD — ESM imports are tree-shakable
import { something } from 'library';
```

## Library-Specific Tree Shaking
```javascript
// Material UI — use path imports (or their built-in tree shaking)
import Button from '@mui/material/Button';       // good
import { Button } from '@mui/material';          // also fine with MUI v5+

// Ant Design — configure babel plugin
// .babelrc: ["import", { "libraryName": "antd", "style": true }]

// date-fns — all named imports are tree-shakable
import { format, parseISO, addDays } from 'date-fns';  // only these 3 included

// Lodash — use lodash-es for tree shaking
import { debounce, throttle } from 'lodash-es';
```

# LAZY LOADING IMAGES AND ASSETS
```html
<!-- Native lazy loading — defer offscreen images -->
<img src="hero.jpg" loading="lazy" alt="Hero image">

<!-- Do NOT lazy-load above-the-fold images — they are critical -->
<img src="logo.png" loading="eager" alt="Logo">
```

```tsx
// React component for lazy images with IntersectionObserver
function LazyImage({ src, alt, placeholder, ...props }) {
  const [loaded, setLoaded] = useState(false);
  const [inView, setInView] = useState(false);
  const imgRef = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setInView(true); observer.disconnect(); } },
      { rootMargin: '200px' }  // start loading 200px before entering viewport
    );
    if (imgRef.current) observer.observe(imgRef.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={imgRef} {...props}>
      {placeholder && !loaded && <img src={placeholder} alt="" aria-hidden />}
      {inView && (
        <img
          src={src}
          alt={alt}
          onLoad={() => setLoaded(true)}
          style={{ opacity: loaded ? 1 : 0, transition: 'opacity 0.3s' }}
        />
      )}
    </div>
  );
}
```

# MEASURING IMPACT
```bash
# Before and after bundle analysis
npx source-map-explorer dist/assets/*.js

# Web Vitals impact — lazy loading should improve:
# LCP  (Largest Contentful Paint)  — smaller initial bundle = faster parse
# TTI  (Time to Interactive)       — less JS to evaluate = interactive sooner
# TBT  (Total Blocking Time)       — less main thread blocking

# Check chunk loading in DevTools:
# Network tab → filter JS → see chunk names and sizes
# Coverage tab → see % of loaded JS actually executed
```

# ANTI-PATTERNS
```
X  Lazy loading tiny components (< 5KB) — network overhead defeats the gain
X  Lazy loading above-the-fold content — causes layout shift and flicker
X  No Suspense fallback — Suspense boundary required for every lazy component
X  Splitting into too many tiny chunks — HTTP/2 helps but 50 chunks is too many
X  Ignoring chunk loading failures — users on slow networks will hit these
X  Not prefetching likely-next chunks — users feel the delay on navigation
X  Importing entire libraries when you need one function
X  Forgetting to analyze bundle — you cannot optimize what you cannot measure

GOOD TARGETS FOR SPLITTING:
  Routes (most impactful)
  Admin/dashboard features (users who never visit admin never pay for that code)
  Rich text editors, map libraries, chart libraries (typically 200-500KB+)
  PDF/export functionality
  Authentication flows (loaded once, then never again)
  Feature flags behind which most users never go