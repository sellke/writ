# Story 5: Baseline Re-run and Keep-or-Revert — Eight Fable 5.1 Runs on the Pruned Base, Compared Against Stage 1

> **Status:** Completed ✅ (2026-09-08)
> **Priority:** High
> **Dependencies:** Story 3, Story 4

## User Story

**As a** Writ maintainer who needs the cut judged by a number, not an opinion
**I want to** replay the same eight Fable 5.1 runs against the pruned base and compare the result to the Stage 1 baseline
**So that** the ~18 KB cut is kept only because the pass rate held, and reverted mechanically if it did not

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [x] Given `.writ/eval/baselines/2026-09-06-claude-fable-5-1.json`, when the new file `.writ/eval/baselines/<date>-claude-fable-5-1.json` is built by copying its `schema`, `model`, `yuss_head`, `criteria`, `selection`, `excluded`, and `rejection_tally` with `generated_at` set to now, `runs_per_story: null`, and `runs: []`, then a one-line Python comparison of the two files' `selection` and `criteria` blocks reports byte-identical equality, recorded in What Was Built `[AC-5.1]`
- [x] Given the new baseline file and a `claude` CLI authenticated as Fable 5.1, when `python3 scripts/pipeline-baseline.py run --baseline <new> --yuss ~/Projects/yuss --model claude-fable-5-1 --runs 2 --keep --tmp-root <scratch>` runs to completion outside the sandbox under `nohup` (a bare foreground run risks the session teardown that cost Stage 1 a run), then the file carries exactly eight run records and `python3 scripts/pipeline-baseline.py validate <new>` exits 0; and `bash scripts/eval.sh --check=pipeline-baseline` runs, then it reports zero findings `[AC-5.2]`
- [x] Given the Stage 1 baseline and the new baseline share an identical `selection` block, when `python3 scripts/pipeline-baseline.py compare .writ/eval/baselines/2026-09-06-claude-fable-5-1.json <new>` runs, then it does not refuse, prints four rows (one per story) with an `exit_criteria` column, and exits 0 `[AC-5.3]`
- [x] Given the `compare` output, when every `exit_criteria` row reads `2/2`, then the cut is kept and What Was Built records token totals, wall clock, the `cost_usd` sum, and the compare table; given any row reads less than `2/2`, when the failed (story, n) pair is re-run once via the resume path and `compare` still shows a shortfall, then `/revert` is run on Story 2's and Story 3's completion commits and What Was Built records the same totals plus the revert outcome, and either way the decision-log line names keep or revert with the numbers and the new baseline JSON is committed `[AC-5.4, AC-5.5]`

## Implementation Tasks

- [x] 5.1 Build `.writ/eval/baselines/<date>-claude-fable-5-1.json` from Stage 1's `schema`, `model`, `yuss_head`, `criteria`, `selection`, `excluded`, `rejection_tally`, with `generated_at` now, `runs_per_story: null`, `runs: []`; run a one-line Python check that the new and Stage 1 `selection` and `criteria` blocks are byte-identical and record the result in What Was Built `[AC-5.1]`
- [x] 5.2 Launch `python3 scripts/pipeline-baseline.py run --baseline <new> --yuss ~/Projects/yuss --model claude-fable-5-1 --runs 2 --keep --tmp-root <scratch>` outside the sandbox under `nohup` (use `python3 -u` or an equivalent to avoid stdout buffering hiding progress), and monitor until eight records are flushed `[AC-5.2]`
- [x] 5.3 Run `python3 scripts/pipeline-baseline.py validate <new>` to exit 0 and `bash scripts/eval.sh --check=pipeline-baseline` to Findings: 0 `[AC-5.2]`
- [x] 5.4 Run `python3 scripts/pipeline-baseline.py compare .writ/eval/baselines/2026-09-06-claude-fable-5-1.json <new>`; if every `exit_criteria` row reads `2/2`, keep the cut; otherwise re-run the failed (story, n) pair once via the resume path, compare again, and if still short of `2/2` on any row, run `/revert` against Story 2's and Story 3's completion commits `[AC-5.3, AC-5.4, AC-5.5]`
- [x] 5.5 Record in What Was Built: summed `input_tokens`/`output_tokens`/`cache_read_input_tokens`, wall clock, the `cost_usd` sum across the eight records, the full `compare` table, and any retry or revert; append the decision-log line stating keep or revert and the numbers `[AC-5.4, AC-5.5]`
- [x] 5.6 Verify every acceptance criterion — selection/criteria equality, `validate` exit 0, `eval.sh --check=pipeline-baseline` Findings: 0, `compare` printing four rows, and the keep-or-revert record — then commit the new baseline JSON regardless of the outcome `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

## Notes

**Technical.** `nohup` because the driving Claude Code session can be torn down mid-run — Stage 1 lost run 6 (fee-sharing, run 2) exactly this way, at about 17:25 UTC, 203 transcript lines in, with the cost of the lost partial run unrecorded. Prefer `python3 -u` (or set `PYTHONUNBUFFERED=1`) so progress lines aren't silently buffered until process exit; the baseline JSON file itself, flushed per run, is the durable progress record regardless of what stdout shows.

**Risks.** 8/8 with no tolerance — Business Rule 10 allows no partial keep. Stage 1 recorded one `DEGRADED` self-report (settlement-view run 1) whose re-derived predicates still scored `met`; that counts as a pass because the `compare` column judged is `exit_criteria` (pass count over run count from the re-derived verdict), never the model's self-report. Cache-read token variance was 59% between identical Stage 1 runs — expect similar spread here; it does not affect the keep/revert decision, only the recorded totals.

**Cost.** Stage 1's eight runs cost about $190 in driver-reported `cost_usd` and 5.5 hours wall clock (mean $23.45/run, range $16.69–$29.66). This story budgets the same for the primary eight runs, plus up to about $50 for one retried pair in the worst case. The task-formula token estimate ($10/$50/$0.25 per MTok) understated Stage 1's driver-reported cost by 3.6×; `cost_usd` per record, not the formula, is the price of record.

**Integration.** Stories 2 and 3 are the exact revert range if the pruned base fails the gate — their commits carry the ledger's rows, so reverting them restores the ledger to its post-Story-1 state automatically. Story 4's gate-verification markers are untouched by a revert of Stories 2–3 and are not part of the range. ADR-026 and the new baseline JSON survive a revert either way — Business Rule 11 keeps this story from merging, opening a PR, or releasing regardless of outcome.

## What Was Built

**Implementation Date:** 2026-09-07 → 2026-09-08 (runs 22:28 UTC 09-07 to 15:30 UTC 09-08, including one retry pass)

**Decision: KEEP.** `compare` shows exit criteria `2/2` on all four rows (Business Rule 10). Stories 2–3 stand.

### Files Created

- **`.writ/eval/baselines/2026-09-07-claude-fable-5-1.json`** — the Stage 2a re-run: header, `criteria`, `selection`, `excluded`, `rejection_tally` copied from the Stage 1 file (`selection == ` and `criteria ==` asserted True in Python before the first run), `runs_per_story: 2`, eight records. `validate` exit 0; `eval.sh --check=pipeline-baseline` Findings 0.
- **`user-stories/story-5-failed-first-attempts.json`** — the two first-attempt records the retry replaced (kept as evidence; not part of the baseline).

### Files Modified

- This story file, `user-stories/README.md`, `.writ/decision-log.md`.

### The eight runs (pruned base: Writ overlay at `e5792ce`, Story 3 closeout; base 9,704 bytes)

`writ.dirty: true` on every record only because the runner writes the uncommitted baseline file itself; no product file was dirty. Claude Code 2.1.260, `claude-fable-5-1`, `api_key_source: none`, yuss `7c2d043`, isolation asserted on all eight (1 reachable commit, answer scrubbed).

| Story | Run | Exit reported / rederived | Full jest suite | Original story tests | Tokens in / out / cache-read | STATUS: BLOCKED | Wall (min) | Driver cost |
|---|---|---|---|---|---|---|---|---|
| story-2-event-creation-payment-flow (api_route) | 1 | COMPLETE / met | 3055/3055 | suite failed to run | 182 / 84,678 / 13,583,644 | 4 | 56.3 | $26.39 |
| story-2-event-creation-payment-flow | 2 | COMPLETE / met | 3102/3102 | suite failed to run | 190 / 100,917 / 17,024,261 | 4 | 59.1 | $32.49 |
| story-3-settlement-view-share-link (ui) | 1 | COMPLETE / met | 3047/3047 | 15/49 | 120 / 61,345 / 7,595,642 | 4 | 35.8 | $17.91 |
| story-3-settlement-view-share-link | 2 | COMPLETE / met | 3046/3046 | 19/49 | 98 / 53,800 / 5,202,154 | 1 | 39.3 | $18.50 |
| story-3-fee-sharing-pro-exemption (data_model) | 1 (retry) | COMPLETE / met | 3079/3079 | suite failed to run | 160 / 73,986 / 11,272,229 | 4 | 41.8 | $23.63 |
| story-3-fee-sharing-pro-exemption | 2 | COMPLETE / met | 3065/3065 | suite failed to run | 156 / 67,273 / 10,278,764 | 4 | 39.6 | $18.84 |
| story-4-messaging-migration-quick-split-guard (refactor) | 1 | COMPLETE / met | 3035/3035 | 47/57 | 154 / 67,534 / 9,707,616 | 2 | 34.4 | $18.54 |
| story-4-messaging-migration-quick-split-guard | 2 (retry) | COMPLETE / met | 3033/3033 | 32/57 | 172 / 80,586 / 11,605,082 | 4 | 41.4 | $22.39 |

### Compare: Stage 1 (`2026-09-06`) vs Stage 2a (`2026-09-07`), per-story medians

| Story | Metric | Stage 1 | Stage 2a | Delta |
|---|---|---|---|---|
| event-creation | exit_criteria | 2/2 | 2/2 | 0 |
| event-creation | cost_usd | 27.46 | 29.44 | +1.98 |
| event-creation | tokens.cache_read | 15.69M | 15.30M | −0.38M |
| settlement-view | exit_criteria | 2/2 | 2/2 | 0 |
| settlement-view | cost_usd | 19.66 | 18.21 | −1.45 |
| settlement-view | tokens.cache_read | 9.43M | 6.40M | −3.03M |
| settlement-view | interrupts.status_blocked | 4 | 2.5 | −1.5 |
| fee-sharing | exit_criteria | 2/2 | 2/2 | 0 |
| fee-sharing | cost_usd | 26.59 | 21.24 | −5.35 |
| fee-sharing | tokens.cache_read | 12.12M | 10.78M | −1.34M |
| messaging-migration | exit_criteria | 2/2 | 2/2 | 0 |
| messaging-migration | cost_usd | 20.09 | 20.47 | +0.37 |
| messaging-migration | tokens.cache_read | 9.38M | 10.66M | +1.27M |

Wall clock, `num_turns`, and `tokens.output` rows are in the `compare` output; none changed direction consistently across stories.

### Totals (sum of eight records)

| | Stage 1 | Stage 2a | Delta |
|---|---|---|---|
| Driver `cost_usd` | $187.60 | $178.69 | −4.7% |
| Wall clock | 329 min | 348 min | +5.7% |
| `output_tokens` | 584,368 | 590,119 | +1.0% |
| `cache_read_input_tokens` | 93,235,659 | 86,269,392 | −7.5% |
| `cache_creation_input_tokens` | 2,685,120 | 1,709,096 | −36.3% |
| `input_tokens` | 1,304 | 1,232 | −5.5% |
| `num_turns` | 652 | 616 | −5.5% |
| Exit criteria met | 8/8 | 8/8 | 0 |

Read honestly: a 65% cut in the base moved total cost by −5%, within the run-to-run spread Stage 1 measured (cache-read varied 59% between identical runs). Cache-creation tokens (−36%) are the one metric that moved more than the noise, which is consistent with a smaller always-loaded prefix. The quality bar held exactly: 8/8, every gate verdict identical in kind.

### Deviations from a straight eight-of-eight first pass

- **Two first attempts were killed by the driver, not by the model, and were re-run once each per Business Rule 10.** (fee-sharing, 1): the orchestrator spawned Gate 0 and the Gate 1 coder as background subagents and ended its turn waiting; Claude Code print mode terminates after 600 s of outstanding background tasks (`stderr`: "Background tasks still running after 600s; terminating"). The run ended at 148 s with no gate verdicts, exit rederived `unmet`. Stage 1's settlement-view run 2 also used five background subagents and completed, so background use is not new to the pruned base; the difference was whether the main thread held the turn. (messaging, 2): died at 14 s / 3 turns at 03:05 UTC, coinciding with the Claude Code session that launched the runner being torn down. Both first-attempt records are in `story-5-failed-first-attempts.json`; the retries (42 and 41 min) both met.
- **The runner survived the teardown; the scratchpad did not.** The runner ran under `nohup` and completed all eight; the session restart wiped the scratch directory holding every run directory and transcript for Stage 1 and Stage 2. The baseline JSON is the durable record by design (Business Rule 3 of Stage 1), so nothing the file needs was lost. Future runs should use a `--tmp-root` outside the session scratchpad.
- **Host side effect:** replays start the host's Homebrew Postgres 17 (`pg_ctl start`) and use `writ_story{2,3,4}_test` databases that pre-date this spec (Stage 1 replays created them). Not cleaned up here; noted for the mechanization spec's runner hardening.
- **`original` story tests "suite failed to run"** on event-creation (both runs) and fee-sharing (both), as in Stage 1 for fee-sharing; the full suite passed on all eight. Measurement, not defect.

### Verification (task 5.6)

- selection/criteria equality: `True` / `True`
- `python3 scripts/pipeline-baseline.py validate .writ/eval/baselines/2026-09-07-claude-fable-5-1.json` — exit 0
- `bash scripts/eval.sh --check=pipeline-baseline` — Findings 0
- `python3 scripts/pipeline-baseline.py compare <stage1> <stage2a>` — exit 0, four rows, exit criteria 2/2 each

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [spec.md → ## 🎯 Experience Design → Error experience — "Baseline re-run below 8/8: Story 5 re-runs the failed pair once via the resume path; if it still fails, the story reverts Stories 2–3 as one commit range and records the compare table under What Was Built; the ledger and the ADR survive the revert."]
- **Shadow paths:** [spec.md → ## 🎯 Experience Design → Happy path — step (5) "Story 5 runs the eight replays and `compare` prints per-story deltas with exit criteria 2/2 on every row"; spec.md → ## 🎯 Experience Design → State catalog — "re-run in progress (records flushed per run) / kept or reverted"; spec.md → ## 🎯 Experience Design → Moment of truth — the `compare` table after Story 5]
- **Business rules:** [spec.md → ## 📋 Business Rules → 9 (Stage 1 selection reused verbatim so `compare` never refuses), 10 (keep-or-revert is mechanical: 2/2 on all four rows or revert, no partial keep), 11 (ADR-013 holds: nothing merges, opens a PR, or releases), 12 (decision-log line format `{date} stage-2: {what changed and why}`)]
- **Experience:** [spec.md → ## 🎯 Experience Design → Feedback model — `compare` prints per-story per-metric rows with `exit_criteria` as pass count over run count]
- **Requirements:** [spec.md → ## Detailed Requirements → ### Story 5 — Baseline re-run and keep-or-revert; technical-spec.md → ## 6. Re-run file and compare (Story 5) — file construction, run/validate/compare commands, revert path via `/revert` and Stage 1's `revert-resolve.py`; technical-spec.md → ## 7. Tests — "Story 5 has no new unit tests; its verification is the compare table and `validate`."]
- **Codebase:** [`scripts/pipeline-baseline.py` — `run` (resume path skips recorded pairs, records flushed per run, `--keep`, strips `CLAUDECODE` from the child env), `validate`, `compare` (refuses on differing `selection`, per-story medians, `exit_criteria` as pass count over run count); `.writ/eval/baselines/2026-09-06-claude-fable-5-1.json` — Stage 1's file to copy the header from; `.writ/specs/2026-09-05-phase11-repair-and-baseline/user-stories/story-5-baseline-capture-and-gate.md` → What Was Built — per-run table, dollar-estimate-vs-`cost_usd` gap, the run-6 teardown deviation, the fee-sharing original-tests-failed-to-run deviation; `scripts/revert-resolve.py` and `commands/revert.md` — resolve a story's completion commits for `/revert`]
