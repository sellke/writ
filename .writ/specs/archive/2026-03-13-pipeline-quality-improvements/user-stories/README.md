# User Stories Overview

> **Specification:** Pipeline Quality Improvements
> **Created:** 2026-03-13
> **Status:** Complete ✅
> **Implementation Mode:** `--quick` (prompt/protocol changes)

## Stories Summary

| Story | Title | Status | Tasks | Progress | Dependencies |
|-------|-------|--------|-------|----------|-------------|
| 1 | [Coding Agent Self-Check](./story-1-coding-agent-self-check.md) | Completed ✅ | 5 | 5/5 | None |
| 2 | [Weighted Review](./story-2-weighted-review.md) | Completed ✅ | 6 | 6/6 | None |
| 3 | ["What Was Built" Record](./story-3-what-was-built-record.md) | Completed ✅ | 5 | 5/5 | None |
| 4 | [Living Spec Auto-Amendment](./story-4-living-spec-amendment.md) | Completed ✅ | 5 | 5/5 | None |
| 5 | [Cross-Spec Consistency Check](./story-5-cross-spec-consistency-check.md) | Completed ✅ | 5 | 5/5 | None |
| 6 | [Documentation Agent Agnosticism](./story-6-documentation-agent-agnosticism.md) | Completed ✅ | 6 | 6/6 | None |
| 7 | [Quick Wins Bundle](./story-7-quick-wins-bundle.md) | Completed ✅ | 5 | 5/5 | None |

**Total Progress:** 37/37 tasks (100%)

## Story Dependencies

All stories are independent — they can execute in a single parallel batch.

Stories 2, 3, and 4 all touch `commands/implement-story.md` but at different points:
- Story 2: Gate 3 (review agent invocation) — adds change surface classification
- Story 3: Step 4 (story completion) — adds "What Was Built" section
- Story 4: Gate 3.5 (drift response) — adds spec-lite auto-amendment

These should be applied sequentially to avoid merge conflicts on the same file.

## Recommended Execution Order

For maximum compound value, implement in priority order:

1. **Story 1** (Coding Agent Self-Check) — immediately reduces pipeline round-trips
2. **Story 2** (Weighted Review) — immediately makes every review faster
3. **Story 3** ("What Was Built") — compounds over time for future development
4. **Story 4** (Living Spec Amendment) — compounds over time for spec accuracy
5. **Story 5** (Cross-Spec Check) — catches planning-level conflicts
6. **Story 6** (Doc Agent Agnosticism) — fixes framework assumption
7. **Story 7** (Quick Wins) — trivial changes, do anytime

## Files Affected

| File | Stories |
|------|---------|
| `agents/coding-agent.md` | 1 |
| `agents/review-agent.md` | 2 |
| `commands/implement-story.md` | 2, 3, 4 |
| `commands/create-spec.md` | 5 |
| `agents/documentation-agent.md` | 6 |
| `agents/architecture-check-agent.md` | 7 |
| `system-instructions.md` | 7 |

## Quick Links

- [Story 1: Coding Agent Self-Check](./story-1-coding-agent-self-check.md)
- [Story 2: Weighted Review](./story-2-weighted-review.md)
- [Story 3: "What Was Built" Record](./story-3-what-was-built-record.md)
- [Story 4: Living Spec Auto-Amendment](./story-4-living-spec-amendment.md)
- [Story 5: Cross-Spec Consistency Check](./story-5-cross-spec-consistency-check.md)
- [Story 6: Documentation Agent Agnosticism](./story-6-documentation-agent-agnosticism.md)
- [Story 7: Quick Wins Bundle](./story-7-quick-wins-bundle.md)
