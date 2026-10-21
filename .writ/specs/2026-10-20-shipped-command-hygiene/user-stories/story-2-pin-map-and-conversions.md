# Story 2: Pin Map and Conversions

> **Status:** Completed ✅
> **Commit:** 882dac43713950d9e388789042f10d0a98dc65a7
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer who rewords commands
**I want to** have every eval.sh literal pin on a command file listed with a reviewed disposition, wording-only pins removed, and structural pins checked by structure
**So that** rewording a command no longer means editing eval code, while every safety contract still fails eval when it drifts

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given `scripts/eval.sh` after Story 1 and both dependency specs, when the pin inventory recipe runs and its parsed call-line count equals `grep -c` of pin call lines, then `pin-map.md` holds exactly one row per command-file pin instance (a loop counts once per target) with check function, eval.sh line, target, kind, literal, category, disposition, and a one-line reason, and its header records the inventory commit and the before count `[AC-2.1]`
- [x] Given every row whose category is `prime-directive`, `recommend-boundary`, `gate-class`, `loop-bound`, `script-invocation`, `verdict-provenance`, or `parsed-format`, when the map is checked, then none has disposition `remove`, and every `keep` row's literal is still present for its target in the post-change recipe output `[AC-2.2]`
- [x] Given each `convert` row, when `scripts/eval-command-structure.py --root <tmp>` runs on a temp copy of the target command, then it passes on the unchanged file and fails naming that row when the structure is broken: a heading demoted to plain prose, a frontmatter key renamed, or a `scripts/<x>.py <subcommand>` invocation reduced to a bare mention of `<x>.py` `[AC-2.3]`
- [x] Given the post-change `scripts/eval.sh`, when the recipe runs again, then the command-file pin count is lower than the header's before count, the drop equals the number of `convert` plus `remove` rows, no `convert` or `remove` literal remains for its target, and the header records the after count and the keep/convert/remove totals `[AC-2.4]`
- [x] Given the removed and converted pins, when `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` run, then all pass with 0 findings; every test that mutated a removed or converted pin was changed in the same commit as the pin; and no test that guards a `keep` row was deleted `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Write failing tests in a new `scripts/tests/test_eval_command_structure.py` against `scripts/eval-command-structure.py --root <tmp>`: per kind on synthetic files (a `heading` row passes on a heading line and fails when the text is only prose or inside a fenced block; a `frontmatter` row fails when the key is renamed or appears only in the body; an `invocation` row passes on `python3 scripts/x.py check` and on `` `scripts/x.py check --spec <folder>` ``, and fails on a bare `x.py` or `scripts/x.py` mention), plus a test parametrized over the helper's table that each row passes on a copy of its real target and fails on its own mutation `[AC-2.3]`
- [x] 2.2 Re-inventory: confirm no `commands/*.lean.md` exists (stop and report if one does), save the recipe from technical-spec.md → Pin inventory recipe in a scratch path, run it, cross-check the parsed count against `grep -c`, resolve every unresolved target by hand, and write `pin-map.md`'s header and one row per instance with its category (expect about 207 rows) `[AC-2.1]`
- [x] 2.3 Give every row a disposition and a one-line reason per technical-spec.md → Categories and disposition rules, reading the command text each pin guards; the seven safety categories take only `keep` or `convert` `[AC-2.1, AC-2.2]`
- [x] 2.4 Implement `scripts/eval-command-structure.py` (`heading`, `frontmatter`, `invocation` kinds; `--root`; PASS/FAIL TSV; Python 3.9 standard library) and `check_command_structure` registered as `command-structure` in `CHECKS`; move each `convert` row into its table and delete that literal from `scripts/eval.sh`, one check function per commit `[AC-2.3, AC-2.4]`
- [x] 2.5 Delete each `remove` row's pin from `scripts/eval.sh`, one check function per commit; in the same commit change any test that mutates it (`test_product_check_direction.py`, `test_review_panel.py`, any other the suite names); delete a check function and its `CHECKS` entry only when it has no pins left and runs nothing else `[AC-2.4, AC-2.5]`
- [x] 2.6 Verify the map: re-run the recipe; confirm every `keep` literal is present, no `convert` or `remove` literal remains for its target, no safety row is `remove`, and the count fell by convert plus remove; record the after count and totals in the header `[AC-2.2, AC-2.4]`
- [x] 2.7 Verify the suites: `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` (outside the sandbox) with 0 findings `[AC-2.5]`

## Notes

- **The hardest constraint lives here.** The pins exist because prose drifted before. When a row is unclear, keep it. A wrong `keep` costs one eval edit later; a wrong `remove` drops a contract silently.
- **Weak safety pins stay.** Some safety pins are single words (`transient`, `read-only`) that pass on any occurrence. Keep them; strengthening them is not this story.
- **What convert gains.** A heading row fails when the heading becomes prose; an invocation row fails when the script call becomes a mention. A literal substring pin passes in both cases. A whole sentence or table row is not a heading; it stays literal or is removed.
- **Ownership.** Each structural row records the check function it came from (`was`). The pin map's reason for a convert row names the structural row.
- **Tests that assert command text directly** (`test_jev_setup_hooks.sh`, `test_spec_analyze_command_hooks.sh`, parts of `test_product_check_direction.py`) are not eval.sh pins. Leave them unless a removed pin's mutation case lives in them.
- **Story 1 overlap.** Story 1 added `check_shipped_refs` to the same file. Rebase line numbers on the current tree; never on this spec's snapshot.
- **Technical spec:** `sub-specs/technical-spec.md` → Current State → Literal pins on command files (per-function guidance), and → Story 2: Pin Map and Conversions (recipe, pin map format, categories, structural checks).
- **Dependency check.** `2026-10-20-harness-cuts` deletes the lean-file pins and the ADR-025 no-op pins. If either group is still present, the dependency has not landed.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Inventory pins, Remove a pin, Convert a pin, Mark a safety row `remove`, Start before dependencies land]
- **Shadow paths:** []
- **Business rules:** [Pin scope, Categories, Convert means still enforced, Tests move with pins, Runtime]
- **Experience:** [State Catalog]

---

## What Was Built

**Implementation Date:** 2026-10-21

### Files Created

1. **`.writ/specs/2026-10-20-shipped-command-hygiene/pin-map.md`** (224 lines)
   - One row per command-file literal pin in `scripts/eval.sh` at inventory commit `04799a9`: 207 rows with check function, line, target, kind, literal, category, disposition, reason. Header: before 207 instances at 199 call sites, after 144 at 144; keep 144 · convert 29 · remove 34.
2. **`scripts/eval-command-structure.py`** (305 lines)
   - Table-driven structural checker: `heading` (outside fenced code, text begins with the value), `frontmatter` (top-level key in the YAML block), `invocation` (script path plus a required subcommand; a bare mention never passes). 30 rows, each with `file`, `kind`, `value`, `was`, `message`. `--root`, one self-test per kind, PASS/FAIL TSV, exit 2 with no `commands/`. Python 3.9 standard library, dev-only.
3. **`scripts/tests/test_eval_command_structure.py`** (509 lines)
   - 34 tests: per-kind positives and negatives (fences, renamed and nested keys, bare mentions, prose after a path), self-test sabotage, each table row passing on its real target and failing on its own mutation, the phase-state regression with the frontmatter note kept, eval wiring (pass, bite, missing helper, no-verdict helper), pin-map consistency, and the check registry.

### Files Modified

- **`scripts/eval.sh`** (30 check functions; `CHECKS`)
  - `check_command_structure` added and registered as `command-structure` after `shipped-refs`.
  - 63 command-file literals deleted (29 converted, 34 removed), one check function per commit. `check_product_check_direction` and its `CHECKS` entry deleted (all nine pins removed; it ran nothing else).
- **`scripts/tests/test_review_panel.py`** — `test_report_entry_pin_bites` deleted with pin-map row 198.
- **`scripts/tests/test_product_check_direction.py`** — eval-copy helper dropped; the mutation cases assert the command text directly.
- **`scripts/tests/test_harness_cuts.py`** — `EVAL_CHECKS` no longer lists the deleted function.
- **`scripts/tests/test_eval_shipped_refs.py`** — one docstring line (eval-copy example).

### Implementation Decisions

1. **Structural rows landed before the literals left** — the helper commit holds every row, so each converted contract was enforced at every commit.
2. **Invocation rows keep the pin's subcommand and flags** — no row is weaker than the literal it replaced; several are stricter (`is-complete`, `sweep`, a `scripts/` prefix).
3. **Kept against the guidance when unsure** — rows 47–49 (release test-gate table) and 182 (verify-spec's eight-row exit criterion) stay `keep`.
4. **Four `structure` pins removed as duplicates** — an `eval-*.py` scenario run by the same check asserts the same text on the same file (DEV-004).
5. **Path-only invocation support removed** — the bare `scripts/phase-state.py` pin became `create-lane` and `validate-result` rows after Gate 3 iteration 1 (DEV-006).

### Test Results

**Verification:** Automated, test-first (helper tests red before the helper existed; the phase-state regression red on the old row).
**Coverage:** 100% (110 statements) on `scripts/eval-command-structure.py`, measured by the orchestrator with `coverage run` and `patch = subprocess` over `test_eval_command_structure.py`.

- ✅ Orchestrator targeted run: `test_eval_command_structure.py`, `test_product_check_direction.py`, `test_review_panel.py`, `test_harness_cuts.py`, `test_eval_shipped_refs.py` → 244 passed (iteration 1); `test_eval_command_structure.py` → 34 passed (after recode).
- ✅ Full pytest (3.9): 2765 passed, 2 skipped (reviewer run on HEAD).
- ✅ Bash tests: 45/45.
- ✅ `bash scripts/eval.sh`: Findings 0, run errors 0; `command-structure` 33/33.
- ✅ Recipe re-run: 572 → 518 pin call lines, each equal to `grep -c`; 207 → 144 command-file instances; every keep literal still pinned; no convert or remove literal left on its target.
- ✅ Reviewer mutations: 13 structural rows each fail on their own mutation; both phase-state rows fail when only the real calls are reduced.
- ✅ `ac-trace.py check` on this spec: no findings.

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s)
- **Drift:** Small (DEV-004, DEV-005, DEV-006)
- **Security:** Clean
- **Boundary Compliance:** every crossing is a file named in technical-spec.md → Files in Scope for Story 2 or a test that mutated a removed pin.
- gate3-route: review-agent (outside_boundary .writ/context.md .writ/specs/2026-10-20-shipped-command-hygiene/pin-map.md scripts/eval-command-structure.py scripts/eval.sh scripts/tests/test_eval_command_structure.py scripts/tests/test_eval_shipped_refs.py scripts/tests/test_harness_cuts.py scripts/tests/test_product_check_direction.py scripts/tests/test_review_panel.py). review-panel: skipped — platform cannot spawn other vendors. arch-lint: none — see .writ/docs/architecture-lint.md.
- Iteration 1 FAIL (Critical, AC-2.3): the path-only `scripts/phase-state.py` row passed on the `calibrated_against` note in `implement-phase.md`'s frontmatter. Fixed in `26907ee`.
- Gate 0 arch-check: pass (rederived proceed). Gate 2: no linter configured; build-smoke unverifiable (unsupported_stack). Gate 3 review-override: unverifiable (no coverage report). Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable by the script; measured 100% by hand. Gate 4 authenticity: pass. Gate 4.5: app-verify unverifiable (no recipe). Gate 5: docs-check unverifiable (no public exports).
- Reviewer audit: no remove row is in a safety category; rows 18–19, 21–22, 33–35, 116, 130, 132, 135–136, 192, and 199–207 scrutinized one by one and agreed. Recommendation for a later pass: verify-spec's 4a–4c report-only / 4d blocking boundary and implement-phase's `scripts/spec-deps.py validate` call were never pinned.

### Deviations from Spec

- **[DEV-004] Structure pins removed as duplicates of `eval-*.py` scenarios** — Severity: Small
  - Spec said: remove means wording only; `## Artifact Map` stays literal.
  - Reality: rows 130, 132, 135, 136 removed because the same check's helper scenario asserts the same text.
  - Resolution: Auto-amended
  - Spec amendment: spec-lite.md business rule added.
- **[DEV-005] `merge, never append` removed beyond the per-function guidance** — Severity: Small
  - Spec said: only the retro nudge is a remove candidate in `check_knowledge_consolidate`.
  - Reality: row 116 removed as wording; the script and README pins and the approval and no-commit pins stay.
  - Resolution: Auto-amended
- **[DEV-006] One pin instance maps to two structural rows** — Severity: Small
  - Spec said: a converted pin becomes a structural row.
  - Reality: row 74 became `create-lane` and `validate-result` rows; path-only invocation support removed.
  - Resolution: Auto-amended
  - Spec amendment: spec-lite.md For Coding Agents updated.
