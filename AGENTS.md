# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## What This Project Is

Writ is an AI-powered development workflow framework — markdown command files and agent definitions that run on any AI coding platform (Cursor, Codex, OpenClaw). There is no application code, no build step, no test suite, and no dependencies. The deliverables are markdown files.

**Version:** See `VERSION` file. Current release process: `/release` command.

## Repository Structure (Self-Dogfooding)

This repo uses Writ to build Writ. Three concerns live here:

| Concern | Location | What it is |
|---|---|---|
| **Product source** | `commands/`, `agents/`, `adapters/`, `scripts/`, `cursor/`, `system-instructions.md`, `SKILL.md` | The distributable methodology — what `install.sh` copies into other projects |
| **Development workspace** | `.writ/` | Specs, research, product docs, ADRs — artifacts from using Writ to build itself |
| **Active installation (Cursor)** | `.cursor/` | **Symlinks** to product source, not copies. Do not replace with regular files or run `install.sh` on this repo. |
| **Active installation (Claude Code)** | `.claude/` | Same pattern: `commands` and `agents` symlink to repo-root `commands/` and `agents/`. Keep `settings.local.json` and other Claude-only files as real files. |

Editing `commands/foo.md`, `.cursor/commands/foo.md`, or `.claude/commands/foo.md` changes the same file via symlink.

## Development Commands

There is no build, lint, or test command. Validation is manual or via Writ commands:

```bash
# Check spec integrity
/verify-spec

# Full project status
/status

# Release (changelog + version bump + git tag)
/release
```

The install/update scripts can be tested:
```bash
bash scripts/install.sh --dry-run    # Preview install into a target project
bash scripts/update.sh --dry-run     # Preview update
```

## Architecture

### Commands (`commands/`)
Markdown workflow files with structured phases. Each command is self-contained — read it and follow the steps. Commands reference agents and other commands but don't import anything.

Key commands in the pipeline: `plan-product` → `create-spec` → `implement-spec` (orchestrates `implement-story` per story) → `verify-spec` → `release`.

### Agents (`agents/`)
Agent definitions for the multi-agent SDLC pipeline within `/implement-story`:
1. Architecture check (read-only, PROCEED/CAUTION/ABORT)
2. Coding agent (TDD, worktree isolation)
3. Review agent (read-only, PASS/FAIL, max 3 iterations)
4. Testing agent (coverage enforcement, >=80%)
5. Documentation agent (framework-adaptive)

Additional: `visual-qa-agent.md` (optional UI validation), `user-story-generator.md` (parallel story creation for `/create-spec`).

### Adapters (`adapters/`)
Platform-specific integration guides. `Codex.md` maps Writ concepts to Codex's native subagent system (YAML frontmatter, worktrees, memory). `cursor.md` maps to Cursor's Task/AskQuestion APIs. `openclaw.md` maps to OpenClaw's session system.

### Scripts (`scripts/`)
Shell scripts for installation (`install.sh`), updates (`update.sh`), migration from Code Captain (`migrate.sh`), and symlink management (`unlink.sh`).

### SKILL.md
Skill manifest for platforms that support skill discovery. Describes all commands with metadata.

## Key Design Decisions

- **Contract-first**: Specs are agreed upon before any files are created. Commands use Plan Mode for discovery, AskQuestion for bounded choices (see ADR-001 in `.writ/decision-records/`).
- **Platform-agnostic tool references**: Commands use generic tool names. Adapters translate to platform-specific APIs.
- **Symlinks for dogfooding**: `.cursor/` symlinks to product source so edits are immediately live and `/refresh-command` improves the product directly.
- **`.writ/state/` is gitignored**: Ephemeral workflow state only.

## When Editing Commands or Agents

- Edits to `commands/` and `agents/` are product changes that ship to all Writ users.
- Edits to `.writ/` are development workspace artifacts for this project only.
- The `system-instructions.md` file defines Writ's identity, Prime Directive (anti-sycophancy rules), and interaction tool selection guidance. It's the root behavioral contract.
