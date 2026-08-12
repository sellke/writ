# Story 1: Porcelain Guard Before Baseline Verification

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** maintainer running `/refactor` on a repository with uncommitted work
**I want to** the command to stop before its first mutation rather than after
**So that** its revert-on-red step never fires against a tree that mixes my uncommitted work with the refactor's own edit

## Acceptance Criteria

- [ ] Given a dirty working tree, when `/refactor` is invoked, then it HALTs before Step 1.2 Baseline Verification and names a remedy, mirroring the wording discipline at `commands/revert.md:60-67`.
- [ ] Given a clean working tree, when `/refactor` is invoked, then behaviour is unchanged from before this story.
- [ ] Given `--dead-code` with an untracked deletion target, when the target list is resolved, then that target is reported and skipped rather than removed, because no git object exists to restore it from.
- [ ] Given the full suite, when `bash scripts/eval.sh` runs, then it reports `Findings: 0`.

## Implementation Tasks

- [ ] 1.1 Read `commands/revert.md:60-67` and reproduce its guard discipline, not a new variant
- [ ] 1.2 Insert the guard ahead of Step 1.2 Baseline Verification in `commands/refactor.md`
- [ ] 1.3 Add the `--dead-code` untracked-target rule against `git ls-files`
- [ ] 1.4 Verify a clean-tree run is behaviourally unchanged; run `bash scripts/eval.sh` to `Findings: 0`

## Notes

**Technical considerations:** `commands/refactor.md` carries `problem:`/`outcome:`/`exit_criteria:` and a `loop:` block (`change`, 10, `halt_reported`, evidence `no recorded run`). Preserve all of it — `eval-loop-bounds.py` asserts the `no recorded run` literal is present.

**Risks:** Keep the guard compact; `refactor.md` is not a disclosure target and should not grow materially.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Code reviewed
