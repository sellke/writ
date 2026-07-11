---
category: lessons
tags: [implement-phase, git-worktrees, phase-orchestration]
created: 2026-07-11
related_artifacts:
  - .gitignore (phase-branch commit f06f405: 'gitignore ephemeral .writ-lanes-* worktree dirs')
  - phase-state.py integrate returned dirty_base during 2026-07-10-skill-lifecycle integration until the ignore rule was added
  - .writ/state/phase-execution-20260711T041106Z.json (Phase 7 first genuine multi-spec run)
---

# Lane worktree dirs must be gitignored for /implement-phase merges

## TL;DR

The ephemeral per-spec lane worktrees that /implement-phase creates under .writ-lanes-{phase}/ inside the repo must be gitignored (like .writ/state/). Otherwise the untracked worktree directory shows as a dirty working tree and trips phase-state.py integrate's dirty_base guard, blocking the verified merge of an otherwise-successful lane. This surfaces on every multi-spec phase run, not just one spec.

## Context

Recorded at phase close from evidence-bound knowledge writeback.

## Detail

The ephemeral per-spec lane worktrees that /implement-phase creates under .writ-lanes-{phase}/ inside the repo must be gitignored (like .writ/state/). Otherwise the untracked worktree directory shows as a dirty working tree and trips phase-state.py integrate's dirty_base guard, blocking the verified merge of an otherwise-successful lane. This surfaces on every multi-spec phase run, not just one spec.

## Related

