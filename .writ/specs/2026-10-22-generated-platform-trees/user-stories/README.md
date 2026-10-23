# User Stories: Generated Platform Trees

> Spec: [`../spec.md`](../spec.md)

| # | Story | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---|---|
| 1 | [Adapter Table Parser and Parity Repairs](story-1-adapter-parser-and-parity-repairs.md) | Completed ✅ | High | None | 7 | 7/7 |
| 2 | [Driver Write Mode for the Cursor and Claude Code Root Files](story-2-driver-write-mode-cursor-and-claude-code.md) | Not Started | High | Story 1 | 7 | 0/7 |
| 3 | [Generated Codex Template](story-3-generated-codex-template.md) | Not Started | High | Story 2 | 7 | 0/7 |
| 4 | [`--check`, Coverage, Tokens, and Eval Wiring](story-4-check-coverage-tokens-and-eval-wiring.md) | Not Started | High | Story 3 | 7 | 0/7 |
| 5 | [Install Evidence and Issue Closure](story-5-install-evidence-and-issue-closure.md) | Not Started | High | Story 4 | 5 | 0/5 |

**Total:** 5 stories, 33 tasks, 24 acceptance criteria.

## Dependencies

- **Story 1** has no story dependency. It writes the adapter parser, repairs the four tool tables (Codex `file_search`, OpenClaw `readonly` fold, `Plan Mode` rows), and points three commands at the adapter row. At the spec level, `2026-10-22-rendering-delegation-rows` (final canvas rows and records) and `2026-10-22-front-door` (`/writ` in the catalogs) land first.
- **Story 2** needs Story 1's parser. It generates `cursor/writ.mdc` and the Claude Code map slot and makes the driver call the existing generators.
- **Story 3** needs Story 2's driver and map function. It generates `codex/AGENTS.md.template`.
- **Story 4** needs Story 3 so `--check` covers every generated file. It adds coverage, tokens, the fixture target, and the eval check, and rewrites the vendor hits the first `coverage` run finds.
- **Story 5** needs Story 4 (`check_platform_trees` must pass on the tree it installs from). It proves the map reaches installed projects and closes the issue.
