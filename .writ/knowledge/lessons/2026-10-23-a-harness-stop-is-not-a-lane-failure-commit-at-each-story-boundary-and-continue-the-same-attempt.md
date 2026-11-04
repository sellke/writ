---
category: lessons
tags: [phase-close, implement-phase, lanes]
created: 2026-10-23
related_artifacts:
  - .writ/specs/2026-10-22-rendering-delegation-rows/user-stories/story-1-claude-code-verification.md
  - .writ/specs/2026-10-22-generated-platform-trees/user-stories/story-4-check-coverage-tokens-and-eval-wiring.md
---

# A harness stop is not a lane failure: commit at each story boundary and continue the same attempt

## TL;DR

Lane workers get cut off mid-story by run budgets, forced handbacks, and spend limits, none of which is a failure of the work. Commit each story the moment its gates pass, and when a worker stops without a failure of the work itself, continue the same attempt (resume the agent, or brief a fresh worker from the lane's on-disk state and notes) instead of classifying it and spending the one permitted retry.

## Context

Recorded at phase close from evidence-bound knowledge writeback.

**Cited evidence:**

- Phase 14 state: 2026-10-22-rendering-delegation-rows and 2026-10-22-generated-platform-trees each spent their retry after a mid-gate harness stop, not a failed gate
- Phase 14 state: 2026-10-22-plugin-distribution was continued at attempts 1 after a spend-limit stop and finished 5/5
- .writ/specs/2026-10-22-rendering-delegation-rows/user-stories/story-1-claude-code-verification.md

## Related

- `.writ/specs/2026-10-22-rendering-delegation-rows/user-stories/story-1-claude-code-verification.md`
- `.writ/specs/2026-10-22-generated-platform-trees/user-stories/story-4-check-coverage-tokens-and-eval-wiring.md`
