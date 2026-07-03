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

**From the first half of the day (architecture + connection.py scaffold):**
- Full Phase 1B catalog architecture review, revised and reconciled against the real `secondbrain/models/asset.py` and the repo's existing empty `catalog/`/`cli/`/`ingest/`/`storage/` scaffold — written to `docs/phase1b_catalog_architecture.md`
- SQLite schema finalized: `assets`, `asset_tags`, `asset_events`, `schema_migrations`, with a partial unique index (`UNIQUE(sha256) WHERE storage_status='verified'`) enforcing the dedup business rule at the database layer
- Working-mode agreement made explicit: learning-first, scaffold-and-review, active-recall checks (see `decisions.md`, 2026-07-02)
- `#SOD`/`#EOD` convention formalized in `docs/readme.md` — file-ownership table, precise checklists, and a note on why fresh chat sessions are expected (context limits / compaction is lossy; the docs are the real memory)
- Confirmed this Cowork workspace is a persistent Project, not a one-off session
- Taught: SQLite connections, `PRAGMA` statements, `journal_mode=WAL` vs the default rollback journal, `foreign_keys=ON`, primary vs. foreign keys, `ON DELETE CASCADE`
- Scaffolded `secondbrain/catalog/connection.py` with 5 TODOs

**From the second half (same day, new chat session — resumed via `#SOD`):**
- `secondbrain/catalog/connection.py` **completed and verified** — all 5 TODOs written by the author, reviewed, tested end-to-end (real connection, directory auto-created, `row_factory` set, `journal_mode=wal` and `foreign_keys=1` both confirmed via `PRAGMA` readback)
- Taught: index fundamentals (`PRIMARY KEY` vs `UNIQUE INDEX` vs plain `INDEX`, read/write trade-off of indexing), why a plain unique index would break the dedup rule (two concrete lifecycle scenarios), `CHECK` constraints as defense-in-depth alongside Pydantic validation, partial indexes
- `secondbrain/catalog/migrations/0001_initial_schema.sql` **completed and verified** — all 4 tables and 7 indexes written by the author (with review/corrections along the way), verified against a real SQLite engine including proof the dedup rule and `CHECK` constraint actually reject bad data, not just "the SQL parses"
- **Two real design bugs caught by the author, not by Claude:**
  - `asset_events` had `ON DELETE CASCADE`, which would silently destroy audit history when an asset is deleted — contradicts the table's own "append-only" purpose. Fixed (no cascade; deletes are now blocked by default while history exists). Logged in `decisions.md` and corrected in `phase1b_catalog_architecture.md`.
  - `assets.id TEXT PRIMARY KEY` was missing explicit `NOT NULL` — SQLite (unlike standard SQL) doesn't imply `NOT NULL` on a primary key unless it's `INTEGER PRIMARY KEY`. Fixed, logged.
- Two "Future Ideas" added to `roadmap.md`: encrypting the catalog file at rest (SQLCipher-style), and designing a real soft-delete feature later instead of hard `DELETE`
- Two **Hard Rules** written into `decisions.md` (and surfaced in `chatgpt_context.md`'s Working Mode section) after repeated violations: (1) never ask the author to write syntax that hasn't been explicitly shown first, (2) verify tool/CLI behavior in Claude's own sandbox before asking the author to run it on their machine
- Attempted (and abandoned, by author's choice) a manual `sqlite3` CLI walkthrough — Python's `python -m sqlite3` module doesn't support `.tables`/`.read` the way the native CLI does; this is what surfaced Hard Rule #2

# Lessons Learned

- Don't assume prior knowledge of relational-database basics (foreign keys) just because the person has deep infra experience — different domain. Worth checking, not assuming, on new-domain concepts generally (SQL, Pydantic, HF APIs).
- The active-recall check-ins are working as intended — the foreign-key gap surfaced immediately instead of silently causing confusion three files later. Same pattern later in the day: the author caught two real schema bugs (`ON DELETE CASCADE` on an audit table, missing `NOT NULL` on a primary key) that a less engaged reviewer would have missed.
- Repeatedly asked the author to write syntax that was never actually shown — multiple times, despite promising to fix it after the first occurrence. A spoken promise mid-conversation doesn't survive more than a few turns; it has to be written into the docs as an actual rule to hold. Now is (twice).
- Presented a tool's behavior (`python -m sqlite3`'s dot-commands) as fact without verifying it first, even though verification was trivially available (Claude's own sandbox). Cost the author real time debugging a non-issue on their end. Same class of failure as the syntax rule, now also written down.
- When a mistake costs the other person something real (time, in this case), own it plainly and fix the process — don't just apologize. The author correctly wasn't interested in an apology, just a fix.

# Next Session (Day 04)

1. `secondbrain/catalog/migrate.py` — the migration runner: `PRAGMA user_version`, transactions, idempotency (apply only pending migrations). New concepts, teach before code, syntax shown before required (per the Hard Rules).
2. Actually create the real `data/secondbrain.db` for the first time, through `migrate.py` — not through manual poking, so `schema_migrations`/`user_version` bookkeeping stays consistent from the start.
3. Delete the stray `schema_check.db` test file from the repo root whenever convenient (harmless, not urgent).
4. Nothing has been committed to git since the Day 03 first-half commit — remind the author before committing; today's second half (migration file, decisions.md corrections, both Hard Rules, roadmap Future Ideas) is all uncommitted.
