# Phase 2 — Ingestion Architecture (Part 1: Discovery)

Scope: **Discovery only** — the first of Phase 2's six roadmap items (Discovery, SHA256, Dedup check, Metadata extraction, Upload pipeline, Verification). Paced the same way Phase 1B was: one design doc per sub-step, not all of Phase 2 at once. Hashing, dedup-by-content, metadata extraction, upload, and verification are separate design passes, later.

---

## 1. What Discovery Does

Given a folder path, find every real file under it and register each one in the catalog as an `Asset` at `storage_status = DISCOVERED`. Nothing about hashing, dedup, or upload happens here — those are later pipeline steps, working off what Discovery hands them.

---

## 2. Decisions

| # | Decision | Chosen | Reason |
|---|---|---|---|
| 1 | Filesystem traversal | `pathlib.Path.rglob("*")` | Recursive, stdlib only, no manual recursion — matches "avoid unnecessary frameworks." |
| 2 | File → `AssetType` classification | Extension lookup table (§3) | Simple, matches the extension-based approach already used for `mime_type`. |
| 3 | `mime_type` | Python stdlib `mimetypes.guess_type()` | No new dependency; good enough for v1 — extension-based, not file-magic inspection. |
| 4 | `note` classification | Not produced by Discovery | No file extension naturally means "note" — reserved for something typed directly into the app later (Phase 4 UI), not a discovered file. |
| 5 | Re-scan duplicate prevention | Check `local_path` before `create()`; skip if already tracked in a non-`FAILED` status | README already commits to "Resumable: nothing has to restart from zero after a crash." A Discovery that creates a fresh duplicate row every time it's re-run on the same folder contradicts that. |
| 6 | Enforcement of #5 | Partial unique index, not just application-level check | Mirrors the existing `idx_assets_sha256_verified` pattern exactly — a business rule enforced at the DB layer, not trusted to application code alone. |
| 7 | Error handling | Skip-and-report | A personal-archive tool scanning real, messy folders will hit unreadable/in-use files. Failing the whole scan over one bad file is worse than skipping it and reporting at the end. |

---

## 3. Extension → AssetType Table

```text
photo:    .jpg .jpeg .jfif .png .heic .gif .bmp .tif .tiff .webp
document: .pdf .doc .docx .txt
audio:    .mp3 .wav .m4a .flac .aac .ogg
video:    .mp4 .mov .avi .mkv .webm
other:    anything unmatched
```

`.md`/`.rtf`/`.odt` intentionally left out of `document` for now — add if real files in your archive need them; easy, low-risk addition later (extension table, not schema).

---

## 4. Schema Change

One new index, added to `secondbrain/catalog/schema.sql` (still `CREATE ... IF NOT EXISTS`, still no migration needed — this is exactly the kind of additive change the Day 04 `schema.sql` correction was designed for):

```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_assets_local_path_active
    ON assets(local_path)
    WHERE storage_status != 'failed';
```

Same shape as the existing dedup index:

```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_assets_sha256_verified
    ON assets(sha256)
    WHERE storage_status = 'verified';
```

`sha256` dedup asks "does this *content* already exist, successfully uploaded?" `local_path` dedup asks "have I already started tracking *this exact file*, and not given up on it?" `!= 'failed'` (not `= 'discovered'`) so a file re-discovered while it's anywhere mid-pipeline (`HASHING`, `UPLOADING`, etc.) is still caught — only a previously `FAILED` attempt at that path allows a fresh row (a deliberate retry).

---

## 5. Repository Addition

One new method on `AssetRepository`, same shape as `get_by_sha256_verified()`:

```python
def get_by_local_path(self, local_path: str) -> Asset | None:
    """Read-only lookup; Discovery uses this to skip files already tracked."""
```

`SELECT * FROM assets WHERE local_path = ? AND storage_status != 'failed'`, reusing `_asset_from_row()`. Read-only, so — consistent with `get()`/`get_tags()` — returns `None` rather than raising when nothing matches.

---

## 6. Discovery Flow

```text
for each path in rglob(folder):
    stat the file                          -- skip-and-report on error
    classify AssetType from extension       -- §3 table
    guess mime_type                         -- mimetypes.guess_type()
    if get_by_local_path(path) is not None:
        skip (already tracked)
    else:
        build Asset(storage_status=DISCOVERED, ...)
        repo.create(asset)

report: N discovered, M skipped (already tracked), K errors (unreadable)
```

---

## 7. Implementation Plan

1. Add the index from §4 to `schema.sql`.
2. Add `get_by_local_path()` to `asset_repository.py`.
3. Scaffold `secondbrain/ingest/discovery.py` (author writes the logic; `pathlib.rglob()` and `mimetypes.guess_type()` syntax shown first, per the Hard Rule).
4. `experiments/test_discovery.py` — prove it against a real folder: run twice, confirm the second run skips everything the first run already found.
