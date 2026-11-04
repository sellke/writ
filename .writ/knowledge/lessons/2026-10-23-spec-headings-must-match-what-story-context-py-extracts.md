---
category: lessons
tags: [phase-close, create-spec, story-context]
created: 2026-10-23
related_artifacts:
  - scripts/story-context.py
---

# Spec headings must match what story-context.py extracts

## TL;DR

Write spec.md's experience and rules sections under the exact headings scripts/story-context.py extracts (## 🎯 Experience Design and the emoji Business Rules heading); a plain heading such as ## Business Rules (Expanded) makes bracket-form context hints resolve to nothing, and story generators fall back to extended references.

## Context

Recorded at phase close from evidence-bound knowledge writeback.

**Cited evidence:**

- All five Phase 14 spec.md files used plain headings; story generators reported unresolved bracket hints and switched to extended references
- scripts/story-context.py

## Related

- `scripts/story-context.py`
