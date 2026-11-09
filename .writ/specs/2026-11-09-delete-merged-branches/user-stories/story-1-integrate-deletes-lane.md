# Story 1: Integrate deletes the merged lane branch

> **Status:** Not Started
> **Priority:** Normal
> **Dependencies:** None

## User Story

**As a** developer running `/implement-phase`
**I want to** `phase-state.py integrate` to delete the lane branch it just merged
**So that** `git branch` lists no lane branch after a phase, and a refused deletion is recorded instead of forced

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given a lane with a verified `succeeded` result and a clean worktree removal, when `phase-state.py integrate` merges it, then the lane branch is gone from `git branch`, the returned JSON and the spec record carry `laneBranchDeleted: true`, and status is `integrated` `[AC-1.1]`
- [ ] Given git refuses `git branch -d` for the lane (for example, the branch is still checked out in a worktree), when integrate merges, then status is `integrated`, `laneBranchDeleted` is `false`, `laneBranchKeptReason` holds git's message, the branch still exists, and no force delete runs `[AC-1.2]`
- [ ] Given a failed, malformed, or merge-conflicting lane result, when integrate runs, then the lane branch still exists and the spec record has no `laneBranchDeleted` key `[AC-1.3]`
- [ ] Given an `integrated` spec whose lane branch no longer exists, when `phase-state.py reconcile` runs, then it reports `consistent` `[AC-1.4]`
- [ ] Given the Story 1 text changes, when the text pins run, then `commands/implement-phase.md` Step 3.2 item 4 says the worktree and lane branch are removed, `.writ/docs/phase-execution-state-format.md` documents `laneBranchDeleted` and `laneBranchKeptReason`, and the `implement-phase.md` byte pin matches the file `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write tests in `scripts/tests/test_phase_state.py` for each acceptance criterion, including a refused-deletion case and reconcile of an integrated spec with no lane branch `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.2 In `scripts/phase-state.py` integrate, delete the lane branch with `git branch -d` after the worktree removal, and only after a successful merge. Never force-delete (Business Rule 6) `[AC-1.1, AC-1.2]`
- [ ] 1.3 In `scripts/phase-state.py` integrate, record `laneBranchDeleted` and, on refusal, `laneBranchKeptReason` on the spec record and in the returned JSON. Status stays `integrated`; keep the `laneBranch` key (Business Rule 7) `[AC-1.1, AC-1.2]`
- [ ] 1.4 Add `lane-branch-deleted-after-merge` to `scripts/eval-phase-lane.py` after `worktree-removed-after-merge`. Assert the lane branch still exists in the failed and malformed scenarios `[AC-1.1, AC-1.3]`
- [ ] 1.5 Update `.writ/docs/phase-execution-state-format.md` (`laneBranch` row, new `laneBranchDeleted` and `laneBranchKeptReason` rows) and `commands/implement-phase.md` Step 3.2 item 4. Offset growth in that file, or re-pin its `KNOWN_OVER_BUDGET` entry in `scripts/tests/test_governor_enforcement.py` with a dated comment `[AC-1.5]`
- [ ] 1.6 Verify acceptance criteria are met by the tagged tests and the phase-lane eval check `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [ ] 1.7 Verify all tests pass: pytest on Python 3.9 and 3.14, each run alone; `bash scripts/eval.sh --check=phase-lanes`; `python3 scripts/gen-platform-trees.py --check` `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

- **Current behavior.** `cmd_integrate` checks out the phase branch, runs `merge --no-ff`, runs `worktree remove --force` with `check=False`, then records `integrated` and `mergeCommit`. The lane branch stays.
- **Order matters.** `git branch -d` refuses a branch checked out in any worktree. Remove the worktree first. If removal fails silently, the `-d` refusal is what gets recorded.
- **Conflict path returns early.** The merge-conflict branch aborts the merge and returns `attention_required` before any deletion. The deletion runs only after the merge succeeds.
- **`-d` succeeds after a clean merge.** The lane tip is an ancestor of the new merge commit on the checked-out phase branch, so `-d` has no reason to refuse. A refusal means something unusual; record it, do not override it.
- **Reconcile needs no code change.** An integrated spec is checked only by `mergeCommit`. Business Rule 7 keeps `laneBranch` as the historical key. The test in 1.1 pins this.
- **Byte budget.** `commands/implement-phase.md` is pinned at `KNOWN_OVER_BUDGET` 1464 in `scripts/tests/test_governor_enforcement.py`. The Step 3.2 wording change adds bytes.
- **Eval check name.** `phase-lanes` is the `eval.sh --check` name for `scripts/eval-phase-lane.py`.
- **Test isolation.** Run pytest alone. Do not run `eval.sh` or the bash tests in the same checkout while pytest runs (project CLAUDE.md).
- **Priority.** Set to `Normal` per the request. The agent template lists High, Medium, or Low.

## Context for Agents

- **Error map rows:** [`git branch -d` refuses the lane] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** []
- **Business rules:** [Business Rule 6, Business Rule 7] — spec.md → ## Business Rules (Expanded)
- **Experience:** [Feedback model (integrate returns `laneBranchDeleted` in its JSON and records it in phase state), Error experience (cleanup never fails an integrate; a refused delete keeps the branch and reports the reason)] — spec.md → ## Specification Contract → ## 🎯 Experience Design
