# User Stories: Gate Upgrade Removal Measurement

> Spec: [`../spec.md`](../spec.md)

| # | Story | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---|---|
| 1 | [Trial Harness: init and prepare](story-1-harness-init-and-prepare.md) | Completed ✅ | High | None | 7 | 7/7 |
| 2 | [Trial Harness: record, sheet, label, and report](story-2-harness-record-sheet-label-report.md) | Completed ✅ | High | Story 1 | 7 | 7/7 |
| 3 | [Run the Arms and Hand Off for Labeling](story-3-run-arms-and-handoff.md) | Completed ✅ | Medium | Story 2 | 7 | 7/7 |
| 4 | [Act on the Labeled Trial (Human-Gated)](story-4-act-on-labeled-trial.md) | Completed ✅ | Medium | Story 3 | 6 | 6/6 |
| 5 | [Run the Repro First Substitute Trial](story-5-repro-first-substitute-trial.md) | Completed ✅ | Medium | Story 3, Story 4 | 7 | 7/7 |
| 6 | 🆕 [Act on the Repro First Verdict](story-6-act-on-repro-first-verdict.md) | Not Started | Medium | Story 5 | 7 | 0/7 |

**Total:** 6 stories, 41 tasks, 29 acceptance criteria (AC-4.5 retired 2026-11-09).

## Dependencies

- **Story 1** has no story dependency. Its unit tests use fixtures, so it can land before the three dependency specs; the real `init` run belongs to Story 3.
- **Story 2** needs Story 1's skeleton and checkout.
- **Story 3** needs Story 2 and all three dependency specs complete (their switches must exist). It ends at `rating-handoff.md`.
- **Story 4** needs Story 3 and a human: the maintainer fills `labeling-sheet.md` and runs `label --labeled-by "<name>"`. `/implement-spec` stops at task 4.1 until `labeled_by` is set, reports that the story waits on human input, and does not mark it complete or skipped. Its harness-deletion task moved to Story 6 on 2026-11-09.
- **Story 5** needs the harness (Story 3) and Story 4's report commit `ef0c418`. It runs only the `off-1`, `off-2`, and `repro-first` arms on the substitute baseline (spec.md Business Rule 14) and ends at `rating-handoff-repro-first.md`.
- **Story 6** needs Story 5. Its labels are delegated to the assistant for this run only (Business Rule 9). It deletes the harness last, and only when Repro First is `keep` or `remove`.
