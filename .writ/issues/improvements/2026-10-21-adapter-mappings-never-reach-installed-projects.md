# Adapter Mappings Never Reach Installed Projects

> **Type:** Improvement
> **Priority:** High
> **Effort:** Medium
> **Created:** 2026-10-21
> **spec_ref:** .writ/specs/2026-10-22-generated-platform-trees/spec.md

## TL;DR

Commands use platform-neutral capability names and say "the adapter maps it". `install.sh` and `update.sh` do not copy `adapters/` into projects. An installed project has the commands but not the mappings they point to.

## Current State

- Found by the `2026-10-20-platform-neutral-names` UAT plan (Known Gap 1, 2026-10-21). `/prototype` now names a `canvas-preview` capability that all four adapters map, but no installed project contains an adapter file.
- `codex/AGENTS.md.template` tells Codex to read `adapters/codex.md`, which is not installed either.
- The mappings work only where the adapter can be read, such as the Writ source repo. Every installed project falls back to whatever the agent infers from the capability name.
- This predates Phase 13. It is the gap that Phase 14's "Generated trees and adapter coverage check" feature targets: generate each platform's tree from one source, and translate capability names at generation time.

## Expected Outcome

- An installed project resolves every capability name a shipped command uses. Either the generated per-platform tree replaces the neutral name with the platform's own tool and degradation text, or the installer ships the platform's adapter section the commands cite.
- A CI check fails when a shipped command uses a capability name that the installed tree cannot resolve.

## Relevant Files

- `scripts/install.sh`, `scripts/update.sh`: what gets copied (no `adapters/`)
- `adapters/*.md`: the mappings, including the new `canvas-preview` rows
- `commands/prototype.md`: Step 2.5, which names `canvas-preview`
- `codex/AGENTS.md.template`: points at `adapters/codex.md`
- `.writ/product/roadmap.md`: Phase 14, "Generated trees and adapter coverage check"

## Resolution

2026-10-22, branch `writ/phase/14/2026-10-22-generated-platform-trees` (spec `2026-10-22-generated-platform-trees`, Story 5). Each platform's root instruction file is generated from the adapter tool tables and carries a `## Capability Map` section (`Capability | On this platform | When unavailable`, one row per neutral name, `canvas-preview` and `Plan Mode` among them), so an installed agent resolves every capability name from the file its platform loads every session. `adapters/` is still not installed, and no installed file points at it.

`scripts/tests/test_install_platform_trees.sh` is the evidence. It commits a copy of the working tree, runs that copy's `install.sh --platform cursor`, `claude`, and `codex` into three fresh `git init` projects, and asserts on the installed files only:

- `.cursor/rules/writ.mdc` (Cursor): `## Capability Map` with a `canvas-preview` row and a `Plan Mode` row.
- The `CLAUDE.md` Writ block, between `<!-- writ:start -->` and `<!-- writ:end -->` (Claude Code): `## Capability Map` with both rows; the `Plan Mode` row names `EnterPlanMode`.
- The `AGENTS.md` Writ block (Codex): `## Capability Map` with both rows, and no `adapters/` substring anywhere in the block.

Result on the final tree: all 8 assertions passed. A source copy with `## Capability Map` stripped from `cursor/writ.mdc`, `claude-code/CLAUDE.md`, and `codex/AGENTS.md.template` fails on the map assertion for each stripped file, so the test reads installed files, not the source.

The second Expected Outcome, a CI check for a capability name the installed tree cannot resolve, is `python3 scripts/gen-platform-trees.py --check` (Story 4), run by `check_platform_trees` in `scripts/eval.sh`: `unmapped` for a neutral name missing from an adapter, `vendor` for a vendor tool name in `commands/`, `agents/`, or `skills/`.

The `## Installation` sections of `adapters/codex.md` and `adapters/claude-code.md` were searched for a sentence that sends an installed user to an adapter file for tool mappings. Neither has one, so neither file changed. `codex/AGENTS.md.template` no longer says to read `adapters/codex.md` (Story 3).
