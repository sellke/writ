# User Stories: Front Door

> Spec: [`../spec.md`](../spec.md)

| # | Story | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---|---|
| 1 | [The `/writ` Command File](story-1-writ-command-file.md) | Not Started | High | None | 7 | 0/7 |
| 2 | [Registration and Catalogs](story-2-registration-and-catalogs.md) | Not Started | High | Story 1 | 7 | 0/7 |
| 3 | [Structure Rows, Issue Resolution, and Routing Fixture](story-3-structure-rows-issue-and-routing-fixture.md) | Not Started | High | Story 1, Story 2 | 7 | 0/7 |

**Total:** 3 stories, 21 tasks, 15 acceptance criteria.

## Dependencies

- **Story 1** has no story dependency. It writes `commands/writ.md` and the command-file tests. At the spec level, `2026-10-22-prompting-guide` lands first, because the command cites the guide's path and `check_referenced_paths` needs the file to exist. Until Story 2 registers the command, `check_manifest` reports it as unregistered.
- **Story 2** needs Story 1. It registers `/writ` on every catalog and surface, regenerates `SKILL.md` and `claude-code/CLAUDE.md`, rewrites README Quick Start, and corrects the Claude Code `todo_write` row.
- **Story 3** needs both. It pins the command's structure in `eval-command-structure.py`, resolves the in-your-own-words issue, and records the routing fixture run.
