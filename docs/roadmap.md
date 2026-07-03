# Roadmap

## Phase 0 — Project Setup

[x] Install uv
[x] Initialize project
[x] Initialize git
[x] Authenticate HF
[x] Create bucket
[x] Upload first object

---

## Phase 1A — Domain Model

[x] Design asset lifecycle
[x] Design dedup strategy
[x] Design asset schema
[x] Design metadata strategy
[x] Create Pydantic models
[x] Create Asset model
[x] Create AssetType enum
[x] Create StorageStatus enum

---

## Phase 1B — Catalog

[x] Design SQLite schema
[x] Design indexes
[x] Build repository layer
[x] Create SQLite database
[x] Persist first asset
[x] Retrieve first asset

---

## Phase 2 — Ingestion

[ ] Discovery
[ ] SHA256
[ ] Dedup check
[ ] Metadata extraction
[ ] Upload pipeline
[ ] Verification

---

## Phase 3 — Search

[ ] Metadata search
[ ] Tag search
[ ] Filter search

---

## Phase 4 — UI

[ ] Gradio UI
[ ] Asset browser
[ ] Search interface

---

## Phase 5 — Semantic Search

[ ] Embeddings
[ ] Vector storage
[ ] Semantic retrieval

---

## Phase 6 — Publishing

[ ] Blog series
[ ] Architecture writeup
[ ] Tutorial series

---

## Future Ideas (unscheduled, not yet a phase)

[ ] Encrypt the SQLite catalog file at rest (e.g. SQLCipher), keyed to the user account/ULID — protects confidentiality (file theft/leak), complementary to CHECK constraints (which protect integrity, not secrecy). Raised 2026-07-02.
[ ] Design a real "delete an asset" feature — likely soft-delete (status flag), not a hard SQL DELETE, consistent with this system never destroying data elsewhere (duplicates, failed-upload retries). Not designed yet; asset_events' RESTRICT-by-default FK currently just blocks hard deletes outright. Raised 2026-07-02.