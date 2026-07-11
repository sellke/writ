# Story 1: Skill Lifecycle Schema + ADR

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer defining how skills mature
**I want to** establish the `status:` lifecycle field, its evidence schema, and the earned-state transition rules — recorded in an ADR and reflected in the manifest and the one shipped skill
**So that** every downstream tool (`/new-skill`, the lint, the catalog) and the skill-extraction spec build on one precise, agreed contract rather than inventing competing conventions

## Acceptance Criteria

- [x] Given a skill's frontmatter, when the lifecycle schema is defined, then it specifies a required `status:` field with the closed vocabulary `candidate | proven | promoted` and an `evidence:` block whose entries each carry `date`, `type` (`usage|transcript|eval|promotion`), `ref`, and `note`.
- [x] Given the earned-state rules, when they are documented, then `candidate` requires no evidence, `proven` requires ≥3 well-formed entries, and `promoted` requires the `proven` bar plus ≥1 `type: promotion` entry, with the ladder described as monotone (no skipping).
- [x] Given the lifecycle decision, when `adr-014-skill-lifecycle.md` is written, then it records the earned-state model, the three-success threshold and its GStack provenance, the manifest-mirror decision, and cites ADR-009 as the extended boundary.
- [x] Given `.writ/manifest.yaml`, when its skills schema comment is updated, then it documents the `status:` field and the earned-state rule as an additive, backward-compatible extension.
- [x] Given `skills/conventional-commits/SKILL.md` is in real use by `/ship`, `/release`, and `coding-agent`, when its frontmatter is updated, then it declares `status: proven` with three `type: usage` evidence entries citing those consumers, and the manifest entry mirrors `status: proven`.

## Implementation Tasks

- [x] 1.1 Draft the schema definition in `sub-specs/technical-spec.md` terms (already specified in D1–D3) and encode a canonical example evidence block to serve as the authoring reference.
- [x] 1.2 Write `.writ/decision-records/adr-014-skill-lifecycle.md` (Status `Accepted`, Date `2026-07-10`) covering earned-state semantics, static transition legality, the three-success threshold (GStack provenance), the evidence schema, and the manifest-mirror decision; cite ADR-009 as extended, not superseded.
- [x] 1.3 Update the `.writ/manifest.yaml` skills schema comment (lines ~215–223) to document the additive `status:` field and the earned-state rule, keeping it backward compatible with `skills: []`.
- [x] 1.4 Set `skills/conventional-commits/SKILL.md` frontmatter to `status: proven` with three well-formed `type: usage` evidence entries citing `commands/ship.md`, `commands/release.md`, and `agents/coding-agent.md`.
- [x] 1.5 Mirror `status: proven` onto the `conventional-commits` entry in `.writ/manifest.yaml`.
- [x] 1.6 Verify each acceptance criterion against the ADR, the manifest comment, and both `conventional-commits` surfaces; confirm the evidence block is well-formed against the D2 schema by inspection (Story 2 adds the automated lint).

## Notes

- The schema is the seam with `2026-07-10-skill-extraction`. Finalize it here; downstream extraction must consume it without amendment.
- `status:` lives in both the SKILL.md frontmatter (authoritative) and the manifest entry (render mirror), exactly as `description:` already does. Keep them in sync manually — the lint (Story 2) validates the frontmatter, not the mirror.
- Do not touch the stale "No production skills extracted yet" line in `.writ/docs/skills.md`; that belongs to the extraction spec.
- ADR-014 extends ADR-009's classification with an orthogonal lifecycle axis — do not restate or alter the command/agent/skill boundary itself.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] ADR-014 recorded and internally consistent with the spec
- [x] `conventional-commits` frontmatter and manifest mirror both read `proven`
- [x] Manifest schema comment documents the additive `status:` field

## Context for Agents

- **Error map rows:** [`technical-spec.md` → `## Error & Rescue Map` → `Validate status value`, `technical-spec.md` → `## Error & Rescue Map` → `Manifest schema mismatch`]
- **Design decisions:** [`technical-spec.md` → `### D1 — Status Is a Closed Three-State Vocabulary`, `technical-spec.md` → `### D2 — Evidence Is a YAML List of Typed Entries`, `technical-spec.md` → `### D3 — State Is Earned From Evidence`, `technical-spec.md` → `### D6 — Manifest Carries a Render Mirror`, `technical-spec.md` → `### D8 — ADR-014 Extends ADR-009`]
- **Business rules:** [`spec.md` → `### Business Rules` → Rules 1–8 (status vocabulary, evidence schema, thresholds), `spec.md` → `### Business Rules` → Rule 11 (manifest mirror), `spec.md` → `### Business Rules` → Rule 12 (conventional-commits proven)]
- **Requirements:** [`spec.md` → `### Detailed Requirements` → `R1 — Lifecycle Status Field`, `R2 — Evidence Block Schema`, `R3 — Earned-State Transition Rules`, `R8 — Schema, Docs, and ADR`]
- **Matrix:** [`technical-spec.md` → `## File × Story Matrix` → S1 rows for `adr-014-skill-lifecycle.md`, `.writ/manifest.yaml`, and `skills/conventional-commits/SKILL.md`]
