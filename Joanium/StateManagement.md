---
name: State Management
trigger: state management, zustand, redux, redux toolkit, react query, tanstack query, global state, client state, server state, jotai, recoil, state architecture, useReducer, context state, state machine, XState
description: Design and implement scalable state management for frontend applications. Covers the client/server state distinction, React Query for server state, Zustand for client state, Redux Toolkit for complex cases, and state machine patterns with XState.
---

# ROLE
You are a frontend architect. Your job is to design state management that scales with app complexity without overcomplicating simple cases. The biggest mistake in frontend state is treating everything the same — server state and client state are different problems.

# THE TWO KINDS OF STATE

## Client State vs Server State
```
CLIENT STATE — owned by the frontend
  Examples: modal open/close, selected tab, form input, theme, sidebar collapsed
  → Use: useState, useReducer, Zustand, Jotai
  → Characteristics: synchronous, derived from user interaction, no async

SERVER STATE — owned by the backend, cached on frontend
  Examples: user profile, product list, dashboard data, comments
  → Use: React Query / TanStack Query, SWR
  → Characteristics: async, can be stale, needs refetch, background sync

COMMON MISTAKE: Using Redux or Zustand for server state
  → This forces you to write loading/error/caching logic manually
  → React Query handles all of this, stop re-inventing it
```

# SERVER STATE WITH REACT QUERY

## Setup
```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,   // data is fresh for 5 min
      gcTime: 10 * 60 * 1000,     // cache kept for 10 min after unused
      retry: 2,
      refetchOnWindowFocus: true,
    },
    mutations: {
      retry: 0,
    }
  }
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <MyApp />
    </QueryClientProvider>
  )
}
```

## Queries — Fetching Data
```typescript
// Basic query
function useUser(userId: string) {
  return useQuery({
    queryKey: ['users', userId],   // cache key — must be unique and descriptive
    queryFn: () => api.users.getById(userId),
    enabled: !!userId,    // don't fetch if userId is empty
  })
}

// Usage
function UserProfile({ userId }: { userId: string }) {
  const { data: user, isLoading, isError, error } = useUser(userId)

  if (isLoading) return <Skeleton />
  if (isError) return <ErrorMessage error={error} />
  return <div>{user.name}</div>
}

// List with filters — filters are part of the query key
function useProducts(filters: ProductFilters) {
  return useQuery({
    queryKey: ['products', filters],   // re-fetches when filters change
    queryFn: () => api.products.list(filters),
    placeholderData: keepPreviousData,   // show old data while fetching new page
  })
}

// Paginated
function useProductPage(page: number) {
  return useQuery({
    queryKey: ['products', 'page', page],
    queryFn: () => api.products.list({ page, limit: 20 }),
    placeholderData: keepPreviousData,
  })
}

// Infinite scroll
function useInfiniteProducts(filters: ProductFilters) {
  return useInfiniteQuery({
    queryKey: ['products', 'infinite', filters],
    queryFn: ({ pageParam }) => api.products.list({ ...filters, cursor: pageParam }),
    initialPageParam: undefined,
    getNextPageParam: (lastPage) => lastPage.nextCursor ?? undefined,
  })
}
// Usage: data.pages.flatMap(p => p.items)
```

## Mutations — Writing Data
```typescript
function useUpdateUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: Partial<User> }) =>
      api.users.update(userId, data),

    // Optimistic update — update UI before server confirms
    onMutate: async ({ userId, data }) => {
      await queryClient.cancelQueries({ queryKey: ['users', userId] })
      const previous = queryClient.getQueryData<User>(['users', userId])

      queryClient.setQueryData<User>(['users', userId], (old) =>
        old ? { ...old, ...data } : old
      )

      return { previous }   // returned as context
    },

    onError: (err, { userId }, context) => {
      // Rollback on error
      if (context?.previous) {
        queryClient.setQueryData(['users', userId], context.previous)
      }
    },

    onSettled: (_, __, { userId }) => {
      // Refetch to sync with server (whether success or error)
      queryClient.invalidateQueries({ queryKey: ['users', userId] })
    }
  })
}

// Invalidate related queries after a mutation
function useDeletePost() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (postId: string) => api.posts.delete(postId),
    onSuccess: (_, postId) => {
      // Remove this post from cache
      queryClient.removeQueries({ queryKey: ['posts', postId] })
      // Invalidate lists — they may have included this post
      queryClient.invalidateQueries({ queryKey: ['posts'], exact: false })
    }
  })
}
```

# CLIENT STATE WITH ZUSTAND

## Basic Store
```typescript
import { create } from 'zustand'

// Simple UI state
interface UIState {
  sidebarOpen: boolean
  theme: 'light' | 'dark'
  activeModal: string | null
  toggleSidebar: () => void
  setTheme: (theme: 'light' | 'dark') => void
  openModal: (id: string) => void
  closeModal: () => void
}

const useUI = create<UIState>((set) => ({
  sidebarOpen: true,
  theme: 'light',
  activeModal: null,
  toggleSidebar: () => set(s => ({ sidebarOpen: !s.sidebarOpen })),
  setTheme: (theme) => set({ theme }),
  openModal: (id) => set({ activeModal: id }),
  closeModal: () => set({ activeModal: null }),
}))

// Usage — components subscribe to only what they need
function Sidebar() {
  const isOpen = useUI(s => s.sidebarOpen)    // re-renders only when sidebarOpen changes
  return <nav className={isOpen ? 'open' : 'closed'}>...</nav>
}

function ThemeToggle() {
  const { theme, setTheme } = useUI(s => ({ theme: s.theme, setTheme: s.setTheme }))
  return <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>Toggle</button>
}
```

## Zustand with Persistence
```typescript
import { persist } from 'zustand/middleware'

const usePreferences = create(
  persist<PreferencesState>(
    (set) => ({
      language: 'en',
      currency: 'USD',
      notifications: true,
      setLanguage: (language) => set({ language }),
      setCurrency: (currency) => set({ currency }),
    }),
    {
      name: 'user-preferences',    // localStorage key
      partialize: (state) => ({    // only persist specific fields
        language: state.language,
        currency: state.currency,
      })
    }
  )
)
```

## Zustand with Slices (Large Stores)
```typescript
import { StateCreator } from 'zustand'

interface CartSlice {
  cartItems: CartItem[]
  addToCart: (product: Product, quantity: number) => void
  removeFromCart: (productId: string) => void
  clearCart: () => void
}

interface CheckoutSlice {
  step: 'cart' | 'shipping' | 'payment' | 'confirm'
  shippingAddress: Address | null
  nextStep: () => void
  setAddress: (address: Address) => void
}

const createCartSlice: StateCreator<CartSlice & CheckoutSlice, [], [], CartSlice> = (set) => ({
  cartItems: [],
  addToCart: (product, quantity) => set(s => ({
    cartItems: [...s.cartItems, { product, quantity }]
  })),
  removeFromCart: (productId) => set(s => ({
    cartItems: s.cartItems.filter(i => i.product.id !== productId)
  })),
  clearCart: () => set({ cartItems: [] })
})

const createCheckoutSlice: StateCreator<CartSlice & CheckoutSlice, [], [], CheckoutSlice> = (set, get) => ({
  step: 'cart',
  shippingAddress: null,
  nextStep: () => {
    const steps = ['cart', 'shipping', 'payment', 'confirm'] as const
    const current = get().step
    const next = steps[steps.indexOf(current) + 1]
    if (next) set({ step: next })
  },
  setAddress: (address) => set({ shippingAddress: address })
})

const useStore = create<CartSlice & CheckoutSlice>()((...a) => ({
  ...createCartSlice(...a),
  ...createCheckoutSlice(...a),
}))
```

# USEREDUCER — COMPLEX LOCAL STATE
```typescript
// For component-level state with multiple related sub-values
type FormState = {
  values: { name: string; email: string; password: string }
  errors: Partial<Record<string, string>>
  submitting: boolean
  submitted: boolean
}

type FormAction =
  | { type: 'SET_FIELD'; field: string; value: string }
  | { type: 'SET_ERROR'; field: string; message: string }
  | { type: 'CLEAR_ERRORS' }
  | { type: 'SUBMIT_START' }
  | { type: 'SUBMIT_SUCCESS' }
  | { type: 'SUBMIT_FAILURE'; errors: Record<string, string> }

function formReducer(state: FormState, action: FormAction): FormState {
  switch (action.type) {
    case 'SET_FIELD':
      return {
        ...state,
        values: { ...state.values, [action.field]: action.value },
        errors: { ...state.errors, [action.field]: undefined }  // clear field error on change
      }
    case 'SET_ERROR':
      return { ...state, errors: { ...state.errors, [action.field]: action.message } }
    case 'SUBMIT_START':
      return { ...state, submitting: true, errors: {} }
    case 'SUBMIT_SUCCESS':
      return { ...state, submitting: false, submitted: true }
    case 'SUBMIT_FAILURE':
      return { ...state, submitting: false, errors: action.errors }
    default:
      return state
  }
}

function RegistrationForm() {
  const [state, dispatch] = useReducer(formReducer, {
    values: { name: '', email: '', password: '' },
    errors: {},
    submitting: false,
    submitted: false,
  })

  const handleSubmit = async () => {
    dispatch({ type: 'SUBMIT_START' })
    try {
      await api.register(state.values)
      dispatch({ type: 'SUBMIT_SUCCESS' })
    } catch (err) {
      dispatch({ type: 'SUBMIT_FAILURE', errors: err.fieldErrors })
    }
  }
  // ...
}
```

# XSTATE — STATE MACHINES FOR COMPLEX FLOWS
```typescript
// For: checkout flows, multi-step forms, media players, anything with complex state transitions
import { createMachine, assign } from 'xstate'
import { useMachine } from '@xstate/react'

const checkoutMachine = createMachine({
  id: 'checkout',
  initial: 'cart',
  context: { items: [], shipping: null, paymentMethod: null },
  states: {
    cart: {
      on: {
        PROCEED: { target: 'shipping', guard: ({ context }) => context.items.length > 0 }
      }
    },
    shipping: {
      on: {
        SET_ADDRESS: {
          actions: assign({ shipping: ({ event }) => event.address })
        },
        PROCEED: {
          target: 'payment',
          guard: ({ context }) => context.shipping !== null
        },
        BACK: 'cart'
      }
    },
    payment: {
      on: {
        SET_PAYMENT: {
          actions: assign({ paymentMethod: ({ event }) => event.method })
        },
        SUBMIT: { target: 'processing' },
        BACK: 'shipping'
      }
    },
    processing: {
      invoke: {
        src: 'processPayment',
        onDone: 'success',
        onError: 'payment',   // back to payment on failure
      }
    },
    success: { type: 'final' },
  }
})

function Checkout() {
  const [state, send] = useMachine(checkoutMachine, {
    actors: {
      processPayment: ({ context }) => api.processPayment(context)
    }
  })

  if (state.matches('cart'))       return <CartStep onProceed={() => send({ type: 'PROCEED' })} />
  if (state.matches('shipping'))   return <ShippingStep onProceed={() => send({ type: 'PROCEED' })} />
  if (state.matches('processing')) return <Spinner />
  if (state.matches('success'))    return <SuccessPage />
}
```
