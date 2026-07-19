# Story 2: Commit Resolver — `scripts/revert-resolve.py`

> **Status:** Complete
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

- [x] Write failing tests for the resolver (recorded / ref-footer / phase-state / ghost / spec-union / ordering / base) under `scripts/tests/`.
- [x] Implement `scripts/revert-resolve.py` per technical-spec §2 (CLI, JSON output, four-layer resolution).
- [x] Implement ghost-commit fuzzy match (subject token-set similarity) returning candidates, never auto-selecting.
- [x] Implement spec-unit union (story commits + spec-scaffold commit via `--diff-filter=A`).
- [x] Implement `base` computation and merge/duplicate warnings.
- [x] Make it read-only (never mutates git or files).
- [x] Verify tests pass with ≥80% coverage on the script.

## Technical Notes

- Follow the style of `scripts/spec-deps.py` / `scripts/phase-state.py` (subprocess git calls, `--json` output, `--repo` flag).
- Phase-state lookup is read-only against `.writ/state/phase-execution-*.json`.
- Similarity metric: keep dependency-free (stdlib `difflib.SequenceMatcher` on normalized subjects) to avoid new deps.
- See `sub-specs/technical-spec.md → §2`.

## Definition of Done

- [x] `revert-resolve.py` implements all four layers + spec union + base + warnings.
- [x] Tests pass, ≥80% coverage on the script.
- [x] Read-only verified (no mutations).

## Context for Agents

- **Files in scope:** `scripts/revert-resolve.py` (new), `scripts/tests/` (new tests).
- **Format reference:** `sub-specs/technical-spec.md → §2`.
- **Business rules:** read-only; ghost-commit never auto-selected; newest→oldest ordering.
- **Shadow paths:** recorded (happy), footer/phase-state (nil recorded), ghost (rewritten), no commits (empty).
- **Dependency:** Story 1 defines the `> **Commit:**` field this resolver reads first.

---

## What Was Built

**Implementation Date:** 2026-07-19

### Files Created

1. **`scripts/revert-resolve.py`** (~430 lines)
   - Deterministic, read-only logical-unit → commit resolver. CLI `revert-resolve.py <unit> <id> [--repo PATH] [--spec SPEC_ID] [--json]`, `unit ∈ {story, spec}`.
   - Four-layer resolution: `recorded` (`> **Commit:**` verified via `git cat-file -e`), `ref-footer` (`git log --grep "Ref: .*<id>"`), `phase-state` (read `.writ/state/phase-execution-*.json` `commit`/`mergeCommit`), `ghost` (stdlib `difflib.SequenceMatcher` subject similarity, emitted under `ghost`, never auto-selected).
   - Spec-unit union (all story commits + spec-scaffold via `git log --diff-filter=A -- <spec>/spec.md` + phase-state). Newest→oldest ordering by `git rev-list --count` depth, dedup, merge/cherry-pick-duplicate warnings, `base` = parent of earliest. Emits the technical-spec §2 JSON shape (with a `schema` field) or a human summary.
   - `ContractError` handling mirroring `spec-deps.py`/`phase-state.py` (blocker JSON + non-zero exit).
2. **`scripts/tests/test_revert_resolve.py`** (~300 lines, 23 tests)
   - Builds disposable git repos per test; covers recorded/ref-footer/phase-state/ghost layers, spec union, ordering, base, dedup, merge warning, read-only guarantee, error paths, and CLI JSON/human/blocker output. Imports the hyphenated module via `importlib`.
3. **`scripts/eval-revert-resolve.py`** (scenario emitter)
   - Runs the real unit suite and emits PASS/FAIL TSV for `eval.sh check_revert` (single source of truth — no duplicated fixtures).

### Implementation Decisions

1. **Newness via `git rev-list --count`** — a deterministic topological-depth proxy for newest→oldest revert ordering that is stable on linear and DAG history (fixture commits can share timestamps).
2. **Ghost never auto-selects** — a missing recorded SHA yields a `ghost` candidate + warning only; a similarity floor (0.30) suppresses meaningless matches. The command layer confirms each substitution.
3. **`schema: revert-resolve-v1`** — added a schema tag (like `spec-deps`/`phase-state` helpers) for forward-compatible consumers.

### Test Results

**Verification:** Automated — `python3 -m unittest scripts.tests.test_revert_resolve` (23 tests, all pass).

**Coverage:** **90%** line coverage on `scripts/revert-resolve.py` (244 stmts, 15 missed; 100% of branches instrumented, measured via `coverage run --branch`). Exceeds the ≥80% target.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean (read-only; no shell string interpolation of untrusted input beyond `re.escape`-guarded grep patterns)

### Deviations from Spec

None. Added an optional `--spec` disambiguation flag (spec §2 lists `--repo`/`--json`) so a `story-N` present in multiple specs resolves deterministically; absent-flag single-spec behavior is unchanged.
