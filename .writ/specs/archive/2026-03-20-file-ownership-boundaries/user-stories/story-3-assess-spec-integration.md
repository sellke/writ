# Story 3 — Assess-Spec Check 5 Integration

> **Status:** Completed ✅ (2026-03-20)
> **Priority:** Medium
> **Dependencies:** Story 1

## User Story

As an **implement-story orchestrator**, I want to incorporate `/assess-spec` Check 5 file overlap data into boundary computation so that when multiple stories share file areas, the boundaries are tighter and overlap-aware.

## Acceptance Criteria

- [x] **Given** `/assess-spec` has been run and produced Check 5 data showing file overlap between stories, **when** Gate 0.5 computes boundaries for a story, **then** overlapping files are classified as readable (not owned) with an `overlap` flag unless the current story's tasks explicitly claim modification.
- [x] **Given** no assess-spec data exists (assess-spec was never run), **when** Gate 0.5 computes boundaries, **then** it proceeds with story-task-only computation (same as Story 1 baseline).
- [x] **Given** assess-spec flagged a file area as "three+ stories share" (warn severity), **when** Gate 0.5 computes boundaries, **then** that area is marked readable with `⚠️ high-overlap` and the review agent receives extra scrutiny context.

## Implementation Tasks

- [x] Define where assess-spec Check 5 data is stored/retrievable (from the assessment report or spec files)
- [x] Add assess-spec data loading to Gate 0.5: check for assessment report, extract Check 5 findings
- [x] Implement overlap-aware boundary classification: shared files default to readable unless explicitly claimed by current story tasks
- [x] Add `overlap` and `high-overlap` flags to the boundary_map schema
- [x] Pass overlap flags to the review agent for scrutiny calibration
- [x] Document fallback: no assess-spec data = baseline computation only

## Notes

- This is an enhancement on top of Story 1's baseline computation. Story 1 works without assess-spec data; this story makes boundaries smarter when that data is available.
- The assess-spec report isn't always persisted as a file — it may only exist in the conversation context. The implementation should check for both: a saved report file and assess-spec findings embedded in the spec (some users run `/assess-spec` and apply its recommendations, which updates story files).

## Definition of Done

- [x] Gate 0.5 loads assess-spec Check 5 data when available
- [x] Overlapping files are correctly classified with overlap flags
- [x] Graceful fallback when no assess-spec data exists
- [x] Review agent receives overlap context for scrutiny calibration

## What Was Built

- **Date:** 2026-03-20
- **Product changes:** `commands/implement-story.md` — Gate 0.5 step 5 (assess-spec merge), **Check 5 persistence** convention (`.writ/specs/{spec}/assessment-report.md` or embedded `## Check 5 — File overlap`), `overlap` / `⚠️ high-overlap` annotations on schema; Gate 3 passes **`boundary_overlap_summary`** to review agent.
- **Product changes:** `agents/review-agent.md` — `boundary_overlap_summary` input and scrutiny guidance for high-overlap paths.
