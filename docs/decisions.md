# Architectural Decisions

## 2026-07-01

### Project Name

Decision:
SecondBrain

Reason:
Memorable and aligned with project goals.

---

### Package Manager

Decision:
uv

Reason:
Modern, fast, becoming industry standard.

---

### Storage

Decision:
Hugging Face Buckets

Reason:
Primary technology being evaluated.

---

### Metadata Store

Decision:
SQLite

Reason:
HF Buckets are object storage, not databases.

---

### UI

Decision:
Gradio

Reason:
Provides a path toward AI interactions.

---

### Repository Structure

Decision:

secondbrain/
    reusable application code

experiments/
    temporary experiments and testing

Reason:
Keep production code separate from experiments.

---

Decision:
SQLite shall be the authoritative catalog.

Rationale:
- supports offline operation
- supports resumability
- supports dedup-safe uploads
- supports provenance
- supports upload verification

---

Decision:
Duplicate files shall be stored as asset records but shall not upload duplicate blobs.

Implementation:
duplicate_of: AssetId | None



---

### Asset Identity

Decision:

Use ULID identifiers.

Implementation:

```python
AssetId = str
```

Reason:

- sortable
- globally unique
- future distributed support
- URL safe

---

### Asset Lifecycle

Decision:

Adopt the following asset lifecycle:

```text
DISCOVERED
    ↓
HASHING
    ↓
DEDUP_CHECK
    ↓
PROCESSING
    ↓
UPLOADING
    ↓
VERIFYING
    ↓
VERIFIED
```

Additional terminal states:

```text
DUPLICATE
FAILED
```

Reason:

Supports:

- resumability
- provenance
- duplicate-safe uploads
- upload verification

---

### Duplicate Detection

Decision:

A duplicate is valid only when:

- SHA256 matches
- referenced asset status == VERIFIED

Reason:

Prevents data loss from failed uploads.

---

### Duplicate Handling

Decision:

Store duplicate asset records,
but do not upload duplicate blobs.

Implementation:

```python
duplicate_of: AssetId | None
```

Reason:

Preserves provenance while avoiding duplicate storage.

---

### Asset Path Retention

Decision:

Retain original local filesystem path.

Implementation:

```python
local_path: Path | None
```

Reason:

- provenance
- migration
- debugging
- re-import

---

### Failure Tracking

Decision:

Track only:

```python
failure_stage
```

Postpone:

```python
failure_reason
```

Reason:

Logging subsystem will be designed later.

---

## 2026-07-02

### Working Mode — Learning-First Collaboration

Decision:

This is the author's first project combining Python, OOP, SQL, Pydantic, and API-based platforms (Hugging Face). The primary goal is deliberate, step-by-step learning, not fastest-path implementation.

Implementation:

- Claude scaffolds files (signatures, docstrings, TODOs) and explains the concept before code is written, wherever the author has enough footing to write the logic themselves.
- Author writes the actual logic; Claude reviews and corrects rather than replacing.
- New concepts (SQL internals, WAL mode, Pydantic validators, HF Bucket APIs, etc.) get a deep-dive explanation before use.
- Claude periodically checks understanding by asking the author to explain a piece back before moving on.
- If the author is blank on a specific piece (expected often, given this is a first project across several new technologies at once), Claude writes that one piece directly, explains it, then hands control back.

Reason:

Optimizes for learning and long-term maintainability by the author, not short-term velocity. Matches the project's own stated philosophy ("teach while building", "explain trade-offs").

---

### Session Shorthand — #SOD / #EOD

Decision:

Adopt `#SOD` (Start of Day) and `#EOD` (End of Day) as explicit session markers, carried over from prior ChatGPT sessions, and apply them to Claude sessions too.

Implementation:

- `#SOD`: read `chatgpt_context.md`, `project_context.md`, `architecture.md`, `decisions.md`, and the latest `dayXX.md` — this is already the documented Session Workflow in `readme.md`, just given a trigger word.
- `#EOD`: update `chatgpt_context.md`, `decisions.md`, and the current `dayXX.md`, and check off completed items in `roadmap.md`.

Reason:

Formalizes the existing Session Workflow with an explicit, memorable trigger; keeps behavior identical across ChatGPT and Claude sessions.

---

### Phase 1B Catalog — Architectural Decisions

Full rationale, schema SQL, and trade-off table: `docs/phase1b_catalog_architecture.md`.

Decision: Tags stored in a normalized `asset_tags(asset_id, tag)` table, not JSON/CSV.
Reason: Roadmap Phase 3 is tag search; needs an indexed real column, not a parsed blob.

Decision: `metadata` stored as a single `metadata_json` TEXT column (SQLite JSON1).
Reason: v1 metadata is read as a whole blob; EAV normalization would be premature before Phase 5.

Decision: Dedup rule enforced at the database layer via a partial unique index — `UNIQUE(sha256) WHERE storage_status = 'verified'`.
Reason: Turns the existing "duplicate only if SHA256 matches AND VERIFIED" rule into a DB constraint instead of trusting application code alone.

Decision: WAL journal mode; one `AssetRepository` facade; short-lived connections per operation.
Reason: Gradio callbacks run on multiple threads; WAL gives concurrent readers + one writer without hand-rolled locking. No connection pool yet.

Decision: Timestamps stored as TEXT ISO-8601 UTC.
Reason: Human-readable in the sqlite3 CLI, sorts correctly as text, round-trips cleanly with Python's `datetime`.

Decision: New append-only `asset_events` table logs every status transition.
Reason: `storage_status` alone only shows current state, not how an asset got there or what failed when — needed for "provenance-aware."

Decision: Repository layer is hand-rolled `sqlite3` + explicit Pydantic mapping, not SQLAlchemy/SQLModel.
Reason: Matches "avoid unnecessary frameworks"; also the more teachable option for a first SQL project.

Decision: Migrations are numbered plain-SQL files applied via a small runner using `PRAGMA user_version`, not Alembic.
Reason: No extra dependency; fully readable diffs; appropriate for a single-file SQLite DB.

Decision: SQLite database file lives at `data/secondbrain.db`, outside the `secondbrain/` package.
Reason: Mirrors the existing production-code vs experiments separation.

Decision: `embedding_id` column stays on `assets`, but no supporting table is built yet.
Reason: What it should point to is a Phase 5 decision — avoid speculative design now.

Decision: Catalog code (Phase 1B) is built inside the existing empty `secondbrain/catalog/` package, not a new top-level package.
Reason: Repo already scaffolds `catalog/`, `ingest/`, `storage/`, `cli/` as the intended layout.

---

### Correction: `asset_events` foreign key must not cascade-delete

Decision:

`asset_events.asset_id` has **no** `ON DELETE CASCADE` (unlike `asset_tags.asset_id`, which correctly does). SQLite's default (no `ON DELETE` clause, `foreign_keys=ON`) applies, which behaves as `RESTRICT`: deleting an `assets` row is blocked while `asset_events` rows still reference it.

Reason:

Caught by the author while writing the migration file: the original design (in the first architecture review pass) had `ON DELETE CASCADE` on `asset_events`, which would silently delete an asset's entire audit/event history the moment the asset itself was deleted — directly contradicting this table's own stated purpose ("append-only," "provenance-aware," per the original `asset_events` decision above). `asset_tags` cascading is fine (current-state metadata, no historical value once the asset is gone); `asset_events` cascading is not (historical record, whose value is precisely that it survives changes to the thing it describes).

Note: there is no "delete an asset" feature designed anywhere in this project yet (no roadmap item, no lifecycle state for it). If one is designed later, a soft-delete (status flag) is more consistent with this system's existing philosophy (never destroy data — see duplicate handling, failed-upload retries) than a hard SQL `DELETE`. Parked in `roadmap.md` under "Future Ideas."

---

### Correction: explicit `NOT NULL` required on `assets.id`

Decision:

`assets.id TEXT PRIMARY KEY` gets an explicit `NOT NULL` added: `TEXT PRIMARY KEY NOT NULL`.

Reason:

Caught by the author while writing the migration file: unlike the SQL standard (where `PRIMARY KEY` always implies `NOT NULL`), SQLite only auto-enforces `NOT NULL` on a primary key when the column is specifically `INTEGER PRIMARY KEY` (SQLite's rowid alias case) — a documented, deliberate SQLite deviation kept for backward compatibility. Our `id` is `TEXT`, not `INTEGER`, so without the explicit `NOT NULL`, SQLite would silently accept a row with `id = NULL`. `asset_events.id` and `schema_migrations.version` are both `INTEGER PRIMARY KEY` and are unaffected; `asset_tags`'s composite `PRIMARY KEY (asset_id, tag)` was already written with explicit `NOT NULL` on both underlying columns, also unaffected.

---

### Hard Rule: syntax must be shown before it's required

Decision:

Claude must never ask the author to write a line of code or SQL containing a syntax pattern that hasn't already been explicitly demonstrated, with a working example, earlier in the same task. Explaining the underlying *concept* (what a partial index does, why `check_same_thread` matters) does **not** satisfy this — the literal *syntax* (how it's written, character for character) must also have been shown separately.

Concrete check before writing any "now you write X" prompt: can I point to the exact syntax pattern, already demonstrated, for every new construct required in X? If not, show it first, then ask.

Reason:

This rule was promised once already today (after the PRAGMA/`conn.execute` incident) and broken twice more since (the multi-word negation/`sqlite3.Connection` mixup, and asking for a composite `PRIMARY KEY` with zero syntax shown). A promise made mid-conversation and not written down doesn't survive the next few turns, let alone a new session — exactly the failure mode this whole docs system exists to prevent. If the author ever has to ask "did you show me this syntax," that is a rule violation on Claude's part, not a gap in the author's preparation.

---

### Hard Rule: verify tool/CLI behavior in sandbox before asking the author to run it

Decision:

Before giving the author any command whose exact behavior Claude hasn't already confirmed (a specific tool's flags, a REPL's supported commands, a CLI's exact output), Claude tests it in its own sandbox first. Only hand over commands already confirmed to work.

Reason:

Claude told the author `python -m sqlite3`'s interactive shell supported `.tables` and `.read` (assuming parity with the native `sqlite3` CLI) without checking. It didn't. The author burned several back-and-forth turns debugging a tool behavior Claude could have verified itself in seconds, since Claude has its own sandbox with Python available. Same underlying failure as the syntax rule above (asserting something as fact without having actually confirmed it), extended to tool/CLI behavior generally, not just taught syntax.