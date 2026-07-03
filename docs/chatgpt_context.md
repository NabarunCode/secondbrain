# SecondBrain ChatGPT Bootstrap Context

## Project

SecondBrain

Repository:

hf-personal-digital-vault

---

## Current Day

Day 03 (in progress — Phase 1B not yet complete, see Next Session)

---

## Current Phase

Phase 1B — SQLite Catalog Design

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
secondbrain/catalog/migrations/0001_initial_schema.sql   (complete)
```

Not done yet: no migration runner (`migrate.py`), no repository code, no *real* `data/secondbrain.db` created yet (only throwaway test copies), nothing committed to git since the first-half-of-Day-03 commit.

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

---

## Next Session

Day 04 (see `docs/day03.md` "Next Session" for full detail):

1. `secondbrain/catalog/migrate.py` — migration runner: `PRAGMA user_version`, transactions, idempotency
2. Create the real `data/secondbrain.db` for the first time, through `migrate.py` (not manually)
3. Delete stray `schema_check.db` test file from repo root whenever (harmless)
4. Reminder: nothing committed to git since the Day 03 first-half commit — ask the author before committing anything