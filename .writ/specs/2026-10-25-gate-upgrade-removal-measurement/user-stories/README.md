# User Stories: Gate Upgrade Removal Measurement

> Spec: [`../spec.md`](../spec.md)

| # | Story | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---|---|
| 1 | [Trial Harness: init and prepare](story-1-harness-init-and-prepare.md) | Completed ✅ | High | None | 7 | 7/7 |
| 2 | [Trial Harness: record, sheet, label, and report](story-2-harness-record-sheet-label-report.md) | Completed ✅ | High | Story 1 | 7 | 7/7 |
| 3 | [Run the Arms and Hand Off for Labeling](story-3-run-arms-and-handoff.md) | Completed ✅ | Medium | Story 2 | 7 | 7/7 |
| 4 | [Act on the Labeled Trial (Human-Gated)](story-4-act-on-labeled-trial.md) | Not Started | Medium | Story 3 | 7 | 0/7 |

**Total:** 4 stories, 28 tasks, 20 acceptance criteria.

## Dependencies

- **Story 1** has no story dependency. Its unit tests use fixtures, so it can land before the three dependency specs; the real `init` run belongs to Story 3.
- **Story 2** needs Story 1's skeleton and checkout.
- **Story 3** needs Story 2 and all three dependency specs complete (their switches must exist). It ends at `rating-handoff.md`.
- **Story 4** needs Story 3 and a human: the maintainer fills `labeling-sheet.md` and runs `label --labeled-by "<name>"`. `/implement-spec` stops at task 4.1 until `labeled_by` is set, reports that the story waits on human input, and does not mark it complete or skipped.
