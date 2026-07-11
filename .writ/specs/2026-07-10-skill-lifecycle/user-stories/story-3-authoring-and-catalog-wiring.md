# Story 3: Authoring + Catalog Wiring

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Stories 1, 2

## User Story

**As a** skill author and a maintainer reading the catalog
**I want to** have `/new-skill` scaffold new skills at `status: candidate`, `gen-skill.sh` render each skill's lifecycle state in the generated catalog, and `.writ/docs/skills.md` explain the lifecycle
**So that** every new skill is born in a valid, lint-clean state and the whole skill inventory's maturity is visible at a glance

## Acceptance Criteria

- [ ] Given `/new-skill <name>` scaffolds a skill, when it writes the temp lint file, the `skills/<name>/SKILL.md` file, and the manifest entry, then all three carry `status: candidate`, and the scaffold passes `scripts/lint-skill.sh` with exit `0`.
- [ ] Given the generated catalog, when `scripts/gen-skill.sh` regenerates `SKILL.md`, then the Available Skills table renders a `Status` column (`| Skill | Status | File | Description |`) showing each skill's lifecycle state.
- [ ] Given a manifest skills entry that omits `status:`, when the catalog is generated, then the generator defaults the rendered status to `candidate` rather than failing.
- [ ] Given `.writ/docs/skills.md`, when the lifecycle section is added, then it documents the three states, the earned-state thresholds, the evidence schema, and a worked example — in a region distinct from the extraction spec's edits, leaving the stale "No production skills extracted yet" line untouched.
- [ ] Given the column addition, when `bash scripts/gen-skill.sh --check` runs after regeneration, then it reports no drift.

## Implementation Tasks

- [ ] 3.1 Update `commands/new-skill.md` so the Phase 2 temp lint candidate (Step 2.1) and the Phase 3 written scaffold (Step 3.1) frontmatter both include `status: candidate`, and the Step 3.2 manifest entry includes `status: candidate`.
- [ ] 3.2 Update the `/new-skill` Core Rules and Completion sections to name `candidate` as the born lifecycle state.
- [ ] 3.3 Add a `SKILL_STATUSES` array to `scripts/gen-skill.sh` populated in both the `yq` path and the fallback line-parser path, defaulting a missing manifest `status:` to `candidate`.
- [ ] 3.4 Render the `Status` column in the Available Skills table and regenerate the root `SKILL.md` via `bash scripts/gen-skill.sh`.
- [ ] 3.5 Add a lifecycle section to `.writ/docs/skills.md` (states, thresholds, evidence schema, worked example) in a distinct region; do NOT edit the stale extraction line.
- [ ] 3.6 Verify a freshly scaffolded skill passes the Story 2 lint and renders correctly in the catalog with `candidate`.
- [ ] 3.7 Run `bash scripts/gen-skill.sh --check`, `bash scripts/lint-skill.sh skills/*/SKILL.md`, `bash scripts/eval.sh`, and `bash scripts/install.sh --dry-run`; confirm all clean.

## Notes

- The scaffold must pass the Story 2 lint the moment it is written — that is why this story depends on both the schema (Story 1) and the lint (Story 2).
- Adding the `Status` column changes generated `SKILL.md`; the regeneration and the `--check` gate belong to this story, not a later one.
- The generator default (`candidate`) matters for `2026-07-10-skill-extraction`: its appended manifest entries render even before evidence accrues.
- `.writ/docs/skills.md` is SHARED-ADDITIVE with the extraction spec. Add the lifecycle section in its own region; the extraction spec fixes the stale "No production skills extracted yet" line separately.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `/new-skill` scaffolds `candidate` in temp file, written file, and manifest entry
- [ ] Catalog renders a `Status` column; `gen-skill.sh --check` clean
- [ ] `.writ/docs/skills.md` lifecycle section added; stale extraction line untouched
- [ ] `bash scripts/eval.sh` and `bash scripts/install.sh --dry-run` clean

## Context for Agents

- **Error map rows:** [`technical-spec.md` → `## Error & Rescue Map` → `Manifest schema mismatch`, `Catalog regen`]
- **Shadow paths:** [`technical-spec.md` → `## Shadow Paths` → `/new-skill scaffold`, `Catalog render`]
- **Design decisions:** [`technical-spec.md` → `### D6 — Manifest Carries a Render Mirror`, `### D7 — Catalog Gains a Status Column`]
- **Business rules:** [`spec.md` → `### Business Rules` → Rule 2 (`/new-skill` scaffolds candidate), Rule 11 (manifest render mirror)]
- **Requirements:** [`spec.md` → `### Detailed Requirements` → `R6 — Authoring Scaffold`, `R7 — Catalog Rendering`, `R8 — Schema, Docs, and ADR`]
- **Experience:** [`spec.md` → `### Primary User Journey` → Steps 1 and 5, `spec.md` → `### State Catalog`]
- **Matrix:** [`technical-spec.md` → `## File × Story Matrix` → S3 rows for `commands/new-skill.md`, `scripts/gen-skill.sh`, `.writ/docs/skills.md`, and `SKILL.md`]
