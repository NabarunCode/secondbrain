-- secondbrain/catalog/migrations/0001_initial_schema.sql
--
-- Full design + rationale for every table, column, constraint, and index:
-- docs/phase1b_catalog_architecture.md §4
--
-- Write the four tables below, in this order (foreign keys point backward,
-- so order matters when building a fresh database):
--
--   1. assets            -- core table: PK, 2 CHECK constraints, 1 self-FK
--   2. asset_tags         -- FK to assets, ON DELETE CASCADE
--   3. asset_events        -- FK to assets
--   4. schema_migrations   -- no FKs; tracks which migrations have run
--
-- Then the indexes (7 total, including the one partial unique index).
--
-- Type it out rather than copy-pasting from the architecture doc — getting
-- a column or constraint wrong is fine, that's what review is for.

PRAGMA foreign_keys = ON;

-- 1. assets
CREATE TABLE assets (
    id                TEXT PRIMARY KEY NOT NULL,         -- ULID -- see decisions.md: SQLite doesn't imply NOT NULL for non-INTEGER PKs

    asset_type        TEXT NOT NULL
                        CHECK (asset_type IN ('photo','note','document','audio','video','other')),
    storage_status    TEXT NOT NULL DEFAULT 'discovered'
                        CHECK (storage_status IN (
                            'discovered','hashing','dedup_check','processing',
                            'uploading','verifying','verified','duplicate','failed'
                        )),
    failure_stage     TEXT,
    duplicate_of      TEXT REFERENCES assets(id),   -- self-FK, no ON DELETE CASCADE (see decisions.md)

    filename          TEXT NOT NULL,
    local_path        TEXT,

    title             TEXT,
    description       TEXT,
    -- tags is NOT a column here -- lives entirely in asset_tags

    bucket_name       TEXT,
    object_key        TEXT,

    mime_type         TEXT NOT NULL,
    size_bytes        INTEGER NOT NULL,
    sha256            TEXT,

    file_modified_at  TEXT NOT NULL,   -- ISO-8601 UTC
    original_date     TEXT,            -- ISO-8601 UTC, nullable

    metadata_json     TEXT,            -- JSON1 blob; the Pydantic dict lives here as text
    thumbnail_path    TEXT,
    embedding_id      TEXT,

    -- Row bookkeeping -- not on the Pydantic model, DB-layer only.
    created_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);


-- 2. asset_tags
CREATE TABLE asset_tags (
	asset_id TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
	tag TEXT NOT NULL,
	PRIMARY KEY (asset_id, tag)
);

-- 3. asset_events
CREATE TABLE asset_events (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	asset_id TEXT NOT NULL REFERENCES assets(id),
	from_status TEXT,
	to_status TEXT NOT NULL,
	occurred_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
	detail TEXT
);

-- 4. schema_migrations
CREATE TABLE schema_migrations(
	version INTEGER PRIMARY KEY NOT NULL,
	filename TEXT NOT NULL,
	applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- Indexes
CREATE UNIQUE INDEX idx_assets_sha256_verified ON assets(sha256) WHERE storage_status = 'verified';
CREATE INDEX idx_assets_sha256 ON assets(sha256);
CREATE INDEX idx_assets_storage_status ON assets(storage_status);
CREATE INDEX idx_assets_asset_type ON assets(asset_type);
CREATE INDEX idx_assets_duplicate_of ON assets(duplicate_of);
CREATE INDEX idx_asset_tags_tag ON asset_tags(tag);
CREATE INDEX idx_asset_events_asset_id ON asset_events(asset_id, occurred_at);


