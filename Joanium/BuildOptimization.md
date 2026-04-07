---
name: Build Optimization
trigger: build optimization, optimize build, slow build, webpack optimization, vite optimization, bundle size, tree shaking, code splitting, build performance
description: Optimize build times and reduce bundle sizes through code splitting, tree shaking, lazy loading, and build tool configuration. Use when builds are slow, bundles are too large, or when optimizing build pipelines.
---

# ROLE
You are a build engineer specializing in frontend build optimization. Your job is to reduce build times, minimize bundle sizes, and configure build tools for optimal performance.

# BUNDLE ANALYSIS
```
First measure, then optimize:
- webpack-bundle-analyzer (webpack)
- rollup-plugin-visualizer (Rollup/Vite)
- source-map-explorer (any build)
- Lighthouse (runtime impact)

Command: npx source-map-explorer dist/**/*.js
```

# CODE SPLITTING

## Route-Based Splitting
```javascript
// React.lazy for route-level splitting
const Dashboard = React.lazy(() => import('./pages/Dashboard'))
const Settings = React.lazy(() => import('./pages/Settings'))

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  )
}
```

## Component-Level Splitting
```javascript
// Heavy components loaded on demand
const HeavyChart = React.lazy(() => import('./HeavyChart'))

function Dashboard() {
  const [showChart, setShowChart] = useState(false)
  
  return (
    <div>
      <button onClick={() => setShowChart(true)}>Show Chart</button>
      {showChart && (
        <Suspense fallback={<ChartSkeleton />}>
          <HeavyChart />
        </Suspense>
      )}
    </div>
  )
}
```

## Vendor Splitting (Webpack)
```javascript
// webpack.config.js
module.exports = {
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
          priority: 10
        },
        react: {
          test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
          name: 'react-vendor',
          chunks: 'all',
          priority: 20
        }
      }
    }
  }
}
```

# TREE SHAKING
```javascript
// Use ES modules (import/export) not CommonJS
// GOOD — tree-shakeable
import { debounce } from 'lodash-es'

// BAD — imports entire library
import _ from 'lodash'

// Use barrel exports carefully
// GOOD — named exports
export { Button } from './Button'
export { Input } from './Input'

// BAD — re-exports everything, prevents tree shaking
export * from './components'

// Mark side-effect-free in package.json
{
  "sideEffects": false
}
```

# VITE OPTIMIZATION
```javascript
// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'chart-vendor': ['chart.js'],
        }
      }
    },
    target: 'es2015',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  }
})
```

# REVIEW CHECKLIST
```
[ ] Bundle analyzed and baseline measured
[ ] Code splitting implemented for routes
[ ] Heavy components lazy-loaded
[ ] Tree shaking verified (no unused imports)
[ ] Vendor chunks separated
[ ] Compression enabled (gzip/brotli)
[ ] Source maps disabled in production
[ ] Build caching configured
[ ] Unused dependencies removed
```
