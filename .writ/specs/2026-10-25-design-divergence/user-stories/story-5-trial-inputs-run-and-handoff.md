# Story 5: Trial Inputs, Generation, Blinding, and Rating Handoff

> **Status:** Completed ✅ (2026-10-29)
> **Priority:** Medium
> **Dependencies:** Story 1, Story 4

## User Story

**As a** Writ maintainer
**I want to** write the six trial briefs, generate both arms, blind them, and stop at a recorded handoff for a human rater
**So that** the keep or remove verdict on declared-axes generation rests on a blind human rating, not on the lane that built the harness.

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [x] Given `.writ/eval/divergence-trial/`, when it is read, then it holds six briefs (`ui-1`, `ui-2`, `api-1`, `api-2`, `data-model-1`, `data-model-2`) of at most 10 lines each, all describing Writ's own surfaces and quoting no other repository's source, plus `prompts/naive.md` and `prompts/axes.md` sharing one output template, and `python3 scripts/divergence-trial.py init` over the briefs has written `<date>-divergence-trial.json` `[AC-5.1]`
- [x] Given both arms were generated at the same tier in one session, when the trial file is read, then all six briefs have an `axes` and a `naive` arm recorded, the axes arm came from declared axes and three independent spawns per brief, the naive arm came from one spawn per brief using `prompts/naive.md`, and the raw drafts sit under `raw/<brief>/<arm>.md` `[AC-5.2]`
- [x] Given `blind` has run, when `rating-sheet.md` is read, then it lists six briefs with Set X and Set Y, drafts titled `Draft 1` to `Draft 3`, no `Commitment:` line, and blank rating fields; `key.json` exists; and each UI draft has a self-contained HTML page at `render/<brief>/<set>-<n>.html`, produced from the blinded text with one shared render prompt `[AC-5.3]`
- [x] Given the handoff, when `.writ/specs/2026-10-25-design-divergence/rating-handoff.md` is read and `report` runs, then the handoff names the rater, the one file to open, the field definitions, the exact `rate` and `report` commands, the honor-system rule (do not open `raw/`, `key.json`, or the trial JSON before rating), and that the lane did not rate; `report` prints `unverifiable` with `reason: unrated`; `rated_by` is null; and spec.md's status reads `In Progress — awaiting blind rating (rating-handoff.md)` `[AC-5.4]`
- [x] Given `scripts/tests/test_divergence_trial_outcome.py` (stdlib only, no import of `scripts/divergence-trial.py`), when `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` run, then the outcome test skips with a clear reason while `trial-report.md` is absent, carries the keep, remove, and unverifiable assertions from technical-spec.md → Verdict Execution, and the suite passes with 0 findings `[AC-5.5]`

## Implementation Tasks

- [x] 5.1 Write `scripts/tests/test_divergence_trial_outcome.py` first: skip with a clear reason while `trial-report.md` is absent; otherwise parse the verdict line and assert the keep, remove, and unverifiable repo state and the spec status `[AC-5.5]`
- [x] 5.2 Write the six briefs under `.writ/eval/divergence-trial/briefs/` (each at most 10 lines, Writ surfaces only) and the two prompt files `prompts/naive.md` and `prompts/axes.md` with one shared output template; then run `python3 scripts/divergence-trial.py init` `[AC-5.1]`
- [x] 5.3 Generate the axes arm per brief: declare axes from the skill's catalog, then spawn three drafts in one message, one spawn per draft, at the `anchor` tier. Generate the naive arm per brief: one spawn using `prompts/naive.md`. Record all twelve arms with `record`, which writes `raw/<brief>/<arm>.md` `[AC-5.2]`
- [x] 5.4 Run `blind`, then render each UI draft from its blinded `Structure:` text to `render/<brief>/<set>-<n>.html`, one spawn per draft, with one shared render prompt for every draft `[AC-5.3]`
- [x] 5.5 Write `rating-handoff.md`, run `report` to confirm `unverifiable` with `reason: unrated` and `rated_by` null, then set spec.md's status line to `In Progress — awaiting blind rating (rating-handoff.md)` `[AC-5.4]`
- [x] 5.6 Verify acceptance criteria: the sheet has no `Commitment:` line and no arm names, the handoff contains every required item, and the trial file matches the arm rules `[AC-5.1, AC-5.2, AC-5.3, AC-5.4]`
- [x] 5.7 Verify all tests pass: `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` outside the sandbox; the outcome test skips with its reason `[AC-5.5]`

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [`init` (not six briefs, or wrong medium split), `blind` (an arm missing), `report` (key missing or hash mismatch), `report` (ratings absent)] — from technical-spec.md → Error & Rescue Map
- **Shadow paths:** [Trial report (no ratings gives `unverifiable`)] — from technical-spec.md → Shadow Paths
- **Business rules:** [Trial integrity (same model, same brief, same output template; blinding strips `Commitment:` lines, renames titles, shuffles drafts, assigns arms to sets at random; UI drafts render after blinding), Human-gated verdict (only a human fills the sheet and runs `rate`; the lane stops at `rating-handoff.md`)] — from spec.md → Business Rules (Expanded), rules 10 and 12
- **Experience:** []

Brief list, prompt files, and paths: technical-spec.md → Trial Inputs and Run (Story 5). Subcommand contract and schema: technical-spec.md → Trial Harness.

---

## What Was Built

**Implementation Date:** 2026-10-26

### Files Created

1. **`scripts/tests/test_divergence_trial_outcome.py`** (1022 lines)
   - Stdlib + pytest, no import of the harness. Skips the verdict check while `trial-report.md` is absent; otherwise asserts the keep / remove / unverifiable repo state from technical-spec.md → Verdict Execution, reading spec.md status through `scripts/spec-status.py`. Also checks the committed briefs, shared prompt template, trial-file hashes, raw arms, blinded sheet (no column-0 `Commitment:` or `Title:`, no arm label in a label position), renders, and handoff, each skipping until its files exist. Fake-repo unit tests cover every branch.
2. **`.writ/eval/divergence-trial/briefs/{ui-1,ui-2,api-1,api-2,data-model-1,data-model-2}.md`** (8–9 lines each)
   - Writ's own surfaces only: spec-progress page, `/prototype` exploration-record viewer, `pr-ready.py` CLI contract, `/why` evidence record, verification ledger, `/retro` rule-to-enforcer table.
3. **`.writ/eval/divergence-trial/prompts/naive.md`**, **`prompts/axes.md`**, **`prompts/render.md`**
   - One shared output template in naive and axes (Structure 15–25 lines, each draft stands alone); axes adds caller usage as private input, persona, and the single-line `Commitment:`; one render prompt for all twelve UI renders.
4. **`.writ/eval/divergence-trial/2026-10-26-divergence-trial.json`** — `init`, twelve `record` runs, `blind`; `rated_by: null`.
5. **`.writ/eval/divergence-trial/raw/<brief>/{axes,naive,axes-plan}.md`** (18 files) — raw drafts as recorded, and the per-brief caller usage, declared axes, and combinations written before any spawn.
6. **`.writ/eval/divergence-trial/rating-sheet.md`**, **`key.json`** — written by `blind` (random seed).
7. **`.writ/eval/divergence-trial/render/ui-{1,2}/{X,Y}-{1,2,3}.html`** (12 files) — self-contained pages rendered from the blinded text.
8. **`.writ/specs/2026-10-25-design-divergence/rating-handoff.md`** — rater, the one file to open, field table, exact `rate` / `report` commands, honor-system rule, regeneration history, "the lane did not rate".

### Files Modified

- **`.writ/specs/2026-10-25-design-divergence/spec.md`** (header)
  - `> **Status:** In Progress — awaiting blind rating (rating-handoff.md)`.

### Implementation Decisions

1. **Generation by the orchestrator** — 18 axes spawns (three per brief, one message) and 6 naive spawns, same model and tier, each reading only its own filled prompt; the coding agent wrote the inputs and the outcome test.
2. **First generation discarded** — Gate 3 cycle 1 found content tells (axes drafts reported on the caller lines; arm lengths differed). Prompts were amended and both arms regenerated, re-blinded, and re-rendered before any rating (DEV-010).
3. **One regeneration on refusal** — second generation: `record` refused ui-1 axes draft 1 (missing `Trade-off:`); that draft was regenerated once with the identical prompt. (First generation: ui-2 axes draft 1, same cause.) No draft was hand-edited.
4. **Status read through the repo detector** — the outcome test calls `scripts/spec-status.py`, which also satisfies `test-integrity.py authenticity`.

### Test Results

**Verification:** `uv run pytest scripts/tests/test_divergence_trial_outcome.py -q` → 68 passed, 1 skipped (default and 3.9; skip: no `trial-report.md`); `python3 scripts/divergence-trial.py report --trial .writ/eval/divergence-trial/2026-10-26-divergence-trial.json` → `unverifiable`, `reason: unrated`; `test-integrity.py authenticity` → pass; full `uv run pytest` → see the commit message.
- ✅ Structure lines per arm (axes/naive): api-1 66/62, api-2 69/72, data-model-1 65/63, data-model-2 67/63, ui-1 60/58, ui-2 60/56

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s)
- **Drift:** Medium
- **Security:** Clean
- **Boundary Compliance:** the trial artifacts, the handoff, and the spec.md status line are the paths Story 5 names
- **gate3-route:** review-agent (outside_boundary on the generated trial artifacts under .writ/eval/divergence-trial/ and the spec status line)
- **review-panel:** skipped — platform cannot spawn other vendors

### Deviations from Spec

- **[DEV-010] First generation discarded for content tells; residual tells from the arm design remain** — Severity: Medium
  - Spec said: the verdict rests on a blind human rating
  - Reality: cycle-1 PAUSE (Large); prompts amended, both arms regenerated; residual style and identifier tells inherent to the arm design remain
  - Resolution: Logged (Medium); Story 6 records the caveat beside `trial-report.md` after rating
- **[DEV-011] Outcome test also checks the committed trial inputs structurally** — Severity: Small
  - Spec said: verdict-state assertions only
  - Reality: plus structural checks that skip until their files exist
  - Resolution: Auto-amended (Small)
