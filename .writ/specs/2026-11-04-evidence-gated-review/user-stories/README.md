# User Stories: Evidence-Gated Review

> Spec: [`../spec.md`](../spec.md) · Lite: [`../spec-lite.md`](../spec-lite.md) · Technical: [`../sub-specs/technical-spec.md`](../sub-specs/technical-spec.md)

## Summary

| # | Story | Status | Priority | Tasks | Progress |
|---|---|---|---|---|---|
| 1 | [ADR-032 and the review-surface inventory](story-1-adr-032-review-surface-inventory.md) | Completed ✅ | High | 7 | 7/7 |
| 2 | [Evidence skill and the `evidence` subcommand](story-2-evidence-skill-and-subcommand.md) | Completed ✅ | High | 7 | 7/7 |
| 3 | [Gate 3 wiring for evidence-gated findings](story-3-gate-3-wiring.md) | Completed ✅ | High | 6 | 6/6 |
| 4 | [Confirmed repros become regression tests](story-4-repro-as-regression-test.md) | Completed ✅ | High | 7 | 7/7 |
| 5 | [Evidence gating in `/review`](story-5-review-evidence-gating.md) | Completed ✅ | Medium | 7 | 7/7 |
| 6 | [Raise the Safety Fact floor to `tested`](story-6-raise-safety-fact-floor.md) | Not Started | Medium | 7 | 0/7 |
| 7 | [Remove the review panel and close out the roadmap](story-7-remove-panel-close-roadmap.md) | Not Started | Medium | 7 | 0/7 |

**Total:** 7 stories, 48 tasks, 35 acceptance criteria.

## Dependencies

```
1 → 2 → 3 → 4 ─┐
        └→ 5 ──┴→ 6 → 7
```

- **Story 1** writes ADR-032 first, so later stories can link to it.
- **Story 2** builds the skill and `review-override.py evidence`. Stories 3 and 5 both call it.
- **Stories 3 and 4** both edit Gate 3 of `commands/implement-story.md` and must run in that order.
- **Story 5** edits only `commands/review.md` and the review surface of the script. It can run in parallel with Stories 3 and 4.
- **Story 6** raises the Safety Fact floor. It follows Stories 4 and 5, which also edit `scripts/review-override.py`. The reviewer filters stay (spec.md → Amendment).
- **Story 7** runs last. It removes the panel and writes the shipped-file scan test for the panel names.

Gate 0 text in `commands/implement-story.md` (Story 7 removes the `--panel` route qualifier) overlaps `2026-10-25-design-divergence`. Land Story 7 after that spec's Story 6, or rebase onto it.
