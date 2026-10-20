# Codex config.toml baseline is dropped on every update

> **Type:** Bug
> **Priority:** Normal
> **Effort:** Small
> **Created:** 2026-10-12
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

`write_copy_manifest` truncates the manifest, then looks up `.codex/config.toml.baseline` in that same file, so the lookup is always empty and the baseline disappears.

## Current State

- `scripts/update.sh` `write_copy_manifest` starts with `cat > "$target"`, where `$target` is the manifest.
- Line ~230 then runs `manifest_hash_for ".codex/config.toml.baseline"`, which greps the now-truncated `$MANIFEST_FILE`.
- The Story 2 evaluator of `2026-10-12-agent-cli-contract` confirmed it in a temp Codex project: baseline count went from 1 to 0 after one update.
- `scripts/unlink.sh` reads the hash before truncating and does not have the bug.

## Expected Outcome

- The `.codex/config.toml.baseline` line survives `update.sh` unchanged, so `.codex/config.toml` stays install-once and its customization check keeps working.

## Relevant Files

- `scripts/update.sh` - `write_copy_manifest`, `manifest_hash_for`
- `scripts/unlink.sh` - the read-before-truncate pattern to copy
- `adapters/codex.md` - documents the baseline convention
