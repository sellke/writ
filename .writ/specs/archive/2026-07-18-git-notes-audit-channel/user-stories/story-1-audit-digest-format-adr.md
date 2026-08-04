# Story 1: Audit Digest Format + ADR-017

> **Status:** Complete
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

- [x] Author `.writ/docs/git-notes-audit-format.md`: spec-level digest schema (§3 of technical-spec), version rollup schema (§4), `refs/notes/writ` convention, `git log --notes=writ` read instructions, sync refspec setup, and the `writ.auditNotes` opt-out.
- [x] Author `.writ/decision-records/adr-017-git-notes-audit-channel.md`: context (Conductor precedent + WWB gap), decision, squash-survival rationale, audit-only content constraint, alternatives considered (per-story notes, default ref, full-WWB-in-note), consequences.
- [x] Cross-link: add the new doc to any docs index and reference ADR-017 from `.writ/docs/what-was-built-format.md` (WWB ↔ notes boundary).
- [x] Verify all schema fields trace to a WWB source field or a git-derived value (no orphan fields).
- [x] Add an entry to the format doc's "Non-goals" mirroring spec exclusions.

## Technical Notes

- This is a docs/ADR-only story — no command or script edits. It is the contract Stories 2–4 implement against.
- Follow existing ADR format in `.writ/decision-records/` and existing docs tone in `.writ/docs/what-was-built-format.md`.
- Digest content must exclude chain-of-thought, prompts, and transcripts (Prime Directive audit constraint).

## Definition of Done

- [x] `.writ/docs/git-notes-audit-format.md` exists and covers both schemas + ref + read/sync/opt-out.
- [x] `adr-017-git-notes-audit-channel.md` exists and follows the repo ADR format.
- [x] WWB format doc references ADR-017 for the boundary.
- [x] Every digest field is traceable to a WWB or git source.

## Context for Agents

- **Files in scope:** `.writ/docs/git-notes-audit-format.md` (new), `.writ/decision-records/adr-017-git-notes-audit-channel.md` (new), `.writ/docs/what-was-built-format.md` (cross-link edit).
- **Format reference:** `spec.md → ## Detailed Requirements`, `sub-specs/technical-spec.md → §3, §4`.
- **Business rules:** audit-only content; dedicated `refs/notes/writ`; attach to surviving commit.
- **Source data:** `.writ/docs/what-was-built-format.md` (WWB fields the digest aggregates).

---

## What Was Built

**Implementation Date:** 2026-07-19

### Files Created

1. **`.writ/docs/git-notes-audit-format.md`** (~230 lines)
   - Full contract for the audit channel: `refs/notes/writ` convention, spec-level
     digest schema (§3) with a field-provenance table, version rollup schema (§4),
     nil-WWB minimal-digest fallback, audit-only content constraint, read surface
     (`git log --notes=writ` + `/status` line), sync refspec setup, `writ.auditNotes`
     opt-out, non-blocking rule, the WWB ↔ notes boundary table, and a Non-goals
     section mirroring spec exclusions.

2. **`.writ/decision-records/adr-017-git-notes-audit-channel.md`** (~120 lines)
   - Records the decision, squash-survival rationale (attach to the landed commit
     post-merge), dedicated-ref choice, audit-only content constraint, default-on +
     clean opt-out, and four considered alternatives (per-story notes, default
     `refs/notes/commits`, full-WWB-in-note, PR-comment mirroring), with consequences.

### Files Modified

- **`.writ/docs/what-was-built-format.md`** (Purpose + Related Documentation)
  - Added the WWB ↔ git-notes audit boundary callout and an ADR-017 cross-link, so
    the forward-looking WWB record and the immutable audit digest are clearly distinct.

### Implementation Decisions

1. **Field-provenance table** — every digest field is mapped to a WWB or git source,
   satisfying the "no orphan fields" AC and giving Stories 2–4 an unambiguous contract.
2. **Opt-out as a git-config key** (`writ.auditNotes`) — per-repo, travels in
   `.git/config`, trivially checkable by ship/release/install (per technical-spec §5).

### Test Results

**Verification:** Static (methodology repo — no runtime)
- ✅ `scripts/eval.sh --check=git-notes-audit` → PASS (format/ADR/WWB scenarios green)

**Coverage:** N/A (documentation deliverable)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean (docs only)
- **Boundary Compliance:** Docs/ADR only; no command or script edits in this story.

### Deviations from Spec

None
