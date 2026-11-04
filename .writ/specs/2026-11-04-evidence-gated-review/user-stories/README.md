# User Stories: Evidence-Gated Review

> Spec: [`../spec.md`](../spec.md) · Lite: [`../spec-lite.md`](../spec-lite.md) · Technical: [`../sub-specs/technical-spec.md`](../sub-specs/technical-spec.md)

## Summary

| # | Story | Status | Priority | Tasks | Progress |
|---|---|---|---|---|---|
| 1 | [ADR-032 and the review-surface inventory](story-1-adr-032-review-surface-inventory.md) | Not Started | High | 7 | 0/7 |
| 2 | [Evidence skill and the `evidence` subcommand](story-2-evidence-skill-and-subcommand.md) | Not Started | High | 7 | 0/7 |
| 3 | [Gate 3 wiring for evidence-gated findings](story-3-gate-3-wiring.md) | Not Started | High | 6 | 0/6 |
| 4 | [Confirmed repros become regression tests](story-4-repro-as-regression-test.md) | Not Started | High | 7 | 0/7 |
| 5 | [Evidence gating in `/review`](story-5-review-evidence-gating.md) | Not Started | Medium | 7 | 0/7 |
| 6 | [Remove the reviewer filters and raise the Safety Fact floor](story-6-remove-filters-raise-floor.md) | Not Started | Medium | 7 | 0/7 |
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
- **Story 6** has a precondition outside this spec. `/edit-spec` must first narrow `2026-10-25-gate-upgrade-removal-measurement` to Gate 0 Divergence and Repro First. If that hasn't happened, the story's first task stops with a blocker.
- **Story 7** runs last. Its scan extends Story 6's scan test.

Gate 0 text in `commands/implement-story.md` (Story 7 removes the `--panel` route qualifier) overlaps `2026-10-25-design-divergence`. Land Story 7 after that spec's Story 6, or rebase onto it.
