# Self-Dogfooding: Writ Building Writ

> This repo uses Writ to develop Writ. This document explains how the two concerns are separated.

## The Three Concerns

This repository contains three distinct things:

| Concern | Location | What it is |
|---|---|---|
| **Product Source** | `commands/`, `agents/`, `skills/`, `adapters/`, `scripts/`, `cursor/`, `system-instructions.md` | The distributable methodology — what `install.sh` copies into other projects |
| **Development Workspace** | `.writ/` | Specs, research, product docs, decisions — artifacts from using Writ to build this project |
| **Active Installation** | `.cursor/`, `.claude/` | Symlinks to product source — what Cursor and Claude Code read at runtime |

## How Symlinks Work

In a normal project, `scripts/install.sh` **copies** product files into `.cursor/`. In this repo, `.cursor/` and `.claude/` use **symlinks** instead:

```
.cursor/commands/              → ../commands/
.cursor/agents/                → ../agents/
.cursor/skills/                → ../skills/
.cursor/system-instructions.md → ../system-instructions.md
.cursor/rules/writ.mdc         → ../../cursor/writ.mdc

.claude/commands/              → ../commands/
.claude/agents/                → ../agents/
.claude/skills/                → ../skills/
```

(`.claude/` may also contain Claude-only files such as `settings.local.json` or `worktrees/` — those stay as regular files.)

The `.cursor/skills` and `.claude/skills` symlinks are created proactively even when `skills/` is empty — as soon as `/new-skill` creates the first `skills/<name>/SKILL.md`, both platforms see it immediately without any further symlink work.

This means:

- **Single source of truth.** Editing `commands/prototype.md`, `.cursor/commands/prototype.md`, or `.claude/commands/prototype.md` changes the same file.
- **`/refresh-command` improves the product directly.** When it edits `.cursor/commands/foo.md`, it's editing the canonical source via symlink.
- **No drift.** There's no stale copy to get out of sync.

## Rules for Working in This Repo

### Editing product source (commands, agents, skills, adapters)

Edit files in `commands/`, `agents/`, `skills/`, `adapters/`, `scripts/`, or `cursor/` directly. Changes are immediately live because `.cursor/` symlinks to them.

### Using Writ as a development tool

Work in `.writ/` as usual — specs, research, decisions, docs. This is the workspace for building Writ itself, and it follows the same conventions as any project using Writ.

### What NOT to do

- **Don't replace symlinks with regular files.** If `.cursor/commands/` or `.claude/commands/` stops being a symlink, the source and installation will diverge silently.
- **Don't run `install.sh` on this repo.** It would overwrite the symlinks with copies, breaking the single-source-of-truth setup.

## Skills

The third Writ primitive — skills — participates in the same dogfood pattern:

- **`skills/` is product source.** Editing `skills/<name>/SKILL.md` ships to every Writ project on the next install or update, exactly like editing a command or agent.
- **The symlink architecture extends.** `.cursor/skills` and `.claude/skills` are symlinks to `../skills` (parallel to the command/agent pattern). Editing a skill via the symlinked path or the source path changes the same file.
- **`skills/` may be empty.** The foundation spec ships the schema, install fanout, and authoring tooling without extracting any production skills — pilot skills land in separate specs. An empty `skills/` directory is valid; the catalog generator silently skips the Skills section.
- **Authoring on this repo uses the same `/new-skill` command** that ships to users. The boundary lint (`scripts/lint-skill.sh`) runs identically here and in installed projects.

See [`.writ/docs/skills.md`](skills.md) for the user-facing skills explainer and [ADR-009](../decision-records/adr-009-command-agent-skill-boundary.md) for the verb/noun/tool boundary.

## Leanness Cadence

Writ's value proposition *is* leanness, so this repo polices its own bloat with a
two-tier **leanness guardian** ([ADR-015](../decision-records/adr-015-leanness-self-governance.md)) —
dogfooding-only, never shipped to users:

- **Tier A (mechanical, every PR):** `bash scripts/eval.sh --check=leanness`
  measures aggregate command weight and cross-registry parity (README `## Commands`
  table ↔ `commands/*.md`, and the `/status` allowlist → files). Registry drift
  hard-FAILs; count/weight growth warns non-blockingly against
  [`.writ/leanness-baseline.json`](../leanness-baseline.json).
- **Tier B (judgment, on a cadence):** the audit ritual in
  [`leanness-audit-format.md`](leanness-audit-format.md) re-applies the "does the
  harness do this natively now?" test (Design Principle #4) and surfaces prune
  candidates. It **recommends, never deletes**.

**Trigger for Tier B:** run at **each phase close** *or* **quarterly**, whichever
comes first — **never per-release** (too frequent; an audit there is friction).
The cadence is documented discipline and is deliberately **not** hooked into any
shipping command (`/release`, `/ship`, `/implement-phase`), which would leak
framework-internal governance to users. Each run produces a dated
`.writ/docs/leanness-audit-YYYY-MM-DD.md`; the first is
[`leanness-audit-2026-07-11.md`](leanness-audit-2026-07-11.md).

## For AI Agents

When working in this repo, be aware of the dual nature:

- **Improving a command's behavior?** You're editing product source. The change will ship to all Writ users.
- **Authoring or editing a skill?** Same — `skills/<name>/SKILL.md` is product source. The boundary lint applies.
- **Writing a spec or researching a feature?** You're using the workspace. The output lives in `.writ/` and documents this project's development.
- **All three are valid.** Just know which hat you're wearing.
