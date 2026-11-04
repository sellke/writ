# Story 1: ADR-032 and the review-surface inventory

> **Status:** Completed ✅ (2026-11-04)
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer who owns the framework's review gates
**I want to** a recorded decision that a finding blocks only on executed evidence, with an inventory of every adversarial-review surface and its verdict
**So that** each later removal traces to an accepted verdict, and Stories 2 to 7 can link to ADR-032

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given `.writ/decision-records/adr-032-evidence-gated-review.md`, when it is read, then it has a header block with Date, Status Accepted, Category, Deciders (@AdamSellke), Origin, and Amends lines, then Context, Decision, Decision Drivers, Alternatives, and Consequences sections, and Consequences names at least one negative consequence. Every relative link in the file resolves to an existing file. `[AC-1.1]`
- [x] Given the inventory table in ADR-032, when it is read, then it has one row for each of the 13 named surfaces: Gate 0 architecture check, Gate 0 divergence, evaluator-agent, review-agent, reviewer filters, Safety Fact, review panel, `/review`, Jev shadow, `/security-audit`, spec analysis (create-spec Step 2.6c), visual-qa-agent, and discovery challenge prompts. `[AC-1.2]`
- [x] Given each inventory row, when its cells are read, then the row names the fact the surface tries to establish, its cost in spawns and instruction bytes, a verdict that is exactly one of keep, replace, demote, or remove, and a one-line reason. `[AC-1.3]`
- [x] Given the removal list in ADR-032, when it is checked against the `### Review panel (Story 7)` and `### Safety Fact floor (Story 6)` tables in `technical-spec.md`, then it names every file, section, and config key those tables remove or change, it lists no reviewer-filters item as removed, and `.writ/decision-records/pruned-instructions-ledger.md` has no new rows. `[AC-1.4]`
- [x] Given ADR-028 and `.writ/product/roadmap.md`, when they are read, then the ADR-028 header block has an `Amended by` line that names ADR-032 and covers the review panel, and Phase 15's Features list has one unchecked line for spec `2026-11-04-evidence-gated-review`. `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write failing tests in `scripts/tests/test_adr_032_inventory.py` (stdlib `unittest`, Python 3.9 compatible) for AC-1.1 through AC-1.5: ADR sections and links, 13 surface rows, verdict vocabulary, removal names, the ADR-028 line, and the roadmap line. Name spec `2026-11-04-evidence-gated-review` in the module docstring and cite each AC ID there. `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [x] 1.2 Write `.writ/decision-records/adr-032-evidence-gated-review.md` with the header and section layout of `adr-031-script-location.md`. Origin links `.writ/issues/improvements/2026-11-03-minimize-adversarial-review-surface.md`. Amends names ADR-028 (review panel). The decision: a finding blocks only on executed evidence. `[AC-1.1]`
- [x] 1.3 Fill the inventory table with 13 rows: fact, cost (spawns, instruction bytes), verdict, one-line reason. Take each verdict from the Scope Boundaries and Removals sections of `spec.md`, as the Amendment changes them, not from memory. `[AC-1.2, AC-1.3]`
- [x] 1.4 List each file, section, and config key from `technical-spec.md` → Removals in ADR-032: the panel removals and the floor change. List no reviewer-filters item as removed. Add no rows to `pruned-instructions-ledger.md`. `[AC-1.4]`
- [x] 1.5 Add `> **Amended by:** [ADR-032](adr-032-evidence-gated-review.md)` to the ADR-028 header block, noting it covers the review panel. Add one unchecked line for `2026-11-04-evidence-gated-review` under Phase 15's Features in `.writ/product/roadmap.md`, in the format of its neighbours. `[AC-1.5]`
- [x] 1.6 Verify AC-1.1 through AC-1.5 by reading the ADR, the ADR-028 header, and the roadmap line against each criterion. `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [x] 1.7 Run `uv run --isolated --python 3.9 --with pytest pytest scripts/tests/test_adr_032_inventory.py`, then the same with `--python 3.14`. Run `bash scripts/eval.sh` and confirm exit 0. Run each one alone, never in parallel. `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

- **ADR number.** ADR-032 is the next free number. Confirm that no `adr-032-*` file exists before writing. See `spec.md` → Corrections made at authoring, item 4.
- **Ledger.** `pruned-instructions-ledger.md` covers only `system-instructions.md` and `commands/_preamble.md`. This story adds no rows there. See Corrections, item 1.
- **Reviewer filters.** The row reads keep. Its reason cites [`trial-report.md`](../../2026-10-25-gate-upgrade-removal-measurement/trial-report.md) (commit `ef0c418`, F01) and `spec.md` → `### Amendment (2026-11-04, during /implement-spec)`.
- **Gate 0 divergence.** `spec.md` Scope Boundaries excludes it from this spec's changes, so its row reads keep. The row's reason should name both trials: the removal trial kept it (`trial-report.md`), and the design-divergence trial still decides it.
- **Effort.** The spec gives no effort size. The roadmap line uses `Effort: M` as a placeholder. Change it if the size differs.
- **Scope.** The ADR, the ADR-028 edit, the roadmap edit, and the test file change no shipped files. `gen-platform-trees.py --check` is unaffected.
- **Links.** `test_eval_shipped_refs.py` fails on links to missing files. Every relative link this story adds must resolve.
- **Python floor.** The test uses stdlib only and no 3.10+ syntax or behavior.
- **Test runs.** Do not run pytest while `eval.sh` or the bash suite runs in the same checkout. `eval.sh` runs `git init` in a temp directory, so run it outside any sandbox.
- **Downstream.** Stories 2 to 7 cite ADR-032 by path and number. Land this story first.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** []
- **Business rules:** `spec.md → ## Detailed Requirements → ### Story 1: ADR-032 and the review-surface inventory`; `spec.md → ## Business Rules (Expanded) → ### Removals`; `technical-spec.md → ## Removals`; `spec.md → ## Specification Contract → ### Corrections made at authoring (2026-11-04)`; `spec.md → ## Specification Contract → ### Amendment (2026-11-04, during /implement-spec)`
- **Experience:** []

---

## What Was Built

**Implementation Date:** 2026-11-04

### Files Created

1. **`scripts/tests/test_adr_032_inventory.py`** (471 lines)
   - 28 stdlib `unittest` tests, Python 3.9 safe. The module docstring names spec `2026-11-04-evidence-gated-review` and cites AC-1.1 through AC-1.5.
   - Classes: `AdrHeaderTest`, `AdrSectionsTest` (sections, header order, a Negative consequence, every relative link resolves), `InventoryRowsTest`, `InventoryCellsTest` (five filled cells, `Spawns:` and `Bytes:` in each cost, verdict vocabulary, verdicts match the spec), `RemovalListTest` (parses technical-spec.md's `### Safety Fact floor (Story 6)` and `### Review panel (Story 7)` tables), `FilterClaimsTest`, `LedgerTest`, `Adr028AmendedByTest`, `RoadmapLineTest`.
2. **`.writ/decision-records/adr-032-evidence-gated-review.md`** (190 lines)
   - Header block (Date, Status Accepted, Category, Deciders, Origin, Amends ADR-028 Decision 3 and the Decision 4 panel cases, Keeps the reviewer filters, Evidence base), then Decision, Context and Problem Statement, Decision Drivers, Alternatives Considered (Options A to E), Decision Outcome, Review-Surface Inventory, Removals, Consequences, Implementation Notes, References.
   - Inventory: 13 rows. keep: Gate 0 architecture check, Gate 0 divergence, reviewer filters, Jev shadow, `/security-audit`, spec analysis (create-spec Step 2.6c), `visual-qa-agent`, discovery challenge prompts. demote: `evaluator-agent`, `review-agent`, `/review`. replace: Safety Fact. remove: review panel.
   - Removals: the Safety Fact floor change (Story 6) and the review panel removals (Story 7), with one pointer to technical-spec.md § Removals for test updates and regenerated trees (DEV-002). No reviewer-filters item is listed as removed.

### Files Modified

- **`.writ/decision-records/adr-028-behavioral-verification-and-cross-family-panels.md`** (header block)
  - One `> **Amended by:** [ADR-032](adr-032-evidence-gated-review.md) (2026-11-04)` line: removes the review panel, Decision 3, and the panel cases in Decision 4. Decisions 1 and 2 stand.
- **`.writ/product/roadmap.md`** (Phase 15 → Features)
  - One unchecked line: `**Evidence-gated review** Effort: M` for `2026-11-04-evidence-gated-review`, linking ADR-032.
- **`.writ/specs/2026-11-04-evidence-gated-review/spec-lite.md`** (For Review Agents → Business Rules)
  - DEV-002 auto-amendment line.
- **`.writ/specs/2026-11-04-evidence-gated-review/drift-log.md`** (Story 1 section)
  - DEV-002 appended. DEV-001 was logged when the pipeline paused.

### Implementation Decisions

1. **Verdicts come from the amended spec** — each row's verdict follows `spec.md` Scope Boundaries, Removals, and `### Amendment (2026-11-04, during /implement-spec)`, not the pre-amendment contract. The reviewer filters row reads keep and cites `trial-report.md` (commit `ef0c418`, F01) and the Amendment.
2. **Byte counts pinned at `ef0c418`** — every inventory count was measured with `wc -c` or `sed -n` at that commit. The test checks that each cost names spawns, bytes, and the measured file; it does not recompute the counts. The review agent re-measured all 25 counts and each matched.
3. **Removals by pointer for tests and trees** — ADR-032 § Removals names every product file, section, function, flag, and config key, and covers the `Tests` and `Generated trees` rows with one pointer to technical-spec.md (DEV-002). The test skips those two rows (`NON_FILE_ROWS`).
4. **Two review recommendations applied after review** — the review panel row now names the two-fail escalation route, and the Gate 0 divergence row says design-divergence Story 6 acts on that trial's `remove`.

### Test Results

**Verification:** Automated, test-first.
**Coverage:** N/A (no source files, no coverage report)

- ✅ Red first: the first Gate 1 run failed 22 and passed 2, then went green.
- ✅ `uv run --isolated --python 3.9 --with pytest pytest scripts/tests/test_adr_032_inventory.py` → 28 passed, exit 0
- ✅ Same on `--python 3.14` → 28 passed, exit 0
- ✅ `test_eval_shipped_refs.py` on 3.9 → 17 passed
- ✅ `bash scripts/eval.sh` → exit 0 (task 1.7)
- ✅ Review-agent mutation check: 28 seeded single edits to the ADR, ADR-028, roadmap, and ledger; the test caught all 28.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s). The Gate 1 recode after DEV-001 is not a review-loop increment: the pause came before any Gate 3 verdict.
- **Drift:** Large (DEV-001, resolved by modify-spec); DEV-002 Small, auto-amended.
- **Security:** Clean
- **Boundary Compliance:** All changes are within Owned files except ADR-028's one header line, which the story itself requires.

### Gate record

**REVIEW_RESULT:** PAUSE

The orchestrator raised the pause at Gate 1, before any Gate 3 review, when the removal trial landed mid-run (DEV-001, Large). The user resolved it as modify-spec: keep the reviewer filters and amend the spec (commit `b69320b`).

**REVIEW_RESULT:** PASS

Post-amendment review by `review-agent`, saved at `.writ/state/gate3-review-story-1-adr-032-review-surface-inventory.md`.

- **Gate 0:** arch-check pass (rederived proceed). `gate0-divergence: skip (unverifiable: docs-only story, no caller usage)`
- **Gate 0.5:** boundary map computed (`.writ/state/boundary-story-1-adr-032-review-surface-inventory.json`)
- **Gate 1:** coding-agent, test-first; red at 22 failed, 2 passed, then green; recoded once after DEV-001
- **Gate 2:** no linters configured. `arch-lint: none — see .writ/docs/architecture-lint.md`. Build smoke not run (no product source changed)
- **Gate 2.5:** change surface cross-component. `gate3-route: review-agent (outside_boundary .writ/decision-records/adr-028-behavioral-verification-and-cross-family-panels.md)`. Blast radius: no consumers, no tests
- **Gate 3:** `reviewer-filters: on`. review-agent PASS. `review-override check`: fail `test_imports_no_source`, the known false positive for tests that read files rather than import a module (open issue `.writ/issues/improvements/2026-09-03-test-integrity-authenticity-flags-every-bash-test.md`); carried on the red-first run and the 28 caught mutations. Not DEGRADED. `safety-fact: traced (claimed traced) — no existing reader of ADR-028 or the roadmap matches the two added lines`. `review-panel: skipped — platform cannot spawn other vendors`. Jev shadow: pass, criteria=5 agree=5 false_pass=0 false_block=0
- **Gate 3.5:** Overall Large; DEV-001 Large (modify-spec), DEV-002 Small (auto-amended). drift-format: pass
- **Gate 4:** 28/28 on 3.9 and 3.14; test-integrity coverage unverifiable (no source files, no coverage report); authenticity `test_imports_no_source` (same known false positive)
- **Gate 4.5:** `app-verify: unverifiable (no_recipe)`
- **Gate 5:** `docs-check: unverifiable (no public exports in the changed set)`

### Deviations from Spec

- **[DEV-001] The reviewer filters stay; the spec no longer removes them** — Severity: Large
  - Spec said: Contract Must Include 1 and 6, Success Criteria, and Scope Boundaries remove the reviewer filters (skill, switch, config key, agent input rows, Gate 3 paragraph, `/review` Step 3 lines).
  - Reality: the removal trial landed mid-run. Its report (`trial-report.md`, commit `ef0c418`) recorded Reviewer Filters keep on 1 valid upgrade-only catch (F01), which contradicts the contract's removal, and Story 1's inventory had to give the filters a verdict.
  - Resolution: Pipeline paused — spec modified by user (keep the filters; commit `b69320b`)
  - Spec amendment: `spec.md` gains `### Amendment (2026-11-04, during /implement-spec)`; Story 6 becomes "Raise the Safety Fact floor to `tested`"; Story 7 writes the panel scan test; Story 5 places the evidence header beside the filters ones. Evidence gating, the panel removal, and the `tested` floor are unchanged.
- **[DEV-002] ADR-032 Removals points to technical-spec.md for test files and generated trees** — Severity: Small
  - Spec said: AC-1.4: the removal list names every file, section, and config key in technical-spec.md's Removals tables, including the `Tests` and `Generated trees` rows.
  - Reality: ADR-032 names every product file, section, function, flag, and config key, and covers the test updates and regenerated trees with one pointer to technical-spec.md § Removals.
  - Resolution: Auto-amended spec-lite.md
  - Spec amendment: spec-lite.md, For Review Agents → Business Rules, gains the DEV-002 line.

### Notes for Downstream Stories

- **Story 7** must update `RoadmapLineTest` in `scripts/tests/test_adr_032_inventory.py`, which asserts the roadmap line is unchecked.
- Inventory byte counts are pinned at `ef0c418`. The test does not recompute them, so later edits to the measured files do not fail it.
