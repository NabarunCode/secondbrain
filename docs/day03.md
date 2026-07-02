# Day 03 — SQLite Catalog, Part 1

Date: 2026-07-02

---

# Working Mode (new as of today)

This project is a learning vehicle first, an app second. See `docs/decisions.md` (2026-07-02, "Working Mode") for the full agreement. Short version: Claude scaffolds and explains, the author writes the logic, Claude reviews and quizzes before moving on.

---

# Today's Goal

Get the SQLite schema designed in `docs/phase1b_catalog_architecture.md` actually running as a real database file, and understand *why* each piece of it works the way it does — not just copy it in.

Concepts to actually understand today (not skim):

- What a SQLite `PRAGMA` is, and specifically what `journal_mode=WAL` and `foreign_keys=ON` change
- `PRIMARY KEY` vs `UNIQUE INDEX` vs a plain `INDEX`
- What a **partial index** is (`WHERE storage_status = 'verified'`) and why it encodes a business rule
- `CHECK` constraints as a way to enforce an enum at the database layer
- The difference between running SQL from a `.sql` file vs from Python's `sqlite3` module

Deliverables:

- `secondbrain/catalog/connection.py` — a function that opens a SQLite connection with the right PRAGMAs set
- `secondbrain/catalog/migrations/0001_initial_schema.sql` — the schema itself
- Manually verify it: open the resulting `.db` file with the `sqlite3` CLI, run `.tables`, `.schema assets`, confirm the partial unique index exists

Not today: migration runner, repository layer, any Python code touching `Asset` objects. That starts Day 04.

---

# Plan for the Rest of Phase 1B (paced, not rushed)

| Day | Focus | New concepts | Deliverable |
|---|---|---|---|
| 03 (today) | Schema + connection | PRAGMAs, constraints, partial indexes | `connection.py`, `0001_initial_schema.sql` |
| 04 | Migration runner | `PRAGMA user_version`, transactions, idempotency | `migrate.py` |
| 05 | Repository, read/write basics | Parameterized SQL, SQL injection, `sqlite3.Row`, Pydantic mapping | `create()`, `get()` on `AssetRepository` |
| 06 | Repository, state + relations | Multi-table transactions, foreign keys, JOINs | `transition_status()`, `add_tags()`/`get_tags()`, `get_by_sha256_verified()` |
| 07 | Testing + end-to-end | `:memory:` DBs, arrange/act/assert, testing that constraints actually reject bad data | `experiments/test_repository.py`, first real `Asset` persisted + retrieved, EOD docs/roadmap update |

This closes out Phase 1B. Pace can compress or stretch depending on how Days 03–04 go — recheck at each EOD.

---

# Completed

- Full Phase 1B catalog architecture review, revised and reconciled against the real `secondbrain/models/asset.py` and the repo's existing empty `catalog/`/`cli/`/`ingest/`/`storage/` scaffold — written to `docs/phase1b_catalog_architecture.md`
- SQLite schema finalized: `assets`, `asset_tags`, `asset_events`, `schema_migrations`, with a partial unique index (`UNIQUE(sha256) WHERE storage_status='verified'`) enforcing the dedup business rule at the database layer
- Working-mode agreement made explicit: learning-first, scaffold-and-review, active-recall checks (see `decisions.md`, 2026-07-02)
- `#SOD`/`#EOD` convention formalized in `docs/readme.md` — file-ownership table, precise checklists, and a note on why fresh chat sessions are expected (context limits / compaction is lossy; the docs are the real memory)
- Confirmed this Cowork workspace is a persistent Project, not a one-off session
- Taught: SQLite connections, `PRAGMA` statements, `journal_mode=WAL` vs the default rollback journal, `foreign_keys=ON`, primary vs. foreign keys, `ON DELETE CASCADE`
- Check-in: author correctly identified all three foreign keys in the schema (`asset_events.asset_id`, `assets.duplicate_of`, `asset_tags.asset_id`) and gave a mostly-correct explanation of WAL's read/write concurrency behavior
- Scaffolded `secondbrain/catalog/connection.py` with 5 TODOs — stopped here for the day before the author attempted them

# Lessons Learned

- Don't assume prior knowledge of relational-database basics (foreign keys) just because the person has deep infra experience — different domain. Backed up and explained it properly once flagged; worth checking, not assuming, on future new-domain concepts too (SQL, Pydantic, HF APIs).
- The active-recall check-ins are working as intended — the foreign-key gap surfaced immediately instead of silently causing confusion three files later.

# Next Session

1. Author attempts the 5 TODOs in `secondbrain/catalog/connection.py` — particularly reason through `check_same_thread` before writing the `sqlite3.connect()` call. Ask if stuck on any single TODO rather than guessing through all five.
2. New concepts before the schema file: `CHECK` constraints, `PRIMARY KEY` vs `UNIQUE INDEX` vs plain `INDEX`, and what a *partial* index is.
3. Create `secondbrain/catalog/migrations/0001_initial_schema.sql` from `docs/phase1b_catalog_architecture.md` §4.
4. Manually verify with the `sqlite3` CLI (`.tables`, `.schema assets`) that the partial unique index actually exists.
5. Nothing has been committed to git since "feat: implement asset schema v1" (two commits ago) — ask before committing anything.
