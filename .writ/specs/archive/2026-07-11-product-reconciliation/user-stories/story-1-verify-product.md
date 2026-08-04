# Story 1: `/verify-spec --product` mode

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

As a **Writ user**, I want to run a consistency check over my product docs, so
that drift between mission, roadmap, and their derivatives is caught the same way
`/verify-spec` catches spec drift.

## Acceptance Criteria

1. **Given** the current repo (mission "Phase 6 (next)" vs roadmap complete),
   **when** I run `/verify-spec --product`, **then** it flags the phase-status
   mismatch as a report-only finding.
2. **Given** a `mission-lite.md` or `.writ/context.md` stale relative to
   `mission.md`, **when** the check runs in default mode, **then** it
   regenerates the derivative(s) and never rewrites `mission.md`/`roadmap.md`.
3. **Given** a mission/roadmap reference to an ADR file that does not exist,
   **when** the check runs, **then** it reports the unresolved reference.
4. **Given** `verify-spec.md`, **then** the Modes table lists `--product` and a
   "Product Consistency Checks" section documents the ~4-check set, the auto-fix
   vs report-only split, and the boundary vs `/plan-product --reconcile`.
5. **Given** no `.writ/product/` directory, **when** the mode runs, **then** it
   skips gracefully with a clear message (no error).

## Implementation Tasks

- [x] 1.1 Add the `--product` row to the Modes table in `verify-spec.md`.
- [x] 1.2 Write the "Product Consistency Checks (`--product`)" section: inputs,
      the 4 checks, and per-check disposition (report-only vs auto-fix).
- [x] 1.3 Specify auto-fix mechanics reusing the spec-lite regen pattern
      (regenerate `mission-lite.md` + `.writ/context.md`; never touch
      authoritative prose).
- [x] 1.4 Specify the product-scoped report output
      (`.writ/product/verification-YYYY-MM-DD.md`).
- [x] 1.5 Add the boundary note cross-referencing `/plan-product --reconcile`.

## Technical Notes

- The `--product` check set is **separate** from spec checks 1–7; the report
  table shows the 4 product checks.
- Reuse verify-spec Phase 4.4 regeneration semantics for derivatives.

## Definition of Done

- [x] All acceptance criteria pass.
- [x] `--product` documented in Modes table + dedicated section.
- [x] Auto-fix/report-only split and boundary note explicit.
- [x] No new command files; `/status` allowlist untouched.
