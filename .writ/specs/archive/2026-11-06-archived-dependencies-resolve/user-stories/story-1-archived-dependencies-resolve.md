# Story 1: Archived dependencies resolve

> **Status:** Completed ✅ (2026-11-08)
> **Commit:** 61bedd05305b3c17011af3f0f4a604484904b503
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** maintainer running `/implement-phase` or `/verify-spec` after a dependency spec was archived
**I want to** `spec-deps.py validate` to treat a dependency whose folder sits under `.writ/specs/archive/` as satisfied
**So that** archiving a complete spec never blocks the phase plan or forces me to delete a correct `Dependencies:` entry

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

> **Verified by:** AC-1.4 — `bash scripts/eval.sh` runs of `--check=spec-dependencies` (17/17 scenarios, the four archive scenarios PASS), `--check=spec-lifecycle-docs` (3/3), `--check=docs-check`, and `--check=platform-trees`, each Findings: 0 on 2026-11-08

> **Verified by:** AC-1.5 — `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` on this repo after the header restore on 2026-11-08: exit 0, `status` `ok`, `archived_dependencies` `{"2026-10-25-gate-upgrade-removal-measurement": ["2026-10-25-design-divergence"]}`

- [x] Given a temp specs dir with `consumer/spec.md` declaring `> **Dependencies:** [done]` and `archive/done/spec.md`, when `spec-deps.py validate --specs-dir <dir>` runs, then it exits 0 with `status` `ok`, `order` equal to `["consumer"]`, `graph["consumer"]` equal to `["done"]`, `archived_dependencies` equal to `{"consumer": ["done"]}`, and `schema` still `spec-deps-graph-v1` `[AC-1.1]`
- [x] Given `archive/done/spec.md` whose header reads `> **Dependencies:** not a list` and `archive/loop/spec.md` declaring `[done]`, with `consumer` declaring `[done, loop]`, when `validate` runs, then it exits 0 with no `blocker` and `archived_dependencies["consumer"]` equal to `["done", "loop"]`; and given a separate fixture dir where `done` is present both as `done/spec.md` (declaring `[]`) and `archive/done/spec.md` and `consumer` declares `[done]`, when `validate` runs there, then `order` is `["done", "consumer"]` and `archived_dependencies` is `{}` `[AC-1.2]`
- [x] Given `consumer` declaring `[ghost]` and an `archive/` folder that holds `done` but not `ghost`, when `validate` runs, then it exits 1 with `blocker.code` `missing_reference` and a `summary` containing both `.writ/specs/ghost/` and `.writ/specs/archive/ghost/`; and given the existing self-reference, duplicate, cycle, and malformed fixtures with an `archive/` folder present, when `validate` runs, then each still returns its code (`self_reference`, `duplicate_reference`, `dependency_cycle`, `malformed_dependencies`) and exit 1 `[AC-1.3]`
- [x] Given the edited `scripts/eval-spec-deps.py`, `.writ/docs/spec-lifecycle.md`, `commands/verify-spec.md`, and `commands/implement-phase.md`, when `bash scripts/eval.sh --check=spec-dependencies`, `--check=spec-lifecycle-docs`, `--check=docs-check`, and `--check=platform-trees` run, then each passes, the eval TSV has four `PASS` archive scenarios, the lifecycle doc contains the paragraph `Deliberate inclusion: dependency resolution`, Check 3f reads `no such folder under .writ/specs/ or .writ/specs/archive/`, and Step 2.1 names `archived_dependencies` `[AC-1.4]`
- [x] Given line 6 of `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/spec.md` restored to `> **Dependencies:** [2026-10-25-design-divergence, 2026-10-25-review-route-rigor, 2026-10-25-repro-first-bug-fixing]`, when `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` runs in this repo, then it exits 0 with `status` `ok` and `archived_dependencies["2026-10-25-gate-upgrade-removal-measurement"]` equal to `["2026-10-25-design-divergence"]` `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write `scripts/tests/test_spec_deps.py`, with a module docstring naming `2026-11-06-archived-dependencies-resolve` Story 1 above every AC tag. Load `spec-deps.py` by path as `test_story_deps.py` does. Add `make_spec(root, spec_id, header, archived=False)` and `run_validate(root)` (subprocess, returns exit and parsed JSON). Write the six tests in technical-spec § Tests, each asserting the exact keys, codes, and exits. Run on Python 3.9 and confirm the archive tests fail `[AC-1.1, AC-1.2, AC-1.3]`
- [x] 1.2 In `scripts/eval-spec-deps.py`, give `make_spec` an `archived: bool = False` parameter that writes under `root / "archive"`, add `scenario_archive()` with the four `emit` lines named in technical-spec § eval-spec-deps.py, and call it from `main()`. Run `python3 scripts/eval-spec-deps.py` and confirm the four scenarios print `FAIL` `[AC-1.4]`
- [x] 1.3 In `scripts/spec-deps.py`, add `_archived_ids(specs_dir)` and rewrite `validate_graph` per technical-spec § Change: resolve each declared dep as active edge, archived, or `missing_reference` (in that order), pass only the active graph to `_find_cycle` and `_topo_order`, keep `graph` as the declared lists, add `archived_dependencies` to the result, and extend the `missing_reference` summary to name both paths. Add the docstring sentence. Leave `_discover`, `parse_header`, `parse_spec`, and `GRAPH_SCHEMA` untouched `[AC-1.1, AC-1.2, AC-1.3]`
- [x] 1.4 In `.writ/docs/spec-lifecycle.md`, add the **Deliberate inclusion: dependency resolution** paragraph after the `⚠️ Do not add a second, separate exclusion check` block and the `spec-deps.py validate` row to the call-site table, per technical-spec § Docs. Add no `##` heading `[AC-1.4]`
- [x] 1.5 Edit `commands/verify-spec.md` Check 3f's missing-reference line and add the one-sentence archived-dependency note after the executable-reference sentence in `commands/implement-phase.md` Step 2.1, per technical-spec § Docs. Keep the three `require_literal` strings `check_spec_dependencies` pins in `implement-phase.md` intact `[AC-1.4]`
- [x] 1.6 Restore line 6 of `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/spec.md` to the three-id header and run `python3 scripts/spec-deps.py validate --specs-dir .writ/specs`; confirm `ok` and the `archived_dependencies` entry `[AC-1.5]`
- [x] 1.7 Verify. Run `python3 scripts/gen-platform-trees.py` then `--check`. Run `uv run --isolated --python 3.9 --with pytest pytest scripts/tests/test_spec_deps.py` and the same on 3.14, alone. Run `bash scripts/eval.sh --check=spec-dependencies`, `--check=spec-lifecycle-docs`, `--check=docs-check`, and `--check=platform-trees` with `--report=<scratch path>`. Check each AC against the test or command that carries its tag `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

- **Order of resolution.** Test `known` before `archived` so an id in both places keeps its ordering edge (Business Rule 3).
- **Topological sort.** `_topo_order` releases a spec only when its dep set is empty. Archived ids must not be in that set, or the consumer is never released and the sort reports a false `dependency_cycle`.
- **Archived headers.** Never call `parse_header` on an archived file. The second fixture in AC-1.2 exists to prove it.
- **No new script.** `spec-deps.py` already has an agent-cli-contract row; no contract edit, no smoke change. Its plugin copy is regenerated by `gen-platform-trees.py`.
- **eval.sh writes.** The default `eval.sh` run writes `.writ/state/eval-*.md`; use `--report=<scratch path>` and never run it while pytest runs (`CLAUDE.md`).
- **Python 3.9.** No `match`, no `pathlib` behavior newer than 3.9; `from __future__ import annotations` is already in the module.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [`_archived_ids` (absent, unreadable), resolution (neither place, duplicate), ordering (archived cycle)] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Happy path, Nil input, Empty input, Upstream error] — technical-spec.md → ## Shadow Paths
- **Business rules:** [1 location alone satisfies, 2 archived never parsed, 3 active wins, 4 additive output, 5 blockers unchanged] — spec.md → ## Specification Contract → 📋 Business Rules; spec.md → ## Business Rules (Expanded)
- **Experience:** [State catalog, Error experience] — spec.md → ## Experience Design → ### State catalog; spec.md → ## Specification Contract → 🎯 Experience Design
- **Reference shape:** spec.md → ## Detailed Requirements → ### `validate_graph` (reference shape); technical-spec.md → ## Change

## What Was Built

**Implementation Date:** 2026-11-08

### Files Created
1. **`scripts/tests/test_spec_deps.py`**
   - Loads `spec-deps.py` by path; `make_spec(root, spec_id, header, archived=False)` and `run_validate(root)`; six tests (ten cases with parametrization) covering AC-1.1 to AC-1.3, an absent and an empty `archive/`, and the four existing blockers with an archive present.

### Files Modified
- **`scripts/spec-deps.py`** (and its generated copy `plugins/writ/scripts/spec-deps.py`)
  - `_archived_ids(specs_dir)` reads folder names under `archive/*/spec.md` only.
  - `validate_graph` resolves each declared dependency as an active edge, an archived id, or `missing_reference`, in that order; `_find_cycle` and `_topo_order` see only the active graph; `graph` keeps the declared lists; the result gains `archived_dependencies`; the `missing_reference` summary names both paths. Docstring sentence added.
- **`scripts/eval-spec-deps.py`** — `make_spec(..., archived=False)` and `scenario_archive()` with four scenarios (17 total).
- **`.writ/docs/spec-lifecycle.md`** — call-site table row and the **Deliberate inclusion: dependency resolution** paragraph.
- **`commands/verify-spec.md`** Check 4d — missing-reference line names `.writ/specs/archive/`; one clause trimmed to offset (DEV-001, DEV-002).
- **`commands/implement-phase.md`** Step 2.1 — archived-dependency sentence; blocker sentence shortened to offset (DEV-002).
- **`scripts/tests/test_governor_enforcement.py`** — `KNOWN_OVER_BUDGET` re-pinned down: `verify-spec.md` 10818 -> 10791, `implement-phase.md` 1465 -> 1464.
- **`.writ/specs/2026-10-25-gate-upgrade-removal-measurement/spec.md`** — `Dependencies:` restored to include `2026-10-25-design-divergence`.
- **Generated copies** — `plugins/writ/commands/{verify-spec,implement-phase}.md`, `cursor/plugin/commands/{verify-spec,implement-phase}.md`.

### Implementation Decisions
1. **Coding subagent ran Gate 1.** A `general-purpose` agent followed `agents/coding-agent.md`; the archive tests and four eval scenarios failed before `spec-deps.py` changed.
2. **One recode.** The orchestrator's recorded run failed three byte-ledger tests (+138 and +24 bytes on two over-budget commands); the recode offset both files below their old overage.
3. **Gate 3 ran `review-agent`** (route: generated copies outside the boundary map), with Safety Fact on.

### Test Results
**Verification:** orchestrator's recorded run, `uv run --isolated --python 3.9 --with pytest pytest -q` on the 17 test files that read a changed file: 869 passed; `python3 scripts/eval-spec-deps.py`: 17 PASS. Coding agent: `test_spec_deps.py` + `test_story_deps.py` 48 passed on 3.9 and 3.14; `eval.sh` spec-dependencies, spec-lifecycle-docs, docs-check, platform-trees, size-pins, leanness: Findings 0; `gen-platform-trees.py --check`: pass.
**Coverage:** `test-integrity.py coverage` unverifiable (`coverage_report_absent`); the only new file is a test file.
- ✅ AC-1.1 to AC-1.3 by tagged tests; AC-1.4 and AC-1.5 by recorded runs (Verified by lines).

### Review Outcome
**Result:** PASS
- **Iteration count:** 2 (one Gate 1 recode before review)
- **Drift:** Small (DEV-001, DEV-002)
- **Security:** Clean
- **Boundary Compliance:** generated copies and the byte-ledger re-pin outside the map, both justified.
- `story-gate: pass (phase post-review, 9 checks, 0 fail, 1 unverifiable)` · `safety-fact: tested (claimed tested)` · `evidence-gate: not run (PASS)` · `reviewer-filters: on` · `gate3-route: review-agent (outside_boundary: five generated copies)` · `arch-lint: none — see .writ/docs/architecture-lint.md`

### Deviations from Spec
- **[DEV-001] `/verify-spec` section named "Check 3f" in the spec is Check 4d** — Severity: Small
  - Resolution: Auto-amended spec-lite.md
- **[DEV-002] Byte-budget offsets: two prose trims and a ledger re-pin** — Severity: Small
  - Resolution: Auto-amended spec-lite.md
