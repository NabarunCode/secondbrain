# Day 04 — SQLite Catalog, Part 2: Repository Layer, Phase 1B Closeout

Date: 2026-07-03

---

# Today's Goal

Per the Day 03 plan: build the migration runner, then the repository layer. What actually happened diverged from that plan partway through, and the divergence is worth recording, not smoothing over.

---

# Completed

**Migration runner — built, then reversed:**

- Built `secondbrain/catalog/migrate.py` as originally planned: numbered `.sql` files, `PRAGMA user_version` tracking, a `schema_migrations` table, a runner that applies pending files in order.
- The author pushed back: `data/secondbrain.db` holds zero real data (Phase 2 ingestion hasn't run yet), so there's nothing a migration needs to preserve right now, and the runner (tracking *multiple* migration files applied in order, exactly once) was solving a problem — more than one migration file — that didn't exist either (there was exactly one). Same shape of mistake as the transaction/rollback over-engineering caught earlier the same week: building for a scenario that will exist later instead of the one that exists now.
- Reversed: `migrate.py` and `migrations/0001_initial_schema.sql` replaced with `secondbrain/catalog/schema.sql` (every statement `CREATE ... IF NOT EXISTS`, no version number, no tracking table) and `schema.py::init_db(conn)`, which just executes it. Safe to call on every app startup, new database or existing one.
- Old `migrate.py`/`migrations/0001_initial_schema.sql` couldn't be deleted from disk (sandbox permissions issue on Claude's side); left as one-line pointer comments to `schema.py`, safe to delete by hand.
- Logged as a correction, not a silent edit: `docs/decisions.md` ("Correction: versioned migration runner replaced with a single idempotent `schema.sql`"), including *when this should be revisited* — the day the catalog holds real assets and a schema change needs to `ALTER` an existing table rather than just add a new one. `docs/phase1b_catalog_architecture.md` §7 and its decision/trade-off tables updated to match.

**Repository layer — completed, full Phase 1B surface:**

- `create()` and `get()` — already existed, re-verified against the new `schema.py`.
- `transition_status(asset_id, to_status, detail)` — updates `assets.storage_status` and inserts a row into `asset_events` (from/to/detail), both in one implicit transaction. This is the audit-trail mechanism the schema was designed around on Day 03.
- `add_tags(asset_id, tags)` / `get_tags(asset_id)` — `add_tags` uses `INSERT OR IGNORE` since tags are a set, not a log (adding a tag that's already there is a no-op, unlike a duplicate asset id, which is an error).
- `get_by_sha256_verified(sha256)` — the dedup lookup; exercises the partial unique index from Day 03 (`WHERE storage_status = 'verified'`). Verified it returns `None` before an asset reaches `VERIFIED` and the correct row after.
- Refactored the row→`Asset` mapping out of `get()` into a private `_asset_from_row()`, shared with `get_by_sha256_verified()`.

**Real bug, caught by the author from actual usage — not by Claude:**

- Running `experiments/test_repository.py` a second time against the same (correctly persisted) `data/secondbrain.db` raised a raw `sqlite3.IntegrityError: UNIQUE constraint failed: assets.id` — the script's hardcoded test id collided with the row the first run had already written.
- First fix attempt (generating a fresh id per run) was rejected by the author as papering over the problem rather than fixing it: `create()` should report a duplicate clearly, not let a low-level DB exception leak out.
- Actual fix: `create()` now catches that specific `IntegrityError` and raises a new `AssetAlreadyExistsError("Asset <id> already exists in the catalog.")`. Any other constraint violation (`CHECK`, `NOT NULL`, etc.) still propagates unchanged — only the duplicate-id case is translated. `AssetNotFoundError` added on the same principle, used by `transition_status()` and `add_tags()` when the target id doesn't exist. Read methods (`get()`, `get_tags()`) stay lenient — return `None`/`[]` rather than raising, matching how they already behaved.
- This is directly in service of the project's own "duplicate-safe" principle (see README) — a repository that silently crashes on a duplicate isn't duplicate-safe, it's duplicate-fatal.

**First real end-to-end round trip, proven twice:**

- First run: created a real `Asset`, persisted it, retrieved it, confirmed the round trip matched.
- Second run: `AssetAlreadyExistsError` caught cleanly, printed a message, no crash — proof the catalog is genuinely persistent across runs (unlike a `:memory:` test database) and that the error handling works, not just that it compiles.

**Proactive complexity review:**

- After the migration reversal, the author asked whether anything else in the Phase 1B code was similarly ahead of its actual need. Reviewed `connection.py`, `schema.sql`, `asset_repository.py`, and the `Asset` model with that lens.
- One candidate found: `PRAGMA journal_mode=WAL` in `connection.py`, justified by "Gradio callbacks run on multiple threads" — a Phase 4 concern, not a Phase 1B one. Discussed openly, including that WAL is what triggered a `disk I/O error` in Claude's own sandbox testing today (environment-specific, not proof of a real problem, but a data point). Decision: keep it — unlike the migration runner, it's a single PRAGMA line, changing it later costs one PRAGMA line, no data risk either direction. Explicitly a different judgment call from the migration one, not a reflexive "keep everything."
- Everything else (schema fields, `Asset` model fields, the two new exception classes) mapped to something that already happened today, not something anticipated for later — no further cuts made.

**Phase 1B closed out:**

- `docs/roadmap.md` — all six Phase 1B items now checked: schema, indexes, repository layer, database creation, persist, retrieve.

---

# Environment Note (Claude's side, not a project issue)

Claude's sandbox has an intermittent read-lag on this mounted repo: files edited via the file-editing tool sometimes read back stale (or truncated) content through the sandbox's shell for a period afterward, and `git status`/`git log` briefly reported the branch as "broken" in that same sandbox view. Verified this doesn't reflect the actual files (`Read`-tool content, and isolated `/tmp` copies, were consistently correct and passed real execution tests). Treated as a Claude-environment artifact throughout the session, not a project bug — worth remembering if a future session hits confusing sandbox output that doesn't match what's actually in the repo.

---

# Lessons Learned

- The migration-runner detour and the earlier transaction/rollback over-engineering (same week) are the same root mistake: designing for the phase after the one you're actually in. Worth an explicit check going forward — "does this solve a problem that exists right now, or one that will exist later" — rather than relying on getting caught each time.
- When something breaks, fix the actual failure mode, not just the trigger. Generating a random id would have stopped the crash without making `create()` handle duplicates correctly — the author caught this distinction immediately.
- Proportion matters, not just direction: WAL and the migration runner are the same *category* of "solving a future phase's problem early," but very different in cost to keep or reverse. Not everything in that category is worth cutting — worth weighing case by case instead of applying the lesson mechanically.

---

# Next Session (Day 05 / Phase 2 — Ingestion)

Phase 1B is functionally complete. Next is where real files enter the picture for the first time — everything so far has used one dummy test asset.

1. Discovery: scan a real local folder for real files.
2. SHA256 hashing of real files.
3. Dedup check using `get_by_sha256_verified()` — first real exercise of the method just built.
4. Metadata extraction (EXIF, etc.).
5. Upload pipeline to HF Buckets.
6. Verification step, transitioning assets through the real lifecycle (`transition_status()` gets used for real instead of in a test).

Before starting: `git status`/`git log` looked inconsistent in Claude's sandbox today (see Environment Note) — worth checking directly on the author's machine before committing today's work, rather than trusting the sandbox's read of it.
