# User Stories: Agent CLI Contract

> Spec: [`../spec.md`](../spec.md)

| # | Story | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---|---|
| 1 | [Contract Doc and ADR-029 Amendment](story-1-contract-doc-and-adr-amendment.md) | Completed ✅ | High | None | 6 | 6/6 |
| 2 | [Stop Shipping Dev-Only Scripts](story-2-stop-shipping-dev-scripts.md) | Completed ✅ | High | None | 7 | 7/7 |
| 3 | [Agent CLI Contract Test](story-3-contract-test.md) | Completed ✅ | High | Story 1, Story 2 | 7 | 7/7 |
| 4 | [Bring Data Tools and Python Check Tools into Conformance](story-4-conformance-fixes.md) | Completed ✅ | Medium | Story 3 | 7 | 7/7 |
| 5 | [Bring Shell Scripts and app-verify into Conformance](story-5-shell-and-app-verify-conformance.md) | Not Started | Medium | Story 4 | 7 | 0/7 |

**Total:** 5 stories, 34 tasks, 25 acceptance criteria.

## Dependencies

- **Stories 1 and 2** are independent and can run in parallel. Story 1 writes the classification table. Story 2 fixes the shipped set the table must match.
- **Story 3** needs both: its completeness test compares the table (Story 1) to the final shipped set (Story 2).
- **Story 4** needs Story 3: it fixes the Python entries in the `KNOWN_VIOLATIONS` list the first test run produces.
- **Story 5** needs Story 4: it fixes the shell scripts and `app-verify.py`, empties the list, and closes the origin issue. Added 2026-10-12 when the maintainer kept the check rule strict (drift-log DEV-001, DEV-002).
