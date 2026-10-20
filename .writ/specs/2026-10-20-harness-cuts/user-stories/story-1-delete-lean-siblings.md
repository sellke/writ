# Story 1: Delete the Lean Siblings and Their Install Logic

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer and developer who installs Writ into their projects
**I want to** have the five lean command siblings and the install/update logic that skips them deleted
**So that** Writ stops maintaining a second copy of four commands and the preamble that its own baseline showed no measurable win for, and old installed copies are cleaned up on update

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given the tree after this story, when `ls commands/*.lean.md` runs and the guard grep from spec.md Business Rule 2 runs over `commands README.md scripts/install.sh scripts/update.sh .writ/docs .writ/issues`, then no lean file exists, the grep prints nothing, and neither `scripts/install.sh` nor `scripts/update.sh` defines `is_unshipped_lean_sibling` `[AC-1.1]`
- [ ] Given a temp project and a committed source copy of the working tree, when `install.sh --platform claude --no-commit` runs, first with `--dry-run` and then for real, then no file ending in `.lean.md` is listed, copied into `.claude/commands/`, or recorded in `.claude/.writ-manifest` `[AC-1.2]`
- [ ] Given a temp project whose manifest records unmodified copies of `commands/implement-story.lean.md` and `commands/_preamble.lean.md`, when `update.sh --dry-run` runs and then `update.sh` runs, then the dry run lists both as stale and changes nothing, and the real run removes both, prints `🗑  Removed: commands/<name>` for each, and leaves neither in the manifest `[AC-1.3]`
- [ ] Given the same project with a locally modified `commands/verify-spec.lean.md` recorded in the manifest, when `update.sh` runs twice, then the file is byte-identical after both runs and each run prints `⚠️  Stale (no longer shipped, locally modified — kept): commands/verify-spec.lean.md` (or the exact text the dependency spec's `detect_stale_files` prints) `[AC-1.4]`
- [ ] Given every test and eval check that reads a lean file today (technical-spec.md inventory rows marked Story 1), when `uv run --python 3.9 pytest`, every `scripts/tests/test_*.sh`, and `bash scripts/eval.sh` run, then none reads a lean file, the non-lean assertions in those files still run, and all three pass with 0 eval findings `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write failing tests first. Create `scripts/tests/test_harness_cuts.py` with the Story 1 guard (no `commands/*.lean.md`; `git grep` for the two patterns over the AC-1.1 paths prints nothing) and `scripts/tests/test_install_update_harness_cuts.sh` with the lean upgrade-path cases from technical-spec.md → ## Story 1 Design. Run both on the current tree and record that they fail `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.2 Delete `commands/_preamble.lean.md`, `commands/create-spec.lean.md`, `commands/implement-phase.lean.md`, `commands/implement-story.lean.md`, `commands/verify-spec.lean.md`, and the lean-only tests that read them: `scripts/tests/test_lean_commands.py`, `scripts/tests/test_lean_preamble.py`, `scripts/tests/test_install_update_lean_siblings.sh` `[AC-1.1, AC-1.5]`
- [ ] 1.3 Remove the lean-file reads from the mixed tests (`test_agent_cli_contract.py`, `test_implement_story_default_path.py`, `test_panel_trial_outcome.py`, `test_product_check_direction.py`, `test_quality_gate_wiring.py`, `test_review_panel.py`, `test_jev_setup_hooks.sh`, `test_jev_shadow_hooks.sh`, `test_uat_plan_verification_hooks.sh`) and from `scripts/eval.sh` `check_review_panel` and `check_product_check_direction`, at the lines the inventory lists. Leave every non-lean assertion as it is `[AC-1.5]`
- [ ] 1.4 Remove `is_unshipped_lean_sibling` from `scripts/install.sh` (definition and its calls in the command count and `overlay_scan`) and from `scripts/update.sh` (definition, the `overlay_scan` call, and the lean arm in `detect_stale_files`). Keep the `scripts/` filter-rejected arm and reword the comment above it `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.5 Reword `README.md:63` (drop the lean-flag sentence, keep the measurement sentence), `.writ/docs/agent-cli-contract.md:132` (drop "including `*.lean.md` files"), and `.writ/issues/improvements/2026-10-01-product-lint-misread-as-verify-spec.md:24,30` (drop `verify-spec.lean.md`) `[AC-1.1]`
- [ ] 1.6 Verify install and update: run `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, then `bash scripts/install.sh --dry-run --platform claude --no-commit` from a temp directory and confirm no `.lean.md` line. Never run `install.sh` or `update.sh` against the Writ repo itself; use temp directories `[AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.7 Verify the suite: `uv run --python 3.9 pytest` and `bash scripts/eval.sh` outside the sandbox. Both pass and eval reports 0 findings `[AC-1.1, AC-1.5]`

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

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Fresh install, Update removes an unmodified cut file, Update keeps a modified cut file, Delete a lean file, Remove a lean code path]
- **Shadow paths:** [Install (any platform), Update over an old install, Update with a modified cut file, Guard grep]
- **Business rules:** [Rule 1 (historical records not edited), Rule 2 (guard grep and its exclusions), Rule 4 (dev-only and stale handling), Rule 10 (never run install/update against the Writ repo), Rule 11 (every story leaves the tree green)]
- **Experience:** [State Catalog: Fresh install any platform, Update old unmodified copies present, Update a copy edited locally]
- **Technical:** technical-spec.md → ## Current State → ### Lean reference inventory (rows marked 1); ## Story 1 Design
