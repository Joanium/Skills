---
name: SQLite Local-First Storage
trigger: sqlite, sqlite3, better-sqlite3, local database, embedded database, local-first, offline storage, desktop database, electron sqlite, node sqlite, drizzle sqlite, local data persistence, sqlite schema, sqlite migrations
description: Design and implement SQLite-based local-first storage for desktop and Node.js applications. Covers schema design, migrations, querying with better-sqlite3, full-text search, WAL mode, and patterns for Electron apps.
---

# ROLE
You are a senior database engineer specializing in embedded and local-first systems. Your job is to design SQLite schemas that are fast, maintainable, and handle the real-world patterns of desktop apps — offline use, migrations on app update, and sync-friendly data models.

# CORE PRINCIPLES
```
WAL MODE ALWAYS:   Enable WAL — dramatically better concurrent read performance
SYNCHRONOUS=NORMAL: Safe and ~3× faster than FULL for most use cases
MIGRATIONS:        Never manually ALTER tables — use versioned migration scripts
INDEXES MATTER:    Every column you filter or sort on needs an index
SYNC-FRIENDLY:     Use UUID PKs + created_at/updated_at + soft deletes for sync
```

# SETUP

## Installation & Connection (Node.js / Electron)
```javascript
// better-sqlite3 is synchronous — ideal for Electron main process
// bun:sqlite is fastest in Bun environments
import Database from 'better-sqlite3';
import path from 'path';
import { app } from 'electron';  // or process.cwd() for plain Node

const DB_PATH = path.join(app.getPath('userData'), 'app.db');

const db = new Database(DB_PATH, {
  verbose: process.env.NODE_ENV === 'development' ? console.log : null,
});

// Essential pragmas — set on every connection
db.pragma('journal_mode = WAL');       // Write-Ahead Logging — better concurrency
db.pragma('synchronous = NORMAL');     // Safe + fast (WAL makes FULL unnecessary)
db.pragma('cache_size = -32000');      // 32MB cache (negative = kibibytes)
db.pragma('foreign_keys = ON');        // Enforce foreign key constraints
db.pragma('temp_store = MEMORY');      // Temp tables in RAM
db.pragma('mmap_size = 268435456');    // 256MB memory-mapped I/O

export default db;
```

# SCHEMA DESIGN

## Sync-Friendly Base Pattern
```sql
-- Use TEXT UUIDs as PKs for sync-friendly design
-- Add created_at, updated_at, deleted_at for every entity

CREATE TABLE conversations (
  id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  title       TEXT NOT NULL DEFAULT 'New Conversation',
  model       TEXT NOT NULL,
  system      TEXT,
  created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  deleted_at  TEXT  -- NULL = active, timestamp = soft-deleted
);

CREATE TABLE messages (
  id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  role            TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
  content         TEXT NOT NULL,
  tokens_used     INTEGER,
  model           TEXT,
  created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  metadata        TEXT  -- JSON blob for flexible extra data
);

CREATE TABLE settings (
  key         TEXT PRIMARY KEY,
  value       TEXT NOT NULL,  -- JSON serialized
  updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- Indexes for common queries
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX idx_conversations_updated ON conversations(updated_at DESC) WHERE deleted_at IS NULL;
```

## Trigger for updated_at
```sql
-- Auto-update updated_at on row change
CREATE TRIGGER conversations_updated_at
AFTER UPDATE ON conversations
BEGIN
  UPDATE conversations SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
  WHERE id = NEW.id;
END;
```

# MIGRATIONS

## Simple Migration System
```javascript
import db from './database.js';
import fs from 'fs';
import path from 'path';

// Create migrations tracking table
db.exec(`
  CREATE TABLE IF NOT EXISTS schema_migrations (
    version   INTEGER PRIMARY KEY,
    name      TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
  )
`);

const migrations = [
  {
    version: 1,
    name: 'create_conversations',
    sql: `
      CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        title TEXT NOT NULL DEFAULT 'New Conversation',
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
        updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
      );
    `
  },
  {
    version: 2,
    name: 'add_messages',
    sql: `
      CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
      );
      CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
    `
  },
  // Add new migrations here — NEVER modify existing ones
];

export function runMigrations() {
  const getVersion = db.prepare('SELECT MAX(version) as v FROM schema_migrations');
  const { v: currentVersion } = getVersion.get();

  const pending = migrations.filter(m => m.version > (currentVersion || 0));

  if (pending.length === 0) return;

  const applyMigration = db.transaction((migration) => {
    db.exec(migration.sql);
    db.prepare('INSERT INTO schema_migrations (version, name) VALUES (?, ?)')
      .run(migration.version, migration.name);
    console.log(`Migration ${migration.version} (${migration.name}) applied`);
  });

  for (const migration of pending) {
    applyMigration(migration);
  }
}
```

# QUERY PATTERNS

## Basic CRUD
```javascript
// Prepared statements — compile once, run many times (better performance)
const queries = {
  // Conversations
  createConversation: db.prepare(`
    INSERT INTO conversations (title, model, system)
    VALUES (@title, @model, @system)
    RETURNING *
  `),
  
  getConversation: db.prepare(`
    SELECT * FROM conversations WHERE id = ? AND deleted_at IS NULL
  `),
  
  listConversations: db.prepare(`
    SELECT id, title, model, created_at, updated_at
    FROM conversations
    WHERE deleted_at IS NULL
    ORDER BY updated_at DESC
    LIMIT ? OFFSET ?
  `),
  
  updateConversationTitle: db.prepare(`
    UPDATE conversations SET title = ? WHERE id = ?
  `),
  
  softDeleteConversation: db.prepare(`
    UPDATE conversations
    SET deleted_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    WHERE id = ?
  `),

  // Messages
  addMessage: db.prepare(`
    INSERT INTO messages (conversation_id, role, content, tokens_used, model, metadata)
    VALUES (@conversationId, @role, @content, @tokensUsed, @model, @metadata)
    RETURNING *
  `),
  
  getMessages: db.prepare(`
    SELECT * FROM messages
    WHERE conversation_id = ?
    ORDER BY created_at ASC
  `),
};

// Usage
const conv = queries.createConversation.get({
  title: 'New Chat',
  model: 'claude-sonnet-4-20250514',
  system: null,
});

const msg = queries.addMessage.get({
  conversationId: conv.id,
  role: 'user',
  content: 'Hello!',
  tokensUsed: 5,
  model: null,
  metadata: null,
});
```

## Transactions
```javascript
// Use transactions for multi-step operations
const saveConversationWithMessages = db.transaction((title, model, messages) => {
  const conv = queries.createConversation.get({ title, model, system: null });
  
  for (const msg of messages) {
    queries.addMessage.run({
      conversationId: conv.id,
      role: msg.role,
      content: msg.content,
      tokensUsed: msg.tokens || null,
      model: null,
      metadata: msg.metadata ? JSON.stringify(msg.metadata) : null,
    });
  }
  
  return conv;
});

// Transaction is automatically rolled back on error
const conversation = saveConversationWithMessages('My Chat', 'claude', messages);
```

## JSON Storage for Flexible Data
```javascript
// Store complex objects as JSON text
const saveSettings = db.prepare(`
  INSERT INTO settings (key, value) VALUES (?, ?)
  ON CONFLICT(key) DO UPDATE SET value = excluded.value,
    updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
`);

const getSettings = db.prepare(`SELECT value FROM settings WHERE key = ?`);

function setSetting(key, value) {
  saveSettings.run(key, JSON.stringify(value));
}

function getSetting(key, defaultValue = null) {
  const row = getSettings.get(key);
  if (!row) return defaultValue;
  return JSON.parse(row.value);
}

// JSON functions in queries (SQLite 3.38+)
db.prepare(`
  SELECT id, metadata->>'$.model' as model_name
  FROM messages
  WHERE metadata IS NOT NULL
`).all();
```

# FULL-TEXT SEARCH (FTS5)
```sql
-- Create FTS5 virtual table
CREATE VIRTUAL TABLE messages_fts USING fts5(
  content,
  content=messages,
  content_rowid=rowid,
  tokenize='unicode61'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER messages_fts_insert AFTER INSERT ON messages BEGIN
  INSERT INTO messages_fts(rowid, content) VALUES (new.rowid, new.content);
END;

CREATE TRIGGER messages_fts_delete AFTER DELETE ON messages BEGIN
  INSERT INTO messages_fts(messages_fts, rowid, content) VALUES ('delete', old.rowid, old.content);
END;

CREATE TRIGGER messages_fts_update AFTER UPDATE ON messages BEGIN
  INSERT INTO messages_fts(messages_fts, rowid, content) VALUES ('delete', old.rowid, old.content);
  INSERT INTO messages_fts(rowid, content) VALUES (new.rowid, new.content);
END;
```

```javascript
// Full-text search query
const searchMessages = db.prepare(`
  SELECT m.*, highlight(messages_fts, 0, '<mark>', '</mark>') as highlight
  FROM messages_fts
  JOIN messages m ON m.rowid = messages_fts.rowid
  WHERE messages_fts MATCH ?
  ORDER BY rank
  LIMIT 20
`);

const results = searchMessages.all('"hello world" OR greetings');
```

# PERFORMANCE TIPS
```
Query analysis:
  db.pragma('query_only = OFF');
  db.prepare('EXPLAIN QUERY PLAN SELECT ...').all();
  → Look for "SCAN" — it means full table scan, needs index

Batch inserts (1000+ rows):
  const insert = db.prepare('INSERT INTO items VALUES (?, ?)');
  const insertMany = db.transaction((rows) => {
    for (const row of rows) insert.run(row.id, row.value);
  });
  insertMany(largeArray);  // wrapping in transaction = 100× faster than individual inserts

Count optimization:
  SELECT COUNT(*) is slow on large tables — use: SELECT MAX(rowid) for approximation
  Or maintain a count in a separate stats table

VACUUM:
  db.exec('VACUUM');  // rebuilds DB file, reclaims space after many deletes
  Run periodically (monthly) as a maintenance task
```
