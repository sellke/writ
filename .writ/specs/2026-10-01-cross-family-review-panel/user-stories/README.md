# User Stories — Cross-Family Review Panel

> Spec: [`../spec.md`](../spec.md) · Technical: [`../sub-specs/technical-spec.md`](../sub-specs/technical-spec.md)

## Summary

| # | Story | Status | Tasks | Progress | Dependencies |
|---|---|---|---|---|---|
| 1 | [Panel Config, Vendor Table, Status, and Amendments](story-1-panel-config-and-status.md) | Completed ✅ | 7 | 7/7 | None |
| 2 | [Tally, Matching Rule, and Tagged Reviewer Output](story-2-tally-and-tagged-output.md) | Not Started | 7 | 0/7 | Story 1 |
| 3 | [Gate 3 Wiring, `--panel`, and Eval Pins](story-3-gate-3-wiring.md) | Not Started | 7 | 0/7 | Stories 1, 2 |
| 4 | [Retrospective Trial Harness and Report](story-4-trial-harness.md) | Not Started | 7 | 0/7 | Story 2 |
| 5 | [Run the Trial and Act on the Verdict](story-5-run-trial-and-act.md) | Not Started | 7 | 0/7 | Stories 3, 4 |

**Total:** 5 stories, 35 tasks, 25 acceptance criteria. Progress: 7/35.

## Dependencies

- **Story 1** is the base: the config contract, vendor table, and `status` every later story calls, plus the ADR-028 and adapter amendments.
- **Story 2** adds `tally` and the tagged agent output it parses. It reuses Story 1's vendor table.
- **Stories 3 and 4** both depend on Story 2 and are independent of each other: Story 3 wires the panel into Gate 3; Story 4 builds the trial harness on the same parser.
- **Story 5** needs both: the trial runs the real Gate 3 prompt through the harness, and its `remove` branch deletes what Story 3 wired.

## Quick Links

- [Story 1](story-1-panel-config-and-status.md) · [Story 2](story-2-tally-and-tagged-output.md) · [Story 3](story-3-gate-3-wiring.md) · [Story 4](story-4-trial-harness.md) · [Story 5](story-5-run-trial-and-act.md)
