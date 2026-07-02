# SecondBrain ChatGPT Bootstrap Context

## Project

SecondBrain

Repository:

hf-personal-digital-vault

---

## Current Day

Day 02

---

## Current Phase

Phase 1B — SQLite Catalog Design

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

Phase 1B:

- design SQLite schema
- design indexes
- design repository layer
- create first SQLite database
- persist first Asset object