# Story 4: Keep CLAUDE.md User-Owned on Uninstall and Reinstall

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** developer who removes or reinstalls Writ in a Claude Code project
**I want to** have only the Writ block taken out of or put back into my `CLAUDE.md`
**So that** my own instructions survive `uninstall.sh`, `/uninstall-writ`, and `/reinstall-writ` byte for byte

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.4

- [ ] Given a `CLAUDE.md` with user content before and after the Writ block (CRLF lines, trailing spaces, a non-ASCII line, blank lines next to both markers, no final newline), when `remove_claude_md_block` runs, then the file equals the original bytes with the start-marker line through the end-marker line removed, with no blank-line trimming and no final-newline change; the file mode is unchanged; and the note is `🗑  Removed: CLAUDE.md Writ block` `[AC-4.1]`
- [ ] Given a `CLAUDE.md` that holds only the Writ block, a `CLAUDE.md` with no markers, a `CLAUDE.md` with two start markers, and no `CLAUDE.md`, when `remove_claude_md_block` runs on each, then it deletes the first (`(empty after Writ block removal)`), leaves the second byte-identical (`✓ CLAUDE.md (no Writ block present)`), returns 13 with a `❌` line on stderr and leaves the third byte-identical, and reports `✓ CLAUDE.md (no file present)` for the fourth `[AC-4.2]`
- [ ] Given temp projects installed with `install.sh --platform claude --no-commit` from a committed temp source copy, when `uninstall.sh --platform claude --no-commit` runs, then a project that started with a hand-written `CLAUDE.md` ends with that file equal to the original plus the one `\n` install's append added, a project that started with no `CLAUDE.md` ends with none, and `uninstall.sh --platform claude --dry-run` on a third project prints `CLAUDE.md Writ block` and changes no file `[AC-4.3]`
- [ ] Given `commands/uninstall-writ.md` and `commands/reinstall-writ.md`, when the test reads them, then `uninstall-writ.md` contains no `rm CLAUDE.md`; `reinstall-writ.md` contains no `cp` of `claude-code/CLAUDE.md` onto `./CLAUDE.md`; the Claude bullets in `/uninstall-writ` Step 3 and `/reinstall-writ` Steps 3–4 say to remove or merge only between `<!-- writ:start -->` and `<!-- writ:end -->`; `/reinstall-writ` Step 4 names `install.sh --platform claude --force`; and both "Do NOT remove" lists name the content outside the markers `[AC-4.4]`

## Implementation Tasks

- [ ] 4.1 Write a failing bundle test `scripts/tests/test_remove_claude_md_block.sh`, following `scripts/tests/test_remove_agents_md_block.sh` (extract the `writ-remove-claude-md-bundled` region, temp workspace per case) but with `cmp`-exact expected files built by `printf`, a mode check through `python3 -c 'import os; print(oct(os.stat(...).st_mode))'` (portable across macOS and Linux `stat`), and the four inputs of AC-4.2 `[AC-4.1, AC-4.2]`
- [ ] 4.2 Write a failing end-to-end test `scripts/tests/test_uninstall_claude_md.sh`: committed temp source copy as in `test_install_update_lean_siblings.sh`, three temp projects (hand-written file, no file, dry run), byte comparison with `cmp`; confirm it fails on today's `uninstall.sh`, which deletes the whole file `[AC-4.3]`
- [ ] 4.3 Write a failing grep test `scripts/tests/test_lifecycle_commands_claude_md.py` (unittest) for the two command docs, using the regex in technical-spec.md → CLAUDE.md Ownership on Uninstall and Reinstall (Story 4) → Lifecycle command docs `[AC-4.4]`
- [ ] 4.4 Add `writ_claude_md_marker_counts` and `remove_claude_md_block` to `scripts/uninstall.sh` inside a new `writ-remove-claude-md-bundled` region: Codex's marker validation and notes, but `head`/`tail` for the kept bytes, `[ -s ]` for emptiness, and `cat "$tmp" >"$file"` to keep the mode (spec.md → D5) `[AC-4.1, AC-4.2]`
- [ ] 4.5 Wire it into `scripts/uninstall.sh`: the Claude branch of the inventory stops adding `CLAUDE.md` to `EXTRA_FILES` and sets `CLAUDE_EXTRA_COUNT`/`CLAUDE_EXTRA_DESC`; the Extras line and `TOTAL` count it; the dry run prints `🗑  CLAUDE.md Writ block`; the remove step calls the function after the `EXTRA_FILES` loop and counts a `🗑` note `[AC-4.2, AC-4.3]`
- [ ] 4.6 Edit `commands/uninstall-writ.md` (Step 3 Claude bullet, "Do NOT remove") and `commands/reinstall-writ.md` (platform table, Step 3 Claude bullet, Step 4 Claude bullet, "Do NOT remove") per the Lifecycle command docs table in technical-spec.md `[AC-4.4]`
- [ ] 4.7 Verify: `uv run --python 3.9 pytest`, then `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, then `bash scripts/eval.sh` outside the sandbox with 0 findings; `test_remove_agents_md_block.sh` must still pass unchanged `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`

## Notes

- **Never run `install.sh`, `update.sh`, or `uninstall.sh` against the Writ repo.** Every test here builds temp projects from a committed temp copy of the tree. Running `uninstall.sh` in this repo would delete symlinked product files.
- **Added 2026-10-20** by the maintainer-approved contract amendment (spec.md → Contract Amendment, rows 1 and 2).
- **Do not change Codex.** `remove_agents_md_block` trims blank lines and normalizes the final newline. Leave it as it is. The Claude function copies its structure, not its rewrite (spec.md → D5).
- **Order inside uninstall.** The function runs after commands, agents, skills, and `EXTRA_FILES` are removed, and before the manifest is removed, like the Codex branch. A malformed-marker return of 13 stops the script under `set -e`, as it does for Codex today. Keep that behavior; do not add new recovery.
- **Depends on Story 2.** Story 2 adds `.claude/system-instructions.md` to the same `EXTRA_FILES` branch and edits the same Claude bullets in both command docs. Start from its result.
- **Adapter is not here.** The adapter's manual install step is Story 3 (AC-3.4). This story touches no adapter file.
- **Mode.** Today `merge_claude_md` writes through `mktemp` + `mv`, which leaves `CLAUDE.md` at mode 0600. That is out of scope. The new function must not add a second case of it.
- **Read first.** technical-spec.md → CLAUDE.md Ownership on Uninstall and Reinstall (Story 4); spec.md → Grounding Notes (the `remove_agents_md_block` bullet) and D5.
- **Test patterns.** `scripts/tests/test_remove_agents_md_block.sh` (bundle extraction), `scripts/tests/test_install_update_lean_siblings.sh` (committed temp source copy).

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Uninstall removes block, Reinstall merges block]
- **Shadow paths:** [Happy, Nil input, Empty input, Upstream error]
- **Business rules:** [User-owned bytes, Uninstall removes only the block, No copy over `CLAUDE.md`, Test isolation]
- **Experience:** [State Catalog]
