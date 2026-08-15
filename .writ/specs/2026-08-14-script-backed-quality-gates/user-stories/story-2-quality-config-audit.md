# Story 2: The Quality-Config Audit

> **Status:** Not Started
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

- [ ] Given a Next.js project whose `next.config.js` sets `typescript.ignoreBuildErrors` or `eslint.ignoreDuringBuilds` to `true`, when `quality-config-audit.py check` runs, then it reports `build_gate_disabled` as blocking, names the file and line, and exits 1. `[AC-2.1]`
- [ ] Given a Jest project with `collectCoverageFrom` configured and no `coverageThreshold` key — or a `coverageThreshold` whose value is zero — when the check runs, then it reports `coverage_threshold_absent` as blocking, because a zero bar and an absent bar are the same bar. `[AC-2.2]`
- [ ] Given a config file that is executable JavaScript or JSONC and cannot be parsed to a bounded answer, when the check runs, then it reports `could_not_parse`, downgrades every finding that file would have decided to `unverifiable`, names the file in `inspected.unparsed`, and never reports the absence of a pattern as evidence the gate is enabled. `[AC-2.3]`
- [ ] Given a project with two package-manager lockfiles, a `lint` script excluding the test tree, or coverage collection excluding a directory containing shipped source, when the check runs, then it reports `duplicate_lockfile`, `tests_excluded_from_typecheck` and `coverage_scope_gap` respectively as informational findings that do not affect the exit code. `[AC-2.4]`
- [ ] Given a real `yuss.app` checkout, when the check runs against it, then it reports `build_gate_disabled` for both `next.config.js:8` and `next.config.js:11`, `coverage_threshold_absent` for `jest.config.js`, `duplicate_lockfile` for `bun.lock` + `pnpm-lock.yaml`, and `coverage_scope_gap` for `app/` — and that output is recorded verbatim in this story's What Was Built record. `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write `scripts/tests/test_quality_config_audit.py` first — `unittest`, module imported by path via `importlib.util`, one test per finding code, plus parse-failure downgrade, the zero-threshold case, determinism, and all three exit codes `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [ ] 2.2 Implement config discovery and the `inspected` envelope — which files were found, which parsed, by what method, which not — before any finding logic, so a vacuous pass is structurally impossible `[AC-2.3]`
- [ ] 2.3 Implement the JSONC-tolerant reader (comment and trailing-comma stripping) and the bounded regex heuristics for executable-JS configs, each emitting `could_not_parse` when it cannot bound its answer `[AC-2.3]`
- [ ] 2.4 Implement the six config-audit finding codes with the severities Story 1's doc records `[AC-2.1, AC-2.2, AC-2.4]`
- [ ] 2.5 Implement baseline suppression — findings present in `.writ/quality-baseline.md` are reported as acknowledged rather than blocking; a malformed baseline exits 2 rather than being ignored `[AC-2.4]`
- [ ] 2.6 Write `scripts/eval-quality-config-audit.py` fixture scenarios following `scripts/eval-ac-trace.py`, and register `quality-config-audit` in `scripts/eval.sh`'s `CHECKS` array with a `check_quality_config_audit()` binding every finding code against both the checker and Story 1's doc, plus `forbid_literal` read-only guards `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [ ] 2.7 Run against a real yuss checkout, record the output verbatim in What Was Built, and verify tests pass with ≥80% coverage on new code and 100% on error paths `[AC-2.5]`

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

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

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
