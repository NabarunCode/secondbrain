# Architectural Decisions

## 2026-07-01

### Project Name

Decision:
SecondBrain

Reason:
Memorable and aligned with project goals.

---

### Package Manager

Decision:
uv

Reason:
Modern, fast, becoming industry standard.

---

### Storage

Decision:
Hugging Face Buckets

Reason:
Primary technology being evaluated.

---

### Metadata Store

Decision:
SQLite

Reason:
HF Buckets are object storage, not databases.

---

### UI

Decision:
Gradio

Reason:
Provides a path toward AI interactions.

---

### Repository Structure

Decision:

secondbrain/
    reusable application code

experiments/
    temporary experiments and testing

Reason:
Keep production code separate from experiments.

---

Decision:
SQLite shall be the authoritative catalog.

Rationale:
- supports offline operation
- supports resumability
- supports dedup-safe uploads
- supports provenance
- supports upload verification

---

Decision:
Duplicate files shall be stored as asset records but shall not upload duplicate blobs.

Implementation:
duplicate_of: AssetId | None



---

### Asset Identity

Decision:

Use ULID identifiers.

Implementation:

```python
AssetId = str
```

Reason:

- sortable
- globally unique
- future distributed support
- URL safe

---

### Asset Lifecycle

Decision:

Adopt the following asset lifecycle:

```text
DISCOVERED
    ↓
HASHING
    ↓
DEDUP_CHECK
    ↓
PROCESSING
    ↓
UPLOADING
    ↓
VERIFYING
    ↓
VERIFIED
```

Additional terminal states:

```text
DUPLICATE
FAILED
```

Reason:

Supports:

- resumability
- provenance
- duplicate-safe uploads
- upload verification

---

### Duplicate Detection

Decision:

A duplicate is valid only when:

- SHA256 matches
- referenced asset status == VERIFIED

Reason:

Prevents data loss from failed uploads.

---

### Duplicate Handling

Decision:

Store duplicate asset records,
but do not upload duplicate blobs.

Implementation:

```python
duplicate_of: AssetId | None
```

Reason:

Preserves provenance while avoiding duplicate storage.

---

### Asset Path Retention

Decision:

Retain original local filesystem path.

Implementation:

```python
local_path: Path | None
```

Reason:

- provenance
- migration
- debugging
- re-import

---

### Failure Tracking

Decision:

Track only:

```python
failure_stage
```

Postpone:

```python
failure_reason
```

Reason:

Logging subsystem will be designed later.