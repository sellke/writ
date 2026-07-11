---
category: lessons
tags: [implement-phase, git-worktrees, phase-orchestration]
created: 2026-07-11
related_artifacts:
  - .gitignore
  - scripts/phase-state.py
  - .writ/docs/phase-execution-state-format.md
---

# Lane worktree dirs must be gitignored for /implement-phase merges

## TL;DR

Gitignore the ephemeral `.writ-lanes-{phase}/` worktrees that `/implement-phase` creates, or the untracked directory dirties the phase branch and blocks the verified merge.

## Context

Recorded at phase close from evidence-bound knowledge writeback (Phase 7 — the first genuine multi-spec `/implement-phase` run; Phase 6 only proved the mechanics in a disposable sandbox).

**Cited evidence:**

- `.gitignore` phase-branch commit `f06f405` ("gitignore ephemeral .writ-lanes-* worktree dirs")
- `scripts/phase-state.py` `integrate` returned `dirty_base` during the `2026-07-10-skill-lifecycle` integration until the ignore rule was added
- Surfaced on the first real multi-spec run, before any lane could merge

## Detail

`phase-state.py create-lane` builds each per-spec lane as a git worktree under `.writ-lanes-{phase}/`. The *intended* location is a repo sibling (`repo.parent/.writ-lanes-{phase}`), outside the checkout — but a relative `--repo .` collapses `repo.parent` back to the repo itself, so lanes can land *inside* it (tracked separately in `.writ/issues/bugs/2026-07-11-lane-worktree-path-relative-repo.md`). When they do, the untracked directory makes `git status` dirty, and `integrate`'s `dirty_base` guard (which refuses to merge while the phase branch has uncommitted changes, so unrelated work can never be hidden inside a merge) fires and blocks an otherwise-successful, fully-verified lane.

The robust defense is the same pattern already used for `.writ/state/`: treat lane worktrees as ephemeral scaffolding and gitignore them (`.writ-lanes-*/`). This holds regardless of where the worktree lands and is not spec-specific — the inside-repo case blocks the very first lane merge, so the ignore rule must ship in the phase orchestration substrate itself rather than be rediscovered per phase.

## Related

- [`.gitignore`](../../../.gitignore)
- [Phase execution state format](../../docs/phase-execution-state-format.md)
- [Bug: lane worktree path collapses inside repo with relative --repo](../../issues/bugs/2026-07-11-lane-worktree-path-relative-repo.md)
