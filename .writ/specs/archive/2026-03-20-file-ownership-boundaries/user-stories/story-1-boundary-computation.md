# Story 1 — Boundary Computation Step (Gate 0.5)

> **Status:** Completed ✅ (2026-03-20)
> **Priority:** High
> **Dependencies:** None

## User Story

As an **implement-story orchestrator**, I want to compute file ownership boundaries from story tasks and the technical spec so that the coding agent receives structured scope constraints before writing any code.

## Acceptance Criteria

- [x] **Given** a story with file paths in its task descriptions, **when** Gate 0.5 runs, **then** it produces a `boundary_map` with owned, readable, and out-of-scope tiers.
- [x] **Given** a technical spec with file paths in its architecture section, **when** Gate 0.5 runs, **then** those paths are incorporated into the boundary computation.
- [x] **Given** Gate 0 produced "don't touch X" warnings, **when** Gate 0.5 runs, **then** file X is promoted to readable or out-of-scope (overriding any task-based ownership).
- [x] **Given** no file paths are extractable from story tasks, **when** Gate 0.5 runs, **then** it falls back to directory-level inference and logs a warning that boundaries are approximate.
- [x] **Given** the story is run via `/prototype`, **when** the pipeline starts, **then** Gate 0.5 is skipped entirely.

## Implementation Tasks

- [x] Define the `boundary_map` schema in `implement-story.md` (owned/readable/out-of-scope arrays with glob support)
- [x] Add Gate 0.5 section to `implement-story.md` between Gate 0 and Gate 1
- [x] Implement boundary extraction: parse file paths from story tasks, tech spec file paths, and import graph of owned files
- [x] Implement Gate 0 warning override: arch-check "don't touch" warnings reclassify files
- [x] Add fallback logic for stories with no extractable file paths
- [x] Add `--quick` mode handling: Gate 0.5 skipped when `--quick` is passed (same as Gate 0)

## Notes

- The boundary computation is inline logic in the orchestrator, not a separate agent — it's a data transformation step, not a judgment call.
- Import graph analysis: for each owned file, check what it imports. Those imports become readable files. This catches "you'll need to read the types file but shouldn't modify it" patterns.
- The `/assess-spec` Check 5 integration is Story 3 — this story handles the core computation without assess-spec data.

## Definition of Done

- [x] Gate 0.5 section exists in `implement-story.md` with clear step-by-step logic
- [x] `boundary_map` schema is defined with examples
- [x] Fallback behavior documented for edge cases
- [x] `--quick` and `/prototype` skip behavior documented

## What Was Built

- **Date:** 2026-03-20
- **Product changes:** `commands/implement-story.md` — Gate 0.5 section with schema, extraction algorithm, arch-check overrides, fallback, skip conditions; pipeline diagram updated; Gate 1 documents passing `(none)` when skipped; Quick Mode lists Gate 0.5 skip.
- **Story 3** extended the same file with Check 5 persistence and merge rules (assess-spec integration).
