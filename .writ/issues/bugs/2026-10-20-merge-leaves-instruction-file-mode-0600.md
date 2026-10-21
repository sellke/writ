# Install and Update Leave CLAUDE.md and AGENTS.md at Mode 0600

> **Type:** Bug
> **Priority:** Normal
> **Effort:** Small
> **Created:** 2026-10-20
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

`merge_claude_md` and `merge_agents_md` write the merged file through `mktemp` and `mv`. The result replaces the user's `CLAUDE.md` or `AGENTS.md` with a file at mode 0600, so a file that was group- or world-readable loses those bits after install or update.

## Current State

- `scripts/install.sh` and `scripts/update.sh`: both merge functions build the new file in a `mktemp` file (mode 0600) and `mv` it over the original.
- `2026-10-20-claude-code-parity` Story 4 adds `remove_claude_md_block` for uninstall and writes back with `cat "$tmp" > "$file"`, which keeps the original mode. The install and update merge paths are out of that spec's scope.
- Found while grounding that spec (2026-10-20).

## Expected Outcome

- After install, update, or uninstall, `CLAUDE.md` and `AGENTS.md` keep the mode they had before. A test checks `stat` output before and after on a 0644 file.

## Relevant Files

- `scripts/install.sh` - `merge_claude_md`, `merge_agents_md`
- `scripts/update.sh` - the same functions
- `.writ/specs/2026-10-20-claude-code-parity/sub-specs/technical-spec.md` - the write-back pattern Story 4 uses
