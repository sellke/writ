# Generalize GBrain interop into engine-detected second-brain retrieval

> **Type:** Improvement
> **Priority:** Normal
> **Effort:** Medium
> **Created:** 2026-10-03
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

Replace the GBrain-only `gbrain-interop` skill with a provider-neutral retrieval skill that separates *corpus* (what to search, optionally including external vault paths) from *engine* (how to search: detected GBrain / QMD / other index, else grep), and wire `/implement-story` as its first consumer.

## Current State

- `skills/gbrain-interop` is GBrain-specific and `candidate` with zero consumers — no command or agent loads it (Goldilocks assessment lists it as a dead end)
- `implement-story` step 5 loads knowledge context by plain grep over `.writ/knowledge/`, so even a healthy brain is never used
- Live GBrain behavior was never verified (roadmap Phase 8 handed it off as UAT scenarios 10–12)
- Corpus is implicitly `.writ/` only; no way to include an external second brain (Obsidian vault, notes folder)
- A naive "prompt for a directory path" design would reduce retrieval to grep — a path gives location, not an index or query interface, so QMD/GBrain vector recall would be lost

## Expected Outcome

- **Engine detected, never prompted:** MCP tools present → CLI health check (`gbrain doctor --json`, `qmd doctor`) → grep fallback; same detect → route → cite → write markdown-first → degrade protocol
- **Corpus declared once:** `.writ/` by default; optional external paths persisted in a gitignored, machine-local location (Writ has no project config file today — pick one)
- **Path → index bridge:** for a declared path, check whether an engine already indexes it (e.g. `qmd collection list`) and scope a vector-capable query to it (`-c <collection>`); grep only when no healthy engine covers it
- **Two brain classes:** index-over-markdown brains (GBrain, QMD, Basic Memory, Obsidian+MCP) participate fully; data-owning brains (Notion, Mem0, Letta) are read-only / one-way export, never a write target
- **ADR-011 preserved:** durable Writ knowledge still written to `.writ/`; external-path hits labeled as personal context, not project record (teammates can't verify `~/notes/...` citations)
- **First consumer:** `implement-story` step 5 routes through the skill, giving it ADR-014 evidence
- Per-provider recipe docs (GBrain existing, QMD second); `memory-interop` eval check generalized from GBrain literals to "every recipe states round-trip + markdown-first write"

## Relevant Files

- `skills/gbrain-interop/SKILL.md` - skill to generalize/replace
- `commands/implement-story.md` - step 5 grep-only knowledge load; first consumer
- `.writ/decision-records/adr-011-memory-interop-markdown-canonical.md` - governing invariant (markdown canonical, indexes disposable)

## Notes

- Avoid a Writ-owned provider registry or retrieval layer — ADR-011 rejected Option C; keep it skill + recipe docs
- ADR-011 review trigger: more providers = more recipe maintenance; demote any recipe needing more than doc-level upkeep for two consecutive releases
- QMD is a cheap second engine to prove the generalization (already installed locally)
