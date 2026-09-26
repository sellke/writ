# User Stories: Architecture Lint and Drift-Guard Follow-ups

> Spec: [`../spec.md`](../spec.md) · Lite: [`../spec-lite.md`](../spec-lite.md) · Technical: [`../sub-specs/technical-spec.md`](../sub-specs/technical-spec.md)

| # | Story | Status | Priority | Dependencies | Criteria | Tasks | Progress |
|---|---|---|---|---|---|---|---|
| 1 | [Codex TOML Freshness](story-1-codex-toml-freshness.md) | Completed ✅ | High | None | 5 | 7 | 7/7 |
| 2 | [Issue-Closure Convention](story-2-issue-closure.md) | Completed ✅ | Medium | None | 4 | 7 | 7/7 |
| 3 | [Ruleset Detection and Gate 2 Wiring](story-3-ruleset-detection-gate2.md) | Completed ✅ | High | None | 5 | 6 | 6/6 |
| 4 | [Architecture-Lint Guide and ADR Hook](story-4-guidance-and-adr-hook.md) | Completed ✅ | Medium | Story 3 | 4 | 6 | 6/6 |

**Total:** 4 stories · 18 criteria · 26 tasks · 100% complete

## Dependencies

- **Story 4** documents what Story 3's `arch-lint.py detect` finds; the helper is authoritative where they differ. Story 3's `arch-lint: none` line links the guide Story 4 creates.
- **Stories 1, 2, 3** touch disjoint files (generator + `eval.sh`; `status.md` + snapshot skill + `create-issue.md`; `arch-lint.py` + `implement-story.md` + ratchet tests).

## Batches

1. Stories 1, 2, 3
2. Story 4
