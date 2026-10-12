# Story 2: Stop Shipping Dev-Only Scripts

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer and developer who installs Writ into their projects
**I want to** have six dev-only scripts excluded from every install and update
**So that** installed projects carry only agent-facing scripts, and the contract in Story 3 covers exactly the set that ships

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given `is_shippable_script` in `scripts/install.sh` and in `scripts/update.sh`, when each is called with `pipeline-baseline.py`, `measure-invocation.py`, `harness-cost.py`, `lean-decision.py`, `prune-ledger.py`, and `spawn-cap.py`, then each call returns non-zero; a call with `spec-status.py` returns zero; the two function bodies are byte-identical; and the six source files still exist under `scripts/` `[AC-2.1]`
- [x] Given a temp project and a source copy that contains the six, when `install.sh --platform claude --no-commit` completes, then the project's `scripts/` holds none of the six and the install manifest has no entry for any of them `[AC-2.2]`
- [x] Given an installed project whose manifest records an unmodified copy of `harness-cost.py` and a source tree that no longer ships it, when `update.sh` runs, then the local copy is removed and the run reports it as removed `[AC-2.3]`
- [x] Given the same setup with a locally modified copy of `harness-cost.py`, when `update.sh` runs, then the local copy is kept and the run prints a stale warning that names the file `[AC-2.4]`
- [x] Given the shipped sources under `commands/`, `agents/`, `skills/`, `adapters/`, and `.writ/docs/`, when the test greps for `scripts/<name>` for each of the six names, then it finds no match; and `commands/update-writ.md` Step 3 lists the six as excluded dev-only helpers `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Write failing shell tests in a new `scripts/tests/test_install_update_dev_scripts.sh`, following the fixture and assert pattern of `scripts/tests/test_install_update_lean_siblings.sh`, covering each of AC-2.1 through AC-2.5 `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [x] 2.2 Add a case arm listing the six names to `is_shippable_script` in `scripts/install.sh` (line ~922), placed before the `*.py|*.sh` acceptance, with `return 1` and a one-line comment citing ADR-029 `[AC-2.1, AC-2.2]`
- [x] 2.3 Add the identical case arm to `is_shippable_script` in `scripts/update.sh` (line ~569) and confirm the two function bodies match with a byte comparison `[AC-2.1, AC-2.3, AC-2.4]`
- [x] 2.4 Reword the exclusion prose in `commands/update-writ.md` Step 3 to name the six as dev-only measurement and eval helpers, using bare names without a `scripts/` path `[AC-2.5]`
- [x] 2.5 Reword `.writ/docs/skills.md` line 330 so it no longer names `scripts/measure-invocation.py`; leave the rest of the file unchanged `[AC-2.5]`
- [x] 2.6 Verify the shell tests: run `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, then run `bash scripts/install.sh --dry-run` in a temp directory and confirm none of the six appear `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [x] 2.7 Verify the regression surface: run `bash scripts/eval.sh` outside the sandbox and `uv run pytest`; both must pass, and eval must still run the six from the source tree `[AC-2.1]`

## Notes

- **Fixtures for AC-2.3 and AC-2.4.** `update.sh` removes only what the manifest records. Build the fixture by installing from a source copy that still contains the six, then run `update.sh` against a copy without them. A fixture with no manifest entry tests nothing.
- **Stale logic.** Read `detect_stale_files` (`scripts/update.sh`, ~line 804) and the stale-removal block (~line 1089) before writing assertions. Assert the exact removal and warning output the code produces. Do not assume wording.
- **Eval depends on these files.** `scripts/eval.sh` calls `pipeline-baseline.py` (~line 3855), `prune-ledger.py` (~line 3905), and `spawn-cap.py` (~line 4679) from the source tree. Exclude them from shipping only. Do not delete, move, or rename them.
- **Product files.** `scripts/install.sh` and `scripts/update.sh` ship to every user. Keep the change to the six-name arm. Make no other filter edits, because Story 3's ship set depends on the final filter.
- **Never run `install.sh` against the Writ repo.** It is symlinked into `.claude/` and `.cursor/` (CLAUDE.md). Run installs only in temp directories.
- **Unrelated working-tree edits.** Other uncommitted edits may exist. Run `git diff` before and after touching a shared file, and change only the targeted lines.
- **Independence.** Story 1 (contract doc, ADR amendment) does not touch these files. This story can run in parallel with it.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Update removes dev-only script] from technical-spec.md → ## Error & Rescue Map (modified copy is flagged stale and kept)
- **Business rules:** spec.md → ## 📋 Business Rules (Expanded) rule 1 (scope follows the ship filter; the test and the filter never keep separate lists)
- **Experience:** spec.md → ## Experience Design → ### State Catalog, row "Dev-only script in an installed project after update"
- **Technical:** spec.md → ## Detailed Requirements → ### Story 2; technical-spec.md → ## Ship Filter (Story 2) and ## Files in Scope (Story 2 rows)
- **Test pattern:** `scripts/tests/test_install_update_lean_siblings.sh` (committed source copy, temp targets, `fail` helper, `hash_file` helper)

## What Was Built

**Implementation Date:** 2026-10-12

### Files Created

1. **`scripts/tests/test_install_update_dev_scripts.sh`** — covers AC-2.1 to AC-2.5. Reads `is_shippable_script` out of `install.sh`, `update.sh`, and `unlink.sh` and compares the bodies. Installs into a temp project. Runs `update.sh` twice against two source copies, one that keeps the six (filtered) and one that deletes them, checking dry-run non-mutation, removal of an unmodified copy, the kept-modified warning, baseline carry-forward, and a second-run warning. Greps shipped sources for `scripts/<six>` paths. [AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]
2. **`.writ/issues/bugs/2026-10-12-update-deletes-modified-stale-files.md`**, **`.writ/issues/bugs/2026-10-12-codex-config-baseline-dropped-on-update.md`**, **`.writ/issues/improvements/2026-10-12-test-integrity-shell-tests.md`** — pre-existing problems found during this story.

### Files Modified

1. **`scripts/install.sh`, `scripts/update.sh`, `scripts/unlink.sh`** — six-name `return 1` arm in `is_shippable_script`, byte-identical in all three. [AC-2.1, AC-2.2]
2. **`scripts/update.sh`** — `detect_stale_files`: `scripts/` paths resolve at the project root; a manifest-listed script the filter rejects is stale; a kept, locally modified stale script prints `⚠️  Stale (no longer shipped, locally modified — kept): <path>`. `write_copy_manifest`: carries that script's old baseline forward (`STALE_KEPT_ENTRIES`). Approved by the maintainer at the Gate 1 BLOCKED escalation; the warning was limited to `scripts/` after Gate 3. [AC-2.3, AC-2.4]
3. **`commands/update-writ.md`** — Step 3 lists the six as dev-only measurement and eval helpers; "Detect stale files" says filter-rejected scripts count as stale. [AC-2.5]
4. **`.writ/docs/skills.md`** — line 330 no longer names `scripts/measure-invocation.py`. [AC-2.5]
5. **`sub-specs/technical-spec.md`** — dated amendment to "Ship Filter (Story 2)" and the Error & Rescue Map row.

### Verification

- `bash scripts/tests/test_install_update_dev_scripts.sh` → PASS. The coding agent removed the filter-stale hunk and, separately, the carry-forward; the test failed both times.
- Full bash loop: 0 failures. `uv run pytest -q` → 2289 passed, 2 skipped. `bash scripts/eval.sh` → exit 0, Findings: 0 (leanness warnings pre-existing, warn-only); eval still runs the six from the source tree.
- Gate 1: first run BLOCKED (the spec's stale-file premise was false); maintainer approved the update.sh patch; second run COMPLETE.
- Gate 2: `bash -n` clean on all changed scripts. Gate 2.5: cross-component, 0 crossings, route evaluator-agent.
- Gate 3 evaluator: PASS, iteration 1, with probes in temp projects (dry run byte-identical manifest, no duplicate entries over three runs, other categories unchanged). Minor residual — "kept" warning printed for categories that are re-baselined — fixed by limiting it to `scripts/`. review-override: unverifiable (no coverage report).
- Gate 3.5 drift-format: pass. Drift: DEV-001 Medium, DEV-002 Small, DEV-003 Small.
- Gate 4 test-integrity: coverage unverifiable (no report). Authenticity `test_imports_no_source` is a checker false positive for shell tests: every existing install/update shell test gets the same verdict, and the mutation runs above show this test fails when the code changes. Filed as `.writ/issues/improvements/2026-10-12-test-integrity-shell-tests.md`.
- Gate 4.5: app-verify unverifiable (no recipe). Gate 5: docs-check unverifiable (no public exports).
- Iteration count: 1
