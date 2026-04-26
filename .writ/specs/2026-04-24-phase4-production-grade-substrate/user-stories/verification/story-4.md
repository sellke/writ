# Story 4 Verification Checklist

> **Story:** [Preamble Enforcement for Commands](../story-4-preamble-enforcement.md)
> **Date:** 2026-04-24
> **Verifier:** Writ agent

## Acceptance Criteria

- [x] `commands/_preamble.md` exists, is <=80 lines, and contains the five required sections: Plan Mode Integrity, File Organization, Tool Selection, Knowledge Context, Adapter Neutrality.
- [x] Every command listed in `.writ/manifest.yaml` has one `## References` section containing `commands/_preamble.md`.
- [x] Every command listed in `.writ/manifest.yaml` references `system-instructions.md` in its `## References` section.
- [x] Manifest agent files in `agents/` include analogous references to `commands/_preamble.md` and `system-instructions.md`.
- [x] Adapter docs for Cursor, Claude Code, and OpenClaw describe the preamble convention and how each platform loads it.

## Verification Commands

- `commands/_preamble.md` line count checked with Python: 41 lines.
- Manifest command coverage checked with Python: all listed commands reference `commands/_preamble.md`.
- Adapter convention notes checked with ripgrep for `Preamble Convention` and `commands/_preamble.md`.
- IDE diagnostics checked with `ReadLints` for edited command, agent, adapter, and story files.

## Notes

- Runtime smoke under external Claude Code and OpenClaw installations was not run in this Cursor session. Story 4's implemented mechanism is static markdown references; adapter-specific runtime enforcement remains documentation-driven until Story 5 adds eval coverage.
