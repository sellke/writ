# Story 3: Test Integrity — Coverage Re-Derivation and Authenticity

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** developer reading `TEST_RESULT: PASS` with `Coverage threshold met: YES`
**I want** a script that recomputes both claims from the test tooling's own output
**So that** the number in the report is the number the tool measured, and a test that imports
nothing it claims to test stops counting as coverage of anything

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given a machine-readable coverage report and a set of new files, when `test-integrity.py coverage` runs, then it recomputes per-file line coverage from the report, reports `coverage_below_threshold` as blocking for any new file under the declared bar, and its verdict is independent of any `Coverage threshold met` value an agent supplied. `[AC-3.1]`
- [x] Given a test file whose only production import is a multi-line `import {\n…\n} from '@/…'` or a dynamic `await import('@/…')`, when `test-integrity.py authenticity` runs, then that file is **not** flagged — module specifiers are extracted from the whole file, never matched line by line. `[AC-3.2]`
- [x] Given a test file that resolves zero module specifiers into project source, when the check runs, then it reports `test_imports_no_source` as blocking, naming the file. `[AC-3.3]`
- [x] Given no coverage report, an unrecognized report format, or a source file the extractor cannot parse, when either subcommand runs, then the result is `unverifiable` with a named reason and exit 0 — never a silent `pass`, and never exit 2. `[AC-3.4]`
- [x] Given a real `yuss.app` checkout, when both subcommands run against its 147 unit test files, then `authenticity` flags exactly 4 files — `app/__tests__/dashboard-participant-workflow.test.tsx`, `app/api/user/password/__tests__/password-change.test.ts`, `app/api/user/profile/__tests__/has-stripe-customer.test.ts`, `lib/__tests__/wordmark-branding.test.ts` — and `coverage` reports 57.2% statements against a `Coverage threshold met: YES` claim; both outputs recorded verbatim in What Was Built. `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Write `scripts/tests/test_test_integrity.py` first — `unittest`, imported by path; the two false-positive fixtures (multi-line import, dynamic import) are the highest-value tests in this story and must be written before the extractor `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [x] 3.2 Implement whole-file module-specifier extraction covering `from '…'`, `import('…')` and `require('…')`, then classify each specifier as project source or external by prefix and resolution `[AC-3.2, AC-3.3]`
- [x] 3.3 Implement the `authenticity` subcommand over a supplied or discovered test-file set, with `inspected.files` populated so zero-tests-examined cannot read as clean `[AC-3.3, AC-3.4]`
- [x] 3.4 Implement the `coverage` subcommand: locate and parse the coverage report, recompute per-file line coverage, and compare against the declared threshold and the prior baseline for modified files `[AC-3.1, AC-3.4]`
- [x] 3.5 Implement the `unverifiable` paths for both subcommands — absent report, unknown format, unparseable source — each with a named reason and exit 0 `[AC-3.4]`
- [x] 3.6 Write `scripts/eval-test-integrity.py` fixture scenarios and register `test-integrity` in `scripts/eval.sh` with finding-code bindings against both the checker and Story 1's doc, plus `forbid_literal` read-only guards `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [x] 3.7 Run both subcommands against a real yuss checkout, record output verbatim, and verify tests pass with ≥80% coverage on new code and 100% on error paths `[AC-3.5]`

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

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

---

## What Was Built

**Implementation Date:** 2026-08-14

### Files Created

1. **`scripts/test-integrity.py`** (848 lines)
   - `authenticity` — whole-file module-specifier extraction, resolution, and
     the `test_imports_no_source` verdict
   - `coverage` — re-derives per-file line coverage from lcov, Jest
     `coverage-summary.json`, Istanbul `coverage-final.json`, and Cobertura XML
   - Ships to target projects
2. **`scripts/tests/test_test_integrity.py`** (106 tests)
   - Written before the extractor, per task 3.1
3. **`scripts/eval-test-integrity.py`** (21 scenarios)

### Files Modified

- **`scripts/eval.sh`** (`CHECKS` array + new `check_test_integrity()`)
  - Binds the four finding codes and three `unverifiable` reasons against both
    the checker and the classification doc, asserts the whole-file extraction
    property positively, and adds three `forbid_literal` read-only guards

### Implementation Decisions

1. **The claim is unrepresentable, not merely ignored** — AC-3.1 requires the
   coverage verdict be independent of any `Coverage threshold met` value an
   agent supplied. Rather than accept and discard such a parameter, `coverage()`
   simply has none. A test asserts the signature contains no `claim`-shaped
   parameter, so the guarantee cannot be softened by a later edit that "just
   passes the claim through for reporting".
2. **`from '…'` alone covers both import forms** — the `from` clause and its
   specifier always sit together no matter how many lines the brace list spans.
   Scanning the whole text therefore needs no special multi-line case; the
   multi-line bug exists only in implementations that iterate lines first.
3. **Comments are stripped before extraction** — otherwise a commented-out
   import vouches for a file that no longer imports anything.
4. **Unresolvable project-shaped specifiers get the benefit of the doubt** —
   generated types and build-time path mappings this module cannot see are
   common. A false positive costs more than a false negative here, and the
   asymmetry is deliberate and documented.
5. **Scope is decided by the project, then by the driver** — `testPathIgnorePatterns`
   is read from the project's own jest config, because the project's runner
   already decides what counts as a unit test. Where no patterns are readable,
   a test importing `@playwright/test`, `cypress`, `puppeteer` and similar is
   treated as out of scope: it exercises production code through a browser
   without importing any of it, so the finding is meaningless against it. Both
   are recorded in `inspected.out_of_scope` rather than silently dropped.
6. **Judging nothing is `unverifiable`, not `pass`** — see DEV-004 below.

### Test Results

**Verification:** Automated

- ✅ 106 unit tests, 0 failures
- ✅ 21/21 eval scenarios
- ✅ `bash scripts/eval.sh` — 0 findings, 0 run errors
- ✅ Per-file coverage re-derived from the report; verdict independent of any
  supplied claim `[AC-3.1]`
- ✅ Multi-line `import {…} from` and dynamic `await import()` both extracted
  and **not** flagged `[AC-3.2]`
- ✅ `test_imports_no_source` blocking, naming the file `[AC-3.3]`
- ✅ Absent report, unknown format, truncated report, and unparseable source
  each `unverifiable` with a named reason and exit 0 `[AC-3.4]`
- ✅ Real `yuss.app` run: exactly 4 files flagged of 147, and 57.2% statements
  re-derived `[AC-3.5]`

**Coverage:** 99.7% of body statements (364/365). The single uncovered line is
`sys.exit(main())` under the `__main__` guard. Error paths are at 100%.

### AC-3.5 — Verbatim yuss Evidence Run

Checkout `ff3ad2e` (2026-08-14).

**authenticity.** `python3 scripts/test-integrity.py authenticity --project ~/Projects/yuss`

```
verdict: fail    exit: 1
inspected.files: 147    out_of_scope: 80    unparsed: []
flagged: 4
  app/__tests__/dashboard-participant-workflow.test.tsx
  app/api/user/password/__tests__/password-change.test.ts
  app/api/user/profile/__tests__/has-stripe-customer.test.ts
  lib/__tests__/wordmark-branding.test.ts
```

Exactly the four files AC-3.5 names, and exactly the 147 unit test files the
spec pins — independently confirmed by jest itself reporting
`Test Suites: 147 passed, 147 total` on the same checkout.

**coverage.** `npx jest --coverage --coverageReporters=json-summary` produced the
report; then
`python3 scripts/test-integrity.py coverage --project ~/Projects/yuss --threshold 80`:

```
verdict: unverifiable    exit: 0
measured.statements_pct: 57.2256
measured.covered_lines:  5037
measured.total_lines:    8802
measured.threshold:      80.0
inspected: {"files": 206, "method": "json-summary @ coverage-summary.json"}
```

Jest's own summary for the same run:

```
Statements   : 57.22% ( 5037/8802 )
Branches     : 52.41% ( 2957/5641 )
Functions    : 58.32% ( 1054/1807 )
Lines        : 58.2% ( 4656/8000 )
```

57.2% re-derived, against a repository whose commit bodies claim "Coverage
90–100% on all new files" and whose agent-typed `Coverage threshold met` field
would read `YES`.

### Review Outcome

**Result:** PASS

- **Iteration count:** 4 iterations — discovery scope, the config-comment
  apostrophe, the `statements`/`lines` aggregate, and the judging-nothing verdict
- **Drift:** Small — two additions recorded below
- **Security:** Clean — read-only, no subprocess, no writes; enforced by
  `forbid_literal` in CI
- **Boundary Compliance:** Reads a coverage report someone else produced; never
  runs the test suite. That separation is what lets Gate 4 call it after the
  testing agent returns.

### Deviations from Spec

- **[DEV-003] Test scope narrowed to the project's own unit-test set** — Severity: Small
  - Spec said: `authenticity` runs "over a supplied or discovered test-file set"
  - Reality: discovery honours the project's `testPathIgnorePatterns` and treats
    e2e-driver specs as out of scope
  - Resolution: the first yuss run flagged 40 files against a ground truth of 4.
    All 36 extra findings were e2e and integration specs — files the project's
    own jest config excludes, and which drive a running app through a browser
    rather than importing modules. AC-3.5 pins the examined set at "its 147 unit
    test files", which is precisely the set `testPathIgnorePatterns` defines, so
    honouring it is what the AC required rather than an extension of it.
  - Spec amendment: none — this implements AC-3.5's stated denominator.

- **[DEV-004] `coverage` with nothing to judge is `unverifiable`, not `pass`** — Severity: Small
  - Spec said: nothing explicit about an invocation supplying no `--new-files`
  - Reality: re-deriving the aggregate without judging any file against the bar
    now yields `unverifiable` with reason `nothing_inspected`
  - Resolution: the first yuss coverage run returned `pass` while reporting
    57.2% against an 80% threshold, because with no new files there was nothing
    to compare. A clean verdict on a project measuring 57% is the exact
    clean-report failure mode the parent spec exists to end, and it is the
    vacuous-pass guard applied to the second subcommand.
  - Spec amendment: none — this is the Business Rules' vacuous-pass guard, which
    already governs.

### Lessons Learned

1. **The false-positive budget is the design constraint, and it kept binding
   after the extractor was correct.** The extractor itself was right on the
   first yuss run — the 4 ground-truth files were flagged and no other unit test
   was. Every subsequent iteration was about the *denominator*: which files the
   check is entitled to judge at all. A correct predicate applied to the wrong
   population still produces 36 false positives, and would still have got the
   check muted.
2. **A project's own config comment broke the parser that read that config.**
   `testPathIgnorePatterns` is followed by a prose comment containing "tests
   that can't connect to a DB locally". The apostrophe read as a string
   delimiter and silently turned every later pattern into garbage matching
   nothing — a clean-looking parse producing a wrong answer, which is the
   failure mode the classification doc's parse-failure rule names. The fix was
   to reuse the comment stripper already written for Story 2's JSONC reader.
3. **Pushing error paths to 100% found a second live defect.** `load_aliases`
   used `.lstrip("./")` to trim a leading `./` from a tsconfig path target —
   which strips any run of `.` and `/`, silently rewriting a monorepo alias
   `["../shared/*"]` to `shared/*`, a different directory inside the project.
   Only a test that deliberately aliased outside the project surfaced it.

### Next Story

**Story 4:** `scripts/build-smoke.py` — booting the framework and telling a
compiler failure apart from an unreachable database.
