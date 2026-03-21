# Story 2 — Coding Agent & Review Agent Integration

> **Status:** Completed ✅ (2026-03-20)
> **Priority:** High
> **Dependencies:** Story 1

## User Story

As an **AI coding agent**, I want to receive file ownership boundaries as a structured input so that I can flag when my implementation touches files outside my owned scope, giving the review agent clear violation signals to check.

## Acceptance Criteria

- [x] **Given** a `boundary_map` is passed to the coding agent, **when** the agent modifies an owned file, **then** no flag is raised.
- [x] **Given** a `boundary_map` is passed to the coding agent, **when** the agent modifies a readable file, **then** its output includes a `BOUNDARY_DEVIATION` entry with the file path and reason.
- [x] **Given** a `boundary_map` is passed to the coding agent, **when** the agent modifies an out-of-scope file, **then** its output includes a `BOUNDARY_VIOLATION` entry with the file path and reason.
- [x] **Given** the review agent receives coding agent output with boundary deviations, **when** it reviews the implementation, **then** it evaluates each deviation and includes a boundary compliance section in its report.
- [x] **Given** no `boundary_map` is provided (e.g., `--quick` mode), **when** the agents run, **then** they behave exactly as today — no boundary checking.

## Implementation Tasks

- [x] Add `boundary_map` to the coding agent input parameters in `agents/coding-agent.md`
- [x] Add boundary awareness instructions to the coding agent prompt template: check modified files against boundary_map, flag deviations
- [x] Define `BOUNDARY_DEVIATION` and `BOUNDARY_VIOLATION` output format in coding agent structured output
- [x] Add boundary compliance section to the review agent in `agents/review-agent.md`
- [x] Update review agent to evaluate deviations: justified (new info) vs. unjustified (scope creep)
- [x] Ensure graceful degradation: no boundary_map = no boundary checking (backward compatible)

## Notes

- **DEVIATION vs. VIOLATION:** A deviation is modifying a readable file (may be justified — the agent needed to add an export, for example). A violation is modifying an out-of-scope file (likely scope creep, should rarely be justified).
- The review agent doesn't auto-fail on deviations — it evaluates the reason. A deviation with a good reason (e.g., "needed to add a type export for the new function") is acceptable. A violation without justification should be flagged as a review finding.
- The architecture check agent (`agents/architecture-check-agent.md`) needs a minor update: its "Warnings for Coding Agent" output should note when a warning overrides a boundary (so Gate 0.5 can consume it).

## Definition of Done

- [x] Coding agent input parameters include `boundary_map`
- [x] Coding agent output includes deviation/violation flags when boundaries are crossed
- [x] Review agent includes boundary compliance in its review report
- [x] Backward compatible — no boundary_map means no boundary behavior

## What Was Built

- **Date:** 2026-03-20
- **Product changes:** `agents/coding-agent.md` — `boundary_map` input, prompt rules, **### Boundary Compliance** output block; `(none)` / empty skip semantics.
- **Product changes:** `agents/review-agent.md` — `boundary_map` + `boundary_overlap_summary` inputs, category **6. Boundary Compliance**, output table **### Boundary Compliance**.
- **Product changes:** `agents/architecture-check-agent.md` — **BOUNDARY OVERRIDE:** guidance for Gate 0.5 consumption.
