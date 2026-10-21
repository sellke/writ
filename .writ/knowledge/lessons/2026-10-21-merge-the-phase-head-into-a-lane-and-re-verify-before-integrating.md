---
category: lessons
tags: [phase-close, implement-phase]
created: 2026-10-21
related_artifacts: []
---

# Merge the phase head into a lane and re-verify before integrating

## TL;DR

Before integrating a lane, merge the current phase-branch head into it and re-run the full suites; commits that land on the phase branch while a lane runs (UAT plans, peer sessions' work) can break that lane's tests after the merge.

## Context

Recorded at phase close from evidence-bound knowledge writeback.

**Cited evidence:**

- .writ/specs/2026-10-20-harness-cuts/drift-log.md DEV-009: guard test failed on the phase branch after integration because a UAT plan committed during the lane named a lean file
- Phase 13 lane 1: a peer session committed the claude-agent-generator spec on the phase branch mid-lane; merging it into the lane surfaced a .writ/context.md conflict before integrate would have aborted

## Related


