# Story 5 — `.writ/context.md` Auto-Loading Convention

> Status: Completed ✅
> Priority: Medium
> Dependencies: Phase A Story 1 (config persistence), Phase A Story 4 (status North Star rewrite)
> Phase A spec: `.writ/specs/2026-03-19-command-suite-evolution/`

## User Story

As a developer orchestrating Writ agents, I want `.writ/context.md` to be auto-maintained and loaded first into coding, review, and architecture-check agents so that every run starts with product mission, active spec, drift history, and issue signal—without manual injection.

## Acceptance Criteria

**Given** the spec or command documentation for this convention
**When** a maintainer reads how `.writ/context.md` works
**Then** its path (`.writ/context.md`), required sections (active product mission from `mission-lite.md` when present; active spec id, title, current story number/title, completion %; last three drift events from `drift-log.md` when present; open issues count from `.writ/issues/` when present; last-updated timestamp), and the rule that the file is **always fully regenerated** (never incrementally patched) are explicit.

**Given** `commands/implement-story.md` after this story
**When** the flow crosses each gate transition
**Then** the command instructs a **full rewrite** of `.writ/context.md` using the defined format (no merge or append of prior content).

**Given** `commands/implement-spec.md` after this story
**When** a story completes
**Then** the command instructs a **full rewrite** of `.writ/context.md` using the defined format.

**Given** `commands/status.md` after Phase A Story 4's rewrite
**When** `/status` (or equivalent) runs
**Then** the command instructs a **full rewrite** of `.writ/context.md` using the defined format.

**Given** `agents/coding-agent.md`, `agents/review-agent.md`, and `agents/architecture-check-agent.md` after this story
**When** each agent assembles its context package for a run
**Then** `.writ/context.md` is the **first** context item loaded (before other project context), when the file exists or after commands have been instructed to create it.

## Implementation Tasks

- [x] Define an AC verification checklist (write triggers per command, full-regeneration wording, first-item ordering in all three agents, section list, dependency on Phase A Story 4 `status.md`) and use it as the test plan for these markdown-only changes.
- [x] Document the `.writ/context.md` schema and regeneration rule in the parent spec (`spec.md` / `spec-lite.md`) and/or a concise note referenced from `implement-story.md`, including fallbacks when optional sources are missing.
- [x] Update `commands/implement-story.md` so gate transitions instruct **full regeneration** of `.writ/context.md` per the schema.
- [x] Update `commands/implement-spec.md` so each story completion instructs **full regeneration** of `.writ/context.md` per the schema.
- [x] Update `commands/status.md` so a status run instructs **full regeneration** of `.writ/context.md` per the schema (coordinate with Phase A Story 4's `status.md` structure).
- [x] Update `agents/coding-agent.md`, `agents/review-agent.md`, and `agents/architecture-check-agent.md` so each loads `.writ/context.md` as the **first** item in its context package.
- [x] Walk the verification checklist against all touched command and agent files; confirm every AC passes and that nothing implies incremental patching of `context.md`.

## Technical Notes

- `.writ/context.md` is **new** in this story: define format and creation convention only; the file lives at the **`.writ/` project root**, not inside a spec folder.
- **No drift accumulation:** each write replaces the entire file. Commands must not describe appending, merging sections, or patching deltas.
- **Sources:** mission snippet (1–3 sentences from `mission-lite.md` if present); active spec metadata and story progress; last three drift events from `drift-log.md` if present (else empty section); open issues count from `.writ/issues/` if present; explicit last-updated timestamp.
- `implement-story.md` already invokes coding, review, and architecture-check agents — refreshing `context.md` at gates keeps those runs aligned with the latest orchestration state.
- **Phase A Story 1** supplies stable config/convention patterns; **Phase A Story 4** owns the `status.md` rewrite — this story's `status.md` edits apply on top of that completed rewrite.
- This is the first story in Phase B. Phase A must be complete before beginning.

## Definition of Done

- [x] All tasks complete
- [x] All AC verified
- [x] Tests passing
- [x] Code reviewed
- [x] Docs updated if needed

## What Was Built

> Implemented: 2026-03-20
> Files modified: 6 (implement-story.md, implement-spec.md, status.md, coding-agent.md, review-agent.md, architecture-check-agent.md)

Defined the `.writ/context.md` schema inline in `implement-story.md` Step 2 with full fallback rules for missing sources (mission-lite, drift-log, issues). All three commands (`implement-story`, `implement-spec`, `status`) now instruct full regeneration — never patching. All three agents (`coding-agent`, `review-agent`, `architecture-check-agent`) now receive `context_md_content` as the first parameter and load it as the first item in their prompt template.
