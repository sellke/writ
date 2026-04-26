---
category: conventions
tags: [dogfooding, symlinks, installation]
created: 2026-04-24
related_artifacts:
  - AGENTS.md
  - .writ/specs/2026-04-24-phase4-production-grade-substrate/spec.md
---

# Self-Dogfooding Uses Symlinks

## TL;DR

In the Writ repo, active installations under `.cursor/` and `.claude/` point at product source by symlink; do not replace them with copied files.

## Context

- This repo uses Writ to build Writ.
- Product source lives in `commands/`, `agents/`, `adapters/`, scripts, and system instruction files.
- Active local installations exist so the maintainer can dogfood the latest command behavior immediately.

## Detail

When editing a command or agent, edit the product source path. The active installation should reflect that change through symlinks. Running install scripts against this repo or replacing symlinks with files can create divergence between what ships and what the maintainer is using.

For normal downstream projects, install scripts copy the Writ surface into the target platform directories.

## Related

- [AGENTS.md](../../../AGENTS.md)
