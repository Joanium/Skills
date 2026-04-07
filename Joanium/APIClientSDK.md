---
name: API Client & SDK Design
trigger: build an sdk, api client library, http client wrapper, typescript sdk, python sdk, sdk design, api wrapper, client library, retry logic http, http interceptor, api client class, axios wrapper, fetch wrapper, sdk best practices
description: Design and implement API client libraries and SDKs that are a joy to use — with typed responses, automatic retries, auth handling, error normalization, and good developer ergonomics. Use this skill when the user wants to build a wrapper around an HTTP API, create an SDK for their service, or improve an existing API client.
---

# ROLE
You are a library author. You design API clients that hide complexity (retries, auth, pagination) behind a clean interface that developers love to use. Your clients are predictable, type-safe, and hard to misuse.

# DESIGN PRINCIPLES

```
1. TYPED RESPONSES        → callers know what they're getting
2. NORMALIZED ERRORS      → one error type, not 10 different exception shapes
3. AUTOMATIC RETRIES      → transparent for transient failures
4. AUTH HANDLING          → built-in, not the caller's problem
5. DISCOVERABLE API       → autocomplete should guide the developer
6. REASONABLE DEFAULTS    → works out of the box, configurable when needed
```

# TYPESCRIPT SDK — COMPLETE EXAMPLE

```typescript
// types.ts — all types in one place
export interface ClientConfig {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;        // ms, default 30000
  maxRetries?: number;     // default 3
  onRequest?: (req: Request) => void;   // hook for logging/tracing
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    cursor: string | null;
    hasMore: boolean;
    total?: number;
  };
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly status: number,
    public readonly requestId?: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }

  isRateLimit(): boolean { return this.status === 429; }
  isNotFound(): boolean  { return this.status === 404; }
  isUnauthorized(): boolean { return this.status === 401; }
}
```

```typescript
// client.ts — core HTTP client
import { ApiError, ClientConfig } from './types';

const DEFAULT_CONFIG = {
  baseUrl: 'https://api.example.com/v1',
  timeout: 30_000,
  maxRetries: 3,
};

export class HttpClient {
  private config: Required<ClientConfig>;

  constructor(config: ClientConfig) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  async request<T>(
    method: string,
    path: string,
    options: {
      body?: unknown;
      query?: Record<string, string | number | boolean | undefined>;
      signal?: AbortSignal;
    } = {}
  ): Promise<T> {
    const url = new URL(path, this.config.baseUrl);
    
    // Add query params, stripping undefined values
    if (options.query) {
      for (const [key, value] of Object.entries(options.query)) {
        if (value !== undefined) url.searchParams.set(key, String(value));
      }
    }

    const headers: HeadersInit = {
      'Authorization': `Bearer ${this.config.apiKey}`,
      'Content-Type':  'application/json',
      'Accept':        'application/json',
      'User-Agent':    'my-sdk/1.0.0',
    };

    const fetchOptions: RequestInit = {
      method,
      headers,
      signal: options.signal ?? AbortSignal.timeout(this.config.timeout),
      body: options.body ? JSON.stringify(options.body) : undefined,
    };

    this.config.onRequest?.(new Request(url, fetchOptions));

    return this.requestWithRetry<T>(url.toString(), fetchOptions);
  }

  private async requestWithRetry<T>(
    url: string, 
    options: RequestInit,
    attempt = 0
  ): Promise<T> {
    let response: Response;
    try {
      response = await fetch(url, options);
    } catch (err) {
      // Network error — retry if attempts remain
      if (attempt < this.config.maxRetries && this.isRetryable(null)) {
        await this.sleep(this.backoff(attempt));
        return this.requestWithRetry<T>(url, options, attempt + 1);
      }
      throw new ApiError('Network error', 'NETWORK_ERROR', 0);
    }

    if (!response.ok) {
      const error = await this.parseError(response);
      // Retry on 429 (rate limit) and 5xx (server errors)
      if (attempt < this.config.maxRetries && this.isRetryable(response)) {
        const retryAfter = response.headers.get('Retry-After');
        const delay = retryAfter ? parseInt(retryAfter) * 1000 : this.backoff(attempt);
        await this.sleep(delay);
        return this.requestWithRetry<T>(url, options, attempt + 1);
      }
      throw error;
    }

    if (response.status === 204) return undefined as T;  // No Content
    return response.json() as Promise<T>;
  }

  private isRetryable(response: Response | null): boolean {
    if (!response) return true;  // network error — always retry
    return response.status === 429 || response.status >= 500;
  }

  private backoff(attempt: number): number {
    // Exponential backoff with jitter: 100ms, 200ms, 400ms...
    return Math.min(100 * Math.pow(2, attempt) + Math.random() * 50, 10_000);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private async parseError(response: Response): Promise<ApiError> {
    try {
      const body = await response.json();
      return new ApiError(
        body.error?.message ?? response.statusText,
        body.error?.code ?? 'UNKNOWN_ERROR',
        response.status,
        body.error?.requestId,
      );
    } catch {
      return new ApiError(response.statusText, 'UNKNOWN_ERROR', response.status);
    }
  }
}
```

```typescript
// resources/users.ts — resource-specific methods
import { HttpClient, PaginatedResponse } from '../index';

export interface User {
  id: string;
  email: string;
  name: string;
  createdAt: string;
}

export interface CreateUserParams {
  email: string;
  name: string;
  role?: 'admin' | 'member';
}

export interface ListUsersParams {
  cursor?: string;
  limit?: number;
  role?: 'admin' | 'member';
}

export class UsersResource {
  constructor(private client: HttpClient) {}

  async get(id: string): Promise<User> {
    return this.client.request<{ data: User }>('GET', `/users/${id}`)
      .then(r => r.data);
  }

  async create(params: CreateUserParams): Promise<User> {
    return this.client.request<{ data: User }>('POST', '/users', { body: params })
      .then(r => r.data);
  }

  async update(id: string, params: Partial<CreateUserParams>): Promise<User> {
    return this.client.request<{ data: User }>('PATCH', `/users/${id}`, { body: params })
      .then(r => r.data);
  }

  async delete(id: string): Promise<void> {
    return this.client.request<void>('DELETE', `/users/${id}`);
  }

  async list(params?: ListUsersParams): Promise<PaginatedResponse<User>> {
    return this.client.request<PaginatedResponse<User>>('GET', '/users', {
      query: params as Record<string, string>,
    });
  }

  // Async iterator for transparent pagination
  async *iterate(params?: Omit<ListUsersParams, 'cursor'>): AsyncGenerator<User> {
    let cursor: string | null = null;
    do {
      const response = await this.list({ ...params, cursor: cursor ?? undefined });
      for (const user of response.data) yield user;
      cursor = response.pagination.cursor;
    } while (cursor);
  }
}
```

```typescript
// index.ts — the public API (what users import)
import { HttpClient } from './client';
import { UsersResource } from './resources/users';
import { OrdersResource } from './resources/orders';
export { ApiError } from './types';
export type { User, ClientConfig } from './types';

export class MyApiClient {
  public readonly users: UsersResource;
  public readonly orders: OrdersResource;
  
  private http: HttpClient;

  constructor(config: ClientConfig) {
    this.http = new HttpClient(config);
    this.users = new UsersResource(this.http);
    this.orders = new OrdersResource(this.http);
  }
}

// Usage:
const client = new MyApiClient({ apiKey: 'sk_live_...' });

const user = await client.users.get('usr_123');
await client.users.update('usr_123', { name: 'Alice B.' });

// Paginate transparently
for await (const user of client.users.iterate({ role: 'admin' })) {
  console.log(user.email);
}
```

# PYTHON SDK — PATTERNS

```python
# client.py
from __future__ import annotations
import time
import httpx
from typing import Any, Generator, TypeVar, Generic
from dataclasses import dataclass

T = TypeVar('T')

class ApiError(Exception):
    def __init__(self, message: str, code: str, status: int, request_id: str | None = None):
        super().__init__(message)
        self.code = code
        self.status = status
        self.request_id = request_id

    def is_rate_limit(self) -> bool: return self.status == 429
    def is_not_found(self) -> bool: return self.status == 404

@dataclass
class PaginatedResponse(Generic[T]):
    data: list[T]
    cursor: str | None
    has_more: bool

class MyApiClient:
    def __init__(
        self, 
        api_key: str, 
        base_url: str = "https://api.example.com/v1",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.base_url = base_url
        self.max_retries = max_retries
        self._client = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "my-sdk-python/1.0.0",
            },
            timeout=timeout,
        )
        self.users = UsersResource(self)

    def request(self, method: str, path: str, **kwargs) -> Any:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.request(method, path, **kwargs)
                if response.is_success:
                    if response.status_code == 204: return None
                    return response.json()
                
                error = self._parse_error(response)
                if response.status_code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else (0.1 * 2 ** attempt)
                    time.sleep(delay)
                    last_error = error
                    continue
                raise error
            except httpx.NetworkError as e:
                if attempt < self.max_retries:
                    time.sleep(0.1 * 2 ** attempt)
                    last_error = ApiError(str(e), "NETWORK_ERROR", 0)
                    continue
                raise ApiError(str(e), "NETWORK_ERROR", 0) from e
        raise last_error  # type: ignore

    def _parse_error(self, response: httpx.Response) -> ApiError:
        try:
            body = response.json()
            error = body.get("error", {})
            return ApiError(
                error.get("message", response.reason_phrase),
                error.get("code", "UNKNOWN_ERROR"),
                response.status_code,
                error.get("requestId"),
            )
        except Exception:
            return ApiError(response.reason_phrase, "UNKNOWN_ERROR", response.status_code)


class UsersResource:
    def __init__(self, client: MyApiClient): self._client = client

    def get(self, user_id: str) -> dict:
        return self._client.request("GET", f"/users/{user_id}")["data"]

    def create(self, email: str, name: str, role: str = "member") -> dict:
        return self._client.request("POST", "/users", json={"email": email, "name": name, "role": role})["data"]

    def list(self, cursor: str | None = None, limit: int = 20) -> PaginatedResponse:
        params = {"limit": limit}
        if cursor: params["cursor"] = cursor
        response = self._client.request("GET", "/users", params=params)
        return PaginatedResponse(
            data=response["data"],
            cursor=response["pagination"]["cursor"],
            has_more=response["pagination"]["hasMore"],
        )

    def iterate(self, limit: int = 100) -> Generator[dict, None, None]:
        cursor = None
        while True:
            page = self.list(cursor=cursor, limit=limit)
            yield from page.data
            if not page.has_more: break
            cursor = page.cursor
```

# ERGONOMICS CHECKLIST

```
[ ] Single import: from my_sdk import MyApiClient, ApiError
[ ] Resource objects for grouping (client.users.get, client.orders.list)
[ ] All errors are ApiError subclass — callers catch one type
[ ] Automatic retry with exponential backoff built-in
[ ] Pagination hidden behind async iterator / generator
[ ] Request timeout configurable but has a sane default
[ ] Auth handled by the client — never ask caller to set headers
[ ] TypeScript: all responses are typed with interfaces
[ ] Python: type hints on all public methods
[ ] README with quickstart — working example in <10 lines
```
