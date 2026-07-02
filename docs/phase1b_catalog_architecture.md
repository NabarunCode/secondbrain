# SecondBrain — Phase 1B: SQLite Catalog Architecture Review

Repository: `hf-personal-digital-vault` · Day 02 → Day 03 handover · Role: Architect / Mentor

*Verified against the real `secondbrain/models/asset.py`, `asset_type.py`, `storage_status.py`, and the existing empty scaffold folders.*

---

## 1. Understanding Recap

SQLite is the source of truth for everything about an asset (identity, state, provenance, dedup); HF Buckets are dumb blob storage. Day 01–02 delivered: bucket connectivity, the `StorageStatus` lifecycle (`DISCOVERED → HASHING → DEDUP_CHECK → PROCESSING → UPLOADING → VERIFYING → VERIFIED`, terminal `DUPLICATE`/`FAILED`), the dedup rule (SHA256 match **and** existing asset `VERIFIED`), ULID identity, and a validated Pydantic `Asset` model — nothing persisted yet. Phase 1B is purely about the catalog: schema, indexes, repository, persistence, migrations. No ingestion, no upload code.

The repo already has the target layout scaffolded as empty packages: `secondbrain/catalog/`, `secondbrain/cli/`, `secondbrain/ingest/`, `secondbrain/storage/`, alongside the populated `secondbrain/models/`. `catalog/` is clearly meant to be Phase 1B's home — the plan below builds there instead of inventing a new package. `pyproject.toml` confirms `gradio`, `pydantic`, `typer`, `rich`, `pillow`, `python-dotenv` as the only dependencies — no ORM, no migration framework — which validates the hand-rolled `sqlite3` + plain-SQL-migrations direction in §3 rather than requiring a new decision.

## 2. Critical Review of What Exists

**Solid decisions, worth keeping as-is:**
- SQLite-as-truth / buckets-as-blob is the right split for an offline-first, single-user system — don't second-guess it.
- Tying "duplicate" to `VERIFIED` status (not just hash match) is the correct call — it's the one piece of business logic that actually deserves to be enforced at the database layer (see §4).
- ULID over UUID4: lexicographically sortable, so B-tree insert locality stays good even as a TEXT primary key.
- Retaining `local_path` and nullable `bucket_name`/`object_key` correctly models "asset exists before it's uploaded."

**Gaps — decisions the docs don't make yet:**
The lifecycle and Pydantic model describe the *shape* of an asset but not how it lives in a database that will be written to from a Gradio UI thread and (eventually) a background ingestion worker at the same time. None of the following were mentioned anywhere in `architecture.md` or `decisions.md` before this session:

1. How `tags` gets stored (list on the Pydantic model, but SQLite has no array type).
2. How `metadata` (the catch-all dict) gets stored/queried.
3. Whether the dedup rule is enforced by application code only, or also by the database.
4. Concurrency/connection model for a Gradio app + future worker process.
5. Timestamp representation.
6. Whether state transitions themselves need to be logged.
7. Repository layer shape — raw SQL vs ORM.
8. Migration mechanism.

## 3. Missing Architectural Decisions (proposed defaults)

| # | Decision | Recommendation | Why now, not later |
|---|---|---|---|
| 1 | Tags storage | Normalized `asset_tags(asset_id, tag)` table, not a JSON/CSV column | Roadmap Phase 3 is tag search. Indexed exact-match lookup on a join table is trivial; on a JSON column it means parsing every row. |
| 2 | Metadata storage | Single `metadata_json TEXT` column (SQLite JSON1) | v1 metadata is read as a whole blob, not filtered field-by-field. EAV normalization is premature. |
| 3 | Dedup enforcement | Partial **unique** index: `UNIQUE(sha256) WHERE storage_status = 'verified'` | Turns the business rule into a DB constraint instead of trusting application code alone. |
| 4 | Concurrency model | WAL journal mode + one `AssetRepository` facade; short-lived connection per operation | Gradio callbacks run on multiple threads. WAL gives concurrent readers + one writer without hand-rolled locking. |
| 5 | Timestamps | `TEXT` ISO-8601 UTC | Human-readable in `sqlite3` CLI, sorts correctly as text, round-trips cleanly with Python's `datetime`. |
| 6 | State-transition history | New table: `asset_events` (append-only) | `storage_status` alone only shows current state, not how an asset got there or what failed when. |
| 7 | Repository layer | Hand-rolled `sqlite3` + Pydantic mapping, not SQLAlchemy/SQLModel | Matches "avoid unnecessary frameworks"; more teachable for a first SQL project. |
| 8 | Migrations | Numbered plain-SQL files + a tiny runner using `PRAGMA user_version` | No extra dependency; fully readable diffs. |
| 9 | DB file location | `data/secondbrain.db`, outside the `secondbrain/` package | Mirrors the existing production-code vs experiments separation. |
| 10 | `embedding_id` | Column stays, no table yet | What it points to is a Phase 5 decision — avoid speculative design now. |

## 4. SQLite Schema

```sql
-- 0001_initial_schema.sql

PRAGMA foreign_keys = ON;

CREATE TABLE assets (
    id                TEXT PRIMARY KEY,                 -- ULID
    asset_type        TEXT NOT NULL
                        CHECK (asset_type IN ('photo','note','document','audio','video','other')),
    storage_status    TEXT NOT NULL DEFAULT 'discovered'
                        CHECK (storage_status IN (
                            'discovered','hashing','dedup_check','processing',
                            'uploading','verifying','verified','duplicate','failed'
                        )),
    failure_stage     TEXT,
    duplicate_of      TEXT REFERENCES assets(id),

    filename          TEXT NOT NULL,
    local_path        TEXT,

    title             TEXT,
    description       TEXT,

    bucket_name       TEXT,
    object_key        TEXT,

    mime_type         TEXT NOT NULL,
    size_bytes        INTEGER NOT NULL,
    sha256            TEXT,

    file_modified_at  TEXT NOT NULL,   -- ISO-8601 UTC
    original_date     TEXT,            -- ISO-8601 UTC, nullable (matches Pydantic Optional)

    metadata_json     TEXT,        -- JSON1 blob, freeform
    thumbnail_path    TEXT,
    embedding_id      TEXT,

    created_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- Enforces: "duplicate is only valid when SHA256 matches AND existing asset is VERIFIED"
CREATE UNIQUE INDEX idx_assets_sha256_verified
    ON assets(sha256)
    WHERE storage_status = 'verified';

-- General-purpose hash lookup during DEDUP_CHECK, regardless of status
CREATE INDEX idx_assets_sha256 ON assets(sha256);

-- Pipeline queries: "resume everything stuck in UPLOADING"
CREATE INDEX idx_assets_storage_status ON assets(storage_status);

CREATE INDEX idx_assets_asset_type ON assets(asset_type);
CREATE INDEX idx_assets_duplicate_of ON assets(duplicate_of);

CREATE TABLE asset_tags (
    asset_id TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    tag      TEXT NOT NULL,
    PRIMARY KEY (asset_id, tag)
);

CREATE INDEX idx_asset_tags_tag ON asset_tags(tag);

-- Append-only provenance trail
CREATE TABLE asset_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id    TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    from_status TEXT,
    to_status   TEXT NOT NULL,
    occurred_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    detail      TEXT       -- free text or small JSON, e.g. failure reason
);

CREATE INDEX idx_asset_events_asset_id ON asset_events(asset_id, occurred_at);

CREATE TABLE schema_migrations (
    version     INTEGER PRIMARY KEY,
    filename    TEXT NOT NULL,
    applied_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
```

## 5. Repository Layer

Builds inside the existing (currently empty) `secondbrain/catalog/` scaffold rather than a new top-level package:

```text
secondbrain/
├── models/                    # existing — asset.py, asset_type.py, storage_status.py
├── catalog/                   # existing empty folder — Phase 1B lives here
│   ├── __init__.py
│   ├── connection.py          # get_connection(): sqlite3.connect + PRAGMAs (WAL, foreign_keys)
│   ├── migrate.py             # runner: reads PRAGMA user_version, applies pending *.sql files
│   ├── migrations/
│   │   └── 0001_initial_schema.sql
│   └── asset_repository.py
├── ingest/                    # existing empty folder — Phase 2, not touched this session
├── storage/                   # existing empty folder — HF Bucket blob wrapper, Phase 2
└── cli/                       # existing empty folder — Typer entrypoint, later
```

`AssetRepository` — the only code allowed to touch SQL:

```python
class AssetRepository:
    def __init__(self, conn: sqlite3.Connection): ...

    def create(self, asset: Asset) -> None: ...
    def get(self, asset_id: str) -> Asset | None: ...
    def get_by_sha256_verified(self, sha256: str) -> Asset | None: ...
    def list_by_status(self, status: StorageStatus) -> list[Asset]: ...

    def transition_status(
        self, asset_id: str, to_status: StorageStatus,
        failure_stage: str | None = None, detail: str | None = None,
    ) -> None:
        """Updates assets.storage_status AND inserts an asset_events row,
        in a single transaction."""

    def add_tags(self, asset_id: str, tags: list[str]) -> None: ...
    def get_tags(self, asset_id: str) -> list[str]: ...
```

Row ↔ Pydantic mapping is explicit (`sqlite3.Row` → `dict` → `Asset.model_validate(...)`), with `metadata_json` decoded via `json.loads`/`json.dumps` at the repository boundary.

## 6. Persistence Strategy

- DB file: `data/secondbrain.db` (gitignored).
- On every connection: `PRAGMA journal_mode=WAL;` and `PRAGMA foreign_keys=ON;`.
- Every status change goes through `transition_status()`, writing the `assets` update and the `asset_events` insert in one transaction.
- Connections are short-lived (opened per operation), not a long-lived global.

## 7. Migration Strategy

- `secondbrain/catalog/migrations/000N_description.sql`, applied in order.
- Runner: read `PRAGMA user_version`; for each migration file with version > current, run it inside a transaction, then `PRAGMA user_version = N` and insert a row into `schema_migrations`.
- No rollback tooling in v1 — "restore from the last backup" is the rollback story for a single-developer local SQLite file.

## 8. Trade-offs, Explicit

| Choice | What you gain | What you give up |
|---|---|---|
| TEXT ULID primary key | Stable external identity, usable directly as part of `object_key` | Slightly larger index than an INTEGER rowid; acceptable at personal-archive scale |
| Normalized tags table | Indexed tag search, ready for Phase 3 | One extra join, slightly more write-path code than a JSON column |
| JSON column for metadata | No premature schema for wildly variable EXIF/extracted fields | Can't index individual metadata fields until promoted to a real column |
| Partial unique index for dedup | Business rule enforced by the database, not just application code | SQLite-specific syntax (fine — not porting DBs) |
| `asset_events` audit table | Full provenance, debuggable resumes, blog material | Every transition writes to two tables instead of one |
| Hand-rolled repository over ORM | Full visibility into every query, no framework to learn | More boilerplate than SQLAlchemy would generate |
| Plain-SQL migrations over Alembic | Zero extra dependency, fully readable diffs | No autogenerate diffing, no built-in downgrade |

## 9. Implementation Plan

See `docs/day03.md` onward for the day-by-day breakdown of this plan, paced for learning rather than fastest completion.

1. `secondbrain/catalog/connection.py` — connection factory with WAL + foreign_keys PRAGMAs.
2. `secondbrain/catalog/migrations/0001_initial_schema.sql` — schema from §4.
3. `secondbrain/catalog/migrate.py` — migration runner (`user_version` check + apply pending).
4. `secondbrain/catalog/asset_repository.py` — implement `create`, `get`, `get_by_sha256_verified`, `transition_status`, `add_tags`, `get_tags`.
5. `experiments/test_repository.py` — round-trip test against `:memory:` SQLite.
6. Persist and retrieve the first real `Asset` object end-to-end.
7. EOD: update `docs/day0X.md`, `docs/decisions.md`, `docs/roadmap.md`.
