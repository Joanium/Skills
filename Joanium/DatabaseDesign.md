---
name: Database Design
trigger: schema design, database schema, ERD, entity relationship, table design, data model, migrations, indexes, foreign keys, normalization, postgres schema, SQL schema, database modeling
description: Third skill in the build pipeline. Read after System Architecture. Covers relational schema design, ERD creation, naming conventions, indexing strategy, migration management, and common modeling patterns for real-world apps.
prev_skill: 02-SystemArchitecture.md
next_skill: 04-APIDesign.md
---

# ROLE
You are a database engineer who has seen the consequences of bad schema design in production — slow queries, impossible migrations, data integrity bugs. You design schemas that are correct, queryable, and evolvable. You treat the schema as the most important long-lived artifact in the codebase.

# CORE PRINCIPLES
```
THE SCHEMA IS YOUR MOST EXPENSIVE MIGRATION — get it right before writing queries
NORMALIZE FIRST, DENORMALIZE WHEN PROVEN SLOW — premature denormalization = data inconsistency
NAME THINGS CLEARLY — user_id not uid, created_at not ts, is_active not flag
EVERY TABLE NEEDS: id (UUID or bigint), created_at, updated_at
SOFT DELETE IS A TRAP — deleted_at adds WHERE deleted_at IS NULL to every query; use it intentionally
FOREIGN KEYS ARE NOT OPTIONAL — your DB is smarter than your application code
INDEX WHAT YOU QUERY ON, NOT EVERYTHING — each index slows down writes
```

# STEP 1 — IDENTIFY ENTITIES FROM USER STORIES

```
PROCESS:
  Read user stories → extract nouns → each noun is a potential table
  Read user actions → extract relationships between nouns

EXAMPLE — YouTube-like platform:
  Stories mention: users, videos, channels, comments, subscriptions, 
                   likes, views, tags, notifications, playlists

  → Entities: users, videos, channels, comments, subscriptions, 
               video_likes, video_views, tags, video_tags, 
               notifications, playlists, playlist_videos

FILTERING ENTITIES:
  → Real tables: persistent data with unique identity
  → Join tables: relationships between two entities (video_tags, playlist_videos)
  → Computed/virtual: don't store what you can calculate (age, view_count if < 1M)
```

# STEP 2 — DESIGN THE SCHEMA

```sql
-- CONVENTIONS:
--   Table names: snake_case, plural (users, not User)
--   Column names: snake_case
--   Primary keys: UUID (globally unique) or BIGSERIAL (simpler, smaller)
--   Foreign keys: {referenced_table_singular}_id (user_id, video_id)
--   Booleans: is_* or has_* prefix (is_active, has_verified_email)
--   Timestamps: always timezone-aware (TIMESTAMPTZ, not TIMESTAMP)

-- USERS
CREATE TABLE users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         TEXT NOT NULL UNIQUE,
  username      TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  display_name  TEXT,
  avatar_url    TEXT,
  bio           TEXT,
  is_verified   BOOLEAN NOT NULL DEFAULT FALSE,
  is_banned     BOOLEAN NOT NULL DEFAULT FALSE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- CHANNELS (one per user for simplicity, or separate for multi-channel)
CREATE TABLE channels (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  handle         TEXT NOT NULL UNIQUE,  -- @mychannel
  name           TEXT NOT NULL,
  description    TEXT,
  banner_url     TEXT,
  subscriber_count BIGINT NOT NULL DEFAULT 0,  -- denormalized for performance
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- VIDEOS
CREATE TABLE videos (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id      UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  title           TEXT NOT NULL,
  description     TEXT,
  status          TEXT NOT NULL DEFAULT 'processing'
                  CHECK (status IN ('processing', 'ready', 'failed', 'deleted')),
  visibility      TEXT NOT NULL DEFAULT 'public'
                  CHECK (visibility IN ('public', 'unlisted', 'private')),
  duration_secs   INTEGER,
  thumbnail_url   TEXT,
  raw_storage_key TEXT,      -- S3 key for raw upload
  hls_storage_key TEXT,      -- S3 key for processed HLS manifest
  view_count      BIGINT NOT NULL DEFAULT 0,
  like_count      BIGINT NOT NULL DEFAULT 0,  -- denormalized
  comment_count   BIGINT NOT NULL DEFAULT 0,  -- denormalized
  published_at    TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TAGS
CREATE TABLE tags (
  id   BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE video_tags (
  video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
  tag_id   BIGINT REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (video_id, tag_id)
);

-- COMMENTS
CREATE TABLE comments (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id   UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  parent_id  UUID REFERENCES comments(id) ON DELETE CASCADE,  -- for replies
  body       TEXT NOT NULL,
  like_count BIGINT NOT NULL DEFAULT 0,
  is_pinned  BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- SUBSCRIPTIONS
CREATE TABLE subscriptions (
  subscriber_id UUID REFERENCES users(id) ON DELETE CASCADE,
  channel_id    UUID REFERENCES channels(id) ON DELETE CASCADE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (subscriber_id, channel_id)
);

-- VIDEO LIKES (composite PK prevents double-likes at DB level)
CREATE TABLE video_likes (
  user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
  video_id   UUID REFERENCES videos(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, video_id)
);

-- VIDEO VIEWS (high-write table — consider separate analytics DB at scale)
CREATE TABLE video_views (
  id         BIGSERIAL PRIMARY KEY,
  video_id   UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  user_id    UUID REFERENCES users(id) ON DELETE SET NULL,  -- nullable for anonymous
  ip_hash    TEXT,  -- for dedup of anonymous views
  watch_secs INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

# STEP 3 — INDEXING STRATEGY

```sql
-- INDEX RULE: add an index for every column you filter, sort, or join on frequently
-- INDEX COST: each index adds ~10-30% to write time — don't index everything

-- USERS
CREATE INDEX idx_users_email    ON users(email);       -- login lookup
CREATE INDEX idx_users_username ON users(username);    -- profile lookup

-- VIDEOS — most queried table
CREATE INDEX idx_videos_channel_id    ON videos(channel_id);
CREATE INDEX idx_videos_status        ON videos(status);
CREATE INDEX idx_videos_published_at  ON videos(published_at DESC);  -- feed ordering
-- Composite: channel feed query (channel_id + status + published_at)
CREATE INDEX idx_videos_channel_feed  ON videos(channel_id, status, published_at DESC)
  WHERE status = 'ready' AND visibility = 'public';  -- partial index — only what matters

-- COMMENTS
CREATE INDEX idx_comments_video_id   ON comments(video_id, created_at DESC);
CREATE INDEX idx_comments_parent_id  ON comments(parent_id);

-- SUBSCRIPTIONS
CREATE INDEX idx_subscriptions_subscriber ON subscriptions(subscriber_id);
CREATE INDEX idx_subscriptions_channel    ON subscriptions(channel_id);

-- VIDEO VIEWS — high-write, be conservative with indexes
CREATE INDEX idx_video_views_video_id ON video_views(video_id, created_at DESC);

-- FULL-TEXT SEARCH (PostgreSQL native, good for MVP)
ALTER TABLE videos ADD COLUMN search_vector TSVECTOR;
CREATE INDEX idx_videos_search ON videos USING GIN(search_vector);

-- Update search vector on write:
CREATE OR REPLACE FUNCTION update_video_search_vector() RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector = to_tsvector('english', coalesce(NEW.title, '') || ' ' || coalesce(NEW.description, ''));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER videos_search_vector_update
  BEFORE INSERT OR UPDATE ON videos
  FOR EACH ROW EXECUTE FUNCTION update_video_search_vector();
```

# STEP 4 — MIGRATIONS STRATEGY

```
TOOLS:
  Node.js:  Prisma Migrate, Drizzle Kit, or Flyway
  Python:   Alembic (SQLAlchemy) or Django migrations
  Go:       golang-migrate, Goose

MIGRATION RULES:
  1. Every schema change is a migration file — never edit an existing migration
  2. Migrations must be reversible (write the down migration)
  3. Never DROP COLUMN in the same release that code stops using it
     → Release 1: code ignores the column (backward-compatible)
     → Release 2: remove the column in the migration (safe)
  4. Adding NOT NULL columns requires a default or a multi-step migration:
     Step 1: Add column as nullable
     Step 2: Backfill data
     Step 3: Add NOT NULL constraint
  5. Run migrations before deploying new code (never after)

NAMING: {timestamp}_{description}.sql
  20240115_001_create_users.sql
  20240115_002_create_videos.sql
  20240116_001_add_search_vector_to_videos.sql
```

# STEP 5 — COMMON PATTERNS

```sql
-- SOFT DELETE (use intentionally, not by default):
ALTER TABLE videos ADD COLUMN deleted_at TIMESTAMPTZ;
-- All queries must include: WHERE deleted_at IS NULL
-- Create a view to hide the filter:
CREATE VIEW active_videos AS SELECT * FROM videos WHERE deleted_at IS NULL;

-- OPTIMISTIC LOCKING (prevent lost updates):
ALTER TABLE videos ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
-- On update: WHERE id = $1 AND version = $2 → if 0 rows affected, conflict

-- AUDIT LOG (who changed what, when):
CREATE TABLE audit_log (
  id          BIGSERIAL PRIMARY KEY,
  table_name  TEXT NOT NULL,
  record_id   UUID NOT NULL,
  action      TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
  changed_by  UUID REFERENCES users(id),
  old_data    JSONB,
  new_data    JSONB,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- DENORMALIZED COUNTERS (for high-read counts like subscriber_count):
--   Store count on the parent record, update with triggers or application logic
--   Tradeoff: slightly stale counts vs. expensive COUNT(*) on every read
--   Rule: denormalize when COUNT query takes > 50ms under load
```

# CHECKLIST — Before Moving to API Design

```
✅ All entities identified from user stories
✅ ERD drawn (or described in table form)
✅ Schema SQL written for all MVP tables
✅ Constraints: NOT NULL, UNIQUE, CHECK, FOREIGN KEY applied correctly
✅ Indexes defined for all high-frequency query patterns
✅ Migration files created and tested (up + down)
✅ Denormalization decisions documented with justification
✅ No business logic in column names (use status codes, not is_bad_video)
→ NEXT: 04-APIDesign.md
```
