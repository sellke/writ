# Story 1: `/ralph plan` — Cross-Spec Execution Planning

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ developer who has created multiple specs
**I want** a `/ralph plan` Cursor command that scans non-complete specs, resolves cross-spec and cross-story dependencies, assesses codebase state, and emits a dependency-aware execution plan plus Ralph handoff artifacts (including state file shape and plan structure)
**So that** I have a single operational entry point to orchestrate autonomous execution across specs and can hand off from Cursor planning to CLI execution with a clear, regenerable plan

## Acceptance Criteria

- [ ] **Given** two or more specs under `.writ/specs/` with status other than Complete and story files containing Status / Dependencies metadata, **when** the developer runs `/ralph plan`, **then** the command produces a cross-spec execution ordering that respects hard dependencies (cross-spec: all stories of Spec A before Spec B when B depends on A; cross-story: story dependency graph within each spec)
- [ ] **Given** a workspace with `.writ/config.md` and observable codebase signals (e.g., package manager files, CI config) as described in the command, **when** `/ralph plan` runs, **then** the outputs include a Ralph-style codebase assessment section the developer can use to tune prompts and risk flags (not a full code audit — a structured checklist grounded in repo reality)
- [ ] **Given** a successful plan run, **when** the developer inspects generated artifacts, **then** there is a documented execution plan structure (sections, ordering rationale, eligible-next-story rules) and a designed `.writ/state/ralph-*.json` schema reference (field purposes, how it relates to existing `.writ/state/execution-*.json` patterns) in repo docs linked from the command
- [ ] **Given** the developer already ran `/ralph plan` once, **when** they change specs, stories, or the repo and run `/ralph plan` again, **then** the command re-scans current reality and treats the plan as disposable (regeneration is the norm; no assumption of immutable plan contract)
- [ ] **Given** `/ralph plan` completes, **when** the developer reviews outputs, **then** handoff artifacts exist for the CLI phase: at minimum a project-tailored prompt template and a `scripts/ralph.sh` loop script template consistent with the spec’s platform split (Cursor plan → terminal execution)

## Implementation Tasks

- [x] 1.1 Write validation scenarios (checklist or fixture-driven dry-run steps) for `/ralph plan` outputs: spec discovery, dependency ordering edge cases (cycle detection / explicit failure), presence of plan sections, state schema examples, and handoff file list
- [x] 1.2 Add `commands/ralph.md` implementing the `/ralph plan` workflow: scan `.writ/specs/*/spec.md` (and/or `spec-lite.md`) for completion status, enumerate `user-stories/*.md`, parse story metadata (Status, Priority, Dependencies), build merged dependency graph across specs
- [x] 1.3 Document the **execution plan** artifact: required sections (e.g., ordered queue, blocked items, assumptions), how “eligible next story” is chosen within constraints, and where the file lives (working document, regenerable)
- [x] 1.4 Author `.writ/docs/ralph-state-format.md` defining `.writ/state/ralph-*.json` (naming, top-level keys, story/spec identifiers, timestamps, human-readable JSON guidance, alignment with `.writ/state/execution-*.json` conventions)
- [x] 1.5 Encode **codebase assessment** steps in the command: what to look for under repo root and `.writ/config.md`, how findings surface in the plan (structured bullets, not ad-hoc prose)
- [x] 1.6 Generate **handoff artifacts** from the plan workflow: PROMPT template tailored to the project + `scripts/ralph.sh` loop script template per spec Implementation Approach (paths and minimal behavior documented in the command)
- [x] 1.7 Verify all acceptance criteria against a multi-spec fixture under `.writ/specs/` (or temporary test specs), update `SKILL.md` / install surface if new commands must be discoverable, and confirm cross-links to `/plan-product` and `/create-spec` relationship per Business Rules

## Notes

**Technical considerations**

- Deliverables are markdown commands and docs — “tests” are explicit validation scenarios and manual dry-runs; there is no automated test runner in this repo (see `AGENTS.md`).
- Reuse patterns from existing commands (`commands/create-spec.md`, `commands/implement-story.md`) for phased steps, AskQuestion gates where decisions are enumerable, and Plan Mode only if discovery is required.
- Spec discovery should ignore `Complete` specs per Business Rules; clarify how status is read (`spec.md` frontmatter vs body — match whatever convention existing specs use).
- Dependency parsing must handle: story N dependencies, cross-story within spec, and cross-spec dependencies if represented in spec metadata or story text (document the canonical source in the command).

**Integration points**

- Positions `/ralph plan` relative to `/plan-product` (strategic) and `/create-spec` (tactical) as operational ordering — see spec → Business Rules → Relationship to Other Commands.
- State file design should not fight existing execution JSON; prefer explicit fields for “which spec / story / gate” rather than overloading `execution-*.json`.
- Future stories will consume this plan and state for CLI execution; keep schema and plan sections extensible (version field in JSON).

**Risks**

- Ambiguous cross-spec dependencies if not stored consistently — mitigation: command documents required metadata format and fails loudly with remediation steps.
- Scope creep into full `/ralph status` or full CLI pipeline — keep Story 1 bounded to planning, schema, and handoff templates; stub references to later stories are OK.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Validation scenarios executed successfully (no failing checks)
- [ ] Code reviewed
- [ ] Documentation updated (`commands/ralph.md`, `.writ/docs/ralph-state-format.md`, and any linked config doc per spec)

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** [Happy Path Flow — steps 2–5 (run `/ralph plan`, scan specs and dependencies, assess codebase, generate plan and handoff, review/adjust)] — spec.md → 🎯 Experience Design → Happy Path Flow
- **Business rules:** [Execution Ordering — dependency graph hard constraints; cross-spec ordering (all of A before B); Plan Disposability — regenerate via `/ralph plan`; State as Single Source of Truth — `.writ/state/ralph-*.json` authoritative; Relationship to Other Commands — operational vs `/plan-product` / `/create-spec`)] — spec.md → 📋 Business Rules
- **Experience:** [Entry Point — `/ralph plan` after specs exist; Happy Path — multi-spec setup, interactive review, terminal handoff `./ralph.sh`] — spec.md → 🎯 Experience Design

---
