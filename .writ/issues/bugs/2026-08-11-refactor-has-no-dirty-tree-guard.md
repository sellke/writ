# `/refactor` Has No Dirty-Tree Guard Before Its First Mutation

> **Type:** Bug
> **Priority:** High
> **Effort:** Small
> **Created:** 2026-08-11
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

`/refactor` establishes a green baseline (tests, typecheck, lint) but never checks that the working tree is clean, so its per-change "revert immediately" step can discard uncommitted work it did not create.

## Current State

- `commands/refactor.md` Step 1.2 "Baseline Verification" gates on three things only: test suite, typechecker, linter. Git state is not among them.
- `skills/safe-refactor-loop/SKILL.md` step 0 repeats the same trio; its step 1 says "**Checkpoint** — note the current clean git state so a revert is one step", which *assumes* a clean tree and prescribes no check that establishes one.
- `/revert` by contrast HALTs on `git status --porcelain` being non-empty **before any git operation** (`commands/revert.md:56-62`) and lists that guard as Safety Guarantee #1.
- Consequence: if a user runs `/refactor` on a dirty tree, a change that verifies red triggers "revert immediately" against a tree that mixes the refactor's edit with the user's uncommitted work. The revert cannot distinguish them.
- `--dead-code` mode compounds this: it removes "orphan files", and an untracked orphan file, once deleted, has no git object to restore from at all.

## Expected Outcome

- `/refactor` runs a `git status --porcelain` guard before Step 1.2's baseline, HALTing with the same wording discipline `/revert` uses, or explicitly documents which paths are safe on a dirty tree and why.
- `--dead-code` deletions are checked against `git ls-files` so an untracked deletion target is surfaced rather than silently removed.
- The `safe-refactor-loop` skill's "note the current clean git state" becomes an executable instruction (capture the HEAD SHA; assert the tree is clean) rather than an assumption.

## Relevant Files

- `commands/refactor.md` - Step 1.2 baseline verification; the missing guard belongs here
- `skills/safe-refactor-loop/SKILL.md` - step 0/step 1 own the per-change checkpoint-and-revert loop
- `commands/revert.md` - lines 56-62 are the guard to mirror

## Notes

Found by the read-only applicability pass in `.writ/specs/2026-08-11-autonomy-gate-classes/user-stories/story-3-destructive-command-applicability.md`, which assessed the four destructive-class commands against ADR-022's reversibility precondition. Under that precondition `/refactor` currently fails condition (1) — "provably git-revertable, confined to tracked files" — specifically because of this gap.

Not fixed in that spec by design (Business Rule 9: the four destructive-class command files are read-only inputs there). This is the highest-value single fix the assessment surfaced: it is small, it is precedented by `/revert`, and it converts one of the four condition-(1) failures into a pass.
