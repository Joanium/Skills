---
name: React Advanced Patterns
trigger: react patterns, react hooks, custom hooks, react context, react performance, useMemo, useCallback, react compound component, render props, react composition, react state management, react optimization, react suspense, react error boundary, react portals
description: Write production-grade React with advanced patterns. Covers custom hooks, compound components, context patterns, performance optimization (memo/useMemo/useCallback), error boundaries, Suspense, portals, and architectural patterns for scalable component systems.
---

# ROLE
You are a senior React engineer. Your job is to write component systems that are composable, performant, and maintainable. React's power is in composition — master the patterns, not just the API.

# CUSTOM HOOKS — EXTRACT AND REUSE LOGIC

## Pattern: Encapsulate Complex State
```tsx
// Bad: logic scattered in component
function UserProfile() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchUser().then(setUser).catch(setError).finally(() => setLoading(false))
  }, [])
  // ...
}

// Good: extracted into a custom hook
function useUser(userId: string) {
  const [state, setState] = useState<{
    data: User | null
    loading: boolean
    error: Error | null
  }>({ data: null, loading: true, error: null })

  useEffect(() => {
    let cancelled = false   // cleanup for race conditions
    setState({ data: null, loading: true, error: null })

    fetchUser(userId)
      .then(data => { if (!cancelled) setState({ data, loading: false, error: null }) })
      .catch(error => { if (!cancelled) setState({ data: null, loading: false, error }) })

    return () => { cancelled = true }
  }, [userId])

  return state
}

// Component is now clean
function UserProfile({ userId }: { userId: string }) {
  const { data: user, loading, error } = useUser(userId)

  if (loading) return <Spinner />
  if (error) return <ErrorMessage error={error} />
  return <div>{user?.name}</div>
}
```

## Useful Custom Hook Patterns
```tsx
// useLocalStorage — persist state to localStorage
function useLocalStorage<T>(key: string, initialValue: T) {
  const [value, setValue] = useState<T>(() => {
    try {
      const stored = localStorage.getItem(key)
      return stored ? JSON.parse(stored) : initialValue
    } catch {
      return initialValue
    }
  })

  const set = useCallback((newValue: T | ((prev: T) => T)) => {
    setValue(prev => {
      const next = typeof newValue === 'function' ? (newValue as Function)(prev) : newValue
      localStorage.setItem(key, JSON.stringify(next))
      return next
    })
  }, [key])

  return [value, set] as const
}

// useDebounce — debounce any value
function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

// usePrevious — track previous value
function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T>()
  useEffect(() => { ref.current = value })
  return ref.current
}

// useMediaQuery — responsive breakpoints
function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches)
  useEffect(() => {
    const mq = window.matchMedia(query)
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [query])
  return matches
}

// useClickOutside — dismiss dropdowns/modals
function useClickOutside(ref: React.RefObject<HTMLElement>, handler: () => void) {
  useEffect(() => {
    const listener = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) handler()
    }
    document.addEventListener('mousedown', listener)
    return () => document.removeEventListener('mousedown', listener)
  }, [ref, handler])
}

// useEventListener — type-safe event listener
function useEventListener<K extends keyof WindowEventMap>(
  event: K,
  handler: (e: WindowEventMap[K]) => void,
  element: EventTarget = window
) {
  const handlerRef = useRef(handler)
  useEffect(() => { handlerRef.current = handler })

  useEffect(() => {
    const listener = (e: Event) => handlerRef.current(e as WindowEventMap[K])
    element.addEventListener(event, listener)
    return () => element.removeEventListener(event, listener)
  }, [event, element])
}
```

# COMPOUND COMPONENTS — API DESIGN PATTERN
```tsx
// Compound components share implicit state via context
// Users get a flexible, composable API

// The context
interface AccordionContext {
  openItems: string[]
  toggle: (id: string) => void
}

const AccordionCtx = React.createContext<AccordionContext | null>(null)
const useAccordion = () => {
  const ctx = React.useContext(AccordionCtx)
  if (!ctx) throw new Error('Must be used inside <Accordion>')
  return ctx
}

// Parent
function Accordion({ children, multiple = false }: {
  children: React.ReactNode
  multiple?: boolean
}) {
  const [openItems, setOpenItems] = useState<string[]>([])

  const toggle = useCallback((id: string) => {
    setOpenItems(prev =>
      prev.includes(id)
        ? prev.filter(i => i !== id)
        : multiple ? [...prev, id] : [id]
    )
  }, [multiple])

  return (
    <AccordionCtx.Provider value={{ openItems, toggle }}>
      <div className="accordion">{children}</div>
    </AccordionCtx.Provider>
  )
}

// Child components
Accordion.Item = function AccordionItem({ id, children }: { id: string; children: React.ReactNode }) {
  return <div data-id={id}>{children}</div>
}

Accordion.Trigger = function AccordionTrigger({ id, children }: { id: string; children: React.ReactNode }) {
  const { openItems, toggle } = useAccordion()
  return (
    <button
      aria-expanded={openItems.includes(id)}
      onClick={() => toggle(id)}
    >
      {children}
    </button>
  )
}

Accordion.Content = function AccordionContent({ id, children }: { id: string; children: React.ReactNode }) {
  const { openItems } = useAccordion()
  if (!openItems.includes(id)) return null
  return <div role="region">{children}</div>
}

// Usage — clean, flexible API
<Accordion multiple>
  <Accordion.Item id="1">
    <Accordion.Trigger id="1">Section 1</Accordion.Trigger>
    <Accordion.Content id="1">Content 1</Accordion.Content>
  </Accordion.Item>
</Accordion>
```

# PERFORMANCE OPTIMIZATION

## When to Use memo, useMemo, useCallback
```tsx
// RULE: Profile first — don't premature-optimize
// React DevTools Profiler shows actual render times

// React.memo — skip re-render if props haven't changed
const ExpensiveList = React.memo(function ExpensiveList({
  items,
  onItemClick,
}: {
  items: Item[]
  onItemClick: (id: string) => void
}) {
  // Only re-renders if items or onItemClick reference changes
  return <ul>{items.map(item => <li key={item.id}>{item.name}</li>)}</ul>
})

// useCallback — stable function reference (for memo'd children, event listeners)
function Parent() {
  const [count, setCount] = useState(0)
  const [items, setItems] = useState<Item[]>([])

  // WITHOUT useCallback: new function reference every render → ExpensiveList always re-renders
  // WITH useCallback: same reference if no deps changed → memo works
  const handleItemClick = useCallback((id: string) => {
    console.log('clicked', id)
  }, [])   // stable — no deps

  return (
    <>
      <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>
      <ExpensiveList items={items} onItemClick={handleItemClick} />
    </>
  )
}

// useMemo — expensive computation / stable object reference
function SearchResults({ query, rawItems }: { query: string; rawItems: Item[] }) {
  // Recomputes only when query or rawItems changes
  const filteredItems = useMemo(() =>
    rawItems.filter(item =>
      item.name.toLowerCase().includes(query.toLowerCase())
    ),
    [rawItems, query]
  )

  // Stable object ref for memo'd child
  const config = useMemo(() => ({ pageSize: 20, sortDir: 'asc' }), [])

  return <ExpensiveList items={filteredItems} config={config} />
}
```

## Avoid These Common Performance Killers
```tsx
// BAD: new object/array on every render → memo always re-renders
<Component style={{ color: 'red' }} />   // new object each render
<Component items={[1, 2, 3]} />           // new array each render

// GOOD: stable reference
const style = { color: 'red' }            // outside component OR useMemo
<Component style={style} />

// BAD: inline arrow function kills memo
<button onClick={() => handleClick(item.id)}>  // new fn each render

// GOOD: use useCallback or pass ID as prop
<ItemButton id={item.id} onClick={handleClick} />  // child curries the ID

// BAD: state that causes excessive re-renders
const [formState, setFormState] = useState({ name: '', email: '', bio: '' })
// every keystroke re-renders entire form

// GOOD: separate state OR use useReducer for forms with many fields
const [name, setName]   = useState('')
const [email, setEmail] = useState('')
```

# ERROR BOUNDARIES
```tsx
// Class component (required for error boundaries — no hooks equivalent yet)
interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

class ErrorBoundary extends React.Component<
  { fallback: React.ReactNode; children: React.ReactNode },
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Log to error reporting service
    console.error('Error caught by boundary:', error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback
    }
    return this.props.children
  }
}

// Usage — wrap risky sections
<ErrorBoundary fallback={<ErrorPage />}>
  <UserDashboard />
</ErrorBoundary>

// Multiple boundaries for isolated failures
<Layout>
  <ErrorBoundary fallback={<p>Navigation failed</p>}>
    <Navigation />
  </ErrorBoundary>
  <ErrorBoundary fallback={<p>Content failed to load</p>}>
    <MainContent />
  </ErrorBoundary>
</Layout>
```

# SUSPENSE AND LAZY LOADING
```tsx
const HeavyPage = React.lazy(() => import('./HeavyPage'))

function App() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <Routes>
        <Route path="/heavy" element={<HeavyPage />} />
      </Routes>
    </Suspense>
  )
}

// Data fetching with Suspense (React 18+ / frameworks like Next.js)
// use() hook for promises
function UserCard({ userPromise }: { userPromise: Promise<User> }) {
  const user = use(userPromise)   // suspends until resolved
  return <div>{user.name}</div>
}

// In parent: wrap in Suspense
<Suspense fallback={<Skeleton />}>
  <UserCard userPromise={fetchUser(userId)} />
</Suspense>
```

# PORTALS — RENDER OUTSIDE DOM HIERARCHY
```tsx
import { createPortal } from 'react-dom'

function Modal({ isOpen, onClose, children }: {
  isOpen: boolean
  onClose: () => void
  children: React.ReactNode
}) {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  // Handle Escape key
  useEffect(() => {
    if (!isOpen) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [isOpen, onClose])

  if (!mounted || !isOpen) return null

  return createPortal(
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content"
        role="dialog"
        aria-modal
        onClick={e => e.stopPropagation()}
      >
        {children}
      </div>
    </div>,
    document.getElementById('modal-root')!
  )
}
```

# CONTEXT — DO IT RIGHT
```tsx
// Pattern: separate state and dispatch contexts to prevent unnecessary re-renders
interface ThemeState { mode: 'light' | 'dark'; accent: string }
type ThemeAction = { type: 'TOGGLE_MODE' } | { type: 'SET_ACCENT'; accent: string }

const ThemeStateCtx    = React.createContext<ThemeState | null>(null)
const ThemeDispatchCtx = React.createContext<React.Dispatch<ThemeAction> | null>(null)

function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(
    (state: ThemeState, action: ThemeAction): ThemeState => {
      switch (action.type) {
        case 'TOGGLE_MODE': return { ...state, mode: state.mode === 'light' ? 'dark' : 'light' }
        case 'SET_ACCENT':  return { ...state, accent: action.accent }
        default: return state
      }
    },
    { mode: 'light', accent: '#0066cc' }
  )

  return (
    <ThemeStateCtx.Provider value={state}>
      <ThemeDispatchCtx.Provider value={dispatch}>
        {children}
      </ThemeDispatchCtx.Provider>
    </ThemeStateCtx.Provider>
  )
}

// Hooks with good error messages
export const useTheme = () => {
  const ctx = React.useContext(ThemeStateCtx)
  if (!ctx) throw new Error('useTheme must be inside ThemeProvider')
  return ctx
}
export const useThemeDispatch = () => {
  const ctx = React.useContext(ThemeDispatchCtx)
  if (!ctx) throw new Error('useThemeDispatch must be inside ThemeProvider')
  return ctx
}

// Component that only reads state — only re-renders when state changes
function ThemeToggle() {
  const dispatch = useThemeDispatch()  // stable reference, never re-renders from state changes
  return <button onClick={() => dispatch({ type: 'TOGGLE_MODE' })}>Toggle</button>
}
```
