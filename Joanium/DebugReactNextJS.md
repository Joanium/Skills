---
name: Debug — React / Next.js
trigger: react bug, next.js error, component not rendering, hydration error, useEffect loop, state not updating, re-render, props undefined, next.js 500, getServerSideProps error, app router, server component, client component, react crash
description: Hyper-specific debugging guide for React and Next.js. Real error messages, real causes, real fixes. Covers hooks errors, hydration mismatches, rendering bugs, Next.js App Router vs Pages Router, SSR/SSG issues, and performance.
---

# Debug — React / Next.js

## First Move

```bash
# Check browser console FIRST — React error messages are detailed
# Also check the terminal — Next.js server errors appear there

# Clear Next.js cache (fixes many mysterious build/runtime issues)
rm -rf .next
npm run dev

# Check Next.js version — App Router vs Pages Router behavior differs
cat package.json | grep '"next"'

# Build to catch errors that only appear in production
npm run build 2>&1 | less

# Analyze bundle size
npm run build -- --analyze  # with @next/bundle-analyzer configured
```

---

## React Hooks Errors

### `Rendered more hooks than during the previous render` / `Rendered fewer hooks`

Hooks must be called in the same order on every render. No conditionals, no early returns before hooks.

```tsx
// WRONG — hook called conditionally
function MyComponent({ user }: { user?: User }) {
  if (!user) return <div>No user</div>  // early return before hook!
  const [count, setCount] = useState(0)  // Error
}

// CORRECT — all hooks first, conditionals after
function MyComponent({ user }: { user?: User }) {
  const [count, setCount] = useState(0)  // hooks always run
  if (!user) return <div>No user</div>   // conditional rendering after hooks
  return <div>{user.name}: {count}</div>
}
```

### `useEffect` Infinite Loop

```tsx
// Bug: dependency array includes an object/array created inline
useEffect(() => {
  fetchData(options)
}, [options])  // options is a new object every render → infinite loop

// Fix 1: move the object outside the component
const OPTIONS = { limit: 10 }  // stable reference
useEffect(() => { fetchData(OPTIONS) }, [OPTIONS])  // or [] if truly static

// Fix 2: useMemo for computed objects
const options = useMemo(() => ({ limit: pageSize }), [pageSize])
useEffect(() => { fetchData(options) }, [options])

// Fix 3: use primitive values in dependencies
useEffect(() => { fetchData({ limit: pageSize }) }, [pageSize])  // number, not object

// Bug: state update inside useEffect with that state as dependency
const [data, setData] = useState(null)
useEffect(() => {
  setData(transform(data))  // updates data → triggers effect → infinite loop
}, [data])

// Fix: use functional update or remove the dependency
useEffect(() => {
  setData(prev => transform(prev))  // functional update doesn't need data as dep
}, [])  // run once
```

### `useState` Not Updating / Stale State

```tsx
// Bug: reading state inside a closure that captured an old value
const [count, setCount] = useState(0)
const handleClick = () => {
  setTimeout(() => {
    console.log(count)  // always logs 0 — stale closure!
    setCount(count + 1) // uses stale count
  }, 1000)
}

// Fix: use functional update — always gets the current state
const handleClick = () => {
  setTimeout(() => {
    setCount(prev => prev + 1)  // prev is always current
  }, 1000)
}

// Fix 2: useRef to access current value in closures
const countRef = useRef(count)
countRef.current = count
const handleClick = () => {
  setTimeout(() => {
    console.log(countRef.current)  // always current
  }, 1000)
}
```

### State Update on Unmounted Component

```tsx
// Warning: Can't perform a React state update on an unmounted component
// (legacy warning, but still causes bugs)

// Fix: cancel async operations on unmount
useEffect(() => {
  let cancelled = false
  
  fetchUser(id).then(user => {
    if (!cancelled) setUser(user)  // only update if still mounted
  })
  
  return () => { cancelled = true }  // cleanup on unmount
}, [id])

// Better fix: use AbortController for fetch
useEffect(() => {
  const controller = new AbortController()
  
  fetch(`/api/user/${id}`, { signal: controller.signal })
    .then(r => r.json())
    .then(setUser)
    .catch(e => {
      if (e.name !== 'AbortError') throw e  // ignore expected abort
    })
  
  return () => controller.abort()
}, [id])
```

---

## Next.js Hydration Errors

### `Hydration failed because the initial UI does not match what was rendered on the server`

```tsx
// Cause 1: rendering different content on server vs client
// Browser APIs (window, localStorage, navigator) don't exist on server

// Wrong:
function Component() {
  return <div>{window.innerWidth}px</div>  // window doesn't exist on server
}

// Fix: only render browser-specific content after mount
function Component() {
  const [width, setWidth] = useState<number | null>(null)
  useEffect(() => {
    setWidth(window.innerWidth)  // runs only on client after hydration
  }, [])
  if (width === null) return null  // render nothing on server
  return <div>{width}px</div>
}

// Fix 2: dynamic import with ssr: false for entire component
const BrowserOnlyComponent = dynamic(() => import('./BrowserComponent'), {
  ssr: false
})

// Cause 2: Date/time rendered differently
// Wrong:
<p>{new Date().toLocaleTimeString()}</p>  // different on server and client!
// Fix: only show dates client-side, or use a stable format
```

### `Hydration: Expected server HTML to contain a matching X`

```tsx
// Cause: invalid HTML nesting
// e.g., <p> inside <p>, <div> inside <p>, <table> without <tbody>
<p>
  <div>...</div>  // Invalid — div inside p
</p>
// Fix: use correct semantic HTML, replace p with div where needed

// Debug: check the rendered HTML in page source (Cmd/Ctrl+U)
// Compare server-rendered HTML vs what React expects
```

---

## Next.js App Router Specific

### Server Component vs Client Component Confusion

```tsx
// Error: useState/useEffect in a Server Component
// Server Components cannot use hooks, browser APIs, or event handlers

// Fix: add 'use client' directive at the top of the file
'use client'
import { useState } from 'react'
export function Counter() {
  const [count, setCount] = useState(0)
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>
}

// Structure: keep Server Components as parents, push 'use client' to leaves
// ServerComponent (fetches data, no hooks) → passes data to ClientComponent (handles interaction)

// Passing non-serializable props from Server to Client Component
// Error: only plain objects, primitives, and some types can pass the boundary
// Wrong: passing class instances, functions (except those defined in client), Dates
// Fix: serialize to plain data (string, number, plain object)
```

### `fetch` Caching in App Router (Next.js 13+)

```tsx
// Next.js caches fetch by default — you might be seeing stale data

// No cache (always fresh)
const data = await fetch('/api/data', { cache: 'no-store' })

// Revalidate every 60 seconds
const data = await fetch('/api/data', { next: { revalidate: 60 } })

// Debug: check if cached response is the issue
// Add cache-busting in development:
const data = await fetch(`/api/data?_=${Date.now()}`, { cache: 'no-store' })
```

### Server Actions Failing Silently

```tsx
'use server'
async function submitForm(formData: FormData) {
  // Errors in server actions don't automatically surface to the client
  // Always return error state
  try {
    await db.insert(...)
    return { success: true }
  } catch (e) {
    return { error: 'Failed to save' }  // return error for client to handle
    // Do NOT throw — unhandled throws show Next.js error page in prod
  }
}
```

---

## Performance — Unnecessary Re-renders

```tsx
// Debug: React DevTools → Profiler tab → record interactions
// Components that re-render unnecessarily show in orange

// Common cause 1: new object/function reference on every render
function Parent() {
  const options = { limit: 10 }   // new object every render
  return <Child options={options} />  // Child re-renders even if value is same
}
// Fix: useMemo/useCallback
function Parent() {
  const options = useMemo(() => ({ limit: 10 }), [])
  const handleClick = useCallback(() => doSomething(), [])
  return <Child options={options} onClick={handleClick} />
}

// Common cause 2: context re-renders all consumers
const MyContext = createContext({})
function Provider({ children }) {
  const [user, setUser] = useState(null)
  const [theme, setTheme] = useState('light')
  // Both user AND theme in same context — any theme change re-renders ALL user consumers
}
// Fix: split contexts
const UserContext = createContext({})
const ThemeContext = createContext({})

// Debug: add logging to find who's causing re-renders
useEffect(() => {
  console.log('UserProfile rendered', { userId, user })
})  // no dependency array = runs every render
```

---

## Next.js API Routes / Route Handlers

```tsx
// Pages Router: pages/api/users.ts
export default function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }
  // ...
}

// App Router: app/api/users/route.ts
export async function GET(request: Request) {
  try {
    const users = await db.query('SELECT * FROM users')
    return Response.json(users)
  } catch (err) {
    console.error('GET /api/users error:', err)
    return Response.json({ error: 'Internal server error' }, { status: 500 })
  }
}

// Debug API routes
// 1. Check the terminal — server errors print there
// 2. Check the Network tab in DevTools — see request/response
// 3. Log the full request:
console.log('method:', request.method)
console.log('url:', request.url)
console.log('body:', await request.json())
```

---

## Common Error Messages

```
Error: Element type is invalid
→ You're rendering undefined. Check your import:
  import MyComponent from './MyComponent'   // default import
  import { MyComponent } from './MyComponent'  // named import
  Make sure the file exports what you're importing

Error: Objects are not valid as a React child
→ You're trying to render a plain object. Convert to string/JSX:
  {user}          // Error if user is {name: 'Alice'}
  {user.name}     // OK
  {JSON.stringify(user)}  // Debug

Warning: Each child in a list should have a unique "key" prop
→ Add key to the outermost element in .map()
  {items.map(item => <div key={item.id}>{item.name}</div>)}
  Never use array index as key if list can reorder or have items removed/added

Error: Too many re-renders
→ You're calling setState unconditionally in render (not in an event handler or useEffect)
  const [x, setX] = useState(0)
  setX(1)           // Error — called during render
  onClick={() => setX(1)}  // OK — called in event handler
```
