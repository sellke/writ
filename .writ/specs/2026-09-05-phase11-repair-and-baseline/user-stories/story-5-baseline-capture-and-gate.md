# Story 5: Baseline Capture and Gate — Eight Fable 5.1 Runs, One Committed JSON, check_pipeline_baseline

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2, Story 4

## User Story

**As a** Writ maintainer who needs the number that every Stage 2 cut will be judged against
**I want to** run the replay pipeline eight times at Claude Fable 5.1, commit the resulting baseline JSON, and have `eval.sh` refuse any baseline file that breaks the schema
**So that** the first `compare` after a Stage 2 cut decides keep-or-revert on a per-story, per-metric delta instead of an opinion, and the file it compares against can be trusted without a human reading it

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [ ] Given Story 3's `selection` block names four yuss.app stories and `claude` plus `ANTHROPIC_API_KEY` are available, when `python3 scripts/pipeline-baseline.py run --model claude-fable-5-1 --runs 2` runs to completion, then `.writ/eval/baselines/2026-MM-DD-claude-fable-5-1.json` is committed with `schema: pipeline-baseline-v1`, `model: claude-fable-5-1`, a `criteria` block, and exactly eight run records (two per story) each carrying every metric field — exit-criteria verdict, tests passed/total, ac-trace findings, input/output/cache-read tokens, wall-clock, interrupts, review iterations, and reported-vs-rederived verdicts for each gate — and the story's What Was Built records total tokens and the dollar estimate across the eight runs `[AC-5.1]`
- [ ] Given no file matches `.writ/eval/baselines/*.json`, when `bash scripts/eval.sh --check=pipeline-baseline` runs, then it emits one `add_note` line naming the missing directory and the command that creates a baseline, and reports zero findings `[AC-5.2]`
- [ ] Given a baseline file that violates the schema in any one way — wrong or missing `schema`, missing `model`, missing `criteria`, `selection` with a story count other than four, `runs` count not equal to `runs_per_story × 4`, a run record missing a metric field, a string value longer than 200 characters, or a string value matching the source-code, transcript, or API-key heuristics — when `bash scripts/eval.sh --check=pipeline-baseline` runs, then it blocks with one `add_finding` per violation naming the file and the offending field path, and a file with none of these violations passes with zero findings `[AC-5.3]`
- [ ] Given two baseline files whose `selection` blocks name the same four stories, when `python3 scripts/pipeline-baseline.py compare <a> <b>` runs, then it prints one row per story per metric with `<a>` value, `<b>` value, and delta, taking the per-story median when the files' `runs_per_story` differ, and exits 0 `[AC-5.4]`
- [ ] Given two baseline files whose `selection` blocks differ in any story path or parent SHA, when `compare <a> <b>` runs, then it prints nothing but a refusal naming the first differing story and exits non-zero `[AC-5.5]`

## Implementation Tasks

- [ ] 5.1 Write tests first: pytest cases in `scripts/tests/test_pipeline_baseline.py` for `validate` (one fixture per violation class listed in the third criterion, plus one clean eight-record fixture) and `compare` (identical selections with equal and unequal `runs_per_story`; mismatched selection), and a bash fixture test in `scripts/tests/` that runs `check_pipeline_baseline` against an empty `baselines/` dir, the clean fixture, and a broken fixture, following the `check_exit_criteria()` fixture-suite shape `[AC-5.2, AC-5.3, AC-5.4, AC-5.5]`
- [ ] 5.2 Add `validate <file>` to `scripts/pipeline-baseline.py`: load JSON, check `schema == "pipeline-baseline-v1"`, `model` present and equal to the model segment of the filename, `criteria` present, `len(selection.stories) == 4`, `len(runs) == runs_per_story * 4`, every run record carries the full metric field list (shared with `run`/`ingest` as one module-level constant so the writer and the validator cannot drift), no string value over 200 characters, and no string value matching the leak heuristics (`sk-ant-` prefix, `import `/`def `/`function ` line starts, `Human:`/`Assistant:` turn markers); print one `path: reason` line per violation and exit 1, else exit 0 `[AC-5.3]`
- [ ] 5.3 Add `check_pipeline_baseline()` to `scripts/eval.sh` next to `check_exit_criteria()` and register `pipeline-baseline` in `CHECKS`: when `.writ/eval/baselines/*.json` matches nothing, `add_note` once and return; otherwise shell out to `python3 scripts/pipeline-baseline.py validate <file>` for each file and turn every output line into an `add_finding` `[AC-5.2, AC-5.3]`
- [ ] 5.4 Add `compare <a> <b>` to `scripts/pipeline-baseline.py`: refuse (non-zero exit, name the first differing story) unless both `selection` blocks name identical story paths and parent SHAs; otherwise aggregate each numeric metric per story (median across that file's runs), and print an aligned table of story × metric with `a`, `b`, and `delta` columns, with the exit-criteria verdict shown as pass count over run count `[AC-5.4, AC-5.5]`
- [ ] 5.5 Run `python3 scripts/pipeline-baseline.py run --model claude-fable-5-1 --runs 2` to completion outside the sandbox; on a `status: timeout` or crashed (story, n) pair, re-run once via the resume path (which skips completed pairs) and keep whatever record results; run `bash scripts/eval.sh --check=pipeline-baseline` until it passes; commit `.writ/eval/baselines/2026-MM-DD-claude-fable-5-1.json` `[AC-5.1]`
- [ ] 5.6 Sum `input_tokens`, `output_tokens`, and `cache_read_input_tokens` across the eight records, compute the dollar estimate at $10/MTok input, $50/MTok output, $0.25/MTok cache read, and record both in this story's What Was Built together with any timeout or retry deviations; append the Business Rule 8 line to `.writ/decision-log.md` `[AC-5.1]`
- [ ] 5.7 Verify every criterion: `uv run --python 3.9 pytest scripts/tests/test_pipeline_baseline.py` green, the bash fixture test green, `bash scripts/eval.sh` at `Findings: 0` with the committed baseline present, and `compare <file> <file>` on the committed baseline printing all-zero deltas `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

## Notes

**Cost.** Eight full `/implement-story` runs at Fable 5.1 default-high effort dominate the cost of this spec (spec.md → ⚠️ Technical Concerns, second bullet). Pricing per Anthropic's September 2026 model docs: $10/MTok input, $50/MTok output, $0.25/MTok cache read. Per-run consumption is unknown until Story 4's smoke run reports it; do not commit to a figure before that record exists. The formula in task 5.6 is the only estimate this story asserts. Record the per-run and total numbers in What Was Built so Stage 2 knows the price before repeating the measurement.

**If a run times out or a record is not clean.** Story 4 flushes each record after its run and its resume path skips completed (story, n) pairs, so a crash or timeout costs one run, not eight. A `status: timeout` record is re-run once; if the retry also fails, keep the record with its status — the eight-record count is a schema requirement and a timeout is a measurement, not a defect to hide. A run whose exit-criteria verdict is FAIL, whose tests fail, or whose reported verdict disagrees with the re-derived one is a *clean* record: it carries every field and is exactly the data the baseline exists to capture. "Not clean" means only a missing field or a leak-heuristic hit. Every deviation from a straight eight-of-eight first-pass run goes in What Was Built.

**Why the check notes when absent.** `eval.sh` ships to installed projects after `/release` (Business Rule 7), and those projects have no `.writ/eval/baselines/` and no reason to. Blocking on absence would make the Writ quality gate fail everywhere except this repository. The gate exists to reject a *malformed* baseline, not to demand one; the demand is Goal Card DONE WHEN 2, which is a spec-level success criterion, not an eval check. Same posture as the existing budget tripwire at `eval.sh:446`, which notes rather than blocks on a condition the project may legitimately be in.

**Validator lives in Python, not bash.** Field-list validation and the leak heuristics belong beside the code that writes the records so writer and validator share one constant. `eval.sh` only shells out and relays lines as findings — the same split `check_exit_criteria()` and `check_quality_config_audit()` already use.

**Leak heuristics are heuristics.** The 200-character cap catches most transcript or source leakage; the prefix and turn-marker patterns catch the short cases. A determined false negative is possible; the fixtures in 5.1 pin the patterns that are checked, and Business Rule 3 is the standard the record is held to.

**Integration points.** Story 2 supplies validated token counting (`token_method_validated: true`) that the dollar estimate assumes. Story 3 defines the `selection` block whose shape `compare` matches on and whose story count `validate` asserts. Story 4 defines the run record — the metric field list `validate` checks must be the one `run`/`ingest` write, so land the constant in Story 4's module and import it, or move it once in this story with Story 4's tests still green. Business Rule 5's per-gate reported/rederived pair is a required field on every record, `rederived: null` where no script exists.

**Fable 5.1 only.** `run --model` accepts any Claude model ID, but this story commits exactly one file, `2026-MM-DD-claude-fable-5-1.json` (Business Rules 4 and 9). An Astra file is Stage 2 work under the same schema.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [spec.md → ## 🎯 Experience Design → Error experience — "No `ANTHROPIC_API_KEY`" (run refuses to start), "`claude` binary missing" (stops before any checkout); spec.md → ## 🎯 Experience Design → State catalog — "`compare` with mismatched selections (refused)", "`run` in progress (partial records flushed after each run)"]
- **Shadow paths:** [spec.md → ## 🎯 Experience Design → Happy path — steps (2) `run --runs 2`, (3) `eval.sh --check=pipeline-baseline`, (4) commit; spec.md → ## 🎯 Experience Design → Entry point — `compare <a> <b>`; spec-lite.md → ## For Testing Agents → Shadow Paths to Verify — "Happy path", "Upstream error" (headless timeout → `status: timeout`, continue), Edge Cases — "`compare` across different `runs_per_story` → per-story medians"]
- **Business rules:** [spec.md → ## 📋 Business Rules → 3 (JSON carries IDs, SHAs, metrics, criteria — never source, transcript, or keys), 4 (one model per file; `<date>-<model-id>.json` with `model` in header), 5 (reported verdict beside re-derived verdict per gate; `rederived: null` without a script), 8 (decision-log line on closing commit), 9 (Fable 5.1 only)]
- **Experience:** [spec.md → ## 🎯 Experience Design → Moment of truth — first `compare` after a Stage 2 cut shows exit-criteria pass rate, tokens, interrupts side by side; spec.md → ## 🎯 Experience Design → Feedback model — one stdout line per story per run, JSON is the durable record]
- **Requirements:** [spec.md → ## Detailed Requirements → ### Story 5 — Baseline capture and gate; spec.md → ## Specification Contract → Success Criteria — DONE WHEN 2 verbatim; spec.md → ## ⚠️ Technical Concerns — second bullet (cost); spec.md → ## 💡 Recommendations — second bullet (criteria in the JSON)]
- **Codebase:** [`scripts/eval.sh` — `CHECKS=(...)` at line 19, `add_note` at line 190, `check_exit_criteria()` at line 3206 and `check_quality_config_audit()` at line 3380 as the fixture-suite shape to imitate; `scripts/pipeline-baseline.py` — `select`/`run`/`ingest` from Stories 3–4; `.writ/eval/baselines/` — new, committed, not under gitignored `.writ/state/`; `scripts/tests/` — pytest + bash fixtures, Python floor 3.9]
