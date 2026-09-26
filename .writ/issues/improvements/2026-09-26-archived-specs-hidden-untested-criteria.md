# Twelve archived criteria were only "tested" by other specs' AC tokens

> **Type:** Improvement
> **Priority:** Low
> **Effort:** Small
> **Created:** 2026-09-26
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

`ac-trace.py` now attributes a test AC token to the spec most recently named above it (commit `7767388`, drift DEV-015 of `2026-09-26-drift-arch-guards`). That cleared 280 false `dangling_reference` findings across 66 specs, and exposed 12 criteria in six archived specs whose only test citation belonged to a different spec.

## Current State

`ac-trace.py check` now reports `untested_criterion` for:

- `2026-09-03-model-delegation`: AC-4.5, AC-5.1, AC-5.3
- `2026-09-05-phase11-repair-and-baseline`: AC-1.5, AC-5.1
- `2026-09-07-phase11-stage2-prune-the-base`: AC-4.5, AC-5.1, AC-5.3
- `2026-09-08-phase11-stage2b-mechanize-the-gates`: AC-5.3
- `2026-09-09-phase11-stage4b-pipeline-demote`: AC-1.5
- `2026-09-24-flagged-harness-cuts`: AC-5.1, AC-5.3

`eval.sh` checks active specs only, so it stays at Findings 0.

## Expected Outcome

For each criterion, either find the test that really covers it and name its spec next to the tag, or record it as untested in that spec's verification notes. Do not add tokens just to satisfy the checker.

## Relevant Files

- `scripts/ac-trace.py`
- `.writ/docs/acceptance-criteria-ids.md` (attribution rule)
- The six archived spec folders above
