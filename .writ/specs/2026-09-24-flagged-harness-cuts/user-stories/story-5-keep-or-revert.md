# Story 5: Keep or revert

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Stories 2, 3, 4

## User Story

**As a** Writ maintainer
**I want to** run the four stories × 2, flag on and flag off, on the current default frontier and compare those two runs with driver `cost_usd`
**So that** the lean siblings become the default load path only on a keep, while a null or quality miss leaves the default unchanged and still closes the gate correctly

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.4

- [ ] Given the four stories × 2 were run twice via `scripts/pipeline-baseline.py` on one current default frontier — Claude Opus 5.5, or GPT-6 Astra when that family is under test — once with `WRIT_HARNESS_LEAN=1` and once unset, when every exit-criteria row is 2/2 and flag-on driver `cost_usd` (priced by `scripts/harness-cost.py`, not the $10/$50/$0.25 formula) is lower than that same-model flag-off control, then the default load path becomes the lean siblings for models of that prowess or higher and `.writ/decision-log.md` records keep, the model, and those numbers. `[AC-5.1]`
- [ ] Given the same same-model compare, when every exit-criteria row is 2/2 and flag-on `cost_usd` does not drop against the flag-off control, then the default load path is unchanged, `.writ/decision-log.md` records null with the model and the numbers, and this story and the spec complete successfully. `[AC-5.2]`
- [ ] Given the same baseline compare, when any exit-criteria row is under 2/2, then the default load path is unchanged (any applied flip is reverted), the compare table is recorded, and the outcome is not treated as a completed keep. `[AC-5.3]`
- [ ] Given Story 5 runs, when the keep-or-revert decision is applied, then model routing is unchanged and `system-instructions.md` is not edited. `[AC-5.4]`

## Implementation Tasks

- [ ] 5.1 Write fixture checks for keep, null, and quality-miss paths against `scripts/pipeline-baseline.py compare` (including a mismatched story-id fixture that must not flip the default) and assert `scripts/harness-cost.py` treats `cost_usd` as the price of record. `[AC-5.1, AC-5.2, AC-5.3]`
- [ ] 5.2 Run the four stories × 2 twice on the current default frontier (Opus 5.5, or GPT-6 Astra when that family is under test): once with `WRIT_HARNESS_LEAN=1` and once unset, using `scripts/pipeline-baseline.py`. Do not use the Fable 5.1 dollar total as the opponent. `[AC-5.1, AC-5.2, AC-5.3]`
- [ ] 5.3 Compare the flag-on run to the same-model flag-off run via `scripts/pipeline-baseline.py compare` and price with `scripts/harness-cost.py baseline`. `[AC-5.1, AC-5.2, AC-5.3]`
- [ ] 5.4 Apply the outcome: keep flips the default load path to the lean siblings; null leaves it unchanged; quality miss reverts any flip and records the compare table — append the matching keep or null line (with numbers) to `.writ/decision-log.md`, or record the quality-miss table without a keep. `[AC-5.1, AC-5.2, AC-5.3]`
- [ ] 5.5 Confirm model routing and `system-instructions.md` are untouched by this story's outcome. `[AC-5.4]`
- [ ] 5.6 Verify acceptance criteria: compare table and `cost_usd` numbers match the decision-log line; default load path matches keep vs null vs quality miss; fixture checks pass. `[AC-5.1, AC-5.2, AC-5.3, AC-5.4]`

## Notes

- Depends on Stories 2, 3, and 4 (lean preamble, spill-to-file, lean command bodies). This story is the only one that may change the default load path.
- Do not run the eight-run baseline while authoring this story file; the baseline is an implementation task.
- Null is a successful completion of the gate and of this spec. A default flip with any exit-criteria row under 2/2 is a Story 5 failure until reverted.
- Cost opponent is the same-model flag-off control, not `.writ/eval/baselines/2026-09-07-claude-fable-5-1.json`. That file is the Stage 2 method and noise precedent. Fable 5.1 is below Opus 5.5 and GPT-6 Astra; it is not the capability bar. A keep does not extend the lean default to a weaker model. A second run reconciles against the repo; a prior keep is not inferred from the decision-log line alone.
- Out of scope: model routing, reasoning-effort defaults, which agent does which work, further edits to `system-instructions.md`.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Keep-or-revert]
- **Shadow paths:** [Baseline decision]
- **Business rules:** [Null completes the spec, Same-model compare]
- **Experience:** [Baseline keep, Baseline null, Baseline quality miss]
