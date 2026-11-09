# Story 6: Act on the Repro First Verdict

> **Status:** Completed ✅ (2026-11-09)
> **Priority:** Medium
> **Dependencies:** Story 5

## User Story

**As a** Writ maintainer
**I want to** label the substitute Repro First run, commit its report with the trial file, and keep or remove Repro First as that verdict decides
**So that** the last Phase 15 upgrade is decided on a committed record, and the repo, roadmap, ADR-030, and spec status agree with it

## Acceptance Criteria

> **AC IDs assigned through:** AC-6.5

- [x] Given `labeling-sheet-repro-first.md` lists upgrade-only findings, when the assistant labels them in a fresh pass without opening the trial JSON or raw outputs, then every note opens "Assistant-assessed, maintainer-delegated", `label --labeled-by "Adam Sellke (delegated to assistant)"` succeeds, `report`'s output is committed verbatim as `trial-report-repro-first.md` with the labeled substitute trial file before any removal edit, and `trial-report.md` stays byte-identical; with zero upgrade-only findings, `label` still runs on the field-less sheet so `labeled_by` is set, and the drift log records that no finding needed a label `[AC-6.1]`
- [x] Given Repro First's verdict is `remove`, when the story closes, then its Removal Inventory (Notes) is applied as built, both whole-file caps are re-pinned downward with a dated disclosure naming this spec and Story 6, `python3 scripts/gen-platform-trees.py` has run, `scripts/repro-order.py` is absent, and `rg -n 'Repro First' commands agents skills .writ/docs` is empty; given `keep` or `unverifiable`, then no Repro First file is edited and the spec stays open with the reason `[AC-6.2]`
- [x] Given the outcome test `scripts/tests/test_gate_upgrade_trial_outcome.py`, when it runs, then Repro First's verdict is read from `trial-report-repro-first.md` when that file exists, the other three verdicts are read from `trial-report.md`, and the test never imports the harness `[AC-6.3]`
- [x] Given Repro First's verdict, when the records are written, then the roadmap Phase 15 "Removal measurement" line and the "Phase 15 and 17 loose ends" item are updated, ADR-030 § Review gains a note with the date, the substitute story IDs (three, plus the excluded `73f34d4`; DEV-014), each verdict and count, the selection rule, the removal-bias caveat, and the delegated-label caveat, and `spec.md` reads `> **Status:** Complete` when every verdict is `keep`, `remove`, or `absent`, else `> **Status:** In Progress — <reason from report>` `[AC-6.4]`
- [x] Given the report commit exists and Repro First's verdict is `keep` or `remove`, when the story closes, then `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py`, `scripts/tests/test_gate_upgrade_trial.py`, and `scripts/tests/fixtures/gate-upgrade-trial/` are deleted, `uv run pytest scripts/tests/test_gate_upgrade_trial_outcome.py` passes, `commands/why.md`, `commands/writ.md`, `commands/retro.md`, and `commands/refresh-command.md` are unchanged, and both pytest runs, the bash tests, `python3 scripts/gen-platform-trees.py --check`, and `bash scripts/eval.sh` pass with 0 findings `[AC-6.5]`

## Implementation Tasks

- [x] 6.1 Write tests in `scripts/tests/test_gate_upgrade_trial_outcome.py` that Repro First reads `trial-report-repro-first.md` when it exists, the other three read `trial-report.md`, and the file never imports the harness `[AC-6.3]`
- [x] 6.2 Label the upgrade-only findings in `labeling-sheet-repro-first.md` from the excerpt files only, as the delegated assistant. Add a delegation entry to `drift-log.md`. Run `label`, then `report` on the substitute trial file. Commit `trial-report-repro-first.md` verbatim with that file `[AC-6.1]`
- [x] 6.3 If the verdict is `remove`, delete Repro First's wiring as built (Notes) from `skills/tdd-cycle/SKILL.md`, `agents/coding-agent.md`, `commands/prototype.md`, `commands/implement-story.md`, and `skills/subagent-worktree-integration/SKILL.md`. Otherwise edit nothing `[AC-6.2]`
- [x] 6.4 If removed, delete `scripts/repro-order.py`, `scripts/tests/test_repro_order.py`, and `scripts/tests/test_repro_first_wiring.py`. Edit `.writ/docs/config-format.md`, `.writ/docs/agent-cli-contract.md`, and `scripts/tests/test_agent_cli_contract.py`. Re-pin both caps. Run `python3 scripts/gen-platform-trees.py` `[AC-6.2]`
- [x] 6.5 Edit `.writ/product/roadmap.md` (Phase 15 "Removal measurement" line and "Phase 15 and 17 loose ends" item). Add the § Review note to `.writ/decision-records/adr-030-contract-verifier-boundary-front-door.md`. Set the `spec.md` status line `[AC-6.4]`
- [x] 6.6 If the verdict is `keep` or `remove`, and the report commit exists, delete `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py`, `scripts/tests/test_gate_upgrade_trial.py`, and `scripts/tests/fixtures/gate-upgrade-trial/` `[AC-6.5]`
- [x] 6.7 Verify: run `uv run --isolated --python 3.9 --with pytest pytest` and the `--python 3.14` form, each alone; the bash tests; `python3 scripts/gen-platform-trees.py --check`; `bash scripts/eval.sh` with 0 findings. If removed, confirm `scripts/repro-order.py` is absent and the `rg` check is empty `[AC-6.2, AC-6.3, AC-6.5]`

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Story 4 row, applied to Repro First (`unverifiable` → Repro First untouched; spec status names the reason), `report` (`unlabeled`, `not_exercised_unacknowledged`, `amendment_requested`)] — from technical-spec.md → Error & Rescue Map
- **Shadow paths:** [Story 4 (`labeled_by` null → stop at task 6.2; every verdict `keep` → records only; a removal leaves `rg` hits → story fails its own verification)] — from technical-spec.md → Shadow Paths
- **Business rules:** [Upgrade-only (rule 5), labels (rule 6), acknowledgments (rule 7), verdict (rule 8), human gate (rule 9, delegated), commit order (rule 10), removal (rule 11), spec status (rule 13)] — from spec.md → Business Rules (Expanded)
- **Experience:** [Error experience (an `unverifiable` upgrade is left untouched and named in the spec status)] — from spec.md → 🎯 Experience Design
- **Technical:** technical-spec.md → ## Verdict Execution (Removal inventories; Repo state the outcome test asserts; Records); ## Upgrades Under Test (Repro First probe); ## Files in Scope

## What Was Built

**Implementation Date:** 2026-11-09

### Files Created

1. **`.writ/specs/2026-10-25-gate-upgrade-removal-measurement/trial-report-repro-first.md`** (11 lines)
   - `report` output verbatim: `repro-first verdict=remove exercised=3/3 upgrade_only=0`.

### Files Modified

- **Repro First removal** (`c66061d`): `skills/tdd-cycle/SKILL.md` restored to `c687fab^`; `agents/coding-agent.md` reverse of `320bbf6`; `commands/prototype.md`, `commands/implement-story.md`, `skills/subagent-worktree-integration/SKILL.md`, `.writ/docs/config-format.md`, `.writ/docs/agent-cli-contract.md`, `scripts/tests/test_agent_cli_contract.py`; DEV-019 extras `scripts/story-gate.py`, `scripts/tests/test_story_gate.py`, `agents/supervisor-agent.md`, `README.md`; `KNOWN_OVER_BUDGET["commands/implement-story.md"]` 13553 → 13201 (exact); generated trees.
- **Deleted:** `scripts/repro-order.py`, `scripts/tests/test_repro_order.py`, `scripts/tests/test_repro_first_wiring.py`; the harness `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py`, `scripts/tests/test_gate_upgrade_trial.py`, `scripts/tests/fixtures/gate-upgrade-trial/` (`bfb67cf`).
- **`scripts/tests/test_gate_upgrade_trial_outcome.py`** — Repro First reads `trial-report-repro-first.md` and the substitute trial file; Business Rule 13 checks the mixed verdict set; 7 new tests `[AC-6.3]`.
- **Records** (`4144a72`): roadmap Phase 15 "Removal measurement" line, loose-ends item, and the repro-first feature item; ADR-030 § Review note; spec status `Complete`.
- **`scripts/review-panel.py`, `scripts/tests/test_review_panel.py`** — no longer name the deleted harness.
- **Spec metadata** (DEV-021): substitute baseline moved to `.writ/eval/gate-upgrade-trial/2026-11-09-repro-first-substitute-baseline.json`; Story 5 dependency line; `Verified by:` lines in Stories 2 and 5.

### Implementation Decisions

1. **Commit order** — `2898b05` report and labeled trial, `c66061d` removal, `4144a72` outcome test and records, `bfb67cf` harness deletion (Business Rule 10).
2. **Inventory amended as built** — four live references the inventory predates were removed with it, chiefly the `story-gate.py` post-review row that would have called a deleted script (DEV-019).
3. **One cap** — `IMPLEMENT_STORY_CAP` no longer exists; only `KNOWN_OVER_BUDGET` is re-pinned, exactly, because total overage is asserted exactly.
4. **Prose-only gates** — `test_default_check_table_equals_default_gates` now excludes gates marked `verification: prose-only`; `gate1_coding` lost its only runner row.

### Test Results

**Verification:** full suite `uv run --isolated --python 3.9 --with pytest pytest -q` → 4344 passed, 2 skipped; Python 3.14 → 4344 passed, 2 skipped, 1434 subtests passed; bash tests 0 failures; `gen-platform-trees.py --check` pass; `eval.sh` 27 findings on the first run, all from this spec (DEV-021), then 0 on `pipeline-baseline`, `review-override`, and `arch-check` after the fixes; outcome test 52 passed including the four live verdict checks. Red run for 6.1: 8 failed, 44 passed.
- ✅ test-integrity authenticity: pass
- coverage: unverifiable (coverage_report_absent)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s), plus one safety-fact re-spawn (`safety_fact_missing`, then `tested`)
- **Drift:** Medium (DEV-018 ⚠️, DEV-019 ⚠️; DEV-020, DEV-021 Small)
- **Security:** Clean
- **Boundary Compliance:** every change outside the original map is covered by DEV-019 or required by the removal
- **gate3-route:** review-agent (outside_boundary on README.md, agents/supervisor-agent.md, scripts/story-gate.py, scripts/review-panel.py, three test files, and generated trees)
- **reviewer-filters:** on
- **safety-fact:** tested (claimed traced)
- **evidence-gate:** not run (PASS)
- **jev shadow:** unverifiable (state_too_large) — advisory only
- **arch-lint:** none — see .writ/docs/architecture-lint.md
- **build-smoke:** unverifiable (unsupported_stack)
- **Advisories not applied:** `scripts/tests/test_agent_cli_contract.py:1119` still uses `repro-order.py` as a sample unlisted script; `.writ/product/mission.md:196`, `mission-lite.md:68,72`, and `roadmap.md:7,744` still describe Repro First as held or the spec as in progress.

