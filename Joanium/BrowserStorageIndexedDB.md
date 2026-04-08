---
name: Browser Storage and IndexedDB
trigger: indexeddb, browser storage, localstorage, sessionstorage, web storage, client side storage, offline storage, cache api, idb, dexie, browser database, client database
description: Choose and implement the right browser storage mechanism. Covers localStorage, sessionStorage, IndexedDB (with Dexie.js), Cache API, cookies, storage quotas, and patterns for offline-first and sync-on-reconnect apps.
---

# ROLE
You are a senior frontend engineer. Browser storage is a spectrum — from tiny key-value stores to full client-side databases. Pick the right tool for the data, design for eviction and quota limits, and never block the main thread on storage I/O.

# STORAGE MECHANISM COMPARISON
```
┌──────────────────┬────────────────┬───────────────┬────────────────────┬──────────────┐
│ Mechanism        │ Capacity       │ API Style     │ Persists           │ Use For      │
├──────────────────┼────────────────┼───────────────┼────────────────────┼──────────────┤
│ localStorage     │ ~5–10 MB       │ Synchronous   │ Until cleared      │ Simple prefs │
│ sessionStorage   │ ~5–10 MB       │ Synchronous   │ Tab session only   │ Temp state   │
│ IndexedDB        │ GB range       │ Async (Prom.) │ Until cleared      │ Structured   │
│ Cache API        │ GB range       │ Async (Prom.) │ Until cleared      │ HTTP caching │
│ Cookies          │ ~4 KB          │ Synchronous   │ Configurable TTL   │ Auth tokens  │
│ OPFS             │ GB range       │ Async         │ Until cleared      │ Large files  │
└──────────────────┴────────────────┴───────────────┴────────────────────┴──────────────┘

DECISION GUIDE:
  Auth tokens:             Secure HttpOnly cookie (server-set)
  UI preferences:          localStorage (theme, language)
  Form draft (tab only):   sessionStorage
  Offline data / caching:  IndexedDB (via Dexie.js)
  Response caching (SW):   Cache API
  Large files:             Origin Private File System (OPFS)
```

# LOCALSTORAGE — PATTERNS AND PITFALLS
```typescript
// Simple wrapper with JSON and error handling
class LocalStorage {
  static get<T>(key: string, defaultValue: T): T {
    try {
      const item = localStorage.getItem(key);
      return item !== null ? (JSON.parse(item) as T) : defaultValue;
    } catch {
      return defaultValue;
    }
  }

  static set<T>(key: string, value: T): void {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (err) {
      // QuotaExceededError — handle gracefully
      console.warn('localStorage quota exceeded:', err);
    }
  }

  static remove(key: string): void {
    localStorage.removeItem(key);
  }
}

// Usage
LocalStorage.set('userPreferences', { theme: 'dark', fontSize: 16 });
const prefs = LocalStorage.get('userPreferences', { theme: 'light', fontSize: 14 });

// PITFALLS:
// ✗ Never store sensitive data (visible in DevTools, no encryption)
// ✗ Synchronous — blocks main thread for large data
// ✗ Strings only — JSON.parse/stringify for everything
// ✗ Shared across all tabs — listen for storage events if you care
// ✗ Not available in Web Workers or Service Workers

// Cross-tab sync
window.addEventListener('storage', (event) => {
  if (event.key === 'userPreferences' && event.newValue) {
    const newPrefs = JSON.parse(event.newValue);
    updateUI(newPrefs);
  }
});
```

# INDEXEDDB WITH DEXIE.JS
```typescript
import Dexie, { type Table } from 'dexie';

// 1. Define TypeScript interfaces
interface Post {
  id?: number;          // auto-increment primary key
  serverId: string;     // server-assigned ID (for sync)
  title: string;
  body: string;
  authorId: string;
  createdAt: Date;
  updatedAt: Date;
  syncStatus: 'synced' | 'pending' | 'failed';
}

interface Draft {
  id?: number;
  postId?: string;
  title: string;
  body: string;
  savedAt: Date;
}

// 2. Define database with versioned schema
class AppDatabase extends Dexie {
  posts!: Table<Post>;
  drafts!: Table<Draft>;

  constructor() {
    super('AppDatabase');

    this.version(1).stores({
      posts:  '++id, serverId, authorId, createdAt, syncStatus',
      // ^^   auto-increment, then indexed fields
      // Non-indexed fields (title, body) don't appear here but are still stored
      drafts: '++id, postId, savedAt',
    });

    // Schema migrations
    this.version(2).stores({
      posts:  '++id, serverId, authorId, createdAt, syncStatus, [authorId+createdAt]',
      // Added compound index [authorId+createdAt] for sorted per-author queries
      drafts: '++id, postId, savedAt',
    }).upgrade(async (tx) => {
      // Migrate data if needed
      await tx.table('posts').toCollection().modify(post => {
        post.syncStatus = post.syncStatus ?? 'synced';
      });
    });
  }
}

export const db = new AppDatabase();
```

```typescript
// 3. Repository pattern over Dexie
class PostRepository {
  async getAll(): Promise<Post[]> {
    return db.posts.orderBy('createdAt').reverse().toArray();
  }

  async getByAuthor(authorId: string, limit = 20): Promise<Post[]> {
    return db.posts
      .where('authorId').equals(authorId)
      .reverse()
      .limit(limit)
      .toArray();
  }

  async getPendingSync(): Promise<Post[]> {
    return db.posts.where('syncStatus').equals('pending').toArray();
  }

  async upsert(post: Omit<Post, 'id'>): Promise<number> {
    // Check if exists by serverId
    const existing = await db.posts.where('serverId').equals(post.serverId).first();
    if (existing?.id) {
      await db.posts.update(existing.id, { ...post, updatedAt: new Date() });
      return existing.id;
    }
    return db.posts.add({ ...post, updatedAt: new Date() });
  }

  async markSynced(localId: number, serverId: string): Promise<void> {
    await db.posts.update(localId, { serverId, syncStatus: 'synced', updatedAt: new Date() });
  }

  async delete(id: number): Promise<void> {
    await db.posts.delete(id);
  }

  // Full-text search (Dexie doesn't support FTS natively — use a library or filter)
  async search(query: string): Promise<Post[]> {
    const lower = query.toLowerCase();
    return db.posts
      .filter(post =>
        post.title.toLowerCase().includes(lower) ||
        post.body.toLowerCase().includes(lower)
      )
      .toArray();
  }
}

// Bulk operations — much faster than individual writes
async function bulkUpsert(posts: Post[]): Promise<void> {
  await db.transaction('rw', db.posts, async () => {
    for (const post of posts) {
      await db.posts.put(post);  // put = insert or replace by primary key
    }
  });
}
```

# OFFLINE-FIRST SYNC PATTERN
```typescript
// Optimistic UI + background sync
class SyncManager {
  private syncInProgress = false;

  // Save locally first, sync in background
  async createPost(data: Omit<Post, 'id' | 'serverId' | 'syncStatus' | 'createdAt' | 'updatedAt'>): Promise<number> {
    const localId = await db.posts.add({
      ...data,
      serverId: `local_${crypto.randomUUID()}`,  // temp ID until synced
      syncStatus: 'pending',
      createdAt: new Date(),
      updatedAt: new Date(),
    });

    // Fire and forget — sync in background
    this.syncPending().catch(console.error);

    return localId;
  }

  async syncPending(): Promise<void> {
    if (this.syncInProgress || !navigator.onLine) return;
    this.syncInProgress = true;

    try {
      const pending = await postRepository.getPendingSync();
      for (const post of pending) {
        try {
          const serverPost = await api.createPost({
            title: post.title,
            body: post.body,
            authorId: post.authorId,
          });
          await postRepository.markSynced(post.id!, serverPost.id);
        } catch (err) {
          await db.posts.update(post.id!, { syncStatus: 'failed' });
        }
      }
    } finally {
      this.syncInProgress = false;
    }
  }
}

// Listen for online event to trigger sync
window.addEventListener('online', () => syncManager.syncPending());
```

# CACHE API — HTTP RESPONSE CACHING
```javascript
// In Service Worker — cache strategies
const CACHE_NAME = 'app-v1';
const STATIC_ASSETS = ['/app.js', '/app.css', '/offline.html'];

// Install: pre-cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
});

// Fetch: cache strategies by route
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Static assets: cache-first
  if (url.pathname.match(/\.(js|css|png|woff2)$/)) {
    event.respondWith(cacheFirst(event.request));
    return;
  }

  // API responses: network-first with cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(event.request));
    return;
  }
});

async function cacheFirst(request: Request): Promise<Response> {
  const cached = await caches.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  const cache = await caches.open(CACHE_NAME);
  cache.put(request, response.clone());
  return response;
}

async function networkFirst(request: Request): Promise<Response> {
  try {
    const response = await fetch(request);
    const cache = await caches.open(CACHE_NAME);
    cache.put(request, response.clone());
    return response;
  } catch {
    return caches.match(request) ?? Response.error();
  }
}
```

# STORAGE QUOTA MANAGEMENT
```typescript
// Check available storage before writing large data
async function checkStorageQuota(): Promise<void> {
  if (!navigator.storage?.estimate) return;

  const { quota = 0, usage = 0 } = await navigator.storage.estimate();
  const percentUsed = (usage / quota) * 100;
  const mbUsed = (usage / 1024 / 1024).toFixed(1);
  const mbQuota = (quota / 1024 / 1024).toFixed(0);

  console.log(`Storage: ${mbUsed}MB / ${mbQuota}MB (${percentUsed.toFixed(1)}%)`);

  if (percentUsed > 80) {
    // Evict old data
    await evictOldData();
  }
}

// Request persistent storage (prevents eviction under pressure)
async function requestPersistentStorage(): Promise<boolean> {
  if (!navigator.storage?.persist) return false;
  const persisted = await navigator.storage.persist();
  console.log(`Persistent storage: ${persisted ? 'granted' : 'not granted'}`);
  return persisted;
}

async function evictOldData(): Promise<void> {
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
  const count = await db.posts
    .where('createdAt').below(thirtyDaysAgo)
    .and(post => post.syncStatus === 'synced')
    .delete();
  console.log(`Evicted ${count} old posts to free storage space`);
}
```

# SECURITY CHECKLIST
```
[ ] Never store auth tokens in localStorage (XSS steals them) → use HttpOnly cookies
[ ] Never store PII in localStorage or IndexedDB without user consent
[ ] Use subresource integrity (SRI) for cached third-party scripts
[ ] Encrypt sensitive IndexedDB data if truly required client-side
[ ] Request persistent storage for offline-critical apps
[ ] Handle QuotaExceededError gracefully — don't crash on full storage
[ ] Clear sensitive data on logout: localStorage.clear(), db.delete()
[ ] Service Worker cache versioned — old caches purged on activation
```
