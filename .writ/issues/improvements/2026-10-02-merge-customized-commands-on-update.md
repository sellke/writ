# Merge Customized Commands with New Upstream Versions on Update

> **Type:** Improvement
> **Priority:** Normal
> **Effort:** Large
> **Created:** 2026-10-02
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

When a user has customized a Writ command and upstream ships a new version, `/update-writ` should help reconcile the two instead of forcing an all-or-nothing keep/overwrite choice.

## Current State

- `scripts/update.sh` detects local modifications via manifest hash and silently preserves the file — the user's copy never receives upstream fixes
- `/update-writ` offers per-file `overwrite` / `keep` / `diff`, but `diff` only displays a two-way diff and re-asks keep/overwrite — no merge path
- Keeping a customization means permanent drift from upstream; overwriting loses the customization
- The manifest stores only a baseline **hash**, not baseline **content**, so a true three-way merge (base → local, base → upstream) has no base to work from
- `/reinstall-writ` explicitly documents "no three-way merge"

## Expected Outcome

- A `merge` option in `/update-writ` alongside overwrite/keep/diff
- Three-way reconciliation: user's local edits re-applied on top of the new upstream version, with conflicts surfaced per hunk
- Non-conflicting changes from both sides applied automatically; true conflicts presented for a bounded decision (keep mine / take theirs / combined)
- Result is reviewable before write, and the manifest baseline is updated to the new upstream so the next update diffs correctly
- Works for commands, agents, and other preserved files (`system-instructions.md`, `rules/writ.mdc`, AGENTS.md/CLAUDE.md Writ blocks)

## Relevant Files

- `commands/update-writ.md` - per-file overwrite/keep/diff decision flow; where a merge option would live
- `scripts/update.sh` - hash-based preserve logic (`manifest_hash_for`, "Preserved: local modifications")
- `scripts/install.sh` - writes the manifest; would need to snapshot baseline content to enable three-way merge

## Notes

- Prerequisite decision: where to store baseline content (e.g. `.writ/.baseline/` snapshot at install/update time) vs. reconstructing it from the upstream git tag matching the installed version
- Markdown commands are prose, so a line-based `git merge-file` may produce noisy conflicts — consider an agent-assisted semantic merge that preserves the intent of the user's customization, with the textual three-way merge as the evidence base
- Must stay consistent with the startup-update-awareness contract: discovery remains read-only; only `/update-writ` applies changes
