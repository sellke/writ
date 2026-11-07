# Story 6: Before/after pipeline trial

> **Status:** Completed ✅ (2026-11-07)
> **Priority:** Medium
> **Dependencies:** Story 4, Story 5

## User Story

**As a** Writ maintainer deciding whether to keep the lean pipeline
**I want to** run one archived spec through the default `/implement-story` pipeline in two arms, before and after the lean changes, and measure the difference
**So that** I can keep, revert, or stop the lean pipeline on recorded evidence

## Acceptance Criteria

> **AC IDs assigned through:** AC-6.5
> **Verified by:** AC-6.1 — `git diff 6cfb1e1 2c63dfa -- .writ/specs` empty and the overlay file list in trial-report.md → Method, re-derived in the Gate 3 review (`.writ/state/gate3-review-story-6-lean-pipeline-trial.md`)
> **Verified by:** AC-6.3 — `timeline.txt` per arm (one run per story) and the arm-before stop rows in trial-report.md → Results, re-derived in the Gate 3 review
> **Verified by:** AC-6.5 — `git worktree list` after removal (no arm worktrees) and a clean `git status` under `commands/` and `agents/`, recorded in What Was Built → Review Outcome

- [x] Given two worktrees cut from one commit, when the trial starts, then `arm-before` holds the command and agent files from the spec's base commit, `arm-after` holds them from Story 5's commit, and both hold the same story files `[AC-6.1]`
- [x] Given both arms have finished or stopped, when `trial-report.md` is written, then it contains Method, Pick, a per-arm table of the seven measures, a Limits section that states the sample size, and one verdict line `[AC-6.2]`
- [x] Given an arm stops at a gate or crashes, when the report is written, then that arm's row reads `stopped at <gate>` and the other arm is not re-run alone `[AC-6.3]`
- [x] Given the measured results, when the verdict line is checked, then it is exactly `lean-pipeline: keep`, `lean-pipeline: regress (<what>)`, or `lean-pipeline: inconclusive`, and more escaped Major+ defects in `arm-after` yield `regress` `[AC-6.4]`
- [x] Given the trial has finished, when both worktrees are removed, then `git worktree list` shows only the main checkout and `git status` shows no change under `commands/` or `agents/` `[AC-6.5]`

## Implementation Tasks

- [x] 6.1 Write tests in `scripts/tests/test_lean_pipeline_trial_report.py` that parse `trial-report.md`, assert its single verdict line is one of the three allowed values, and assert `regress` when `arm-after` has more escaped defects `[AC-6.4]`
- [x] 6.2 Record candidate specs and the pick in `trial-report.md`, then cut `arm-before` and `arm-after` worktrees from one commit in the scratchpad. Set `commands/implement-story.md` and `agents/` to the spec's base commit in `arm-before`, and to Story 5's commit in `arm-after` `[AC-6.1]`
- [x] 6.3 Run `/implement-story` on every story in order in each arm, headless via `claude -p ... < /dev/null`, default path, same model and settings. Record each gate stop and recode in the scratchpad `[AC-6.3]`
- [x] 6.4 Measure both arms on blocking findings, escaped Major+ defects, review iterations, wall-clock time, tokens, orchestrator script calls, and failed or stopped gates. Write method, pick, per-arm table, limits with sample size, and verdict line into `trial-report.md` `[AC-6.2, AC-6.4]`
- [x] 6.5 Remove both worktrees with `git worktree remove`, then confirm `git status` shows no change under `commands/` or `agents/` `[AC-6.5]`
- [x] 6.6 Verify acceptance criteria are met by reading `trial-report.md` and running `git worktree list` `[AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5]`
- [x] 6.7 Verify all tests pass: run `uv run --isolated --python 3.9 --with pytest pytest scripts/tests/test_lean_pipeline_trial_report.py` and the same with `--python 3.14`, with no other pytest in flight `[AC-6.4]`

## Notes

- **Procedure:** `technical-spec.md` → `## Trial procedure (Story 6)` defines the pick, worktree, run, measure, and report steps. Follow it; this story does not restate it.
- **Sample size:** one spec, one run per arm. The report can show a regression. It cannot prove an improvement, and it must say so (`technical-spec.md` → Trial procedure, step 5; `spec.md` → Technical Concerns).
- **Regression rule:** more escaped Major+ defects in `arm-after` is `regress`. Nothing reverts automatically. This story changes no product file.
- **Planted catch:** `2026-08-13-claude-md-install-merge` is the preferred pick. Its known Major data-loss defect is recorded in `.writ/specs/2026-11-06-lean-story-tasks/trial-report.md` → Results → "The one substantive difference". Confirm it still meets the pick rules (at most 3 stories, identifiable implementation commits, a Gate 3 FAIL or drift entry) before choosing it.
- **Escaped-defect check:** a post-run read against the known defect, plus a full-suite run on each arm (procedure step 4). Run the suites one at a time.
- **Stay off the main checkout's pytest:** run no pytest or `eval.sh` in the main checkout while worktrees are cut or changed. `test_smoke_leaves_repo_unchanged` fails otherwise (`CLAUDE.md`).
- **Headless limits:** `claude -p` has no AskUserQuestion and no Plan Mode. A stop for a question counts as `stopped at <gate>` in the report.
- **Measurement sources:** tokens come from session usage or `measure-invocation.py` (procedure step 4).
- **Arm inputs:** `arm-after` uses the commit for Story 5 from `git log`. Story 4 and Story 5 must be complete first.
- **Test runtime:** the report test is stdlib only and must pass on the Python 3.9 floor (`CLAUDE.md`).
- **Verification scope:** this story runs only the report test. The full pytest suite on both interpreters, the bash tests, and `eval.sh` run once at the end of the spec (`spec.md` → Success Criteria).

## Context for Agents

- **Error map rows:** [Trial (Story 6)] — from `technical-spec.md` → Error & Rescue Map (arm stops; record the stop, do not re-run one arm)
- **Shadow paths:** []
- **Business rules:** []
- **Experience:** []
- **Trial procedure:** `technical-spec.md` → `## Trial procedure (Story 6)`

---

## What Was Built

**Implementation Date:** 2026-11-07

### Files Created

1. **`.writ/specs/2026-11-06-lean-story-pipeline/trial-report.md`** — Pick, Method, a per-arm table of the measures, Limits, and the verdict `lean-pipeline: keep`
2. **`scripts/tests/test_lean_pipeline_trial_report.py`** — 9 tests: the verdict line is one of three values; more escaped Major+ defects in `arm-after` must read `regress`; the live report passes
3. **`scripts/tests/test_trial_report_tokens_repro.py`, `scripts/tests/test_trial_report_gates_repro.py`** — Gate 3 iteration 1 evidence repros, committed unchanged

### Files Modified

[None modified]

### Implementation Decisions

1. **Arms share one base tree and differ only in the pipeline overlay** — `f054e9d` plus the trial spec from `16048cd`; overlay from `40b1a7c` (before) and `183768c` (after); the stories' own targets (`install.sh`, `update.sh`) are never overlaid.
2. **Headless, same model, project/local settings only** — `claude -p ... --model claude-opus-5-5 --permission-mode bypassPermissions --setting-sources project,local < /dev/null`, both arms at once.

### Test Results

**Verification:** Automated

- ✅ Recorded run (Python 3.9): 11 passed across the report test and both repros; 9 passed on Python 3.14 for the report test
- ✅ Planted-defect replay: edit lost in `arm-before`'s tree, survives in `arm-after` (`6aecc66`)
- ✅ Each arm's story and regression bash tests pass

**Coverage:** N/A

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s) (iteration 1 FAIL: token row and gate row did not match the raw streams; confirmed, row 7)
- **Gate 3 route:** `evaluator-agent`
- **Drift:** Medium (DEV-024, DEV-025)
- **AC-6.5:** `git worktree remove --force` on both arms; `git worktree list` then showed the main checkout, this run's worktree, and two other sessions' worktrees; `git status` clean under `commands/` and `agents/`

### Trial result

| Measure | arm-before | arm-after |
|---|---|---|
| Stories completed | 0 of 2 | 2 of 2 |
| Escaped Major+ defects | 0 | 0 |
| Orchestrator script calls | 29 | 12 |
| Cost | $5.58 | $9.37 |

Verdict: `lean-pipeline: keep` (one spec, two stories, one run per arm).

### Deviations from Spec

See `drift-log.md` Story 6: DEV-024, DEV-025 (Medium).

### Lessons Learned

1. **Re-derive the orchestrator's own numbers** — a resumed headless session writes several result events; per-event `usage` sums, `modelUsage` is cumulative. The evaluator caught the first report reading one event.

### Next Story

None: spec complete pending the integration suite.

