# Story 1: Audit Digest Format + ADR-017

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None
> **Story Points:** 3

## User Story

As a **Writ maintainer**, I want **a documented audit-digest format and a decision record for the git-notes audit channel**, so that **the `/ship` and `/release` integrations (Stories 2–4) build against a single, stable schema and rationale instead of inventing their own.**

## Acceptance Criteria

1. **Given** a completed spec with per-story WWB records, **when** I read `.writ/docs/git-notes-audit-format.md`, **then** it fully specifies the spec-level digest schema, the version rollup schema, the `refs/notes/writ` ref convention, and read/sync/opt-out instructions.
2. **Given** the WWB-vs-notes distinction, **when** I read ADR-017, **then** it records the decision, the squash-survival rationale (why attach post-land, not per-story), the audit-only content constraint (no transcripts/CoT), and the boundary against duplicating WWB.
3. **Given** the format doc, **when** Stories 2–4 reference it, **then** every field they emit is defined there (no undocumented fields).

## Implementation Tasks

- [ ] Author `.writ/docs/git-notes-audit-format.md`: spec-level digest schema (§3 of technical-spec), version rollup schema (§4), `refs/notes/writ` convention, `git log --notes=writ` read instructions, sync refspec setup, and the `writ.auditNotes` opt-out.
- [ ] Author `.writ/decision-records/adr-017-git-notes-audit-channel.md`: context (Conductor precedent + WWB gap), decision, squash-survival rationale, audit-only content constraint, alternatives considered (per-story notes, default ref, full-WWB-in-note), consequences.
- [ ] Cross-link: add the new doc to any docs index and reference ADR-017 from `.writ/docs/what-was-built-format.md` (WWB ↔ notes boundary).
- [ ] Verify all schema fields trace to a WWB source field or a git-derived value (no orphan fields).
- [ ] Add an entry to the format doc's "Non-goals" mirroring spec exclusions.

## Technical Notes

- This is a docs/ADR-only story — no command or script edits. It is the contract Stories 2–4 implement against.
- Follow existing ADR format in `.writ/decision-records/` and existing docs tone in `.writ/docs/what-was-built-format.md`.
- Digest content must exclude chain-of-thought, prompts, and transcripts (Prime Directive audit constraint).

## Definition of Done

- [ ] `.writ/docs/git-notes-audit-format.md` exists and covers both schemas + ref + read/sync/opt-out.
- [ ] `adr-017-git-notes-audit-channel.md` exists and follows the repo ADR format.
- [ ] WWB format doc references ADR-017 for the boundary.
- [ ] Every digest field is traceable to a WWB or git source.

## Context for Agents

- **Files in scope:** `.writ/docs/git-notes-audit-format.md` (new), `.writ/decision-records/adr-017-git-notes-audit-channel.md` (new), `.writ/docs/what-was-built-format.md` (cross-link edit).
- **Format reference:** `spec.md → ## Detailed Requirements`, `sub-specs/technical-spec.md → §3, §4`.
- **Business rules:** audit-only content; dedicated `refs/notes/writ`; attach to surviving commit.
- **Source data:** `.writ/docs/what-was-built-format.md` (WWB fields the digest aggregates).
