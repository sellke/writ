# User Stories: Delete Merged Branches

> Spec: [`../spec.md`](../spec.md)

## Summary

| Story | Status | Tasks | Progress |
|---|---|---|---|
| [Story 1: Integrate deletes the merged lane branch](story-1-integrate-deletes-lane.md) | Not Started | 0 / 7 | 0% |
| [Story 2: /ship deletes the landed local branch](story-2-ship-deletes-local-branch.md) | Not Started | 0 / 7 | 0% |

**Total:** 2 stories, 14 tasks, 10 acceptance criteria.

## Dependencies

- Neither story depends on the other. They share no file except possibly `scripts/tests/test_governor_enforcement.py`, and only when both re-pin a byte budget; run them one after another if both re-pin.

## Order

1. Story 1: `phase-state.py integrate`, the lane eval check, the state-format doc, `implement-phase.md`.
2. Story 2: `scripts/ship-branch-cleanup.py`, its tests, `/ship` Step 6b, registration.
