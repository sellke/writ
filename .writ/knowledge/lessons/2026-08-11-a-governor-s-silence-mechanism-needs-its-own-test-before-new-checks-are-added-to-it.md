---
category: lessons
tags: [phase-close]
created: 2026-08-11
related_artifacts:
  - scripts/eval-leanness.py
  - .writ/specs/archive/2026-08-11-governor-instrumentation
---

# A governor's silence mechanism needs its own test before new checks are added to it

## TL;DR

A governor's silence mechanism needs its own test before new checks are added to it.

## Context

Recorded at phase close from evidence-bound knowledge writeback (commit a9b3ed8; payload rejoined 2026-09-06).

**Cited evidence:**

- scripts/eval-leanness.py:527,533,540,603 pre-fix; 2026-08-11-governor-instrumentation Story 1; verified post-fix by lowering a ceiling by 1 (warning returns naming the ceiling) and by injecting a legacy unbounded string (warns per-metric, silences nothing).

## Related

- `scripts/eval-leanness.py`
- `.writ/specs/archive/2026-08-11-governor-instrumentation`
