# Story 5: Trial lean tasks on one archived spec

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 2, Story 3, Story 4

## User Story

**As a** Writ maintainer deciding whether to keep the lean-task rules
**I want to** run one archived spec's stories under the old and new generator rules and compare the results
**So that** I can keep or revert the rules based on measured effects

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [ ] Given archived specs under `.writ/specs/archive/`, when the trial picks one, then the pick has at most 3 stories, a `drift-log.md`, and a median task length above 35 words, and each rejected candidate has a recorded reason. `[AC-5.1]`
- [ ] Given the picked spec's first implementation commit resolves, when the worktrees are cut, then `arm-original` holds the archived `user-stories/` unchanged and `arm-lean` holds stories regenerated from the same `spec.md` and `technical-spec.md`, both cut at the same base commit. `[AC-5.2]`
- [ ] Given both arms finish, when the report is written, then it has a per-arm row for story words, `[DEV-` entries, review findings by severity, gates stopped or failed, and tests passing. `[AC-5.3]`
- [ ] Given an arm stops at a gate, when the report is written, then that arm's row reads `stopped at <gate>` and the arm is not retried alone. `[AC-5.4]`
- [ ] Given the measurements are complete, when the report is written, then it states the sample size, ends with exactly one verdict line, and both worktrees are removed. `[AC-5.5]`

## Implementation Tasks

- [ ] 5.1 Write `measure.py` in the session scratchpad. It computes per-arm words per task and `[DEV-` counts, and prints the required report rows as a checklist. `[AC-5.3]`
- [ ] 5.2 Pick the trial spec from `.writ/specs/archive/` by the first criterion's conditions. Record every candidate and its reason in `trial-report.md`. `[AC-5.1]`
- [ ] 5.3 Create worktrees `arm-original` and `arm-lean` at the base commit, in the scratchpad. Copy the spec folder unchanged into `arm-original`. Regenerate `arm-lean`'s `user-stories/` with `user-story-generator` from the same `spec.md` and `technical-spec.md`. `[AC-5.2]`
- [ ] 5.4 Run `/implement-story` on every story in each arm, in dependency order, under the same model and settings. Record any stop with its gate in `trial-report.md`. `[AC-5.3, AC-5.4]`
- [ ] 5.5 Write `trial-report.md` with the method, the per-arm table, the sample size, and the verdict line `lean-tasks: keep`, `lean-tasks: regress (<what>)`, or `lean-tasks: inconclusive`. Remove both worktrees with `git worktree remove`. `[AC-5.3, AC-5.4, AC-5.5]`
- [ ] 5.6 Verify `trial-report.md` against each criterion. Confirm `git status` shows changes only in the spec folder and that both worktrees are gone. `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

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

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Trial worktree: pre-implementation commit cannot be resolved, Trial run: /implement-story fails or stops for a question] — from technical-spec.md → ## Error & Rescue Map
- **Business rules:** [Rule 1 (tasks name files and external contracts), Rule 2 (task word cap and counting method, expanded)] — from spec.md → ## Specification Contract → 📋 Business Rules and spec.md → ## 📋 Business Rules (Expanded)
- **Trial procedure:** technical-spec.md → ## Trial procedure (Story 5)
- **Success criteria:** spec.md → ## Specification Contract → **Success Criteria**
