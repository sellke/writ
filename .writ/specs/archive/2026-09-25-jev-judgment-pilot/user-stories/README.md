# User Stories: Jev Judgment Pilot

> Spec: [`../spec.md`](../spec.md) · Lite: [`../spec-lite.md`](../spec-lite.md) · Technical: [`../sub-specs/technical-spec.md`](../sub-specs/technical-spec.md)

| # | Story | Status | Priority | Dependencies | Criteria | Tasks | Progress |
|---|---|---|---|---|---|---|---|
| 1 | [ADR-027 and Opt-in Resolution](story-1-adr-and-opt-in.md) | Completed ✅ | High | None | 5 | 6 | 6/6 |
| 2 | [Client Transport and eval Check](story-2-client-transport.md) | Completed ✅ | High | Story 1 | 5 | 7 | 7/7 |
| 3 | [Spec-Findings Producer and Step 2.6c Cascade](story-3-spec-findings-cascade.md) | Completed ✅ | High | Story 2 | 5 | 7 | 7/7 |
| 4 | [Calibration Fixtures and Thresholds](story-4-calibration.md) | Completed ✅ | Medium | Story 3 | 4 | 7 | 7/7 |
| 5 | [Gate 3 Shadow Judgment and Agreement Report](story-5-gate3-shadow.md) | Completed ✅ | Medium | Story 2 | 5 | 7 | 7/7 |
| 6 | [Provider Setup Prompt](story-6-setup-prompt.md) | Completed ✅ | High | Story 3 | 5 | 6 | 6/6 |

**Total:** 6 stories · 29 criteria · 40 tasks · 100% complete

## Dependencies

- **Story 1** stands alone: the ADR, plus `status`, the first subcommand of `jev-judge.py`.
- **Story 2** builds the transport, which every later subcommand calls.
- **Stories 3 and 5** both depend only on Story 2, so they can run in parallel. They touch different command files: Story 3 edits `create-spec.md` and `verify-spec.md`; Story 5 edits `implement-story.md` and `evaluator-agent.md`. Both add subcommands to `scripts/jev-judge.py` and tests to `scripts/tests/test_jev_judge.py`, so merge them one after the other.
- **Story 4** calibrates the thresholds that Story 3's `spec-findings` applies.
- **Story 6** adds the one-time setup prompt. It edits `create-spec.md` Step 2.6c, which Story 3 also edits, so it runs after Story 3.

## Batches

1. Story 1
2. Story 2
3. Stories 3 and 5 (parallel; serialize edits to the shared script)
4. Stories 4 and 6 (parallel; serialize edits to the shared script)
