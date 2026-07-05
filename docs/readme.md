# SecondBrain Project Memory

This directory acts as the persistent memory system for the SecondBrain project.

The purpose of this folder is to ensure that project knowledge survives:

- chat context limits
- multiple ChatGPT sessions
- multiple AI assistants
- long project timelines

The documentation in this folder is considered the authoritative source of truth.

---

# Files

| File | Purpose | Updated when | Updated by |
|---|---|---|---|
| `session_context.md` | Fast bootstrap summary — current day, current phase, completed work, next steps, headline decisions. Read first in any new session. | `#EOD` only (kept accurate for the *next* `#SOD`, not touched mid-day) | Assistant |
| `project_context.md` | Static high-level info — goals, audience, author background, blog angle. Rarely changes. | Only when the project's purpose/audience/positioning itself changes | Author or assistant, on explicit request |
| `architecture.md` | Cross-cutting, current-state system architecture — lifecycle, high-level data flow, component design. Stays scannable; does not carry phase-level implementation detail. | When a cross-cutting architectural decision changes the overall picture | Assistant, during the session it happens |
| `phaseN_<topic>.md` (e.g. `phase1b_catalog_architecture.md`) | Deep-dive design doc for a single roadmap phase — full schema, trade-off tables, implementation plan. Created when a phase's detail would otherwise bloat `architecture.md`. `decisions.md` links to these rather than repeating them. | Once per phase, when that phase's architecture review happens; amended if the design changes before the phase closes | Assistant |
| `decisions.md` | Append-only ADR log — what was decided, why, alternatives considered. Never rewritten, only appended, dated. | As soon as a decision is made — not deferred to `#EOD` | Assistant, live during the session |
| `roadmap.md` | Phase checklist — `[ ]` / `[x]` per item. | `#EOD`, once a deliverable is actually done (not when merely planned) | Assistant |
| `dayXX.md` | Daily engineering journal. Goal/plan section written at `#SOD` (or whenever the day's work starts); Completed / Lessons Learned / Next Session sections filled at `#EOD`. One file per day, e.g. `day01.md`, `day02.md`, `day03.md`. | Goal at start of day, rest at `#EOD` | Assistant |
| `readme.md` (this file) | Meta-doc — describes the docs system itself and the `#SOD`/`#EOD` workflow. | When the workflow itself changes | Assistant, on explicit request |

---

# Session Workflow

## Shorthand

`#SOD` (Start of Day) — begin or resume a session, in a **new chat**, with **no memory of prior sessions**. Assumes only file access, not chat history.

`#EOD` (End of Day) — signals the author is done for the day. Not a summary request: it means write everything from this session into the correct files, right now, before the session ends. See "Guiding Principle" below — if it isn't in a file, it didn't happen for the next session's purposes.

Applies to any assistant working on this project, not just ChatGPT. Requires read/write access to this repo (e.g. a Cowork session with the folder connected) to actually execute the file writes described below — an assistant without file-write access can only produce text for the author to paste in manually.

## `#SOD` — Beginning of a new session

0. **First, immediately call `mcp__cowork__request_cowork_directory` with path `C:\projects\hf-personal-digital-vault`** if this chat doesn't already have it — don't wait to be asked. Folder access is granted per chat, not automatically inherited across new chats in the same Project. If access fails or is denied, say so explicitly and stop — do **not** fall back to any pre-loaded/uploaded Project knowledge snapshot as a substitute, since that can be stale (see `decisions.md`, "Hard Rule: confirm live folder access before `#SOD`").
1. Read, in order: `session_context.md`, `project_context.md`, `architecture.md`, `decisions.md`, the highest-numbered `dayXX.md`, `roadmap.md` — from the live folder just confirmed in step 0, not from memory or an uploaded snapshot.
2. Read any `phaseN_<topic>.md` referenced by the current phase in `decisions.md` or `roadmap.md`.
3. State back a short recap of where the project stands (current day, current phase, what's done, what's next) before doing anything else, so the author can correct anything stale.
4. Continue the project from there — do not rely on chat history from a different session even if it happens to be visible.

## `#EOD` — End of a session

1. Fill in today's `dayXX.md`: Completed, Lessons Learned, Next Session (replace any `(fill in at EOD)` placeholders with what actually happened).
2. Confirm every decision made this session is already in `decisions.md` (it should be — decisions get logged live, not batched).
3. Update `session_context.md`: bump Current Day / Current Phase, refresh Completed and Next Session sections.
4. Check off any `roadmap.md` items that were actually finished (not just attempted).
5. Remind the author of the commit commands below — do not commit automatically without being asked.

---

## Commit

One commit per session, docs and code together — they're explaining each
other, not two separate changes. Split them only if a session produces two
genuinely unrelated pieces of work, or docs are ready but code isn't.

```bash
git add .
git commit -m "<what this session actually did>"
git push
```

(Superseded 2026-07-03: this used to be two separate steps, docs then code.
No CI or changelog tooling depends on that split, and it fought the
project's own "code and docs are both part of the story" framing more than
it helped. See `decisions.md`.)

---

# Guiding Principle

Chat history is ephemeral.

Project documentation is persistent.

When there is a conflict, trust the documentation.

---

## Why sessions are short on purpose

Chat context windows are finite (~200K tokens as of mid-2026). Long sessions eventually auto-compact — the assistant summarizes and discards older turns to keep going, which is lossy by design. Don't rely on it as memory.

Expect to start a new chat roughly once per `#SOD`/`#EOD` cycle (sometimes more within a long day), especially given this project favors deep-dive explanations over terse answers. This isn't a workaround — it's the intended use of this docs system: a brand-new session with zero chat history should be able to fully reconstruct context from files alone in one `#SOD` pass. If it can't, the docs are missing something, not the chat.