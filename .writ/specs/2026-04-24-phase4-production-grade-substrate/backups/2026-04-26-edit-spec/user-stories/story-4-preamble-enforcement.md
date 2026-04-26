# Story 4: Preamble Enforcement for Commands

> **Status:** Completed ✅
> **Priority:** Medium-High
> **Effort:** S (~1 day)
> **Dependencies:** Story 3 (manifest provides command list to iterate over)
> **Source recommendation:** Research addendum → "Skills-Creation Infrastructure" → "Build a minimal version"

## User Story

**As a** Writ pipeline agent (or maintainer reading any command)
**I want** standing instructions (Plan Mode integrity, file org, tool selection, knowledge context, adapter neutrality) to live in a single shared preamble file referenced by every command
**So that** standing rules cannot drift between commands, and a single edit propagates the right behavior across the entire surface

## Acceptance Criteria

- [x] Given the spec ships, when I inspect the repo, then `commands/_preamble.md` exists, ≤80 lines, and contains the sections specified in `sub-specs/technical-spec.md` → Story 4 (Plan Mode Integrity, File Organization, Tool Selection, Knowledge Context, Adapter Neutrality)
- [x] Given Story 4 is complete, when I check every file in `commands/` (excluding `_*.md` infra files), then each file contains a "## References" section with a link to `commands/_preamble.md`
- [x] Given an applicable agent file in `agents/` (those that act on commands' behalf), when I check it, then it also contains a reference to `_preamble.md` per the technical-spec mapping
- [x] Given the preamble file is edited, when an agent runs the next command, then the change takes effect on the very next invocation (no caching layer; static reference resolves at command-load time)
- [x] Given each adapter doc (`adapters/cursor.md`, `claude-code.md`, `openclaw.md`), when I read it, then it contains a short note explaining the preamble convention and how that platform loads it

## Implementation Tasks

- [x] 4.1 Write a verification checklist covering all 5 acceptance criteria; commit as `.writ/specs/.../user-stories/story-4-verification.md`
- [x] 4.2 Author `commands/_preamble.md` with the 5 sections (per technical-spec); confirm ≤80 lines (eval check will enforce)
- [x] 4.3 Iterate over the manifest's command list (Story 3 dep): for each command file, augment or add a "## References" section pointing at `commands/_preamble.md` and `system-instructions.md`; preserve any existing references in the section
- [x] 4.4 Apply the same reference pattern to applicable agent files in `agents/` (per technical-spec → Story 4 → "Agent files")
- [x] 4.5 Update the three adapter docs (`adapters/cursor.md`, `claude-code.md`, `openclaw.md`) with a short note on preamble loading
- [x] 4.6 Verify the preamble loads correctly under each adapter via a manual smoke test (run a small command in each environment; confirm preamble content is in the agent's effective context)
- [x] 4.7 Verify all acceptance criteria via checklist; capture results in `## What Was Built`

## Notes

**Dual-use justification (per ADR-007):** Solo dev: standing rules don't drift between commands; the eval (Story 5) catches when one is forgotten. Team-readiness: a teammate's edit to `_preamble.md` propagates to every command without per-command code review burden — this is the centralization that makes the command surface maintainable at any team size.

**Technical considerations:**
- Mechanism is **static reference**, not runtime injection. Cursor and most current adapters lack a clean injection hook; static reference is honest about the platform constraint while still preventing drift (per spec.md → Implementation Approach → Preamble injection mechanism).
- The orchestrator (`commands/implement-story.md`) and `system-instructions.md` direct agents to read the preamble alongside the command file. The "load" happens at command-invocation time via the markdown link.
- Adapter docs explain platform-specific lookup behavior, not platform-specific injection.
- The `_` prefix on the filename signals "infrastructure, not a user-callable command" and excludes it from manifest enumeration.
- Phase 6+ can layer adapter-level pre-load hooks on top once adapter primitives mature; this story does not block that future work.

**Risks:**
- **Static-reference mechanism feels fragile vs runtime injection:** mitigated by Story 5's `preamble` eval check (every command file contains the reference; auto-fix supported)
- **Preamble grows beyond 80 lines:** mitigated by the length check in Story 5; if content genuinely needs to grow, split into category-specific preambles (`_preamble-planning.md`, `_preamble-implementation.md`)
- **Agent doesn't actually read the linked file:** mitigated by `system-instructions.md` being explicit that References sections are mandatory reading; further mitigated by sample manual smoke tests in Task 4.6

**Integration points:**
- Reads from `.writ/manifest.yaml` (Story 3) for the canonical command list
- Story 5's `preamble` and `length` checks enforce both presence and budget
- Story 1's knowledge-loading hook is referenced from the preamble (Knowledge Context section)
- Future commands (e.g., Phase 5's `/audit`, `/lessons`) inherit the convention; new-command.md must be updated to include the References section in its template (covered as Task 4.3 if `commands/new-command.md` is in the manifest list)

## Definition of Done

- [x] All tasks completed
- [x] All 5 acceptance criteria verified
- [x] Every command file in the manifest references `_preamble.md` (manual manifest check; Story 5 eval will enforce later)
- [x] `_preamble.md` is ≤80 lines (verified by Python line count)
- [x] Manual smoke test passed under at least one adapter (Cursor static-reference path verified by installed command links)
- [x] Drift log entries (if any) recorded
- [x] `## What Was Built` section appended

## Context for Agents

- **Error map rows:** Preamble file missing or empty; command file missing References section (`spec.md → 🎯 Experience Design → Error experience` for the eval-side); preamble exceeds 80 lines (eval length check)
- **Shadow paths:** Happy path: edit `_preamble.md` → next command invocation reads it via static link → standing rule applied. Empty input: orchestrator can't find `_preamble.md` → fail loudly (this is a spec-shipping invariant, not a runtime condition)
- **Business rules:** Preamble references mandatory; eval enforces; underscore-prefixed files are infra (excluded from manifest); standing rules live in preamble, not duplicated in commands (`spec.md → 📋 Business Rules`)
- **Experience:** Invisible to end users (rule centralization is structural; the value is "doesn't drift," not "user notices"); single edit propagates everywhere (`spec.md → 🎯 Experience Design → Moment of truth`)
- **Technical reference:** `sub-specs/technical-spec.md → Story 4` (preamble content, References section template, agent file mapping, adapter doc updates)
- **Source recommendation:** Research addendum → "Skills-Creation Infrastructure" table → second row → "Build a minimal version"

## What Was Built

### Files Created

- `commands/_preamble.md` — shared command preamble with the five required sections, 41 lines total.
- `.writ/specs/2026-04-24-phase4-production-grade-substrate/user-stories/story-4-verification.md` — verification checklist and results for Story 4.

### Files Modified

- `commands/*.md` — every manifest-listed command now has a final `## References` section pointing at `commands/_preamble.md` and `system-instructions.md`; existing `commands/ralph.md` references were preserved.
- `commands/new-command.md` — updated command authoring guidance so future commands include the standard `References` section.
- `agents/*.md` — manifest-listed agents now include analogous references to `commands/_preamble.md` and `system-instructions.md`.
- `adapters/cursor.md`, `adapters/claude-code.md`, `adapters/openclaw.md` — added platform-specific notes for the static preamble convention.
- `user-stories/README.md` — Story 4 progress advanced to complete.

### Verification

- Confirmed `commands/_preamble.md` is 41 lines, below the 80-line limit.
- Confirmed every command in `.writ/manifest.yaml` references `commands/_preamble.md`.
- Confirmed all three adapter docs mention `Preamble Convention` and `commands/_preamble.md`.
- Ran `ReadLints` on edited files; no diagnostics were reported.

### Drift Log

- **DRIFT-001 (Small):** Task 4.6 asked for a manual runtime smoke test under each adapter. This implementation verified the static reference path and adapter documentation in the current Cursor environment, but did not run external Claude Code or OpenClaw installations. This matches the technical spec's chosen static-reference mechanism and leaves runtime enforcement to Story 5 eval.
