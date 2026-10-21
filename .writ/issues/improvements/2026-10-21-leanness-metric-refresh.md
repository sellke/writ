# Refresh the Leanness Metric So Its Warnings Carry Signal

> **Type:** Improvement
> **Priority:** Low
> **Effort:** Small
> **Created:** 2026-10-21
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

The Tier A leanness check raises 17 standing warnings that nobody acts on. The `scripts` surface counts tests together with shipped scripts. The justified ceilings date from August.

## Current State

- From the 2026-10-21 Tier B audit (`.writ/docs/leanness-audit-2026-10-21.md`):
  - The `scripts` surface is 94,320 lines and includes `scripts/tests/`. Phase 13 added +7,236 lines there, mostly regression tests, which reads as growth.
  - Every surface is past a justified ceiling recorded on 2026-08-12 to 2026-09-03.
  - Commands fell by 2,139 lines in Phase 13, but no ceiling or baseline recorded the drop.
  - `commands/implement-phase.md` is 34,881 bytes, 140% of the per-invocation budget, and is the next reduction candidate.
- ADR-023 keeps bytes as a drift signal only. The point here is to make that signal readable, not to add a budget.

## Expected Outcome

- `eval-leanness.py` reports shipped scripts, dev-only scripts, and tests as separate surfaces.
- The baseline ratchets down after Phase 13, so the next growth warning means something.
- A coaching-only reduction pass on `implement-phase.md`, with a cut log, following `.writ/specs/2026-10-20-shipped-command-hygiene/cut-log.md`.

## Relevant Files

- `scripts/eval-leanness.py`
- `.writ/leanness-baseline.json`
- `commands/implement-phase.md`
- `.writ/decision-records/adr-023-stakes-proportional-diligence.md`
