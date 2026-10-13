# update.sh deletes a locally modified stale file on the second run

> **Type:** Bug
> **Priority:** High
> **Effort:** Small
> **Created:** 2026-10-12
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

A locally modified file that upstream no longer ships survives one `update.sh` run and is deleted on the next, so the user's edits are lost.

## Current State

- `detect_stale_files` keeps a stale file when its local hash differs from the manifest baseline.
- `write_copy_manifest` then records commands, agents, skills, and `.writ/docs` from the local copies, so the kept file gets its own modified hash as the new baseline.
- On the next update, local hash equals baseline, so the file counts as unmodified and is removed.
- Reproduced by the Story 2 evaluator of `2026-10-12-agent-cli-contract` with a modified `commands/old-cmd.md`: run 1 kept it, run 2 printed `🗑  Removed: commands/old-cmd.md`. HEAD's `update.sh` before that spec behaves the same.
- `scripts/` is the exception since that spec: a kept, modified, filter-rejected script carries its old baseline forward (`STALE_KEPT_ENTRIES`) and keeps warning.

## Expected Outcome

- A kept, locally modified stale file stays on every later update until the user deletes it.
- Each update warns about it, in every category, as `/update-writ` Step 6 promises ("skip modified stale files with a warning").

## Relevant Files

- `scripts/update.sh` - `detect_stale_files` and `write_copy_manifest` (`STALE_KEPT_ENTRIES` carry-forward is scripts-only)
- `commands/update-writ.md` - Step 3 "Detect stale files" and Step 6 item 6
- `scripts/tests/test_install_update_dev_scripts.sh` - second-run pattern to reuse

## Notes

- Fix direction: carry the old baseline forward for every category, and stop re-recording a stale path from its local copy. Then widen the warning, which is limited to `scripts/` until this lands.
