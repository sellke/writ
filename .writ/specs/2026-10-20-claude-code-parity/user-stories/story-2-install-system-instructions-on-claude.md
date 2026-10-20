# Story 2: Install the System Instructions and Import Line on Claude Code

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** developer installing or updating Writ in a Claude Code project
**I want to** get `.claude/system-instructions.md` installed, kept current, and imported from my `CLAUDE.md` without Writ touching my own text
**So that** the Prime Directive loads in every session, the `../system-instructions.md` links in installed commands resolve, and my `CLAUDE.md` stays mine

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given a temp project with no `CLAUDE.md` and a committed temp source copy of this tree, when `install.sh --platform claude --no-commit` runs, then `.claude/system-instructions.md` is byte-identical to the source `system-instructions.md` and contains `## Prime Directive`; the manifest records it under the key `system-instructions.md`; the `CLAUDE.md` Writ block contains the line `@.claude/system-instructions.md`; the output shows a `System instructions` step and no `(skipped — no system-instructions for Claude Code)` line; and `--dry-run` into a second temp project prints `system-instructions.md → always updated` and writes no file `[AC-2.1]`
- [ ] Given a `CLAUDE.md` with user content before and after the markers (CRLF lines, trailing spaces, a non-ASCII line, a user `@notes.md` line, no final newline), when install appends the block, update replaces a baseline-matching block with a longer template, and `install.sh --force` replaces a modified block, then the bytes before the `<!-- writ:start -->` line and after the `<!-- writ:end -->` line equal the originals, except the single `\n` an append adds when the file had no final newline `[AC-2.2]`
- [ ] Given an installed project, when `update.sh --platform claude --no-commit` runs against a source whose `system-instructions.md` changed, then an unmodified local copy is updated; a locally modified copy is preserved and listed as `system-instructions.md` among the preserved files; `--force` overwrites it; and a project in the pre-parity state (no local copy, no manifest entry, an old block that matches its `CLAUDE.md.writ-block` baseline) gets `✨ New:       system-instructions.md` and a block that contains the import line `[AC-2.3]`
- [ ] Given a `CLAUDE.md` whose Writ block has local modifications and no `@.claude/system-instructions.md` line, when install or update preserves the block, then `CLAUDE.md` is byte-identical before and after and the run prints a `⚠️` warning that names `@.claude/system-instructions.md` and `--force`; given a preserved block that already contains the line, then no such warning prints `[AC-2.4]`
- [ ] Given an installed Claude Code project, when `uninstall.sh --platform claude --dry-run` and then `uninstall.sh --platform claude --no-commit` run, then the dry run lists `.claude/system-instructions.md` and the real run removes it with the other platform files; and the Claude rows in `commands/update-writ.md`, `commands/reinstall-writ.md`, and `commands/uninstall-writ.md` name `.claude/system-instructions.md` `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write failing shell tests in a new `scripts/tests/test_install_update_claude_parity.sh`, following `scripts/tests/test_install_update_lean_siblings.sh` (committed temp source copy, `WRIT_REPO="$SRC"` for update, `fail` and `hash_file` helpers), with a `python3 -c` prefix/suffix extractor compared by `cmp`, covering the install, update, force, upgrade, and uninstall cases `[AC-2.1, AC-2.2, AC-2.3, AC-2.5]`
- [ ] 2.2 Add failing cases to `scripts/tests/test_merge_claude_md.sh` and `scripts/tests/test_update_claude_md.sh`: preserved block without the import line (warning printed, file unchanged by `cmp`), preserved block with the line (no warning), and CRLF user content outside the markers on the replace path `[AC-2.2, AC-2.4]`
- [ ] 2.3 Edit `scripts/install.sh`: Claude branch of the inventory block, the dry-run platform-files block, and the platform step block (replace the skipped step with the copy); `write_copy_manifest` records `system-instructions.md` for Claude; the scoped git commit adds the file `[AC-2.1]`
- [ ] 2.4 Edit `scripts/update.sh`: run the `SYSINST_ACTION` scan for `cursor` or `claude`, count it as actionable for Claude, copy on `update`/`new` in the Claude apply branch, record it in `write_copy_manifest`, and add it to the scoped git commit `[AC-2.3]`
- [ ] 2.5 Add `writ_block_inner_has_line` inside the `writ-merge-bundled` region of both `install.sh` and `update.sh`, and print the warning from the preserved branch of each `merge_claude_md` in preview and apply; keep both bundles in sync `[AC-2.4]`
- [ ] 2.6 Edit `scripts/uninstall.sh` (Claude branch of the `EXTRA_FILES` block) and the Claude rows and bullets in `commands/update-writ.md` (platform table, Step 3 platform files), `commands/reinstall-writ.md` (platform table, Step 3 removal list, Step 4 copy list), and `commands/uninstall-writ.md` (Step 3 platform files) `[AC-2.5]`
- [ ] 2.7 Verify: `uv run --python 3.9 pytest`, then `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, then `bash scripts/eval.sh` outside the sandbox with 0 findings; also run `install.sh --platform claude --dry-run` in a temp directory and read the output `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

- **Never run `install.sh`, `update.sh`, or `uninstall.sh` against the Writ repo.** The source-repo guard aborts them, and `.claude/` is a symlink tree. Every test creates temp projects and a committed temp source copy.
- **The import line comes from the template.** Story 1 put it in `claude-code/CLAUDE.md`. `merge_claude_md` writes the template's bytes; do not add code that inserts the line.
- **Match Cursor, do not improve it.** Install copies unconditionally ("always updated"). Update uses Cursor's `SYSINST_ACTION` rules, including "no baseline → update". Cursor and Codex behavior must not change (spec scope).
- **Dependency on `2026-10-20-harness-cuts`.** It edits the same scripts first. Locate edits by function or block (`write_copy_manifest`, the platform step block, `merge_claude_md`, the `EXTRA_FILES` block), not by line.
- **Two bundles.** `install.sh` and `update.sh` each carry their own `merge_claude_md` with different variable names (`CLAUDE_MERGE_NOTE` vs `CLAUDE_MD_ACTION`/`CLAUDE_MD_NOTE`). The bundle tests extract the text between the `writ-merge-bundled` markers, so the new helper must sit inside them.
- **Story 4 owns `CLAUDE.md` on uninstall and reinstall.** Today `uninstall.sh --platform claude` deletes the whole `CLAUDE.md`, and `/reinstall-writ` Step 4 copies the template over it. Story 4 (added 2026-10-20) fixes both and edits the same `EXTRA_FILES` block and Claude doc bullets after this story. Here, add only `.claude/system-instructions.md` to those paths.
- **Fixture for the upgrade case.** After a temp install, delete `.claude/system-instructions.md`, drop its manifest line, replace the block inner with a stub old body, and set `CLAUDE.md.writ-block` to that inner's hash. A fixture without the baseline tests nothing.
- **Read first.** technical-spec.md → Install, Update, Uninstall (Story 2), including Preserved-block warning and Byte-identity test method; spec.md → Grounding Notes → Decision D3. The shadow-path rows' Install and Update columns apply here.
- **Test patterns.** `scripts/tests/test_install_update_lean_siblings.sh`, `scripts/tests/test_merge_claude_md.sh`, `scripts/tests/test_update_claude_md.sh`.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Install copies system instructions, Install merges block, Update system instructions, Install or update block, Uninstall system instructions]
- **Shadow paths:** [Happy, Nil input, Empty input, Upstream error]
- **Business rules:** [User-owned bytes, The block comes only from the template, System instructions copy, Update decision, Uninstall, Test isolation]
- **Experience:** [State Catalog, Interaction Patterns]
