# User Stories: Agent CLI Contract

> Spec: [`../spec.md`](../spec.md)

| # | Story | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---|---|
| 1 | [Contract Doc and ADR-029 Amendment](story-1-contract-doc-and-adr-amendment.md) | Completed ✅ | High | None | 6 | 6/6 |
| 2 | [Stop Shipping Dev-Only Scripts](story-2-stop-shipping-dev-scripts.md) | Not Started | High | None | 7 | 0/7 |
| 3 | [Agent CLI Contract Test](story-3-contract-test.md) | Not Started | High | Story 1, Story 2 | 7 | 0/7 |
| 4 | [Bring Violating Scripts into Conformance](story-4-conformance-fixes.md) | Not Started | Medium | Story 3 | 7 | 0/7 |

**Total:** 4 stories, 27 tasks, 20 acceptance criteria.

## Dependencies

- **Stories 1 and 2** are independent and can run in parallel. Story 1 writes the classification table. Story 2 fixes the shipped set the table must match.
- **Story 3** needs both: its completeness test compares the table (Story 1) to the final shipped set (Story 2).
- **Story 4** needs Story 3: it works through the `KNOWN_VIOLATIONS` list the first test run produces, and ends with the list empty.
