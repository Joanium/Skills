---
name: Prisma ORM
trigger: prisma, prisma schema, prisma client, prisma migrate, prisma query, prisma relation, prisma typescript, prisma findMany, prisma where, prisma include, prisma transaction, prisma middleware, prisma seed, prisma studio, prisma postgresql
description: Use Prisma ORM effectively — schema design, type-safe queries, relations, migrations, transactions, performance patterns, and common pitfalls in Node.js/TypeScript applications.
---

# ROLE
You are a senior full-stack TypeScript engineer who treats the Prisma schema as the source of truth for your data layer. You write type-safe, efficient queries and understand Prisma's tradeoffs.

# SCHEMA DESIGN

## Full Schema Example
```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id        String   @id @default(cuid())    // cuid2 for collision resistance
  email     String   @unique
  name      String
  role      Role     @default(USER)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt               // auto-updates on every write

  // Relations
  posts     Post[]
  profile   Profile?                          // optional 1-1
  sessions  Session[]

  @@map("users")                              // table name in DB
}

model Profile {
  id     String  @id @default(cuid())
  bio    String?
  avatar String?
  userId String  @unique                      // FK, unique = 1-1 relation

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@map("profiles")
}

model Post {
  id          String    @id @default(cuid())
  title       String
  content     String
  published   Boolean   @default(false)
  publishedAt DateTime?
  authorId    String

  author   User       @relation(fields: [authorId], references: [id])
  tags     Tag[]      @relation("PostToTag")  // implicit M2M
  comments Comment[]

  @@index([authorId])                         // always index FKs
  @@index([published, publishedAt])           // compound index for common filter
  @@map("posts")
}

// Implicit Many-to-Many — Prisma manages junction table automatically
model Tag {
  id    String @id @default(cuid())
  name  String @unique
  posts Post[] @relation("PostToTag")

  @@map("tags")
}

// Explicit Many-to-Many — when you need extra data on the junction
model PostCategory {
  postId     String
  categoryId String
  assignedAt DateTime @default(now())
  assignedBy String

  post     Post     @relation(fields: [postId], references: [id])
  category Category @relation(fields: [categoryId], references: [id])

  @@id([postId, categoryId])    // composite primary key
  @@map("post_categories")
}

enum Role {
  USER
  ADMIN
  MODERATOR
}
```

# QUERIES — THE CORE PATTERNS

## CRUD
```typescript
import { PrismaClient } from '@prisma/client'
const prisma = new PrismaClient()

// CREATE
const user = await prisma.user.create({
  data: {
    name: 'Alice',
    email: 'alice@example.com',
    profile: {
      create: { bio: 'Engineer' }    // nested create
    }
  },
  include: { profile: true }          // return with relation
})

// READ
const user = await prisma.user.findUnique({
  where: { email: 'alice@example.com' }
})

const users = await prisma.user.findMany({
  where: {
    role: 'ADMIN',
    createdAt: { gte: new Date('2024-01-01') }
  },
  orderBy: { createdAt: 'desc' },
  take: 20,
  skip: 0,
  select: { id: true, name: true, email: true }  // select only needed fields
})

// UPDATE
const updated = await prisma.user.update({
  where: { id: userId },
  data: { name: 'Alice B.' }
})

// UPSERT
const user = await prisma.user.upsert({
  where: { email: 'alice@example.com' },
  update: { name: 'Alice B.' },
  create: { name: 'Alice', email: 'alice@example.com' }
})

// DELETE
await prisma.user.delete({ where: { id: userId } })

// DELETE MANY
const { count } = await prisma.post.deleteMany({
  where: { published: false, createdAt: { lt: thirtyDaysAgo } }
})
```

## Filtering
```typescript
// String filters
where: {
  name: { contains: 'ali', mode: 'insensitive' },   // ILIKE %ali%
  email: { startsWith: 'alice' },
  title: { not: { contains: 'draft' } }
}

// Number ranges
where: {
  price: { gte: 10, lte: 100 }
}

// Null checks
where: { publishedAt: null }          // IS NULL
where: { publishedAt: { not: null } } // IS NOT NULL

// Array: in / notIn
where: { role: { in: ['ADMIN', 'MODERATOR'] } }
where: { id: { notIn: blockedIds } }

// Relation filters
where: {
  posts: {
    some: { published: true }   // has at least one published post
  }
}
where: {
  posts: {
    every: { published: true }  // all posts are published
  }
}
where: {
  profile: { is: null }         // has no profile
}

// AND / OR / NOT
where: {
  OR: [
    { email: { contains: '@company.com' } },
    { role: 'ADMIN' }
  ],
  NOT: { role: 'BANNED' }
}
```

## Select vs Include
```typescript
// include — include full related model (adds JOIN)
const user = await prisma.user.findUnique({
  where: { id },
  include: {
    posts: {
      where: { published: true },
      orderBy: { createdAt: 'desc' },
      take: 5,
      include: { tags: true }     // nested include
    },
    profile: true
  }
})

// select — pick exactly which fields (more efficient)
const user = await prisma.user.findUnique({
  where: { id },
  select: {
    id: true,
    name: true,
    _count: { select: { posts: true } },   // count relation
    posts: {
      select: { id: true, title: true }
    }
  }
})
```

# TRANSACTIONS
```typescript
// Sequential transaction — all or nothing
const [user, post] = await prisma.$transaction([
  prisma.user.create({ data: { name: 'Alice', email: 'alice@ex.com' } }),
  prisma.post.create({ data: { title: 'Hello', authorId: '...' } })
])

// Interactive transaction — for conditional logic
const order = await prisma.$transaction(async (tx) => {
  // Check stock
  const item = await tx.item.findUnique({ where: { id: itemId } })
  if (!item || item.stock < quantity) throw new Error('Out of stock')

  // Decrement stock
  await tx.item.update({
    where: { id: itemId },
    data: { stock: { decrement: quantity } }
  })

  // Create order
  return tx.order.create({
    data: { userId, itemId, quantity, total: item.price * quantity }
  })
}, {
  maxWait: 5000,   // max time to acquire transaction
  timeout: 10000   // max transaction duration
})
```

# MIGRATIONS
```bash
# Create and apply migration
npx prisma migrate dev --name add_user_role

# Apply migrations in production (no interactive prompt)
npx prisma migrate deploy

# Check migration status
npx prisma migrate status

# Reset DB + re-run all migrations (dev only — destroys data)
npx prisma migrate reset

# Generate client after schema change
npx prisma generate
```

# SEEDING
```typescript
// prisma/seed.ts
import { PrismaClient } from '@prisma/client'
const prisma = new PrismaClient()

async function main() {
  await prisma.user.upsert({
    where: { email: 'admin@example.com' },
    update: {},
    create: {
      email: 'admin@example.com',
      name: 'Admin',
      role: 'ADMIN'
    }
  })
}

main()
  .catch(console.error)
  .finally(() => prisma.$disconnect())
```
```json
// package.json
"prisma": { "seed": "ts-node prisma/seed.ts" }
```
```bash
npx prisma db seed
```

# SINGLETON CLIENT (NODE.JS)
```typescript
// lib/prisma.ts — avoid multiple instances in dev (hot reload creates new clients)
import { PrismaClient } from '@prisma/client'

const globalForPrisma = global as unknown as { prisma: PrismaClient }

export const prisma = globalForPrisma.prisma ?? new PrismaClient({
  log: process.env.NODE_ENV === 'development'
    ? ['query', 'error', 'warn']
    : ['error']
})

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma
}
```

# PERFORMANCE PATTERNS
```typescript
// Add @@index in schema for any field you filter/sort on
@@index([authorId])
@@index([createdAt])
@@index([status, createdAt])   // compound for status + date filter

// Avoid N+1 — use include instead of looping
// ✗ N+1
const users = await prisma.user.findMany()
for (const user of users) {
  user.posts = await prisma.post.findMany({ where: { authorId: user.id } })
}

// ✓ Single query with JOIN
const users = await prisma.user.findMany({
  include: { posts: true }
})

// Pagination cursor-based (efficient on large datasets)
const users = await prisma.user.findMany({
  take: 20,
  skip: 1,                     // skip the cursor itself
  cursor: { id: lastUserId },
  orderBy: { id: 'asc' }
})
```

# COMMON MISTAKES TO AVOID
```
✗ Creating a new PrismaClient() in every request — use the singleton pattern
✗ Not adding @@index for foreign keys and commonly filtered fields
✗ Using findMany without take — full table scan on large tables
✗ Mixing select and include on the same relation
✗ Not using $transaction for operations that must be atomic
✗ Forgetting to run prisma generate after schema changes
✗ Using prisma migrate dev in production — use migrate deploy
✗ Returning raw Prisma models from API — map to DTOs to avoid leaking internals
```
