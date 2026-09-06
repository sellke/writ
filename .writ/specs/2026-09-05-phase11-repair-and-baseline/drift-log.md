# Drift Log — Phase 11 Stage 1: Repair and Baseline

> Parent: [`spec.md`](spec.md)

Deviations recorded during implementation. Per-story detail lives in each
story's `## What Was Built` → *Deviations from Spec*; this file carries the
spec-level entries. Append-only; `spec.md` is never auto-modified.

| ID | Story | Severity | Title |
|---|---|---|---|
| DEV-001 | 1 | Medium | `check_knowledge_integrity` also blocks on an empty `## TL;DR` |
| DEV-002 | 1 | Small | `--force` removed with a `/revert` pointer rather than bare removal |
| DEV-003 | 1 | Small | Integration-failure next action is fix-in-place / revert / abort, not `implement-phase` quarantine vocabulary |
| DEV-004 | 1 | Small | Typecheck detection list is new (`ship.md` detects no typechecker); test-runner detection borrowed as specified |
| DEV-005 | 1 | Small | Bare `*.md` tokens in `check_referenced_paths` resolve by basename anywhere in `git ls-files -co` |
| DEV-006 | 1 | Small | Allowlist self-checks (malformed row, stale row) are additional blocking findings |
| DEV-007 | 1 | Small | Lesson TL;DR reconstructed from the H1 title; payload `statement` was empty in all ten |

---

## DEV-001 — `check_knowledge_integrity` also blocks on an empty `## TL;DR`

**Severity:** Medium · **Story:** 1 · **Found:** 2026-09-06, Gate 3 review

**Spec said:** the check fails when any `.writ/knowledge/**/*.md` has a bullet whose content is a single character. **Implementation did:** additionally emits a blocking finding for a `## TL;DR` section with no text (fixture asserts it). **Why it matters:** scope expansion of a blocking gate — a future ledger entry without a statement now fails `eval.sh`. Consistent with the spec's own observation that all ten shredded entries had an empty TL;DR and with `knowledge_writeback` now rejecting empty statements. **Resolution:** ⚠️ flagged; pipeline PASS. `spec.md` unchanged; a maintainer who disagrees removes the `tldr` branch and its fixture.

## DEV-002 — `--force` removed with a `/revert` pointer

**Severity:** Small · **Story:** 1 · **Found:** 2026-09-06, Gate 3 review. Spec allowed removal; implementation removed the clause and points at `/revert` (exists) as the re-run path. `spec-lite.md` amended.

## DEV-003 — Integration-failure next action vocabulary

**Severity:** Small · **Story:** 1 · **Found:** 2026-09-06, Gate 3 review. Spec said "quarantine per `implement-phase`'s vocabulary"; quarantine is a spec-level lane concept, so at story level `implement-spec.md` offers Fix in place (`/implement-story {id} --review-only`), Revert (`/revert`), Abort. `spec-lite.md` amended.

## DEV-004 — Typecheck detection by manifest file

**Severity:** Small · **Story:** 1 · **Found:** 2026-09-06, Gate 3 review. `ship.md` detects test runners but no typechecker; test-runner detection follows `ship.md:92–96`, typecheck detection is by manifest file (`tsconfig.json` / mypy / `cargo check` / `go vet`). `spec-lite.md` amended.

## DEV-005 — Bare-name resolution by basename

**Severity:** Small · **Story:** 1 · **Found:** 2026-09-06, Gate 3 review. Path-form tokens resolve against repo root, `commands/`, and the spec archive; bare tokens resolve if any file with that basename exists in `git ls-files -co`. Matches the assessment's `objective.md` criterion but lets the dogfooding `.writ/` workspace stand in for "created by a named command" for ~10 runtime-created names (reviewer Minor 1). `spec-lite.md` amended to record the rule.

## DEV-006 — Allowlist self-checks

**Severity:** Small · **Story:** 1 · **Found:** 2026-09-06, Gate 3 review. Rows missing a command/reason and rows no longer referenced (when the creating command exists) are blocking findings. Fixtures for both added at Gate 4. `spec-lite.md` amended.

## DEV-007 — TL;DR from title

**Severity:** Small · **Story:** 1 · **Found:** 2026-09-06, Gate 3 review. The payload `statement` was empty in all ten source records (which is why the files had empty TL;DRs); the H1 is the lesson as source commits `a9b3ed8` / `2dba942` list it. Not invented content, not a distinct recovered field. `spec-lite.md` amended.
