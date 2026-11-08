---
category: lessons
tags: [phase-close, testing, multi-spec]
created: 2026-11-06
related_artifacts:
  - .writ/specs/2026-11-06-ship-watch-and-merge/drift-log.md
  - scripts/tests/test_pr_ready.py
  - scripts/tests/test_verify_ledger.py
---

# Do not pin a placeholder a later spec fills

## TL;DR

When one spec ships a placeholder that a later spec in the same phase fills (a Callers cell, a stub row, a TODO value), the first spec's tests should check the placeholder's shape, not its exact text. Pinning the text verbatim breaks the full suite when the second spec lands, and the repair arrives at close-out without a story to own it.

## Context

Recorded at phase close from evidence-bound knowledge writeback.

**Cited evidence:**

- .writ/specs/2026-11-06-ship-watch-and-merge/drift-log.md DEV-011
- commit b3d8d16 updated CALLERS constants in scripts/tests/test_pr_ready.py and scripts/tests/test_verify_ledger.py

## Related

- `.writ/specs/2026-11-06-ship-watch-and-merge/drift-log.md`
- `scripts/tests/test_pr_ready.py`
- `scripts/tests/test_verify_ledger.py`
