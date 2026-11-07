# User Stories: Lean Implement Phase

> Spec: [../spec.md](../spec.md) · Progress: 1/4 stories (25%)

| # | Story | Status | Tasks | AC | Dependencies |
|---|---|---|---|---|---|
| 1 | [UAT plans on request](story-1-uat-on-request.md) | Completed ✅ | 6/6 | 5 | None |
| 2 | [Health counts given sources; Goal emit leaves the phase](story-2-health-and-goal-emit.md) | Not Started | 0/6 | 4 | Story 1 |
| 3 | [Lane result file and shipped brief template](story-3-lane-result-file.md) | Not Started | 0/6 | 4 | Story 2 |
| 4 | [Compress implement-phase.md to 240 lines](story-4-prose-compression.md) | Not Started | 0/6 | 4 | Story 3 |

## Dependencies

All four stories edit `commands/implement-phase.md`, so they run one after another. Story 4 compresses text the first three change.

Batches (`story-deps.py validate`): [1] → [2] → [3] → [4].
