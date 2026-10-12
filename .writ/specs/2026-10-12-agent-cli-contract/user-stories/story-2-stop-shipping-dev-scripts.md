# Story 2: Stop Shipping Dev-Only Scripts

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer and developer who installs Writ into their projects
**I want to** have six dev-only scripts excluded from every install and update
**So that** installed projects carry only agent-facing scripts, and the contract in Story 3 covers exactly the set that ships

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given `is_shippable_script` in `scripts/install.sh` and in `scripts/update.sh`, when each is called with `pipeline-baseline.py`, `measure-invocation.py`, `harness-cost.py`, `lean-decision.py`, `prune-ledger.py`, and `spawn-cap.py`, then each call returns non-zero; a call with `spec-status.py` returns zero; the two function bodies are byte-identical; and the six source files still exist under `scripts/` `[AC-2.1]`
- [ ] Given a temp project and a source copy that contains the six, when `install.sh --platform claude --no-commit` completes, then the project's `scripts/` holds none of the six and the install manifest has no entry for any of them `[AC-2.2]`
- [ ] Given an installed project whose manifest records an unmodified copy of `harness-cost.py` and a source tree that no longer ships it, when `update.sh` runs, then the local copy is removed and the run reports it as removed `[AC-2.3]`
- [ ] Given the same setup with a locally modified copy of `harness-cost.py`, when `update.sh` runs, then the local copy is kept and the run prints a stale warning that names the file `[AC-2.4]`
- [ ] Given the shipped sources under `commands/`, `agents/`, `skills/`, `adapters/`, and `.writ/docs/`, when the test greps for `scripts/<name>` for each of the six names, then it finds no match; and `commands/update-writ.md` Step 3 lists the six as excluded dev-only helpers `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write failing shell tests in a new `scripts/tests/test_install_update_dev_scripts.sh`, following the fixture and assert pattern of `scripts/tests/test_install_update_lean_siblings.sh`, covering each of AC-2.1 through AC-2.5 `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [ ] 2.2 Add a case arm listing the six names to `is_shippable_script` in `scripts/install.sh` (line ~922), placed before the `*.py|*.sh` acceptance, with `return 1` and a one-line comment citing ADR-029 `[AC-2.1, AC-2.2]`
- [ ] 2.3 Add the identical case arm to `is_shippable_script` in `scripts/update.sh` (line ~569) and confirm the two function bodies match with a byte comparison `[AC-2.1, AC-2.3, AC-2.4]`
- [ ] 2.4 Reword the exclusion prose in `commands/update-writ.md` Step 3 to name the six as dev-only measurement and eval helpers, using bare names without a `scripts/` path `[AC-2.5]`
- [ ] 2.5 Reword `.writ/docs/skills.md` line 330 so it no longer names `scripts/measure-invocation.py`; leave the rest of the file unchanged `[AC-2.5]`
- [ ] 2.6 Verify the shell tests: run `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, then run `bash scripts/install.sh --dry-run` in a temp directory and confirm none of the six appear `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [ ] 2.7 Verify the regression surface: run `bash scripts/eval.sh` outside the sandbox and `uv run pytest`; both must pass, and eval must still run the six from the source tree `[AC-2.1]`

## Notes

- **Fixtures for AC-2.3 and AC-2.4.** `update.sh` removes only what the manifest records. Build the fixture by installing from a source copy that still contains the six, then run `update.sh` against a copy without them. A fixture with no manifest entry tests nothing.
- **Stale logic.** Read `detect_stale_files` (`scripts/update.sh`, ~line 804) and the stale-removal block (~line 1089) before writing assertions. Assert the exact removal and warning output the code produces. Do not assume wording.
- **Eval depends on these files.** `scripts/eval.sh` calls `pipeline-baseline.py` (~line 3855), `prune-ledger.py` (~line 3905), and `spawn-cap.py` (~line 4679) from the source tree. Exclude them from shipping only. Do not delete, move, or rename them.
- **Product files.** `scripts/install.sh` and `scripts/update.sh` ship to every user. Keep the change to the six-name arm. Make no other filter edits, because Story 3's ship set depends on the final filter.
- **Never run `install.sh` against the Writ repo.** It is symlinked into `.claude/` and `.cursor/` (CLAUDE.md). Run installs only in temp directories.
- **Unrelated working-tree edits.** Other uncommitted edits may exist. Run `git diff` before and after touching a shared file, and change only the targeted lines.
- **Independence.** Story 1 (contract doc, ADR amendment) does not touch these files. This story can run in parallel with it.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Update removes dev-only script] from technical-spec.md → ## Error & Rescue Map (modified copy is flagged stale and kept)
- **Business rules:** spec.md → ## 📋 Business Rules (Expanded) rule 1 (scope follows the ship filter; the test and the filter never keep separate lists)
- **Experience:** spec.md → ## Experience Design → ### State Catalog, row "Dev-only script in an installed project after update"
- **Technical:** spec.md → ## Detailed Requirements → ### Story 2; technical-spec.md → ## Ship Filter (Story 2) and ## Files in Scope (Story 2 rows)
- **Test pattern:** `scripts/tests/test_install_update_lean_siblings.sh` (committed source copy, temp targets, `fail` helper, `hash_file` helper)
