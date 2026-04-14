---
name: Frontend Architecture
trigger: frontend architecture, React structure, component design, state management, routing, UI structure, folder structure, React app, Next.js setup, SPA architecture, component tree, design system, Tailwind setup
description: Fifth skill in the build pipeline. Read after API Design. Covers frontend folder structure, component hierarchy, state management strategy, routing, API integration patterns, and performance considerations for React/Next.js applications.
prev_skill: 04-APIDesign.md
next_skill: 06-BackendArchitecture.md
---

# ROLE
You are a senior frontend engineer. You build UIs that are fast, maintainable, and pleasant to work in. You know that the #1 cause of frontend complexity is improper state management and unclear component boundaries. You design the architecture before opening a code editor.

# CORE PRINCIPLES
```
COLOCATE — keep related code together (component + styles + tests in one folder)
LIFT STATE ONLY WHEN NEEDED — start local, lift when two siblings need it
SERVER STATE ≠ CLIENT STATE — server data belongs in React Query/SWR, not useState
COMPONENTS SHOULD DO ONE THING — if you can't describe it in 5 words, split it
DESIGN TOKENS BEFORE COMPONENTS — colors, spacing, typography in one place
ACCESSIBLE BY DEFAULT — semantic HTML, ARIA labels, keyboard navigation from the start
```

# STEP 1 — CHOOSE THE FRAMEWORK AND RENDERING STRATEGY

```
DECISION MATRIX:

  Next.js App Router (recommended for most apps)
    ✅ SSR/SSG for SEO-critical pages (landing, video pages, profiles)
    ✅ API routes co-located (or proxy to your backend)
    ✅ Server Components reduce JS bundle and improve LCP
    ✅ Image optimization, routing, and caching built in
    Use when: public-facing content needs SEO, you want full-stack in one repo

  Vite + React SPA
    ✅ Simpler mental model, no server-side concepts
    ✅ Better for highly interactive apps with no SEO requirement
    ✅ Faster development builds
    Use when: authenticated dashboard, internal tools, admin panel

  Remix
    ✅ Form-first, progressive enhancement, excellent data loading patterns
    Use when: content-heavy, form-heavy, high reliability requirements

RENDERING PER PAGE TYPE:
  Page Type           Strategy    Reason
  ─────────────────   ─────────   ───────────────────────────────────
  Homepage / feed     ISR/SSG     High traffic, content changes hourly
  Video watch page    SSR         Dynamic OG tags, SEO, per-request data
  Channel page        SSR         Dynamic content, SEO
  Upload / edit       CSR         No SEO need, highly interactive
  Dashboard           CSR         Private, personalized, interactive
  Auth pages          CSR         No SEO value
```

# STEP 2 — FOLDER STRUCTURE

```
src/
├── app/                    # Next.js App Router pages (or pages/ for Pages Router)
│   ├── (auth)/             # Route group — auth pages, no shared layout
│   │   ├── login/
│   │   └── register/
│   ├── (main)/             # Route group — main layout with nav
│   │   ├── layout.tsx      # Shared nav + sidebar
│   │   ├── page.tsx        # Homepage / feed
│   │   ├── watch/[id]/     # Video watch page
│   │   ├── channel/[handle]/
│   │   ├── upload/
│   │   └── dashboard/
│   └── api/                # Next.js API routes (or proxy layer)
│
├── components/
│   ├── ui/                 # Pure presentational, no data fetching
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.test.tsx
│   │   │   └── index.ts    # re-export
│   │   ├── Avatar/
│   │   ├── Modal/
│   │   ├── VideoCard/
│   │   └── index.ts        # barrel export
│   │
│   ├── features/           # Feature-specific, may fetch data
│   │   ├── VideoPlayer/
│   │   ├── CommentSection/
│   │   ├── UploadForm/
│   │   ├── SubscribeButton/
│   │   └── SearchBar/
│   │
│   └── layout/             # Structural components
│       ├── Navbar.tsx
│       ├── Sidebar.tsx
│       └── Footer.tsx
│
├── hooks/                  # Custom React hooks
│   ├── useAuth.ts          # Current user, login/logout
│   ├── useVideo.ts         # React Query wrapper for video API
│   ├── useInfiniteScroll.ts
│   └── useDebounce.ts
│
├── lib/                    # Pure utilities, no React
│   ├── api.ts              # Axios/fetch client with auth interceptors
│   ├── formatters.ts       # formatDuration, formatCount, formatDate
│   ├── validators.ts       # Zod schemas for form validation
│   └── constants.ts        # App-wide constants
│
├── store/                  # Client-only global state (Zustand or Context)
│   ├── authStore.ts        # Current user, token
│   └── playerStore.ts      # Video player state (volume, quality)
│
├── styles/
│   ├── globals.css         # Tailwind base + CSS variables (design tokens)
│   └── themes/
│
└── types/                  # TypeScript types mirroring API responses
    ├── api.ts              # Generated or hand-written from OpenAPI spec
    └── index.ts
```

# STEP 3 — STATE MANAGEMENT STRATEGY

```
THREE TYPES OF STATE — treat them differently:

1. SERVER STATE (data from the API) → React Query or SWR
   Examples: current user's videos, feed data, comments
   DO NOT put in useState — React Query handles caching, revalidation, loading

   import { useQuery, useMutation } from '@tanstack/react-query'

   const { data, isLoading, error } = useQuery({
     queryKey: ['videos', { channelId }],
     queryFn: () => api.videos.list({ channelId }),
     staleTime: 60_000,  // consider fresh for 1 minute
   })

   const likeMutation = useMutation({
     mutationFn: (videoId: string) => api.videos.like(videoId),
     onSuccess: () => {
       queryClient.invalidateQueries({ queryKey: ['videos', videoId] })
     }
   })

2. GLOBAL CLIENT STATE → Zustand (auth, theme, UI state shared across routes)
   Examples: logged-in user, player volume, notification count

   import { create } from 'zustand'
   import { persist } from 'zustand/middleware'

   export const useAuthStore = create(persist(
     (set) => ({
       user: null,
       token: null,
       login: (user, token) => set({ user, token }),
       logout: () => set({ user: null, token: null }),
     }),
     { name: 'auth-storage' }
   ))

3. LOCAL UI STATE → useState / useReducer
   Examples: modal open/closed, form inputs, accordion expanded
   Keep as close to where it's used as possible. Lift only if needed.

ANTI-PATTERNS:
  ❌ useEffect + useState to fetch data — use React Query instead
  ❌ Storing server data in Redux/Zustand — it's already cached in React Query
  ❌ Prop drilling more than 2 levels — use Context or Zustand
  ❌ One global store for everything — separate concerns
```

# STEP 4 — API CLIENT LAYER

```typescript
// lib/api.ts — centralized API client
import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

const client = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 10_000,
})

// Attach token to every request
client.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors globally
client.interceptors.response.use(
  (res) => res.data.data,  // unwrap the envelope
  async (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error.response?.data?.error ?? error)
  }
)

// Typed API methods (mirror your API spec exactly)
export const api = {
  videos: {
    list:   (params) => client.get('/videos', { params }),
    get:    (id)     => client.get(`/videos/${id}`),
    create: (body)   => client.post('/videos', body),
    update: (id, body) => client.patch(`/videos/${id}`, body),
    delete: (id)     => client.delete(`/videos/${id}`),
    like:   (id)     => client.post(`/videos/${id}/like`),
    unlike: (id)     => client.delete(`/videos/${id}/like`),
  },
  auth: {
    login:    (body) => client.post('/auth/login', body),
    register: (body) => client.post('/auth/register', body),
    me:       ()     => client.get('/me'),
  },
}
```

# STEP 5 — COMPONENT DESIGN PATTERNS

```typescript
// UI COMPONENT PATTERN — pure, no data fetching, fully typed
interface VideoCardProps {
  video: Video
  onLike?: (videoId: string) => void
  variant?: 'default' | 'compact' | 'featured'
}

export function VideoCard({ video, onLike, variant = 'default' }: VideoCardProps) {
  return (
    <article className="...">
      <img src={video.thumbnail_url} alt={video.title} />
      <h3>{video.title}</h3>
      <span>{formatCount(video.view_count)} views</span>
      {onLike && (
        <button onClick={() => onLike(video.id)} aria-label="Like video">
          Like
        </button>
      )}
    </article>
  )
}

// FEATURE COMPONENT — fetches own data, uses hooks
export function VideoFeed({ channelId }: { channelId?: string }) {
  const { data, isLoading, fetchNextPage } = useInfiniteQuery({
    queryKey: ['videos', channelId],
    queryFn: ({ pageParam = 1 }) => api.videos.list({ channelId, page: pageParam }),
    getNextPageParam: (last) => last.pagination.has_next ? last.pagination.page + 1 : undefined
  })

  if (isLoading) return <VideoCardSkeleton count={6} />

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {data?.pages.flatMap(p => p).map(video => (
        <VideoCard key={video.id} video={video} />
      ))}
    </div>
  )
}

// COMPOUND COMPONENT PATTERN — for complex UI with shared state
const VideoPlayer = {
  Root:     VideoPlayerRoot,
  Controls: VideoPlayerControls,
  Progress: VideoPlayerProgress,
  Volume:   VideoPlayerVolume,
}
// Usage: <VideoPlayer.Root><VideoPlayer.Controls /><VideoPlayer.Progress /></VideoPlayer.Root>
```

# STEP 6 — PERFORMANCE DEFAULTS

```
CODE SPLITTING:
  - Route-level splitting is automatic in Next.js / React Router
  - Dynamic import heavy components: const VideoPlayer = dynamic(() => import('./VideoPlayer'))

IMAGE OPTIMIZATION:
  - Always use next/image — automatic WebP, lazy loading, size optimization
  - Always specify width and height or fill — prevents layout shift

INFINITE SCROLL vs PAGINATION:
  - Feed / explore: infinite scroll (useIntersectionObserver + useInfiniteQuery)
  - Search results: pagination (discrete pages, better for returning to position)
  - Comments: "load more" button (explicit user action)

SKELETON LOADING:
  - Every data-fetching component has a matching skeleton (same dimensions)
  - Prevents layout shift, better than spinners for content-shaped data

MEMOIZATION (use sparingly):
  - useMemo: expensive computations only (filtering 1000+ items)
  - useCallback: functions passed to memo'd children only
  - React.memo: components that receive stable props and re-render often
  - RULE: profile first, memoize after — premature memoization adds complexity
```

# CHECKLIST — Before Moving to Backend Architecture

```
✅ Framework and rendering strategy chosen per page type
✅ Folder structure defined and scaffolded
✅ State management strategy documented (server vs global vs local)
✅ API client written with auth interceptors and envelope unwrapping
✅ Component taxonomy defined (ui, features, layout)
✅ Design tokens in globals.css (colors, spacing, typography)
✅ Performance defaults in place (images, code splitting, skeletons)
✅ TypeScript types written for all API response shapes
→ NEXT: 06-BackendArchitecture.md
```
