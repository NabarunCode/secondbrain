```text
   _____                           ______             _     
  / ___/___  _________  ____  ____/ / __ )_________ _(_)___ 
  \__ \/ _ \/ ___/ __ \/ __ \/ __  / __  / ___/ __ `/ / __ \
 ___/ /  __/ /__/ /_/ / / / / /_/ / /_/ / /  / /_/ / / / / /
/____/\___/\___/\____/_/ /_/\__,_/_____/_/   \__,_/_/_/ /_/ 
```

<div align="center">

**Can Hugging Face Buckets become my personal digital memory?**

![Python](https://img.shields.io/badge/python-3.14-3776AB?logo=python&logoColor=white)
![Package Manager](https://img.shields.io/badge/package_manager-uv-DE5FE9)
![Database](https://img.shields.io/badge/database-SQLite-003B57?logo=sqlite&logoColor=white)
![Validation](https://img.shields.io/badge/validation-Pydantic-E92063?logo=pydantic&logoColor=white)
![Status](https://img.shields.io/badge/status-work--in--progress-yellow)
![License](https://img.shields.io/badge/license-TBD-lightgrey)

</div>

---

SecondBrain is a personal digital memory system — photos, notes, documents, audio, video — built to test whether **Hugging Face Buckets** can work as a general-purpose personal storage backend, not just an AI/ML artifact store. **SQLite** is the source of truth for everything: metadata, state, dedup, provenance. Buckets just hold the bytes.

This is a working build log, not a finished product. It's being built in public, one day at a time, by someone new to Python, SQL, and API-driven platforms — the code *and* the docs in this repo are both part of the story.

## Table of Contents

- [Status](#-status)
- [Why This Project Exists](#-why-this-project-exists)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Layout](#-project-layout)
- [The `docs/` Folder Is Part of the Project](#-the-docs-folder-is-part-of-the-project)
- [Roadmap](#-roadmap)
- [Running What Exists So Far](#-running-what-exists-so-far)
- [License](#-license)

---

## 📍 Status

**Day 04 · Phase 1B — SQLite Catalog — complete.**

The domain model, asset lifecycle, SQLite schema, and full repository layer (`create`, `get`, `transition_status`, `add_tags`/`get_tags`, `get_by_sha256_verified`) are designed, implemented, and verified end-to-end against a real database file. There is **no ingestion pipeline and no UI yet** — nothing uploads to a bucket automatically, and everything persisted so far is one dummy test asset, not real files. Full phase-by-phase progress lives in [`docs/roadmap.md`](docs/roadmap.md).

## 🤔 Why This Project Exists

20+ years in enterprise infrastructure, cloud, and virtualization — currently on a career break learning AI/ML and software engineering from first principles. Rather than a tutorial-follow-along project, this is a real system, built slowly and deliberately, with the reasoning behind every decision written down as it happens. If it also turns into a genuinely useful personal archive along the way, even better.

## 🏗️ Architecture

```text
┌──────────────┐               ┌────────────────────┐
│    SQLite    │               │     HF Buckets     │
│ source of    │               │  blob storage      │
│    truth     │               │  (photos, docs...) │
└──────────────┘               └────────────────────┘

  Local File
      │
      ▼
  DISCOVERED → HASHING → DEDUP_CHECK → PROCESSING → UPLOADING → VERIFYING → VERIFIED
      │                                                                        
      └──────────────────────── any state ───────────────────────▶ FAILED
```

| Principle | What it means here |
|---|---|
| **Offline-first** | Works without a network connection until upload time |
| **Duplicate-safe** | A file only counts as a duplicate if its hash matches an asset that's already `VERIFIED` — not just any hash match — so a failed upload can always be retried |
| **Resumable** | Every asset's exact state is tracked; nothing has to restart from zero after a crash |
| **Provenance-aware** | Every state change is logged, not just the current state |

Full design detail: [`docs/architecture.md`](docs/architecture.md) (system-wide) and [`docs/phase1b_catalog_architecture.md`](docs/phase1b_catalog_architecture.md) (current phase — schema, indexes, trade-offs, in depth).

## 🧰 Tech Stack

| Tool | Role |
|---|---|
| [Python 3.14](https://www.python.org/) | Language |
| [uv](https://docs.astral.sh/uv/) | Package/project manager |
| SQLite | Catalog — source of truth |
| [Pydantic](https://docs.pydantic.dev/) | Domain models, validation |
| [Gradio](https://www.gradio.app/) | UI (Phase 4, not started) |
| [Hugging Face Buckets](https://huggingface.co/docs) | Blob storage backend |

## 📁 Project Layout

```text
secondbrain/
├── models/     Pydantic domain models (Asset, AssetType, StorageStatus)
├── catalog/    SQLite schema, connection handling, repository layer
├── ingest/     discovery → hash → dedup → upload pipeline   (not started)
├── storage/    HF Bucket blob wrapper                        (not started)
└── cli/        command-line entrypoint                       (not started)

experiments/    throwaway scripts, kept separate from production code
docs/           project memory system — see below
```

## 🧠 The `docs/` Folder Is Part of the Project

This project treats chat history as ephemeral and documentation as the only thing that persists across sessions, tools, and AI assistants. Every architectural decision, every trade-off, every mistake and correction gets written down as it happens — not cleaned up after the fact.

Worth reading if you want the real story, not just the code:

- [`docs/readme.md`](docs/readme.md) — how the memory system itself works
- [`docs/decisions.md`](docs/decisions.md) — every architectural decision, with reasoning (including the ones that turned out wrong and got corrected)
- [`docs/roadmap.md`](docs/roadmap.md) — phase-by-phase progress

<details>
<summary>Daily build log</summary>

- [`docs/day01.md`](docs/day01.md) — first HF Bucket upload
- [`docs/day02.md`](docs/day02.md) — asset lifecycle, dedup strategy, Pydantic models
- [`docs/day03.md`](docs/day03.md) — SQLite catalog schema and connection layer
- [`docs/day04.md`](docs/day04.md) — repository layer, migration-runner reversal, Phase 1B closeout

</details>

## 🗺️ Roadmap

| Phase | Focus | Status |
|---|---|---|
| 0 | Project setup | ✅ Done |
| 1A | Domain model | ✅ Done |
| 1B | SQLite catalog | ✅ Done |
| 2 | Ingestion pipeline | ⬜ Not started |
| 3 | Search | ⬜ Not started |
| 4 | Gradio UI | ⬜ Not started |
| 5 | Semantic search / embeddings | ⬜ Not started |
| 6 | Blog series and writeup | ⬜ Not started |

## ▶️ Running What Exists So Far

```bash
uv sync
uv run python experiments/test_asset.py       # exercises the Asset model
uv run python experiments/test_repository.py  # persists + retrieves a real Asset via SQLite
```

There's no end-to-end pipeline yet — that's Phase 2.

## 📄 License

Not yet decided.
