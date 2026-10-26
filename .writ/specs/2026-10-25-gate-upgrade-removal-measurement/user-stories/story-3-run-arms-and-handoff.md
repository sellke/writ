# Story 3: Run the Arms and Hand Off for Labeling

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer
**I want to** run every trial arm on the four Phase 11 baseline stories and stop at a recorded handoff for a human labeler
**So that** the keep or remove verdict for each Phase 15 gate upgrade rests on human labels, not on the lane that ran the arms.

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given `scripts/tests/test_gate_upgrade_trial_outcome.py` exists, when `uv run pytest` runs while `trial-report.md` is absent, then the outcome test skips with a reason naming `trial-report.md`, and the file imports nothing from `gate-upgrade-trial.py` `[AC-3.1]`
- [ ] Given the three dependency specs pass `spec-status.py is-complete`, when `init` runs with `--repo .`, then the trial file records the four upgrade presence probes, the four baseline story identities, and a yuss snapshot `before` value `[AC-3.2]`
- [ ] Given `prepare` has run for a story, when its arms are spawned and recorded, then every applicable arm is recorded: `off-1`, `off-2`, and `reviewer-filters` on every story; `safety-fact` where `gate3_route` is `review-agent`; `gate0-divergence` where `gate0_route` is `review-agent`; `repro-first` recognition on every story, and its full repro arm only when `Kind:` is a bug fix. An arm that fails both spawns stays unrecorded and is named in the lane's report `[AC-3.3]`
- [ ] Given every applicable arm is recorded, when `sheet` runs and `rating-handoff.md` is written, then `labeling-sheet.md` exists with blank `label:`, `note:`, and `ack:` fields, and `report` prints `unverifiable` with `reason: unlabeled` or `not_exercised_unacknowledged` and `labeled_by` is null `[AC-3.4]`
- [ ] Given the lane has stopped, when the committed files and `spec.md` are read, then they hold no yuss source, diff, story, or reviewer text; the yuss snapshot `after` value matches `before` with `unchanged: true`; and the spec status line reads `In Progress — awaiting human labels (rating-handoff.md)` `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write `scripts/tests/test_gate_upgrade_trial_outcome.py` first: stdlib only, no import of the harness, skip with a clear reason while `trial-report.md` is absent `[AC-3.1]`
- [ ] 3.2 Confirm the three dependency specs with `spec-status.py is-complete`; if any is not complete, stop before `init` and report which. Run `init` against `.writ/eval/baselines/2026-09-07-claude-fable-5-1.json`, record the four presence probes, and snapshot yuss (`HEAD`, `git show-ref`, `git status --porcelain`) before any `prepare` `[AC-3.2, AC-3.5]`
- [ ] 3.3 Write `.writ/eval/gate-upgrade-trial/prompts/gate0-comparison.md` and `prompts/repro-stop.md` as Writ's own text, with no yuss text `[AC-3.3]`
- [ ] 3.4 For each of the four stories, run `prepare`, then spawn and `record` every applicable arm per technical-spec.md § Arms. Use the anchor tier and one model for all arms. Re-run a failed spawn once with the identical prompt; a second failure leaves the arm unrecorded and is reported `[AC-3.3, AC-3.4]`
- [ ] 3.5 Snapshot yuss again after the last `prepare`, store the result and `unchanged` in the trial file, run `sheet`, then write `rating-handoff.md` and set the spec.md status line `[AC-3.2, AC-3.4, AC-3.5]`
- [ ] 3.6 Confirm `report` prints `unverifiable` with `reason: unlabeled` or `not_exercised_unacknowledged` and `labeled_by` is null. Stop. Never fill the sheet and never run `label` `[AC-3.4]`
- [ ] 3.7 Verify all tests pass: `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` outside the sandbox. The outcome test skips with its reason. Grep the committed files for yuss paths and text `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

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

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Spawn (any arm), Repro arm] — from technical-spec.md → Error & Rescue Map
- **Shadow paths:** [Trial run (all arms recorded; yuss unreachable), Report (no labels gives `unverifiable`)] — from technical-spec.md → Shadow Paths
- **Business rules:** [yuss isolation (Rule 2), Arms (Rule 3), Exercise (Rule 4), Human gate (Rule 9)] — from spec.md → Business Rules (Expanded)
- **Experience:** []

Arm procedures and switch states: technical-spec.md → Arms. Evidence `record` checks: technical-spec.md → Arm Evidence. Trial inputs, prompt files, and the handoff contents: technical-spec.md → Trial Inputs (Story 3).
