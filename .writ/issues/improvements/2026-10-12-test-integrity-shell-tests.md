# test-integrity authenticity flags every shell test

> **Type:** Improvement
> **Priority:** Normal
> **Effort:** Small
> **Created:** 2026-10-12
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

`test-integrity.py authenticity` reports `test_imports_no_source` (blocking) for every `scripts/tests/test_*.sh`, because it only counts Python imports and Python subprocess calls as exercising source.

## Current State

- `test_install_update_lean_siblings.sh`, `test_install_update_thresholds.sh`, `test_eval_spawn_cap.sh`, and the new `test_install_update_dev_scripts.sh` all fail with `0 project-source imports`, though each runs `scripts/install.sh` or `scripts/update.sh` by path.
- Gate 4 treats the finding as blocking, so any story whose tests are shell scripts cannot pass Gate 4 honestly.
- `2026-10-12-agent-cli-contract` Story 2 recorded it as a checker false positive, with mutation evidence that its test fails when the code under test changes.

## Expected Outcome

- A shell test that runs a project script by path (`bash "$ROOT/scripts/x.sh"`, `"$SRC/scripts/x.sh"`, `source …/scripts/x.sh`) counts as exercising source.
- A shell test that touches no project script still gets `test_imports_no_source`.

## Relevant Files

- `scripts/test-integrity.py` - `SCRIPT_SUFFIXES` and the script-literal check (~line 292, ~375)
- `scripts/tests/test_test_integrity.py` - add shell-test cases
