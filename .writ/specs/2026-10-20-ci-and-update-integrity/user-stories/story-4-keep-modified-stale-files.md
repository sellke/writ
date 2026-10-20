# Story 4: Keep Modified Stale Files in Every Category

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 3

## User Story

**As a** user of a project with Writ installed
**I want to** have `update.sh` keep, and warn about, any file I edited that upstream stopped shipping, on every run, until I delete it
**So that** my edits are never lost on the second update, whatever folder the file lives in

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [ ] Given a temp Claude Code project installed from a source that ships `commands/zz-kept.md`, `claude-code/agents/zz-kept.md`, `skills/zz-kept/SKILL.md`, `.writ/docs/zz-kept.md`, and `scripts/zz_kept.py`, each then edited locally, and a later source that drops all five, when `update.sh` runs three times and each run rewrites the manifest, then all five local files exist and are byte-identical after every run `[AC-4.1]`
- [ ] Given the same project, when each of the three updates and a `--dry-run` runs, then each output contains `⚠️  Stale (no longer shipped, locally modified — kept): <path>` for all five manifest paths (`commands/zz-kept.md`, `agents/zz-kept.md`, `skills/zz-kept/SKILL.md`, `.writ/docs/zz-kept.md`, `scripts/zz_kept.py`), and the dry run leaves the manifest byte-identical `[AC-4.2]`
- [ ] Given the manifest after each run, when it is read, then each kept path has exactly one line carrying the hash recorded at install, not the local hash; an unmodified `commands/zz-clean.md` dropped by the same source is removed on run 1 with `🗑  Removed: commands/zz-clean.md` and leaves the manifest; and after the user deletes one kept file, the next run prints no warning for it and drops its line `[AC-4.3]`
- [ ] Given `scripts/tests/test_update_kept_stale_files.sh` and the pre-fix `update.sh`, when the test runs, then it fails, naming a kept file the update removed; after the fix it passes, and `scripts/tests/test_install_update_dev_scripts.sh` still passes unchanged `[AC-4.4]`
- [ ] Given `commands/update-writ.md` and the issue `.writ/issues/bugs/2026-10-12-update-deletes-modified-stale-files.md`, when the story closes, then the frontmatter `outcome` (line 5) and exit criterion (line 10), Steps 3, 6, and 7 (lines 124, 194, 199-223, with `# baselines: shipped` in the Step 7 template), and Completion (lines 286-288) all say three things: only shipped paths get baselines, a kept customized or stale file keeps its previous baseline, and a modified stale file is flagged on every run. The issue ends with a `## Resolution` section naming the fix and the test `[AC-4.5]`

## Implementation Tasks

- [ ] 4.1 Write a new `scripts/tests/test_update_kept_stale_files.sh`, reusing the committed-source-copy, `plant`/`check_update`, `fail`, and `hash_file` patterns of `scripts/tests/test_install_update_dev_scripts.sh` (lines 19-39, 61-72, 116-158). Cover the five categories, three manifest-rewriting runs, the dry run, the unmodified removal, and delete-then-run. Run it against the unchanged `scripts/update.sh`, confirm it fails, and save the failing line for What Was Built `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`
- [ ] 4.2 In `detect_stale_files` (`scripts/update.sh:821-877`), remove the `category = scripts` condition from the modified branch (`868-874`), so every category prints the existing warning text and appends `<baseline>  <path>` to `STALE_KEPT_ENTRIES` `[AC-4.2]`
- [ ] 4.3 In `write_copy_manifest`, confirm that each `STALE_KEPT_ENTRIES` path is written exactly once with its old baseline. After Story 3 no kept path is in the shipped set, so the "already recorded" check at the end of the function is only a duplicate guard. Keep it or simplify it, but do not drop the entry `[AC-4.1, AC-4.3]`
- [ ] 4.4 Edit `commands/update-writ.md` so the frontmatter `outcome` and exit criterion, Steps 3, 6, and 7, and Completion match AC-4.5. Add the `# baselines: shipped` header line to the Step 7 manifest template. Change no other section `[AC-4.5]`
- [ ] 4.5 Verify the fix: `bash scripts/tests/test_update_kept_stale_files.sh` and `bash scripts/tests/test_install_update_dev_scripts.sh` pass. Re-prove the pre-fix failure by copying the new test into a temp `git archive <pre-fix commit>` extract and running it there; this leaves git state unchanged `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`
- [ ] 4.6 Verify the regression surface: `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` (no `FAIL` lines), and `bash scripts/eval.sh` outside any sandbox; all pass `[AC-4.4, AC-4.5]`
- [ ] 4.7 Append `## Resolution` to `.writ/issues/bugs/2026-10-12-update-deletes-modified-stale-files.md`, naming the shipped-only recording (Story 3), the `detect_stale_files` change, and `scripts/tests/test_update_kept_stale_files.sh` `[AC-4.5]`

## Notes

- **Run 1 must rewrite the manifest.** `update.sh` exits "Already up to date" before `write_copy_manifest` (`scripts/update.sh:1024-1038`) when nothing is actionable. If a kept file is the only change, the pre-fix script keeps it, and the test proves nothing. `commands/zz-clean.md` (unmodified, dropped) forces a rewrite on run 1. An unrelated upstream edit to a locally unmodified shipped command forces runs 2 and 3.
- **The shippable-named script case.** Before the fix, `scripts/zz_kept.py` gets a warning on run 1 and is removed on run 2, because the pre-fix `append_manifest_shippable_scripts` re-records it. The fixture covers this on purpose.
- **Paths.** The agent's upstream path is `claude-code/agents/zz-kept.md` (`AGENTS_SRC`), with manifest path `agents/zz-kept.md`. The skill's local path is `.claude/skills/zz-kept/SKILL.md`, with manifest path `skills/zz-kept/SKILL.md`. Scripts and `.writ/docs` resolve at the project root.
- **Keep the warning text.** `test_install_update_dev_scripts.sh:100` and `2026-10-20-platform-neutral-names` match `⚠️  Stale (no longer shipped, locally modified — kept): <path>` byte for byte.
- **Wording now covers line-level detail.** Line numbers are from 2026-10-20. Re-read the file before editing. The old Completion line says the manifest "re-baselines, so the next update compares against what is on disk". Under the fix, a kept customized file keeps its previous baseline, so the next update asks again when upstream differs.
- **Never run `install.sh` or `update.sh` against the Writ repo.** It is symlinked into `.claude/` and `.cursor/`. Run everything in temp directories. The test does `git init`, so run it outside any sandbox.
- **Other Phase 13 work touches `update.sh`.** The Cuts feature removes `is_unshipped_lean_sibling`, which `detect_stale_files` calls at `859-860`. Run `git diff scripts/update.sh` before editing, and change only the targeted lines.
- **Citations.** Name this spec (`2026-10-20-ci-and-update-integrity`) in the comment that carries `AC-4.n` tokens.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Rewrite manifest (kept stale path), Stale removal (user deleted the kept file), Update early exit (only kept stale files differ)] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Kept stale file across updates] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Rule 4 (stale definition), Rule 5 (unmodified removed), Rule 6 (modified kept in every category), Rule 7 (dry run, `--force`), Rule 13 (temp dirs only)] — spec.md → ## Business Rules (Expanded)
- **Experience:** [State Catalog rows "Update, modified stale file", "Update, second and later runs", "User deletes a kept stale file"] — spec.md → ## Experience Design → ### State Catalog
- **Technical:** technical-spec.md → ## Story 4 Design: Kept stale files
