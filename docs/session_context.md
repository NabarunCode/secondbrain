# SecondBrain Session Bootstrap Context

## Project

SecondBrain

Repository:

hf-personal-digital-vault

---

## Current Day

Day 04 (complete — Phase 1B closed out, see Next Session)

---

## Current Phase

Phase 1B — SQLite Catalog — COMPLETE. Next: Phase 2 — Ingestion.

---

## Working Mode (set Day 03)

This is the author's first project combining Python, OOP, SQL, Pydantic, and API-based platforms. Learning is the primary goal, not fastest completion. Assistant scaffolds files with TODOs and deep-dive explanations; author writes the actual logic; assistant reviews and quizzes before advancing. Full agreement: `decisions.md` (2026-07-02).

**Hard rule, violated repeatedly on Day 03 before being written down — read this every session:** never ask the author to write a line containing syntax that hasn't been explicitly demonstrated first, with a working example. Explaining the *concept* is not enough; the literal *syntax* must be shown too. Full text: `decisions.md`, "Hard Rule: syntax must be shown before it's required."

Session convention: `#SOD` = read this file + `project_context.md` + `architecture.md` + `decisions.md` + latest `dayXX.md` + `roadmap.md`, then recap and resume. `#EOD` = write the session's outcomes back into these files before ending. Full protocol: `docs/readme.md`.

---

## Technology Stack

- Python 3.14
- uv
- Hugging Face Buckets
- SQLite
- Pydantic
- Gradio

---

## Major Architectural Principle

```text
SQLite
    =
Source of Truth

HF Buckets
    =
Blob Storage Backend
```

---

## Completed

### Day 01

- Installed uv
- Initialized project
- Initialized git
- Authenticated to Hugging Face
- Created HF Bucket
- Uploaded first object

Bucket:

```
hinabarun/testproject
```

Object:

```
secondbrain-folder/hello-secondbrain.txt
```

---

### Day 02

Completed:

- Asset lifecycle v1
- Asset schema v1
- Duplicate-safe upload architecture
- Upload verification strategy
- ULID asset identity
- Pydantic Asset model
- AssetType enum
- StorageStatus enum

Created:

```text
secondbrain/models/

    asset.py
    asset_type.py
    storage_status.py
```

Successfully validated:

- Asset object creation
- model_dump()
- model_dump_json()

---

### Day 03

Completed (spans two chat sessions, same calendar day):

- Full Phase 1B catalog architecture review, verified against real `secondbrain/models/` code and the repo's empty `catalog/`/`cli/`/`ingest/`/`storage/` scaffolds — `docs/phase1b_catalog_architecture.md`
- Working-mode agreement + `#SOD`/`#EOD` convention formalized (`docs/readme.md`, `decisions.md`) — confirmed this workspace is a persistent Cowork Project, memory/instructions carry across chats here
- **`secondbrain/catalog/connection.py` — DONE, verified working** (WAL + foreign_keys PRAGMAs, row_factory, directory auto-creation)
- **`secondbrain/catalog/migrations/0001_initial_schema.sql` — DONE, verified working** (4 tables, 7 indexes, dedup rule and CHECK constraints proven to actually reject bad data, not just parse)
- Author caught two real design bugs Claude missed: `asset_events` wrongly had `ON DELETE CASCADE` (would destroy audit history), `assets.id` was missing explicit `NOT NULL` (SQLite quirk: PK doesn't imply NOT NULL except for `INTEGER PRIMARY KEY`). Both fixed and logged.
- Two Hard Rules added after repeated violations: (1) never require syntax that hasn't been shown, (2) verify tool/CLI behavior in Claude's sandbox before asking the author to run it
- Two Future Ideas parked in `roadmap.md`: catalog encryption at rest, real soft-delete design

Created:

```text
docs/phase1b_catalog_architecture.md
docs/day03.md
secondbrain/catalog/connection.py              (complete)
secondbrain/catalog/migrations/0001_initial_schema.sql   (complete, later replaced — see Day 04)
```

Not done yet (at end of Day 03): no migration mechanism, no repository code, no *real* `data/secondbrain.db` created yet.

---

### Day 04

Completed:

- Built the migration runner as planned (`migrate.py`, `PRAGMA user_version`, `schema_migrations` table) — then **reversed it**. The author pushed back: zero real data exists yet in `data/secondbrain.db` (Phase 2 hasn't run), so there's nothing to preserve across schema changes, and the runner was solving a "many migration files" problem that didn't exist (there was exactly one). Replaced with `secondbrain/catalog/schema.sql` (`CREATE ... IF NOT EXISTS` everywhere, no version tracking) + `schema.py::init_db(conn)`. Logged as a correction in `decisions.md`, including when to revisit it (once real assets exist and a schema change needs to `ALTER` rather than just add).
- **`secondbrain/catalog/asset_repository.py` — full Phase 1B surface DONE, verified working**: `create()`, `get()`, `transition_status()`, `add_tags()`/`get_tags()`, `get_by_sha256_verified()`.
- Real bug from actual use (caught by the author, not Claude): re-running the test script raised a raw `sqlite3.IntegrityError` on a duplicate id. Fixed properly, not papered over — `create()` now raises a clear `AssetAlreadyExistsError`; `AssetNotFoundError` added for the same reason in `transition_status()`/`add_tags()`.
- First real `Asset` persisted, retrieved, and round-tripped end-to-end against the real (persistent) `data/secondbrain.db` — proven across two runs.
- Proactively re-reviewed the rest of the Phase 1B code for the same "solving a future phase's problem early" pattern. Found one candidate (WAL journal mode, justified by a Phase 4/Gradio concern) and explicitly decided to keep it — different cost/benefit than the migration runner (one PRAGMA line either way).
- **Phase 1B closed out**: all `roadmap.md` items checked.
- Renamed `docs/chatgpt_context.md` → `docs/session_context.md` — the file's own text already said it applies to "any assistant working on this project, not just ChatGPT"; the name hadn't matched that in a while. `docs/command for chatgpt.txt` (the literal copy-paste bootstrap block for ChatGPT sessions specifically, which lack file access) keeps its name — that one's genuinely ChatGPT-specific — only its file reference was updated.

Created / replaced:

```text
docs/day04.md
docs/session_context.md                 (renamed from chatgpt_context.md)
secondbrain/catalog/schema.sql          (replaces migrations/0001_initial_schema.sql)
secondbrain/catalog/schema.py           (replaces migrate.py)
secondbrain/catalog/asset_repository.py (complete: all 6 methods)
```

---

## Important Decisions

- Use uv
- Use HF Buckets
- Use SQLite
- Use Gradio
- Keep experiments separate
- SQLite is authoritative
- HF Buckets are blob storage
- Store duplicate asset records
- Do not upload duplicate blobs
- Use ULID identifiers
- Idempotent `schema.sql` (no versioned migrations) until real data exists to preserve

---

## Next Session

Day 05 / Phase 2 — Ingestion (see `docs/day04.md` "Next Session" for full detail). This is where real files enter the picture for the first time — everything through Day 04 used one dummy test asset.

1. Discovery: scan a real local folder for real files.
2. SHA256 hashing of real files.
3. Dedup check using `get_by_sha256_verified()` — first real exercise of the method built Day 04.
4. Metadata extraction (EXIF, etc.).
5. Upload pipeline to HF Buckets.
6. Verification step, using `transition_status()` for real.

Reminder: `git status`/`git log` looked inconsistent in Claude's sandbox on Day 04 (likely a sandbox-side mount artifact, not a real repo problem — see `docs/day04.md` "Environment Note") — check directly on the author's machine before committing.
