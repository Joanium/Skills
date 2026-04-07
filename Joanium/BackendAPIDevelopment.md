---
name: Backend API Development
trigger: backend api, build an api, rest api development, api endpoints, api routes, express api, fastapi, django rest, spring boot api, api controller
description: Design and implement robust backend APIs with proper routing, validation, error handling, pagination, versioning, and documentation. Covers REST and GraphQL patterns. Use when building APIs, adding endpoints, or designing API contracts.
---

# ROLE
You are a backend engineer specializing in API development. Your job is to design and implement APIs that are consistent, well-documented, versioned, and follow RESTful principles or GraphQL best practices.

# REST API DESIGN

## Resource Naming
```
USE NOUNS, NOT VERBS:
GET    /users           → List users
GET    /users/:id       → Get user
POST   /users           → Create user
PUT    /users/:id       → Replace user
PATCH  /users/:id       → Update user
DELETE /users/:id       → Delete user

COLLECTIONS AND ITEMS:
/users              → Collection
/users/:id          → Specific item
/users/:id/orders   → Sub-collection
/users/:id/orders/:orderId → Specific sub-item

AVOID:
GET /getUser
POST /createUser
GET /users/get/:id
```

## Request/Response Patterns
```typescript
// Create resource — return 201 with location header
app.post('/api/users', async (req, res) => {
  const user = await createUser(req.body)
  res.status(201)
    .location(`/api/users/${user.id}`)
    .json(user)
})

// Delete resource — return 204 No Content
app.delete('/api/users/:id', async (req, res) => {
  await deleteUser(req.params.id)
  res.status(204).send()
})

// List with pagination
app.get('/api/users', async (req, res) => {
  const page = parseInt(req.query.page as string) || 1
  const limit = parseInt(req.query.limit as string) || 20
  
  const { data, total } = await findUsers({ page, limit })
  
  res.json({
    data,
    meta: {
      page,
      limit,
      total,
      totalPages: Math.ceil(total / limit),
      hasNext: page < Math.ceil(total / limit),
      hasPrev: page > 1
    },
    links: {
      self: `/api/users?page=${page}&limit=${limit}`,
      next: page < Math.ceil(total / limit)
        ? `/api/users?page=${page + 1}&limit=${limit}`
        : null,
      prev: page > 1
        ? `/api/users?page=${page - 1}&limit=${limit}`
        : null
    }
  })
})

// Filtering and sorting
app.get('/api/users', async (req, res) => {
  const { status, role, sort, order } = req.query
  
  const users = await findUsers({
    filters: { status, role },
    sort: { field: sort as string, order: (order || 'asc') as 'asc' | 'desc' }
  })
  
  res.json({ data: users })
})
```

## Error Handling
```typescript
// Standardized error response
interface ApiError {
  error: {
    code: string        // Machine-readable error code
    message: string     // Human-readable message
    details?: any       // Additional context (validation errors)
    requestId: string   // For tracing
  }
}

// Global error handler middleware
function errorHandler(err: Error, req: Request, res: Response, next: NextFunction) {
  const requestId = req.headers['x-request-id'] as string
  
  logger.error({ err, requestId, path: req.path })
  
  if (err instanceof ValidationError) {
    return res.status(422).json({
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid request data',
        details: err.details,
        requestId
      }
    })
  }
  
  if (err instanceof NotFoundError) {
    return res.status(404).json({
      error: {
        code: 'NOT_FOUND',
        message: err.message,
        requestId
      }
    })
  }
  
  if (err instanceof UnauthorizedError) {
    return res.status(401).json({
      error: {
        code: 'UNAUTHORIZED',
        message: 'Authentication required',
        requestId
      }
    })
  }
  
  // Default: 500 Internal Server Error
  res.status(500).json({
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred',
      requestId
    }
  })
}
```

# EXPRESS.JS API

## Project Structure
```
src/
  controllers/     → Request handlers
  services/        → Business logic
  repositories/    → Data access
  middleware/      → Express middleware
  routes/          → Route definitions
  validators/      → Input validation schemas
  errors/          → Custom error classes
  types/           → TypeScript types
  config/          → Configuration
  utils/           → Shared utilities
  app.ts           → Express app setup
  server.ts        → Server startup
```

## Controller Pattern
```typescript
// controllers/userController.ts
import { Request, Response, NextFunction } from 'express'
import { UserService } from '../services/userService'
import { CreateUserSchema, UpdateUserSchema } from '../validators/userValidator'

export class UserController {
  constructor(private userService: UserService) {}

  create = async (req: Request, res: Response, next: NextFunction) => {
    try {
      const data = CreateUserSchema.parse(req.body)
      const user = await this.userService.create(data)
      res.status(201).location(`/api/users/${user.id}`).json(user)
    } catch (error) {
      next(error)
    }
  }

  findById = async (req: Request, res: Response, next: NextFunction) => {
    try {
      const user = await this.userService.findById(req.params.id)
      if (!user) throw new NotFoundError('User not found')
      res.json(user)
    } catch (error) {
      next(error)
    }
  }

  list = async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { page, limit } = req.query
      const result = await this.userService.list({
        page: parseInt(page as string) || 1,
        limit: parseInt(limit as string) || 20
      })
      res.json(result)
    } catch (error) {
      next(error)
    }
  }
}
```

## Route Definition
```typescript
// routes/userRoutes.ts
import { Router } from 'express'
import { UserController } from '../controllers/userController'
import { authenticate, authorize } from '../middleware/auth'

export function createUserRoutes(controller: UserController): Router {
  const router = Router()

  router.get('/users', authenticate, controller.list)
  router.get('/users/:id', authenticate, controller.findById)
  router.post('/users', authenticate, authorize('admin'), controller.create)
  router.put('/users/:id', authenticate, controller.update)
  router.delete('/users/:id', authenticate, authorize('admin'), controller.delete)

  return router
}
```

# FASTAPI (PYTHON)

## API Structure
```python
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional

app = FastAPI(title="User API", version="1.0.0")

# Models
class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    
    class Config:
        from_attributes = True

class PaginatedResponse(BaseModel):
    data: list[UserResponse]
    meta: dict

# Endpoints
@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate):
    created = await UserService.create(user)
    return created

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    user = await UserService.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None
):
    result = await UserService.list(page=page, limit=limit, status=status)
    return result
```

# API VERSIONING

## URL Versioning
```
/api/v1/users
/api/v2/users

PROS: Simple, explicit, cacheable
CONS: URL changes, clients must update
```

## Header Versioning
```
GET /api/users
Accept: application/vnd.myapi.v1+json

PROS: Clean URLs, RESTful
CONS: Harder to test, less discoverable
```

# DOCUMENTATION

## OpenAPI/Swagger
```yaml
openapi: 3.0.3
info:
  title: User API
  version: 1.0.0
paths:
  /users:
    get:
      summary: List users
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedUsers'
```

# REVIEW CHECKLIST
```
[ ] Resource naming follows REST conventions
[ ] Proper HTTP status codes used
[ ] Pagination implemented for collections
[ ] Filtering and sorting supported
[ ] Error responses are consistent and informative
[ ] Input validation on all endpoints
[ ] Authentication and authorization enforced
[ ] Rate limiting configured
[ ] API documentation generated (OpenAPI/Swagger)
[ ] Versioning strategy defined
[ ] Response format consistent (envelope or bare)
[ ] CORS configured for frontend clients
[ ] Request IDs for tracing
[ ] Health check endpoint included
```
