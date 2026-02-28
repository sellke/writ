# Self-Dogfooding: Writ Building Writ

> This repo uses Writ to develop Writ. This document explains how the two concerns are separated.

## The Three Concerns

This repository contains three distinct things:

| Concern | Location | What it is |
|---|---|---|
| **Product Source** | `commands/`, `agents/`, `adapters/`, `scripts/`, `cursor/`, `system-instructions.md` | The distributable methodology — what `install.sh` copies into other projects |
| **Development Workspace** | `.writ/` | Specs, research, product docs, decisions — artifacts from using Writ to build this project |
| **Active Installation** | `.cursor/` | Symlinks to product source — what Cursor reads at runtime |

## How Symlinks Work

In a normal project, `scripts/install.sh` **copies** product files into `.cursor/`. In this repo, `.cursor/` uses **symlinks** instead:

```
.cursor/commands/             → ../commands/
.cursor/agents/               → ../agents/
.cursor/system-instructions.md → ../system-instructions.md
.cursor/rules/writ.mdc        → ../../cursor/writ.mdc
```

This means:

- **Single source of truth.** Editing `commands/prototype.md` or `.cursor/commands/prototype.md` changes the same file.
- **`/refresh-command` improves the product directly.** When it edits `.cursor/commands/foo.md`, it's editing the canonical source via symlink.
- **No drift.** There's no stale copy to get out of sync.

## Rules for Working in This Repo

### Editing product source (commands, agents, adapters)

Edit files in `commands/`, `agents/`, `adapters/`, `scripts/`, or `cursor/` directly. Changes are immediately live because `.cursor/` symlinks to them.

### Using Writ as a development tool

Work in `.writ/` as usual — specs, research, decisions, docs. This is the workspace for building Writ itself, and it follows the same conventions as any project using Writ.

### What NOT to do

- **Don't replace symlinks with regular files.** If `.cursor/commands/` stops being a symlink, the source and installation will diverge silently.
- **Don't run `install.sh` on this repo.** It would overwrite the symlinks with copies, breaking the single-source-of-truth setup.

## For AI Agents

When working in this repo, be aware of the dual nature:

- **Improving a command's behavior?** You're editing product source. The change will ship to all Writ users.
- **Writing a spec or researching a feature?** You're using the workspace. The output lives in `.writ/` and documents this project's development.
- **Both are valid.** Just know which hat you're wearing.
