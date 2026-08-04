# Phase 8: Native-Memory Guidance Per Adapter — User Stories

> **Spec:** [`../spec.md`](../spec.md)
> **Status:** Completed ✅
> **Progress:** 2/2 stories
> **Dependencies:** [2026-07-11-gbrain-compatibility-recipe] (references its skill/recipe; asserts them in the eval check)

## Story Summary

| # | Story | Priority | Dependencies | Status | Tasks |
|---|---|---|---|---|---:|
| 1 | [Per-adapter native-memory guidance + mission sweep](story-1-adapter-guidance.md) | High | None (within spec) | Completed ✅ | 6/6 |
| 2 | [`memory-interop` eval check + registration](story-2-eval-check.md) | High | Story 1 + sibling spec | Completed ✅ | 4/4 |

## Dependency Plan

```text
Story 1  (four adapter sections + mission-language sweep)
   │
Story 2  (memory-interop eval check: asserts adapters + sibling GBrain artifacts; register in CHECKS)
```

### Sequencing Rationale

- **Story 1** writes the per-adapter "Native Memory & the Writ Ledger" sections (one consistent rule, per-platform mechanics) and verifies the active mission language is free of stale framing. It owns the four adapter files.
- **Story 2** ships the machine-checkable proof: `check_memory_interop` asserts the adapter sections *and* the sibling spec's GBrain skill/recipe/registration, then registers the check. It depends on Story 1 (its adapter assertions) and on the sibling `gbrain-compatibility-recipe` spec (its GBrain assertions) — both satisfied by sequential phase execution with the sibling first.

Execution is sequential.

## Progress Rules

- Update each story's status from `Not Started` → `In Progress` → `Completed ✅`.
- Count only top-level items under `## Implementation Tasks`.
- The two-place rule must read consistently across all four adapters — inconsistency is a failing eval, not a style nit.
- Never weaken `check_memory_interop` to pass around a missing sibling artifact; fix the run order instead.
