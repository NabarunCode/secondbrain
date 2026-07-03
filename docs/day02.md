# Day 02 — Asset Model and Lifecycle Design

Date: 2026-07-01

---

# Goal

Design the foundational domain model for SecondBrain before implementing storage and ingestion.

The objective was to avoid premature coding and instead establish:

- asset lifecycle
- deduplication strategy
- upload guarantees
- storage ownership
- asset schema

---

# Major Architectural Decision

The most important decision made today:

```text
SQLite
    =
Source of Truth

HF Buckets
    =
Blob Storage Backend
```

Consequences:

- offline operation possible
- resumable uploads
- provenance tracking
- duplicate-safe uploads
- upload verification
- recovery after failures

---

# Asset Lifecycle v1

Final lifecycle:

```text
                     Local File
                          |
                          v

                     DISCOVERED
                          |
                          v

                       HASHING
                          |
                          v

                     DEDUP_CHECK
                       /      \
                      /        \
                     /          \
              DUPLICATE      PROCESSING
                                  |
                                  v

                              UPLOADING
                                  |
                                  v

                              VERIFYING
                                  |
                                  v

                              VERIFIED


Any state
    |
    v

FAILED
```

---

# Duplicate Detection Strategy

Decision:

A file is considered a duplicate only if:

1. SHA256 matches
2. Existing asset status == VERIFIED

Reason:

Prevent accidental data loss when previous uploads failed.

---

# Duplicate Handling Strategy

Decision:

Store duplicate asset records but do not upload duplicate blobs.

Example:

```text
IMG001.JPG
       ↑
IMG001_copy.JPG
       ↑
IMG001_backup.JPG
```

Implementation:

```python
duplicate_of: AssetId | None
```

---

# Asset Status Enum

```python
class StorageStatus(str, Enum):

    DISCOVERED = "discovered"

    HASHING = "hashing"

    DEDUP_CHECK = "dedup_check"

    PROCESSING = "processing"

    UPLOADING = "uploading"

    VERIFYING = "verifying"

    VERIFIED = "verified"

    DUPLICATE = "duplicate"

    FAILED = "failed"
```

---

# Asset Schema v1

```text
Asset
├── id
├── asset_type
├── storage_status
├── failure_stage
├── duplicate_of
│
├── filename
├── local_path
│
├── title
├── description
├── tags
│
├── bucket_name
├── object_key
│
├── mime_type
├── size_bytes
├── sha256
│
├── file_modified_at
├── original_date
│
├── metadata
│
├── thumbnail_path
├── embedding_id
```

---

# Important Design Decisions

## ULID

Decision:

```python
AssetId = str
```

Reason:

- sortable
- globally unique
- future distributed systems support

---

## local_path retained

Reason:

- provenance
- migration
- re-import
- debugging

---

## bucket_name/object_key nullable

Reason:

Assets may exist locally before upload.

---

## failure_reason postponed

Decision:

Track only:

```python
failure_stage
```

Reason:

Logging subsystem will be designed later.

---

# Python / Pydantic Learning

Learned:

- classes
- objects
- inheritance
- BaseModel
- Enums
- Optional fields
- Field(default_factory)
- model_dump()
- model_dump_json()

Mental model:

```text
class
    =
    blueprint

object
    =
    instance

attribute
    =
    database column

Pydantic model
    =
    validated database row
```

---

# Implemented Files

```text
secondbrain/

└── models/
    ├── __init__.py
    ├── asset.py
    ├── asset_type.py
    └── storage_status.py
```

---

# Validation

Successfully created and instantiated the first Asset object:

```bash
uv run python experiments/test_asset.py
```

Successfully verified:

- Asset object creation
- model_dump()
- model_dump_json()

---

# Next Session

Phase 1B:

- design SQLite schema
- design indexes
- design catalog layer
- create first SQLite database
- persist first Asset object