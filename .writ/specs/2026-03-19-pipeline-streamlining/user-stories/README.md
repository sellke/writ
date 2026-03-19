# Pipeline Streamlining — User Stories

## Overview

| # | Story | Status | Tasks | Priority | Dependencies |
|---|-------|--------|-------|----------|--------------|
| 1 | [Shrink verify-spec to pure diagnostic](story-1-verify-spec-shrink.md) | Completed ✅ | 7/7 | High | None |
| 2 | [Make /release self-sufficient with conditional gate](story-2-release-gate.md) | Completed ✅ | 8/8 | High | Story 1 |
| 3 | [Tighten /ship — opt-in tests, inline spec check](story-3-ship-tighten.md) | Completed ✅ | 6/6 | Medium | None |
| 4 | [Update cross-references across pipeline](story-4-cross-references.md) | Completed ✅ | 5/5 | Low | Stories 1, 2, 3 |

**Total: 26/26 tasks (100%)**

## Dependencies

- Story 2 depends on Story 1: release needs to know verify-spec's final scope to avoid duplication.
- Story 4 depends on Stories 1, 2, 3: cross-references can only be updated after all three commands are rewritten.
- Stories 1 and 3 are independent and can be implemented in parallel.

## Quick Links

- [Spec](../spec.md)
- [Spec Lite](../spec-lite.md)
- [Technical Spec](../sub-specs/technical-spec.md)
