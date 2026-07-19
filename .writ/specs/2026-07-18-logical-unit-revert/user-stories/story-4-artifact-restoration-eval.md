# Story 4: Artifact Restoration + Eval

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 3
> **Story Points:** 3

## User Story

As a **developer after a revert**, I want **Writ's artifacts reset to match reality**, so that **the spec, story status, WWB, drift-log, and context.md never claim work exists that was just undone.**

## Acceptance Criteria

1. **Given** a successful revert of a story, **when** it completes, **then** the story status → `Not Started`, its tasks/AC are unchecked, its `## What Was Built` record is annotated with a `> **Reverted:**` banner (not deleted), a `drift-log.md` revert entry is appended, and `context.md` is regenerated.
2. **Given** a spec revert, **when** it completes, **then** restoration is applied across all its stories and the spec status is reset appropriately.
3. **Given** a reverted WWB record, **when** a downstream story loads dependency WWB, **then** the reverted record is treated as non-authoritative (skipped or flagged).
4. **Given** the feature, **when** `scripts/eval.sh` runs, **then** it asserts `revert.md` references the dirty-tree guard, plan-before-mutate gate, and hard-reset second confirmation; and the resolver tests pass.

## Implementation Tasks

- [ ] Implement artifact restoration in `commands/revert.md` Phase 5 (technical-spec §4): status reset, task/AC unchecking, WWB banner, drift-log entry, context.md regeneration.
- [ ] Add the WWB "Reverted" annotation convention to `.writ/docs/what-was-built-format.md` and make the WWB loader in `commands/implement-story.md` Step 2 treat reverted records as non-authoritative.
- [ ] Add spec-level restoration (all stories + spec status).
- [ ] Add the eval check (`eval.sh` + helper): static assertions on `revert.md` rules + wire resolver tests into the suite.
- [ ] Verify end-to-end on this repo: revert a test story, confirm all artifacts consistent.

## Technical Notes

- Reuse `/implement-story`'s context.md schema for regeneration (don't invent a new one).
- WWB banner preserves history — never delete the record.
- See `sub-specs/technical-spec.md → §4, §5, §6`.

## Definition of Done

- [ ] Restoration implemented for story and spec units.
- [ ] WWB "Reverted" annotation documented + honored by the loader.
- [ ] `eval.sh` gains passing revert checks; resolver tests wired in.
- [ ] Manual end-to-end dogfood consistent.

## Context for Agents

- **Files in scope:** `commands/revert.md`, `commands/implement-story.md` (WWB loader), `.writ/docs/what-was-built-format.md`, `scripts/eval.sh` (+ helper).
- **Format reference:** `sub-specs/technical-spec.md → §4, §5, §6`.
- **Business rules:** full restoration; WWB preserved+annotated; reverted WWB non-authoritative downstream.
- **Dependency:** Story 3 wires the Phase 5 call site this story implements.
