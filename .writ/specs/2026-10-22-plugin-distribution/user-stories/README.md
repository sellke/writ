# User Stories: Plugin Distribution

> Spec: [`../spec.md`](../spec.md)

| # | Story | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---|---|
| 1 | [Verify Both Plugin Formats and Decide the Layout](story-1-verify-plugin-formats-and-decide-layout.md) | Completed ✅ | High | None | 7 | 7/7 |
| 2 | [Claude Code Plugin](story-2-claude-code-plugin.md) | Completed ✅ | High | Story 1 | 7 | 7/7 |
| 3 | [Cursor Plugin](story-3-cursor-plugin.md) | Not Started | High | Story 1, Story 2 | 6 | 0/6 |
| 4 | [Scaffold Script, `/initialize` Step 0, and ADR-031](story-4-scaffold-script-initialize-and-adr-031.md) | Completed ✅ | High | Story 1 | 6 | 6/6 |
| 5 | [Smoke Test Across Five Targets, README Install Order, and Live-Run Evidence](story-5-smoke-test-and-readme.md) | Not Started | High | Story 2, Story 3, Story 4 | 7 | 0/7 |

**Total:** 5 stories, 33 tasks, 25 acceptance criteria.

## Dependencies

- **Story 1** has no story dependency and runs alone: it fills the Verification Record and decides layout, Prime Directive carrier, token classes, and namespacing. At the spec level, `2026-10-22-generated-platform-trees` lands first (`gen-platform-trees.py`, `TARGETS`, `--check`).
- **Story 2** and **Story 4** need Story 1 and touch disjoint files, so they may run as one batch.
- **Story 3** needs Story 2 as well: both add targets to `TARGETS` and both extend `scripts/tests/test_plugin_distribution.py` (which Story 1 creates).
- **Story 5** needs Stories 2, 3, and 4: the smoke test runs against the plugin directories and the scaffold script, and the README order follows its recorded results.
