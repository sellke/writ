# User Stories: Claude Code Parity

> Spec: [`../spec.md`](../spec.md)
> Amended 2026-10-20 (maintainer-approved): Story 4 added; Story 3 gained AC-3.5 and task 3.6.

| # | Story | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---|---|
| 1 | [Generate the CLAUDE.md Template from the Manifest](story-1-generate-claude-md-template.md) | Not Started | High | None | 7 | 0/7 |
| 2 | [Install the System Instructions and Import Line on Claude Code](story-2-install-system-instructions-on-claude.md) | Not Started | High | Story 1 | 7 | 0/7 |
| 3 | [Correct the Claude Code Adapter](story-3-correct-claude-code-adapter.md) | Not Started | Medium | None | 7 | 0/7 |
| 4 | [Keep CLAUDE.md User-Owned on Uninstall and Reinstall](story-4-claude-md-ownership-on-uninstall-and-reinstall.md) | Not Started | High | Story 2 | 7 | 0/7 |

**Total:** 4 stories, 28 tasks, 19 acceptance criteria.

## Dependencies

- **Stories 1 and 3** are independent and can run in parallel. Story 1 edits the generator, the template, `eval.sh`, and the ship filter. Story 3 edits only `adapters/claude-code.md` and its new test.
- **Story 2** needs Story 1. Its install tests read the import line from the regenerated `claude-code/CLAUDE.md`, and both stories edit `scripts/install.sh` and `scripts/update.sh`.
- **Story 4** needs Story 2. Both edit the Claude branch of the `EXTRA_FILES` block in `scripts/uninstall.sh` and the Claude bullets of `commands/uninstall-writ.md` and `commands/reinstall-writ.md`. Story 4 shares no file with Story 3; the adapter's manual install fix is Story 3's AC-3.4.
- **Spec level:** the whole spec runs after `2026-10-20-harness-cuts`, which edits the same lifecycle scripts first.
