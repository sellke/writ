---
category: lessons
tags: [phase-execution, implement-phase, worktree, lessons]
created: 2026-07-11
related_artifacts:
  - scripts/phase-state.py
---

# create-lane worktree root: use --repo . or an explicit in-repo --worktree-root

## TL;DR

When creating an /implement-phase lane with scripts/phase-state.py create-lane, run it with --repo . from the repository root, or pass an explicit in-repo --worktree-root; an absolute --repo path makes the reducer compute the lane root as repo.parent/.writ-lanes-{phase}, which places the lane worktree as a sibling of the repository (outside the repo and outside the .writ-lanes-*/ gitignore) rather than inside it.

## Context

Recorded at phase close from evidence-bound knowledge writeback.

**Cited evidence:**

- scripts/phase-state.py create-lane computes worktree_root = repo.parent / .writ-lanes-{phase} when --worktree-root is unset (create-lane region around line 190)
- Recurred across phases: Phase 7 closure records a tracked create-lane worktree-pathing bug, and Phase 8 spec-2 lane initially landed at /Users/Adam/Projects/.writ-lanes-8 (sibling of the repo) before being recreated with an explicit --worktree-root
- .writ/product/roadmap.md Phase 7 closure note

## Related

- `scripts/phase-state.py`
