# Recommended Autonomous Delivery — User Stories

> **Spec:** [`../spec.md`](../spec.md)
> **Status:** Complete
> **Progress:** 5/5 stories · 35/35 tasks

## Story Summary

| Story | Title | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---:|---:|
| [1](story-1-governance-and-autonomy-policy.md) | Governance and Autonomy Policy | Completed ✅ | High | None | 7 | 7/7 |
| [2](story-2-recommendation-semantics.md) | Recommendation Semantics | Completed ✅ | High | Story 1 | 7 | 7/7 |
| [3](story-3-autonomous-spec-implementation.md) | Autonomous Spec-to-Implementation Orchestration | Completed ✅ | High | Story 2 | 7 | 7/7 |
| [4](story-4-preview-deployment-and-uat.md) | PR Preview Deployment and Staged UAT | Completed ✅ | High | Story 3 | 7 | 7/7 |
| [5](story-5-merge-release-and-recovery.md) | Merge, Release, and Recovery | Completed ✅ | High | Story 4 | 7 | 7/7 |

## Execution Order

The stories form one deliberate sequence:

```text
Story 1: Governance
    ↓
Story 2: Recommendation policy
    ↓
Story 3: Spec-to-implementation orchestration
    ↓
Story 4: PR preview and production approval
    ↓
Story 5: Merge and release
```

### Dependency Rationale

- **Story 1 before Story 2:** Recommendation behavior must not be implemented while ADR-010 and Phase 6 still define a contradictory autonomy ceiling.
- **Story 2 before Story 3:** The orchestrator needs one shared definition of evidence, automatic selection, pause boundaries, and rationale records.
- **Story 3 before Story 4:** PR staging consumes the active mode, durable state, verified implementation result, and recommendation log.
- **Story 4 before Story 5:** Merge and release require successful checks, same-SHA preview evidence, UAT context, and explicit production approval.

## Totals

- **Stories:** 5
- **Acceptance criteria:** 25
- **Implementation tasks:** 35
- **Completed tasks:** 35
- **Overall progress:** 100%

## Supporting Documents

- [Full specification](../spec.md)
- [Lite specification](../spec-lite.md)
- [Technical specification](../sub-specs/technical-spec.md)
- [Source issue](../../../issues/improvements/2026-07-09-label-recommended-spec-options.md)

## Implementation Note

This spec blocks implementation of `2026-07-09-phase6-autonomy-ceiling` until Story 1 reconciles its governance, contract, and affected stories. Multi-spec `/implement-phase --recommend` remains excluded.
