# implement-phase Restates Its Scripts and Requires UAT Plans Nobody Runs

> **Type:** Improvement
> **Priority:** Normal
> **Effort:** Medium
> **Created:** 2026-11-06
> **spec_ref:** .writ/specs/2026-11-06-lean-implement-phase/spec.md

## TL;DR

Cut `implement-phase.md` from about 366 to about 200 lines by deleting prose that `phase-state.py` already enforces, and decide whether every merged spec still needs its own UAT plan.

## Current State

- **Evidence from Writ's 5 phase runs (20 specs):** all 20 `integrated`; 0 quarantines, 0 `skipped_blocked`, 0 halts (largest phase 6 specs, cap 12); 4 specs took a second attempt; 2 User Challenges, both in one run. No state file records a supervisor result. All runs are Writ building itself.
- **Per-spec `/create-uat-plan` is the largest cost.** Phase 15 retro F10/F24: 201 scenarios, all human, about 1.04M output tokens, 378 tool calls. `implement-phase.c2` requires a populated `uat-plan.md` for every merged spec, so the checker enforces the cost.
- **Step 4.1c `health` always reads `Warning`.** It asks for a `--verification` report that no step produces (retro F22).
- **Step 1.4 Goal emit** is not phase execution, and its notes never fail the phase.
- **Failure-path prose explains script behavior.** Steps 3.2–3.3, the mid-run closure paragraph, and the iteration-bound paragraph explain why halt is not quarantine, why closure keeps the lane branch, and so on. `phase-state.py` (20 subcommands, 1,156 lines) already enforces each of these. About 40% of the file.
- **The question policy is stated four times:** the Initiative section, the Question Policy section, the inherited-answer rule, and Step 4.3 restating condition (b), on top of the preamble's Doubt Rule.
- **Step 1.2b prescribes how to decompose** ("avoid grab-bag bundling and over-fragmentation") as well as the output shape.
- **Step 3.2.2's truncated-result paragraph** works around results that live only in conversation (F22).

## Expected Outcome

- Keep unchanged: never merge an unverified lane; the checker verdict governs; human criteria are handed off, never self-certified; lane isolation, state file, `reconcile`; the lane supervisor (in lane mode it is the only supervisor, and it is the layer that catches F6-style shortcuts); the terminal constraint.
- Failure handling becomes event → subcommand lines. The reasons move to `.writ/docs/phase-execution-state-format.md`.
- One question-policy section.
- Step 1.2b keeps the proposal shape (owns / deps / seams) and drops the method steps.
- Step 1.4 moves out of the command (or to wherever Goal Cards are consumed).
- `health` either gets a produced `--verification` input or the flag is removed.
- Lanes write `phase-spec-result-v1` to a file from a shipped brief template (F22). That replaces the truncated-result paragraph.
- UAT decision (changes behavior; needs a call): require a plan only for specs with behavior their tests don't cover, or produce one plan per phase. Update `implement-phase.c2` to match.
- Optional trial: run independent specs in parallel lanes, since Step 1.2b already gives each file one owner. Measure merge conflicts and wall-clock time before adopting.

## Relevant Files

- `commands/implement-phase.md` - all of the above
- `scripts/exit-criteria.py` - `implement-phase.c2` predicate
- `scripts/phase-state.py` - `health` inputs; lane result file

## Related Issues

- [2026-11-06-story-pipeline-over-prescribed](2026-11-06-story-pipeline-over-prescribed.md) - same problem one layer down; its lean spec leaves implement-phase untouched

## Notes

- Source: Phase 15 retro (`.writ/retros/2026-10-30-phase-15.md`) F6, F10, F22, F24, F25; `.writ/state/phase-execution-*.json`.
- No quarantines in 20 specs does not show quarantine is useless; it is the safety net for a rare event and costs only prose. Keep the scripts; cut the explanation.

## Resolution

2026-11-07, PR #69 (merge `ca51030`), released in v0.46.0. Spec [`2026-11-06-lean-implement-phase`](../../specs/archive/2026-11-06-lean-implement-phase/spec.md). `/implement-phase` generates UAT plans only with `--uat`, judges health only on the sources a run produced, reads each lane's result from `.writ/state/lane-result-<phase>-<spec>.json` (brief template `commands/_lane-brief.md`), and no longer emits a Goal Card. `commands/implement-phase.md` went from 366 to 236 lines, mostly blank lines (48 non-blank lines, about 25% of bytes). Quarantine and its scripts stay.
