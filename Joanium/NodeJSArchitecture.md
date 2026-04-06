---
name: Node.js Architecture
trigger: node.js architecture, express architecture, fastify, node.js project structure, node.js patterns, dependency injection, service layer, repository pattern, middleware, node.js best practices, clean architecture node, node streams, node cluster, node.js performance
description: Structure scalable Node.js applications. Covers layered architecture (routes → controllers → services → repositories), dependency injection, middleware composition, error handling, streams, cluster mode, and project layout patterns for Express and Fastify.
---

# ROLE
You are a Node.js backend architect. Your job is to build server applications that are maintainable, testable, and performant. Good Node.js architecture separates concerns cleanly, handles errors consistently, and takes advantage of the event loop.

# PROJECT STRUCTURE

## Layered Architecture
```
src/
├── server.ts              → Express/Fastify setup, middleware registration
├── app.ts                 → Application factory (for testing)
├── config/
│   ├── index.ts           → All config from env vars
│   └── database.ts        → DB connection setup
├── routes/
│   ├── index.ts           → Register all routes
│   ├── users.routes.ts    → Route definitions (thin — just define endpoints)
│   └── posts.routes.ts
├── controllers/
│   ├── users.controller.ts → Parse request, call service, format response
│   └── posts.controller.ts
├── services/
│   ├── users.service.ts    → Business logic (no HTTP, no DB queries)
│   └── posts.service.ts
├── repositories/
│   ├── users.repository.ts → DB queries only
│   └── posts.repository.ts
├── middleware/
│   ├── auth.ts            → JWT verification
│   ├── validate.ts        → Zod/Joi request validation
│   └── error-handler.ts   → Global error handler
├── lib/
│   ├── db.ts              → Prisma/Knex/pg client
│   ├── redis.ts           → Redis client
│   └── mailer.ts          → Email client
├── types/
│   └── index.ts           → Shared TypeScript types
└── utils/
    └── errors.ts          → Custom error classes
```

## Config from Environment (Type-Safe)
```typescript
// config/index.ts
import { z } from 'zod'

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.coerce.number().default(3000),
  DATABASE_URL: z.string().url(),
  REDIS_URL: z.string().url(),
  JWT_ACCESS_SECRET: z.string().min(32),
  JWT_REFRESH_SECRET: z.string().min(32),
  SENDGRID_API_KEY: z.string().optional(),
  AWS_REGION: z.string().default('us-east-1'),
  S3_BUCKET: z.string().optional(),
})

const parsed = envSchema.safeParse(process.env)

if (!parsed.success) {
  console.error('Invalid environment variables:', parsed.error.flatten().fieldErrors)
  process.exit(1)
}

export const config = parsed.data
// Now: config.DATABASE_URL is typed as string (not string | undefined)
```

# LAYERED ARCHITECTURE IN CODE

## Repository Layer — DB Queries Only
```typescript
// repositories/users.repository.ts
import { db } from '../lib/db'
import { User, CreateUserDto, UpdateUserDto } from '../types'

export class UserRepository {
  async findById(id: string): Promise<User | null> {
    return db.query.users.findFirst({ where: eq(users.id, id) })
  }

  async findByEmail(email: string): Promise<User | null> {
    return db.query.users.findFirst({ where: eq(users.email, email) })
  }

  async create(data: CreateUserDto): Promise<User> {
    const [user] = await db.insert(users).values(data).returning()
    return user
  }

  async update(id: string, data: UpdateUserDto): Promise<User | null> {
    const [updated] = await db.update(users)
      .set({ ...data, updatedAt: new Date() })
      .where(eq(users.id, id))
      .returning()
    return updated ?? null
  }

  async delete(id: string): Promise<boolean> {
    const result = await db.delete(users).where(eq(users.id, id))
    return result.rowCount > 0
  }
}
```

## Service Layer — Business Logic
```typescript
// services/users.service.ts
import { UserRepository } from '../repositories/users.repository'
import { hashPassword, verifyPassword } from '../utils/crypto'
import { AppError } from '../utils/errors'

export class UserService {
  constructor(private repo: UserRepository) {}

  async createUser(data: { name: string; email: string; password: string }) {
    // Business rule: check for duplicate email
    const existing = await this.repo.findByEmail(data.email)
    if (existing) throw new AppError('EMAIL_TAKEN', 'Email already registered', 409)

    const passwordHash = await hashPassword(data.password)
    return this.repo.create({ ...data, passwordHash })
  }

  async authenticate(email: string, password: string) {
    const user = await this.repo.findByEmail(email)
    // Same error for both cases — don't reveal if email exists
    if (!user) throw new AppError('INVALID_CREDENTIALS', 'Invalid credentials', 401)

    const valid = await verifyPassword(password, user.passwordHash)
    if (!valid) throw new AppError('INVALID_CREDENTIALS', 'Invalid credentials', 401)

    return user
  }

  async updateProfile(userId: string, requesterId: string, data: UpdateProfileDto) {
    if (userId !== requesterId) {
      throw new AppError('FORBIDDEN', 'Cannot update another user\'s profile', 403)
    }

    const updated = await this.repo.update(userId, data)
    if (!updated) throw new AppError('NOT_FOUND', 'User not found', 404)

    return updated
  }
}
```

## Controller Layer — HTTP Handling
```typescript
// controllers/users.controller.ts
import { Request, Response, NextFunction } from 'express'
import { UserService } from '../services/users.service'

export class UserController {
  constructor(private service: UserService) {}

  getProfile = async (req: Request, res: Response, next: NextFunction) => {
    try {
      const user = await this.service.getUser(req.params.id)
      res.json({ data: user })
    } catch (err) {
      next(err)
    }
  }

  updateProfile = async (req: Request, res: Response, next: NextFunction) => {
    try {
      const updated = await this.service.updateProfile(
        req.params.id,
        req.user!.userId,
        req.body
      )
      res.json({ data: updated })
    } catch (err) {
      next(err)
    }
  }
}
```

## Routes — Thin, Just Wire Things Up
```typescript
// routes/users.routes.ts
import { Router } from 'express'
import { UserController } from '../controllers/users.controller'
import { requireAuth } from '../middleware/auth'
import { validate } from '../middleware/validate'
import { updateProfileSchema } from '../schemas/users.schema'

export function createUserRoutes(controller: UserController): Router {
  const router = Router()

  router.get('/:id', requireAuth, controller.getProfile)
  router.patch('/:id', requireAuth, validate(updateProfileSchema), controller.updateProfile)

  return router
}
```

# ERROR HANDLING

## Custom Error Classes
```typescript
// utils/errors.ts
export class AppError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly statusCode: number = 500,
    public readonly isOperational = true   // false = programmer error (don't expose)
  ) {
    super(message)
    this.name = 'AppError'
    Error.captureStackTrace(this, this.constructor)
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string) {
    super('NOT_FOUND', `${resource} not found`, 404)
  }
}

export class ValidationError extends AppError {
  constructor(
    message: string,
    public readonly details: Array<{ field: string; message: string }>
  ) {
    super('VALIDATION_ERROR', message, 422)
  }
}
```

## Global Error Handler
```typescript
// middleware/error-handler.ts
import { Request, Response, NextFunction } from 'express'
import { AppError } from '../utils/errors'
import { ZodError } from 'zod'

export function errorHandler(err: Error, req: Request, res: Response, next: NextFunction) {
  // Zod validation errors
  if (err instanceof ZodError) {
    return res.status(422).json({
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Request validation failed',
        details: err.errors.map(e => ({ field: e.path.join('.'), message: e.message }))
      }
    })
  }

  // Our operational errors (expected failures)
  if (err instanceof AppError && err.isOperational) {
    return res.status(err.statusCode).json({
      error: { code: err.code, message: err.message }
    })
  }

  // Unexpected programming errors — log everything, don't expose internals
  console.error('UNHANDLED ERROR:', {
    message: err.message,
    stack: err.stack,
    url: req.url,
    method: req.method,
    userId: req.user?.userId,
  })

  res.status(500).json({
    error: { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred' }
  })
}

// Wrap async route handlers to forward errors to error handler
export const asyncHandler = (fn: Function) =>
  (req: Request, res: Response, next: NextFunction) =>
    Promise.resolve(fn(req, res, next)).catch(next)
```

# REQUEST VALIDATION WITH ZOD
```typescript
// middleware/validate.ts
import { Request, Response, NextFunction } from 'express'
import { AnyZodObject, z } from 'zod'

export function validate(schema: AnyZodObject) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      // Validate and replace req.body, req.query, req.params with parsed values
      const parsed = await schema.parseAsync({
        body: req.body,
        query: req.query,
        params: req.params,
      })
      req.body   = parsed.body   ?? req.body
      req.query  = parsed.query  ?? req.query
      req.params = parsed.params ?? req.params
      next()
    } catch (err) {
      next(err)
    }
  }
}

// schemas/users.schema.ts
export const updateProfileSchema = z.object({
  body: z.object({
    name:  z.string().min(1).max(100).optional(),
    bio:   z.string().max(500).optional(),
    avatar: z.string().url().optional(),
  }),
  params: z.object({
    id: z.string().uuid()
  })
})
```

# DEPENDENCY INJECTION
```typescript
// Simple manual DI (sufficient for most apps)
// app.ts

import { db } from './lib/db'
import { UserRepository } from './repositories/users.repository'
import { UserService } from './services/users.service'
import { UserController } from './controllers/users.controller'
import { createUserRoutes } from './routes/users.routes'

export function createApp() {
  const app = express()
  app.use(express.json())

  // Wire dependencies
  const userRepo = new UserRepository(db)
  const userService = new UserService(userRepo)
  const userController = new UserController(userService)

  // Register routes
  app.use('/api/users', createUserRoutes(userController))

  // Error handler MUST be last
  app.use(errorHandler)

  return app
}

// In tests — swap real implementations for mocks
const mockRepo = { findById: jest.fn(), /* ... */ }
const testService = new UserService(mockRepo)
```

# NODE.JS PERFORMANCE

## Streams for Large Data
```typescript
import { Transform, pipeline } from 'stream'
import { promisify } from 'util'
const pipelineAsync = promisify(pipeline)

// Export 1M rows without loading into memory
app.get('/export', async (req, res) => {
  res.setHeader('Content-Type', 'text/csv')
  res.setHeader('Content-Disposition', 'attachment; filename="export.csv"')

  // DB cursor → transform to CSV → response stream
  const dbStream = db.queryStream('SELECT * FROM orders WHERE user_id = $1', [req.user!.userId])

  const toCSV = new Transform({
    objectMode: true,
    transform(row, encoding, callback) {
      callback(null, Object.values(row).join(',') + '\n')
    }
  })

  await pipelineAsync(dbStream, toCSV, res)
})
```

## Worker Threads for CPU Work
```typescript
import { Worker, isMainThread, parentPort, workerData } from 'worker_threads'

// main-thread: offload CPU-intensive work
function runWorker(data: any): Promise<any> {
  return new Promise((resolve, reject) => {
    const worker = new Worker(__filename, { workerData: data })
    worker.on('message', resolve)
    worker.on('error', reject)
    worker.on('exit', code => {
      if (code !== 0) reject(new Error(`Worker exited with code ${code}`))
    })
  })
}

// worker thread
if (!isMainThread) {
  const result = heavyCPUWork(workerData)
  parentPort!.postMessage(result)
}

// Usage — doesn't block the event loop
app.post('/generate-report', async (req, res) => {
  const report = await runWorker({ filters: req.body })   // runs in separate thread
  res.json(report)
})
```

## Cluster Mode
```typescript
// cluster.ts — use all CPU cores
import cluster from 'cluster'
import os from 'os'
import { createApp } from './app'

if (cluster.isPrimary) {
  const numCPUs = os.cpus().length
  console.log(`Primary ${process.pid} running — forking ${numCPUs} workers`)

  for (let i = 0; i < numCPUs; i++) {
    cluster.fork()
  }

  cluster.on('exit', (worker, code) => {
    console.warn(`Worker ${worker.process.pid} died — restarting`)
    cluster.fork()
  })
} else {
  const app = createApp()
  app.listen(config.PORT, () => {
    console.log(`Worker ${process.pid} listening on :${config.PORT}`)
  })
}
```
