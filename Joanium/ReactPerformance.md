---
name: React Performance Optimization
trigger: react slow, react performance, unnecessary re-renders, useMemo, useCallback, memo, react profiler, react optimization, slow component, react re-render, virtualize list, bundle size react, react lazy, code splitting react
description: Diagnose and fix React performance problems including unnecessary re-renders, slow lists, large bundle sizes, and expensive computations. Use this skill whenever the user has a sluggish React app, asks about useMemo/useCallback/memo, wants to profile components, or needs to optimize rendering behavior.
---

# ROLE
You are a React performance specialist. You diagnose re-render causes, identify the expensive operations, and apply targeted fixes — not blanket memoization that adds complexity without benefit.

# GOLDEN RULE
```
Measure before optimizing.
React DevTools Profiler → find what's slow → fix that thing.
Don't add useMemo/useCallback/memo everywhere "just in case".
These have overhead too — they're worth it only when the prevented work is more expensive.
```

# STEP 1 — DIAGNOSE

```
1. Install React DevTools browser extension
2. Open DevTools > Profiler tab
3. Click Record → interact with the app → Stop
4. Look for:
   - Components with high "render duration" (bars)
   - Components that render when they shouldn't ("why did this render?")
   - Flame chart showing time per component

Enable "Highlight updates" in DevTools settings → see what flashes on interaction
```

# RE-RENDER CAUSES (KNOW THESE)

```
A component re-renders when:
1. Its own state changes (useState, useReducer)
2. Its parent re-renders (and it's not memoized)
3. A context it subscribes to changes
4. A hook it uses returns a new value

This is NOT a bug — it's how React works.
Only optimize when the re-render is measurably expensive.
```

# MEMO — WHEN TO USE

```tsx
// React.memo — skip re-render if props haven't changed (shallow equality)
// USE WHEN: component renders often + props rarely change + render is expensive

// ❌ Pointless — this component is trivial to render
const Label = memo(({ text }: { text: string }) => <span>{text}</span>);

// ✓ Worthwhile — expensive render, parent re-renders frequently
const DataGrid = memo(({ rows, columns }: DataGridProps) => {
  // renders 1000+ rows with complex formatting
  return <table>...</table>;
});

// ⚠️ memo is USELESS if you pass new object/array/function literals each render
// Parent:
<DataGrid rows={[...data]} />  // new array reference every render → memo ignored
// Fix: move array outside component or use useMemo
```

# useMemo — WHEN TO USE

```tsx
// useMemo — cache an expensive computed value
// USE WHEN: computation is expensive (sort/filter large arrays, complex math)

// ❌ Pointless — trivial computation
const doubled = useMemo(() => value * 2, [value]);

// ✓ Worthwhile — expensive filter + sort over large dataset
const filteredSortedUsers = useMemo(() => {
  return users
    .filter(u => u.role === selectedRole && u.isActive)
    .sort((a, b) => a.name.localeCompare(b.name));
}, [users, selectedRole]);

// ✓ Stabilize object reference to prevent child re-renders
const config = useMemo(() => ({
  theme, locale, currency
}), [theme, locale, currency]);
```

# useCallback — WHEN TO USE

```tsx
// useCallback — stable function reference across renders
// USE WHEN: function is passed to memo-wrapped child OR is a useEffect dependency

// ❌ Pointless — child isn't memoized, won't prevent re-renders
const handleClick = useCallback(() => setCount(c => c + 1), []);

// ✓ Worthwhile — passed to memo-wrapped expensive child
const handleSort = useCallback((column: string) => {
  setSortColumn(column);
  setSortDir(prev => prev === 'asc' ? 'desc' : 'asc');
}, []);  // no dependencies — stable forever

<DataGrid onSort={handleSort} />  // DataGrid is memo-wrapped

// ✓ useEffect dependency
useEffect(() => {
  fetchData(userId);
}, [fetchData, userId]);  // fetchData must be stable to avoid infinite loop
const fetchData = useCallback(async (id: string) => {
  const data = await api.getUser(id);
  setUser(data);
}, []);  // no deps — stable
```

# STATE STRUCTURE — PREVENT CASCADING RE-RENDERS

```tsx
// ❌ One big state object — any change re-renders everything subscribed
const [appState, setAppState] = useState({
  user: null, theme: 'light', cart: [], filters: {}
});

// ✓ Split state by change frequency
const [user, setUser] = useState(null);
const [theme, setTheme] = useState('light');
const [cart, setCart] = useState([]);
const [filters, setFilters] = useState({});

// ✓ Co-locate state — put state as close to where it's used as possible
// Don't lift state to App if only one component needs it
function SearchBar() {
  const [query, setQuery] = useState('');  // stays local
  // ...
}
```

# CONTEXT — PREVENT OVER-SUBSCRIBING

```tsx
// ❌ One big context — ANY change re-renders ALL consumers
const AppContext = createContext({ user, theme, cart, notifications });

// ✓ Split contexts by what changes together
const UserContext = createContext(user);           // changes on login/logout
const ThemeContext = createContext(theme);         // changes on theme toggle
const CartContext = createContext(cart);           // changes on add/remove

// ✓ Memoize context value to prevent re-renders when parent re-renders
function CartProvider({ children }) {
  const [cart, setCart] = useState([]);
  const value = useMemo(() => ({ cart, setCart }), [cart]);
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}
```

# LARGE LISTS — VIRTUALIZATION

```tsx
// Rendering 1000+ items? Don't render them all — virtualize.
// Only render what's visible in the viewport.

// Option 1: @tanstack/react-virtual (headless, flexible)
import { useVirtualizer } from '@tanstack/react-virtual';

function VirtualList({ items }) {
  const parentRef = useRef(null);
  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,   // estimated row height in px
  });

  return (
    <div ref={parentRef} style={{ height: '600px', overflow: 'auto' }}>
      <div style={{ height: virtualizer.getTotalSize() }}>
        {virtualizer.getVirtualItems().map(virtualItem => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: virtualItem.start,
              height: virtualItem.size,
              width: '100%',
            }}
          >
            {items[virtualItem.index].name}
          </div>
        ))}
      </div>
    </div>
  );
}

// Option 2: react-window (simpler, less flexible)
import { FixedSizeList } from 'react-window';
const Row = ({ index, style }) => <div style={style}>{items[index].name}</div>;
<FixedSizeList height={600} itemCount={items.length} itemSize={50} width="100%">
  {Row}
</FixedSizeList>
```

# CODE SPLITTING — REDUCE INITIAL BUNDLE

```tsx
// Lazy-load heavy components (loaded only when rendered)
import { lazy, Suspense } from 'react';

const DataGrid = lazy(() => import('./DataGrid'));
const RichTextEditor = lazy(() => import('./RichTextEditor'));
const ChartDashboard = lazy(() => import('./ChartDashboard'));

function App() {
  return (
    <Suspense fallback={<Skeleton />}>
      <Routes>
        <Route path="/dashboard" element={<ChartDashboard />} />
        <Route path="/editor" element={<RichTextEditor />} />
      </Routes>
    </Suspense>
  );
}

// Analyze bundle:
// npx vite-bundle-visualizer   (Vite)
// npx webpack-bundle-analyzer  (webpack)
```

# COMMON PERFORMANCE MISTAKES

```tsx
// ❌ Creating new objects/arrays in JSX props
<Component style={{ color: 'red' }} />          // new object every render
<Component items={items.filter(Boolean)} />     // new array every render
<Component onClick={() => handleClick(id)} />   // new function every render

// ✓ Move constants outside component or memoize
const STYLE = { color: 'red' };
<Component style={STYLE} />

const activeItems = useMemo(() => items.filter(Boolean), [items]);
<Component items={activeItems} />

const handleClick = useCallback(() => onClick(id), [onClick, id]);
<Component onClick={handleClick} />

// ❌ useEffect with missing or wrong dependencies causing infinite loops
useEffect(() => {
  fetchData(filters);
}, []);  // missing filters dependency — stale closure

// ✓ Correct dependencies
useEffect(() => {
  fetchData(filters);
}, [filters, fetchData]);

// ❌ Blocking renders with synchronous expensive computations
function Component() {
  const result = expensiveCompute(data); // runs every render
  return <div>{result}</div>;
}

// ✓ Memoize
const result = useMemo(() => expensiveCompute(data), [data]);
```

# CHECKLIST
```
[ ] Used React DevTools Profiler to find actual bottleneck
[ ] Large lists are virtualized (react-virtual or react-window)
[ ] Heavy routes are lazy-loaded with React.lazy
[ ] Context split by change frequency
[ ] State co-located, not over-lifted
[ ] useMemo on genuinely expensive computations only
[ ] useCallback on functions passed to memo-wrapped children
[ ] No inline object/array/function literals in frequently-rendered JSX
[ ] Bundle analyzed for large dependencies
```
