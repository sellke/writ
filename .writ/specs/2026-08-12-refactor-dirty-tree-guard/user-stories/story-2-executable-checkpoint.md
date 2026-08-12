# Story 2: Executable Checkpoint in `safe-refactor-loop`

> **Status:** Completed ✅ — 2026-08-12
> **Commit:** c7a963bbf2f18f9bd4a11819b31e89c73294e17b
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** coding agent running the safe-refactor loop
**I want to** the checkpoint step to capture a HEAD SHA and assert the tree is clean
**So that** "note the current clean git state" is something I do rather than something the skill assumes

## Acceptance Criteria

> **Amended 2026-08-12 after Gate 0 (CAUTION).** The original three criteria were: step 1 instructs capture+assert; `lint-skill.sh` clean; `eval.sh` Findings 0. The architecture check ran the latter two and found **both already green on the unmodified file** — `lint-skill.sh` passes today, and `grep -rn safe-refactor-loop scripts/` returns zero matches, so `eval.sh` never examines this file. The story had no mechanically verifiable criterion for its own deliverable. It does now.

- [x] Given `skills/safe-refactor-loop/SKILL.md` step 1 item 1, when it is read, then it instructs capturing the current HEAD SHA **and names it as the revert target consumed by step 4**, and asserts `git status --porcelain` is empty at the top of **every** iteration, with the reason stated.
- [x] Given step 4's red branch, when it is read, then it reverts **to the captured checkpoint SHA** and states that restoration includes files the change created — so a reverted module-split leaves a tree clean enough for the next iteration's assert.
- [x] Given a consumer running outside a git repository, when the checkpoint runs, then it warns that per-change revert is unavailable and continues, matching `commands/refactor.md:70` rather than diverging from it.
- [x] Given `scripts/eval.sh`, when it runs, then `require_literal` pins assert the checkpoint's **assertion and revert target** — not merely the topic — so this story is verified rather than assumed.
- [x] Given the skill's own register, when the new wording is read, then it uses the skill's established stop-and-report voice and introduces no `HALT` (control-flow vocabulary that appears in no skill), and the frontmatter `status`, `status_evidence` and `description` are byte-identical.
- [x] Given `bash scripts/lint-skill.sh skills/safe-refactor-loop/SKILL.md`, when it runs, then it exits clean. *(No-regression check, not verification of this story — stated honestly per Gate 0 finding 4.)*
- [x] Given `bash scripts/eval.sh`, when it runs, then it reports `Findings: 0`, with the two expected `skills.lines` / `skills.chars` ratchet warnings recorded as notes.

## Implementation Tasks

- [x] 2.1 Rewrite `:62` Checkpoint as an executable instruction — capture the HEAD SHA and name it as the revert target, assert `git status --porcelain` is empty at the top of every iteration, state the reason, and carry the not-a-git-repo exception from `commands/refactor.md:70`. Use the skill's stop-and-report register, not `HALT`.
- [x] 2.2 Tighten step 4's red branch (`:69-71`) to revert **to the checkpoint SHA**, including files the change created — without this the SHA has no reader and the assert false-positives on module splits (Gate 0 findings 2 and 3).
- [x] 2.3 Add `require_literal` pins in `scripts/eval.sh` on the assertion and the revert target, following Story 1's Implementation Decision 4. Prove they bite by mutation, then revert.
- [x] 2.4 Reconcile the Examples block (`:109-125`) so its traces do not illustrate the superseded assumed-checkpoint (Gate 0 finding 8).
- [x] 2.5 Verify: `lint-skill.sh` clean, frontmatter and description byte-identical, `bash scripts/eval.sh` → `Findings: 0`. Do **not** run `--update-baseline`.

## Notes

**Technical considerations:** `lint-skill.sh:52` forbids `Read skills/` inside a skill — do not add one. Keep the skill's `status: candidate` and evidence fields as they are.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Code reviewed

---

## What Was Built

**Implementation Date:** 2026-08-12

### Files Modified

- **`skills/safe-refactor-loop/SKILL.md`** (step 1 item 1, step 4 red branch, Examples)
  - Checkpoint rewritten from an assumption into an executable instruction: captures the current commit as the change's **revert target** via `git rev-parse HEAD`, asserts `git status --porcelain` is empty at the **top of every iteration**, and states why — step 4 leaves the tree clean on both branches, so anything uncommitted at a checkpoint is a partial commit, an incomplete revert, or an out-of-band edit. Non-empty output stops the loop and reports what is uncommitted. Outside a git repository it notes per-change revert is unavailable and continues, matching `commands/refactor.md:70`.
  - Step 4's red branch now reverts **to the captured revert target**, giving the SHA a reader, and requires restoration to cover files the change created — without which a reverted module split leaves untracked files and the next checkpoint stops on the loop's own leftovers.
  - Both Examples traces reconciled so neither illustrates the superseded assumed-checkpoint.
- **`scripts/eval.sh`** (`check_revert()`)
  - Six `require_literal` pins on the skill. Additions only; no existing pin weakened.

### Implementation Decisions

1. **The invariant is "clean at the top of every iteration", not "clean on the first".** The orchestrator's initial reading was that the tree is dirty mid-loop so an unconditional assert would misfire on iterations 2..N. Gate 0 corrected it: Checkpoint is item 1, Apply is item 2, and item 4 ends both branches clean. The assertion is *strongest* on later iterations, where it catches partial commits and incomplete reverts that the command-level one-shot guard structurally cannot.
2. **No `HALT` in a skill.** That is command control-flow vocabulary and appears in no skill in the tree. The skill's existing stop-and-report register was used instead.
3. **Restoration is required without prescribing `git clean -fd`.** Naming an unbounded destructive command in prose is a foot-gun aimed at ignored build artifacts; the requirement is stated and the scope left to the operator.

### Test Results

**Verification:** `bash scripts/eval.sh` → `Findings: 0`, `Run errors: 0`. `lint-skill.sh` clean. Frontmatter `status`, `status_evidence`, `description` byte-identical to HEAD, catalog and README mirrors intact.
- ✅ TDD: pins written first, `Findings: 4` red against the unmodified skill, then green.
- ✅ All six pins bite individually under mutation; restore returns `Findings: 0`.
- ✅ Two mutations that passed *before* hardening (surgical step-4 revert, softened consequence) now produce findings.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 (Gate 3 PASS with 5 Minor findings; 2 closed in-story, 3 recorded)
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** `skills/safe-refactor-loop/SKILL.md` + `scripts/eval.sh` pins as scoped; `.writ/context.md` touched out of boundary (DEV-001) and corrected.

### Deviations from Spec

- **[DEV-003] Story amended at Gate 0** — Severity: Small. Original ACs were green on the unmodified file; the story could not fail. 3 tasks → 5, ACs rewritten.
- **[DEV-004] Two pins weaker than they looked** — Severity: Small. `revert target` positionally blind; consequence unpinned. Both closed, all six now bite.

### Known residual (recorded, not closed)

- The green branch has the symmetric created-files hole the red branch closed — an unstaged new file leaves the tree dirty for the next checkpoint. Gate 3 rated it Minor and out of AC scope; deliberately not expanded into this story.
- Terminology split: the body says "revert target", the Examples say "checkpoint SHA".
