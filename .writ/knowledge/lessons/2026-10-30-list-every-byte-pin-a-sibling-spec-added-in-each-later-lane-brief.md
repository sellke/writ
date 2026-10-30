---
category: lessons
tags: [phase-close, implement-phase, byte-budget]
created: 2026-10-30
related_artifacts:
  - scripts/tests/test_review_route_rigor.py
  - scripts/tests/test_governor_enforcement.py
---

# List every byte pin a sibling spec added in each later lane brief

## TL;DR

A spec can leave a whole-file size cap behind in its own test module, not only in KNOWN_OVER_BUDGET. review-route-rigor pinned IMPLEMENT_STORY_CAP at the file size plus 5 bytes in scripts/tests/test_review_route_rigor.py, so the next lane's one-line Gate 1 addition broke it, and the brief had named only the governor pin. After each lane merges, grep the new tests for size assertions on shared command files and carry each pin, with its current value, into every later lane brief.

## Context

Recorded at phase close from evidence-bound knowledge writeback.

**Cited evidence:**

- scripts/tests/test_review_route_rigor.py
- scripts/tests/test_governor_enforcement.py
- lane 4 (repro-first-bug-fixing) report: IMPLEMENT_STORY_CAP 40234 -> 40682, not named in the brief

## Related

- `scripts/tests/test_review_route_rigor.py`
- `scripts/tests/test_governor_enforcement.py`
