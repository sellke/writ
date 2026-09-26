# Story 4: Drift Roll-up at Spec End

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** Writ maintainer running `/implement-spec`
**I want to** one line at spec end counting the drift logged during the run, with the Medium and Large headlines
**So that** Medium warnings from individual stories add up somewhere I will read instead of scrolling past

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.4

- [x] Given `drift-format.py summary --drift-log L [--since D]`, when L has story sections with `> Run:` dates and DEV entries, then it prints `pass`, one `medium:` or `large:` line per Medium/Large DEV (`DEV-NNN title (Story N)`), and a summary line `S small, M medium, L large [since D]` last; with `--since`, only sections dated on or after D count `[AC-4.1]`
- [x] Given a missing log, when `summary` runs, then it prints `pass` with zero counts; given an unreadable log, then `unverifiable` with `reason: drift_log_unreadable`; given a malformed `--since`, then exit 2 `[AC-4.2]`
- [x] Given `commands/implement-spec.md` Step 4.2, when the spec run completes, then it runs `summary` with `--since` set to the execution state's start date and adds a `Drift this run:` line plus the Medium headlines to the report `[AC-4.3]`
- [x] Given any roll-up output, when the report is built, then it never changes the checker verdict, the banner, or any story status; and a wiring test pins the Step 4.2 invocation `[AC-4.4]`

## Implementation Tasks

- [x] 4.1 Write failing tests in `scripts/tests/test_drift_format.py` for counts by severity, headline lines, `--since` filtering, sections with no Run date, missing and unreadable logs, and bad `--since` `[AC-4.1, AC-4.2]`
- [x] 4.2 Add the `summary` subcommand to `scripts/drift-format.py` per technical-spec §4, reusing the existing entry parser; update the docstring `[AC-4.1, AC-4.2]`
- [x] 4.3 Write a failing wiring test pinning the Step 4.2 `summary` invocation and its report-only rule `[AC-4.3, AC-4.4]`
- [x] 4.4 Edit `commands/implement-spec.md` Step 4.2: invocation, `Drift this run:` report line, report-only sentence `[AC-4.3, AC-4.4]`
- [x] 4.5 Verify: `uv run --python 3.9 pytest scripts/tests/test_drift_format.py`, `uv run pytest`, bash suite, `bash scripts/eval.sh` Findings 0 `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`

## Notes

Large deviations were already decided by a human at Gate 3.5; they appear in the roll-up for the record, not for action. `implement-spec.md` has ~4 KB of budget headroom; keep the edit under five lines.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** spec.md → ## 📋 Business Rules (8 Roll-up is report-only)
- **Technical:** sub-specs/technical-spec.md → ## 4

---

## What Was Built

**Implementation Date:** 2026-09-26

### Files Modified

1. **`scripts/drift-format.py`**
   - New `summary --drift-log PATH [--since YYYY-MM-DD]` subcommand: counts DEV entries by severity per `## Story N:` section (sections end at `---`), prints `pass`, one `medium:`/`large:` headline per entry in file order, then `drift-format summary: S small, M medium, L large[ since D]` last.
   - Reuses `_entries` and `_read`. Missing log gives `pass` with zeros; directory or undecodable log gives `unverifiable` / `reason: drift_log_unreadable`; bad `--since` exits 2. Never prints `fail`. [AC-4.1, AC-4.2]
2. **`scripts/tests/test_drift_format.py`** — `DriftSummaryTests` (10) and `DriftSummaryWiringTests` (1). [AC-4.1, AC-4.2, AC-4.3, AC-4.4]
3. **`commands/implement-spec.md`** — Step 4.2 runs `summary --since <startedAt date>`, adds `Drift this run:` plus Medium headlines to the report, and states the roll-up is report-only. [AC-4.3, AC-4.4]

### Implementation Decisions

1. Entries without a canonical severity, or outside a story section, are skipped; `check` owns format validation (DEV-006).
2. Undated sections count only when `--since` is absent.

### Test Results

- `uv run --python 3.9 pytest scripts/tests/test_drift_format.py scripts/tests/test_exit_criteria.py scripts/tests/test_governor_enforcement.py`: 130 passed. `test_eval_drift_format.sh`: 3/3. Full `uv run pytest`, bash suite, and `eval.sh` run once at spec end.
- Live roll-up on this spec's log: `5 small, 0 medium, 0 large since 2026-09-26`.
- Gate 3 evaluator: PASS, Overall Drift Small. Residual (minor): lowercase severities are skipped silently; Step 4.2 does not define the report line when `summary` is `unverifiable`. `review-override.py`: the same foreign-token `dangling_reference` as Story 1. `docs-check`: unverifiable (no public exports).
