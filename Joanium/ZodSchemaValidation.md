---
name: Zod Schema Validation
trigger: zod, schema validation, input validation, zod schema, z.object, z.string, z.number, zod parse, zod safeParse, zod transform, zod refine, zod typescript, runtime validation, form validation zod, api validation zod, ajv, valibot, validation library
description: Validate, parse, and transform data with Zod. Covers schema composition, transforms, refinements, error handling, TypeScript inference, and patterns for API input, forms, and environment config validation.
---

# ROLE
You are a TypeScript engineer who treats "this data came from outside your codebase" as untrusted by default — whether it's API input, form data, localStorage, env vars, or database results. You use Zod to parse, not just validate: if it passes, you get back a correctly-typed value; if it fails, you get a structured error, not a runtime crash.

# CORE PHILOSOPHY
```
PARSE, DON'T VALIDATE:
  Validation: "is this data valid?" → returns true/false
  Parsing:    "give me this data or tell me exactly why you can't" → returns typed value or structured error

schema.parse(data)      → returns typed T or THROWS ZodError
schema.safeParse(data)  → returns { success: true, data: T } or { success: false, error: ZodError }
                          PREFER safeParse — never use parse where you'd need to try/catch

TYPE INFERENCE:
  Define schema once → get TypeScript type for free — no duplication
  type User = z.infer<typeof UserSchema>;
```

# PRIMITIVE SCHEMAS
```typescript
import { z } from 'zod';

// Primitives
const StringSchema = z.string();
const NumberSchema = z.number();
const BooleanSchema = z.boolean();
const DateSchema = z.date();
const NullSchema = z.null();
const UndefinedSchema = z.undefined();
const AnySchema = z.any();
const UnknownSchema = z.unknown();  // prefer over any — forces you to narrow

// Literal values
const StatusSchema = z.literal('active');
const PrioritySchema = z.union([z.literal(1), z.literal(2), z.literal(3)]);

// Enums
const RoleSchema = z.enum(['admin', 'editor', 'viewer']);
type Role = z.infer<typeof RoleSchema>;  // "admin" | "editor" | "viewer"

// Native enum
enum Direction { Up = 'UP', Down = 'DOWN' }
const DirectionSchema = z.nativeEnum(Direction);
```

# STRING VALIDATIONS
```typescript
const EmailSchema = z.string()
  .min(1, 'Email is required')
  .email('Must be a valid email')
  .max(255, 'Email too long')
  .toLowerCase()    // transform: normalize to lowercase
  .trim();          // transform: strip whitespace

const PasswordSchema = z.string()
  .min(8, 'Password must be at least 8 characters')
  .max(100, 'Password too long')
  .regex(/[A-Z]/, 'Must contain uppercase letter')
  .regex(/[0-9]/, 'Must contain a number');

const UrlSchema = z.string().url('Must be a valid URL');
const UuidSchema = z.string().uuid('Must be a valid UUID');
const CuidSchema = z.string().cuid();
const SlugSchema = z.string().regex(/^[a-z0-9-]+$/, 'Slug must be lowercase alphanumeric and hyphens');

// String coercion (from unknown input)
const NumericStringSchema = z.coerce.number();  // "42" → 42
const DateStringSchema = z.coerce.date();        // "2024-01-15" → Date object
```

# NUMBER VALIDATIONS
```typescript
const AgeSchema = z.number()
  .int('Age must be a whole number')
  .min(0, 'Age cannot be negative')
  .max(150, 'Age out of range');

const PriceSchema = z.number()
  .positive('Price must be positive')
  .multipleOf(0.01, 'Max 2 decimal places');

const PortSchema = z.number().int().min(1).max(65535);

// Coerce string to number (useful for query params — everything is string in URL)
const PageSchema = z.coerce.number().int().min(1).default(1);
const LimitSchema = z.coerce.number().int().min(1).max(100).default(20);
```

# OBJECT SCHEMAS
```typescript
const UserSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(100),
  email: z.string().email(),
  age: z.number().int().min(0).optional(),
  role: z.enum(['admin', 'user']).default('user'),
  createdAt: z.date().default(() => new Date()),
  metadata: z.record(z.string(), z.unknown()).optional()  // { [key: string]: unknown }
});

type User = z.infer<typeof UserSchema>;
// {
//   id: string;
//   name: string;
//   email: string;
//   age?: number;
//   role: "admin" | "user";
//   createdAt: Date;
//   metadata?: Record<string, unknown>;
// }

// Partial, Required, Pick, Omit
const UpdateUserSchema = UserSchema.partial();              // all fields optional
const RequiredUserSchema = UserSchema.required();           // all fields required
const PublicUserSchema = UserSchema.pick({ id: true, name: true, email: true });
const CreateUserSchema = UserSchema.omit({ id: true, createdAt: true });
```

## Strip Unknown Keys (Default) vs Passthrough vs Strict
```typescript
const schema = z.object({ name: z.string() });

schema.parse({ name: 'Alice', extra: 'field' });
// → { name: 'Alice' }  ← extra key stripped by default

schema.strict().parse({ name: 'Alice', extra: 'field' });
// → throws ZodError: "Unrecognized key: extra"

schema.passthrough().parse({ name: 'Alice', extra: 'field' });
// → { name: 'Alice', extra: 'field' }  ← unknown keys passed through
```

# ARRAY AND COLLECTION SCHEMAS
```typescript
const TagsSchema = z.array(z.string().min(1)).min(1).max(10);
const MatrixSchema = z.array(z.array(z.number()));

// Tuple (fixed-length array with specific types)
const CoordinateSchema = z.tuple([z.number(), z.number()]);
const CoordinateWithLabelSchema = z.tuple([z.number(), z.number()]).rest(z.string());

// Set and Map
const SetSchema = z.set(z.string());
const MapSchema = z.map(z.string(), z.number());

// Record (object with dynamic string keys)
const ScoresSchema = z.record(z.string(), z.number());  // { [userId: string]: number }
const ConfigSchema = z.record(z.string(), z.union([z.string(), z.number(), z.boolean()]));
```

# UNION AND DISCRIMINATED UNION
```typescript
// Simple union
const IdSchema = z.union([z.string().uuid(), z.number().int().positive()]);

// Discriminated union — much faster, better errors
const ShapeSchema = z.discriminatedUnion('type', [
  z.object({ type: z.literal('circle'), radius: z.number() }),
  z.object({ type: z.literal('rectangle'), width: z.number(), height: z.number() }),
  z.object({ type: z.literal('triangle'), base: z.number(), height: z.number() })
]);

type Shape = z.infer<typeof ShapeSchema>;
// { type: 'circle'; radius: number } | { type: 'rectangle'; width: number; height: number } | ...

const result = ShapeSchema.safeParse({ type: 'circle', radius: 5 });
// { success: true, data: { type: 'circle', radius: 5 } }
```

# TRANSFORMS AND REFINEMENTS

## .transform() — Change the Output Type
```typescript
// Parse a date string into a Date object
const DateStringSchema = z.string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, 'Must be YYYY-MM-DD')
  .transform(str => new Date(str));
// type: string → Date

// Parse comma-separated string into array
const TagsInputSchema = z.string()
  .transform(str => str.split(',').map(s => s.trim()).filter(Boolean));
// type: string → string[]

// Parse JSON string
const JsonStringSchema = z.string().transform((str, ctx) => {
  try {
    return JSON.parse(str);
  } catch {
    ctx.addIssue({ code: 'custom', message: 'Invalid JSON' });
    return z.NEVER;  // signals transform failed
  }
});
```

## .refine() — Custom Validation Logic
```typescript
// Cross-field validation
const DateRangeSchema = z.object({
  startDate: z.date(),
  endDate: z.date()
}).refine(data => data.endDate > data.startDate, {
  message: 'End date must be after start date',
  path: ['endDate']  // attach error to specific field
});

// Async refinement (check uniqueness in DB)
const CreateUserSchema = z.object({
  email: z.string().email()
}).superRefine(async (data, ctx) => {
  const existing = await db.user.findUnique({ where: { email: data.email } });
  if (existing) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'Email already registered',
      path: ['email']
    });
  }
});

// Use parseAsync for async schemas
const result = await CreateUserSchema.safeParseAsync({ email: 'alice@example.com' });
```

# ERROR HANDLING
```typescript
const result = UserSchema.safeParse(input);

if (!result.success) {
  // result.error is ZodError
  console.log(result.error.issues);
  // [
  //   { path: ['email'], message: 'Invalid email', code: 'invalid_string' },
  //   { path: ['age'], message: 'Expected number, received string', code: 'invalid_type' }
  // ]

  // Flatten for form libraries
  const flat = result.error.flatten();
  // {
  //   formErrors: [],          // top-level errors
  //   fieldErrors: {
  //     email: ['Invalid email'],
  //     age: ['Expected number, received string']
  //   }
  // }

  // Format for API response
  const formatted = result.error.format();
  // { email: { _errors: ['Invalid email'] }, age: { _errors: ['...'] } }
}
```

# REAL-WORLD PATTERNS

## API Request Validation (Express/Fastify)
```typescript
// middleware/validate.ts
import { z, ZodSchema } from 'zod';
import { Request, Response, NextFunction } from 'express';

export function validateBody<T>(schema: ZodSchema<T>) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      return res.status(422).json({
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Request validation failed',
          details: result.error.issues.map(i => ({
            field: i.path.join('.'),
            message: i.message
          }))
        }
      });
    }
    req.body = result.data;  // replace with parsed+sanitized data
    next();
  };
}

// Route:
const CreatePostSchema = z.object({
  title: z.string().min(1).max(200).trim(),
  content: z.string().min(1),
  tags: z.array(z.string()).max(5).default([])
});

router.post('/posts', validateBody(CreatePostSchema), async (req, res) => {
  const post = req.body;  // fully typed as { title: string, content: string, tags: string[] }
  // ...
});
```

## Query Parameter Validation
```typescript
const ListUsersQuerySchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  status: z.enum(['active', 'inactive', 'all']).default('all'),
  search: z.string().min(1).max(100).optional(),
  sortBy: z.enum(['name', 'email', 'createdAt']).default('createdAt'),
  sortDir: z.enum(['asc', 'desc']).default('desc')
});

// req.query is all strings — coerce handles conversion
const query = ListUsersQuerySchema.parse(req.query);
// query.page is number, not string
```

## Environment Variables Validation
```typescript
// env.ts — validate at startup, not at runtime
const EnvSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']),
  DATABASE_URL: z.string().url(),
  PORT: z.coerce.number().int().min(1000).max(65535).default(3000),
  JWT_SECRET: z.string().min(32, 'JWT secret must be at least 32 chars'),
  ANTHROPIC_API_KEY: z.string().startsWith('sk-ant-'),
  REDIS_URL: z.string().url().optional(),
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info')
});

const env = EnvSchema.parse(process.env);  // throw at startup if invalid
export { env };

// Usage: import { env } from './env';
// env.PORT is number, env.NODE_ENV is typed union
```

## Schema Composition and Reuse
```typescript
// Base schemas
const IdField = z.object({ id: z.string().uuid() });
const TimestampFields = z.object({
  createdAt: z.date(),
  updatedAt: z.date()
});
const PaginationSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20)
});

// Compose
const UserSchema = IdField.merge(TimestampFields).extend({
  name: z.string(),
  email: z.string().email()
});

const CreateUserSchema = UserSchema.omit({ id: true, createdAt: true, updatedAt: true });
const UpdateUserSchema = CreateUserSchema.partial();
const ListUsersQuery = PaginationSchema.extend({ search: z.string().optional() });
```

# CHECKLIST
```
[ ] Use z.infer<typeof Schema> for TypeScript types — never duplicate definitions
[ ] Use safeParse for user/external input — never parse() where you'd need try/catch
[ ] Use z.coerce for URL query params and form data (all come in as strings)
[ ] Add .trim() and .toLowerCase() on string inputs at the boundary
[ ] Attach path to .refine() errors so they map to specific form fields
[ ] Validate env vars at startup — fail fast with clear error
[ ] Strip unknown keys on API input (default behavior) to prevent mass assignment
[ ] Use discriminatedUnion over union when you have a type discriminator — better perf + errors
[ ] For async validation, use .safeParseAsync() and await it
```
