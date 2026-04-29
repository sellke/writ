# Daily Writ Update Check On Session Start

> **Type:** Feature
> **Priority:** Normal
> **Effort:** Medium
> **Created:** 2026-04-28
> **spec_ref:** .writ/specs/2026-04-28-daily-writ-update-check/spec.md

## TL;DR

When Writ is first invoked in a session, it should check whether Writ updates are available, but rate-limit that check to at most once per day.

## Current State

- Writ provides session auto-orientation when first invoked without a specific command.
- Users must explicitly run `/update-writ` to discover and apply upstream Writ updates.
- There is no passive daily update awareness during normal Writ startup.

## Expected Outcome

- On first Writ invocation within a session, Writ checks whether an upstream update is available.
- The update check runs at most once per day per project or installation.
- If an update is available, Writ surfaces a concise prompt or note pointing the user to `/update-writ`.
- If no update is available, Writ stays quiet or minimally intrusive.
- The check should not slow down normal startup noticeably or require network access more than the daily limit.

## Relevant Files

- `system-instructions.md` - Defines first-in-session auto-orientation behavior.
- `cursor/writ.mdc` - Cursor active instruction mirror for Writ session behavior.
- `commands/update-writ.md` - Existing interactive update workflow that the notification should point to.

## Related Issues

- [2026-04-02-codex-openclaw-lifecycle-support](2026-04-02-codex-openclaw-lifecycle-support.md) - Extends lifecycle update commands across platforms; this issue adds passive update discovery.

## Notes

- The daily limit likely needs a small timestamp persisted under `.writ/state/` or an equivalent platform-local state location.
- The implementation should distinguish update discovery from applying updates; startup should only notify, not mutate files.
