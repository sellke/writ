# Story 1: Porcelain Guard Before Baseline Verification

> **Status:** Completed ✅ — 2026-08-12
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** maintainer running `/refactor` on a repository with uncommitted work
**I want to** the command to stop before its first mutation rather than after
**So that** its revert-on-red step never fires against a tree that mixes my uncommitted work with the refactor's own edit

## Acceptance Criteria

- [x] Given a dirty working tree, when `/refactor` is invoked, then it HALTs before Step 1.2 Baseline Verification and names a remedy, mirroring the wording discipline at `commands/revert.md:60-67`.
- [x] Given a clean working tree, when `/refactor` is invoked, then behaviour is unchanged from before this story.
- [x] Given `--dead-code` with an untracked deletion target, when the target list is resolved, then that target is reported and skipped rather than removed, because no git object exists to restore it from.
- [x] Given the full suite, when `bash scripts/eval.sh` runs, then it reports `Findings: 0`.

## Implementation Tasks

- [x] 1.1 Read `commands/revert.md:60-67` and reproduce its guard discipline, not a new variant
- [x] 1.2 Insert the guard ahead of Step 1.2 Baseline Verification in `commands/refactor.md`
- [x] 1.3 Add the `--dead-code` untracked-target rule against `git ls-files`
- [x] 1.4 Verify a clean-tree run is behaviourally unchanged; run `bash scripts/eval.sh` to `Findings: 0`

## Notes

**Technical considerations:** `commands/refactor.md` carries `problem:`/`outcome:`/`exit_criteria:` and a `loop:` block (`change`, 10, `halt_reported`, evidence `no recorded run`). Preserve all of it — `eval-loop-bounds.py` asserts the `no recorded run` literal is present.

**Risks:** Keep the guard compact; `refactor.md` is not a disclosure target and should not grow materially.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Code reviewed

---

## What Was Built

**Implementation Date:** 2026-08-12

### Files Created

[None created]

### Files Modified

- **`commands/refactor.md`** (Step 1.1, new Step 1.1b, Step 1.3, Safety Guarantees; +22/-9 lines)
  - Added `#### Step 1.1b: Dirty-Tree Guard` between Step 1.1 and Step 1.2: runs `git status --porcelain`; non-empty output HALTs with `"Working tree has uncommitted changes — commit or stash before refactoring. Nothing has been changed."` and the reason (Phase 3 reverts a red change with git, and a revert cannot tell uncommitted work from the edit it just made).
  - Fail-closed on unreadable repo state: any non-zero exit HALTs too (corrupt index, stale `.git/index.lock`, permissions), with **not a git repository** as the sole warn-and-continue exception. `--dry-run` is exempt from the guard entirely — it stops at Phase 2 and never runs the revert-on-red loop.
  - Retargeted Step 1.1's direct-target jump from "proceed to Step 1.2" to "proceed to Step 1.1b", so `/refactor <path>` — the first row of the Modes table — cannot route past the guard.
  - Step 1.3 gained the `--dead-code` tracked-target rule: run `git ls-files --error-unmatch -- <path>` before any whole-file deletion enters the plan; a non-zero exit means untracked, so report it as skipped and never delete it. Scoped explicitly to whole-file deletions — unused exports and symbols inside tracked files are unaffected.
  - Safety Guarantees renumbered seven → eight, with **Clean tree required** inserted as #1, matching `commands/revert.md`'s ordering where the dirty-tree guard is also #1.
  - Frontmatter untouched: `problem:`, `outcome:`, `exit_criteria:` and the `loop:` block (including the `no recorded run` literal asserted by `scripts/eval-loop-bounds.py`) all survive verbatim.
- **`scripts/eval.sh`** (`check_revert()`, +19/-0 lines)
  - Added a `local refactor_cmd` declaration and 8 `require_literal` pins on `commands/refactor.md`, sited beside the existing `/revert` safety pins, with a comment recording the shared dirty-tree discipline.
  - Pins: `#### Step 1.1b: Dirty-Tree Guard`, `git status --porcelain`, `HALT immediately`, `commit or stash before refactoring`, `exempt from this guard`, `not a git repository`, `git ls-files --error-unmatch`, `report it as skipped`.
  - Additions only — no existing pin was deleted, narrowed, or reworded.

### Implementation Decisions

1. **Guard promoted to its own numbered step** — makes reachability structural rather than positional, and gives the eval a stable heading to pin. This was the fix for a Gate 3 FAIL; see DEV-001.
2. **Wording mirrored near-verbatim from `commands/revert.md:60-68`** — per Task 1.1, so the repo has one dirty-tree discipline rather than two variants that can drift apart.
3. **Pins housed in the existing `check_revert()` rather than a new `check_refactor()`** — keeps related safety pins co-located and avoids growing the `scripts/` surface further.
4. **Pins carry the assertion, not just the topic** — `HALT immediately` and `commit or stash before refactoring` mean inverting the guard to "warn and continue", or dropping the remedy, now breaks a pin. This closed a Gate 3 finding that the first pin set could stay green through exactly that regression.
5. **Fail-closed on unreadable repo state** — a repo whose state cannot be read is not a clean tree. Not-a-git-repository is the single argued exception, since there is no uncommitted work to protect there.
6. **Leanness ratchet warnings left standing** — `--update-baseline` would have moved every surface's floor while recording no reason. See DEV-002.

### Test Results

**Verification:** `bash scripts/eval.sh` — **Findings: 0, Run errors: 0** (report `.writ/state/eval-20260812-071448.md`); `check_revert` PASS 23/23 scenarios. Regression: `scripts/eval-loop-bounds.py` 37/37 PASS including `refactor-no-recorded-run-literal` and the blocking `schema-refactor` frontmatter contract check; `scripts/eval-leanness.py` `"structural": []` (the blocking gate) with only non-blocking ratchet warnings.

**Coverage:** N/A — the story created zero new files, so the ≥80%-line-coverage-on-new-files gate has no target. The relevant test surface for the two modified markdown/bash files is the `require_literal` pin set.

- ✅ All 8 pinned literals resolve exactly once in `commands/refactor.md`
- ✅ All 8 pins sit on unconditional straight-line code inside `check_revert()` — no early `return`/`exit`/enclosing conditional above them, so a green run genuinely exercised every one
- ✅ Additions-only confirmed: `git diff --cached scripts/eval.sh | grep '^-'` is empty
- ✅ Behavioural trace: dirty tree, clean tree, `--dry-run`, non-repo, and gitignored `--dead-code` target each reach their intended outcome
- ✅ `commands/revert.md`'s 7 pre-existing pins in the same block untouched and still passing
- ✅ `skills/safe-refactor-loop/SKILL.md` (Story 2) and `.writ/leanness-baseline.json` byte-identical to HEAD

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Clean — the change increases safety posture; the `--` argument terminator on `git ls-files` also removes a narrow argument-injection footgun where a filename beginning with `-` could be reparsed as a flag.
- **Boundary Compliance:** Both deliverables cleanly inside Owned. Frontmatter and the Story 2 overlap file (`skills/safe-refactor-loop/SKILL.md`) both untouched. Harness scaffolding present in the working tree (`.gitignore`, `.claude/worktrees/`, `.claude/agent-memory/`) was excluded from the story commit.

### Deviations from Spec

- **[DEV-001] Guard implemented as a distinct numbered step rather than inline prose ahead of Step 1.2** — Severity: Small
  - Spec said: Task 1.2 — "Insert the guard ahead of Step 1.2 Baseline Verification in `commands/refactor.md`." No structural form was prescribed.
  - Reality: The guard is its own heading, `#### Step 1.1b: Dirty-Tree Guard`, sited between Step 1.1 and Step 1.2, with the direct-target jump at `commands/refactor.md:48` retargeted at it.
  - Resolution: Auto-amended
  - Spec amendment: `spec-lite.md` "Implementation Approach" now reads "Guard is its own step (`Step 1.1b`) between Step 1.1 and Step 1.2 Baseline Verification in `commands/refactor.md`; every upstream jump instruction is retargeted at it." `spec.md` unmodified. Recommended follow-up: mirror the wording into `sub-specs/technical-spec.md`'s Edit surface row.
- **[DEV-002] `scripts/` leanness ratchet warnings tripped by the eval.sh additions** — Severity: Small
  - Spec said: Nothing — `.writ/leanness-baseline.json` is outside the story's edit surface.
  - Reality: The 19-line addition pushed `scripts.lines` to 32557 (ceiling 32538) and `scripts.chars` to 1409164 (ceiling 1407447). Overshoot equals the addition exactly.
  - Resolution: Flagged for review
  - Spec amendment: N/A — flagged for post-implementation review. The baseline owner should record the increment with a dated reason naming this story rather than running `--update-baseline`.

### Open Follow-up (not drift)

Nothing pins the jump sentence `proceed to Step 1.1b` at `commands/refactor.md:48`. The review and testing gates independently found that reverting that one line would leave all 8 new pins green while re-opening the exact defect this story fixed — the pins assert the guard's *content* exists, not that the only jump into Phase 1 points at it. Both gates declined to block. A 9th pin, `require_literal "$refactor_cmd" 'proceed to Step 1.1b' "..."`, closes it. Related structural blind spot: the pins are presence-only greps and do not assert document *order*, so moving Step 1.1b after Phase 4 would keep every pin green. Position was manually verified correct for this run.
