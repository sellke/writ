# Story 5: Baseline Re-run and Keep-or-Revert — Eight Fable 5.1 Runs on the Pruned Base, Compared Against Stage 1

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 3, Story 4

## User Story

**As a** Writ maintainer who needs the cut judged by a number, not an opinion
**I want to** replay the same eight Fable 5.1 runs against the pruned base and compare the result to the Stage 1 baseline
**So that** the ~18 KB cut is kept only because the pass rate held, and reverted mechanically if it did not

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [ ] Given `.writ/eval/baselines/2026-09-06-claude-fable-5-1.json`, when the new file `.writ/eval/baselines/<date>-claude-fable-5-1.json` is built by copying its `schema`, `model`, `yuss_head`, `criteria`, `selection`, `excluded`, and `rejection_tally` with `generated_at` set to now, `runs_per_story: null`, and `runs: []`, then a one-line Python comparison of the two files' `selection` and `criteria` blocks reports byte-identical equality, recorded in What Was Built `[AC-5.1]`
- [ ] Given the new baseline file and a `claude` CLI authenticated as Fable 5.1, when `python3 scripts/pipeline-baseline.py run --baseline <new> --yuss ~/Projects/yuss --model claude-fable-5-1 --runs 2 --keep --tmp-root <scratch>` runs to completion outside the sandbox under `nohup` (a bare foreground run risks the session teardown that cost Stage 1 a run), then the file carries exactly eight run records and `python3 scripts/pipeline-baseline.py validate <new>` exits 0; and `bash scripts/eval.sh --check=pipeline-baseline` runs, then it reports zero findings `[AC-5.2]`
- [ ] Given the Stage 1 baseline and the new baseline share an identical `selection` block, when `python3 scripts/pipeline-baseline.py compare .writ/eval/baselines/2026-09-06-claude-fable-5-1.json <new>` runs, then it does not refuse, prints four rows (one per story) with an `exit_criteria` column, and exits 0 `[AC-5.3]`
- [ ] Given the `compare` output, when every `exit_criteria` row reads `2/2`, then the cut is kept and What Was Built records token totals, wall clock, the `cost_usd` sum, and the compare table; given any row reads less than `2/2`, when the failed (story, n) pair is re-run once via the resume path and `compare` still shows a shortfall, then `/revert` is run on Story 2's and Story 3's completion commits and What Was Built records the same totals plus the revert outcome, and either way the decision-log line names keep or revert with the numbers and the new baseline JSON is committed `[AC-5.4, AC-5.5]`

## Implementation Tasks

- [ ] 5.1 Build `.writ/eval/baselines/<date>-claude-fable-5-1.json` from Stage 1's `schema`, `model`, `yuss_head`, `criteria`, `selection`, `excluded`, `rejection_tally`, with `generated_at` now, `runs_per_story: null`, `runs: []`; run a one-line Python check that the new and Stage 1 `selection` and `criteria` blocks are byte-identical and record the result in What Was Built `[AC-5.1]`
- [ ] 5.2 Launch `python3 scripts/pipeline-baseline.py run --baseline <new> --yuss ~/Projects/yuss --model claude-fable-5-1 --runs 2 --keep --tmp-root <scratch>` outside the sandbox under `nohup` (use `python3 -u` or an equivalent to avoid stdout buffering hiding progress), and monitor until eight records are flushed `[AC-5.2]`
- [ ] 5.3 Run `python3 scripts/pipeline-baseline.py validate <new>` to exit 0 and `bash scripts/eval.sh --check=pipeline-baseline` to Findings: 0 `[AC-5.2]`
- [ ] 5.4 Run `python3 scripts/pipeline-baseline.py compare .writ/eval/baselines/2026-09-06-claude-fable-5-1.json <new>`; if every `exit_criteria` row reads `2/2`, keep the cut; otherwise re-run the failed (story, n) pair once via the resume path, compare again, and if still short of `2/2` on any row, run `/revert` against Story 2's and Story 3's completion commits `[AC-5.3, AC-5.4, AC-5.5]`
- [ ] 5.5 Record in What Was Built: summed `input_tokens`/`output_tokens`/`cache_read_input_tokens`, wall clock, the `cost_usd` sum across the eight records, the full `compare` table, and any retry or revert; append the decision-log line stating keep or revert and the numbers `[AC-5.4, AC-5.5]`
- [ ] 5.6 Verify every acceptance criterion — selection/criteria equality, `validate` exit 0, `eval.sh --check=pipeline-baseline` Findings: 0, `compare` printing four rows, and the keep-or-revert record — then commit the new baseline JSON regardless of the outcome `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

## Notes

**Technical.** `nohup` because the driving Claude Code session can be torn down mid-run — Stage 1 lost run 6 (fee-sharing, run 2) exactly this way, at about 17:25 UTC, 203 transcript lines in, with the cost of the lost partial run unrecorded. Prefer `python3 -u` (or set `PYTHONUNBUFFERED=1`) so progress lines aren't silently buffered until process exit; the baseline JSON file itself, flushed per run, is the durable progress record regardless of what stdout shows.

**Risks.** 8/8 with no tolerance — Business Rule 10 allows no partial keep. Stage 1 recorded one `DEGRADED` self-report (settlement-view run 1) whose re-derived predicates still scored `met`; that counts as a pass because the `compare` column judged is `exit_criteria` (pass count over run count from the re-derived verdict), never the model's self-report. Cache-read token variance was 59% between identical Stage 1 runs — expect similar spread here; it does not affect the keep/revert decision, only the recorded totals.

**Cost.** Stage 1's eight runs cost about $190 in driver-reported `cost_usd` and 5.5 hours wall clock (mean $23.45/run, range $16.69–$29.66). This story budgets the same for the primary eight runs, plus up to about $50 for one retried pair in the worst case. The task-formula token estimate ($10/$50/$0.25 per MTok) understated Stage 1's driver-reported cost by 3.6×; `cost_usd` per record, not the formula, is the price of record.

**Integration.** Stories 2 and 3 are the exact revert range if the pruned base fails the gate — their commits carry the ledger's rows, so reverting them restores the ledger to its post-Story-1 state automatically. Story 4's gate-verification markers are untouched by a revert of Stories 2–3 and are not part of the range. ADR-026 and the new baseline JSON survive a revert either way — Business Rule 11 keeps this story from merging, opening a PR, or releasing regardless of outcome.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [spec.md → ## 🎯 Experience Design → Error experience — "Baseline re-run below 8/8: Story 5 re-runs the failed pair once via the resume path; if it still fails, the story reverts Stories 2–3 as one commit range and records the compare table under What Was Built; the ledger and the ADR survive the revert."]
- **Shadow paths:** [spec.md → ## 🎯 Experience Design → Happy path — step (5) "Story 5 runs the eight replays and `compare` prints per-story deltas with exit criteria 2/2 on every row"; spec.md → ## 🎯 Experience Design → State catalog — "re-run in progress (records flushed per run) / kept or reverted"; spec.md → ## 🎯 Experience Design → Moment of truth — the `compare` table after Story 5]
- **Business rules:** [spec.md → ## 📋 Business Rules → 9 (Stage 1 selection reused verbatim so `compare` never refuses), 10 (keep-or-revert is mechanical: 2/2 on all four rows or revert, no partial keep), 11 (ADR-013 holds: nothing merges, opens a PR, or releases), 12 (decision-log line format `{date} stage-2: {what changed and why}`)]
- **Experience:** [spec.md → ## 🎯 Experience Design → Feedback model — `compare` prints per-story per-metric rows with `exit_criteria` as pass count over run count]
- **Requirements:** [spec.md → ## Detailed Requirements → ### Story 5 — Baseline re-run and keep-or-revert; technical-spec.md → ## 6. Re-run file and compare (Story 5) — file construction, run/validate/compare commands, revert path via `/revert` and Stage 1's `revert-resolve.py`; technical-spec.md → ## 7. Tests — "Story 5 has no new unit tests; its verification is the compare table and `validate`."]
- **Codebase:** [`scripts/pipeline-baseline.py` — `run` (resume path skips recorded pairs, records flushed per run, `--keep`, strips `CLAUDECODE` from the child env), `validate`, `compare` (refuses on differing `selection`, per-story medians, `exit_criteria` as pass count over run count); `.writ/eval/baselines/2026-09-06-claude-fable-5-1.json` — Stage 1's file to copy the header from; `.writ/specs/2026-09-05-phase11-repair-and-baseline/user-stories/story-5-baseline-capture-and-gate.md` → What Was Built — per-run table, dollar-estimate-vs-`cost_usd` gap, the run-6 teardown deviation, the fee-sharing original-tests-failed-to-run deviation; `scripts/revert-resolve.py` and `commands/revert.md` — resolve a story's completion commits for `/revert`]
