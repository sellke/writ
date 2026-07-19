# Story 2: Commit Resolver — `scripts/revert-resolve.py`

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1
> **Story Points:** 5

## User Story

As **the `/revert` command**, I want **a deterministic resolver that maps a logical unit to its commits (with ghost-commit fallback)**, so that **revert decisions rest on real git history, resilient to rewritten SHAs.**

## Acceptance Criteria

1. **Given** a story with a recorded `Commit:` SHA present in history, **when** the resolver runs, **then** it returns that commit with `source: recorded, confidence: exact`.
2. **Given** shipped work with a `/ship` `Ref:` footer, **when** no recorded SHA exists, **then** the resolver finds commits via `git log --grep "Ref: <id>"` (`source: ref-footer`).
3. **Given** a recorded SHA absent from history (rewritten), **when** the resolver runs, **then** it emits a `ghost` candidate (top message-similarity match) with a `similarity` score and does NOT auto-select it.
4. **Given** a `spec` unit, **when** the resolver runs, **then** it returns the union of its stories' commits plus the spec-scaffolding commit, ordered newest → oldest, deduped.
5. **Given** any resolution, **when** it completes, **then** it computes `base` = parent of the earliest resolved commit and warns on merge/cherry-pick duplicates.

## Implementation Tasks

- [ ] Write failing tests for the resolver (recorded / ref-footer / phase-state / ghost / spec-union / ordering / base) under `scripts/tests/`.
- [ ] Implement `scripts/revert-resolve.py` per technical-spec §2 (CLI, JSON output, four-layer resolution).
- [ ] Implement ghost-commit fuzzy match (subject token-set similarity) returning candidates, never auto-selecting.
- [ ] Implement spec-unit union (story commits + spec-scaffold commit via `--diff-filter=A`).
- [ ] Implement `base` computation and merge/duplicate warnings.
- [ ] Make it read-only (never mutates git or files).
- [ ] Verify tests pass with ≥80% coverage on the script.

## Technical Notes

- Follow the style of `scripts/spec-deps.py` / `scripts/phase-state.py` (subprocess git calls, `--json` output, `--repo` flag).
- Phase-state lookup is read-only against `.writ/state/phase-execution-*.json`.
- Similarity metric: keep dependency-free (stdlib `difflib.SequenceMatcher` on normalized subjects) to avoid new deps.
- See `sub-specs/technical-spec.md → §2`.

## Definition of Done

- [ ] `revert-resolve.py` implements all four layers + spec union + base + warnings.
- [ ] Tests pass, ≥80% coverage on the script.
- [ ] Read-only verified (no mutations).

## Context for Agents

- **Files in scope:** `scripts/revert-resolve.py` (new), `scripts/tests/` (new tests).
- **Format reference:** `sub-specs/technical-spec.md → §2`.
- **Business rules:** read-only; ghost-commit never auto-selected; newest→oldest ordering.
- **Shadow paths:** recorded (happy), footer/phase-state (nil recorded), ghost (rewritten), no commits (empty).
- **Dependency:** Story 1 defines the `> **Commit:**` field this resolver reads first.
