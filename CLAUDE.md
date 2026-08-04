# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

Writ is an AI-powered development workflow framework — markdown command files and agent definitions that run on any AI coding platform (Cursor, Claude Code, OpenClaw). There is no application code, no build step, no test suite, and no dependencies. The deliverables are markdown files.

**Version:** See `VERSION` file. Current release process: `/release` command.

## Repository Structure (Self-Dogfooding)

This repo uses Writ to build Writ. Three concerns live here:

| Concern | Location | What it is |
|---|---|---|
| **Product source** | `commands/`, `agents/`, `adapters/`, `scripts/`, `cursor/`, `system-instructions.md`, `SKILL.md` | The distributable methodology — what `install.sh` copies into other projects |
| **Development workspace** | `.writ/` | Specs, research, product docs, ADRs — artifacts from using Writ to build itself |
| **Active installation** | `.cursor/`, `.claude/` | **Symlinks** to product source, not copies. Do not replace with regular files or run `install.sh` on this repo. |

Editing `commands/foo.md`, `.cursor/commands/foo.md`, and `.claude/commands/foo.md` all change the same file via symlink.

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

Pipeline: `plan-product` → `create-spec` → `implement-phase` (loops `implement-spec` per spec) or `implement-spec` directly → `verify-spec` → `release`.

Commands are self-contained — each is read and followed top to bottom; they reference agents and other commands but don't import anything. `agents/` holds the docs for the `/implement-story` SDLC gates; the *loadable* Claude Code agent definitions (with frontmatter) live in `claude-code/agents/`. `adapters/` exists because commands use platform-agnostic tool names — each adapter translates them to one platform's APIs.

## Key Design Decisions

- **Contract-first**: Specs are agreed upon before any files are created. Commands use Plan Mode for discovery, AskQuestion for bounded choices (see ADR-001 in `.writ/decision-records/`).
- **Platform-agnostic tool references**: Commands use generic tool names. Adapters translate to platform-specific APIs.
- **Symlinks for dogfooding**: `.cursor/` symlinks to product source so edits are immediately live and `/refresh-command` improves the product directly.
- **`.writ/state/` is gitignored**: Ephemeral workflow state only.

## When Editing Commands or Agents

- Edits to `commands/` and `agents/` are product changes that ship to all Writ users.
- Edits to `.writ/` are development workspace artifacts for this project only.
- The `system-instructions.md` file defines Writ's identity, Prime Directive (anti-sycophancy rules), and interaction tool selection guidance. It's the root behavioral contract.
