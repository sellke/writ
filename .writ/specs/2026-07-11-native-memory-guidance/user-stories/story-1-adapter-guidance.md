# Story 1: Per-Adapter Native-Memory Guidance + Mission Sweep

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None (within this spec)

## User Story

**As a** Writ user on any supported platform
**I want** clear guidance on what to keep in my platform's native memory versus the Writ ledger
**So that** negotiated decisions, conventions, and lessons stay reviewable in markdown while my platform still handles session preferences and trivia

## Acceptance Criteria

- [ ] Given each of `adapters/cursor.md`, `adapters/claude-code.md`, `adapters/codex.md`, `adapters/openclaw.md`, when a reader reaches the "Native Memory & the Writ Ledger" section, then it states the identical two-place rule: session prefs/trivia → native memory; negotiated decisions/conventions/lessons → the reviewable Writ ledger.
- [ ] Given each adapter section, when read, then it names that platform's real native-memory surface (Cursor Memories + semantic index; Claude Code `CLAUDE.md` + `.claude/agent-memory/`; Codex `AGENTS.md`; OpenClaw session state) and the anti-pattern (decisions living only in native memory are unreviewable and evaporate on churn).
- [ ] Given each adapter section, when read, then it cross-links the `gbrain-interop` skill / `.writ/docs/gbrain-recipe.md` for the external-index layer, presenting the three-layer model consistently.
- [ ] Given the active surfaces (`mission.md`, `mission-lite.md`, `README.md`, `.writ/docs/*`), when swept, then none carries stale "persistent-database knowledge layer" framing and the active mission reads "not a memory database or retrieval engine."

## Implementation Tasks

- [ ] 1.1 Draft the canonical two-place sentence and the three-layer framing (native / ledger / external index).
- [ ] 1.2 Add the "Native Memory & the Writ Ledger" section to `adapters/cursor.md`, grounded in Cursor Memories + semantic indexing.
- [ ] 1.3 Add the section to `adapters/claude-code.md`, grounded in `CLAUDE.md` + `.claude/agent-memory/`.
- [ ] 1.4 Add the section to `adapters/codex.md`, grounded in `AGENTS.md` layering.
- [ ] 1.5 Add the section to `adapters/openclaw.md`, grounded in session/file-based state; each section cross-links the `gbrain-interop` skill / recipe.
- [ ] 1.6 Sweep active surfaces for stale "persistent-database knowledge layer" framing; fix any active reference found (expected: none), leaving historical ADRs/specs untouched. Record the verification result.

## Notes

- Write the rule once; adapt only the platform-mechanics paragraph per adapter (keeps the eval assertion simple and consistency cheap).
- Place each section near existing memory/context content in that adapter (see technical-spec D2 anchors).
- Do not edit the sibling spec's skill/recipe/manifest/catalog; only reference them.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Consistent rule across all four adapters; platform mechanics accurate
- [ ] Documentation reviewed

## Context for Agents

- **Business rules:** [`spec.md` → `### Business Rules` → Rules 1–5]
- **Design:** [`sub-specs/technical-spec.md` → `### D1`, `### D2`, `### D3`]
- **Mission language:** [`.writ/product/mission.md` active "not a memory database or retrieval engine" wording]
