# Story 5: Trial lean tasks on one archived spec

> **Status:** Completed ✅ (2026-11-06)
> **Priority:** Medium
> **Dependencies:** Story 2, Story 3, Story 4

## User Story

**As a** Writ maintainer deciding whether to keep the lean-task rules
**I want to** run one archived spec's stories under the old and new generator rules and compare the results
**So that** I can keep or revert the rules based on measured effects

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5
> **Verified by:** AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5 — `trial-report.md` in this spec folder (pick table, method, per-arm results, limits, one verdict line), checked by the Gate 3 evaluator against `measure.py` reruns and the arm patches; worktrees removed

- [x] Given archived specs under `.writ/specs/archive/`, when the trial picks one, then the pick has at most 3 stories, a `drift-log.md`, and a median task length above 35 words, and each rejected candidate has a recorded reason. `[AC-5.1]`
- [x] Given the picked spec's first implementation commit resolves, when the worktrees are cut, then `arm-original` holds the archived `user-stories/` unchanged and `arm-lean` holds stories regenerated from the same `spec.md` and `technical-spec.md`, both cut at the same base commit. `[AC-5.2]`
- [x] Given both arms finish, when the report is written, then it has a per-arm row for story words, `[DEV-` entries, review findings by severity, gates stopped or failed, and tests passing. `[AC-5.3]`
- [x] Given an arm stops at a gate, when the report is written, then that arm's row reads `stopped at <gate>` and the arm is not retried alone. `[AC-5.4]`
- [x] Given the measurements are complete, when the report is written, then it states the sample size, ends with exactly one verdict line, and both worktrees are removed. `[AC-5.5]`

## Implementation Tasks

- [x] 5.1 Write `measure.py` in the session scratchpad. It computes per-arm words per task and `[DEV-` counts, and prints the required report rows as a checklist. `[AC-5.3]`
- [x] 5.2 Pick the trial spec from `.writ/specs/archive/` by the first criterion's conditions. Record every candidate and its reason in `trial-report.md`. `[AC-5.1]`
- [x] 5.3 Create worktrees `arm-original` and `arm-lean` at the base commit, in the scratchpad. Copy the spec folder unchanged into `arm-original`. Regenerate `arm-lean`'s `user-stories/` with `user-story-generator` from the same `spec.md` and `technical-spec.md`. `[AC-5.2]`
- [x] 5.4 Run `/implement-story` on every story in each arm, in dependency order, under the same model and settings. Record any stop with its gate in `trial-report.md`. `[AC-5.3, AC-5.4]`
- [x] 5.5 Write `trial-report.md` with the method, the per-arm table, the sample size, and the verdict line `lean-tasks: keep`, `lean-tasks: regress (<what>)`, or `lean-tasks: inconclusive`. Remove both worktrees with `git worktree remove`. `[AC-5.3, AC-5.4, AC-5.5]`
- [x] 5.6 Verify `trial-report.md` against each criterion. Confirm `git status` shows changes only in the spec folder and that both worktrees are gone. `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

## Notes

- Worktrees stay outside the main checkout. The technical spec allows the scratchpad or `/tmp`. Use the scratchpad, per session rules.
- Do not create, remove, or run `git worktree` while pytest runs in this checkout. CLAUDE.md: it breaks `test_smoke_leaves_repo_unchanged`.
- Sample of one. The trial can show a regression. It cannot prove an improvement. The report says so (Business Rule 3 applies to this caveat).
- Each arm pays a full `/implement-story` run per story. Token cost is the main cost of the trial.
- Use the same model and settings in both arms.
- Headless runs: `claude -p` needs `< /dev/null` inside loops. Headless mode lacks AskUserQuestion and Plan Mode, so a gate that asks stops the arm.
- A stopped arm is recorded, not retried alone. Retrying one arm breaks the comparison.
- Archived drift logs use different formats, so `[DEV-` counts may undercount. See spec.md → ## Evidence.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Trial worktree: pre-implementation commit cannot be resolved, Trial run: /implement-story fails or stops for a question] — from technical-spec.md → ## Error & Rescue Map
- **Business rules:** [Rule 1 (tasks name files and external contracts), Rule 2 (task word cap and counting method, expanded)] — from spec.md → ## Specification Contract → 📋 Business Rules and spec.md → ## 📋 Business Rules (Expanded)
- **Trial procedure:** technical-spec.md → ## Trial procedure (Story 5)
- **Success criteria:** spec.md → ## Specification Contract → **Success Criteria**

---

## What Was Built

**Implementation Date:** 2026-11-06

### Files Created

1. **`.writ/specs/2026-11-06-lean-story-tasks/trial-report.md`**
   - Pick table, method, per-arm results, the substantive difference, limits, and the verdict `lean-tasks: keep`

### Files Modified

- **`drift-log.md`**, **`spec-lite.md`** — DEV-009 (Small, auto-amended) and DEV-010 (Medium, logged)

Scratch only (not committed): `measure.py`, per-arm gate summaries, recorded test outputs, and full arm patches in the session scratchpad. Worktrees and `trial/*` branches removed.

### Implementation Decisions

1. **Picked `2026-08-13-claude-md-install-merge`** — qualifies with 2 stories; `phase11-stage4b-pipeline-demote` also qualifies but has 3.
2. **Reduced Gate 1 + Gate 3 loop in both arms** — no recipe or coverage tooling at the old commit (DEV-010).
3. **Seeded arm-original from `16048cd`** — the stories as first committed, with completion bookkeeping reset (DEV-009).

### Test Results

**Verification:** Manual, against the report

- ✅ arm-original: Story 1 PASS after one recode (Major data-loss finding reproduced and fixed), Story 2 PASS; all story tests pass
- ✅ arm-lean: Stories 1 and 2 PASS on first review; all story tests pass
- ✅ Report numbers re-derived by the Gate 3 evaluator from `measure.py` and the patches

**Coverage:** N/A

### Review Outcome

**Result:** PASS with drift note

- **Iteration count:** 1 iteration(s)
- **Drift:** Medium (DEV-010)
- **Security:** Clean
- **Boundary Compliance:** Only the spec folder changed in this repo

### Deviations from Spec

- **[DEV-009] arm-original seeded from the pre-implementation commit, not the `archive/` copy** — Severity: Small; auto-amended in spec-lite.md
- **[DEV-010] Reduced, hand-run pipeline instead of `/implement-story`** — Severity: Medium; logged, disclosed in the report

### Lessons Learned

1. **The original stories prescribed a bug twice** — `16048cd` shipped it in August, and the trial's original arm reproduced it until review caught it. The regenerated stories did not prescribe it. One spec; the cause cannot be pinned on the task rules alone.
2. **Lean stories log more Small drift** — leaving decisions to the coder puts more of them on record.
