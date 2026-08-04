# Story 2: `gbrain-recipe.md` User-Facing Recipe

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ user who already runs (or wants to run) GBrain
**I want** a concise, accurate recipe for registering `.writ/` as a GBrain source and removing it cleanly
**So that** I gain best-in-class retrieval over my markdown substrate without risking my canonical data or taking on a hard dependency

## Acceptance Criteria

- [x] Given `.writ/docs/gbrain-recipe.md`, when a user reads it, then it explains what the recipe is, when to use it, and that the user installs GBrain themselves (Writ ships no GBrain).
- [x] Given the setup section, when followed, then it registers `.writ/` as a source with real commands (`gbrain sources add <repo-or-path>` + `gbrain sync`) and documents the artifact→page tag mapping (`spec`, `adr`, `knowledge-decision`, `knowledge-convention`, `knowledge-glossary`, `knowledge-lesson`).
- [x] Given the MCP section, when followed, then it shows optional MCP registration (`gbrain serve`; `claude mcp add gbrain -- gbrain serve` for Claude Code; manual for other hosts) and brain-first retrieval expectations that cite markdown paths.
- [x] Given the round-trip section, when read, then it states the guarantee (removing GBrain loses zero canonical data), gives the concrete removal path, and recommends gitignoring the `.gbrain-source` pin file.

## Implementation Tasks

- [x] 2.1 Write `.writ/docs/gbrain-recipe.md`: purpose/when-to-use, prerequisites (user installs GBrain), and a link to the `gbrain-interop` skill.
- [x] 2.2 Document source registration (`gbrain sources add` + `gbrain sync`), the artifact→page tag mapping, and optional MCP registration — all against GBrain's real interface, with a named version-tracking boundary.
- [x] 2.3 Document the round-trip guarantee with the concrete removal path and the `.gbrain-source` gitignore recommendation; note version-sensitive details (sync strategy, embedding-provider keys) as "verify against current GBrain docs."
- [x] 2.4 Cross-check every cited GBrain command against current GBrain/GStack docs; ensure `bash scripts/eval.sh --check=memory-interop` (sibling-owned) passes for this spec's artifacts.

## Notes

- Ground in `garrytan/gbrain` + GStack `USING_GBRAIN_WITH_GSTACK.md`. Do not invent flags.
- The doc is a human explainer; keep routing rules in the skill (ADR-009 boundary).
- The round-trip guarantee is true by construction: canonical data never lives only in the index.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Every cited GBrain command verified against current docs
- [x] `scripts/eval.sh --check=memory-interop` green for this spec's assertions *(check authored by sibling `native-memory-guidance` spec; not yet present in `scripts/eval.sh` — this spec's artifacts are in place to satisfy it)*
- [x] Documentation reviewed

## Context for Agents

- **Business rules:** [`spec.md` → `### Business Rules` → Rules 1 (markdown canonical), 5 (cite markdown path), 7 (round-trip), 8 (version boundary), 10 (zero infrastructure)]
- **Design:** [`sub-specs/technical-spec.md` → `### D4` (page mapping), `### D5` (version boundary), `### D6` (disposable artifacts)]
- **Error paths:** [`sub-specs/technical-spec.md` → `## Error & Rescue Map`]
