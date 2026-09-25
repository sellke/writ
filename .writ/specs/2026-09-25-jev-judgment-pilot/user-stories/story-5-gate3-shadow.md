# Story 5: Gate 3 Shadow Judgment and Agreement Report

> **Status:** Completed ✅
> **Commit:** c8e42e7832834f26f48763b2e581a9d5b915a2be
> **Priority:** Medium
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer gathering evidence for conditional evaluator spawning
**I want to** run shadow judgment on every evaluated story, comparing Jev's per-criterion assessment against the evaluator's verdict without changing gate outcomes
**So that** I can decide later whether the evaluator spawn can be made conditional based on the shadow-report promotion rule

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [x] Given `ac-shadow --story FILE --tests-output FILE --diff FILE --review-output FILE [--log PATH]`, when it runs on Python 3.9 stdlib, then it asks one Noul per criterion ("is this criterion satisfied by the recorded test output and diff?") in a single request; appends one JSONL row to `.writ/state/jev-shadow.jsonl` (created if missing) with story, model, per-criterion `p`, evaluator verdict, and agreement; the diff slice excludes paths matching `.env*`, `*.pem`, `*.key`, `*secret*`, and `*credential*`; and the summary reports `excluded_paths=N` `[AC-5.1]`
- [x] Given `agents/evaluator-agent.md`'s Acceptance Criteria checklist lines (Output Format and the On PASS/On FAIL examples), when `ac-shadow` runs, then every line in those sections gains a trailing `[AC-N.M]` tag; `ac-shadow` parses evaluator verdicts by tag; and review output with no tags gives `unverifiable no_evaluator_ids` and no row is written `[AC-5.2]`
- [x] Given `commands/implement-story.md` Gate 3 after the `review-override.py` block, when `jev-judge.py status` is `pass`, then one line runs `ac-shadow --story <story-file> --tests-output <tests-output> --diff <diff> --review-output <review-output>`; any verdict is a story-report note; it never changes PASS/FAIL/PAUSE; it never counts toward the review loop; and it never marks the story DEGRADED `[AC-5.3]`
- [x] Given `shadow-report [--log PATH]`, when it reads a log of shadow rows, then it prints evaluated-story count, per-criterion agreement %, and false-pass count (Jev p ≥ `ac_shadow.satisfied` where the evaluator said not satisfied); the verdict is `pass promotion_met` only when there are ≥30 stories, 0 false passes, and ≥95% agreement; otherwise `unverifiable promotion_not_met`; it reads only the log, with no network `[AC-5.4]`
- [x] Given pytest fixtures and wiring tests, when `uv run --python 3.9 pytest scripts/tests/test_jev_judge.py` and the bash wiring test run, then the replay-mode pytest covers a row written, `no_evaluator_ids`, secret-path exclusion, and promotion met/not met on synthetic logs; a bash wiring test pins the `implement-story` Gate 3 line and the evaluator `[AC-N.M]` tag format; and `bash scripts/eval.sh` ends with Findings 0 `[AC-5.5]`

## Implementation Tasks

- [x] 5.1 Write `scripts/tests/test_jev_judge.py` pytest fixtures for `ac-shadow`: a row written with model, per-criterion `p`, agreement; `no_evaluator_ids` (no tags in review output); secret-path exclusion count; promotion met/not met on synthetic logs; assert JSONL row format and `shadow-report` output `[AC-5.1, AC-5.2, AC-5.4, AC-5.5]`
- [x] 5.2 Add `ac-shadow` subcommand to `scripts/jev-judge.py`: accept `--story FILE --tests-output FILE --diff FILE --review-output FILE [--log PATH]`; diff slice excludes secret-path patterns with count; ask one Noul per criterion; parse evaluator verdict by `[AC-N.M]` tag; append JSONL row with story, model, per-criterion `p`, evaluator verdict, agreement; create `.writ/state/` if missing; return verdict per technical-spec §1 `[AC-5.1, AC-5.2]`
- [x] 5.3 Add `shadow-report` subcommand to `scripts/jev-judge.py`: read log path (default `.writ/state/jev-shadow.jsonl`); print story count, per-criterion agreement %, false-pass count; apply promotion rule (≥30 stories, zero false passes, ≥95% agreement); return `pass promotion_met` or `unverifiable promotion_not_met`; no network `[AC-5.4]`
- [x] 5.4 Append `[AC-N.M]` tag suffix to `agents/evaluator-agent.md`: every checklist line in "Output Format" (Acceptance Criteria checklist and Recorded Test Results) and "On PASS/On FAIL" examples gains trailing `[AC-N.M]`; `ac-shadow` parses by this tag; lines without tags give `no_evaluator_ids` `[AC-5.2]`
- [x] 5.5 Add one line to `/implement-story` Gate 3 after `review-override.py` block: when `jev-judge.py status` is `pass`, run `ac-shadow` with story file, test output, diff, and review output; verdict is a note only; never changes gate outcomes; never counts toward review loop; never marks story DEGRADED `[AC-5.3]`
- [x] 5.6 Add `test_eval_jev_shadow.sh` to `scripts/tests/`: bash wiring test pins the `implement-story` Gate 3 `ac-shadow` line and evaluator `[AC-N.M]` tag format; replay-mode `ac-shadow` on fixture story; assert row written and summary format `[AC-5.3, AC-5.5]`
- [x] 5.7 Verify acceptance criteria: `uv run --python 3.9 pytest scripts/tests/test_jev_judge.py::test_ac_shadow*` green; `bash scripts/tests/test_eval_jev_shadow.sh` green; `bash scripts/eval.sh` ends with Findings 0; confirm secret-path exclusion, promotion rule, no network in eval; closing commit appends `{date} jev-pilot: {what changed and why}` to `.writ/decision-log.md` `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

## Notes

**Technical considerations.** `ac-shadow` mirrors the Stage 2b helper family (argparse subcommand, one verdict line, `reason:` lines, summary last). Diff slice is post-Gate-2.5 output; secret-path exclusion counts and names in output. Evaluator lines lacking `[AC-N.M]` tags (older agent file) → `no_evaluator_ids`, shadow skipped, Gate 3 unaffected. Replay transport for tests via `WRIT_JEV_REPLAY`. Promotion rule: ≥30 stories, zero false passes (Jev p ≥ 0.9 where evaluator said not satisfied), ≥95% per-criterion agreement. Shadow rows are silent in story report except one note line; no friction signal (ADR-025).

**Risks.** Tag format is new; parse defensively and test the capture. False-pass count is the key metric for the promotion decision — over-counting is a false alarm. Agreement % must be clear (per-criterion sum / total evaluated criteria). The evaluator-agent-md edit is minimal: tag suffixes only, no reformat.

**Integration.** Story 2 (client transport) must ship first; this story reads the evaluator output format as established. `/implement-story` Gate 3 wiring is one conditional line. No new story dependencies beyond Story 2. No edits to `commands/create-spec.md`, `commands/verify-spec.md`, or `/implement-story` outside Gate 3.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [ac-shadow --story, ac-shadow --tests-output --diff, Shadow parse, Shadow log append, promotion rule]
- **Business rules:** [Secret-path exclusion (BR 7), Promotion rule (BR 8), Advisory only (BR 4), Stdlib only (BR 9), Decision log (BR 10)]
- **Shadow paths:** [spec.md → Gate 3 shadow (Story 5), technical-spec §5 (Shadow parse, Shadow log append rows), technical-spec §7 (evaluator lines lack IDs, `.env.local` in diff)]

---

## What Was Built

**Implementation Date:** 2026-09-25

### Files Created

1. **`scripts/tests/test_jev_shadow_hooks.sh`**
   - Pins the Gate 3 shadow line, and checks that the lean sibling is untouched.
   - Pins the `[AC-N.M]` tag rule in `agents/evaluator-agent.md` (examples included) and `claude-code/agents/writ-evaluator.md`.
   - Runs `ac-shadow` and `shadow-report` in replay mode. [AC-5.2, AC-5.3, AC-5.5]
2. **`scripts/tests/fixtures/jev-replay/ac-shadow/`**
   - A synthetic story, test output, review, and a diff containing `.env.local` and `tls.key` blocks.
   - Plus one synthetic recording. [AC-5.1, AC-5.5]

### Files Modified

1. **`scripts/jev-judge.py`**
   - `ac-shadow` asks one Noul per criterion, keyed by AC ID, in a single request.
   - It slices the diff with secret-path exclusion, and a fail-closed guard (`secret_path_unparsed`) stops anything the slicer can't place.
   - It parses tagged evaluator verdicts and appends one JSONL row to `.writ/state/jev-shadow.jsonl`.
   - `shadow-report` applies the promotion rule: ≥30 stories, 0 false passes, ≥95% agreement. [AC-5.1, AC-5.2, AC-5.4]
2. **`agents/evaluator-agent.md`**
   - Checklist lines now end with an `[AC-N.M]` tag.
   - The On PASS lines are tagged, and On FAIL gains a tagged checklist. [AC-5.2]
3. **`claude-code/agents/writ-evaluator.md`** — same tag rule; this is Claude Code's loadable evaluator (DEV-023). [AC-5.2]
4. **`commands/implement-story.md`**
   - Adds one Gate 3 "Jev shadow (opt-in)" paragraph after review-override, using the targeted test run.
   - The result is a note only. It never changes the verdict, the review loop, or DEGRADED. [AC-5.3]
5. **`scripts/tests/test_jev_judge.py`** — 87 new tests. [AC-5.5]
6. **`scripts/tests/test_governor_enforcement.py`** and **`scripts/tests/test_lean_commands.py`**
   - implement-story ratchet: 9103→9656.
   - SHA re-pin.
7. **`scripts/tests/fixtures/jev-replay/README.md`** and **`.writ/decision-log.md`**.

### Implementation Decisions

1. Criteria are keyed by AC ID, not list position, because Jev is weak at indirection.
2. After the evaluator reproduced two leaking diff shapes, secret-path exclusion was made fail-closed (DEV-021).
3. A story's shadow row is dropped rather than truncated when state is over budget, and the summary names `state_too_large`.

### Test Results

- Full `uv run --python 3.9 pytest -q`: 1710 passed, 1 skipped.
- All bash tests pass.
- `eval.sh`: Findings 0.
- Coverage of `scripts/jev-judge.py`: 98%.
- Live smoke (vercel-gateway, synthetic 3-criterion story): p = 0.98 / 0.98 / 0.03. All three agree with the evaluator at 0.9.
- Mutation checks: removing the guard fails 6 tests; splitting only on `diff --git` fails 3; removing the false-pass rule fails.
- ⚠️ `test-integrity.py authenticity` reports `test_imports_no_source`. This is the known false positive. Not DEGRADED.

### Review Outcome

**Result:** PASS — 1 iteration. A Minor security residual (the diff-slice leak) was fixed before commit.

**Drift:** Small (DEV-020 to DEV-023).
