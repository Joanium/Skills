---
name: Backend Architecture
trigger: backend structure, server architecture, Node.js structure, Express setup, FastAPI structure, folder structure backend, middleware, service layer, repository pattern, MVC, clean architecture, controller service repository
description: Sixth skill in the build pipeline. Read after Frontend Architecture. Covers backend folder structure, layered architecture (controllers/services/repositories), middleware stack, dependency injection, and writing maintainable server-side code.
prev_skill: 05-FrontendArchitecture.md
next_skill: 07-AuthSecurity.md
---

# ROLE
You are a backend engineer who has seen what happens when business logic ends up in route handlers — unmaintainable, untestable spaghetti. You enforce a strict layered architecture that makes code easy to test, extend, and hand off to another developer.

# CORE PRINCIPLES
```
LAYER YOUR CODE: route handler → controller → service → repository → database
BUSINESS LOGIC LIVES IN THE SERVICE LAYER ONLY — never in controllers or DB queries
CONTROLLERS ARE THIN — validate input, call service, return response. That's it.
REPOSITORIES ABSTRACT THE DATABASE — services never write SQL directly
DEPENDENCY INJECTION OVER IMPORTS — makes code testable and swappable
FAIL FAST — validate at the edge, trust validated data deeper in the stack
ONE CONCERN PER FILE — a 500-line service file is a design failure
```

# STEP 1 — FOLDER STRUCTURE

```
src/
├── server.ts               # Express/Fastify app setup, start server
├── app.ts                  # App factory (middlewares, routes — no server.listen here)
│
├── config/
│   ├── env.ts              # Validated env vars (use zod to validate process.env)
│   ├── database.ts         # DB connection pool
│   └── redis.ts            # Redis client
│
├── routes/                 # HTTP routing layer only — no logic
│   ├── index.ts            # Mount all routers here
│   ├── auth.routes.ts
│   ├── video.routes.ts
│   └── user.routes.ts
│
├── controllers/            # Input validation + calling services + formatting response
│   ├── auth.controller.ts
│   ├── video.controller.ts
│   └── user.controller.ts
│
├── services/               # Business logic — the heart of the application
│   ├── auth.service.ts
│   ├── video.service.ts
│   ├── upload.service.ts
│   └── notification.service.ts
│
├── repositories/           # Database access — all SQL/ORM calls live here
│   ├── user.repository.ts
│   ├── video.repository.ts
│   └── comment.repository.ts
│
├── middleware/
│   ├── authenticate.ts     # JWT verification, attaches req.user
│   ├── authorize.ts        # Role-based access control
│   ├── validate.ts         # Zod request schema validation
│   ├── rateLimiter.ts      # Per-route rate limits
│   └── errorHandler.ts     # Global error handler (last middleware)
│
├── jobs/                   # Background workers
│   ├── transcode.job.ts    # Video transcoding worker
│   ├── email.job.ts        # Email sender worker
│   └── queue.ts            # BullMQ queue setup
│
├── lib/                    # Pure utilities (no Express/framework dependencies)
│   ├── logger.ts           # Pino/Winston logger
│   ├── storage.ts          # S3 client wrappers
│   ├── mailer.ts           # Email sending
│   ├── errors.ts           # Custom error classes
│   └── crypto.ts           # Hashing, token generation
│
└── types/
    ├── express.d.ts        # Augment req.user type
    └── index.ts            # Shared types
```

# STEP 2 — LAYERED ARCHITECTURE IN PRACTICE

```typescript
// ─── ROUTES — declare endpoints and middleware chain only ───────────────────
// routes/video.routes.ts
import { Router } from 'express'
import { authenticate } from '@/middleware/authenticate'
import { validate } from '@/middleware/validate'
import { VideoController } from '@/controllers/video.controller'
import { createVideoSchema, listVideosSchema } from '@/validators/video.validators'

const router = Router()
const ctrl = new VideoController()

router.get('/',      validate(listVideosSchema),  ctrl.list)
router.get('/:id',                                ctrl.getById)
router.post('/',     authenticate, validate(createVideoSchema), ctrl.create)
router.patch('/:id', authenticate,                ctrl.update)
router.delete('/:id',authenticate,                ctrl.delete)

export default router

// ─── CONTROLLER — thin layer: validate → service → respond ─────────────────
// controllers/video.controller.ts
export class VideoController {
  constructor(private videoService = new VideoService()) {}

  list = async (req: Request, res: Response, next: NextFunction) => {
    try {
      const result = await this.videoService.listVideos(req.query)
      res.json({ data: result.videos, meta: { pagination: result.pagination } })
    } catch (err) {
      next(err)  // always pass to error handler
    }
  }

  create = async (req: Request, res: Response, next: NextFunction) => {
    try {
      // req.body is already validated by validate() middleware
      const video = await this.videoService.createVideo(req.user!.id, req.body)
      res.status(201).json({ data: video })
    } catch (err) {
      next(err)
    }
  }
}

// ─── SERVICE — all business logic lives here ────────────────────────────────
// services/video.service.ts
export class VideoService {
  constructor(
    private videoRepo = new VideoRepository(),
    private notifService = new NotificationService(),
    private storageLib = storage,
  ) {}

  async createVideo(userId: string, input: CreateVideoInput) {
    // 1. Business rule: check user can create videos
    const user = await this.userRepo.findById(userId)
    if (user.is_banned) throw new ForbiddenError('Account suspended')

    // 2. Create video record in "processing" state
    const video = await this.videoRepo.create({
      channel_id: user.channel_id,
      title: input.title,
      description: input.description,
      status: 'processing',
    })

    // 3. Enqueue transcoding job (async — don't wait)
    await transcodeQueue.add('transcode', { videoId: video.id, storageKey: input.storageKey })

    // 4. Notify subscribers (async — don't wait)
    this.notifService.notifySubscribers(user.channel_id, video.id).catch(logger.error)

    return video
  }

  async listVideos(query: ListVideosQuery) {
    const { videos, total } = await this.videoRepo.findMany({
      channelId: query.channel_id,
      status: 'ready',
      visibility: 'public',
      page: Number(query.page) || 1,
      limit: Math.min(Number(query.limit) || 20, 100),
      sort: query.sort || 'latest',
    })

    return {
      videos,
      pagination: {
        page: Number(query.page) || 1,
        limit: Math.min(Number(query.limit) || 20, 100),
        total,
        has_next: total > (Number(query.page) || 1) * Math.min(Number(query.limit) || 20, 100),
      }
    }
  }
}

// ─── REPOSITORY — all database access, zero business logic ─────────────────
// repositories/video.repository.ts
export class VideoRepository {
  async create(data: CreateVideoData): Promise<Video> {
    return db.video.create({ data })  // Prisma example
  }

  async findById(id: string): Promise<Video | null> {
    return db.video.findUnique({ where: { id }, include: { channel: true, tags: true } })
  }

  async findMany(opts: FindVideosOpts): Promise<{ videos: Video[]; total: number }> {
    const where = {
      channel_id: opts.channelId,
      status:     opts.status,
      visibility: opts.visibility,
    }
    const [videos, total] = await Promise.all([
      db.video.findMany({
        where,
        skip:    (opts.page - 1) * opts.limit,
        take:    opts.limit,
        orderBy: opts.sort === 'latest' ? { published_at: 'desc' } : { view_count: 'desc' },
      }),
      db.video.count({ where }),
    ])
    return { videos, total }
  }
}
```

# STEP 3 — CUSTOM ERROR CLASSES

```typescript
// lib/errors.ts — centralized error hierarchy
export class AppError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly statusCode: number,
    public readonly details?: unknown,
  ) {
    super(message)
    this.name = this.constructor.name
  }
}

export class NotFoundError extends AppError {
  constructor(resource = 'Resource') {
    super('NOT_FOUND', `${resource} not found`, 404)
  }
}

export class ForbiddenError extends AppError {
  constructor(message = 'Forbidden') {
    super('FORBIDDEN', message, 403)
  }
}

export class ConflictError extends AppError {
  constructor(message = 'Conflict') {
    super('CONFLICT', message, 409)
  }
}

export class ValidationError extends AppError {
  constructor(details: { field: string; message: string }[]) {
    super('VALIDATION_ERROR', 'Validation failed', 422, details)
  }
}

// middleware/errorHandler.ts — global error handler (last Express middleware)
export function errorHandler(err: Error, req: Request, res: Response, next: NextFunction) {
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      error: { code: err.code, message: err.message, details: err.details }
    })
  }

  // Unexpected errors — log but don't leak internals
  logger.error({ err, req: { method: req.method, url: req.url } }, 'Unexpected error')
  res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred' } })
}
```

# STEP 4 — ENVIRONMENT AND CONFIG

```typescript
// config/env.ts — validate ALL environment variables at startup
import { z } from 'zod'

const envSchema = z.object({
  NODE_ENV:       z.enum(['development', 'test', 'production']),
  PORT:           z.string().default('3000').transform(Number),
  DATABASE_URL:   z.string().url(),
  REDIS_URL:      z.string().url(),
  JWT_SECRET:     z.string().min(32),
  S3_BUCKET:      z.string(),
  S3_REGION:      z.string(),
  AWS_ACCESS_KEY: z.string(),
  AWS_SECRET_KEY: z.string(),
})

const parsed = envSchema.safeParse(process.env)

if (!parsed.success) {
  console.error('Invalid environment variables:', parsed.error.flatten())
  process.exit(1)  // fail loudly at startup, not at runtime
}

export const env = parsed.data
// Usage everywhere: import { env } from '@/config/env' — never access process.env directly
```

# STEP 5 — MIDDLEWARE STACK ORDER

```typescript
// app.ts — correct middleware order matters
import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import rateLimit from 'express-rate-limit'
import { requestLogger } from './middleware/requestLogger'
import { errorHandler } from './middleware/errorHandler'

export function createApp() {
  const app = express()

  // 1. Security headers (before anything else)
  app.use(helmet())

  // 2. CORS (before routes)
  app.use(cors({ origin: process.env.ALLOWED_ORIGINS?.split(','), credentials: true }))

  // 3. Body parsing
  app.use(express.json({ limit: '10mb' }))

  // 4. Request logging
  app.use(requestLogger)

  // 5. Global rate limit (before routes)
  app.use(rateLimit({ windowMs: 60_000, max: 100, standardHeaders: true }))

  // 6. Routes
  app.use('/api/v1', routes)

  // 7. 404 handler (after all routes)
  app.use((req, res) => res.status(404).json({ error: { code: 'NOT_FOUND', message: 'Route not found' } }))

  // 8. Error handler (MUST be last, with 4 args)
  app.use(errorHandler)

  return app
}
```

# CHECKLIST — Before Moving to Auth & Security

```
✅ Folder structure created and committed to repo
✅ Routes → Controller → Service → Repository pattern established
✅ Custom error classes written and global error handler in place
✅ Environment validation at startup (app fails loudly on missing vars)
✅ Middleware stack defined in correct order
✅ No SQL or ORM calls outside repository files
✅ No HTTP request/response objects used in service layer
✅ Logger configured (Pino recommended — fastest Node.js logger)
→ NEXT: 07-AuthSecurity.md
```
