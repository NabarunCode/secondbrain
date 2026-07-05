-- secondbrain/catalog/schema.sql
--
-- Full design + rationale for every table, column, constraint, and index:
-- docs/phase1b_catalog_architecture.md §4
--
-- Every statement is IF NOT EXISTS: this file is safe to run on every app
-- startup, against a brand-new file or an existing one. No version number,
-- no migrations table, no runner. There is no real data in this catalog
-- yet, so there's nothing to preserve across schema changes -- when the
-- schema needs to change, edit this file directly and delete
-- data/secondbrain.db to pick it up. A real migration mechanism (numbered
-- files, applied in order, tracked so each runs once) becomes worth
-- building the day this database holds real assets we can't just recreate.
-- See docs/decisions.md, 2026-07-03 correction.

PRAGMA foreign_keys = ON;

-- 1. assets
CREATE TABLE IF NOT EXISTS assets (
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
CREATE TABLE IF NOT EXISTS asset_tags (
	asset_id TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
	tag TEXT NOT NULL,
	PRIMARY KEY (asset_id, tag)
);

-- 3. asset_events
CREATE TABLE IF NOT EXISTS asset_events (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	asset_id TEXT NOT NULL REFERENCES assets(id),
	from_status TEXT,
	to_status TEXT NOT NULL,
	occurred_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
	detail TEXT
);

-- Indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_assets_sha256_verified ON assets(sha256) WHERE storage_status = 'verified';
CREATE INDEX IF NOT EXISTS idx_assets_sha256 ON assets(sha256);
CREATE INDEX IF NOT EXISTS idx_assets_storage_status ON assets(storage_status);
CREATE INDEX IF NOT EXISTS idx_assets_asset_type ON assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_assets_duplicate_of ON assets(duplicate_of);
CREATE INDEX IF NOT EXISTS idx_asset_tags_tag ON asset_tags(tag);
CREATE INDEX IF NOT EXISTS idx_asset_events_asset_id ON asset_events(asset_id, occurred_at);

-- TODO (Phase 2 Discovery, docs/phase2_ingestion_architecture.md §4):
-- Add idx_assets_local_path_active -- a UNIQUE INDEX on assets(local_path),
-- partial: WHERE storage_status != 'failed'. Same shape as
-- idx_assets_sha256_verified two lines above, just a different column and
-- a different WHERE condition. Stops Discovery from creating a second
-- catalog row for a file it's already tracking.

CREATE UNIQUE INDEX IF NOT EXISTS idx_assets_local_path_active ON assets(local_path) WHERE storage_status!='failed';
