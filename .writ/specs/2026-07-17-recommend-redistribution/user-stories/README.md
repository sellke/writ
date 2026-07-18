# User Stories: Recommend Redistribution

> **Spec:** 2026-07-17-recommend-redistribution
> **Status:** Complete

## Progress

| # | Story | Status | Tasks | Dependencies |
|---|-------|--------|-------|--------------|
| 1 | [`--recommend` command redistribution](story-1-command-redistribution.md) | Completed ✅ | 5/5 | None |
| 2 | [Policy + product-layer reconciliation](story-2-policy-product-reconciliation.md) | Completed ✅ | 6/6 | Story 1 |
| 3 | [Eval falsifiability-gate reconciliation](story-3-eval-gate-reconciliation.md) | Completed ✅ | 4/4 | Story 1, Story 2 |

**Total:** 15/15 tasks (100%)

## Dependencies

- **Story 2 → Story 1:** the policy/product prose describes the redistributed commands, so the command contracts land first.
- **Story 3 → Stories 1 & 2:** the eval gate asserts the literals and contracts those stories produce.

## Quick Links

- [spec.md](../spec.md) — contract, scope, deferred-staging boundary
- [spec-lite.md](../spec-lite.md) — condensed agent context
- [ADR-013 (revised 2026-07-17)](../../../decision-records/adr-013-recommended-autonomous-delivery.md) — decision of record
