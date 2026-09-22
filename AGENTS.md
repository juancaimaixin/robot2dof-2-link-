# Project Operating Rules

## Context Recovery

- At the start of a conversation, read only `PROGRESS.md`, `git status --short`, relevant sections of `PLAN.md`, and source files relevant to the current task.
- Do not traverse the entire repository at startup.
- Do not read all of `PROGRESS_HISTORY.md`; use `rg` to locate keywords only when the current summary is insufficient.
- Do not read `.git`, caches, `__pycache__`, or generated images unless the task needs them.
- Consult relevant `PLAN.md` sections when changing stages or clarifying rules.

## Collaboration

- The user writes source code; the assistant explains, reviews, and verifies it unless the user explicitly authorizes implementation.
- Advance one small concept or complete functional block at a time.
- After a meaningful milestone, update `PROGRESS.md` and append a brief entry to `PROGRESS_HISTORY.md`.

## Validation

- Project Python on the original workstation: `D:\miniconda\envs\robot2dof\python.exe`.
- Run pytest and Ruff together at meaningful checkpoints, not after every line.
