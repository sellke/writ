# Story 1: Authoritative Cross-Spec Dependencies

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer executing a roadmap phase
**I want to** declare, generate, validate, and consume authoritative cross-spec dependencies
**So that** phase execution follows a deterministic, valid dependency graph without confusing spec sequencing with story-level dependencies

## Acceptance Criteria

- [x] Given a new spec is created, when `/create-spec` writes its metadata header, then it emits `> **Dependencies:** [spec-folder-id, ...]` in declared order or `> **Dependencies:** []` when no cross-spec dependencies exist.
- [x] Given a phase contains valid explicit spec dependencies, when `/implement-phase` builds its execution plan, then it uses the explicit DAG as binding order, preserves roadmap order among otherwise independent specs, and treats shared-file or prose inference as warnings only.
- [x] Given `/verify-spec` Check 4 encounters a missing reference, self-reference, duplicate entry, or cross-spec cycle, when it validates the reachable spec graph, then it reports the exact invalid reference, edge, duplicate, or cycle as a blocking finding.
- [x] Given a legacy spec omits the optional `Dependencies` header, when dependency metadata is parsed, then the spec is treated as declaring `[]` without changing or conflating existing story dependency parsing.
- [x] Given an invalid cross-spec dependency graph is resolved before phase execution, when `/implement-phase` prepares the phase plan, then it stops before the confirmation gate and presents the affected spec and actionable graph diagnostic.

## Implementation Tasks

- [x] 1.1 Write failing fixture-based dependency contract checks in `scripts/eval.sh` covering absent, empty, ordered, malformed, missing, self-referential, duplicate, and cyclic spec headers while asserting story dependencies remain separate.
- [x] 1.2 Update `commands/create-spec.md` to collect the optional ordered cross-spec dependency list and emit the canonical `> **Dependencies:** [...]` header for every new spec, using `[]` when empty.
- [x] 1.3 Update `commands/implement-phase.md` to parse exact spec-folder IDs, build and topologically order the binding explicit DAG, use roadmap order as the independent-spec tie-breaker, and keep inferred overlap advisory.
- [x] 1.4 Extend Check 4 in `commands/verify-spec.md` to validate reference existence, self-reference, duplicate entries, and cycles across the reachable cross-spec graph without changing story dependency validation.
- [x] 1.5 Complete the `scripts/eval.sh` fixture assertions for exact blocking diagnostics, legacy-header compatibility, deterministic ordering, and the pre-confirmation stop behavior.
- [x] 1.6 Run the focused dependency fixtures in `scripts/eval.sh` and verify all happy-path, legacy, and invalid-graph cases pass with deterministic output.
- [x] 1.7 Verify every acceptance criterion against `commands/create-spec.md`, `commands/implement-phase.md`, `commands/verify-spec.md`, and `scripts/eval.sh`, then run `bash scripts/eval.sh`.

## Notes

- The `Dependencies` header is optional only for legacy specs; `/create-spec` must emit it for all newly generated specs.
- Dependency values are exact folder IDs under `.writ/specs/`. Titles and fuzzy matching are invalid, while declared input order remains available for display even though execution order is topological.
- Duplicate declarations are invalid. Any offered deduplication must preserve first-occurrence order and must not silently rewrite a locked spec.
- Cross-spec and story-level dependency graphs are distinct contracts. Existing story dependency syntax and validation must remain unchanged.
- Invalid explicit metadata is blocking; shared-file and prose overlap analysis can identify potentially missing declarations but cannot reorder a valid explicit graph.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [`technical-spec.md` → `## Error & Rescue Map` → `Parse spec dependencies`, `technical-spec.md` → `## Error & Rescue Map` → `Resolve dependency graph`]
- **Shadow paths:** [`technical-spec.md` → `## Shadow Paths` → `Dependency sequencing`]
- **Business rules:** [`spec.md` → `### Business Rules` → Rule 3 (optional ordered exact-ID array), `spec.md` → `### Business Rules` → Rule 4 (explicit dependencies bind; inference only warns), `spec.md` → `### Business Rules` → Rule 5 (Check 4 validation and separate story/spec graphs)]
- **Experience:** [`spec.md` → `### Primary User Journey` → Step 2 (validate dependencies and show ordered plan), `spec.md` → `### State Catalog` → `Invalid dependency graph`, `technical-spec.md` → `### D1 — Explicit Dependencies Are Authoritative`, `technical-spec.md` → `## File × Story Matrix` → S1 rows for commands/create-spec.md, commands/verify-spec.md, and commands/implement-phase.md]
