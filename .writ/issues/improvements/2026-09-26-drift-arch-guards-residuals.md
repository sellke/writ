# Residual gaps from drift-arch-guards reviews

> **Type:** Improvement
> **Priority:** Low
> **Effort:** Small
> **Created:** 2026-09-26
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

Gate 3 reviews of `2026-09-26-drift-arch-guards` named four minor gaps, none blocking.

## Current State

1. `commands/implement-story.md` does not say what the `gate3-route:` line shows when the two-fail escalation switches a story to `--full-pipeline` partway through.
2. `commands/implement-spec.md` Step 4.2 does not say what the report shows when `drift-format.py summary` returns `unverifiable`.
3. `drift-format.py summary` skips entries whose severity is not exactly `Small`/`Medium`/`Large` without warning (DEV-006); `check` catches them only if it runs on that story.
4. `scripts/tests/test_evaluator_agent_contract.py::test_review_agent_not_in_story_edit_set` reads the uncommitted working tree, so it fails during any legitimate edit to `agents/review-agent.md` until commit.

## Expected Outcome

One line of prose each for 1 and 2; a `reason:` line or count of skipped entries for 3; scope or remove the guard in 4.

## Relevant Files

- `commands/implement-story.md`, `commands/implement-spec.md`
- `scripts/drift-format.py`
- `scripts/tests/test_evaluator_agent_contract.py`
