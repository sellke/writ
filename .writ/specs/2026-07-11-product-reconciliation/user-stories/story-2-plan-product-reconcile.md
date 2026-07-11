# Story 2: `/plan-product --reconcile` mode

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

As a **Writ user**, I want to revise my existing product plan against what has
actually shipped, so that mission and roadmap stay a living compass instead of
being regenerated from scratch or left to rot.

## Acceptance Criteria

1. **Given** `plan-product.md`, **then** it documents a `--reconcile` posture
   that **replaces** greenfield discovery with scan → diff → propose.
2. **Given** `--reconcile` runs, **then** it scans existing `.writ/product/` and
   diffs it against reality: shipped specs under `.writ/specs/` (Complete),
   roadmap phase statuses, and recent git direction.
3. **Given** drift is found, **then** revisions are **proposed in Plan Mode**
   (targeted edits to mission/roadmap; new ADRs only for genuine direction
   changes) — not a from-scratch regeneration.
4. **Given** the user locks the revisions, **then** they are applied via the same
   Agent-Mode AskQuestion gate as greenfield.
5. **Given** `plan-product.md`, **then** a boundary note pairs `--reconcile`
   (revision, after) with `/verify-spec --product` (consistency, before) and
   suggests running `--product` first.

## Implementation Tasks

- [x] 2.1 Add a `--reconcile` invocation/mode section near the top of
      `plan-product.md`.
- [x] 2.2 Document the scan step (existing product docs + ADRs).
- [x] 2.3 Document the diff-vs-reality step (shipped specs, roadmap statuses, git).
- [x] 2.4 Document the propose step (Plan Mode, targeted revisions, ADRs only for
      direction changes) and the lock/apply gate.
- [x] 2.5 Add the boundary note cross-referencing `/verify-spec --product`.

## Technical Notes

- Reconcile is a **revision** posture; it must not regenerate the whole product
  package. Reuse existing Phase 2 writing mechanics only for the files that change.
- Keep the greenfield flow intact — `--reconcile` is an alternate entry, not a
  replacement of default `/plan-product`.

## Definition of Done

- [x] All acceptance criteria pass.
- [x] `--reconcile` documented as scan → diff → propose, distinct from greenfield.
- [x] Boundary note vs `--product` present.
- [x] No new command files.
