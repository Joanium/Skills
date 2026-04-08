---
name: React Hooks Advanced
trigger: react hooks, custom hooks, useReducer, useCallback, useMemo, useRef, useEffect patterns, hook composition, react hook design, advanced hooks, hook optimization, useContext patterns, useDeferredValue, useTransition, hook testing
description: Master advanced React hooks patterns — custom hook design, composition, performance optimization, and avoiding common pitfalls that cause bugs and re-renders.
---

# ROLE
You are a React engineer who has audited hundreds of components and knows exactly where developers misuse hooks, cause infinite render loops, and leak memory. You write hooks that are composable, testable, and correctly handle the async lifecycle of React.

# CORE HOOK RULES (NEVER BREAK THESE)
```
RULE 1: Only call hooks at the top level — never inside loops, conditions, or nested functions
RULE 2: Only call hooks from React function components or other custom hooks
RULE 3: Every hook call must run in the same ORDER every render (same count, same sequence)
RULE 4: Custom hooks must start with "use" — React depends on this naming convention
```

# useEffect — THE MOST MISUNDERSTOOD HOOK

## Dependency Array Patterns
```typescript
// NO dependency array → runs after every render (almost never what you want)
useEffect(() => { fetchData(); });

// EMPTY array → runs once after mount (good for init, subscriptions)
useEffect(() => {
  const sub = socket.subscribe('channel');
  return () => sub.unsubscribe();  // cleanup runs on unmount
}, []);

// WITH dependencies → runs when any dep changes
useEffect(() => {
  fetchUser(userId);
}, [userId]);  // ← only re-fetch when userId changes

// COMMON BUG: missing deps
const [data, setData] = useState(null);
useEffect(() => {
  fetchUser(userId).then(setData);
}, []);  // ← eslint-plugin-react-hooks will warn: userId missing from deps
         // if userId changes, effect won't re-run → stale data
```

## Cleanup Patterns
```typescript
// HTTP abort on unmount / dep change
useEffect(() => {
  const controller = new AbortController();

  fetch(`/api/users/${userId}`, { signal: controller.signal })
    .then(r => r.json())
    .then(setUser)
    .catch(err => {
      if (err.name !== 'AbortError') setError(err);
    });

  return () => controller.abort();
}, [userId]);

// Interval cleanup
useEffect(() => {
  const id = setInterval(() => setTick(t => t + 1), 1000);
  return () => clearInterval(id);
}, []);

// Event listener cleanup
useEffect(() => {
  const handler = (e: KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
  };
  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler);
}, [onClose]);
```

## Async in useEffect (Don't Make It Async Directly)
```typescript
// WRONG — useEffect async function returns a promise, not a cleanup fn
useEffect(async () => {
  const data = await fetchData();  // cleanup fn would need to be returned, but you return promise
  setData(data);
}, []);

// CORRECT — define async inside
useEffect(() => {
  let cancelled = false;

  async function load() {
    const data = await fetchData();
    if (!cancelled) setData(data);  // prevent state update after unmount
  }

  load();
  return () => { cancelled = true; };
}, []);
```

# useCallback AND useMemo

## When to Actually Use Them
```typescript
// useMemo: expensive computation, or stable reference for deps
const sortedItems = useMemo(
  () => [...items].sort((a, b) => a.price - b.price),
  [items]  // only re-sort when items changes
);

// useCallback: stable function reference passed to child component or used in deps
const handleSubmit = useCallback(async (values: FormValues) => {
  await api.createUser(values);
  onSuccess();
}, [onSuccess]);  // stable reference unless onSuccess changes

// WRONG: wrapping everything in useCallback/useMemo
// The comparison itself costs time. Only memoize when:
//   1. Computation is genuinely expensive (> ~1ms)
//   2. Function is passed to a React.memo child
//   3. Function is in a useEffect dep array and causes infinite loops
```

## Infinite Loop Prevention
```typescript
// BUG: fetchData recreated every render → triggers effect → fetchData recreated → loop
const fetchData = () => fetch(`/api/data/${id}`);
useEffect(() => { fetchData(); }, [fetchData]);  // infinite loop

// FIX option 1: move function inside effect
useEffect(() => {
  const fetchData = () => fetch(`/api/data/${id}`);
  fetchData();
}, [id]);

// FIX option 2: useCallback with correct deps
const fetchData = useCallback(() => fetch(`/api/data/${id}`), [id]);
useEffect(() => { fetchData(); }, [fetchData]);
```

# useReducer — FOR COMPLEX STATE

## When to Prefer useReducer Over useState
```typescript
// Use useState when: single value, simple toggle, independent values
const [isOpen, setIsOpen] = useState(false);

// Use useReducer when: multiple related values, next state depends on current state,
// complex transitions, multiple sub-components need to dispatch the same actions

type State = {
  status: 'idle' | 'loading' | 'success' | 'error';
  data: User[] | null;
  error: string | null;
};

type Action =
  | { type: 'FETCH_START' }
  | { type: 'FETCH_SUCCESS'; payload: User[] }
  | { type: 'FETCH_ERROR'; payload: string };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'FETCH_START':
      return { status: 'loading', data: null, error: null };
    case 'FETCH_SUCCESS':
      return { status: 'success', data: action.payload, error: null };
    case 'FETCH_ERROR':
      return { status: 'error', data: null, error: action.payload };
    default:
      return state;
  }
}

// In component:
const [state, dispatch] = useReducer(reducer, {
  status: 'idle', data: null, error: null
});

dispatch({ type: 'FETCH_START' });
```

# useRef — BEYOND DOM ACCESS

## Stable Mutable Values Without Re-renders
```typescript
// Track latest callback without stale closure
function useLatestCallback<T extends (...args: any[]) => any>(callback: T): T {
  const ref = useRef(callback);
  useLayoutEffect(() => {
    ref.current = callback;
  });
  return useCallback((...args) => ref.current(...args), []) as T;
}

// Track previous value
function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T | undefined>(undefined);
  useEffect(() => {
    ref.current = value;
  });
  return ref.current;
}

// Prevent effect from running on mount (run only on updates)
function useUpdateEffect(effect: () => void, deps: React.DependencyList) {
  const isMounted = useRef(false);
  useEffect(() => {
    if (!isMounted.current) {
      isMounted.current = true;
      return;
    }
    return effect();
  }, deps);
}

// Store interval/timeout IDs
const timerRef = useRef<NodeJS.Timeout | null>(null);
useEffect(() => {
  timerRef.current = setInterval(() => { /* ... */ }, 1000);
  return () => {
    if (timerRef.current) clearInterval(timerRef.current);
  };
}, []);
```

# CUSTOM HOOK DESIGN PATTERNS

## Data Fetching Hook
```typescript
interface UseAsyncState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

function useAsync<T>(
  asyncFn: () => Promise<T>,
  deps: React.DependencyList
): UseAsyncState<T> {
  const [state, dispatch] = useReducer(
    (s: UseAsyncState<T>, a: Partial<UseAsyncState<T>>) => ({ ...s, ...a }),
    { data: null, loading: true, error: null, refetch: () => {} }
  );
  const [trigger, setTrigger] = useState(0);

  useEffect(() => {
    let cancelled = false;
    dispatch({ loading: true, error: null });

    asyncFn()
      .then(data => { if (!cancelled) dispatch({ data, loading: false }); })
      .catch(error => { if (!cancelled) dispatch({ error, loading: false }); });

    return () => { cancelled = true; };
  }, [...deps, trigger]);

  const refetch = useCallback(() => setTrigger(t => t + 1), []);

  return { ...state, refetch };
}

// Usage:
const { data: users, loading, error, refetch } = useAsync(
  () => api.getUsers(page),
  [page]
);
```

## Local Storage Hook
```typescript
function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = useCallback((value: T | ((val: T) => T)) => {
    setStoredValue(prev => {
      const valueToStore = value instanceof Function ? value(prev) : value;
      try {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      } catch (err) {
        console.error('localStorage write failed:', err);
      }
      return valueToStore;
    });
  }, [key]);

  return [storedValue, setValue] as const;
}
```

## Debounce Hook
```typescript
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

// Usage:
const [search, setSearch] = useState('');
const debouncedSearch = useDebounce(search, 300);
useEffect(() => { fetchResults(debouncedSearch); }, [debouncedSearch]);
```

## Event Listener Hook
```typescript
function useEventListener<K extends keyof WindowEventMap>(
  eventType: K,
  handler: (event: WindowEventMap[K]) => void,
  element: EventTarget = window,
  options?: AddEventListenerOptions
) {
  const savedHandler = useRef(handler);
  useLayoutEffect(() => { savedHandler.current = handler; });

  useEffect(() => {
    const listener = (event: Event) => savedHandler.current(event as WindowEventMap[K]);
    element.addEventListener(eventType, listener, options);
    return () => element.removeEventListener(eventType, listener, options);
  }, [eventType, element]);
}
```

## Intersection Observer Hook
```typescript
function useIntersectionObserver(
  options?: IntersectionObserverInit
): [React.RefCallback<Element>, boolean] {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const observerRef = useRef<IntersectionObserver | null>(null);

  const ref: React.RefCallback<Element> = useCallback((node) => {
    if (observerRef.current) observerRef.current.disconnect();
    if (!node) return;

    observerRef.current = new IntersectionObserver(([entry]) => {
      setIsIntersecting(entry.isIntersecting);
    }, options);

    observerRef.current.observe(node);
  }, [options?.threshold, options?.root, options?.rootMargin]);

  return [ref, isIntersecting];
}

// Usage (infinite scroll, lazy images):
const [ref, isVisible] = useIntersectionObserver({ threshold: 0.1 });
<div ref={ref}>{isVisible && <HeavyComponent />}</div>
```

# CONCURRENT MODE HOOKS

## useTransition — Non-Blocking State Updates
```typescript
const [isPending, startTransition] = useTransition();
const [searchResults, setSearchResults] = useState([]);

function handleSearch(query: string) {
  // Mark as transition → React can interrupt this update for urgent ones
  startTransition(() => {
    setSearchResults(expensiveFilter(allData, query));
  });
}

// isPending = true while transition is computing
{isPending && <Spinner />}
```

## useDeferredValue — Defer Non-Critical Renders
```typescript
const [query, setQuery] = useState('');
const deferredQuery = useDeferredValue(query);

// query updates immediately (input stays responsive)
// deferredQuery lags behind — used for expensive list filtering
const filteredList = useMemo(
  () => items.filter(i => i.name.includes(deferredQuery)),
  [items, deferredQuery]
);
```

# HOOK TESTING
```typescript
import { renderHook, act } from '@testing-library/react';

test('useDebounce delays value update', async () => {
  jest.useFakeTimers();

  const { result, rerender } = renderHook(
    ({ value }) => useDebounce(value, 300),
    { initialProps: { value: 'a' } }
  );

  expect(result.current).toBe('a');

  rerender({ value: 'ab' });
  expect(result.current).toBe('a');  // not yet updated

  act(() => jest.advanceTimersByTime(300));
  expect(result.current).toBe('ab'); // now updated
});
```

# ANTI-PATTERNS CHECKLIST
```
❌  useEffect with no cleanup for subscriptions/listeners → memory leaks
❌  setState after component unmount → "Can't perform state update on unmounted component"
❌  Object/array literals in dependency arrays → new reference every render → infinite loop
    useEffect(() => {}, [{ id: 1 }])  // new object each render
❌  Missing deps in useEffect → stale closures reading old values
❌  Wrapping every function in useCallback "just in case" → premature optimization
❌  Storing derived state in useState when useMemo would do
❌  Giant monolithic custom hooks — split by concern

✅  Always return cleanup from useEffect when subscribing to anything
✅  Use functional updater form: setState(prev => prev + 1) when new state depends on old
✅  Lint with eslint-plugin-react-hooks exhaustive-deps rule enabled
✅  Keep hooks focused — one hook, one concern
```
