# Story 3: Run the Arms and Hand Off for Labeling

> **Status:** Completed ✅ (2026-10-29)
> **Commit:** 4542d78c3b510568f4c9717b41f319fcc5dbdd15
> **Priority:** Medium
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer
**I want to** run every trial arm on the four Phase 11 baseline stories and stop at a recorded handoff for a human labeler
**So that** the keep or remove verdict for each Phase 15 gate upgrade rests on human labels, not on the lane that ran the arms.

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given `scripts/tests/test_gate_upgrade_trial_outcome.py` exists, when `uv run pytest` runs while `trial-report.md` is absent, then the outcome test skips with a reason naming `trial-report.md`, and the file imports nothing from `gate-upgrade-trial.py` `[AC-3.1]`
- [x] Given the three dependency specs pass `spec-status.py is-complete`, when `init` runs with `--repo .`, then the trial file records the four upgrade presence probes, the four baseline story identities, and a yuss snapshot `before` value `[AC-3.2]`
- [x] Given `prepare` has run for a story, when its arms are spawned and recorded, then every applicable arm is recorded: `off-1`, `off-2`, and `reviewer-filters` on every story; `safety-fact` where `gate3_route` is `review-agent`; `gate0-divergence` where `gate0_route` is `review-agent`; `repro-first` recognition on every story, and its full repro arm only when `Kind:` is a bug fix. An arm that fails both spawns stays unrecorded and is named in the lane's report `[AC-3.3]`
- [x] Given every applicable arm is recorded, when `sheet` runs and `rating-handoff.md` is written, then `labeling-sheet.md` exists with blank `label:`, `note:`, and `ack:` fields, and `report` prints `unverifiable` with `reason: unlabeled` or `not_exercised_unacknowledged` and `labeled_by` is null `[AC-3.4]`
- [x] Given the lane has stopped, when the committed files and `spec.md` are read, then they hold no yuss source, diff, story, or reviewer text; the yuss snapshot `after` value matches `before` with `unchanged: true`; and the spec status line reads `In Progress — awaiting human labels (rating-handoff.md)` `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Write `scripts/tests/test_gate_upgrade_trial_outcome.py` first: stdlib only, no import of the harness, skip with a clear reason while `trial-report.md` is absent `[AC-3.1]`
- [x] 3.2 Confirm the three dependency specs with `spec-status.py is-complete`; if any is not complete, stop before `init` and report which. Run `init` against `.writ/eval/baselines/2026-09-07-claude-fable-5-1.json`, record the four presence probes, and snapshot yuss (`HEAD`, `git show-ref`, `git status --porcelain`) before any `prepare` `[AC-3.2, AC-3.5]`
- [x] 3.3 Write `.writ/eval/gate-upgrade-trial/prompts/gate0-comparison.md` and `prompts/repro-stop.md` as Writ's own text, with no yuss text `[AC-3.3]`
- [x] 3.4 For each of the four stories, run `prepare`, then spawn and `record` every applicable arm per technical-spec.md § Arms. Use the anchor tier and one model for all arms. Re-run a failed spawn once with the identical prompt; a second failure leaves the arm unrecorded and is reported `[AC-3.3, AC-3.4]`
- [x] 3.5 Snapshot yuss again after the last `prepare`, store the result and `unchanged` in the trial file, run `sheet`, then write `rating-handoff.md` and set the spec.md status line `[AC-3.2, AC-3.4, AC-3.5]`
- [x] 3.6 Confirm `report` prints `unverifiable` with `reason: unlabeled` or `not_exercised_unacknowledged` and `labeled_by` is null. Stop. Never fill the sheet and never run `label` `[AC-3.4]`
- [x] 3.7 Verify all tests pass: `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` outside the sandbox. The outcome test skips with its reason. Grep the committed files for yuss paths and text `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

- **Human gate.** This story ends at `rating-handoff.md`, not at a verdict. The maintainer labels. Story 4 acts on the labels.
- **Spend.** About 35 spawns across the four stories: 12 arm spawns for `off-1`, `off-2`, and `reviewer-filters`; about 4 `safety-fact` spawns plus any single re-review; 3 Gate 0 comparison spawns and their two sketch spawns each; 4 repro recognition spawns plus at most one full repro; and the one-time re-run allowance for failed spawns.
- **Honor-system blinding.** The sheet hides which upgrade raised each finding, but the trial JSON (committed) maps IDs to upgrades and the raw outputs (gitignored state directory) name their arm. `rating-handoff.md` tells the maintainer to open only `labeling-sheet.md` and the excerpt files, and not the trial JSON or `<state>/<slug>/` raw outputs, before labeling. Gate 0 excerpts reveal themselves through their `Avoided by:` line. `trial-report.md` repeats this caveat.
- **yuss is read-only.** Use only `git -C <yuss> rev-parse`, `show-ref`, `status --porcelain`, and the fetch into a fresh repo under `$TMPDIR` that `prepare` performs. Make no write to `/Users/asellke/Projects/yuss`.
- **Retrospective proxies.** The Gate 0 and Repro First arms are proxies: a sketch comparison and a repro re-run. The handoff and report must say so.
- **Small sample.** Four stories and one on-run per upgrade arm. The handoff states this.
- **Hard dependency.** Story 2 must land first. `init`, `prepare`, `record`, `sheet`, and `report` must exist before tasks 3.2 through 3.6 run. If `review-panel.py` is missing or lacks a reused name, `prepare` and `record` exit 2 with `reason: review_panel_missing`; stop and report it.
- **Trial file and sheet are committed.** Keep both free of yuss text. Raw outputs stay in the gitignored `.writ/state/gate-upgrade-trial/`.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Spawn (any arm), Repro arm] — from technical-spec.md → Error & Rescue Map
- **Shadow paths:** [Trial run (all arms recorded; yuss unreachable), Report (no labels gives `unverifiable`)] — from technical-spec.md → Shadow Paths
- **Business rules:** [yuss isolation (Rule 2), Arms (Rule 3), Exercise (Rule 4), Human gate (Rule 9)] — from spec.md → Business Rules (Expanded)
- **Experience:** []

Arm procedures and switch states: technical-spec.md → Arms. Evidence `record` checks: technical-spec.md → Arm Evidence. Trial inputs, prompt files, and the handoff contents: technical-spec.md → Trial Inputs (Story 3).

## What Was Built

**Implementation Date:** 2026-10-29

### Files Created

1. **`scripts/tests/test_gate_upgrade_trial_outcome.py`** — stdlib + pytest; never loads the harness. One live test per upgrade (`test_upgrade_verdict_matches_repo`) skips while `trial-report.md` is absent; once present it ties each `upgrade:` verdict to the presence probe or the removal assertions, the trial file's labels, and the spec status. 37 unit tests run the private checks against fake repos.
2. **`.writ/eval/gate-upgrade-trial/prompts/gate0-comparison.md`** — comparison-reviewer brief: defects in the shipped diff that the chosen sketch avoids, Gate 3 issue fields plus `- **Avoided by:** "<sketch line>"`.
3. **`.writ/eval/gate-upgrade-trial/prompts/repro-stop.md`** — recognition-then-stop brief appended to the coding-agent prompt in `parent/`.
4. **`.writ/eval/gate-upgrade-trial/2026-10-29-gate-upgrade-trial.json`** — the trial file: four stories, routes, 23 recorded arms (keys, switch states, raw-output hashes), 6 upgrade-only findings with IDs and null labels, yuss before/after snapshot (`unchanged: true`), `labeled_by: null`. IDs, SHAs, paths, keys, and words only.
5. **`.writ/eval/gate-upgrade-trial/labeling-sheet.md`** — F01-F06 with blank `label:`/`note:` and one blank `ack:` (repro-first).
6. **`.writ/specs/2026-10-25-gate-upgrade-removal-measurement/rating-handoff.md`** — who labels, what to open, label and ack rules, exercise counts, commands, honor-system rule, caveats.

### Files Modified

- **`.writ/specs/2026-10-25-gate-upgrade-removal-measurement/spec.md`** — status `In Progress — awaiting human labels (rating-handoff.md)`.

### Implementation Decisions

1. **Trial run by the orchestrator** — Gate 1 wrote the test and prompts; the orchestrator ran `init`, `prepare`, every arm spawn, `record`, `snapshot`, and `sheet` (spawning needs the orchestrator).
2. **Proceeded with design-divergence incomplete** on the phase orchestrator's instruction (DEV-007, Medium).
3. **Removal-inventory corrections** for Story 4 recorded as DEV-011.

### Test Results

**Verification:** orchestrator run `uv run pytest scripts/tests/test_gate_upgrade_trial_outcome.py scripts/tests/test_gate_upgrade_trial.py -q -rs` → 346 passed, 4 skipped (reason names `trial-report.md`), exit 0; reviewer: full suite 3987 passed, 7 skipped; Python 3.9 outcome test 37 passed, 4 skipped; bash tests 0 failures; `eval.sh` 0 findings.
- ✅ test-integrity authenticity: pass

### Trial Run

- **Exercise:** Gate 0 Divergence 3/4 (quick-split story-3 predicted `evaluator-agent`); Safety Fact 4/4; Reviewer Filters 4/4; Repro First 0/4 (all four `Kind: not a bug fix`).
- **Upgrade-only findings:** Gate 0 Divergence 3, Safety Fact 2, Reviewer Filters 1, Repro First 0. Off-only: 0 for every upgrade.
- **Report:** `unverifiable` — unlabeled 3 / 2 / 1; `repro-first not_exercised_unacknowledged`; `labeled_by` null. The lane did not label.
- **Spawns:** 30 (16 Gate 3 arms, 1 safety-fact re-review on story-4 after `safety_fact_below_floor read`, 6 sketches, 3 comparisons, 4 repro recognitions); one model (`claude-opus-5-5`) throughout; no spawn failed.
- **yuss:** HEAD `a5afd435…`, refs and status hashes identical before and after.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Medium (DEV-007 ⚠️; DEV-008 to DEV-011 Small)
- **Security:** Clean (no yuss text committed; read-only yuss access)
- **Boundary Compliance:** six owned files plus the spec status line
- **gate3-route:** review-agent (outside_boundary against the computed map)
- **reviewer-filters:** on
- **gate0-divergence:** chose A (one call, errors as exceptions) — B added ten public helper names with the same unchanged usage
- **review-panel:** skipped — platform cannot spawn other vendors
- **review-override check:** pass (no blocking helper finding)
- **safety-fact:** tested (claimed tested) — the live outcome check is skipped while `trial-report.md` is absent
- **jev shadow:** pass (criteria=5 agree=1 false_block=4) — advisory only
- **arch-lint:** none — see .writ/docs/architecture-lint.md
- **build-smoke:** unverifiable (unsupported_stack)
- **Reviewer note before labeling:** on story-4 and fee-sharing story-3 one "current gates" run produced zero keys, so the baseline there is effectively one run; disclosed in `rating-handoff.md`.
