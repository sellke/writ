# Story 3: Test Integrity — Coverage Re-Derivation and Authenticity

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** developer reading `TEST_RESULT: PASS` with `Coverage threshold met: YES`
**I want** a script that recomputes both claims from the test tooling's own output
**So that** the number in the report is the number the tool measured, and a test that imports
nothing it claims to test stops counting as coverage of anything

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given a machine-readable coverage report and a set of new files, when `test-integrity.py coverage` runs, then it recomputes per-file line coverage from the report, reports `coverage_below_threshold` as blocking for any new file under the declared bar, and its verdict is independent of any `Coverage threshold met` value an agent supplied. `[AC-3.1]`
- [ ] Given a test file whose only production import is a multi-line `import {\n…\n} from '@/…'` or a dynamic `await import('@/…')`, when `test-integrity.py authenticity` runs, then that file is **not** flagged — module specifiers are extracted from the whole file, never matched line by line. `[AC-3.2]`
- [ ] Given a test file that resolves zero module specifiers into project source, when the check runs, then it reports `test_imports_no_source` as blocking, naming the file. `[AC-3.3]`
- [ ] Given no coverage report, an unrecognized report format, or a source file the extractor cannot parse, when either subcommand runs, then the result is `unverifiable` with a named reason and exit 0 — never a silent `pass`, and never exit 2. `[AC-3.4]`
- [ ] Given a real `yuss.app` checkout, when both subcommands run against its 147 unit test files, then `authenticity` flags exactly 4 files — `app/__tests__/dashboard-participant-workflow.test.tsx`, `app/api/user/password/__tests__/password-change.test.ts`, `app/api/user/profile/__tests__/has-stripe-customer.test.ts`, `lib/__tests__/wordmark-branding.test.ts` — and `coverage` reports 57.2% statements against a `Coverage threshold met: YES` claim; both outputs recorded verbatim in What Was Built. `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write `scripts/tests/test_test_integrity.py` first — `unittest`, imported by path; the two false-positive fixtures (multi-line import, dynamic import) are the highest-value tests in this story and must be written before the extractor `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [ ] 3.2 Implement whole-file module-specifier extraction covering `from '…'`, `import('…')` and `require('…')`, then classify each specifier as project source or external by prefix and resolution `[AC-3.2, AC-3.3]`
- [ ] 3.3 Implement the `authenticity` subcommand over a supplied or discovered test-file set, with `inspected.files` populated so zero-tests-examined cannot read as clean `[AC-3.3, AC-3.4]`
- [ ] 3.4 Implement the `coverage` subcommand: locate and parse the coverage report, recompute per-file line coverage, and compare against the declared threshold and the prior baseline for modified files `[AC-3.1, AC-3.4]`
- [ ] 3.5 Implement the `unverifiable` paths for both subcommands — absent report, unknown format, unparseable source — each with a named reason and exit 0 `[AC-3.4]`
- [ ] 3.6 Write `scripts/eval-test-integrity.py` fixture scenarios and register `test-integrity` in `scripts/eval.sh` with finding-code bindings against both the checker and Story 1's doc, plus `forbid_literal` read-only guards `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [ ] 3.7 Run both subcommands against a real yuss checkout, record output verbatim, and verify tests pass with ≥80% coverage on new code and 100% on error paths `[AC-3.5]`

## Notes

**Technical considerations:** The specifier extractor is the whole story. A line-oriented
regex is the obvious implementation and it is wrong: measured against yuss's 147 unit test
files it flagged 22 where the truth is 4, an 82% false-positive rate, because multi-line
`import {` blocks and dynamic `await import()` calls both escape it. Extract specifiers from
the entire file text, not per line. The parent spec's Evidence Base §2 records all three
measurement passes and their disagreement — that table is the fixture set.

Classifying a specifier as "project source" needs care beyond a `@/` or `./` prefix check: a
relative import of a test helper is not production source, and an aliased import may resolve
outside the project. Resolve where cheaply possible, and where not, prefer flagging nothing
over flagging wrongly — a false positive on this check costs more than a false negative,
because a check that cries about good tests gets muted and takes the four real findings with
it.

**Risks:** Coverage report formats vary (lcov, Jest JSON summary, coverage.py XML). Supporting
one well and emitting `unverifiable` for the rest is correct and honest; guessing at a format
and misparsing it produces a confident wrong number, which is worse than no number. The parent
spec's stack-support rule already licenses the narrow answer.

Second risk: a test that legitimately tests only types or only constants will trip
`test_imports_no_source`. That is a waiver case, not a bug — but if the waiver list grows past
a handful on a real project, the heuristic is wrong and should be narrowed rather than
waived around.

**Integration:** Story 5 wires both subcommands into Gate 4, where the `coverage` verdict
overrides the testing agent's self-reported field. This story must therefore produce a verdict
that is meaningful standalone — Gate 4 consumes it, it does not depend on Gate 4.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** Parse coverage report (absent / unknown format), Extract module
  specifiers (multi-line import / dynamic import / unparseable file) — from
  `sub-specs/technical-spec.md` → `## Error & Rescue Map`
- **Shadow paths:** Happy, Nil input, Empty input (zero tests examined → `unverifiable`),
  Upstream error (truncated coverage report) — from `sub-specs/technical-spec.md` →
  `## Shadow Paths`
- **Business rules:** the verdict trichotomy, the vacuous-pass guard — from `spec.md` →
  `## 📋 Business Rules`
- **Ground truth fixture:** `spec.md` → `## Evidence Base` §1 (57.23% statements, absent
  `coverageThreshold`, `app/` excluded from collection) and §2 (the three-method measurement
  table and the 4 true positives)
- **The claim being verified:** `agents/testing-agent.md:133` —
  `- **Coverage threshold met:** [YES/NO]` — and the exit criterion at `:19` that binds PASS
  to it
- **Precedent to mirror:** `scripts/ac-trace.py` (CLI, JSON, exit codes, determinism tests),
  `scripts/exit-criteria.py` (a re-derivation that overrides a self-report)
