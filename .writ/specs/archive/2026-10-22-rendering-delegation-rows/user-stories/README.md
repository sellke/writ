# User Stories: Rendering-Delegation Rows

> Spec: [`../spec.md`](../spec.md)

| # | Story | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---|---|
| 1 | [Claude Code Live Verification and Record](story-1-claude-code-verification.md) | Completed ✅ | High | None | 6 | 6/6 |
| 2 | [Cursor, Codex, and OpenClaw Rows from First-Party Docs with UAT Protocols](story-2-docs-based-rows-and-uat-protocols.md) | Completed ✅ | High | Story 1 | 7 | 7/7 |
| 3 | [Verification-Record Tests, prototype.md Reconciliation, and Issue Note](story-3-tests-and-reconciliation.md) | Completed ✅ | High | Story 1, Story 2 | 7 | 7/7 |

**Total:** 3 stories, 20 tasks, 15 acceptance criteria.

## Dependencies

- **Story 1** has no dependency. It runs the Claude Code protocol in the lane, writes the `adapters/claude-code.md` record, and adds `test_verification_records` with the `claude-code` case.
- **Story 2** needs Story 1: both add cases to the same test function in `scripts/tests/test_platform_neutral_names.py`. Story 2 edits the other three adapters and the UAT protocols, and never touches `adapters/claude-code.md`.
- **Story 3** needs both. It adds the negative test case, reconciles `commands/prototype.md` Step 2.5 against the four records, and appends `### Verification` to the origin issue's `## Resolution`.
