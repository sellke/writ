# Story 2: Pin Map and Conversions

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer who rewords commands
**I want to** have every eval.sh literal pin on a command file listed with a reviewed disposition, wording-only pins removed, and structural pins checked by structure
**So that** rewording a command no longer means editing eval code, while every safety contract still fails eval when it drifts

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given `scripts/eval.sh` after Story 1 and both dependency specs, when the pin inventory recipe runs and its parsed call-line count equals `grep -c` of pin call lines, then `pin-map.md` holds exactly one row per command-file pin instance (a loop counts once per target) with check function, eval.sh line, target, kind, literal, category, disposition, and a one-line reason, and its header records the inventory commit and the before count `[AC-2.1]`
- [ ] Given every row whose category is `prime-directive`, `recommend-boundary`, `gate-class`, `loop-bound`, `script-invocation`, `verdict-provenance`, or `parsed-format`, when the map is checked, then none has disposition `remove`, and every `keep` row's literal is still present for its target in the post-change recipe output `[AC-2.2]`
- [ ] Given each `convert` row, when `scripts/eval-command-structure.py --root <tmp>` runs on a temp copy of the target command, then it passes on the unchanged file and fails naming that row when the structure is broken: a heading demoted to plain prose, a frontmatter key renamed, or a `scripts/<x>.py <subcommand>` invocation reduced to a bare mention of `<x>.py` `[AC-2.3]`
- [ ] Given the post-change `scripts/eval.sh`, when the recipe runs again, then the command-file pin count is lower than the header's before count, the drop equals the number of `convert` plus `remove` rows, no `convert` or `remove` literal remains for its target, and the header records the after count and the keep/convert/remove totals `[AC-2.4]`
- [ ] Given the removed and converted pins, when `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` run, then all pass with 0 findings; every test that mutated a removed or converted pin was changed in the same commit as the pin; and no test that guards a `keep` row was deleted `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write failing tests in a new `scripts/tests/test_eval_command_structure.py` against `scripts/eval-command-structure.py --root <tmp>`: per kind on synthetic files (a `heading` row passes on a heading line and fails when the text is only prose or inside a fenced block; a `frontmatter` row fails when the key is renamed or appears only in the body; an `invocation` row passes on `python3 scripts/x.py check` and on `` `scripts/x.py check --spec <folder>` ``, and fails on a bare `x.py` or `scripts/x.py` mention), plus a test parametrized over the helper's table that each row passes on a copy of its real target and fails on its own mutation `[AC-2.3]`
- [ ] 2.2 Re-inventory: confirm no `commands/*.lean.md` exists (stop and report if one does), save the recipe from technical-spec.md → Pin inventory recipe in a scratch path, run it, cross-check the parsed count against `grep -c`, resolve every unresolved target by hand, and write `pin-map.md`'s header and one row per instance with its category (expect about 207 rows) `[AC-2.1]`
- [ ] 2.3 Give every row a disposition and a one-line reason per technical-spec.md → Categories and disposition rules, reading the command text each pin guards; the seven safety categories take only `keep` or `convert` `[AC-2.1, AC-2.2]`
- [ ] 2.4 Implement `scripts/eval-command-structure.py` (`heading`, `frontmatter`, `invocation` kinds; `--root`; PASS/FAIL TSV; Python 3.9 standard library) and `check_command_structure` registered as `command-structure` in `CHECKS`; move each `convert` row into its table and delete that literal from `scripts/eval.sh`, one check function per commit `[AC-2.3, AC-2.4]`
- [ ] 2.5 Delete each `remove` row's pin from `scripts/eval.sh`, one check function per commit; in the same commit change any test that mutates it (`test_product_check_direction.py`, `test_review_panel.py`, any other the suite names); delete a check function and its `CHECKS` entry only when it has no pins left and runs nothing else `[AC-2.4, AC-2.5]`
- [ ] 2.6 Verify the map: re-run the recipe; confirm every `keep` literal is present, no `convert` or `remove` literal remains for its target, no safety row is `remove`, and the count fell by convert plus remove; record the after count and totals in the header `[AC-2.2, AC-2.4]`
- [ ] 2.7 Verify the suites: `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` (outside the sandbox) with 0 findings `[AC-2.5]`

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

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Inventory pins, Remove a pin, Convert a pin, Mark a safety row `remove`, Start before dependencies land]
- **Shadow paths:** []
- **Business rules:** [Pin scope, Categories, Convert means still enforced, Tests move with pins, Runtime]
- **Experience:** [State Catalog]
