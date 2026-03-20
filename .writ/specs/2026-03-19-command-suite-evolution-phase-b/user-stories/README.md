# Command Suite Evolution — Phase B User Stories

## Overview

| # | Story | Status | Tasks | Priority | Dependencies |
|---|-------|--------|-------|----------|--------------|
| 5 | [.writ/context.md Auto-Loading](story-5-context-autoloading.md) | Completed ✅ | 7/7 | Medium | Phase A Stories 1, 4 |
| 7 | [Issue → Spec Promotion](story-7-issue-spec-promotion.md) | Completed ✅ | 6/6 | Medium | Phase A Story 4 + Story 5 (this phase) |
| 9 | [/refresh-command Batch Analysis](story-9-refresh-command-batch.md) | Completed ✅ | 7/7 | Low | Story 7 (this phase) |

**Total: 20/20 tasks (100%)**

**Prerequisite:** Phase A (`2026-03-19-command-suite-evolution`) must be fully complete before starting.

## Execution Batches

All three stories are sequential — each touches `status.md` and must land in order.

**Batch 1 (after Phase A complete):** ✅ Complete
- Story 5: .writ/context.md auto-loading

**Batch 2 (after Story 5):** ✅ Complete
- Story 7: Issue → spec promotion

**Batch 3 (after Story 7):** ✅ Complete
- Story 9: /refresh-command batch analysis

## Dependencies

- Story 5 depends on Phase A Stories 1+4: context auto-loading builds on config and the rewritten status
- Story 7 depends on Phase A Story 4 + Phase B Story 5: extends status.md after both prior rewrites are stable
- Story 9 depends on Phase B Story 7: auto-trigger section in status.md lands after Story 7's Needs Triage section

## Quick Links

- [Spec](../spec.md)
- [Spec Lite](../spec-lite.md)
- [Phase A Spec](../../2026-03-19-command-suite-evolution/spec.md)
