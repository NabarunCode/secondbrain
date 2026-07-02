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

## chatgpt_context.md

The primary bootstrap file.

Contains:

- current project status
- current phase
- completed work
- next steps
- important architectural decisions

Every new chat should begin by reading this file.

---

## project_context.md

High-level project information:

- project goals
- target audience
- personal background
- blog positioning
- technology choices

---

## architecture.md

Contains:

- system architecture
- data flow
- component design
- storage design

---

## decisions.md

Architectural Decision Record (ADR).

Records:

- what decisions were made
- why they were made
- alternatives considered

---

## roadmap.md

Contains:

- phases
- milestones
- current progress
- future work

---

## dayXX.md

Engineering journal.

Each day contains:

- work completed
- lessons learned
- problems encountered
- next actions

Examples:

- day01.md
- day02.md
- day03.md

---

# Session Workflow

## Beginning of a new session

Read:

- chatgpt_context.md
- project_context.md
- architecture.md
- decisions.md
- latest dayXX.md

Then continue the project.

---

## End of a session

Update:

- chatgpt_context.md
- decisions.md
- current dayXX.md

---

## Commit documentation

```bash
git add docs
git commit -m "docs: update project memory"
```

---

## Commit code separately

```bash
git add .
git commit -m "<feature description>"
```

---

# Guiding Principle

Chat history is ephemeral.

Project documentation is persistent.

When there is a conflict, trust the documentation.