# Story 1: Artifact Integrity Convention in `_preamble.md`

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None
> **Story Points:** 2

## User Story

As a **Writ command author**, I want **a standing Artifact Integrity rule in the preamble**, so that **every command has one consistent, adapter-neutral way to verify its inputs and fail early with a helpful repair offer.**

## Acceptance Criteria

1. **Given** `_preamble.md`, **when** I read it, **then** it has an `## Artifact Integrity` section defining the Required Artifacts convention (required vs optional), the check-then-HALT behavior, and bounded repair (name the creating command, no auto-mutation).
2. **Given** the section, **when** a command declares required artifacts, **then** the preamble's rule tells it to HALT + offer repair on required absence and warn+degrade on optional absence.
3. **Given** the section, **when** read on any platform, **then** it uses only generic existence checks (adapter-neutral).

## Implementation Tasks

- [ ] Add the `## Artifact Integrity` section to `commands/_preamble.md` per technical-spec §1 (after "File Organization").
- [ ] Include the required/optional distinction, HALT + bounded-repair behavior, and the common artifact → creating-command map.
- [ ] State adapter neutrality explicitly.
- [ ] Ensure wording aligns with existing preamble tone and the Prime Directive (no auto-mutation without confirmation).

## Technical Notes

- This is the foundation Stories 2–3 build on; keep it concise (preamble is shared standing instructions, not a manual).
- See `sub-specs/technical-spec.md → §1`.

## Definition of Done

- [ ] `_preamble.md` has the Artifact Integrity section covering convention + HALT + repair + neutrality.
- [ ] Tone consistent with the rest of the preamble.

## Context for Agents

- **Files in scope:** `commands/_preamble.md`.
- **Format reference:** `sub-specs/technical-spec.md → §1`.
- **Business rules:** required vs optional; bounded repair; adapter-neutral.
- **Downstream:** Stories 2 (context.md map) and 3 (declarations) depend on this convention.
