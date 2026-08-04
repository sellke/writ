# Story 8 — ADR Unification

> Status: Completed ✅
> Priority: Medium
> Dependencies: None

## User Story

As a Writ user planning product direction, I want Phase 2 of `/plan-product` to emit foundational decisions as numbered ADR files (ADR-000, ADR-001, etc.) in `.writ/decision-records/` instead of `decisions.md`, and I want `/create-adr` to state how product-level ADRs relate to technical ADRs, so that one structured format carries product posture and market focus without competing with an informal `decisions.md` path.

## Acceptance Criteria

**Given** `commands/plan-product.md` after this story
**When** an agent completes Phase 2 of the plan-product flow
**Then** it creates numbered ADR files (e.g. ADR-000 for product posture, ADR-001 for market focus, continuing for each major decision surfaced in discovery) under `.writ/decision-records/` and does **not** instruct creation of `decisions.md` for that phase.

**Given** those ADR files produced by plan-product
**When** a maintainer reads them
**Then** each file follows the same structured ADR format used elsewhere (Context, Decision, Alternatives, Consequences — aligned with `/create-adr` expectations).

**Given** `commands/create-adr.md` after this story
**When** a maintainer reads guidance on when to use which path
**Then** the command notes that product-level ADRs in the **000-series** are seeded by `/plan-product`, and `/create-adr` is for technical and architectural decisions — without implying duplicate formats.

**Given** either updated command file
**When** someone asks what happens to existing projects that already have `decisions.md`
**Then** both files include an explicit migration note: existing `.writ/product/decisions.md` files are **not** modified, migrated, or deleted by these instructions (soft deprecation only).

**Given** the plan-product command’s documented outputs (overview / “what gets created” section)
**When** a reader follows the doc
**Then** the output list describes ADR files under `.writ/decision-records/` (numbered) rather than `decisions.md`.

## Implementation Tasks

- [x] Define an AC verification checklist (Phase 2 outputs, ADR template fields, create-adr wording, migration note in both files, output section accuracy) and use it as the test plan for these markdown-only changes.
- [x] Update `commands/plan-product.md` Phase 2 so it directs creation of sequential ADR files in `.writ/decision-records/` (ADR-000, ADR-001, …) mapped to major discovery decisions, with standard ADR section structure.
- [x] Update `commands/plan-product.md` output / deliverables documentation to list numbered ADRs instead of `decisions.md`, and add the migration note that existing `decisions.md` files are left unchanged.
- [x] Update `commands/create-adr.md` with guidance distinguishing product-level (000-series, seeded by `/plan-product`) from technical/architectural ADRs (use `/create-adr`), plus the same migration note.
- [x] Cross-link or align terminology between plan-product and create-adr (ADR numbering, directory `.writ/decision-records/`) so agents do not contradict each other.
- [x] Walk the verification checklist against both command files; confirm every AC passes and wording is consistent with the contract summary (nine targeted markdown edits; no runtime code).

## Technical Notes

- Scope is **markdown command files only** (`commands/plan-product.md`, `commands/create-adr.md`); no application/runtime code in this story.
- **Rationale:** `decisions.md` and ADRs currently overlap in purpose; numbered ADRs remove ambiguity and keep product decisions in the same system as architecture records, with the 000-series reserved for product posture and related foundational choices from plan-product.
- **Soft deprecation:** Do not script or instruct bulk migration of legacy `decisions.md`; teams may keep or retire those files on their own timeline.
- Align generated ADR content with the structure already implied by `create-adr.md` so agents produce consistent, reviewable records.

## Definition of Done

- [x] All tasks complete
- [x] All AC verified
- [x] Tests passing
- [x] Code reviewed
- [x] Docs updated if needed
