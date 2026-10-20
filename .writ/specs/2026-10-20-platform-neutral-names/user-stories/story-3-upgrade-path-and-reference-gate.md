# Story 3: Upgrade-Path Test, Reference Gate, and Issue Resolutions

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** Writ user upgrading a project installed before the rename, and as the maintainer
**I want to** have `update.sh` swap `design.md` for `writ-design.md` without losing my edits, and have a test that fails on any leftover Writ `/design` reference
**So that** upgrading never leaves me with a dead `/design` pointer or silently deletes my changes, and the rename cannot regress

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given a temp project and the committed source copy `SRC_NEW`, when `install.sh --platform <p> --no-commit` runs for each of `cursor`, `claude`, and `codex`, then `<platform_dir>/commands/writ-design.md` exists, `<platform_dir>/commands/design.md` does not, and the install manifest records `commands/writ-design.md` and not `commands/design.md` `[AC-3.1]`
- [ ] Given a project installed from `SRC_OLD` (the last release, with `commands/design.md`) on each of the three platforms, with `design.md` unmodified, when `update.sh` runs from `SRC_NEW`, then the dry run lists `🗑  commands/design.md` and removes nothing, and the real run prints `🗑  Removed: commands/design.md`, removes the file, installs `writ-design.md`, and drops `commands/design.md` from the manifest `[AC-3.2]`
- [ ] Given a `claude` project installed from `SRC_OLD` with a locally modified `.claude/commands/design.md`, when `update.sh` runs from `SRC_NEW` twice, then the file is byte-identical after both runs and each run prints `⚠️  Stale (no longer shipped, locally modified — kept): commands/design.md` `[AC-3.3]`
- [ ] Given the repo, when `writ_design_refs(REPO)` runs, then it returns no hits; and given the fixture repo in technical-spec.md → ## Reference Gate → Tests, it reports exactly the four planted lines, ignores the rest, and fails (not passes) when `git grep` errors `[AC-3.4]`
- [ ] Given the two origin issues and spec.md's Upgrade Note, when the story is done, then each issue ends with a `## Resolution` section naming this spec and the fix, its `spec_ref` points at this spec, the Upgrade Note's removal and warning lines match what `update.sh` printed in AC-3.2 and AC-3.3, and `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` (0 findings) pass `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write `scripts/tests/test_install_update_writ_design.sh` following `scripts/tests/test_install_update_dev_scripts.sh`: build `SRC_NEW` and `SRC_OLD` as technical-spec.md → ## Upgrade Path Test describes, then the fresh-install, unmodified-upgrade, and modified-upgrade cases. Read `detect_stale_files` and the removal block in `scripts/update.sh` first and assert the exact lines it prints. Label each block with its AC ID `[AC-3.1, AC-3.2, AC-3.3]`
- [ ] 3.2 Add `writ_design_refs(root)` and the tests `test_no_writ_design_reference`, `test_gate_fixture`, and `test_gate_git_error` to `scripts/tests/test_platform_neutral_names.py`, reusing `RECORD_PREFIXES` and `DATED_SNAPSHOTS` from Story 1 `[AC-3.4]`
- [ ] 3.3 Run both tests. Fix every reference the gate names in a shipped path. `RECORD_PREFIXES` already lists `.writ/specs/2026-10-20-claude-code-parity/`. If the gate names another in-flight `.writ/specs/<folder>/`, add that folder to `RECORD_PREFIXES` with a one-line reason and log it in the drift log. Prove each test can fail: point `SRC_NEW` at `SRC_OLD` in a scratch copy of the bash test and confirm the fresh-install case fails `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [ ] 3.4 Append `## Resolution` to `.writ/issues/bugs/2026-10-19-prototype-visual-preview-cursor-only.md` (the `canvas-preview` capability and the four adapter rows) and `.writ/issues/bugs/2026-10-19-design-command-name-collision.md` (renamed to `/writ-design`; how old installs upgrade; native `/design` behavior not verified in a live Claude Code session). Set each issue's `spec_ref` to `.writ/specs/2026-10-20-platform-neutral-names/` `[AC-3.5]`
- [ ] 3.5 Compare spec.md → ## Upgrade Note with the output the bash test observed. Correct any line that does not match, and record the correction in the drift log `[AC-3.2, AC-3.3, AC-3.5]`
- [ ] 3.6 Verify the regression surface: `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` outside the sandbox, with 0 findings `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

- **AC-3.3 needs another spec.** Today `update.sh` warns about a kept, modified stale file only under `scripts/`. A modified `commands/design.md` is kept silently on the first run and deleted on the second (`.writ/issues/bugs/2026-10-12-update-deletes-modified-stale-files.md`). `2026-10-20-ci-and-update-integrity` fixes that for every category and keeps the warning text as it is today. If it has not landed, AC-3.3 fails. Stop and report blocked. Do not patch `update.sh` in this story.
- **Second update takes the early-exit path.** Run 2 has nothing else to do and leaves through "Already up to date". The ci-and-update-integrity spec requires the warning on that path too, so AC-3.3 asserts it on run 2. Run 1 rewrites the manifest because it also installs `writ-design.md`.
- **Never run `install.sh` or `update.sh` against the Writ repo itself.** The repo's `.claude/` and `.cursor/` are symlinks into the product source (CLAUDE.md). Every install and update in this story runs in a temp directory from a committed copy of the working tree. `update.sh` clones `WRIT_REPO`, so the copy must be committed.
- **OpenClaw has no install path.** `install.sh` accepts `cursor`, `claude`, and `codex` only. "Each platform" in AC-3.1 and AC-3.2 means those three.
- **The bash test runs `git init`.** Run it outside any sandbox, like `eval.sh`.
- **Record list stays narrow.** Never add a shipped path to `RECORD_PREFIXES`. The three dated snapshots are the only `.writ/docs/` or `.writ/explanations/` exceptions.
- **Parse `git grep` with `--null`.** One snapshot path has a space in it. Treat exit 1 as no matches, and exit 2 or higher as an error.
- **The Resolution must not overclaim.** Nobody has verified in a live Claude Code session (2.1.233 or later) whether a project command shadows the native `/design`. The rename removes the collision either way. Say that.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Fresh install, Update unmodified `design.md` (both rows), Update modified `design.md`, Rename sweep, Gate run] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Upgrade an old install, Reference gate] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Rule 11 (upgrade via stale detection only), Rule 12 (gate record list), Rule 13 (test isolation), Rule 14 (runtime floor)] — spec.md → ## Business Rules (Expanded)
- **Experience:** [State Catalog rows "Fresh install", "Update, old `design.md` unmodified", "Update, old `design.md` locally modified", "Maintainer leaves a Writ `/design` reference"] — spec.md → ## Experience Design → ### State Catalog
- **Technical:** technical-spec.md → ## Reference Gate (Story 3), ## Upgrade Path Test (Story 3), ## Interaction Edge Cases; spec.md → ## Upgrade Note
- **Test pattern:** `scripts/tests/test_install_update_dev_scripts.sh` (tar source copy, `commit_src`, `fail`, `hash_file`, two-run check)
