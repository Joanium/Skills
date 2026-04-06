---
name: TypeScript Advanced
trigger: typescript generics, utility types, typescript patterns, type inference, conditional types, mapped types, template literal types, discriminated unions, type guards, advanced typescript, strict typescript, satisfies operator, infer keyword
description: Write advanced TypeScript with confidence. Covers generics, utility types, conditional types, mapped types, discriminated unions, type guards, and real-world patterns for building fully type-safe applications.
---

# ROLE
You are a TypeScript expert. Your job is to write fully type-safe code with zero `any`, squeeze out every ounce of type inference, and design type systems that make invalid states unrepresentable. Good TypeScript means the compiler catches bugs, not runtime crashes.

# CORE PHILOSOPHY
```
NO any — use unknown, never, or generics instead
TYPE INFERENCE FIRST — annotate where inference fails, not everywhere
MAKE INVALID STATES UNREPRESENTABLE — model domain with discriminated unions
STRICT MODE ALWAYS — "strict": true in tsconfig is non-negotiable
TYPES DESCRIBE REALITY — don't lie to the compiler
```

# TSCONFIG — START HERE
```json
{
  "compilerOptions": {
    "strict": true,               // enables: noImplicitAny, strictNullChecks, etc.
    "noUncheckedIndexedAccess": true,  // arr[0] returns T | undefined
    "exactOptionalPropertyTypes": true, // { a?: string } ≠ { a: string | undefined }
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true,
    "moduleResolution": "bundler",
    "target": "ES2022",
    "lib": ["ES2022", "DOM"]
  }
}
```

# GENERICS

## Basic to Advanced
```typescript
// Basic generic — type parameter flows through
function identity<T>(value: T): T {
  return value
}

// Multiple type params
function pair<A, B>(a: A, b: B): [A, B] {
  return [a, b]
}

// Constrained generics — T must have specific shape
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key]
}

// Default type params
function createList<T = string>(): T[] {
  return []
}

// Generic with conditional return type
function parseJSON<T>(json: string): T extends object ? T : never {
  return JSON.parse(json)
}
```

## Generic Classes and Interfaces
```typescript
interface Repository<T, ID = string> {
  findById(id: ID): Promise<T | null>
  findAll(): Promise<T[]>
  save(entity: T): Promise<T>
  delete(id: ID): Promise<void>
}

class UserRepository implements Repository<User> {
  async findById(id: string): Promise<User | null> { /* ... */ }
  async findAll(): Promise<User[]> { /* ... */ }
  async save(user: User): Promise<User> { /* ... */ }
  async delete(id: string): Promise<void> { /* ... */ }
}
```

# UTILITY TYPES — KNOW ALL OF THEM

## Built-in Utilities
```typescript
interface User {
  id: string
  name: string
  email: string
  role: 'admin' | 'user'
  createdAt: Date
}

// Partial<T> — all fields optional
type UpdateUserDto = Partial<User>
// { id?: string; name?: string; email?: string; ... }

// Required<T> — all fields required (reverse of Partial)
type FullUser = Required<Partial<User>>

// Pick<T, K> — select specific keys
type UserPublic = Pick<User, 'id' | 'name' | 'email'>

// Omit<T, K> — exclude specific keys
type CreateUserDto = Omit<User, 'id' | 'createdAt'>

// Readonly<T> — all fields readonly
type FrozenUser = Readonly<User>

// Record<K, V> — object type with specific keys and values
type RolePermissions = Record<User['role'], string[]>
// { admin: string[]; user: string[] }

// Exclude<T, U> — remove from union
type NonAdmin = Exclude<User['role'], 'admin'>  // 'user'

// Extract<T, U> — keep matching union members
type AdminOnly = Extract<User['role'], 'admin'>  // 'admin'

// NonNullable<T> — remove null and undefined
type DefiniteString = NonNullable<string | null | undefined>  // string

// ReturnType<T> — extract function return type
async function fetchUser(id: string): Promise<User> { /* ... */ }
type FetchResult = ReturnType<typeof fetchUser>  // Promise<User>
type AwaitedUser = Awaited<FetchResult>          // User

// Parameters<T> — extract function params as tuple
type FetchParams = Parameters<typeof fetchUser>  // [id: string]

// ConstructorParameters<T>
class ApiClient {
  constructor(baseUrl: string, timeout: number) {}
}
type ClientArgs = ConstructorParameters<typeof ApiClient>  // [string, number]

// InstanceType<T>
type ClientInstance = InstanceType<typeof ApiClient>  // ApiClient
```

# CONDITIONAL TYPES
```typescript
// Basic conditional type
type IsString<T> = T extends string ? true : false
type A = IsString<string>   // true
type B = IsString<number>   // false

// Infer — extract types from other types
type UnwrapPromise<T> = T extends Promise<infer U> ? U : T
type UnwrapArray<T> = T extends Array<infer U> ? U : T

type Resolved = UnwrapPromise<Promise<User>>  // User
type Item = UnwrapArray<User[]>               // User

// Extract function return type manually (same as ReturnType)
type MyReturnType<T> = T extends (...args: any[]) => infer R ? R : never

// Deep unwrap
type DeepUnwrap<T> = T extends Promise<infer U> ? DeepUnwrap<U> : T
type D = DeepUnwrap<Promise<Promise<Promise<string>>>>  // string

// Distributive conditional types — apply to each union member
type ToArray<T> = T extends any ? T[] : never
type StringOrNumber = ToArray<string | number>  // string[] | number[]
// NOT (string | number)[] — distributes over each member

// Prevent distribution with brackets
type ToArraySingle<T> = [T] extends [any] ? T[] : never
type S = ToArraySingle<string | number>  // (string | number)[]
```

# MAPPED TYPES
```typescript
// Basic mapped type
type Nullable<T> = {
  [K in keyof T]: T[K] | null
}

// Modifiers — add/remove optional and readonly
type Mutable<T> = {
  -readonly [K in keyof T]: T[K]  // remove readonly
}

type Complete<T> = {
  [K in keyof T]-?: T[K]  // remove optional (same as Required)
}

// Remapping keys with as
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K]
}
type UserGetters = Getters<Pick<User, 'name' | 'email'>>
// { getName: () => string; getEmail: () => string }

// Filter keys by value type
type PickByValue<T, V> = {
  [K in keyof T as T[K] extends V ? K : never]: T[K]
}
type StringFields = PickByValue<User, string>
// { id: string; name: string; email: string }
```

# DISCRIMINATED UNIONS — MODEL STATE MACHINES
```typescript
// The pattern: a shared literal field (discriminant) distinguishes each variant
type RequestState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error }

function renderUser(state: RequestState<User>) {
  switch (state.status) {
    case 'idle':    return null
    case 'loading': return <Spinner />
    case 'success': return <UserCard user={state.data} />  // data is User here
    case 'error':   return <ErrorMsg error={state.error} /> // error is Error here
  }
  // TypeScript ensures exhaustive matching — add a new variant and it will error
}

// Exhaustive check helper
function assertNever(x: never): never {
  throw new Error(`Unexpected value: ${x}`)
}

// Real-world: API response
type ApiResult<T, E = string> =
  | { ok: true; data: T }
  | { ok: false; error: E; statusCode: number }

function handleResult<T>(result: ApiResult<T>): T {
  if (result.ok) return result.data        // T narrowed here
  throw new Error(`${result.statusCode}: ${result.error}`)  // string & number narrowed here
}
```

# TYPE GUARDS
```typescript
// typeof guard — primitives
function processInput(value: string | number) {
  if (typeof value === 'string') {
    return value.toUpperCase()  // string narrowed
  }
  return value.toFixed(2)  // number narrowed
}

// instanceof guard — class instances
function handleError(err: unknown) {
  if (err instanceof Error) {
    console.error(err.message)  // Error narrowed
  }
}

// in guard — object shape check
function isUser(obj: unknown): obj is User {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'email' in obj
  )
}

// Custom type predicate
function isAdmin(user: User): user is User & { role: 'admin' } {
  return user.role === 'admin'
}

// Assertion function (throws if invalid)
function assertIsString(val: unknown): asserts val is string {
  if (typeof val !== 'string') {
    throw new TypeError(`Expected string, got ${typeof val}`)
  }
}

// unknown vs any — always prefer unknown
function safeProcess(data: unknown) {
  // data: unknown — you must narrow before using
  if (typeof data === 'string') { /* ok */ }
  // data.toUpperCase()  ← compile error. Good!
}
function unsafeProcess(data: any) {
  data.toUpperCase()  // compiles but might crash at runtime. Bad!
}
```

# TEMPLATE LITERAL TYPES
```typescript
type EventName = 'click' | 'focus' | 'blur'
type Handler = `on${Capitalize<EventName>}`
// 'onClick' | 'onFocus' | 'onBlur'

type CSSUnit = 'px' | 'rem' | 'em' | '%'
type CSSValue = `${number}${CSSUnit}`

type Route = '/users' | '/posts' | '/comments'
type ApiRoute = `/api/v1${Route}`
// '/api/v1/users' | '/api/v1/posts' | '/api/v1/comments'

// Strongly typed event emitter
type EventMap = {
  'user:created': User
  'user:deleted': { id: string }
  'post:published': { postId: string; authorId: string }
}

declare function emit<K extends keyof EventMap>(event: K, payload: EventMap[K]): void
declare function on<K extends keyof EventMap>(event: K, handler: (payload: EventMap[K]) => void): void

emit('user:created', { id: '1', name: 'Alice', email: 'a@b.com', role: 'user', createdAt: new Date() })
emit('user:created', { wrong: 'shape' })  // ← compile error
```

# THE satisfies OPERATOR (TS 4.9+)
```typescript
// Problem: type annotation loses literal types
const config: Record<string, string> = {
  apiUrl: 'https://api.example.com',
  timeout: '3000'
}
config.apiUrl  // type is string, not 'https://api.example.com'

// satisfies: validates shape but preserves literal types
const config2 = {
  apiUrl: 'https://api.example.com',
  timeout: '3000'
} satisfies Record<string, string>

config2.apiUrl  // type is 'https://api.example.com' — preserved!

// Real-world use: route definitions
type RouteConfig = {
  path: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  auth: boolean
}

const routes = {
  getUsers:  { path: '/users', method: 'GET',  auth: false },
  createUser: { path: '/users', method: 'POST', auth: true  },
} satisfies Record<string, RouteConfig>

routes.getUsers.method  // 'GET' — literal preserved, not 'GET' | 'POST' | ...
```

# COMMON PATTERNS

## Builder Pattern with Method Chaining
```typescript
class QueryBuilder<T> {
  private conditions: string[] = []
  private limitValue?: number

  where(condition: string): this {
    this.conditions.push(condition)
    return this
  }

  limit(n: number): this {
    this.limitValue = n
    return this
  }

  build(): string {
    let query = 'SELECT * FROM table'
    if (this.conditions.length) query += ` WHERE ${this.conditions.join(' AND ')}`
    if (this.limitValue) query += ` LIMIT ${this.limitValue}`
    return query
  }
}

const query = new QueryBuilder<User>()
  .where('role = "admin"')
  .where('active = true')
  .limit(10)
  .build()
```

## Branded Types — Prevent Mixing Up Same-Shaped Values
```typescript
type UserId = string & { readonly __brand: 'UserId' }
type PostId = string & { readonly __brand: 'PostId' }

function createUserId(id: string): UserId {
  return id as UserId
}

function getUser(id: UserId): User { /* ... */ }
function getPost(id: PostId): Post { /* ... */ }

const userId = createUserId('usr_123')
const postId = 'post_456' as PostId

getUser(userId)   // ✓
getUser(postId)   // ✗ compile error — can't mix up IDs
```
