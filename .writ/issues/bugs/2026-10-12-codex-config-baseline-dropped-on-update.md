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

## Resolution

2026-10-20, branch `writ/phase/13/2026-10-20-ci-and-update-integrity` (spec `2026-10-20-ci-and-update-integrity`, Story 2). `write_copy_manifest` in `scripts/update.sh` now reads `manifest_hash_for ".codex/config.toml.baseline"` into a local before `cat > "$target"` truncates the manifest, the same order `scripts/unlink.sh` uses. The Codex block writes that value when it is non-empty, so a manifest with no baseline line still gets none.

`scripts/tests/test_update_codex_config_baseline.sh` installs Codex into a temp project, runs two updates that rewrite the manifest and one dry run, and checks that one baseline line with the install-time hash survives each and that `.codex/config.toml` is unchanged. It also covers the no-baseline case. On the pre-fix `update.sh` it fails at the first update: line count 0, want 1.
