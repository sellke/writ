# User Stories: Product Reconciliation

> **Spec:** 2026-07-11-product-reconciliation
> **Status:** Complete

## Progress

| # | Story | Status | Tasks | Dependencies |
|---|-------|--------|-------|--------------|
| 1 | [`/verify-spec --product` mode](story-1-verify-product.md) | Completed ✅ | 5/5 | None |
| 2 | [`/plan-product --reconcile` mode](story-2-plan-product-reconcile.md) | Completed ✅ | 5/5 | None |
| 3 | [`/retro` product-drift nudge](story-3-retro-nudge.md) | Completed ✅ | 4/4 | Story 1 |

**Total:** 14/14 tasks (100%)

## Dependencies

- **Story 3 → Story 1:** the `/retro` nudge points users to `/verify-spec
  --product`, so that mode should be defined first.
- Stories 1 and 2 are independent and can proceed in parallel.

## Quick Links

- [spec.md](../spec.md) — contract, boundary discipline, `--product` check set
- [spec-lite.md](../spec-lite.md) — condensed agent context
- [sub-specs/technical-spec.md](../sub-specs/technical-spec.md) — per-file edits
