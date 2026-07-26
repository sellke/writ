# User Stories: Leanness Instrumentation Rewrite

> Spec: [`spec.md`](../spec.md)
> Created: 2026-07-26
> Progress: 5/5 complete (100%)

## Stories

| # | Story | Status | Priority | Tasks | AC | Depends on |
|---|---|---|---|---:|---:|---|
| 1 | [Full-Surface Measurement & Baseline Schema](story-1-full-surface-measurement.md) | Completed ✅ | High | 7/7 | 5 | — |
| 2 | [Coverage Guard — Hard-FAIL on Unmeasured Surface](story-2-coverage-guard.md) | Completed ✅ | High | 7/7 | 5 | Story 1 |
| 3 | [Static `story_context_bytes` Metric](story-3-story-context-bytes.md) | Completed ✅ | Medium | 7/7 | 5 | — |
| 4 | [Reduction Ratchet Replaces Growth Tolerance](story-4-reduction-ratchet.md) | Completed ✅ | High | 7/7 | 5 | Story 1 |
| 5 | [ADR-019 & Tier B Audit Format Update](story-5-adr-and-tier-b.md) | Completed ✅ | Medium | 7/7 | 5 | 1, 2, 3, 4 |

**Totals:** 5 stories · 35 implementation tasks · 25 acceptance criteria

## Dependency Graph

```
1 ──┬──> 2 ──┐
    │        ├──> 5
    └──> 4 ──┤
             │
3 ───────────┘
```

**Execution batches:**

| Batch | Stories | Mode |
|---|---|---|
| 1 | Story 1, Story 3 | parallel — both independent |
| 2 | Story 2, Story 4 | parallel — both need Story 1's surface registry |
| 3 | Story 5 | sequential — records what actually shipped |

## Dependency Rationale

- **Story 1 → Stories 2 and 4.** Both consume the surface registry that Story 1 introduces. The coverage guard compares repo-root entries against it; the ratchet compares per-surface baselines derived from it.
- **Story 3 is independent.** It adds a metric computed from `implement-story.md`'s declared load set and never touches the registry. It shares a merge seam with Story 1 in `compute_metrics` — keep the addition self-contained.
- **Story 5 depends on all four.** It is the durable record, written last so it documents what shipped rather than what was planned. ADR-019 cannot honestly describe the ratchet reversal or the trend-line reset before those land.

## Ordering Note

Story 2 is the story that justifies the spec's shape. Story 1 fixes the blind spot that exists today (`scripts/` unmeasured, 32% coverage). Story 2 is what makes the *next* blind spot impossible. If scope has to be cut, cut elsewhere.

## Scope Guard

No story in this spec deletes anything. This spec builds the instrument; the surgery is downstream work. A story that starts pruning surface has escaped its contract — see `spec.md → ## Scope Boundaries`.
