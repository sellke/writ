# User Stories: Lean Story Tasks

| # | Story | Status | Priority | Dependencies | Tasks |
|---|---|---|---|---|---|
| 1 | [`oversized_task` finding in ac-trace](story-1-oversized-task-finding.md) | Completed ✅ | High | None | 6/6 |
| 2 | [Lean task rules in the story generator and Step 2.6a](story-2-lean-task-rules.md) | Not Started | High | Story 1 | 0/6 |
| 3 | [Drop the generic Definition of Done](story-3-drop-generic-dod.md) | Not Started | Medium | Story 2 | 0/7 |
| 4 | [State each business rule once](story-4-rules-stated-once.md) | Not Started | Medium | Story 3 | 0/7 |
| 5 | [Trial lean tasks on one archived spec](story-5-lean-tasks-trial.md) | Not Started | Medium | Stories 2, 3, 4 | 0/6 |

**Total: 6/32 tasks (19%)**

## Dependencies

- Story 1 adds the check that Story 2's Step 2.6a change relies on.
- Stories 2, 3, and 4 all edit `agents/user-story-generator.md` and `commands/create-spec.md`, so they run in sequence.
- Story 5 regenerates stories with the generator as changed by Stories 2–4.
