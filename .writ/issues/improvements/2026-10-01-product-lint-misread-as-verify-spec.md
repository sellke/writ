# `/verify-spec --product` Reads as the Post-Implementation Step

> **Type:** Improvement
> **Priority:** Normal
> **Effort:** Small
> **Created:** 2026-10-01
> **spec_ref:** .writ/specs/2026-10-01-product-check-direction/spec.md

## TL;DR

The product-docs consistency lint lives under `/verify-spec`, the command users know as "run after implementing a spec," so a suggestion to run it after `/plan-product --reconcile` was read as skipping implementation.

## Current State

- `/verify-spec` (checks 1–8) is the post-implementation spec check; `/verify-spec --product` (checks P1–P4) lints `.writ/product/` and shares no checks with it.
- Observed 2026-10-01: after a reconcile, the suggested next step `/verify-spec --product` was read as "verify a spec we haven't built yet."
- The two command files disagree on its position. `verify-spec.md:37` calls `--product` the lint that runs *before* `--reconcile`; `plan-product.md:106` tells reconcile to suggest it *after* applying edits. Both uses are valid, but the before/after framing makes it sound like a single slot.

## Expected Outcome

- The product lint is invoked from the product command: `/plan-product --check`, the before/after pair living in one command, the same way `--reconcile` already does.
- `/verify-spec --product` keeps working for one release as a deprecated alias that prints the new name, then is removed.
- One sentence in both files states the lint's two uses: before reconcile to find drift, after reconcile to confirm consistency.
- References in `release.md`, `retro.md`, `verify-spec.lean.md`, and the eval/test pins are migrated in the same change.

## Relevant Files

- `commands/verify-spec.md` - defines `--product` (line 35) and the before/after boundary (line 37, §Product Consistency Checks at line 618)
- `commands/plan-product.md` - `--reconcile` points at `/verify-spec --product` before (line 39) and after (line 106)
- `commands/verify-spec.lean.md` - 12 references that must move with the canonical file

## Notes

- Also referenced by `commands/release.md`, `commands/retro.md` (product-drift nudge), `scripts/tests/test_lean_commands.py`, and `scripts/roadmap-sync.py`'s docstring; check `scripts/eval.sh` for `require_literal` pins on the flag before renaming.
- Cheaper alternative if the move is judged not worth the churn: keep the flag, retitle the mode "Product lint (not a spec check)" in the invocation table, and fix the before/after wording. That leaves the naming trap in place.
- Historical mentions in `CHANGELOG.md` and `.writ/product/verification-*.md` stay as written.

## Resolution

2026-10-02, spec `2026-10-01-product-check-direction`: Story 1 commit 3992545, Story 2 commit 0fe1575. The lint stays at `/verify-spec --product`; discovery rejected the move to `/plan-product`. Every file that names both commands now states one direction: "Verification surfaces drift after implementation; `/plan-product --reconcile` realigns the baseline when it does." `--reconcile` Step R4 hands back to `/create-spec`, and `/implement-phase` and `/release` each suggest `/verify-spec --product` in one completion line. The eval check `product-check-direction` and `scripts/tests/test_product_check_direction.py` pin the wording.
