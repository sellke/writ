---
category: lessons
tags: [story-decomposition, boundaries, context-engine]
created: 2026-04-24
related_artifacts:
  - .writ/specs/2026-03-27-context-engine/drift-log.md
  - commands/implement-story.md
  - .writ/specs/2026-04-24-phase4-production-grade-substrate/sub-specs/technical-spec.md
---

# Story Overlap Needs Explicit Boundaries

## TL;DR

When adjacent stories can plausibly touch the same files, the implementation pipeline needs an explicit boundary map before coding starts.

## Context

- The Context Engine work surfaced overlap between story responsibilities.
- Without a boundary map, an agent can solve the current story by silently absorbing another story's scope.
- Phase 4 Story 1 adds knowledge loading beside the existing boundary computation rather than replacing it.

## Detail

Use story tasks and technical-spec file maps to identify owned, readable, and out-of-scope files. Treat boundaries as review signals, not hard locks: a justified deviation can proceed, but it must be visible to the reviewer.

This lesson is especially relevant when adding new orchestration context. More context should sharpen scope, not blur ownership.

## Related

- [Context Engine drift log](../../specs/2026-03-27-context-engine/drift-log.md)
- [Implement Story command](../../../commands/implement-story.md)
