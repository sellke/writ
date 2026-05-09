# Writ Update Check Prompts When No Update Exists

> **Type:** Bug
> **Priority:** Normal
> **Effort:** Medium
> **Created:** 2026-05-08
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

The daily Writ update check is prompting users to run `/update-writ` even when there are no upstream changes available.

## Current State

- The completed daily update check spec says no-update, already-checked, unsupported, source-repo, and linked-install states should stay quiet.
- Users can still see an update prompt when Writ appears current or when no new changes are available.
- This creates a false-positive update notification and sends users into `/update-writ` unnecessarily.

## Expected Outcome

- Writ only shows the update-available message when a copied installation has newer upstream content available.
- Current/no-update states stay silent and continue the original requested workflow.
- Source-repo and linked-install states never recommend `/update-writ`.
- The daily cache records enough status to prevent repeated same-day false prompts.

## Relevant Files

- `system-instructions.md` - Defines the startup update awareness protocol.
- `cursor/writ.mdc` - Cursor mirror of the startup update awareness protocol.
- `commands/update-writ.md` - Existing update workflow referenced by the notification.

## Related Issues

- [2026-04-28-daily-session-update-check](../features/2026-04-28-daily-session-update-check.md) - Original feature request for daily Writ update awareness.

## Notes

- Regression context: `.writ/specs/2026-04-28-daily-writ-update-check/spec.md` explicitly requires quiet behavior when Writ is current or no update is available.
- Verify the update-available decision rule distinguishes newer upstream content from a merely reachable upstream source.
