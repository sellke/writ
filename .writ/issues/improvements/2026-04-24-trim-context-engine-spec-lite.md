# Trim Context Engine Spec Lite

> **Type:** Improvement
> **Priority:** Low
> **Effort:** Small
> **Created:** 2026-04-24
> **spec_ref:** .writ/specs/2026-03-27-context-engine/spec-lite.md

## TL;DR

The Context Engine `spec-lite.md` predates Story 5's 100-line eval budget and currently exceeds it. Story 5 grandfathers it with an `eval-exempt` comment to avoid unrelated churn during eval rollout.

## Current State

- `.writ/specs/2026-03-27-context-engine/spec-lite.md` is 121 lines.
- Story 5's `length` check now enforces `spec-lite.md` files at 100 lines or less.
- The file is a shipped Phase 3 artifact; trimming it is not required for Eval Tier 1 to ship safely.

## Expected Outcome

- Trim the lite spec to 100 lines or less while preserving the coding, review, and testing context that agents still need.
- Remove the `eval-exempt: length` comment once the file is under budget.

## Relevant Files

- `.writ/specs/2026-03-27-context-engine/spec-lite.md`
- `scripts/eval.sh`

## Related Issues

- None.

## Notes

- This is a grandfathered pre-existing violation from the post-Stories-1-4 surface.
- Do not broaden Story 5 into a rewrite of shipped Context Engine documentation.
