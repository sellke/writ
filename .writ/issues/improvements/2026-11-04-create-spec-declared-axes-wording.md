# `/create-spec --from-prototype` Still Reads "Declared Axes"

> **Type:** Improvement
> **Priority:** Low
> **Effort:** XS
> **Created:** 2026-11-04
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

`commands/create-spec.md` `--from-prototype` Step 0 item 1 tells the agent to read "declared axes" from `exploration.md`. The design-divergence blind trial said `remove` on 2026-11-04, so `/prototype` Step 2.5 no longer declares axes. It asks for up to three drafts and states what each commits to.

## Current State

- `commands/create-spec.md` Step 0 item 1 lists "declared axes, chosen draft, and why each rejected draft lost" as what the exploration record holds.
- `commands/prototype.md` Step 2.5 now records one row per draft with what it commits to, the chosen draft, and why each rejected draft lost.

## Expected Outcome

- Step 0 item 1 names what `exploration.md` now holds: what each draft commits to, the chosen draft, and why each rejected draft lost.
- The Directions Considered line in the `--from-prototype` contract keeps reading the rejected drafts, unchanged.

## Relevant Files

- `commands/create-spec.md`: `--from-prototype` Step 0
- `commands/prototype.md`: Step 2.5 "Record the decision"
- `.writ/specs/archive/2026-10-25-design-divergence/trial-report.md`: the verdict
