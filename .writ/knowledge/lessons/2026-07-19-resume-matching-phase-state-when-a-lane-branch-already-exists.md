---
category: lessons
tags: [phase-close, implement-phase, resume]
created: 2026-07-19
related_artifacts:
  - scripts/phase-state.py
  - .writ/docs/phase-execution-state-format.md
---

# Resume matching phase state when a lane branch already exists

## TL;DR

When /implement-phase hits lane_collision, prefer reconciling an existing phase-execution-*.json that owns the lane over initializing a new empty state that cannot create-lane.

## Context

Recorded at phase close from evidence-bound knowledge writeback.

**Cited evidence:**

- .writ/state/phase-execution-20260719-121255.json
- scripts/phase-state.py

## Related

- `scripts/phase-state.py`
- `.writ/docs/phase-execution-state-format.md`
