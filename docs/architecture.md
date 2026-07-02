# SecondBrain Architecture

# Core Principle

```text
SQLite
    =
Source of Truth

HF Buckets
    =
Blob Storage Backend
```

The system is designed to work offline-first.

SQLite owns:

- asset metadata
- upload state
- deduplication
- provenance
- workflow tracking

HF Buckets own:

- binary blobs
- thumbnails
- future derived artifacts

---

# High Level Architecture

```text
                Personal Assets

        Photos
        Notes
        Documents
        Audio
        Video
               |
               v

          Discovery Layer
               |
               v

        Ingestion Pipeline
               |
               + SHA256
               + Metadata extraction
               + Thumbnail generation
               + Embeddings (future)
               |
               v

            SQLite
      (Source of Truth)
               |
               v

          HF Buckets
         (Blob Store)
               |
               v

            Gradio
              UI
```

---

# Asset Lifecycle v1

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

# Duplicate Strategy

A file is considered a duplicate only if:

1. SHA256 matches
2. Existing asset status == VERIFIED

Reason:

Prevent data loss when previous uploads failed.

---

# Duplicate Handling

Decision:

Store duplicate asset records,
but do not upload duplicate blobs.

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