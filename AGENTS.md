# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## What This Project Is

Writ is an AI-powered development workflow framework — markdown command files and agent definitions that run on any AI coding platform (Cursor, Codex, OpenClaw). There is no application code, no build step, no test suite, and no dependencies. The deliverables are markdown files.

**Version:** See `VERSION` file. Current release process: `/release` command.

## Repository Structure (Self-Dogfooding)

This repo uses Writ to build Writ. Several concerns live here:

| Concern | Location | What it is |
|---|---|---|
| **Product source** | `commands/`, `agents/`, `skills/`, `adapters/`, `scripts/`, `cursor/`, `system-instructions.md`, `SKILL.md` | The distributable methodology — what `install.sh` copies into other projects |
| **Development workspace** | `.writ/` | Specs, research, product docs, ADRs — artifacts from using Writ to build itself |
| **Active installation (Cursor)** | `.cursor/` | **Symlinks** to product source, not copies. Do not replace with regular files or run `install.sh` on this repo. |
| **Active installation (Claude Code)** | `.claude/` | Same pattern: `commands`, `agents`, and `skills` symlink to repo-root `commands/`, `agents/`, `skills/`. Keep `settings.local.json` and other Claude-only files as real files. |
| **Active installation (Codex CLI)** | `.codex/` | **`agents` → `codex/agents/`** (TOML). Same symlink idea as other platforms — do not replace with opaque copies while developing Writ itself. |

Editing `commands/foo.md`, `.cursor/commands/foo.md`, or `.claude/commands/foo.md` changes the same file via symlink. Same applies to `skills/<name>/SKILL.md` once the first skill ships.

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

Key commands in the pipeline: `plan-product` → `create-spec` → `implement-phase` (phase-level orchestrator; loops `implement-spec` per spec) or `implement-spec` directly (single spec) → `create-uat-plan` (UAT validation; auto-called by `implement-phase`) → `verify-spec` → `release`.

### Agents (`agents/`)
Agent definitions for the multi-agent SDLC pipeline within `/implement-story`:
1. Architecture check (read-only, PROCEED/CAUTION/ABORT)
2. Coding agent (TDD, worktree isolation, loads "What Was Built" from dependencies)
3. Review agent (read-only, PASS/FAIL, max 3 iterations, outputs parsed for "What Was Built" records)
4. Testing agent (coverage enforcement, >=80%)
5. Documentation agent (framework-adaptive)

Additional: `visual-qa-agent.md` (optional UI validation), `user-story-generator.md` (parallel story creation for `/create-spec`, generates context hints that index into spec content for targeted agent context).

### Adapters (`adapters/`)
Platform-specific integration guides. `adapters/codex.md` maps Writ concepts to Codex CLI subagents, `AGENTS.md`, and `.codex/config.toml`. `cursor.md` maps to Cursor's Task/AskQuestion APIs. `openclaw.md` maps to OpenClaw's session system. Each adapter includes a Skills section documenting per-platform install paths and invocation behavior.

### Scripts (`scripts/`)
Shell scripts for installation (`install.sh`), updates (`update.sh`), migration from Code Captain (`migrate.sh`), symlink management (`unlink.sh`), root-catalog generation (`gen-skill.sh`), and skills boundary linting (`lint-skill.sh`).

### Skills (`skills/`)
Folder-per-skill capability files (`skills/<name>/SKILL.md`) — the third Writ primitive (verb/noun/tool: command/agent/skill). Skills are reusable capabilities wielded by commands and agents, not workflows or roles. Authoring is via `/new-skill` with the boundary lint enforced at authoring time and again via `/refresh-command --lint-skills`. Empty by default — pilot extractions land in separate specs. See [`.writ/docs/skills.md`](.writ/docs/skills.md) for the explainer and [ADR-009](.writ/decision-records/adr-009-command-agent-skill-boundary.md) for the boundary rationale.

### SKILL.md
Root catalog for platforms that support skill discovery. Auto-generated from `.writ/manifest.yaml` by `scripts/gen-skill.sh`. Describes all commands, agents, and (when present) skills with metadata.

## Key Design Decisions

- **Contract-first**: Specs are agreed upon before any files are created. Commands use Plan Mode for discovery, AskQuestion for bounded choices (see ADR-001 in `.writ/decision-records/`).
- **Platform-agnostic tool references**: Commands use generic tool names. Adapters translate to platform-specific APIs.
- **Symlinks for dogfooding**: `.cursor/` symlinks to product source so edits are immediately live and `/refresh-command` improves the product directly.
- **`.writ/state/` is gitignored**: Ephemeral workflow state only.

## When Editing Commands or Agents

- Edits to `commands/` and `agents/` are product changes that ship to all Writ users.
- Edits to `.writ/` are development workspace artifacts for this project only.
- The `system-instructions.md` file defines Writ's identity, Prime Directive (anti-sycophancy rules), and interaction tool selection guidance. It's the root behavioral contract.
