# Story 1: Delete the Lean Siblings and Their Install Logic

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer and developer who installs Writ into their projects
**I want to** have the five lean command siblings and the install/update logic that skips them deleted
**So that** Writ stops maintaining a second copy of four commands and the preamble that its own baseline showed no measurable win for, and old installed copies are cleaned up on update

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given the tree after this story, when `ls commands/*.lean.md` runs and the guard grep from spec.md Business Rule 2 runs over `commands README.md scripts/install.sh scripts/update.sh .writ/docs .writ/issues`, then no lean file exists, the grep prints nothing, and neither `scripts/install.sh` nor `scripts/update.sh` defines `is_unshipped_lean_sibling` `[AC-1.1]`
- [x] Given a temp project and a committed source copy of the working tree, when `install.sh --platform claude --no-commit` runs, first with `--dry-run` and then for real, then no file ending in `.lean.md` is listed, copied into `.claude/commands/`, or recorded in `.claude/.writ-manifest` `[AC-1.2]`
- [x] Given a temp project whose manifest records unmodified copies of `commands/implement-story.lean.md` and `commands/_preamble.lean.md`, when `update.sh --dry-run` runs and then `update.sh` runs, then the dry run lists both as stale and changes nothing, and the real run removes both, prints `🗑  Removed: commands/<name>` for each, and leaves neither in the manifest `[AC-1.3]`
- [x] Given the same project with a locally modified `commands/verify-spec.lean.md` recorded in the manifest, when `update.sh` runs twice, then the file is byte-identical after both runs and each run prints `⚠️  Stale (no longer shipped, locally modified — kept): commands/verify-spec.lean.md` (or the exact text the dependency spec's `detect_stale_files` prints) `[AC-1.4]`
- [x] Given every test and eval check that reads a lean file today (technical-spec.md inventory rows marked Story 1), when `uv run --python 3.9 pytest`, every `scripts/tests/test_*.sh`, and `bash scripts/eval.sh` run, then none reads a lean file, the non-lean assertions in those files still run, and all three pass with 0 eval findings `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write failing tests first. Create `scripts/tests/test_harness_cuts.py` with the Story 1 guard (no `commands/*.lean.md`; `git grep` for the two patterns over the AC-1.1 paths prints nothing) and `scripts/tests/test_install_update_harness_cuts.sh` with the lean upgrade-path cases from technical-spec.md → ## Story 1 Design. Run both on the current tree and record that they fail `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.2 Delete `commands/_preamble.lean.md`, `commands/create-spec.lean.md`, `commands/implement-phase.lean.md`, `commands/implement-story.lean.md`, `commands/verify-spec.lean.md`, and the lean-only tests that read them: `scripts/tests/test_lean_commands.py`, `scripts/tests/test_lean_preamble.py`, `scripts/tests/test_install_update_lean_siblings.sh` `[AC-1.1, AC-1.5]`
- [x] 1.3 Remove the lean-file reads from the mixed tests (`test_agent_cli_contract.py`, `test_implement_story_default_path.py`, `test_panel_trial_outcome.py`, `test_product_check_direction.py`, `test_quality_gate_wiring.py`, `test_review_panel.py`, `test_jev_setup_hooks.sh`, `test_jev_shadow_hooks.sh`, `test_uat_plan_verification_hooks.sh`) and from `scripts/eval.sh` `check_review_panel` and `check_product_check_direction`, at the lines the inventory lists. Leave every non-lean assertion as it is `[AC-1.5]`
- [x] 1.4 Remove `is_unshipped_lean_sibling` from `scripts/install.sh` (definition and its calls in the command count and `overlay_scan`) and from `scripts/update.sh` (definition, the `overlay_scan` call, and the lean arm in `detect_stale_files`). Keep the `scripts/` filter-rejected arm and reword the comment above it `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.5 Reword `README.md:63` (drop the lean-flag sentence, keep the measurement sentence), `.writ/docs/agent-cli-contract.md:132` (drop "including `*.lean.md` files"), and `.writ/issues/improvements/2026-10-01-product-lint-misread-as-verify-spec.md:24,30` (drop `verify-spec.lean.md`) `[AC-1.1]`
- [x] 1.6 Verify install and update: run `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, then `bash scripts/install.sh --dry-run --platform claude --no-commit` from a temp directory and confirm no `.lean.md` line. Never run `install.sh` or `update.sh` against the Writ repo itself; use temp directories `[AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.7 Verify the suite: `uv run --python 3.9 pytest` and `bash scripts/eval.sh` outside the sandbox. Both pass and eval reports 0 findings `[AC-1.1, AC-1.5]`

## Notes

- **Order matters.** Delete the files before Story 2 removes the code paths. If `eval-leanness.py` lost its lean exemption first, it would count `implement-story.lean.md` (32,187 bytes) as a new over-budget command and `test_governor_enforcement.py` would fail.
- **AC-1.4 depends on `2026-10-20-ci-and-update-integrity`.** Today only `scripts/` keeps a modified stale file across two runs. That spec carries the old baseline forward in every category. Read `detect_stale_files` as it left it and assert the warning text it prints.
- **Fixtures need manifest lines.** `update.sh` removes only what the manifest records. Plant each old lean file with a `<sha256>  commands/<name>` line. Any content works; the source no longer has the real files.
- **Force a manifest rewrite on run 1.** If the kept file were the only difference, `update.sh` would exit "Already up to date" before rewriting the manifest. The two unmodified removals in AC-1.3 make run 1 rewrite it.
- **Shell tests that grep a missing file pass silently.** `test_jev_shadow_hooks.sh` and `test_jev_setup_hooks.sh` grep the lean files with `&&`/`if`; grep exits 2 on a missing file and the check passes. Edit them anyway. Story 2's repo-wide guard catches any leftover.
- **`test_review_panel.py`** loops over `(STORY_CMD, LEAN_CMD)` in many places, and its eval fixture root copies the lean file. Each loop becomes `STORY_CMD` only.
- **Never run `install.sh` against the Writ repo.** `.claude/` and `.cursor/` are symlinks into the source (CLAUDE.md). Run installs only in temp directories.
- **Historical records stay.** Do not edit `CHANGELOG.md`, `.writ/decision-log.md`, `.writ/specs/archive/`, `.writ/research/`, `.writ/product/`, `.writ/decision-records/`, or the Complete spec `.writ/specs/2026-10-12-agent-cli-contract/`.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Fresh install, Update removes an unmodified cut file, Update keeps a modified cut file, Delete a lean file, Remove a lean code path]
- **Shadow paths:** [Install (any platform), Update over an old install, Update with a modified cut file, Guard grep]
- **Business rules:** [Rule 1 (historical records not edited), Rule 2 (guard grep and its exclusions), Rule 4 (dev-only and stale handling), Rule 10 (never run install/update against the Writ repo), Rule 11 (every story leaves the tree green)]
- **Experience:** [State Catalog: Fresh install any platform, Update old unmodified copies present, Update a copy edited locally]
- **Technical:** technical-spec.md → ## Current State → ### Lean reference inventory (rows marked 1); ## Story 1 Design

---

## What Was Built

**Implementation Date:** 2026-10-20

### Files Created

1. **`scripts/tests/test_harness_cuts.py`** (170 lines) — guard tests. AC-1.1: no `commands/*.lean.md`; the Business Rule 2 guard grep over `commands README.md scripts/install.sh scripts/update.sh .writ/docs .writ/issues` prints nothing; neither `install.sh` nor `update.sh` defines or names `is_unshipped_lean_sibling`. AC-1.5: the three lean-only tests are gone; the nine mixed tests plus `test_manifest_shipped_baselines.sh` name no lean file and still exist; `check_review_panel` and `check_product_check_direction` name no lean file and still pin a `commands/` file.
2. **`scripts/tests/test_install_update_harness_cuts.sh`** (157 lines) — upgrade path on a committed source copy in a temp dir. AC-1.2: claude install, dry run and real, lists, copies, and records no `.lean.md`. AC-1.3: unmodified `implement-story.lean.md` and `_preamble.lean.md` with manifest lines are listed stale by the dry run (tree unchanged) and removed by the real run with `🗑  Removed:` lines and no manifest line. AC-1.4: a modified `verify-spec.lean.md` survives two updates byte for byte, warns on each, and keeps its original baseline.

### Files Modified

- **`commands/_preamble.lean.md`, `create-spec.lean.md`, `implement-phase.lean.md`, `implement-story.lean.md`, `verify-spec.lean.md`** — deleted.
- **`scripts/tests/test_lean_commands.py`, `test_lean_preamble.py`, `test_install_update_lean_siblings.sh`** — deleted.
- **`scripts/install.sh`** — removed `is_unshipped_lean_sibling` and its calls in `write_copy_manifest` (commands and agents loops), the `CMD_COUNT` loop, and `overlay_scan`.
- **`scripts/update.sh`** — removed `is_unshipped_lean_sibling` and its calls in `write_copy_manifest` (commands and agents loops), `overlay_scan`, and the lean arm of `detect_stale_files`. The `! -f "$upstream_file"` test, the `scripts/` filter-rejected arm, and the kept-modified branch stay; the comment describes the two remaining arms.
- **`scripts/eval.sh`** (`check_review_panel`, `check_product_check_direction`) — pin only the default files.
- **Mixed tests** — lean reads removed from `test_agent_cli_contract.py`, `test_implement_story_default_path.py`, `test_panel_trial_outcome.py`, `test_product_check_direction.py`, `test_quality_gate_wiring.py`, `test_review_panel.py`, `test_jev_setup_hooks.sh`, `test_jev_shadow_hooks.sh`, `test_uat_plan_verification_hooks.sh`, and `test_manifest_shipped_baselines.sh` (DEV-002).
- **`scripts/tests/test_gen_claude_agents.py`, `scripts/tests/test_jev_shadow_hooks.sh`** — `AC-2.2` and `AC-2.4` citations for `2026-10-20-claude-agent-generator` (DEV-003).
- **`README.md`, `.writ/docs/agent-cli-contract.md`, `.writ/issues/improvements/2026-10-01-product-lint-misread-as-verify-spec.md`** — lean mentions removed; the issue file also drops the deleted `test_lean_commands.py`.

### Implementation Decisions

1. **Every call removed, not only the listed ones** — the dependency spec added two `write_copy_manifest` calls per script after the inventory was written (DEV-001).
2. **The guard test fails on any mention of `is_unshipped_lean_sibling`**, not only its definition, because a leftover `name ... && continue` call would fail silently.
3. **Bash-test authenticity carried on evidence** — mutation runs on scratch copies of `update.sh`: removing the `! -f "$upstream_file"` arm fails the test ("update dry run prints no stale-file list"); removing the `STALE_KEPT_ENTRIES` carry-forward fails it ("manifest dropped the original baseline").

### Test Results

**Verification:** test-first, then full suites.

- Red: `test_harness_cuts.py` on the unchanged tree → 4 failed; the AC-1.5 class on a `git archive HEAD` extract → 3 of 4 failed (the "still exist" test passes on both trees by design); `test_install_update_harness_cuts.sh` → `FAIL: source still ships _preamble.lean.md`.
- Green (orchestrator run): `uv run --python 3.9 pytest -q scripts/tests/test_harness_cuts.py` → 8 passed; the targeted Python set → 579 passed, 1 skipped (before the AC-1.5 tests); the six touched bash tests → PASS.
- Full suites (coding agent and reviewer, run alone): `uv run --python 3.9 pytest` → 2634 passed, 2 skipped (baseline 2683; −53 in the two deleted files, −4 removed methods, +8 new); bash loop → 40 run, 0 failed; `bash scripts/eval.sh` → `Findings: 0`.
- Completion simulation: with Story 1 marked Completed in a slug-named copy, `review-override.py check` → `pass`; `ac-trace.py check` → no findings.

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s)
- **Drift:** Small (DEV-001 to DEV-004)
- **Security:** Clean
- **Boundary Compliance:** one justified deviation (`test_gen_claude_agents.py`, docstring only)
- gate3-route: review-agent (outside_boundary over the changed set; cross-component surface). review-panel: skipped (platform cannot spawn other vendors). arch-lint: none — see .writ/docs/architecture-lint.md.
- Gate 0 arch-check: pass (rederived proceed). Gate 2: no linter configured; `bash -n` and `py_compile` clean; build-smoke unverifiable (unsupported stack). Gate 3 iteration 1: FAIL (AC-1.5 had no test citation; `untested_criterion` once Completed). Iteration 2: PASS. review-override: unverifiable before completion, pass in the completion simulation. Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable (no report). Gate 4 authenticity: `test_imports_no_source` on `test_install_update_harness_cuts.sh`, the known false positive for bash tests (`.writ/issues/improvements/2026-10-12-test-integrity-shell-tests.md`); carried on the red-phase proof and the mutation runs above, not DEGRADED. Gate 4.5: app-verify unverifiable (no recipe). Gate 5: docs-check unverifiable (no public exports).

### Deviations from Spec

- **[DEV-001] More `is_unshipped_lean_sibling` call sites removed than the inventory lists** — Severity: Small
  - Spec said: definition, command count, `overlay_scan` (install); definition, `overlay_scan`, `detect_stale_files` arm (update).
  - Reality: also the `write_copy_manifest` commands and agents loops in both scripts.
  - Resolution: Auto-amended.
  - Spec amendment: spec-lite.md S1 Files in Scope line.
- **[DEV-002] `test_manifest_shipped_baselines.sh` edited though absent from the inventory** — Severity: Small
  - Spec said: nine mixed tests.
  - Reality: this dependency-spec test also read a lean file; its lean filter and the lean half of its AC-3.4 fixture were removed.
  - Resolution: Auto-amended.
  - Spec amendment: spec-lite.md S1 Files in Scope line.
- **[DEV-003] Citations for another spec added outside Files in Scope** — Severity: Small
  - Spec said: nothing.
  - Reality: `AC-2.2` and `AC-2.4` citations for `2026-10-20-claude-agent-generator` replace the bare tokens the deleted `test_lean_preamble.py` carried.
  - Resolution: Auto-amended.
  - Spec amendment: spec-lite.md S1 line.
- **[DEV-004] AC-1.5 gets its own tests** — Severity: Small
  - Spec said: task 1.1 tests AC-1.1 to AC-1.4.
  - Reality: four AC-1.5 absence tests, needed so ac-trace finds a citation once the story is Completed.
  - Resolution: Auto-amended.
  - Spec amendment: spec-lite.md S1 line.
