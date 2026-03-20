# Command Suite Evolution — Phase A User Stories

## Overview

| # | Story | Status | Tasks | Priority | Dependencies |
|---|-------|--------|-------|----------|--------------|
| 1 | [Config Persistence Layer](story-1-config-persistence.md) | Completed ✅ | 7/7 | High | None |
| 2 | [Agent Iteration Caps](story-2-agent-iteration-caps.md) | Completed ✅ | 6/6 | High | None |
| 3 | [Spec-Lite Integrity Check](story-3-speclite-integrity-check.md) | Completed ✅ | 7/7 | High | None |
| 4 | [/status North Star Rewrite](story-4-status-north-star.md) | Completed ✅ | 7/7 | High | Story 1 |
| 6 | [Prototype → Spec Escalation](story-6-prototype-escalation.md) | Completed ✅ | 7/7 | Medium | None |
| 8 | [ADR Unification](story-8-adr-unification.md) | Completed ✅ | 6/6 | Medium | None |

**Total: 40/40 tasks (100%)**

Stories 5, 7, and 9 (dependent extensions) live in the Phase B spec:
`.writ/specs/2026-03-19-command-suite-evolution-phase-b/`

## Execution Batches

**Batch 1 (parallel — all independent):** ✅ Complete
- Story 1: Config persistence layer
- Story 2: Agent iteration caps
- Story 3: Spec-lite integrity check
- Story 6: Prototype → spec escalation
- Story 8: ADR unification

**Batch 2 (after Story 1 completes):** ✅ Complete
- Story 4: /status North Star rewrite

## Dependencies

- Story 4 depends on Story 1: status rewrite reads from `.writ/config.md`

## Quick Links

- [Spec](../spec.md)
- [Spec Lite](../spec-lite.md)
- [Technical Sub-Spec](../sub-specs/technical-spec.md)
- [Phase B Spec](../../2026-03-19-command-suite-evolution-phase-b/spec.md)
