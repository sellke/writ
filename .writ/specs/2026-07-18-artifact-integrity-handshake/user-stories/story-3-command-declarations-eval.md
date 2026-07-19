# Story 3: Per-Command Required Artifacts Declarations + Eval

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 1, Story 2
> **Story Points:** 3

## User Story

As a **developer running high-traffic commands**, I want **each to declare and check its Required Artifacts**, so that **commands fail early with actionable guidance instead of cryptic mid-run errors.**

## Acceptance Criteria

1. **Given** the 7 high-traffic commands (`create-spec`, `implement-story`, `implement-spec`, `implement-phase`, `ship`, `release`, `status`), **when** I read each, **then** it has a `## Required Artifacts` block marking required vs optional per technical-spec §3.
2. **Given** a required artifact is missing, **when** the command runs, **then** it HALTs with a specific message + bounded repair offer (per the preamble rule).
3. **Given** `scripts/eval.sh` runs, **then** it asserts the preamble Artifact Integrity section exists, each of the 7 commands has a Required Artifacts block, and no `.writ/index.md` was introduced.

## Implementation Tasks

- [ ] Add `## Required Artifacts` blocks to all 7 commands (technical-spec §3), matching each command's real dependencies.
- [ ] Ensure each block references the preamble Artifact Integrity behavior (don't re-explain HALT logic per command).
- [ ] Add the eval check (`eval.sh` + helper): preamble section present, 7 declarations present, `.writ/index.md` guard.
- [ ] Run `eval.sh` and confirm the new check passes.
- [ ] Manual dogfood: temporarily rename a required artifact, run a command, confirm the specific HALT + repair offer.

## Technical Notes

- Keep declarations short — they point to the shared preamble behavior, not duplicate it.
- The `.writ/index.md` guard in eval prevents accidental reintroduction of the rejected design.
- See `sub-specs/technical-spec.md → §3, §4`.

## Definition of Done

- [ ] All 7 commands have accurate Required Artifacts blocks.
- [ ] `eval.sh` gains the passing integrity/declaration/index-guard check.
- [ ] Manual HALT + repair verified on this repo.

## Context for Agents

- **Files in scope:** `commands/create-spec.md`, `implement-story.md`, `implement-spec.md`, `implement-phase.md`, `ship.md`, `release.md`, `status.md`, `scripts/eval.sh` (+ helper).
- **Format reference:** `sub-specs/technical-spec.md → §3, §4`.
- **Business rules:** declarations reference shared preamble behavior; only 7 commands; index.md guard.
- **Dependencies:** Story 1 (behavior) + Story 2 (Map/Integrity line).
