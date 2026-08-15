# Story 2: The Quality-Config Audit

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** developer whose framework enforces gates on top of a project whose own gates may be
switched off
**I want** a read-only script that inspects the project's build, typecheck, lint and coverage
configuration and reports what is disabled
**So that** a year of running `tsc --noEmit` inside a pipeline cannot coexist with
`ignoreBuildErrors: true` in the project's own config without anyone noticing

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given a Next.js project whose `next.config.js` sets `typescript.ignoreBuildErrors` or `eslint.ignoreDuringBuilds` to `true`, when `quality-config-audit.py check` runs, then it reports `build_gate_disabled` as blocking, names the file and line, and exits 1. `[AC-2.1]`
- [x] Given a Jest project with `collectCoverageFrom` configured and no `coverageThreshold` key — or a `coverageThreshold` whose value is zero — when the check runs, then it reports `coverage_threshold_absent` as blocking, because a zero bar and an absent bar are the same bar. `[AC-2.2]`
- [x] Given a config file that is executable JavaScript or JSONC and cannot be parsed to a bounded answer, when the check runs, then it reports `could_not_parse`, downgrades every finding that file would have decided to `unverifiable`, names the file in `inspected.unparsed`, and never reports the absence of a pattern as evidence the gate is enabled. `[AC-2.3]`
- [x] Given a project with two package-manager lockfiles, a `lint` script excluding the test tree, or coverage collection excluding a directory containing shipped source, when the check runs, then it reports `duplicate_lockfile`, `tests_excluded_from_typecheck` and `coverage_scope_gap` respectively as informational findings that do not affect the exit code. `[AC-2.4]`
- [x] Given a real `yuss.app` checkout, when the check runs against it, then it reports `build_gate_disabled` for both `next.config.js:8` and `next.config.js:11`, `coverage_threshold_absent` for `jest.config.js`, `duplicate_lockfile` for `bun.lock` + `pnpm-lock.yaml`, and `coverage_scope_gap` for `app/` — and that output is recorded verbatim in this story's What Was Built record. `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Write `scripts/tests/test_quality_config_audit.py` first — `unittest`, module imported by path via `importlib.util`, one test per finding code, plus parse-failure downgrade, the zero-threshold case, determinism, and all three exit codes `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [x] 2.2 Implement config discovery and the `inspected` envelope — which files were found, which parsed, by what method, which not — before any finding logic, so a vacuous pass is structurally impossible `[AC-2.3]`
- [x] 2.3 Implement the JSONC-tolerant reader (comment and trailing-comma stripping) and the bounded regex heuristics for executable-JS configs, each emitting `could_not_parse` when it cannot bound its answer `[AC-2.3]`
- [x] 2.4 Implement the six config-audit finding codes with the severities Story 1's doc records `[AC-2.1, AC-2.2, AC-2.4]`
- [x] 2.5 Implement baseline suppression — findings present in `.writ/quality-baseline.md` are reported as acknowledged rather than blocking; a malformed baseline exits 2 rather than being ignored `[AC-2.4]`
- [x] 2.6 Write `scripts/eval-quality-config-audit.py` fixture scenarios following `scripts/eval-ac-trace.py`, and register `quality-config-audit` in `scripts/eval.sh`'s `CHECKS` array with a `check_quality_config_audit()` binding every finding code against both the checker and Story 1's doc, plus `forbid_literal` read-only guards `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [x] 2.7 Run against a real yuss checkout, record the output verbatim in What Was Built, and verify tests pass with ≥80% coverage on new code and 100% on error paths `[AC-2.5]`

## Notes

**Technical considerations:** Read-only in the strict sense `scripts/exit-criteria.py`
documents about itself — never writes a file. This is the **first** Writ script whose input
surface is the host project's own source-of-truth config rather than `.writ/**`, command
markdown, or git. That crosses the product-source/development-workspace boundary described in
`CLAUDE.md` and deserves a sentence in the module docstring saying so deliberately.

No dependencies are available. `json` and `tomllib` are stdlib; `yaml` is not. `tsconfig.json`
is JSONC and `next.config.js` / `jest.config.js` are executable JavaScript. The heuristics are
therefore pattern matches, and their honesty depends entirely on `could_not_parse` firing
whenever a match's absence is uninformative.

**Risks:** The tempting shortcut is to treat "pattern not found" as "gate enabled". That
converts every unparseable config into a clean bill of health and reproduces, exactly, the
defect this story exists to catch. The parent spec's Evidence Base §2 records the same error
being made three different ways in the research that motivated this spec — a naive line regex
over-reported by 82%, a careful human read over-reported by 50%. Bound every heuristic, and
when it cannot be bounded, say `unverifiable`.

Second risk: this check will light up on any real brownfield project. That is correct
behavior, and the baseline is what makes it survivable — but a baseline that grows every run
is a disabled check wearing a costume. Task 2.5 should make re-baselining awkward on purpose.

**Integration:** `scripts/install.sh`'s `is_shippable_script()` copies `scripts/*.py` into
every target project, so this file ships; `scripts/eval-quality-config-audit.py` does not (the
`eval-*` prefix is excluded) and `scripts/tests/` is never copied. CI runs `scripts/eval.sh`
only — never `scripts/tests/` — so the eval scenarios and `require_literal` bindings from task
2.6 are this checker's entire CI protection.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** Read `package.json`, Read `next.config.js`, Read `tsconfig.json`, Read a
  lockfile, Read baseline (absent), Read baseline (malformed) — from
  `sub-specs/technical-spec.md` → `## Error & Rescue Map`
- **Shadow paths:** Happy, Nil input, Empty input (zero config files → `unverifiable`, never
  `pass`), Upstream error — from `sub-specs/technical-spec.md` → `## Shadow Paths`
- **Business rules:** "unparseable is not absent", the vacuous-pass guard, baseline-then-ratchet
  — from `spec.md` → `## 📋 Business Rules`
- **Ground truth fixture:** `spec.md` → `## Evidence Base` §3 gives the exact yuss lines
  (`next.config.js:7–12`, `jest.config.js:30–36`, dual lockfiles with `packageManager`)
- **Precedent to mirror:** `scripts/ac-trace.py` (CLI shape, `sort_keys=True` JSON, exit
  0/1/2, `scanned_files`/`ignore_filter` inspection envelope), `scripts/eval-ac-trace.py`
  (fixture-scenario TSV harness), `scripts/eval.sh` → `check_ac_trace` (finding-code bindings
  against both checker and doc)

---

## What Was Built

**Implementation Date:** 2026-08-14

### Files Created

1. **`scripts/quality-config-audit.py`** (739 lines)
   - Read-only audit of a project's build, typecheck, lint and coverage config
   - Six config-audit finding codes plus `unsupported_stack`, the `inspected`
     envelope, baseline suppression, and the JSONC reader
   - Ships to target projects — `is_shippable_script()` copies `scripts/*.py`
2. **`scripts/tests/test_quality_config_audit.py`** (85 tests)
   - Written before the implementation, per task 2.1
   - Never copied to target projects; developer-run only
3. **`scripts/eval-quality-config-audit.py`** (19 scenarios)
   - Fixture asserter following `scripts/eval-ac-trace.py`'s TSV shape
   - Not shipped — the `eval-*` prefix is excluded by `is_shippable_script()`

### Files Modified

- **`scripts/eval.sh`** (`CHECKS` array + new `check_quality_config_audit()`)
  - Registers the check and binds all seven finding codes against **both** the
    checker and `.writ/docs/quality-signal-classification.md`, plus the verdict
    rules, the parse-failure rule, the re-baselining prohibition, the schema
    string, and three `forbid_literal` read-only guards
- **`.writ/docs/quality-signal-classification.md`** (Baseline → Format)
  - Corrected a heading-level inconsistency in Story 1's own output: the prose
    said `###` sections while the worked example used `##`. The parser
    implements `##`, matching the example.

### Implementation Decisions

1. **`could_not_parse` and its downgrade are one operation** — `Audit.could_not_parse()`
   takes the codes it invalidates as a required argument, so recording a parse
   failure without downgrading the findings that file would have decided is not
   expressible. The forbidden outcome — a clean report produced by a parser that
   gave up — is prevented structurally rather than by remembering to pair two calls.
2. **One licensed asymmetry, and only one** — a non-match is normally
   uninformative, but finding `collectCoverageFrom` in a `jest.config.js` proves
   the file was read and its shape understood, which makes a missing
   `coverageThreshold` a fact about the config rather than about the parser.
   That is the single place a non-match concludes anything, it is the rule
   Story 1's doc records, and it has its own test both ways.
3. **`strip_jsonc` is a character scan, not a regex** — a regex over the whole
   text strips a `//` living inside a string literal (a `paths` entry containing
   a URL) and corrupts the very file it was meant to rescue. Tested with a URL
   value, a glob containing `/*`, and an escaped quote.
4. **The `inspected` envelope is built before any finding logic** (task 2.2) —
   so `findings: []` with `inspected.files: 0` resolves to `unverifiable`, never
   `pass`. Asserted by a test that runs an empty project and a clean project and
   requires their verdicts to differ.
5. **Re-baselining made awkward on purpose** (task 2.5) — the checker has no
   `--update-baseline` flag, never writes, and a malformed baseline exits 2
   naming the line rather than being treated as empty. A test asserts the
   baseline file is byte-identical after a run.
6. **Measured coverage with a stdlib tracer** — Writ has no dependencies and
   `coverage` is unavailable. `trace` does not usefully instrument
   importlib-loaded modules, so coverage was measured with a `sys.settrace`
   harness that credits import-time definition lines and counts function-body
   statements.

### Test Results

**Verification:** Automated

- ✅ 85 unit tests, 0 failures — `python3 scripts/tests/test_quality_config_audit.py`
- ✅ 19/19 eval scenarios — `python3 scripts/eval-quality-config-audit.py`
- ✅ `bash scripts/eval.sh` — 0 findings, 0 run errors across all 42 checks
- ✅ `build_gate_disabled` blocking at `next.config.js:8` and `:11`, exit 1 `[AC-2.1]`
- ✅ `coverage_threshold_absent` for absent **and** zero thresholds, in both
  `jest.config.*` and a `package.json` `jest` block `[AC-2.2]`
- ✅ `could_not_parse` downgrades to `unverifiable`, names the file in
  `inspected.unparsed`, exits 0, and never reports a pattern's absence as
  evidence the gate is enabled `[AC-2.3]`
- ✅ `duplicate_lockfile`, `tests_excluded_from_typecheck`, `coverage_scope_gap`
  informational, exit code unaffected `[AC-2.4]`
- ✅ Real `yuss.app` run reproduces all four pinned findings `[AC-2.5]`

**Coverage:** 99.7% of body statements (288/289). The single uncovered line is
`sys.exit(main())` under the `if __name__ == "__main__"` guard, unreachable
in-process by construction. Error paths are at 100%.

### AC-2.5 — Verbatim yuss Evidence Run

Checkout `ff3ad2e` (2026-08-14). Command:

```
python3 scripts/quality-config-audit.py check --project ~/Projects/yuss
```

Exit code **1**, verdict `fail`, `inspected.files: 6`, `inspected.unparsed: []`.
Findings, in emitted order:

| severity | code | locator | measured |
|---|---|---|---|
| informational | `coverage_scope_gap` | `app` | 112 uncollected source files |
| informational | `duplicate_lockfile` | `bun.lock` | `bun.lock, pnpm-lock.yaml` |
| informational | `coverage_scope_gap` | `hooks` | 14 uncollected source files |
| blocking | `coverage_threshold_absent` | `jest.config.js` | `coverageThreshold: absent` |
| blocking | `build_gate_disabled` | `next.config.js:8` | `ignoreDuringBuilds: true` |
| blocking | `build_gate_disabled` | `next.config.js:11` | `ignoreBuildErrors: true` |
| informational | `tests_excluded_from_typecheck` | `package.json` | lint script `--ignore-pattern '**/__tests__/**' --ignore-pattern 'tests/**'` |
| informational | `tests_excluded_from_typecheck` | `tsconfig.json` | `**/__tests__/**, tests/**` |

```
inspected.method: bun.lock:presence; jest.config.js:pattern-match;
                  next.config.js:pattern-match; package.json:json;
                  pnpm-lock.yaml:presence; tsconfig.json:json
```

All four AC-2.5 findings reproduced exactly, including both `build_gate_disabled`
line numbers. The four additional findings are true positives the AC did not
enumerate: `hooks/` (14 first-party source files outside `collectCoverageFrom`)
and the two `tests_excluded_from_typecheck` sites.

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iterations — one for the `pocket-js` false positive,
  one for the quoted-key defect below
- **Drift:** Small — one heading-level correction to Story 1's doc, recorded above
- **Security:** Clean — read-only, no subprocess, no network, no writes.
  `forbid_literal` on `os.remove`, `.write_text(`, and `import subprocess`
  enforces this in CI
- **Boundary Compliance:** This is the first Writ script whose input surface is
  the host project's own config rather than `.writ/**`, command markdown, or
  git. The module docstring says so deliberately, per the story's Technical
  considerations.

### Deviations from Spec

- **[DEV-002] Nested packages excluded from `coverage_scope_gap`** — Severity: Small
  - Spec said: `coverage_scope_gap` fires when "coverage collection excludes a
    source directory that contains shipped code"
  - Reality: a directory carrying its own `package.json` is skipped, and the
    source walk stops at any nested manifest
  - Resolution: added, not removed, scope. The first yuss run flagged
    `pocket-js/` — a vendored sub-package with its own `package.json`,
    `next.config.js` and `package-lock.json`. Flagging a separate package as a
    coverage gap of the *root* package is a false positive, and the parent
    spec's stated risk is precisely that a check which cries about
    correctly-scoped code gets muted and takes the true findings with it. The
    technical spec's monorepo interaction row ("inspect the package containing
    the story's changed files") already implied this boundary.
  - Spec amendment: none — this narrows a heuristic within its stated intent.

### Lessons Learned

1. **The fixture run earned its place as an acceptance criterion, not a
   follow-up.** The synthetic tempdir fixtures were all green before the first
   yuss run, and the yuss run immediately produced a false positive
   (`pocket-js/`) that no synthetic fixture had modelled, because no synthetic
   fixture thought to nest a whole second package inside the first. The parent
   spec's *Must Include* — that validation against real application code is an
   acceptance criterion — was load-bearing rather than ceremonial.
2. **Pushing for 100% on error paths found a live defect the AC-level tests
   missed.** `coverageThreshold: {global: {lines: 0}}` in a `package.json`
   silently failed to fire `coverage_threshold_absent`, because the JS-config
   path reads a bare key (`lines: 0`) while the `package.json` path reaches the
   same regex through `json.dumps`, which quotes it (`"lines": 0`). The zero-bar
   reading is documented as "the obvious way to launder the check", so this was
   a hole in the one path most likely to be exploited deliberately.
3. **A test asserting `findings == []` was itself a vacuous-pass hazard.** The
   first draft of the empty-vs-clean test asserted both produce no findings,
   which contradicted the Error & Rescue Map's requirement of an informational
   `unsupported_stack`. The property that actually mattered — the two verdicts
   must differ — survived; the over-specified premise did not.

### Next Story

**Story 3:** `scripts/test-integrity.py` — coverage re-derivation and the
multi-line-aware module-specifier extractor, whose ground truth is exactly 4
files out of yuss's 147.
