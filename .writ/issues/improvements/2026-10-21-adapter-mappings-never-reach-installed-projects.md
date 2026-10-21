# Adapter Mappings Never Reach Installed Projects

> **Type:** Improvement
> **Priority:** High
> **Effort:** Medium
> **Created:** 2026-10-21
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

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
