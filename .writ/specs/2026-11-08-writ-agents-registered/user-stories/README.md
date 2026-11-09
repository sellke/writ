# User Stories: Writ Agents Registered

> Spec: [`../spec.md`](../spec.md)

## Summary

| Story | Status | Tasks | Progress |
|---|---|---|---|
| [Story 1: Register the writ-* agents in this repo](story-1-register-writ-agents.md) | Completed ✅ | 7 / 7 | 100% |
| [Story 2: Spawn fallback and no inline coding](story-2-spawn-fallback.md) | Completed ✅ | 7 / 7 | 100% |

**Total:** 2 stories, 14 tasks, 9 acceptance criteria.

## Dependencies

- Story 1 has none.
- Story 2 depends on Story 1: its fallback rule describes the registered state Story 1 creates.

## Order

1. Story 1: repoint `.claude/agents`, the eval check and its tests, the fresh-session run.
2. Story 2: the adapter fallback rule, the Gate 1 sentence, the supervisor ESCALATE clause, regenerated copies, text pins.
