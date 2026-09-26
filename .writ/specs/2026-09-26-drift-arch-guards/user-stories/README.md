# User Stories: Drift and Architecture Guards

> Spec: [`../spec.md`](../spec.md) · Lite: [`../spec-lite.md`](../spec-lite.md) · Technical: [`../sub-specs/technical-spec.md`](../sub-specs/technical-spec.md)

| # | Story | Status | Priority | Dependencies | Criteria | Tasks | Progress |
|---|---|---|---|---|---|---|---|
| 1 | [Boundary Crossings Script](story-1-boundary-crossings.md) | Not Started | High | None | 4 | 5 | 0/5 |
| 2 | [Gate 3 Risk Route](story-2-gate3-risk-route.md) | Not Started | High | Story 1 | 5 | 6 | 0/6 |
| 3 | [Contract-Anchored Drift and Architecture-Class Severity](story-3-contract-anchored-drift.md) | Not Started | High | None | 4 | 6 | 0/6 |
| 4 | [Drift Roll-up at Spec End](story-4-drift-rollup.md) | Not Started | Medium | None | 4 | 5 | 0/5 |

**Total:** 4 stories · 17 criteria · 22 tasks · 0% complete

## Dependencies

- **Story 1** builds the `crossings` helper that Story 2 wires.
- **Stories 3 and 4** are independent of 1 and 2. Story 3 edits `implement-story.md` Gate 3 context routing, which Story 2 also edits, so the two serialize on that file and the governor re-pin is recomputed by whichever lands second.

## Batches

1. Stories 1, 3, 4
2. Story 2
