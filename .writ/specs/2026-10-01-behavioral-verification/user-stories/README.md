# User Stories: Behavioral Verification

> Spec: [spec.md](../spec.md) · Lite: [spec-lite.md](../spec-lite.md) · Technical: [technical-spec.md](../sub-specs/technical-spec.md)

## Summary

| # | Story | Status | Tasks | Progress | Dependencies |
|---|---|---|---|---|---|
| 1 | [Recipe format, validator, and product amendments](story-1-recipe-format-and-validator.md) | Completed ✅ | 7 | 7/7 | None |
| 2 | [/create-uat-plan drafts the recipe and binds scenarios](story-2-uat-plan-recipe-and-binding.md) | Completed ✅ | 7 | 7/7 | Story 1, Story 3 |
| 3 | [Run script and fixture app](story-3-run-script-and-fixture.md) | Completed ✅ | 7 | 7/7 | Story 1 |
| 4 | [Gate 4.5 becomes behavioral verification](story-4-gate-4-5-behavioral-verification.md) | Completed ✅ | 7 | 7/7 | Story 3 |
| 5 | [exit-criteria.py evidence check and eval check](story-5-evidence-exit-criteria.md) | Completed ✅ | 7 | 7/7 | Story 2 |

**Total:** 5 stories, 35 tasks, 100% complete.

## Dependencies

- **Story 1** defines the recipe grammar and parser that every other story reads.
- **Story 3** builds the run mechanics and fixture on Story 1's parser.
- **Stories 2 and 4** are the two consumers of the run script. Both depend on Story 3 and are independent of each other.
- **Story 5** reads the scenario `**Verification:**` lines Story 2 defines and closes the spec's success criteria end to end.

Suggested order: 1 → 3 → (2 ∥ 4) → 5.
