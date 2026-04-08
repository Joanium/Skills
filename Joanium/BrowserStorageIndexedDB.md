---
name: Browser Storage and IndexedDB
trigger: indexeddb, localstorage, sessionstorage, browser storage, idb, client side storage, offline storage, cache api, opfs, web storage, browser database, client database, dexie, local data persistence
description: Choose and implement the right browser storage for any use case — localStorage, sessionStorage, IndexedDB (with Dexie), Cache API, and OPFS — with size limits, persistence, and performance tradeoffs.
---

# ROLE
You are a senior front-end engineer who knows when to use each browser storage primitive. You write offline-capable, performant web apps that persist the right data the right way.

# STORAGE OPTIONS — CHOOSE THE RIGHT ONE
```
localStorage:
  Size:        5–10MB
  Persistence: Survives tab close, survives browser restart
  Access:      Sync — blocks main thread
  Use for:     User preferences, settings, small auth tokens
  Avoid for:   Large data, binary files, anything > 100KB

sessionStorage:
  Size:        5–10MB
  Persistence: Cleared when tab closes
  Access:      Sync — blocks main thread
  Use for:     Wizard/form state within a session
  Avoid for:   Anything that should survive tab close

IndexedDB:
  Size:        Hundreds of MB to GB (varies by browser/origin)
  Persistence: Survives browser restart (unless "temporary" storage cleared)
  Access:      Async — non-blocking
  Use for:     Large datasets, offline apps, complex queries, binary data
  Avoid for:   Simple key-value — localStorage is simpler

Cache API (Service Worker):
  Size:        Hundreds of MB
  Persistence: Until explicitly cleared or browser evicts
  Access:      Async
  Use for:     HTTP response caching, offline assets
  Avoid for:   App data — use IndexedDB instead

OPFS (Origin Private File System):
  Size:        Large (browser-managed)
  Persistence: Survives restart
  Access:      Async (sync via worker)
  Use for:     SQLite in browser (via WASM), large binary files, high-performance writes
```

# LOCALSTORAGE — SIMPLE KEY-VALUE
```typescript
// Always serialize/deserialize
const save = (key: string, value: unknown) => {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch (e) {
    console.error('Storage quota exceeded', e)
  }
}

const load = <T>(key: string, fallback: T): T => {
  try {
    const item = localStorage.getItem(key)
    return item ? JSON.parse(item) : fallback
  } catch {
    return fallback
  }
}

const remove = (key: string) => localStorage.removeItem(key)
const clear = () => localStorage.clear()

// Typed wrapper
const preferences = {
  get: () => load<UserPrefs>('prefs', defaultPrefs),
  set: (prefs: UserPrefs) => save('prefs', prefs),
  update: (partial: Partial<UserPrefs>) => {
    const current = preferences.get()
    preferences.set({ ...current, ...partial })
  }
}

// Listen for changes from other tabs
window.addEventListener('storage', (e: StorageEvent) => {
  if (e.key === 'prefs' && e.newValue) {
    const prefs = JSON.parse(e.newValue)
    syncPrefsToUI(prefs)
  }
})
```

# INDEXEDDB WITH DEXIE (RECOMMENDED WRAPPER)
```bash
npm install dexie
```

## Schema + Database Setup
```typescript
// db.ts
import Dexie, { type EntityTable } from 'dexie'

interface Contact {
  id: number
  name: string
  email: string
  phone?: string
  tags: string[]
  updatedAt: Date
}

interface Message {
  id: number
  contactId: number
  body: string
  read: boolean
  sentAt: Date
}

const db = new Dexie('MyDatabase') as Dexie & {
  contacts: EntityTable<Contact, 'id'>
  messages: EntityTable<Message, 'id'>
}

db.version(1).stores({
  contacts: '++id, email, *tags',        // ++ = auto-increment; * = multi-entry index
  messages: '++id, contactId, sentAt'
})

// Migration to version 2
db.version(2).stores({
  contacts: '++id, email, *tags, updatedAt'
}).upgrade(tx => {
  return tx.table('contacts').toCollection().modify(contact => {
    contact.updatedAt = new Date()
  })
})

export { db }
export type { Contact, Message }
```

## CRUD Operations
```typescript
import { db } from './db'

// CREATE
const id = await db.contacts.add({
  name: 'Alice',
  email: 'alice@example.com',
  tags: ['friend', 'colleague'],
  updatedAt: new Date()
})

// BULK INSERT
await db.contacts.bulkAdd([
  { name: 'Bob', email: 'bob@ex.com', tags: [], updatedAt: new Date() },
  { name: 'Carol', email: 'carol@ex.com', tags: ['vip'], updatedAt: new Date() }
])

// READ
const contact = await db.contacts.get(id)
const all = await db.contacts.toArray()

// QUERY — where clause
const friends = await db.contacts
  .where('tags')
  .equals('friend')
  .toArray()

// Range query
const recent = await db.messages
  .where('sentAt')
  .above(new Date(Date.now() - 7 * 86400000))  // last 7 days
  .sortBy('sentAt')

// Compound filter (JS filter after index query)
const unreadFromContact = await db.messages
  .where('contactId').equals(contactId)
  .filter(msg => !msg.read)
  .toArray()

// UPDATE
await db.contacts.update(id, { name: 'Alice B.', updatedAt: new Date() })

// UPSERT
await db.contacts.put({ id, name: 'Alice B.', email: 'alice@ex.com', tags: [], updatedAt: new Date() })

// DELETE
await db.contacts.delete(id)
await db.contacts.where('email').equals('spam@ex.com').delete()

// COUNT
const count = await db.contacts.count()
const friendCount = await db.contacts.where('tags').equals('friend').count()
```

## Pagination
```typescript
async function getContactsPage(page: number, pageSize = 20) {
  const offset = page * pageSize

  const [items, total] = await Promise.all([
    db.contacts
      .orderBy('name')
      .offset(offset)
      .limit(pageSize)
      .toArray(),
    db.contacts.count()
  ])

  return {
    items,
    total,
    totalPages: Math.ceil(total / pageSize),
    hasMore: offset + pageSize < total
  }
}
```

## Transactions
```typescript
// Atomic: send message + mark contact active
await db.transaction('rw', db.contacts, db.messages, async () => {
  const messageId = await db.messages.add({
    contactId,
    body: 'Hello!',
    read: false,
    sentAt: new Date()
  })

  await db.contacts.update(contactId, { updatedAt: new Date() })

  return messageId
})
```

## Reactive with Live Query
```typescript
import { useLiveQuery } from 'dexie-react-hooks'

// Component auto-rerenders when matching data changes
function ContactList() {
  const contacts = useLiveQuery(
    () => db.contacts.orderBy('name').toArray(),
    []  // deps — rerun query if these change
  )

  if (!contacts) return <Spinner />
  return <ul>{contacts.map(c => <li key={c.id}>{c.name}</li>)}</ul>
}
```

# RAW INDEXEDDB (Without Library)
```typescript
// Open database
function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('MyDB', 1)

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result
      const store = db.createObjectStore('items', {
        keyPath: 'id',
        autoIncrement: true
      })
      store.createIndex('byEmail', 'email', { unique: true })
    }

    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

// Add item
async function addItem(db: IDBDatabase, item: object) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction('items', 'readwrite')
    const request = tx.objectStore('items').add(item)
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}
```

# CACHE API (SERVICE WORKER ASSETS)
```typescript
// In service worker
const CACHE_VERSION = 'v2'
const STATIC_ASSETS = ['/app.js', '/styles.css', '/index.html']

// Precache on install
self.addEventListener('install', (event: ExtendableEvent) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then(cache => cache.addAll(STATIC_ASSETS))
  )
})

// Cache-first strategy for assets
self.addEventListener('fetch', (event: FetchEvent) => {
  if (event.request.destination === 'script' || event.request.destination === 'style') {
    event.respondWith(
      caches.match(event.request).then(cached => cached ?? fetch(event.request))
    )
  }
})

// Network-first strategy for API (fallback to cache)
self.addEventListener('fetch', (event: FetchEvent) => {
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          const clone = response.clone()
          caches.open(CACHE_VERSION).then(cache => cache.put(event.request, clone))
          return response
        })
        .catch(() => caches.match(event.request))
    )
  }
})
```

# STORAGE QUOTA
```typescript
// Check available storage
const quota = await navigator.storage.estimate()
console.log(`Used: ${quota.usage! / 1024 / 1024}MB`)
console.log(`Available: ${quota.quota! / 1024 / 1024}MB`)

// Request persistent storage (won't be evicted under pressure)
const isPersisted = await navigator.storage.persist()
console.log(isPersisted ? 'Persistent' : 'Best-effort')
```

# COMMON MISTAKES TO AVOID
```
✗ Storing large data in localStorage — it's synchronous and blocks the main thread
✗ Not handling QuotaExceededError — always wrap localStorage writes in try/catch
✗ Storing sensitive data without encryption — localStorage is readable by any same-origin JS
✗ Not versioning IndexedDB schema — breaking schema changes without migration loses data
✗ Querying all records then filtering in JS — use where() with indexed fields for performance
✗ Not using transactions for multi-table writes — partial writes leave inconsistent state
✗ Using raw IDB API — always use Dexie unless you have a specific reason not to
✗ Caching authenticated API responses in Cache API — shared cache leaks between users
```
