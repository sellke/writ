# User Stories: Platform-Neutral Names

> Spec: [`../spec.md`](../spec.md)

| # | Story | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---|---|
| 1 | [Canvas-Preview Capability in `/prototype` and the Four Adapters](story-1-canvas-preview-capability.md) | Not Started | High | None | 7 | 0/7 |
| 2 | [Rename `/design` to `/writ-design` Across Every Reference](story-2-rename-writ-design.md) | Not Started | High | Story 1 | 7 | 0/7 |
| 3 | [Upgrade-Path Test, Reference Gate, and Issue Resolutions](story-3-upgrade-path-and-reference-gate.md) | Not Started | High | Story 2 | 6 | 0/6 |

**Total:** 3 stories, 20 tasks, 15 acceptance criteria.

## Dependencies

- **Story 1** has no story dependency. At the spec level, `2026-10-20-claude-code-parity` lands first, because it rewrites parts of `adapters/claude-code.md`.
- **Story 2** needs Story 1. Both edit `commands/prototype.md` and `adapters/cursor.md`, so running them in parallel would conflict. Story 2 also needs the parity spec's `claude-code/CLAUDE.md` generator.
- **Story 3** needs Story 2. Its install, update, and gate tests read the renamed tree. Its modified-file criterion (AC-3.3) also needs `2026-10-20-ci-and-update-integrity`, which makes `update.sh` keep and warn about a modified stale file in every category.
