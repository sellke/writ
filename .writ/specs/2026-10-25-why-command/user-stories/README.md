# User Stories: Why Command

> Spec: [`../spec.md`](../spec.md)

| # | Story | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---|---|
| 1 | [The `/why` Command File](story-1-why-command-file.md) | Completed ✅ | High | None | 7 | 7/7 |
| 2 | [Registration and Catalogs](story-2-registration-and-catalogs.md) | Completed ✅ | High | Story 1 | 7 | 7/7 |
| 3 | [The Front Door Routes Why Questions to `/why`](story-3-front-door-route.md) | Not Started | High | Story 2 | 6 | 0/6 |
| 4 | [`/create-spec` Reads the `/why` Handoff](story-4-create-spec-reads-handoff.md) | Not Started | High | Story 1, Story 2 | 7 | 0/7 |

**Total:** 4 stories, 27 tasks, 17 acceptance criteria.

## Dependencies

- **Story 1** has no dependency. It writes `commands/why.md` and the command tests in `scripts/tests/test_why_command.py`, and runs dogfood questions 1 to 3. Until Story 2 lands, `check_manifest` reports the command unregistered and the generated-tree check reports the plugin trees stale.
- **Story 2** needs Story 1. It registers `/why` in the manifest, regenerates `SKILL.md` and the platform trees, updates the hand-maintained catalogs, and moves `CURSOR_COUNT` to 34.
- **Story 3** needs Story 2, because both edit `scripts/tests/test_front_door.py`. It switches the front door's why-or-how route to `/why` and updates the prompting guide.
- **Story 4** needs Story 1 for the heading it reads and Story 2 for a clean generated-tree check. It adds `/create-spec` Step 1.2, re-pins the create-spec byte budget, and runs dogfood question 4 end to end.
- **Stories 3 and 4** share no file except the regenerated trees, where each changes a different command's copy. They can run in one batch.
