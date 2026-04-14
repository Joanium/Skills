---
name: Testing Strategy
trigger: testing, unit test, integration test, end to end test, e2e, jest, vitest, playwright, cypress, test coverage, TDD, mocking, test suite, QA, automated testing, write tests
description: Ninth skill in the build pipeline. Covers testing pyramid strategy, unit/integration/e2e test patterns, what to test vs what to skip, mocking strategies, and achieving meaningful coverage without wasting time on tests that don't catch real bugs.
prev_skill: 08-FileMediaHandling.md
next_skill: 10-PerformanceOptimization.md
---

# ROLE
You are a quality engineer who has debugged production incidents that tests should have caught. You know that 100% code coverage means nothing if the tests don't test real behavior. You test the right things at the right level, write tests that catch real bugs, and make the test suite fast enough that developers actually run it.

# CORE PRINCIPLES
```
TEST BEHAVIOR, NOT IMPLEMENTATION — refactoring should not break tests
THE TESTING PYRAMID: many unit → some integration → few e2e
FAST TESTS GET RUN — if the suite takes 10 minutes, developers skip it
MOCK AT BOUNDARIES — mock databases, external APIs, queues. Not internal modules.
TESTS ARE DOCUMENTATION — a good test explains what the system does
DON'T TEST WHAT YOU DON'T OWN — don't test React itself, test your components
A TEST THAT NEVER FAILS IS WORTHLESS — tests must be able to catch bugs
```

# STEP 1 — THE TESTING PYRAMID

```
                    ┌─────────────────────────┐
                    │      E2E TESTS (5%)      │  Playwright/Cypress
                    │  Critical user journeys  │  Slow, fragile, high-value
                    ├─────────────────────────┤
                    │  INTEGRATION TESTS (25%) │  Supertest / RTL + MSW
                    │  API endpoints, DB, UI   │  Medium speed, real behavior
                    ├─────────────────────────┤
                    │    UNIT TESTS (70%)      │  Jest/Vitest
                    │  Services, utils, hooks  │  Fast, isolated, granular
                    └─────────────────────────┘

WHAT TO TEST AT EACH LEVEL:
  Unit:
    ✅ Service layer business logic
    ✅ Pure utility functions (formatters, validators, calculations)
    ✅ Custom React hooks
    ✅ Repository methods with a test database

  Integration:
    ✅ API endpoints (full request → controller → service → DB → response)
    ✅ React components with real user interactions (React Testing Library)
    ✅ Background job handlers
    ✅ Authentication flows

  E2E:
    ✅ Critical user journeys (register → upload video → publish)
    ✅ Payment flows
    ✅ Auth flows (login, logout, token refresh)
    ❌ NOT: every edge case (too slow, too brittle)

WHAT NOT TO TEST:
  ❌ Getters and setters with no logic
  ❌ Framework internals (React's useState works — trust it)
  ❌ Types (TypeScript catches these at compile time)
  ❌ Third-party library behavior
  ❌ Trivial pass-through functions
```

# STEP 2 — BACKEND UNIT TESTS (SERVICES)

```typescript
// services/__tests__/video.service.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { VideoService } from '../video.service'
import { VideoRepository } from '@/repositories/video.repository'
import { NotificationService } from '@/services/notification.service'

// MOCK DEPENDENCIES — don't hit real DB in unit tests
vi.mock('@/repositories/video.repository')
vi.mock('@/services/notification.service')

describe('VideoService', () => {
  let service: VideoService
  let mockVideoRepo: vi.Mocked<VideoRepository>
  let mockNotifService: vi.Mocked<NotificationService>

  beforeEach(() => {
    mockVideoRepo = new VideoRepository() as vi.Mocked<VideoRepository>
    mockNotifService = new NotificationService() as vi.Mocked<NotificationService>
    service = new VideoService(mockVideoRepo, mockNotifService)
    vi.clearAllMocks()
  })

  describe('createVideo', () => {
    it('creates a video in processing state', async () => {
      const userId = 'user-123'
      const input = { title: 'My Video', description: 'Cool video', storageKey: 'videos/raw.mp4' }
      const createdVideo = { id: 'video-456', ...input, status: 'processing' }

      mockVideoRepo.findUserChannel.mockResolvedValue({ id: 'channel-789', owner_id: userId })
      mockVideoRepo.create.mockResolvedValue(createdVideo)

      const result = await service.createVideo(userId, input)

      expect(result).toEqual(createdVideo)
      expect(mockVideoRepo.create).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'processing', title: 'My Video' })
      )
    })

    it('throws ForbiddenError if user is banned', async () => {
      mockVideoRepo.findUserChannel.mockResolvedValue(null)  // banned users have no channel
      
      await expect(service.createVideo('banned-user', {}))
        .rejects.toThrow('ForbiddenError')
    })

    it('enqueues transcoding job after creation', async () => {
      const mockEnqueue = vi.spyOn(transcodeQueue, 'add').mockResolvedValue({} as any)
      mockVideoRepo.findUserChannel.mockResolvedValue({ id: 'ch-1', owner_id: 'u-1' })
      mockVideoRepo.create.mockResolvedValue({ id: 'v-1', status: 'processing' })

      await service.createVideo('u-1', { storageKey: 'raw.mp4' })

      expect(mockEnqueue).toHaveBeenCalledWith('transcode', expect.objectContaining({ videoId: 'v-1' }))
    })
  })

  describe('listVideos', () => {
    it('enforces max limit of 100', async () => {
      mockVideoRepo.findMany.mockResolvedValue({ videos: [], total: 0 })
      await service.listVideos({ limit: '9999' })
      expect(mockVideoRepo.findMany).toHaveBeenCalledWith(expect.objectContaining({ limit: 100 }))
    })

    it('returns correct pagination metadata', async () => {
      mockVideoRepo.findMany.mockResolvedValue({ videos: new Array(20), total: 50 })
      const result = await service.listVideos({ page: '1', limit: '20' })
      expect(result.pagination).toEqual({ page: 1, limit: 20, total: 50, has_next: true })
    })
  })
})
```

# STEP 3 — INTEGRATION TESTS (API ENDPOINTS)

```typescript
// routes/__tests__/video.routes.test.ts
import request from 'supertest'
import { createApp } from '@/app'
import { db } from '@/config/database'
import { createTestUser, createTestVideo, generateTestToken } from '../helpers/factories'

describe('GET /api/v1/videos', () => {
  let app: Express

  beforeAll(async () => {
    app = createApp()
    await db.migrate.latest()  // run migrations on test DB
  })

  beforeEach(async () => {
    await db.seed.run(['test'])  // seed minimal test data
  })

  afterAll(async () => {
    await db.destroy()
  })

  it('returns paginated list of public videos', async () => {
    const channel = await createTestUser()
    await createTestVideo({ channel_id: channel.id, status: 'ready', visibility: 'public' })
    await createTestVideo({ channel_id: channel.id, status: 'ready', visibility: 'public' })

    const res = await request(app).get('/api/v1/videos').expect(200)

    expect(res.body.data).toHaveLength(2)
    expect(res.body.meta.pagination).toMatchObject({ page: 1, has_next: false })
  })

  it('excludes private and processing videos from public feed', async () => {
    const channel = await createTestUser()
    await createTestVideo({ channel_id: channel.id, status: 'processing' })
    await createTestVideo({ channel_id: channel.id, status: 'ready', visibility: 'private' })

    const res = await request(app).get('/api/v1/videos').expect(200)

    expect(res.body.data).toHaveLength(0)
  })
})

describe('POST /api/v1/videos', () => {
  it('requires authentication', async () => {
    await request(app).post('/api/v1/videos').send({ title: 'Test' }).expect(401)
  })

  it('creates a video for authenticated creator', async () => {
    const { user, token } = await createTestUser({ role: 'creator' })

    const res = await request(app)
      .post('/api/v1/videos')
      .set('Authorization', `Bearer ${token}`)
      .send({ title: 'My Video', description: 'Cool', visibility: 'public' })
      .expect(201)

    expect(res.body.data).toMatchObject({ title: 'My Video', status: 'processing' })
    expect(res.body.data.id).toBeDefined()
  })

  it('returns 422 for missing title', async () => {
    const { token } = await createTestUser({ role: 'creator' })

    const res = await request(app)
      .post('/api/v1/videos')
      .set('Authorization', `Bearer ${token}`)
      .send({})
      .expect(422)

    expect(res.body.error.code).toBe('VALIDATION_ERROR')
    expect(res.body.error.details).toContainEqual(
      expect.objectContaining({ field: 'title' })
    )
  })
})
```

# STEP 4 — FRONTEND COMPONENT TESTS (REACT TESTING LIBRARY)

```typescript
// components/features/VideoCard/__tests__/VideoCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { VideoCard } from '../VideoCard'

const mockVideo = {
  id: 'v-123',
  title: 'How to Code',
  thumbnail_url: 'https://cdn.example.com/thumb.jpg',
  view_count: 12500,
  channel: { name: 'Dev Channel', avatar_url: null },
  published_at: '2024-01-15T00:00:00Z',
}

describe('VideoCard', () => {
  it('renders video title and channel name', () => {
    render(<VideoCard video={mockVideo} />)
    expect(screen.getByText('How to Code')).toBeInTheDocument()
    expect(screen.getByText('Dev Channel')).toBeInTheDocument()
  })

  it('formats view count with abbreviation', () => {
    render(<VideoCard video={mockVideo} />)
    expect(screen.getByText('12.5K views')).toBeInTheDocument()
  })

  it('calls onLike when like button clicked', () => {
    const onLike = vi.fn()
    render(<VideoCard video={mockVideo} onLike={onLike} />)
    fireEvent.click(screen.getByRole('button', { name: /like/i }))
    expect(onLike).toHaveBeenCalledWith('v-123')
  })

  it('does not render like button when onLike not provided', () => {
    render(<VideoCard video={mockVideo} />)
    expect(screen.queryByRole('button', { name: /like/i })).not.toBeInTheDocument()
  })
})

// HOOKS TESTING:
import { renderHook, waitFor } from '@testing-library/react'
import { useDebounce } from '../useDebounce'

describe('useDebounce', () => {
  it('returns debounced value after delay', async () => {
    vi.useFakeTimers()
    const { result, rerender } = renderHook(({ value }) => useDebounce(value, 300), {
      initialProps: { value: 'initial' }
    })

    rerender({ value: 'updated' })
    expect(result.current).toBe('initial')  // not yet debounced

    vi.advanceTimersByTime(300)
    await waitFor(() => expect(result.current).toBe('updated'))
    vi.useRealTimers()
  })
})
```

# STEP 5 — E2E TESTS (PLAYWRIGHT)

```typescript
// e2e/video-upload.spec.ts
import { test, expect } from '@playwright/test'
import { loginAs, seedDatabase } from './helpers'

test.describe('Video Upload Journey', () => {
  test.beforeEach(async ({ page }) => {
    await seedDatabase('creator-with-channel')
    await loginAs(page, 'creator@test.com')
  })

  test('creator can upload and publish a video', async ({ page }) => {
    // Navigate to upload page
    await page.goto('/upload')
    
    // Fill in video details
    await page.getByLabel('Title').fill('My Test Video')
    await page.getByLabel('Description').fill('A description')
    
    // Upload file
    await page.getByLabel('Video file').setInputFiles('./fixtures/test-video.mp4')
    await expect(page.getByRole('progressbar')).toBeVisible()
    await expect(page.getByText('Upload complete')).toBeVisible({ timeout: 30_000 })
    
    // Publish
    await page.getByRole('button', { name: 'Publish' }).click()
    
    // Assert redirect to video page
    await expect(page).toHaveURL(/\/watch\//)
    await expect(page.getByText('My Test Video')).toBeVisible()
  })

  test('shows error for oversized files', async ({ page }) => {
    await page.goto('/upload')
    // Set a file that exceeds the 10GB limit (mocked at test level)
    // ... assert error message
  })
})

test.describe('Authentication', () => {
  test('redirects to login when accessing protected page', async ({ page }) => {
    await page.goto('/upload')
    await expect(page).toHaveURL('/login?redirect=/upload')
  })

  test('persists session after page reload', async ({ page }) => {
    await loginAs(page, 'viewer@test.com')
    await page.reload()
    await expect(page.getByText('viewer@test.com')).toBeVisible()
  })
})
```

# STEP 6 — TEST CONFIGURATION

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      include: ['src/services/**', 'src/lib/**'],  // only where logic lives
      exclude: ['src/routes/**', 'src/types/**'],   // skip pass-through files
      thresholds: {
        lines:     80,
        functions: 80,
        branches:  70,
      }
    }
  }
})

// src/test/setup.ts — global test setup
import { beforeAll, afterAll, beforeEach } from 'vitest'

beforeAll(async () => {
  process.env.DATABASE_URL = 'postgresql://localhost:5432/test_db'
  await runMigrations()
})

beforeEach(async () => {
  await truncateAllTables()  // clean slate before each test
})

afterAll(async () => {
  await closeDbConnection()
})
```

# CHECKLIST — Before Moving to Performance

```
✅ Unit tests for all service layer methods (happy path + error cases)
✅ Integration tests for all API endpoints (auth, validation, success, 404)
✅ Component tests for all UI components (render, interaction, edge cases)
✅ E2E tests for 3-5 critical user journeys
✅ Test database configured (separate from dev, wiped between tests)
✅ Factory helpers for creating test fixtures (avoid duplication)
✅ Coverage thresholds enforced in CI (80% on service layer)
✅ Tests run in under 2 minutes (fast = developers run them)
✅ No tests that depend on order or shared state between tests
→ NEXT: 10-PerformanceOptimization.md
```
