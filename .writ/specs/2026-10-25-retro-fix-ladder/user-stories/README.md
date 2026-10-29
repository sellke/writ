# User Stories: Retro Fix Ladder

> Spec: [`../spec.md`](../spec.md)

| # | Story | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---|---|
| 1 | [retro-check.py, the Rule Table and Ladder Checker](story-1-retro-check-script.md) | Completed ✅ | High | None | 7 | 7/7 |
| 2 | [Seed This Repository's Rule-to-Enforcer Table](story-2-seed-rule-table.md) | Not Started | High | Story 1 | 6 | 0/6 |
| 3 | [/retro Fix Ladder, Proof, Rule Table, and Signal Retirement](story-3-retro-ladder-and-table.md) | Not Started | High | Story 1, Story 2 | 7 | 0/7 |
| 4 | [/refresh-command Execution-Failure and Used-Skill Criteria](story-4-refresh-command-criteria.md) | Completed ✅ | High | None | 7 | 7/7 |

**Total:** 4 stories, 27 tasks, 19 acceptance criteria. **Progress:** 14/27 tasks (52%).

## Dependencies

- **Story 1** has no dependency. It ships `scripts/retro-check.py`, its tests, and the agent CLI contract row.
- **Story 2** needs Story 1: its test runs `retro-check.py --table` on the seeded `.writ/retros/rule-enforcers.md`.
- **Story 3** needs Stories 1 and 2: `commands/retro.md` cites the script and the table path, and `check_referenced_paths` fails while the table file is missing.
- **Story 4** has no dependency and can run beside any other story. Stories 3 and 4 both regenerate the platform trees, but they change different generated files.
