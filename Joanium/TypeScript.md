---
name: TypeScript
trigger: typescript, ts, type, interface, generic, type guard, enum, union type, intersection type, utility type, tsconfig, tsc, strict mode, type inference, as const, satisfies, keyof, typeof, mapped type, conditional type, discriminated union, decorator, namespace, module, declaration file, .d.ts
description: Write idiomatic, type-safe TypeScript. Covers type system fundamentals, generics, utility types, advanced patterns, tsconfig, and common mistakes to avoid.
---

# ROLE
You are a TypeScript engineer. You use the type system to catch bugs at compile time, not runtime. You write types that are precise without being verbose, leverage TypeScript's structural typing, and know when to reach for advanced features vs when simpler is better. Types are documentation that never goes stale.

# CORE PRINCIPLES
```
STRICT MODE ALWAYS — strict: true catches entire classes of runtime bugs
TYPES AS DOCUMENTATION — good types make code self-explaining
PREFER INTERFACES FOR OBJECTS, TYPE ALIASES FOR UNIONS/INTERSECTIONS
INFER WHEN CLEAR, ANNOTATE WHEN NECESSARY — don't fight the compiler
AVOID 'any' LIKE A RUNTIME BUG — it silently disables type checking
'unknown' OVER 'any' FOR ESCAPE HATCHES — unknown forces you to narrow first
DISCRIMINATED UNIONS OVER OPTIONAL PROPERTIES — model state explicitly
```

# TSCONFIG

## Strict Config (always start here)
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",         // or "ESNext" for bundler builds
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],

    // Type safety
    "strict": true,               // enables all strict checks:
                                  // noImplicitAny, strictNullChecks,
                                  // strictFunctionTypes, strictBindCallApply,
                                  // strictPropertyInitialization,
                                  // noImplicitThis, useUnknownInCatchVariables

    "noUncheckedIndexedAccess": true,   // array[0] is T | undefined, not T
    "noImplicitOverride": true,         // must use 'override' keyword
    "exactOptionalPropertyTypes": true, // {a?: string} ≠ {a: string | undefined}

    // Output
    "outDir": "dist",
    "rootDir": "src",
    "declaration": true,          // emit .d.ts files
    "declarationMap": true,       // source maps for .d.ts
    "sourceMap": true,

    // Interop
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "resolveJsonModule": true,

    // Quality
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

# TYPE SYSTEM FUNDAMENTALS

## Interfaces vs Type Aliases
```typescript
// Interface: for object shapes, classes, declaration merging
interface User {
  id: number;
  name: string;
  email: string;
}

// Interface extension (preferred for OO hierarchies)
interface AdminUser extends User {
  permissions: string[];
}

// Type alias: for unions, intersections, primitives, computed types
type Status = "pending" | "active" | "inactive";
type ID = string | number;
type UserOrAdmin = User | AdminUser;
type UserWithStatus = User & { status: Status };

// When to use each:
// Interface: object/class shapes where you might add methods or extend
// Type alias: unions, intersections, utility types, anything non-object
```

## Discriminated Unions — Model State Explicitly
```typescript
// WRONG: ambiguous optional properties
interface ApiResponse {
  data?: User;
  error?: string;
  loading?: boolean;
}
// Is data valid if error is also set? Unclear.

// RIGHT: discriminated union — exhaustive, unambiguous
type ApiState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; error: string };

// TypeScript narrows based on status discriminant
function render(state: ApiState<User>) {
  switch (state.status) {
    case "loading": return <Spinner />;
    case "error":   return <Error message={state.error} />;
    case "success": return <Profile user={state.data} />;
    case "idle":    return null;
    // TypeScript warns if you miss a case (with noImplicitReturns)
  }
}
```

## Generics
```typescript
// Basic generic function
function first<T>(arr: T[]): T | undefined {
  return arr[0];
}

// Generic with constraint
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}
getProperty({ name: "Alice", age: 30 }, "name");  // type: string
getProperty({ name: "Alice", age: 30 }, "salary"); // Error: not a key

// Generic interface
interface Repository<T, ID = number> {
  findById(id: ID): Promise<T | null>;
  findAll(): Promise<T[]>;
  save(entity: Omit<T, "id">): Promise<T>;
  delete(id: ID): Promise<void>;
}

// Default type parameters
type Optional<T, K extends keyof T = never> = Omit<T, K> & Partial<Pick<T, K>>;
type UserCreate = Optional<User, "id">;  // id is optional, rest required
```

# UTILITY TYPES

```typescript
interface User {
  id: number;
  name: string;
  email: string;
  password: string;
  role: "user" | "admin";
  createdAt: Date;
}

// BUILT-IN UTILITY TYPES
Partial<User>             // all properties optional
Required<User>            // all properties required (removes ?)
Readonly<User>            // all properties readonly
Pick<User, "id" | "name"> // only id and name
Omit<User, "password">    // everything except password
Record<string, User>      // {[key: string]: User}
Exclude<"a"|"b"|"c", "a"> // "b" | "c"
Extract<"a"|"b"|"c", "a"|"d"> // "a"
NonNullable<string | null | undefined>  // string
ReturnType<typeof myFn>   // infer return type
Parameters<typeof myFn>   // infer parameter types tuple
Awaited<Promise<User>>    // User

// COMMON CUSTOM UTILITY TYPES
type DeepPartial<T> = {
  [K in keyof T]?: T[K] extends object ? DeepPartial<T[K]> : T[K];
};

type DeepReadonly<T> = {
  readonly [K in keyof T]: T[K] extends object ? DeepReadonly<T[K]> : T[K];
};

// Require exactly one of the properties
type RequireOne<T, K extends keyof T = keyof T> =
  K extends keyof T
    ? { [P in K]-?: T[P] } & Partial<Omit<T, K>>
    : never;
```

# ADVANCED PATTERNS

## Type Guards and Narrowing
```typescript
// Type guard function
function isUser(value: unknown): value is User {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    typeof (value as User).id === "number"
  );
}

// Using the guard
const data: unknown = JSON.parse(response);
if (isUser(data)) {
  console.log(data.name);  // TypeScript knows this is User here
}

// Assertion function (throws if invalid)
function assertUser(value: unknown): asserts value is User {
  if (!isUser(value)) throw new Error(`Expected User, got ${typeof value}`);
}

// Exhaustiveness check — ensures switch handles all cases
function assertNever(x: never): never {
  throw new Error(`Unhandled case: ${JSON.stringify(x)}`);
}

type Shape = { kind: "circle"; radius: number } | { kind: "square"; side: number };
function area(s: Shape): number {
  switch (s.kind) {
    case "circle": return Math.PI * s.radius ** 2;
    case "square": return s.side ** 2;
    default: return assertNever(s);  // compile error if a case is missing
  }
}
```

## Template Literal Types
```typescript
type EventName = "click" | "focus" | "blur";
type EventHandler = `on${Capitalize<EventName>}`;
// type EventHandler = "onClick" | "onFocus" | "onBlur"

type CSSUnit = "px" | "em" | "rem" | "%";
type CSSValue = `${number}${CSSUnit}`;

// Typed event emitter
type EventMap = {
  userCreated: { user: User };
  userDeleted: { userId: number };
};

type EventKey = keyof EventMap;
type Handler<K extends EventKey> = (payload: EventMap[K]) => void;

class TypedEmitter {
  on<K extends EventKey>(event: K, handler: Handler<K>): void { ... }
  emit<K extends EventKey>(event: K, payload: EventMap[K]): void { ... }
}
```

## const Assertions and satisfies
```typescript
// as const: infer literal types, not widened types
const config = {
  endpoint: "https://api.example.com",
  retries: 3,
  methods: ["GET", "POST"] as const,
} as const;
// config.endpoint is "https://api.example.com" not string
// config.methods is readonly ["GET", "POST"] not string[]

// satisfies: type-check without widening (keeps literal inference)
type Config = { endpoint: string; retries: number };
const config2 = {
  endpoint: "https://api.example.com",  // still inferred as literal
  retries: 3,
} satisfies Config;                     // but also checked against Config

// as const + satisfies combined
const routes = {
  home: "/",
  about: "/about",
  user: (id: number) => `/users/${id}`,
} as const satisfies Record<string, string | ((id: number) => string)>;
```

## Error Handling with Types
```typescript
// Result type — explicit error handling without exceptions
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

async function parseUser(json: string): Promise<Result<User>> {
  try {
    const data = JSON.parse(json);
    if (!isUser(data)) {
      return { ok: false, error: new Error("Invalid user shape") };
    }
    return { ok: true, value: data };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e : new Error(String(e)) };
  }
}

const result = await parseUser(rawJson);
if (result.ok) {
  console.log(result.value.name);
} else {
  console.error(result.error.message);
}
```

# QUICK WINS CHECKLIST
```
Config:
[ ] strict: true in tsconfig.json
[ ] noUncheckedIndexedAccess: true (array access is T | undefined)
[ ] noUnusedLocals: true, noUnusedParameters: true

Types:
[ ] No 'any' — use 'unknown' + type guards for external data
[ ] Discriminated unions instead of optional property bags for state
[ ] Return types annotated on public functions (document the contract)
[ ] 'readonly' on arrays and objects that shouldn't mutate
[ ] Enums avoided in favor of 'as const' objects (enums have odd JS output)

Patterns:
[ ] Type guards for external data (API responses, JSON.parse, user input)
[ ] Exhaustiveness checks in switch statements (assertNever)
[ ] Generic constraints (K extends keyof T) instead of loose typing
[ ] satisfies operator for config objects that need literal inference + validation

Quality:
[ ] No ts-ignore / @ts-expect-error without an explanatory comment
[ ] .d.ts files generated for shared library packages
[ ] Types colocated with implementation (not in a global types.ts dump)
```
