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

- `#SOD`: read `session_context.md`, `project_context.md`, `architecture.md`, `decisions.md`, and the latest `dayXX.md` — this is already the documented Session Workflow in `readme.md`, just given a trigger word.
- `#EOD`: update `session_context.md`, `decisions.md`, and the current `dayXX.md`, and check off completed items in `roadmap.md`.

(`chatgpt_context.md` renamed to `session_context.md` 2026-07-03 — see correction below.)

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

Decision: ~~Migrations are numbered plain-SQL files applied via a small runner using `PRAGMA user_version`, not Alembic.~~ Superseded 2026-07-03 — see correction below.
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

### Correction: versioned migration runner replaced with a single idempotent `schema.sql`

Decision:

Dropped the numbered-migration-files + `PRAGMA user_version` runner (`migrate.py`, `migrations/000N_*.sql`, `schema_migrations` table) built on Day 04. Replaced with `secondbrain/catalog/schema.sql` (every statement `CREATE ... IF NOT EXISTS`) plus `secondbrain/catalog/schema.py::init_db(conn)`, which just executes that one file. Safe to call on every app startup, new database or existing one.

Reason:

The author pushed back: `data/secondbrain.db` holds zero real data — Phase 2 (ingestion) hasn't run yet — so there is nothing a migration needs to preserve right now. The entire point of versioned migrations is applying schema changes to a database *without losing existing data*; with no existing data, that problem doesn't exist yet, and the runner (tracking which of potentially many files had been applied, in order, exactly once) was solving a problem — multiple migration files — that also didn't exist yet (there was exactly one). Same shape of mistake as the transaction/rollback over-engineering caught earlier the same day: building for a scenario that will exist later instead of the one that exists now.

When this decision should be revisited: the day `data/secondbrain.db` holds real photos/documents worth not losing (Phase 2+) and the schema needs to change out from under that real data. At that point `CREATE TABLE IF NOT EXISTS` stops being sufficient — it only creates *new* tables, it cannot `ALTER` an existing one safely — and a real migration mechanism becomes a genuine, not speculative, need. Until then: edit `schema.sql` directly, delete `data/secondbrain.db`, let `init_db()` recreate it.

---

### Correction: `chatgpt_context.md` renamed to `session_context.md`

Decision:

Renamed `docs/chatgpt_context.md` to `docs/session_context.md`. All references updated in `readme.md`, `decisions.md`, and `docs/command for chatgpt.txt` (content only — that file's own name stays as-is, since it genuinely is the ChatGPT-specific copy-paste bootstrap block, used because ChatGPT lacks direct file access the way a Cowork session has).

Reason:

The file's own opening line already said the `#SOD`/`#EOD` workflow "applies to any assistant working on this project, not just ChatGPT." The name was a leftover from before Cowork/Claude sessions existed, no longer matched what the file actually said or did. References inside historical `dayXX.md` logs were left as-is (they're an accurate record of what the file was called at the time, not a live spec).

---

### Correction: git commit convention — one combined commit per session, not docs/code split

Decision:

`readme.md`'s "Commit documentation" / "Commit code separately" two-step convention replaced with a single `git add . && git commit && git push` per session.

Reason:

The split convention was written on Day 03 without being tested against how work actually happens here. It's a team-project pattern (clean changelog generation, `git bisect` isolating docs noise from code regressions) that doesn't apply to a solo project with no CI and no automated tests yet. It also worked against the project's own stated framing — "the code *and* the docs in this repo are both part of the story" — by putting them in separate commits. Same root issue as the migration-runner correction above: adopting a convention that sounds like good practice in the abstract without checking it against this project's actual current stage.

---

### Hard Rule: syntax must be shown before it's required

Decision:

Claude must never ask the author to write a line of code or SQL containing a syntax pattern that hasn't already been explicitly demonstrated, with a working example, earlier in the same task. Explaining the underlying *concept* (what a partial index does, why `check_same_thread` matters) does **not** satisfy this — the literal *syntax* (how it's written, character for character) must also have been shown separately.

Concrete check before writing any "now you write X" prompt: can I point to the exact syntax pattern, already demonstrated, for every new construct required in X? If not, show it first, then ask.

**Clarified 2026-07-05:** pointing at an existing method *in the file* as "the pattern" does not satisfy this rule if the author didn't write that existing method themselves. `get_by_sha256_verified()` was written by Claude during the Day 04 drift — its presence in the file is not the same as the `?`/tuple-parameter mechanism and `.fetchone()` having been demonstrated to this author. "Already demonstrated" means demonstrated to the person, in this conversation (or a prior one they were actively part of) — not merely present somewhere in the codebase.

Reason:

This rule was promised once already today (after the PRAGMA/`conn.execute` incident) and broken twice more since (the multi-word negation/`sqlite3.Connection` mixup, and asking for a composite `PRIMARY KEY` with zero syntax shown). A promise made mid-conversation and not written down doesn't survive the next few turns, let alone a new session — exactly the failure mode this whole docs system exists to prevent. If the author ever has to ask "did you show me this syntax," that is a rule violation on Claude's part, not a gap in the author's preparation. Violated again on Day 05 in this new "pointing at existing code" shape — the clarification above closes that specific loophole.

---

### Hard Rule: verify tool/CLI behavior in sandbox before asking the author to run it

Decision:

Before giving the author any command whose exact behavior Claude hasn't already confirmed (a specific tool's flags, a REPL's supported commands, a CLI's exact output), Claude tests it in its own sandbox first. Only hand over commands already confirmed to work.

Reason:

Claude told the author `python -m sqlite3`'s interactive shell supported `.tables` and `.read` (assuming parity with the native `sqlite3` CLI) without checking. It didn't. The author burned several back-and-forth turns debugging a tool behavior Claude could have verified itself in seconds, since Claude has its own sandbox with Python available. Same underlying failure as the syntax rule above (asserting something as fact without having actually confirmed it), extended to tool/CLI behavior generally, not just taught syntax.

---

## 2026-07-05

### Reaffirmed: scaffold-and-teach working mode, for Phase 2 onward

Decision:

All of Day 04 was built by Claude writing code directly (schema.py, asset_repository.py, etc.) rather than scaffolding it for the author to write, a silent drift from the Day 02 Working Mode agreement. Starting Phase 2, reverting explicitly: Claude scaffolds (signatures, docstrings, TODOs), explains the concept, and — per the existing Hard Rule — shows the exact syntax needed before asking the author to write anything with it. The author writes the logic; Claude reviews.

Also reaffirmed: Phase 2 gets an architecture review doc (`phase2_ingestion_architecture.md`) before any code, same as Phase 1B's `phase1b_catalog_architecture.md`.

Reason:

The author explicitly said the goal is learning, not shipping fast — direct implementation optimizes for the wrong thing here. Worth naming explicitly rather than letting Day 04's pace quietly become the new default.

---

### Phase 2 Ingestion — Discovery: architectural decisions

Full rationale: `docs/phase2_ingestion_architecture.md`. Scoped to Discovery only — Phase 2's other five items (hashing, dedup, metadata, upload, verification) get their own design passes later, same pacing as Phase 1B.

Decision: Traversal via `pathlib.Path.rglob("*")`, not `os.walk`.
Reason: Recursive in one call, stdlib only.

Decision: `AssetType` classified by file extension via a lookup table; `note` is never produced by Discovery.
Reason: No file extension naturally means "note" — reserved for something typed directly into the app later (Phase 4), not a discovered file.

Decision: `mime_type` via stdlib `mimetypes.guess_type()`.
Reason: No new dependency; extension-based is good enough for v1.

Decision: Discovery checks `get_by_local_path()` before `create()`, skipping files already tracked in a non-`FAILED` status; enforced at the DB layer via a new partial unique index (`idx_assets_local_path_active`, `WHERE storage_status != 'failed'`), mirroring `idx_assets_sha256_verified` exactly.
Reason: Without this, re-running Discovery on an already-scanned folder creates duplicate catalog rows for the same physical file — contradicts the README's "Resumable" principle. `!= 'failed'` rather than `= 'discovered'` so a file mid-pipeline (hashing, uploading, etc.) is still caught; only a previously `FAILED` attempt allows a fresh row.

Decision: Errors during discovery (unreadable/in-use files) are skip-and-report, not fail-fast.
Reason: A personal-archive tool scanning real, messy folders will hit bad files; failing the whole scan over one is worse than skipping and reporting at the end.

---

### Hard Rule: format chat responses for readability — spacing/emojis, not dense paragraphs

Decision:

Claude's chat responses (not files written to the repo — those stay plain prose/code, no emojis) should use short chunks, line breaks, and light emoji use as visual markers, rather than long unbroken paragraphs. Closer to how ChatGPT typically formats a reply than a dense wall of text.

Reason:

The author found long paragraph-after-paragraph responses hard to read. Explicitly requested this be persisted as a standing rule, not a one-off ask — same reasoning as the other two Hard Rules: a preference stated once mid-conversation doesn't survive into the next session unless it's written down.