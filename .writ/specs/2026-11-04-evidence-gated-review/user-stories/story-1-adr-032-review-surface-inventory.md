# Story 1: ADR-032 and the review-surface inventory

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer who owns the framework's review gates
**I want to** a recorded decision that a finding blocks only on executed evidence, with an inventory of every adversarial-review surface and its verdict
**So that** each later removal traces to an accepted verdict, and Stories 2 to 7 can link to ADR-032

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given `.writ/decision-records/adr-032-evidence-gated-review.md`, when it is read, then it has a header block with Date, Status Accepted, Category, Deciders (@AdamSellke), Origin, and Amends lines, then Context, Decision, Decision Drivers, Alternatives, and Consequences sections, and Consequences names at least one negative consequence. Every relative link in the file resolves to an existing file. `[AC-1.1]`
- [ ] Given the inventory table in ADR-032, when it is read, then it has one row for each of the 13 named surfaces: Gate 0 architecture check, Gate 0 divergence, evaluator-agent, review-agent, reviewer filters, Safety Fact, review panel, `/review`, Jev shadow, `/security-audit`, spec analysis (create-spec Step 2.6c), visual-qa-agent, and discovery challenge prompts. `[AC-1.2]`
- [ ] Given each inventory row, when its cells are read, then the row names the fact the surface tries to establish, its cost in spawns and instruction bytes, a verdict that is exactly one of keep, replace, demote, or remove, and a one-line reason. `[AC-1.3]`
- [ ] Given the removal list in ADR-032, when it is checked against the Reviewer Filters and Review panel removal tables in `technical-spec.md`, then it names every removed file, section, and config key, and `.writ/decision-records/pruned-instructions-ledger.md` has no new rows. `[AC-1.4]`
- [ ] Given ADR-028 and `.writ/product/roadmap.md`, when they are read, then the ADR-028 header block has an `Amended by` line that names ADR-032 and covers the review panel, and Phase 15's Features list has one unchecked line for spec `2026-11-04-evidence-gated-review`. `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write failing tests in `scripts/tests/test_adr_032_inventory.py` (stdlib `unittest`, Python 3.9 compatible) for AC-1.1 through AC-1.5: ADR sections and links, 13 surface rows, verdict vocabulary, removal names, the ADR-028 line, and the roadmap line. Name spec `2026-11-04-evidence-gated-review` in the module docstring and cite each AC ID there. `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [ ] 1.2 Write `.writ/decision-records/adr-032-evidence-gated-review.md` with the header and section layout of `adr-031-script-location.md`. Origin links `.writ/issues/improvements/2026-11-03-minimize-adversarial-review-surface.md`. Amends names ADR-028 (review panel). The decision: a finding blocks only on executed evidence. `[AC-1.1]`
- [ ] 1.3 Fill the inventory table with 13 rows: fact, cost (spawns, instruction bytes), verdict, one-line reason. Take each verdict from the Scope Boundaries and Removals sections of `spec.md`, not from memory. `[AC-1.2, AC-1.3]`
- [ ] 1.4 List each removed file, section, and config key from `technical-spec.md` → Removals in ADR-032. Add no rows to `pruned-instructions-ledger.md`. `[AC-1.4]`
- [ ] 1.5 Add `> **Amended by:** [ADR-032](adr-032-evidence-gated-review.md)` to the ADR-028 header block, noting it covers the review panel. Add one unchecked line for `2026-11-04-evidence-gated-review` under Phase 15's Features in `.writ/product/roadmap.md`, in the format of its neighbours. `[AC-1.5]`
- [ ] 1.6 Verify AC-1.1 through AC-1.5 by reading the ADR, the ADR-028 header, and the roadmap line against each criterion. `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [ ] 1.7 Run `uv run --isolated --python 3.9 --with pytest pytest scripts/tests/test_adr_032_inventory.py`, then the same with `--python 3.14`. Run `bash scripts/eval.sh` and confirm exit 0. Run each one alone, never in parallel. `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

- **ADR number.** ADR-032 is the next free number. Confirm that no `adr-032-*` file exists before writing. See `spec.md` → Corrections made at authoring, item 4.
- **Ledger.** `pruned-instructions-ledger.md` covers only `system-instructions.md` and `commands/_preamble.md`. This story adds no rows there. See Corrections, item 1.
- **Gate 0 divergence.** `spec.md` Scope Boundaries excludes it from this spec's changes, so its row reads keep. The row's reason should name the design-divergence trial, which still decides it (`spec.md` header, Amends paragraph).
- **Effort.** The spec gives no effort size. The roadmap line uses `Effort: M` as a placeholder. Change it if the size differs.
- **Scope.** The ADR, the ADR-028 edit, the roadmap edit, and the test file change no shipped files. `gen-platform-trees.py --check` is unaffected.
- **Links.** `test_eval_shipped_refs.py` fails on links to missing files. Every relative link this story adds must resolve.
- **Python floor.** The test uses stdlib only and no 3.10+ syntax or behavior.
- **Test runs.** Do not run pytest while `eval.sh` or the bash suite runs in the same checkout. `eval.sh` runs `git init` in a temp directory, so run it outside any sandbox.
- **Downstream.** Stories 2 to 7 cite ADR-032 by path and number. Land this story first.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** []
- **Business rules:** `spec.md → ## Detailed Requirements → ### Story 1: ADR-032 and the review-surface inventory`; `spec.md → ## Business Rules (Expanded) → ### Removals`; `technical-spec.md → ## Removals`; `spec.md → ## Specification Contract → ### Corrections made at authoring (2026-11-04)`
- **Experience:** []
