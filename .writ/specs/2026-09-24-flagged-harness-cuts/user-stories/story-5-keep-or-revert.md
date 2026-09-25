# Story 5: Keep or revert

> **Status:** Completed ✅ (2026-09-25)
> **Priority:** High
> **Dependencies:** Stories 2, 3, 4

## User Story

**As a** Writ maintainer
**I want to** run the four stories × 2, flag on and flag off, on the current default frontier and compare those two runs with driver `cost_usd`
**So that** the lean siblings become the default load path only on a keep, while a null or quality miss leaves the default unchanged and still closes the gate correctly

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.4

> **Amended 2026-09-25 (user-approved, see drift-log DEV-010):** the sample is reduced from four stories × 2 to one story × 2 per arm. A static bound (lean prefix saves ~1,170 tokens per turn, under 1% of a run's cache reads, against a 59% run-to-run spread) means no sample in this plan can separate a prefix-driven cost drop from noise. The reduced run tests the real risk — whether lean-loaded `/implement-story` still completes a real story — and can end only in null or quality miss. A keep still requires the original four stories × 2.

- [x] Given one story × 2 runs per arm via `scripts/pipeline-baseline.py` on one current default frontier (Claude Opus 5.5, or GPT-6 Astra when that family is under test) — one arm with the lean siblings actually loaded in the replay checkout and `WRIT_HARNESS_LEAN=1`, one arm unset — when the decision check reads the two baseline files, then it reports `keep` only if the sample is the full four stories × 2, every exit-criteria row is 2/2, and flag-on driver `cost_usd` (priced by `scripts/harness-cost.py`, not the $10/$50/$0.25 formula) is lower than the same-model control; on the reduced sample it never reports `keep`. `[AC-5.1]`
- [x] Given the same same-model compare, when every exit-criteria row is 2/2 and no keep is possible or `cost_usd` does not drop, then the default load path is unchanged, `*.lean.md` siblings are not shipped by `install.sh` / `update.sh`, `.writ/decision-log.md` records null with the model, the sample size, and the numbers, and this story and the spec complete successfully. `[AC-5.2]`
- [x] Given the same baseline compare, when any exit-criteria row is under 2/2, or the two files do not select the same stories, then the default load path is unchanged (any applied flip is reverted), the compare table is recorded, and the outcome is not treated as a keep. `[AC-5.3]`
- [x] Given Story 5 runs, when the keep-or-revert decision is applied, then model routing is unchanged and `system-instructions.md` is not edited. `[AC-5.4]`

## Implementation Tasks

- [x] 5.1 Write fixture tests for a decision check over two `pipeline-baseline-v1` files: keep (full sample, 2/2, cheaper), null (2/2, not cheaper; and reduced sample even when cheaper), quality miss (a row under 2/2), and compare error (mismatched story ids, missing file, empty `runs`) — none of the last three may report keep; `cost_usd` is the price of record `[AC-5.1, AC-5.2, AC-5.3]`
- [x] 5.2 Add a lean arm to `scripts/pipeline-baseline.py run`: after the Writ overlay, the lean siblings replace their defaults in the replay checkout, the driver gets `WRIT_HARNESS_LEAN=1`, and the run record says which arm it was; the control arm is unchanged `[AC-5.1, AC-5.3]`
- [x] 5.3 Run one story × 2 per arm on the current default frontier, compare with `scripts/pipeline-baseline.py compare`, price with `scripts/harness-cost.py baseline`, and run the decision check. Do not use the Fable 5.1 dollar total as the opponent. `[AC-5.1, AC-5.2, AC-5.3]`
- [x] 5.4 Apply the outcome: keep flips the default load path; null or quality miss leaves it unchanged and `install.sh` / `update.sh` skip `*.lean.md` siblings; append the keep or null line (model, sample, numbers) to `.writ/decision-log.md`, or record the quality-miss table without a keep `[AC-5.1, AC-5.2, AC-5.3]`
- [x] 5.5 Confirm model routing and `system-instructions.md` are untouched by this story's outcome `[AC-5.4]`
- [x] 5.6 Verify acceptance criteria: compare table and `cost_usd` numbers match the decision-log line; default load path and install behavior match the outcome; fixture tests pass `[AC-5.1, AC-5.2, AC-5.3, AC-5.4]`

## Notes

- Depends on Stories 2, 3, and 4 (lean preamble, spill-to-file, lean command bodies). This story is the only one that may change the default load path.
- Do not run the eight-run baseline while authoring this story file; the baseline is an implementation task.
- Null is a successful completion of the gate and of this spec. A default flip with any exit-criteria row under 2/2 is a Story 5 failure until reverted.
- Cost opponent is the same-model flag-off control, not `.writ/eval/baselines/2026-09-07-claude-fable-5-1.json`. That file is the Stage 2 method and noise precedent. Fable 5.1 is below Opus 5.5 and GPT-6 Astra; it is not the capability bar. A keep does not extend the lean default to a weaker model. A second run reconciles against the repo; a prior keep is not inferred from the decision-log line alone.
- Out of scope: model routing, reasoning-effort defaults, which agent does which work, further edits to `system-instructions.md`.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Keep-or-revert]
- **Shadow paths:** [Baseline decision]
- **Business rules:** [Null completes the spec, Same-model compare]
- **Experience:** [Baseline keep, Baseline null, Baseline quality miss]

---

## What Was Built

**Implementation Date:** 2026-09-25

### Files Created

1. **`scripts/lean-decision.py`** — `decide --control --lean [--format text|json]`: keep / null / quality_miss / compare_error. Keep requires 4 stories × 2, every row N/N, and lower summed `cost_usd`. Setup failures, commit mismatch, and dirty trees are `compare_error`.
2. **`scripts/tests/test_lean_decision.py`** — decision fixtures (keep, null, reduced-sample null, quality miss, compare errors, provenance, setup failures).
3. **`scripts/tests/test_install_update_lean_siblings.sh`** — install skips lean siblings; update removes unmodified leftovers and keeps modified ones; orphans still ship.
4. **`.writ/eval/baselines/2026-09-25-lean-arms/{control,lean}/2026-09-25-claude-opus-5-5.json`** — the two arm records (1 story × 2 each).

### Files Modified

- **`scripts/pipeline-baseline.py`** (`run --lean`, `apply_lean_siblings`, `driver_env`, `WRIT_KEYS`)
  - Lean bodies replace defaults in the replay checkout with the default `name:` / `description:` restored; only linked lean files (the preamble) kept under their own names; driver gets `WRIT_HARNESS_LEAN=1`; control strips an inherited flag; records carry `writ.harness_lean`; one arm per file.
- **`scripts/install.sh`, `scripts/update.sh`** — skip `*.lean.md` when the default exists; update removes unmodified stale lean siblings.
- **`scripts/tests/test_pipeline_baseline_run.py`, `scripts/tests/test_pipeline_baseline.py`** — lean-arm and backward-compatible validate tests.
- **`.writ/decision-log.md`** — null line with model, sample, and numbers.

### Implementation Decisions

1. **Reduced sample (user-approved, DEV-010)** — 1 story × 2 per arm; the prefix cut bounds any saving under 1% of cache reads against a 59% spread, so the runs test lean-text quality, and the check can only return null or quality miss.
2. **Lean arm swaps the text the harness actually loads** — the flag alone reaches nothing in Claude Code; the overlay replaces `.claude/commands/<stem>.md` and restores the default frontmatter so the lean arm carries no test-arm hints.
3. **Both arms from one clean commit** — `78d422c`; arm files written outside the repo during runs so neither run saw a dirty tree.

### Test Results

**Verification:** Automated + live baseline
- ✅ Baseline (claude-opus-5-5, story `2026-07-23-quick-split-single-transaction/story-3-settlement-view-share-link`):

| Arm | Run | Status | Exit criteria | Tests | Turns | cost_usd |
|---|---|---|---|---|---|---|
| control | 1 | complete | met | 3049/3049 | 45 | $6.85 |
| control | 2 | complete | met | 3070/3070 | 39 | $5.71 |
| lean | 1 | complete | met | 3039/3039 | 41 | $5.03 |
| lean | 2 | complete | met | 3052/3052 | 48 | $5.72 |

- ✅ `lean-decision.py decide` — **null**: reduced sample; lean $10.75 vs control $12.56 (−$1.81), per-run costs overlap; formula_usd $4.49 vs $4.67 (does not decide)
- ✅ `uv run --python 3.9 pytest -q` — 1368 passed, 1 skipped; all bash tests pass
- ✅ `bash scripts/eval.sh` — exit 0, Findings: 0
- ✅ Flag-off floor hash `84f2c4c2…c359` unchanged; four default commands and `_preamble.md` unchanged vs `main`
- ✅ AC-5.4: `system-instructions.md` and model-routing frontmatter unchanged vs `main`
- ⚠️ `test-integrity.py authenticity` — known checker false positive (see Story 1). Gate 3 `review-override.py` — `dangling_reference` `AC-5.5` from another spec's test (cross-spec collision).

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s) (pre-run fixes applied from Minor findings before any paid run)
- **Drift:** Large (DEV-010, user-approved); Small (DEV-011..013)
- **Security:** Clean
- **Boundary Compliance:** No default command text, `system-instructions.md`, or routing changed.

### Deviations from Spec

- **[DEV-010] Story 5 sample reduced to one story × 2 per arm** — Severity: Large — spec modified by user
- **[DEV-011] Story 5 scripts not listed in spec-lite Files in Scope** — Severity: Small — Auto-amended
- **[DEV-012] install/update skip lean siblings before the decision exists** — Severity: Small — Auto-amended
- **[DEV-013] Control arm strips an inherited WRIT_HARNESS_LEAN** — Severity: Small — Auto-amended
