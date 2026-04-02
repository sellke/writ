# Codex & OpenClaw Platform Support for Lifecycle Commands

> **Type:** Feature
> **Priority:** Normal
> **Effort:** Large
> **Created:** 2026-04-02
> **spec_ref:**

## TL;DR

Extend `/update-writ`, `/reinstall-writ`, `/uninstall-writ`, and the shell scripts (`install.sh`, `update.sh`, `unlink.sh`, `uninstall.sh`) to support Codex and OpenClaw as installation targets.

## Current State

- Lifecycle commands and scripts support two platforms: Cursor and Claude Code
- Codex has no adapter file (`adapters/Codex.md` is referenced in AGENTS.md but doesn't exist) and no defined installation structure
- OpenClaw has an adapter (`adapters/openclaw.md`) but no installation scripts or defined file layout
- AGENTS.md is the de facto Codex entry point, but Codex's broader project-level configuration patterns are undocumented in this repo
- The three new lifecycle commands (`update-writ`, `reinstall-writ`, `uninstall-writ`) and `uninstall.sh` were built with Cursor + Claude Code only

## Expected Outcome

- Installation structures defined for both Codex and OpenClaw — where commands, agents, and configuration files live on each platform
- `adapters/codex.md` created with installation guide, tool mapping, and workflow patterns (matching the depth of `adapters/claude-code.md`)
- `install.sh`, `update.sh`, `unlink.sh`, `uninstall.sh` extended with `--platform codex` and `--platform openclaw` options
- `/update-writ`, `/reinstall-writ`, `/uninstall-writ` updated with platform-specific paths for Codex and OpenClaw
- Platform-specific agent files if needed (like `claude-code/agents/` provides Claude Code–native agents with YAML frontmatter)

## Relevant Files

- `adapters/openclaw.md` - existing adapter with tool mapping but no installation structure
- `scripts/install.sh` - current installer supporting `--platform cursor|claude`
- `commands/update-writ.md` - lifecycle command with platform detection logic to extend

## Notes

- This is blocked on understanding Codex's and OpenClaw's native project configuration patterns. Research should precede implementation — `/research` on both platforms' conventions would be a good starting point.
- Codex may share structure with Claude Code (both are Anthropic tools using markdown agents), but the specifics need verification.
- OpenClaw's session-based model may not map cleanly to file-based installation. It might need a fundamentally different install pattern (e.g., copying to a skills directory rather than a project-local `.openclaw/`).
- Consider whether each platform needs its own agent variants (like Claude Code has `claude-code/agents/` with YAML frontmatter) or can share the base agent definitions.
- The README's Platform Support table should be updated to include Codex and re-include OpenClaw once this work ships.
