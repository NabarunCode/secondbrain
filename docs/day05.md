# Day 05 — Phase 2 Kickoff: Ingestion / Discovery Design

Date: 2026-07-05

(Note: this session initially misdated itself as still "Day 04" / 2026-07-03 — caught via `date` in Claude's sandbox partway through. See `decisions.md` correction.)

---

# Today's Goal

Start Phase 2 (Ingestion), paced like Phase 1B: architecture review first, one sub-step at a time, author writes the code with Claude scaffolding — not Claude implementing directly, which is how Day 04 actually went.

---

# Completed

**Working mode reaffirmed:**

- Day 04's code (schema.py, asset_repository.py, etc.) was written directly by Claude, a drift from the Day 02 scaffold-and-teach agreement. Explicitly reaffirmed for Phase 2 onward: Claude scaffolds (signatures, docstrings, TODOs) and shows syntax before requiring it; the author writes the logic. Logged in `decisions.md`.
- New Hard Rule added: chat responses should be spaced out and easy to read (short chunks, light emoji use) rather than dense paragraphs — applies to chat only, not files written to the repo. Logged in `decisions.md` and surfaced in `session_context.md`.

**Phase 2 Discovery — design:**

- `docs/phase2_ingestion_architecture.md` written, scoped to Discovery only (the first of Phase 2's six items). Key decisions:
  - Traversal via `pathlib.Path.rglob("*")`.
  - `AssetType` classification by file extension lookup table (photo/document/audio/video/other); `note` is never produced by Discovery — reserved for something typed directly into the app later (Phase 4), not a discovered file.
  - `mime_type` via stdlib `mimetypes.guess_type()`.
  - Re-scan duplicate prevention: Discovery checks `get_by_local_path()` before `create()`, skipping files already tracked in a non-`FAILED` status. Enforced at the DB layer via a new partial unique index, mirroring the existing `idx_assets_sha256_verified` pattern.
  - Errors (unreadable/in-use files): skip-and-report, not fail-fast.
- All decisions also logged in `decisions.md`.

**Implementation, in progress (author writing, Claude scaffolding/reviewing):**

- `idx_assets_local_path_active` — **DONE and verified.** Added to `schema.sql` by the author (one typo round-tripped and fixed: a stray `''` before an unquoted `failed`, and an index name that didn't match the docs — both caught and corrected). Verified in Claude's sandbox: blocks a second active row for the same `local_path`, allows a fresh row once the earlier one is marked `failed` (real retry scenario, not just "does it parse").
- `AssetRepository.get_by_local_path()` — **DONE, verified.** Signature: `local_path: Path` (matching the `Asset` model and what Discovery will hand in from `rglob()`; required adding `from pathlib import Path` to `asset_repository.py`, which didn't previously import it). Body: `SELECT * FROM assets WHERE local_path = ? AND storage_status != 'failed'`, `.fetchone()`, `None` if empty, else `self._asset_from_row(row)` — same shape as `get_by_sha256_verified()`.
  - Two rounds of real bugs caught and fixed along the way: (1) `local_path = str(Path)` written literally into the SQL string instead of a `?` placeholder; (2) a mis-indented `return`; (3) `str(local_path,)` instead of `(str(local_path),)` — comma inside `str()`'s parens vs. outside it, the difference between a plain string and an actual one-item tuple.
  - Verified with a real 3-case test: active row found, unrelated path returns `None`, and a row marked `failed` correctly returns `None` too (enabling a retry). Not just "does it parse."
  - Along the way: Claude had initially pointed at existing code (`get_by_sha256_verified()`) as if that counted as "already demonstrated" syntax, without the author having written it themselves — a real Hard Rule violation, caught by the author. Corrected by actually teaching the `?`/tuple-parameter mechanism and `.fetchone()` with live, run examples (parameter binding, cursor-vs-fetched-row, `(x,)` vs `(x)`) before asking for another attempt.

**Not yet started:** `secondbrain/ingest/discovery.py` itself. `pathlib.rglob()` and `mimetypes.guess_type()` haven't been taught yet (new syntax, per Hard Rule, needs its own dedicated moment). One small cleanup remains: a leftover `#raise NotImplementedError` comment in `get_by_local_path()` should be deleted (harmless, dead code).

---

# Lessons Learned

- Caught a real date-tracking bug in the docs system itself: this session ran two calendar days after "Day 04" (07-03 → 07-05) but kept treating itself as still Day 04 until `date` was actually run in the sandbox. The lesson from Day 04 ("verify tool/CLI behavior before asserting it") applies just as much to *dates* as to command output — don't trust an assumed/carried-over date, check it.
- Splitting review into small increments continues to work: the index typo (quote mismatch, name mismatch) and the `get_by_local_path()` bugs were each caught individually rather than compounding into a bigger tangle.
- "Look at the existing method above it" is not the same as "syntax has been demonstrated to the author" — that existing method (`get_by_sha256_verified()`) was written by Claude during the Day 04 drift, not by the author, so pointing at it wasn't actually teaching. The Hard Rule requires the syntax be shown and worked through with the specific author in this project, not just be present somewhere in the file. Fixed by teaching `?`/tuple parameter binding and `.fetchone()` with live, run examples instead of a reference pointer.

---

# Next Session

`get_by_local_path()` is done and verified. Remaining for Discovery:

1. Delete the leftover `#raise NotImplementedError` line in `get_by_local_path()` (dead code, harmless, just cleanup).
2. Teach `pathlib.rglob()` and `mimetypes.guess_type()` (new syntax, not yet shown) before scaffolding `secondbrain/ingest/discovery.py`.
3. Scaffold `discovery.py` itself with TODOs.
4. `experiments/test_discovery.py` — prove Discovery against a real folder, run twice, confirm the second run skips everything already tracked.

Reminder: commit convention is one combined commit per session (`git add . && git commit -m "..." && git push`). Nothing from today's session has been committed yet as of this writing.
