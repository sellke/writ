# Story 1: Record Story Commit SHA in `/implement-story`

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None
> **Story Points:** 2

## User Story

As a **developer who may later need to undo work**, I want **`/implement-story` to record the completion commit SHA into the story file**, so that **`/revert` can map a story to its exact commit without guessing.**

## Acceptance Criteria

1. **Given** a story completes and is committed at Step 4, **when** the commit is made, **then** the story file header gains `> **Commit:** <full-sha>`.
2. **Given** a story is re-run (re-implemented), **when** it recommits, **then** the `Commit:` field is updated (idempotent), not duplicated.
3. **Given** a legacy story file without the field, **when** it is read by the resolver, **then** absence is tolerated (resolver falls back to later layers).

## Implementation Tasks

- [ ] In `commands/implement-story.md` Step 4, after the completion commit, add a task to capture `git rev-parse HEAD` and write `> **Commit:** <sha>` into the story header block.
- [ ] Make the write idempotent (update existing field on re-run).
- [ ] Document the field in `.writ/docs/what-was-built-format.md` (or story-file conventions) as optional/backward-compatible.
- [ ] Note the ordering: SHA is recorded AFTER the completion commit (so it reflects the real commit), then no further commit is needed for the field (accept it lands with the next status update or is amended — pick and document the simpler approach).

## Technical Notes

- The completion commit happens in Step 4 item 6; the SHA field must reference that commit. Simplest: record it in the same commit is impossible (SHA unknown pre-commit) — so either (a) write the field and include it in the `user-stories/README.md` progress commit that follows, or (b) amend. Prefer (a): fold the `Commit:` write into the same file-update batch as the README progress update. Document the chosen approach.
- See `sub-specs/technical-spec.md → §1`.

## Definition of Done

- [ ] `implement-story.md` Step 4 records the story commit SHA (idempotent).
- [ ] Field documented as optional/backward-compatible.
- [ ] Manual dogfood: complete a story, confirm `> **Commit:**` appears.

## Context for Agents

- **Files in scope:** `commands/implement-story.md`, `.writ/docs/what-was-built-format.md`.
- **Format reference:** `sub-specs/technical-spec.md → §1`.
- **Business rules:** idempotent; backward-compatible.
- **Downstream:** Story 2's resolver reads this field first.
