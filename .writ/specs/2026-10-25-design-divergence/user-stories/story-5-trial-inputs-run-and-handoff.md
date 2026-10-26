# Story 5: Trial Inputs, Generation, Blinding, and Rating Handoff

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 1, Story 4

## User Story

**As a** Writ maintainer
**I want to** write the six trial briefs, generate both arms, blind them, and stop at a recorded handoff for a human rater
**So that** the keep or remove verdict on declared-axes generation rests on a blind human rating, not on the lane that built the harness.

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [ ] Given `.writ/eval/divergence-trial/`, when it is read, then it holds six briefs (`ui-1`, `ui-2`, `api-1`, `api-2`, `data-model-1`, `data-model-2`) of at most 10 lines each, all describing Writ's own surfaces and quoting no other repository's source, plus `prompts/naive.md` and `prompts/axes.md` sharing one output template, and `python3 scripts/divergence-trial.py init` over the briefs has written `<date>-divergence-trial.json` `[AC-5.1]`
- [ ] Given both arms were generated at the same tier in one session, when the trial file is read, then all six briefs have an `axes` and a `naive` arm recorded, the axes arm came from declared axes and three independent spawns per brief, the naive arm came from one spawn per brief using `prompts/naive.md`, and the raw drafts sit under `raw/<brief>/<arm>.md` `[AC-5.2]`
- [ ] Given `blind` has run, when `rating-sheet.md` is read, then it lists six briefs with Set X and Set Y, drafts titled `Draft 1` to `Draft 3`, no `Commitment:` line, and blank rating fields; `key.json` exists; and each UI draft has a self-contained HTML page at `render/<brief>/<set>-<n>.html`, produced from the blinded text with one shared render prompt `[AC-5.3]`
- [ ] Given the handoff, when `.writ/specs/2026-10-25-design-divergence/rating-handoff.md` is read and `report` runs, then the handoff names the rater, the one file to open, the field definitions, the exact `rate` and `report` commands, the honor-system rule (do not open `raw/`, `key.json`, or the trial JSON before rating), and that the lane did not rate; `report` prints `unverifiable` with `reason: unrated`; `rated_by` is null; and spec.md's status reads `In Progress — awaiting blind rating (rating-handoff.md)` `[AC-5.4]`
- [ ] Given `scripts/tests/test_divergence_trial_outcome.py` (stdlib only, no import of `scripts/divergence-trial.py`), when `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` run, then the outcome test skips with a clear reason while `trial-report.md` is absent, carries the keep, remove, and unverifiable assertions from technical-spec.md → Verdict Execution, and the suite passes with 0 findings `[AC-5.5]`

## Implementation Tasks

- [ ] 5.1 Write `scripts/tests/test_divergence_trial_outcome.py` first: skip with a clear reason while `trial-report.md` is absent; otherwise parse the verdict line and assert the keep, remove, and unverifiable repo state and the spec status `[AC-5.5]`
- [ ] 5.2 Write the six briefs under `.writ/eval/divergence-trial/briefs/` (each at most 10 lines, Writ surfaces only) and the two prompt files `prompts/naive.md` and `prompts/axes.md` with one shared output template; then run `python3 scripts/divergence-trial.py init` `[AC-5.1]`
- [ ] 5.3 Generate the axes arm per brief: declare axes from the skill's catalog, then spawn three drafts in one message, one spawn per draft, at the `anchor` tier. Generate the naive arm per brief: one spawn using `prompts/naive.md`. Record all twelve arms with `record`, which writes `raw/<brief>/<arm>.md` `[AC-5.2]`
- [ ] 5.4 Run `blind`, then render each UI draft from its blinded `Structure:` text to `render/<brief>/<set>-<n>.html`, one spawn per draft, with one shared render prompt for every draft `[AC-5.3]`
- [ ] 5.5 Write `rating-handoff.md`, run `report` to confirm `unverifiable` with `reason: unrated` and `rated_by` null, then set spec.md's status line to `In Progress — awaiting blind rating (rating-handoff.md)` `[AC-5.4]`
- [ ] 5.6 Verify acceptance criteria: the sheet has no `Commitment:` line and no arm names, the handoff contains every required item, and the trial file matches the arm rules `[AC-5.1, AC-5.2, AC-5.3, AC-5.4]`
- [ ] 5.7 Verify all tests pass: `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` outside the sandbox; the outcome test skips with its reason `[AC-5.5]`

## Notes

- This story ends at the handoff, not at a verdict. Story 6 acts on the human's rating.
- The implementing agent knows the key, because it generates the arms and runs `blind`. It must never fill the rating sheet and never run `rate`. It never acts on a verdict it produced.
- `key.json` and the raw drafts are committed so they survive a lane worktree. Blinding is therefore honor-system. The handoff tells the rater to open only the sheet, and `trial-report.md` states the same caveat.
- The briefs come from Writ's own roadmap (Phase 15 and Phase 16 surfaces), so no private or third-party source is committed. Do not add material from other repositories.
- `render_only_enough` is recorded per brief for the prototype research's Further Research item 5. It is not part of the keep rule.
- Both arms use the same tier (`anchor`, platform `inherit`) in one session. Mixed tiers make the comparison invalid.
- Spend: about 6 × (3 + 1) generation spawns, plus 12 render spawns for the two UI briefs (3 drafts × 2 arms × 2 briefs), at the anchor tier.
- A draft set that `record` refuses (wrong draft count, a missing field, `Commitment:` in the wrong arm) or a failed spawn is regenerated once with the identical prompt. A second failure stops the story before `blind` and is reported; never hand-edit a draft to make it pass.
- Story 4 must land first. The `init`, `record`, and `blind` subcommands must exist before tasks 5.2 through 5.4 run.
- Integration: Story 6 reads `rating-handoff.md` and the trial file. Changes to the sheet format or trial schema in this story break Story 6's `report` path.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [`init` (not six briefs, or wrong medium split), `blind` (an arm missing), `report` (key missing or hash mismatch), `report` (ratings absent)] — from technical-spec.md → Error & Rescue Map
- **Shadow paths:** [Trial report (no ratings gives `unverifiable`)] — from technical-spec.md → Shadow Paths
- **Business rules:** [Trial integrity (same model, same brief, same output template; blinding strips `Commitment:` lines, renames titles, shuffles drafts, assigns arms to sets at random; UI drafts render after blinding), Human-gated verdict (only a human fills the sheet and runs `rate`; the lane stops at `rating-handoff.md`)] — from spec.md → Business Rules (Expanded), rules 10 and 12
- **Experience:** []

Brief list, prompt files, and paths: technical-spec.md → Trial Inputs and Run (Story 5). Subcommand contract and schema: technical-spec.md → Trial Harness.
