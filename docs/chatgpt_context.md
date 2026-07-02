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

Completed:

- Full Phase 1B catalog architecture review, verified against real `secondbrain/models/` code and the repo's empty `catalog/`/`cli/`/`ingest/`/`storage/` scaffolds
- SQLite schema designed: `assets`, `asset_tags`, `asset_events` (new — append-only audit trail), `schema_migrations`, with a partial unique index enforcing the dedup rule at the DB layer
- Repository layer, persistence, and migration strategy designed (hand-rolled `sqlite3` + Pydantic, plain-SQL migrations via `PRAGMA user_version`)
- Working-mode agreement established: learning-first, scaffold-and-review, active-recall checks
- `#SOD`/`#EOD` convention formalized in `docs/readme.md`, including a file-ownership table and a note that fresh chat sessions are expected regularly (context/compaction limits) — this docs system is the actual memory, not chat history
- Confirmed this workspace is a persistent Cowork Project (not a one-off session) — memory/instructions do carry across chats here
- Started teaching SQLite fundamentals: PRAGMAs, WAL mode, `foreign_keys=ON`, primary/foreign keys, `ON DELETE CASCADE` — author correctly identified all three foreign keys in the schema
- Scaffolded `secondbrain/catalog/connection.py` (5 TODOs) — **not yet completed by author**

Created:

```text
docs/phase1b_catalog_architecture.md
docs/day03.md
secondbrain/catalog/connection.py   (skeleton, TODOs pending)
```

Not done yet: migrations file not created, no repository code, no SQLite database file exists yet, nothing committed to git since two commits ago.

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

Resume Day 03 (or start Day 04 — see `docs/day03.md` for the paced plan through Day 07):

1. Finish the 5 TODOs in `secondbrain/catalog/connection.py` (author attempts, especially the `check_same_thread` reasoning; assistant reviews)
2. Explain CHECK constraints, `PRIMARY KEY` vs `UNIQUE INDEX` vs plain `INDEX`, and partial indexes
3. Create `secondbrain/catalog/migrations/0001_initial_schema.sql` from the design in `docs/phase1b_catalog_architecture.md` §4
4. Manually verify with the `sqlite3` CLI: `.tables`, `.schema assets`, confirm the partial unique index exists
5. Reminder: nothing has been committed to git since "feat: implement asset schema v1" — ask the author before committing