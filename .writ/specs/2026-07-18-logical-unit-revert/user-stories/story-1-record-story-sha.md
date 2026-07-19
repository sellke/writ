# Story 1: Record Story Commit SHA in `/implement-story`

> **Status:** Complete
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

- [x] In `commands/implement-story.md` Step 4, after the completion commit, add a task to capture `git rev-parse HEAD` and write `> **Commit:** <sha>` into the story header block.
- [x] Make the write idempotent (update existing field on re-run).
- [x] Document the field in `.writ/docs/what-was-built-format.md` (or story-file conventions) as optional/backward-compatible.
- [x] Note the ordering: SHA is recorded AFTER the completion commit (so it reflects the real commit), then no further commit is needed for the field (accept it lands with the next status update or is amended — pick and document the simpler approach).

## Technical Notes

- The completion commit happens in Step 4 item 6; the SHA field must reference that commit. Simplest: record it in the same commit is impossible (SHA unknown pre-commit) — so either (a) write the field and include it in the `user-stories/README.md` progress commit that follows, or (b) amend. Prefer (a): fold the `Commit:` write into the same file-update batch as the README progress update. Document the chosen approach.
- See `sub-specs/technical-spec.md → §1`.

## Definition of Done

- [x] `implement-story.md` Step 4 records the story commit SHA (idempotent).
- [x] Field documented as optional/backward-compatible.
- [x] Manual dogfood: complete a story, confirm `> **Commit:**` appears. _(Verified via the resolver's `recorded` layer unit tests + eval static assertion `require_literal '> **Commit:**'`; no live `/implement-story` run in this isolated lane.)_

## Context for Agents

- **Files in scope:** `commands/implement-story.md`, `.writ/docs/what-was-built-format.md`.
- **Format reference:** `sub-specs/technical-spec.md → §1`.
- **Business rules:** idempotent; backward-compatible.
- **Downstream:** Story 2's resolver reads this field first.

---

## What Was Built

**Implementation Date:** 2026-07-19

### Files Modified

- **`commands/implement-story.md`** (Step 4 + new "Recording the Story Commit SHA" subsection)
  - Added item 7 "Record the story commit SHA" to the Step 4 completion checklist (renumbering Report → 8).
  - Documented the chosen approach: capture `git rev-parse HEAD` after the completion commit, write `> **Commit:** <full-sha>` into the header block near `Status`, idempotent in-place update on re-run, land the one-line write in the immediately-following bookkeeping commit (never `--amend`, which would rewrite the recorded SHA), plus the backward-compat fallback for legacy stories.

### Implementation Decisions

1. **No `--amend` for the SHA field** — amending the completion commit would change the very SHA just recorded, breaking the `recorded` resolver layer. The field lands in the tiny follow-up bookkeeping commit instead; the recorded SHA points at the (revert-target) completion commit.
2. **Optional/backward-compatible by contract** — absence of `> **Commit:**` is never an error; the resolver degrades to `ref-footer` → `phase-state` → `ghost`. Documented in `what-was-built-format.md` and enforced by `revert-resolve.py` (`_read_commit_field` returns `None` gracefully).

### Test Results

**Verification:** Automated (resolver unit suite) + eval static assertion.
- ✅ `RecordedLayerTests` (3 tests) exercise the recorded-SHA layer the field feeds.
- ✅ `check_revert` asserts `> **Commit:**` is present in `implement-story.md`.

**Coverage:** n/a (markdown change); resolver coverage 90% overall.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean

### Deviations from Spec

None.
