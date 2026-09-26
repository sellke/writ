# Story 4: Drift Roll-up at Spec End

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** Writ maintainer running `/implement-spec`
**I want to** one line at spec end counting the drift logged during the run, with the Medium and Large headlines
**So that** Medium warnings from individual stories add up somewhere I will read instead of scrolling past

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.4

- [ ] Given `drift-format.py summary --drift-log L [--since D]`, when L has story sections with `> Run:` dates and DEV entries, then it prints `pass`, one `medium:` or `large:` line per Medium/Large DEV (`DEV-NNN title (Story N)`), and a summary line `S small, M medium, L large [since D]` last; with `--since`, only sections dated on or after D count `[AC-4.1]`
- [ ] Given a missing log, when `summary` runs, then it prints `pass` with zero counts; given an unreadable log, then `unverifiable` with `reason: drift_log_unreadable`; given a malformed `--since`, then exit 2 `[AC-4.2]`
- [ ] Given `commands/implement-spec.md` Step 4.2, when the spec run completes, then it runs `summary` with `--since` set to the execution state's start date and adds a `Drift this run:` line plus the Medium headlines to the report `[AC-4.3]`
- [ ] Given any roll-up output, when the report is built, then it never changes the checker verdict, the banner, or any story status; and a wiring test pins the Step 4.2 invocation `[AC-4.4]`

## Implementation Tasks

- [ ] 4.1 Write failing tests in `scripts/tests/test_drift_format.py` for counts by severity, headline lines, `--since` filtering, sections with no Run date, missing and unreadable logs, and bad `--since` `[AC-4.1, AC-4.2]`
- [ ] 4.2 Add the `summary` subcommand to `scripts/drift-format.py` per technical-spec §4, reusing the existing entry parser; update the docstring `[AC-4.1, AC-4.2]`
- [ ] 4.3 Write a failing wiring test pinning the Step 4.2 `summary` invocation and its report-only rule `[AC-4.3, AC-4.4]`
- [ ] 4.4 Edit `commands/implement-spec.md` Step 4.2: invocation, `Drift this run:` report line, report-only sentence `[AC-4.3, AC-4.4]`
- [ ] 4.5 Verify: `uv run --python 3.9 pytest scripts/tests/test_drift_format.py`, `uv run pytest`, bash suite, `bash scripts/eval.sh` Findings 0 `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`

## Notes

Large deviations were already decided by a human at Gate 3.5; they appear in the roll-up for the record, not for action. `implement-spec.md` has ~4 KB of budget headroom; keep the edit under five lines.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** spec.md → ## 📋 Business Rules (8 Roll-up is report-only)
- **Technical:** sub-specs/technical-spec.md → ## 4
