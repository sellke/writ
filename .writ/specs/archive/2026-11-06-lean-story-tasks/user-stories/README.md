# User Stories: Lean Story Tasks

| # | Story | Status | Priority | Dependencies | Tasks |
|---|---|---|---|---|---|
| 1 | [`oversized_task` finding in ac-trace](story-1-oversized-task-finding.md) | Completed ✅ | High | None | 6/6 |
| 2 | [Lean task rules in the story generator and Step 2.6a](story-2-lean-task-rules.md) | Completed ✅ | High | Story 1 | 6/6 |
| 3 | [Drop the generic Definition of Done](story-3-drop-generic-dod.md) | Completed ✅ | Medium | Story 2 | 7/7 |
| 4 | [State each business rule once](story-4-rules-stated-once.md) | Completed ✅ | Medium | Story 3 | 7/7 |
| 5 | [Trial lean tasks on one archived spec](story-5-lean-tasks-trial.md) | Completed ✅ | Medium | Stories 2, 3, 4 | 6/6 |

**Total: 32/32 tasks (100%)**

## Dependencies

- Story 1 adds the check that Story 2's Step 2.6a change relies on.
- Stories 2, 3, and 4 all edit `agents/user-story-generator.md` and `commands/create-spec.md`, so they run in sequence.
- Story 5 regenerates stories with the generator as changed by Stories 2–4.
