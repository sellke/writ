# Guide user projects to encode architecture rules as lint rules

> **Type:** Feature
> **Priority:** Normal
> **Effort:** Medium
> **Created:** 2026-09-26
> **spec_ref:** .writ/specs/archive/2026-09-26-arch-lint-and-follow-ups/spec.md

## TL;DR

Gate 2 already runs a project's own linters. Import and layer rules written as lint rules (dependency-cruiser, eslint-plugin-boundaries, import-linter, ArchUnit) become a blocking, mechanical architecture check on every story, with no model judgment. Writ does not yet tell projects to do this. Excluded from `2026-09-26-drift-arch-guards`.

## Current State

- `2026-09-26-drift-arch-guards` added boundary crossings (file-level scope) and architecture-class Large drift (agent judgment against the locked contract).
- Neither checks intended module layering; Gate 3 agents have no codified architecture to judge "integrity" against beyond the spec and ADRs.

## Expected Outcome

- `/plan-product` or `/create-adr` suggests encoding layer and import constraints as lint rules for the detected stack, with one example per ecosystem.
- Gate 2's linter detection surfaces those rules as the architecture check, and the story report names when none exist.

## Relevant Files

- `commands/implement-story.md` (Gate 2)
- `commands/plan-product.md`, `commands/create-adr.md`
- `.writ/docs/` (new guidance doc)

## Resolution

2026-09-26, commits cb1659c and 4edbe5b (spec `2026-09-26-arch-lint-and-follow-ups`, Stories 3 and 4). Gate 2 runs a detected dependency-cruiser or import-linter ruleset via `scripts/arch-lint.py detect` and reports `arch-lint:`; `.writ/docs/architecture-lint.md` ships one example per tool; `/create-adr` asks for an Enforcement note. A `/plan-product` hook was left out by the spec's scope decision. TypeScript dependency-cruiser configs are tracked in `improvements/2026-09-26-arch-lint-typescript-depcruise-configs.md`.
