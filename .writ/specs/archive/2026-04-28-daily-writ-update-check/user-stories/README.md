# User Stories: Daily Writ Update Check

> **Spec:** `.writ/specs/2026-04-28-daily-writ-update-check/spec.md`
> **Total Stories:** 3
> **Progress:** 3/3 complete

## Story Summary

| Story | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---:|---:|
| [Story 1: Startup Update Check Protocol](story-1-startup-protocol.md) | Completed ✅ | High | None | 7 | 7/7 |
| [Story 2: Cache and Detection Contract](story-2-cache-and-detection-contract.md) | Completed ✅ | High | Story 1 | 6 | 6/6 |
| [Story 3: Verification and Issue Linkage](story-3-verification-and-issue-linkage.md) | Completed ✅ | Medium | Stories 1 and 2 | 6 | 6/6 |

## Dependency Flow

Story 1 establishes where the startup update check lives and how it fits before auto-orientation or command workflows.

Story 2 depends on Story 1 because the cache and detection rules need to plug into that startup protocol.

Story 3 depends on Stories 1 and 2 because verification needs the final behavior and decision matrix to review, and the source issue should only point to a real spec package.

## Implementation Order

1. `story-1-startup-protocol.md`
2. `story-2-cache-and-detection-contract.md`
3. `story-3-verification-and-issue-linkage.md`

## Quick Links

- [Main Spec](../spec.md)
- [Spec Lite](../spec-lite.md)
- [Technical Spec](../sub-specs/technical-spec.md)
- [Source Issue](../../../issues/features/2026-04-28-daily-session-update-check.md)
