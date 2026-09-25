# Story 4: Calibration Fixtures and Thresholds

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 3

## User Story

**As a** Writ maintainer deciding whether Jev's findings can be trusted
**I want to** grow the labeled fixture set to ≥20 stories with balanced classes, add `calibrate --fixtures` and `--write-thresholds`, and record per-class precision/recall plus chosen thresholds
**So that** we can measure Jev's per-class confidence and calibrate thresholds that give zero false positives on clean fixtures while maximizing recall

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.4

- [ ] Given `scripts/tests/fixtures/spec-analyze/`, when the tree is listed, then it holds ≥20 labeled story fixtures with ≥4 per class (contradiction, gap, ambiguity, clean); the four existing slugs stay unchanged; new fixtures are named `synthetic-*`; every fixture keeps the existing `gold.json` shape; and `test_spec_analyze_precision.py` still passes `[AC-4.1]`
- [ ] Given committed recorded responses in `scripts/tests/fixtures/jev-replay/`, when `calibrate --fixtures DIR` runs, then it scores each recorded Noul `p` against the gold label, computes TP/FP/FN per class, selects the `emit` and `escalate` thresholds that give zero false positives on clean fixtures and then maximum recall, and prints the chosen threshold pair for each judgment type (contradiction, gap, ambiguity) `[AC-4.2]`
- [ ] Given a scored run, when `--write-thresholds` is passed, then `scripts/jev-thresholds.json` is written with `"calibrated": true` and the `backend`, `model`, and `calibrated_on` of the recorded responses; with no recorded responses and no `--live` flag, the verdict is `unverifiable no_live_run` and the thresholds file is not changed; `--live` requires Story 1's provider to be enabled (this repo can use `vercel-gateway` via `AI_GATEWAY_API_KEY`) and records fresh responses into `scripts/tests/fixtures/jev-replay/` `[AC-4.3]`
- [ ] Given the closing commit for Story 4, when `.writ/decision-log.md` is read, then Story 4's What Was Built records the per-class TP/FP/FN table and the chosen `emit`/`escalate` thresholds, or states plainly that no live run happened (`no_live_run`) and that thresholds remain uncalibrated starting values, and the closing commit line reads `{date} jev-pilot: calibrated thresholds from {N} fixtures` or `{date} jev-pilot: no_live_run; thresholds uncalibrated` `[AC-4.4]`

## Implementation Tasks

- [ ] 4.1 Write `scripts/tests/test_jev_calibrate.py` (pytest): ≥20 fixtures exist with ≥4 per class, gold labels have the correct shape, `calibrate --fixtures` can read them, and thresholds can be written `[AC-4.1, AC-4.2, AC-4.3]`
- [ ] 4.2 Author ≥16 new labeled fixtures (synthetic-contradiction-*, synthetic-gap-*, synthetic-ambiguity-*, synthetic-clean-*) under `scripts/tests/fixtures/spec-analyze/`, each with a spec folder, user-stories directory, and gold.json matching the existing shape from Story 3 `[AC-4.1]`
- [ ] 4.3 Implement `calibrate` subcommand in `scripts/jev-judge.py`: read fixtures from `--fixtures DIR`, score recorded responses (from replay) against gold labels, compute TP/FP/FN per judgment type (contradiction, gap, ambiguity), and select thresholds for zero false positives on clean fixtures plus maximum recall `[AC-4.2]`
- [ ] 4.4 Add `--write-thresholds` flag: after a scored run, write `scripts/jev-thresholds.json` with `"calibrated": true` and the chosen thresholds; print `unverifiable no_live_run` with no responses and no `--live`, leaving thresholds unchanged; record fresh responses to replay when `--live` is passed `[AC-4.3]`
- [ ] 4.5 Document in Story 4's What Was Built: list the four per-class precision/recall counts and the chosen thresholds (or the `no_live_run` reason), and append the decision-log line `[AC-4.4]`
- [ ] 4.6 Verify acceptance criteria: ≥20 fixtures with balanced classes exist, `calibrate --fixtures` scores and picks thresholds correctly, `--write-thresholds` updates the JSON, `test_spec_analyze_precision.py` still passes `[AC-4.1, AC-4.2, AC-4.3]`
- [ ] 4.7 Verify all tests pass: `uv run pytest scripts/tests/test_jev_calibrate.py`, `test_spec_analyze_precision.py`, and bash eval checks for calibration; closing commit appends the decision-log line `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`

## Notes

**Technical considerations.** Calibration requires a live Jev API key at implementation time. If unavailable, the story closes with an honest `no_live_run` record; thresholds stay at their conservative starting values, and the provider remains usable but uncalibrated. The calibrate command must not fail on that condition — it must print `unverifiable no_live_run` and exit 0 (Business Rule 2).

**Threshold selection.** The goal is zero false positives on clean fixtures (no contradictions/gaps/ambiguities falsely raised for a clean story) and then maximum recall. This means: for each judgment type, find the lowest `emit` threshold that gives FP=0 on clean, then set `escalate` to maximize TP from the band below.

**Codebase patterns.** Counting, threshold search, and numeric comparison stay in Python code (Technical Spec §1; Jev is weak at these operations). Response confidence comes from `jev-judge.py` as `p` (probability) in the spec-findings JSON (Story 3 output shape). Thresholds are tied to the pinned model ID (Business Rule 5: `jev-1.13.0`).

**Honest caveat.** A live key may not be available at implementation time (Technical Concerns). The story must still close with a plain record of what happened: if `no_live_run`, state it clearly in WWB and the decision log. This prevents silent miscalibration later.

**Fixture realism.** The ≥16 new synthetic fixtures should exercise the four classes realistically: contradictions where two criteria truly conflict, gaps where an edge case is missed, ambiguities where competent implementers could interpret a criterion differently, and clean stories with no issues.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing (`test_jev_calibrate.py`, `test_spec_analyze_precision.py`)
- [ ] Code reviewed
- [ ] Documentation updated (Story 4 What Was Built + decision-log.md)

## Context for Agents

- **Business rules:** [5 (Pinned model where possible; gateway calibrates against alias `typesafe-ai/jev`), 6 (No network in tests or eval: replay only)]
- **Technical Concerns:** [Calibration requires live key at implementation time; without one, record `no_live_run` plainly and leave thresholds uncalibrated]
- **Shadow paths:** [Partial (1 of 5 stories escalated), Happy (all confident), Nil (provider disabled)] — calibrate focuses on fixture scoring, not orchestrator integration
- **Error map rows:** [Build request (State over budget: scored but large fixtures), Parse response (model mismatch: thresholds not applied)]
