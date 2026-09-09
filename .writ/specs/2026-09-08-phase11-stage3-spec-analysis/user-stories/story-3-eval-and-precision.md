# Story 3: Eval Check + Precision Record on Labeled Fixtures

> **Status:** Completed ✅
> **Commit:** d07ac944bb59940a7df194981de8f7a86887f01f
> **Priority:** High
> **Dependencies:** Story 1, Story 2

## User Story

**As a** Writ maintainer who needs a machine check and a written precision number, not another $180 baseline
**I want to** register `spec-analyze` in `scripts/eval.sh` so helper defects count as findings while live-repo analysis verdicts stay notes, and score contradiction / gap / ambiguity / clean against committed gold labels
**So that** `bash scripts/eval.sh` exits 0 after this story even when live Writ specs are unverifiable, precision is written before any later blocking promotion, and we never check out yuss, run an eight-run, or `/revert`

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given `scripts/eval.sh` after this story, when `CHECKS` and function names are read, then `spec-analyze` is listed in `CHECKS=(...)` and `check_spec_analyze()` exists; a missing `scripts/spec-analyze.py` causes `add_finding` (eval fails that check) `[AC-3.1]`
- [x] Given a present helper that exits 2 on usage, when `check_spec_analyze` runs, then it calls `add_finding` and does not treat the refusal as an analysis note `[AC-3.2]`
- [x] Given the live repo (or a fixture whose helper prints `pass`, `fail`, or `unverifiable` with exit 0 or 1), when `bash scripts/eval.sh --check=spec-analyze` runs, then analysis verdicts and reasons are relayed with `add_note` only — not count-blocking — and the check exits 0; live Writ specs may be `unverifiable` without a findings file `[AC-3.3]`
- [x] Given `scripts/tests/fixtures/spec-analyze/`, when the fixture tree is listed, then it contains at least one labeled case each for contradiction, gap, ambiguity, and clean, with gold labels beside the fixtures; directory or story names may reuse Stage 1 yuss slugs (`story-2-event-creation-payment-flow`, `story-3-settlement-view-share-link`, `story-3-fee-sharing-pro-exemption`, `story-4-messaging-migration-quick-split-guard`) or `synthetic-*`; AC text is authored here `[AC-3.4]`
- [x] Given those gold labels, when structural check plus schema-check runs against the labeled JSON (semantic gold is the committed JSON, not a live LLM), then Story 3 What Was Built records `{TP}/{FP}` per class (contradiction, gap, ambiguity, clean) and overall precision, and the closing commit appends `{date} stage-3: spec-analyze.py advisory; hooks after 2.6a + verify-spec; precision {…}` to `.writ/decision-log.md`; no yuss checkout, eight-run, keep-or-revert, or `/revert`; committed baseline JSON is not rewritten `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Write `scripts/tests/test_eval_spec_analyze.sh` in the `test_eval_drift_format.sh` / `test_eval_verdict_provenance.sh` stub-helper shape: `spec-analyze` in `CHECKS`; `check_spec_analyze()` defined; missing helper → `add_finding`; usage exit 2 → `add_finding`; stub `pass` / `fail` / `unverifiable` → report notes, check exit 0 `[AC-3.1, AC-3.2, AC-3.3]`
- [x] 3.2 Write precision assertions (pytest under `scripts/tests/` or a focused bash file) that score structural findings plus schema-check against gold labels for the four classes and fail if a clean fixture trips `unmeasurable_criterion` `[AC-3.4, AC-3.5]`
- [x] 3.3 Add `spec-analyze` to `CHECKS=(...)` and implement `check_spec_analyze()` in `scripts/eval.sh` (additive only; do not revert Stage 2b checks): missing helper / exit 2 → `add_finding`; live-repo `pass` / `fail` / `unverifiable` → `add_note`; invoke Story 1’s `python3 scripts/spec-analyze.py check --spec <live folder>` without requiring `--findings` `[AC-3.1, AC-3.2, AC-3.3]`
- [x] 3.4 Author labeled fixtures under `scripts/tests/fixtures/spec-analyze/` (contradiction, gap, ambiguity, clean) plus sibling gold-label files; reuse Stage 1 slugs where a stand-in exists, otherwise `synthetic-*` `[AC-3.4]`
- [x] 3.5 Run the precision score on the committed labels, append `{TP}/{FP}` per class and overall precision to this story’s What Was Built, and append the `{date} stage-3: … precision {…}` line to `.writ/decision-log.md` `[AC-3.5]`
- [x] 3.6 Verify acceptance criteria: registration and note-vs-finding split match AC-3.1–AC-3.3, four labeled classes exist, WWB + decision-log carry precision, no yuss / eight-run / `/revert` `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
- [x] 3.7 Verify all tests pass: `bash scripts/tests/test_eval_spec_analyze.sh`, the precision assertions, and `bash scripts/eval.sh --check=spec-analyze` (full `eval.sh` still exits 0) `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

**Technical considerations.** Story 1 owns `scripts/spec-analyze.py` and its pytest CLI fixtures. Story 2 owns command hooks. This story only adds an eval check and a fixture-scored precision record. Shared `eval.sh` with Stage 2b: append `spec-analyze`; do not rewrite `check_drift_format` / `check_verdict_provenance` or committed baseline JSON.

**Relay split.** Helper missing and usage exit 2 are helper defects (`add_finding`). Analysis `fail` on the live repo is still advisory (`add_note`) so a structural hit or `unverifiable` without `--findings` cannot fail the quality gate. That differs from `check_drift_format`, which `add_finding`s a printed `fail`.

**Precision scoring.** Semantic gold is the labeled JSON next to each fixture, not a live LLM pass. Prefer under-firing `unmeasurable_criterion`; a miss on a vague fixture is a gap in the precision table, not a script `fail` on a clean fixture.

**Risks.** Treating analysis `fail` like Stage 2b format-check `fail` would make live specs count-blocking and violate Goal Card DONE WHEN line 5. Inventing precision without gold files violates the Precision score shadow path.

**Integration.** Depends on Story 1’s CLI (exit 0/1/2, verdict lines) and Story 2’s hooks existing so the decision-log line can honestly name “hooks after 2.6a + verify-spec.” No keep-or-revert gate; no `/revert`.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [`eval.sh` live repo, Helper missing]
- **Shadow paths:** [Precision score]
- **Business rules:** [Advisory for one release, No yuss checkout, no eight-run, Decision log, Shared `eval.sh`]
- **Experience:** [Feedback model (analysis via `add_note`; helper defect via `add_finding`), State catalog (eval check registered / precision recorded / still advisory), Happy path (step 6 — Story 3 records precision)]

---

## What Was Built

**Implementation Date:** 2026-09-08

### Files Created

1. **`scripts/tests/test_eval_spec_analyze.sh`** — missing helper / exit 2 → finding; analysis fail → note, check exit 0. [AC-3.1, AC-3.2, AC-3.3]
2. **`scripts/tests/test_spec_analyze_precision.py`** — gold-label score. [AC-3.4, AC-3.5]
3. **`scripts/tests/fixtures/spec-analyze/`** — four labeled cases named after Stage 1 yuss slugs (contradiction, gap, ambiguity, clean).

### Files Modified

- **`scripts/eval.sh`** — `spec-analyze` in `CHECKS`; `check_spec_analyze()` notes analysis verdicts; findings only for missing helper / usage.

### Implementation Decisions

1. **Analysis `fail` is `add_note`.** Unlike `check_drift_format`, a live-spec structural hit must not fail eval.
2. **Precision is schema + structural vs gold**, not a live LLM. Semantic gold is the committed findings array.
3. **Fixture stories carry no `AC-n.m` tokens.** Stand-in AC text must not be scanned as citations against this spec.

### Test Results

- Precision: contradiction 1/0, gap 1/0, ambiguity 1/0, clean 1/0; overall **4 TP / 0 FP**
- `bash scripts/tests/test_eval_spec_analyze.sh` green
- `bash scripts/eval.sh --check=spec-analyze` Findings 0 (live spec `unverifiable` / `no_findings`)
- No yuss checkout, eight-run, or `/revert`

### Review Outcome

**Result:** PASS — 1 iteration. Drift: None.

Gate 3 `review-override.py` printed `fail` / `dangling_reference` for `AC-3.6`, `AC-3.7`, `AC-3.9` cited only in `scripts/tests/test_ac_trace.py` fixture strings. Those IDs are not this spec’s criteria and are not introduced by this story. Recoding this story cannot clear them without breaking ac-trace’s own tests. Residual architecture/taste: none.
