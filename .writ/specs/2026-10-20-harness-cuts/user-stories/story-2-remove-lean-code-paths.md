# Story 2: Remove the Lean Code Paths from the Scripts

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer
**I want to** have every lean flag branch, the lean arm of the baseline tooling, and `lean-decision.py` removed from `scripts/`
**So that** no script carries a code path for files that no longer exist, and the guard grep comes back empty across the whole repo outside the historical records

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given the repo after this story, when the guard grep runs with the full pathspec from spec.md Business Rule 2, then it prints nothing, and `scripts/lean-decision.py`, `scripts/tests/test_lean_decision.py`, `scripts/tests/test_measure_invocation_lean.py`, and `scripts/tests/test_eval_manifest_lean.sh` do not exist `[AC-2.1]`
- [ ] Given a story whose fetched context exceeds the budget, when `python3 scripts/story-context.py assemble --story <path> --budget-bytes N` runs with and without `--state-dir DIR`, then both runs exit 0 with identical output, the payload keys are exactly `fetched_context`, `warnings`, `bytes`, and `truncated`, the context is truncated by priority as today, and no file is written under `DIR` or `.writ/state/` `[AC-2.2]`
- [ ] Given `scripts/pipeline-baseline.py`, when `run --help` is read and `overlay_writ` writes a run record, then `--lean` is not an accepted option, the record's `writ` block has exactly `source`, `commit`, `dirty`, `checkout_manifest_version`, and `manifest_diff_count`, and `validate` still passes a baseline whose records carry a legacy `harness_lean` of true or false `[AC-2.3]`
- [ ] Given a temp root whose `commands/` holds `a.md` and `b.variant.md`, when `eval-leanness.py` computes `all_command_files` and `metrics.commands`, then both files are commands; and given the real repo, `measure-invocation.py`'s report has no `harness_lean` key and `scripts/eval.sh` `check_manifest` has no name-based exemption for command files `[AC-2.4]`
- [ ] Given `is_shippable_script` in `scripts/install.sh`, `scripts/update.sh`, and `scripts/unlink.sh`, when the bodies are read and compared, then the dev-only arm no longer names `lean-decision.py`, the three bodies are byte-identical, `test_install_update_dev_scripts.sh` passes with `prune-ledger.py` as its locally modified fixture, and neither `.writ/docs/agent-cli-contract.md` nor `commands/update-writ.md` names `lean-decision.py` `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write failing tests first: widen the guard in `scripts/tests/test_harness_cuts.py` to `.` plus the exclusion list and add the four deleted-file checks; add a `test_story_context.py` case for an over-budget story with `--state-dir` (no `spill` key, no file written); update `test_pipeline_baseline_run.py` for the new `WRIT_KEYS` and record shape and add a `run --lean` usage-error case; reduce `test_pipeline_baseline.py:1233` to the legacy-tolerance case; add the AC-2.4 fixture case to `test_eval_leanness_contract.py`; switch `test_install_update_dev_scripts.sh` to `prune-ledger.py` and drop `lean-decision.py` from `test_agent_cli_contract_doc.py` `DEV_ONLY`. Run them and record the failures `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [ ] 2.2 `scripts/story-context.py`: delete `LEAN_ENV`, `DEFAULT_STATE_DIR`, `SPILL_TAIL_BYTES`, `_harness_lean`, `_spill`, `_tail_cut_category`, and the spill branch and parameter of `_payload`. Keep `state_dir=None` on `assemble` and `--state-dir` on the CLI as a hidden no-op (`help=argparse.SUPPRESS`). Update the docstring and usage. In `test_story_context.py`, delete `SpillFlagOnTests`, `SpillFlagOffTests`, `SpillRescueTests`, `RealStateDirGuardTests`, and the flag helpers; the base class stops popping the variable and patching `DEFAULT_STATE_DIR` `[AC-2.2]`
- [ ] 2.3 `scripts/measure-invocation.py`: delete the lean flag constants, `_harness_lean`, `_resolve_lean`, the `.lean.md` filter, the per-command `source` key, and the `harness_lean` report key. `scripts/eval-leanness.py`: delete `is_lean_sibling` and its two uses. `scripts/eval.sh` `check_manifest`: delete lines 581-584. Delete `test_measure_invocation_lean.py` and `test_eval_manifest_lean.sh`; remove the env patch at `test_measure_invocation.py:74-84` `[AC-2.1, AC-2.4]`
- [ ] 2.4 `scripts/pipeline-baseline.py`: delete `run --lean` and everything only it uses (technical-spec.md → ## Story 2 Design). `WRIT_KEYS` drops `harness_lean`; `validate` is unchanged. Delete `LeanArmTest` and its fixtures from `test_pipeline_baseline_run.py`. Afterwards `grep -n -i lean scripts/pipeline-baseline.py` shows only words containing "clean" `[AC-2.1, AC-2.3]`
- [ ] 2.5 Delete `scripts/lean-decision.py` and `scripts/tests/test_lean_decision.py`. Drop `lean-decision.py` from the dev-only arm of `is_shippable_script` in `install.sh`, `update.sh`, and `unlink.sh`, keeping the three bodies byte-identical. Reword `.writ/docs/agent-cli-contract.md:126` (five dev-only scripts) and `commands/update-writ.md:111` `[AC-2.1, AC-2.5]`
- [ ] 2.6 Verify the shell tests: `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`. Never run `install.sh` or `update.sh` against the Writ repo itself; the tests use temp directories `[AC-2.5]`
- [ ] 2.7 Verify the suite: `uv run --python 3.9 pytest` (including `test_agent_cli_contract.py`, which must still pass `story-context.py`'s `--help` and bad-flag checks) and `bash scripts/eval.sh` outside the sandbox with 0 findings `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`

## Notes

- **`--state-dir` stays.** `story-context.py` ships. The agent CLI contract says a removed flag stays accepted as a no-op. `pipeline-baseline.py` is dev-only, so `--lean` goes outright.
- **Legacy baselines.** `.writ/eval/baselines/2026-09-25-lean-arms/` holds records with `writ.harness_lean`. `eval.sh` `check_pipeline_baseline` validates only top-level `*.json`, but `validate` must still accept the key so those files stay readable.
- **Default outputs do not change.** `measure-invocation.py` with the flag unset already printed no `harness_lean` and loaded default files. `story-context.py` without the flag already truncated. Removing the flag branch must leave the default output byte-identical; compare before and after on the real repo.
- **`test_install_update_dev_scripts.sh`** uses `lean-decision.py` as the kept-modified fixture in `KEPT_WARNING`, `plant_old_install`, and `check_update`. Replace every use with `prune-ledger.py`. Its "upstream deleted the six" case already covers an installed `lean-decision.py` from before v0.42.0.
- **`harness-cost.py` needs no edit.** It has no lean code; its `static` command total includes the lean files only because it globs `commands/*.md`, and that drops after Story 1.
- **Shared files with Stories 3 and 4.** `test_harness_cuts.py`, the ship-filter arm, and `.writ/docs/agent-cli-contract.md` are edited again later. Keep changes to the lines named here.
- **Never run `install.sh` or `update.sh` against the Writ repo.** Use temp directories.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Remove a lean code path, Delete lean-decision.py]
- **Shadow paths:** [Guard grep]
- **Business rules:** [Rule 2 (guard grep and its exclusions), Rule 3 (ship filters stay identical), Rule 7 (removed flags), Rule 8 (legacy data stays readable), Rule 11 (every story leaves the tree green)]
- **Experience:** [State Catalog: Maintainer exports the old lean variable, Writ source repo]
- **Technical:** technical-spec.md → ## Current State → ### Lean reference inventory (rows marked 2); ## Story 2 Design
