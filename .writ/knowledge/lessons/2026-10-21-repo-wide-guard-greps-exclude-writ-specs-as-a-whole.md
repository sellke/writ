---
category: lessons
tags: [phase-close, eval]
created: 2026-10-21
related_artifacts: []
---

# Repo-wide guard greps exclude .writ/specs as a whole

## TL;DR

A repo-wide guard grep that pins the absence of a removed name should exclude .writ/specs/ as a whole, not a list of spec folders; spec folders, UAT plans, and drift logs are records that legitimately name what was removed.

## Context

Recorded at phase close from evidence-bound knowledge writeback.

**Cited evidence:**

- .writ/specs/2026-10-20-harness-cuts/drift-log.md DEV-005 and DEV-009
- .writ/specs/2026-10-20-platform-neutral-names/drift-log.md DEV-004 (same pattern for the /design rename gate)

## Related


