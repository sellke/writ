# create-lane places lane worktrees inside the repo when --repo is relative

> **Type:** Bug
> **Priority:** Normal
> **Effort:** Small
> **Created:** 2026-07-11
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

`phase-state.py create-lane` derives the lane worktree location from `repo.parent`, so a relative `--repo .` collapses the intended repo-sibling path into a directory *inside* the repo — dirtying the phase branch.

## Current State

- `cmd_create_lane` computes: `worktree_root = repo.parent / f".writ-lanes-{phase}"` (`scripts/phase-state.py` ~line 190).
- With an absolute `--repo /abs/writ` → `/abs/.writ-lanes-{phase}/…` (sibling of the repo, **outside** it — the apparent intent).
- With a relative `--repo .` → `Path(".").parent` is `.`, so lanes land at `./.writ-lanes-{phase}/…` **inside** the repo.
- Observed live in the Phase 7 run: specs 1–2 (invoked with `--repo .`) landed inside the repo; specs 3–4 (invoked with `--repo /abs`) landed as siblings — non-deterministic placement from the same command.
- The inside-repo case makes the untracked worktree dir show as a dirty working tree and trips `integrate`'s `dirty_base` guard, blocking the first lane merge (worked around by gitignoring `.writ-lanes-*/`, commit `f06f405`).

## Expected Outcome

- Lane worktree placement is deterministic regardless of how `--repo` is expressed.
- Recommended fix: resolve the repo to an absolute path before deriving the parent, e.g. `repo = Path(args.repo).resolve()` in `cmd_create_lane`, so `--repo .` and `--repo /abs/writ` both yield the same sibling location.
- Confirm the chosen location is documented in `.writ/docs/phase-execution-state-format.md` (the `worktreePath` contract).

## Relevant Files

- `scripts/phase-state.py` - `cmd_create_lane` worktree_root computation (~line 190)
- `.writ/docs/phase-execution-state-format.md` - documents `worktreePath`; keep in sync with the fix

## Related Issues

- (none)

## Notes

- The `.writ-lanes-*/` gitignore rule (`f06f405`) is defense-in-depth and should stay even after this fix, since a future `--worktree-root` could still point inside the repo.
- Surfaced during the first genuine multi-spec `/implement-phase` run (Phase 7); see lesson `.writ/knowledge/lessons/2026-07-11-lane-worktree-dirs-must-be-gitignored-for-implement-phase-merges.md`.
