# Story 5: Gate 3 Shadow Judgment and Agreement Report

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer gathering evidence for conditional evaluator spawning
**I want to** run shadow judgment on every evaluated story, comparing Jev's per-criterion assessment against the evaluator's verdict without changing gate outcomes
**So that** I can decide later whether the evaluator spawn can be made conditional based on the shadow-report promotion rule

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [ ] Given `ac-shadow --story FILE --tests-output FILE --diff FILE --review-output FILE [--log PATH]`, when it runs on Python 3.9 stdlib, then it asks one Noul per criterion ("is this criterion satisfied by the recorded test output and diff?") in a single request; appends one JSONL row to `.writ/state/jev-shadow.jsonl` (created if missing) with story, model, per-criterion `p`, evaluator verdict, and agreement; the diff slice excludes paths matching `.env*`, `*.pem`, `*.key`, `*secret*`, and `*credential*`; and the summary reports `excluded_paths=N` `[AC-5.1]`
- [ ] Given `agents/evaluator-agent.md`'s Acceptance Criteria checklist lines (Output Format and the On PASS/On FAIL examples), when `ac-shadow` runs, then every line in those sections gains a trailing `[AC-N.M]` tag; `ac-shadow` parses evaluator verdicts by tag; and review output with no tags gives `unverifiable no_evaluator_ids` and no row is written `[AC-5.2]`
- [ ] Given `commands/implement-story.md` Gate 3 after the `review-override.py` block, when `jev-judge.py status` is `pass`, then one line runs `ac-shadow --story <story-file> --tests-output <tests-output> --diff <diff> --review-output <review-output>`; any verdict is a story-report note; it never changes PASS/FAIL/PAUSE; it never counts toward the review loop; and it never marks the story DEGRADED `[AC-5.3]`
- [ ] Given `shadow-report [--log PATH]`, when it reads a log of shadow rows, then it prints evaluated-story count, per-criterion agreement %, and false-pass count (Jev p ≥ `ac_shadow.satisfied` where the evaluator said not satisfied); the verdict is `pass promotion_met` only when there are ≥30 stories, 0 false passes, and ≥95% agreement; otherwise `unverifiable promotion_not_met`; it reads only the log, with no network `[AC-5.4]`
- [ ] Given pytest fixtures and wiring tests, when `uv run --python 3.9 pytest scripts/tests/test_jev_judge.py` and the bash wiring test run, then the replay-mode pytest covers a row written, `no_evaluator_ids`, secret-path exclusion, and promotion met/not met on synthetic logs; a bash wiring test pins the `implement-story` Gate 3 line and the evaluator `[AC-N.M]` tag format; and `bash scripts/eval.sh` ends with Findings 0 `[AC-5.5]`

## Implementation Tasks

- [ ] 5.1 Write `scripts/tests/test_jev_judge.py` pytest fixtures for `ac-shadow`: a row written with model, per-criterion `p`, agreement; `no_evaluator_ids` (no tags in review output); secret-path exclusion count; promotion met/not met on synthetic logs; assert JSONL row format and `shadow-report` output `[AC-5.1, AC-5.2, AC-5.4, AC-5.5]`
- [ ] 5.2 Add `ac-shadow` subcommand to `scripts/jev-judge.py`: accept `--story FILE --tests-output FILE --diff FILE --review-output FILE [--log PATH]`; diff slice excludes secret-path patterns with count; ask one Noul per criterion; parse evaluator verdict by `[AC-N.M]` tag; append JSONL row with story, model, per-criterion `p`, evaluator verdict, agreement; create `.writ/state/` if missing; return verdict per technical-spec §1 `[AC-5.1, AC-5.2]`
- [ ] 5.3 Add `shadow-report` subcommand to `scripts/jev-judge.py`: read log path (default `.writ/state/jev-shadow.jsonl`); print story count, per-criterion agreement %, false-pass count; apply promotion rule (≥30 stories, zero false passes, ≥95% agreement); return `pass promotion_met` or `unverifiable promotion_not_met`; no network `[AC-5.4]`
- [ ] 5.4 Append `[AC-N.M]` tag suffix to `agents/evaluator-agent.md`: every checklist line in "Output Format" (Acceptance Criteria checklist and Recorded Test Results) and "On PASS/On FAIL" examples gains trailing `[AC-N.M]`; `ac-shadow` parses by this tag; lines without tags give `no_evaluator_ids` `[AC-5.2]`
- [ ] 5.5 Add one line to `/implement-story` Gate 3 after `review-override.py` block: when `jev-judge.py status` is `pass`, run `ac-shadow` with story file, test output, diff, and review output; verdict is a note only; never changes gate outcomes; never counts toward review loop; never marks story DEGRADED `[AC-5.3]`
- [ ] 5.6 Add `test_eval_jev_shadow.sh` to `scripts/tests/`: bash wiring test pins the `implement-story` Gate 3 `ac-shadow` line and evaluator `[AC-N.M]` tag format; replay-mode `ac-shadow` on fixture story; assert row written and summary format `[AC-5.3, AC-5.5]`
- [ ] 5.7 Verify acceptance criteria: `uv run --python 3.9 pytest scripts/tests/test_jev_judge.py::test_ac_shadow*` green; `bash scripts/tests/test_eval_jev_shadow.sh` green; `bash scripts/eval.sh` ends with Findings 0; confirm secret-path exclusion, promotion rule, no network in eval; closing commit appends `{date} jev-pilot: {what changed and why}` to `.writ/decision-log.md` `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

## Notes

**Technical considerations.** `ac-shadow` mirrors the Stage 2b helper family (argparse subcommand, one verdict line, `reason:` lines, summary last). Diff slice is post-Gate-2.5 output; secret-path exclusion counts and names in output. Evaluator lines lacking `[AC-N.M]` tags (older agent file) → `no_evaluator_ids`, shadow skipped, Gate 3 unaffected. Replay transport for tests via `WRIT_JEV_REPLAY`. Promotion rule: ≥30 stories, zero false passes (Jev p ≥ 0.9 where evaluator said not satisfied), ≥95% per-criterion agreement. Shadow rows are silent in story report except one note line; no friction signal (ADR-025).

**Risks.** Tag format is new; parse defensively and test the capture. False-pass count is the key metric for the promotion decision — over-counting is a false alarm. Agreement % must be clear (per-criterion sum / total evaluated criteria). The evaluator-agent-md edit is minimal: tag suffixes only, no reformat.

**Integration.** Story 2 (client transport) must ship first; this story reads the evaluator output format as established. `/implement-story` Gate 3 wiring is one conditional line. No new story dependencies beyond Story 2. No edits to `commands/create-spec.md`, `commands/verify-spec.md`, or `/implement-story` outside Gate 3.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [ac-shadow --story, ac-shadow --tests-output --diff, Shadow parse, Shadow log append, promotion rule]
- **Business rules:** [Secret-path exclusion (BR 7), Promotion rule (BR 8), Advisory only (BR 4), Stdlib only (BR 9), Decision log (BR 10)]
- **Shadow paths:** [spec.md → Gate 3 shadow (Story 5), technical-spec §5 (Shadow parse, Shadow log append rows), technical-spec §7 (evaluator lines lack IDs, `.env.local` in diff)]
