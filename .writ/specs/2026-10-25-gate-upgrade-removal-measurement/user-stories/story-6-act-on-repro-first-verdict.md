# Story 6: Act on the Repro First Verdict

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 5

## User Story

**As a** Writ maintainer
**I want to** label the substitute Repro First run, commit its report with the trial file, and keep or remove Repro First as that verdict decides
**So that** the last Phase 15 upgrade is decided on a committed record, and the repo, roadmap, ADR-030, and spec status agree with it

## Acceptance Criteria

> **AC IDs assigned through:** AC-6.5

- [ ] Given `labeling-sheet-repro-first.md` lists upgrade-only findings, when the assistant labels them in a fresh pass without opening the trial JSON or raw outputs, then every note opens "Assistant-assessed, maintainer-delegated", `label --labeled-by "Adam Sellke (delegated to assistant)"` succeeds, `report`'s output is committed verbatim as `trial-report-repro-first.md` with the labeled substitute trial file before any removal edit, and `trial-report.md` stays byte-identical; with zero upgrade-only findings, `label` still runs on the field-less sheet so `labeled_by` is set, and the drift log records that no finding needed a label `[AC-6.1]`
- [ ] Given Repro First's verdict is `remove`, when the story closes, then its Removal Inventory (Notes) is applied as built, both whole-file caps are re-pinned downward with a dated disclosure naming this spec and Story 6, `python3 scripts/gen-platform-trees.py` has run, `scripts/repro-order.py` is absent, and `rg -n 'Repro First' commands agents skills .writ/docs` is empty; given `keep` or `unverifiable`, then no Repro First file is edited and the spec stays open with the reason `[AC-6.2]`
- [ ] Given the outcome test `scripts/tests/test_gate_upgrade_trial_outcome.py`, when it runs, then Repro First's verdict is read from `trial-report-repro-first.md` when that file exists, the other three verdicts are read from `trial-report.md`, and the test never imports the harness `[AC-6.3]`
- [ ] Given Repro First's verdict, when the records are written, then the roadmap Phase 15 "Removal measurement" line and the "Phase 15 and 17 loose ends" item are updated, ADR-030 § Review gains a note with the date, the four substitute story IDs, each verdict and count, the selection rule, the removal-bias caveat, and the delegated-label caveat, and `spec.md` reads `> **Status:** Complete` when every verdict is `keep`, `remove`, or `absent`, else `> **Status:** In Progress — <reason from report>` `[AC-6.4]`
- [ ] Given the report commit exists and Repro First's verdict is `keep` or `remove`, when the story closes, then `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py`, `scripts/tests/test_gate_upgrade_trial.py`, and `scripts/tests/fixtures/gate-upgrade-trial/` are deleted, `uv run pytest scripts/tests/test_gate_upgrade_trial_outcome.py` passes, `commands/why.md`, `commands/writ.md`, `commands/retro.md`, and `commands/refresh-command.md` are unchanged, and both pytest runs, the bash tests, `python3 scripts/gen-platform-trees.py --check`, and `bash scripts/eval.sh` pass with 0 findings `[AC-6.5]`

## Implementation Tasks

- [ ] 6.1 Write tests in `scripts/tests/test_gate_upgrade_trial_outcome.py` that Repro First reads `trial-report-repro-first.md` when it exists, the other three read `trial-report.md`, and the file never imports the harness `[AC-6.3]`
- [ ] 6.2 Label the upgrade-only findings in `labeling-sheet-repro-first.md` from the excerpt files only, as the delegated assistant. Add a delegation entry to `drift-log.md`. Run `label`, then `report` on the substitute trial file. Commit `trial-report-repro-first.md` verbatim with that file `[AC-6.1]`
- [ ] 6.3 If the verdict is `remove`, delete Repro First's wiring as built (Notes) from `skills/tdd-cycle/SKILL.md`, `agents/coding-agent.md`, `commands/prototype.md`, `commands/implement-story.md`, and `skills/subagent-worktree-integration/SKILL.md`. Otherwise edit nothing `[AC-6.2]`
- [ ] 6.4 If removed, delete `scripts/repro-order.py`, `scripts/tests/test_repro_order.py`, and `scripts/tests/test_repro_first_wiring.py`. Edit `.writ/docs/config-format.md`, `.writ/docs/agent-cli-contract.md`, and `scripts/tests/test_agent_cli_contract.py`. Re-pin both caps. Run `python3 scripts/gen-platform-trees.py` `[AC-6.2]`
- [ ] 6.5 Edit `.writ/product/roadmap.md` (Phase 15 "Removal measurement" line and "Phase 15 and 17 loose ends" item). Add the § Review note to `.writ/decision-records/adr-030-contract-verifier-boundary-front-door.md`. Set the `spec.md` status line `[AC-6.4]`
- [ ] 6.6 If the verdict is `keep` or `remove`, and the report commit exists, delete `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py`, `scripts/tests/test_gate_upgrade_trial.py`, and `scripts/tests/fixtures/gate-upgrade-trial/` `[AC-6.5]`
- [ ] 6.7 Verify: run `uv run --isolated --python 3.9 --with pytest pytest` and the `--python 3.14` form, each alone; the bash tests; `python3 scripts/gen-platform-trees.py --check`; `bash scripts/eval.sh` with 0 findings. If removed, confirm `scripts/repro-order.py` is absent and the `rg` check is empty `[AC-6.2, AC-6.3, AC-6.5]`

## Notes

- **Delegated labels (exception to Business Rule 9).** On 2026-11-09 the maintainer delegated the substitute run's labels and acknowledgments to the assistant. Business Rule 9 otherwise stands. The note prefix and `--labeled-by` value above are fixed by that delegation. Record it in `drift-log.md` as DEV-012 did. The delegation covers this run only.
- **Zero-finding case.** With no upgrade-only findings there is nothing to label. Technical-spec § Verdict step 4 reads `labeled_by` null as `unverifiable` for an exercised upgrade, and `label` accepts a sheet with no fields. So run `label --labeled-by "Adam Sellke (delegated to assistant)"` on the field-less sheet anyway; `report` then gives `remove`.
- **Substitute inputs.** Assumes Story 5 wrote `labeling-sheet-repro-first.md` and the substitute trial file under `.writ/eval/gate-upgrade-trial/`, and stopped at `rating-handoff-repro-first.md`. Confirm the paths from that handoff before task 6.2.
- **Removal Inventory as built.** Source: repro-first spec.md § Removal Inventory, as amended by `.writ/specs/archive/2026-10-25-repro-first-bug-fixing/drift-log.md` (DEV-007, DEV-010, DEV-012, DEV-013) and this spec's DEV-011.
  - `skills/tdd-cycle/SKILL.md`: the `### Bug fixes: repro first` section; the bug example under `## Examples`, restored to the three-line `parseDate('')` example; the When to Use bug bullet, restored to "reproduce it with a failing test first."
  - `commands/prototype.md`: the bug-path sentence in Step 3 principle 1 and the `**Bug path:**` line in Step 3, as built (cherry-pick, not `git apply`).
  - `commands/implement-story.md`: the `**Bug path:**` line in Gate 1, as built (base kept across recodes; exit 2 routed).
  - `agents/coding-agent.md`: the bug-path sentences in Implementation Requirements 1 and 3; the `### Repro` item and output block.
  - `skills/subagent-worktree-integration/SKILL.md`: the ordered-commits paragraph.
  - `scripts/repro-order.py`, `scripts/tests/test_repro_order.py`, `scripts/tests/test_repro_first_wiring.py`: delete.
  - `.writ/docs/agent-cli-contract.md`: the `repro-order.py` row. `scripts/tests/test_agent_cli_contract.py`: its smoke entry.
  - `.writ/docs/config-format.md`: the `Repro First` key-table row and section.
- **Caps.** repro-first DEV-010 raised `KNOWN_OVER_BUDGET["commands/implement-story.md"]` in `scripts/tests/test_governor_enforcement.py` and `IMPLEMENT_STORY_CAP` in `scripts/tests/test_review_route_rigor.py` by 448 bytes. This spec's DEV-011 records that. Re-pin both downward from their values at execution time, to the post-removal measure with the existing slack. Read the current values first. DEV-011 measured 15717 and 40682 at Story 4 time.
- **No skill removed.** Repro First removes no skill directory, so `bash scripts/gen-skill.sh` is not needed.
- **Spec status.** Business Rule 13 governs. The contract's "Complete when Repro First is `keep` or `remove`" matches it only while the other three verdicts are `keep`, `remove`, or `absent`. The current `trial-report.md` has all three at `keep`. Gate 0 may be removed by the design-divergence blind trial (Business Rule 12); the outcome test enforces Rule 13 either way.
- **Removal-bias caveat.** The substitute proxy catches a defect only when a shipped fix still fails its repro at the story commit. Say so in the ADR note. A `keep` here is not proof of a general result.
- **Commit order.** (1) labeled substitute trial file, `trial-report-repro-first.md`, and the drift-log entry (task 6.2); (2) removal edits, if any (tasks 6.3, 6.4); (3) outcome test, roadmap, ADR-030, spec status (tasks 6.1, 6.5); (4) harness deletion (task 6.6). Never commit yuss content.
- **Shared hot spots.** `scripts/tests/test_governor_enforcement.py`, `.writ/product/roadmap.md`, ADR-030, and `.writ/docs/config-format.md` also get edits from sibling Phase 15 specs. Use targeted edits and re-pin from the current value.
- **Gate 0 is out of scope.** This story does not edit any Gate 0 wiring or `skills/design-divergence/`.
- **Never touched:** `commands/why.md`, `commands/writ.md`, `commands/retro.md`, `commands/refresh-command.md`, and anything under yuss.
- **Run the bash tests in the background.** They take about 12 minutes, past the Bash tool limit. Run pytest alone; do not run `eval.sh` or other writes under `.writ/state/` in the same checkout while it runs.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Story 4 row, applied to Repro First (`unverifiable` → Repro First untouched; spec status names the reason), `report` (`unlabeled`, `not_exercised_unacknowledged`, `amendment_requested`)] — from technical-spec.md → Error & Rescue Map
- **Shadow paths:** [Story 4 (`labeled_by` null → stop at task 6.2; every verdict `keep` → records only; a removal leaves `rg` hits → story fails its own verification)] — from technical-spec.md → Shadow Paths
- **Business rules:** [Upgrade-only (rule 5), labels (rule 6), acknowledgments (rule 7), verdict (rule 8), human gate (rule 9, delegated), commit order (rule 10), removal (rule 11), spec status (rule 13)] — from spec.md → Business Rules (Expanded)
- **Experience:** [Error experience (an `unverifiable` upgrade is left untouched and named in the spec status)] — from spec.md → 🎯 Experience Design
- **Technical:** technical-spec.md → ## Verdict Execution (Removal inventories; Repo state the outcome test asserts; Records); ## Upgrades Under Test (Repro First probe); ## Files in Scope
