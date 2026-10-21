# Story 4: Keep CLAUDE.md User-Owned on Uninstall and Reinstall

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** developer who removes or reinstalls Writ in a Claude Code project
**I want to** have only the Writ block taken out of or put back into my `CLAUDE.md`
**So that** my own instructions survive `uninstall.sh`, `/uninstall-writ`, and `/reinstall-writ` byte for byte

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.4

- [x] Given a `CLAUDE.md` with user content before and after the Writ block (CRLF lines, trailing spaces, a non-ASCII line, blank lines next to both markers, no final newline), when `remove_claude_md_block` runs, then the file equals the original bytes with the start-marker line through the end-marker line removed, with no blank-line trimming and no final-newline change; the file mode is unchanged; and the note is `🗑  Removed: CLAUDE.md Writ block` `[AC-4.1]`
- [x] Given a `CLAUDE.md` that holds only the Writ block, a `CLAUDE.md` with no markers, a `CLAUDE.md` with two start markers, and no `CLAUDE.md`, when `remove_claude_md_block` runs on each, then it deletes the first (`(empty after Writ block removal)`), leaves the second byte-identical (`✓ CLAUDE.md (no Writ block present)`), returns 13 with a `❌` line on stderr and leaves the third byte-identical, and reports `✓ CLAUDE.md (no file present)` for the fourth `[AC-4.2]`
- [x] Given temp projects installed with `install.sh --platform claude --no-commit` from a committed temp source copy, when `uninstall.sh --platform claude --no-commit` runs, then a project that started with a hand-written `CLAUDE.md` ends with that file equal to the original plus the one `\n` install's append added, a project that started with no `CLAUDE.md` ends with none, and `uninstall.sh --platform claude --dry-run` on a third project prints `CLAUDE.md Writ block` and changes no file `[AC-4.3]`
- [x] Given `commands/uninstall-writ.md` and `commands/reinstall-writ.md`, when the test reads them, then `uninstall-writ.md` contains no `rm CLAUDE.md`; `reinstall-writ.md` contains no `cp` of `claude-code/CLAUDE.md` onto `./CLAUDE.md`; the Claude bullets in `/uninstall-writ` Step 3 and `/reinstall-writ` Steps 3–4 say to remove or merge only between `<!-- writ:start -->` and `<!-- writ:end -->`; `/reinstall-writ` Step 4 names `install.sh --platform claude --force`; and both "Do NOT remove" lists name the content outside the markers `[AC-4.4]`

## Implementation Tasks

- [x] 4.1 Write a failing bundle test `scripts/tests/test_remove_claude_md_block.sh`, following `scripts/tests/test_remove_agents_md_block.sh` (extract the `writ-remove-claude-md-bundled` region, temp workspace per case) but with `cmp`-exact expected files built by `printf`, a mode check through `python3 -c 'import os; print(oct(os.stat(...).st_mode))'` (portable across macOS and Linux `stat`), and the four inputs of AC-4.2 `[AC-4.1, AC-4.2]`
- [x] 4.2 Write a failing end-to-end test `scripts/tests/test_uninstall_claude_md.sh`: committed temp source copy as in `test_install_update_lean_siblings.sh`, three temp projects (hand-written file, no file, dry run), byte comparison with `cmp`; confirm it fails on today's `uninstall.sh`, which deletes the whole file `[AC-4.3]`
- [x] 4.3 Write a failing grep test `scripts/tests/test_lifecycle_commands_claude_md.py` (unittest) for the two command docs, using the regex in technical-spec.md → CLAUDE.md Ownership on Uninstall and Reinstall (Story 4) → Lifecycle command docs `[AC-4.4]`
- [x] 4.4 Add `writ_claude_md_marker_counts` and `remove_claude_md_block` to `scripts/uninstall.sh` inside a new `writ-remove-claude-md-bundled` region: Codex's marker validation and notes, but `head`/`tail` for the kept bytes, `[ -s ]` for emptiness, and `cat "$tmp" >"$file"` to keep the mode (spec.md → D5) `[AC-4.1, AC-4.2]`
- [x] 4.5 Wire it into `scripts/uninstall.sh`: the Claude branch of the inventory stops adding `CLAUDE.md` to `EXTRA_FILES` and sets `CLAUDE_EXTRA_COUNT`/`CLAUDE_EXTRA_DESC`; the Extras line and `TOTAL` count it; the dry run prints `🗑  CLAUDE.md Writ block`; the remove step calls the function after the `EXTRA_FILES` loop and counts a `🗑` note `[AC-4.2, AC-4.3]`
- [x] 4.6 Edit `commands/uninstall-writ.md` (Step 3 Claude bullet, "Do NOT remove") and `commands/reinstall-writ.md` (platform table, Step 3 Claude bullet, Step 4 Claude bullet, "Do NOT remove") per the Lifecycle command docs table in technical-spec.md `[AC-4.4]`
- [x] 4.7 Verify: `uv run --python 3.9 pytest`, then `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, then `bash scripts/eval.sh` outside the sandbox with 0 findings; `test_remove_agents_md_block.sh` must still pass unchanged `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Uninstall removes block, Reinstall merges block]
- **Shadow paths:** [Happy, Nil input, Empty input, Upstream error]
- **Business rules:** [User-owned bytes, Uninstall removes only the block, No copy over `CLAUDE.md`, Test isolation]
- **Experience:** [State Catalog]

## What Was Built

**Implementation Date:** 2026-10-21

### Files Created

- **`scripts/tests/test_remove_claude_md_block.sh`** — loads only the `writ-remove-claude-md-bundled` region. `cmp`-exact expected files built by `printf`; mode checked through `python3 os.stat`. The AC-4.1 fixture has CRLF lines, trailing spaces, non-ASCII text, blank lines next to both markers, a CRLF end marker, no final newline, and mode 0640. Covers the four AC-4.2 inputs plus a whitespace-only remainder, a block on line 1, a block last with no final newline, end before start, start without end, the default argument, and no leftover temp file.
- **`scripts/tests/test_uninstall_claude_md.sh`** — committed temp source copy (Story 2's pattern). Project A: a hand-written `CLAUDE.md` ends as the original plus one `\n`, same mode. Project B: no `CLAUDE.md` before install, none after uninstall. Project C: the dry run changes nothing (full tree snapshot with modes and hashes) and prints `CLAUDE.md Writ block`. Project D: malformed markers stop uninstall with exit 13 and a `❌` line, file untouched.
- **`scripts/tests/test_lifecycle_commands_claude_md.py`** — 10 unittest cases: no `rm` of `CLAUDE.md` and no `cp` of the template onto `CLAUDE.md` in either doc; the Claude bullets name both markers; uninstall names `uninstall.sh --platform claude`; reinstall Step 4 names `install.sh --platform claude --force`; both "Do NOT remove" lists name content outside the markers; the regexes match the old doc lines.

### Files Modified

- **`scripts/uninstall.sh`** — new `writ-remove-claude-md-bundled` region with `writ_claude_md_marker_counts` and `remove_claude_md_block` (D5: `head`/`tail` with a line-1 guard, `[ -s ]` for emptiness, `cat "$tmp" >"$file"` to keep the mode, return 13 with `❌` on stderr for malformed markers). The Claude inventory no longer puts `CLAUDE.md` in `EXTRA_FILES`; it sets `CLAUDE_EXTRA_COUNT` and `CLAUDE_EXTRA_DESC`, which the Extras line and `TOTAL` include. The dry run prints `🗑  CLAUDE.md Writ block`. The remove step calls the function after the `EXTRA_FILES` loop and before the manifest removal, and counts a `🗑` note. Cursor and Codex output is unchanged.
- **`commands/uninstall-writ.md`** — Step 3 Claude bullet removes `.claude/system-instructions.md` and only the marker-bounded block, deleting `CLAUDE.md` only if nothing is left; "Do NOT remove" names Claude content outside the markers.
- **`commands/reinstall-writ.md`** — platform table names the `CLAUDE.md` Writ block; Step 3 leaves `CLAUDE.md` in place; Step 4 merges between the markers the way `install.sh --platform claude --force` does, then copies `system-instructions.md`; "Do NOT remove" names Claude content outside the markers.

### Implementation Decisions

1. **The region carries its own marker-count helper** so the bundle test can load it alone, as D5 requires.
2. **Codex is untouched.** `remove_agents_md_block` and its test are unchanged.

### Test Results

**Verification:** test-first, then full suites.

- Red: the bundle test failed with "uninstall.sh has no writ-remove-claude-md-bundled region"; on today's `uninstall.sh` the end-to-end projects A–D each failed (A: the whole file was deleted); the docs test gave 8 failed, 2 passed.
- Mutations: the coder's six (`mv` instead of `cat`, no `rm "$tmp"`, blank-line trim, whitespace counted as empty, count dropped from `TOTAL`, `|| true` on the call) and the evaluator's (head and tail off-by-one, return 1 instead of 13, `❌` on stdout) were each caught. Two evaluator mutants survived as equivalent (the line-1 guard on macOS, a redundant order test).
- Evaluator probes: Cursor and Codex uninstall give the same dry-run output, run output, and tree as HEAD's script; the git-commit path records the block removal or the deletion.
- Orchestrator run: `test_remove_claude_md_block.sh`, `test_uninstall_claude_md.sh`, `test_remove_agents_md_block.sh`, `test_install_update_claude_parity.sh` → exit 0; `test_lifecycle_commands_claude_md.py` → 10 passed; eval `referenced-paths` and `broken-refs` → Findings 0.
- Full suites (coder and evaluator): pytest 3.9 → 2682 passed, 2 skipped; bash loop → 44 run, 0 failed; `bash scripts/eval.sh` → Findings 0; `ac-trace.py check` → no findings.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-011, DEV-012, DEV-013)
- **Security:** Clean
- **Boundary Compliance:** all edits in owned files; Gate 2.5 found 0 crossings
- gate3-route: evaluator-agent. review-panel: skipped — platform cannot spawn other vendors. arch-lint: none — see .writ/docs/architecture-lint.md.
- Gate 0 arch-check: pass (rederived proceed). Gate 2: `bash -n` and `py_compile` clean; no linter configured. Gate 3.5 drift-format: pass. Gate 3 review-override and Gate 4 authenticity: `test_imports_no_source` on the two bash tests (the known shell-test false positive, `.writ/issues/improvements/2026-10-12-test-integrity-shell-tests.md`) and on the docs test, which reads markdown deliverables as text; carried on the red-phase and mutation evidence above, not DEGRADED. Gate 4 coverage: unverifiable (no report). Gate 4.5: app-verify unverifiable (no recipe). Gate 5: docs-check unverifiable (no public exports).
- Evaluator residual (Minor taste, not fixed): `commands/uninstall-writ.md` frontmatter `exit_criteria` and the Step 2 confirm prompt name only `AGENTS.md` content outside the markers; `uninstall.sh --help` does not say `CLAUDE.md` is edited; a read-only `CLAUDE.md` stops uninstall with exit 1 after commands, agents, and skills are removed, where the old `rm -f` succeeded; "only if nothing is left" in the doc means zero bytes in the script.

### Deviations from Spec

- **[DEV-011] The reinstall doc names `.claude/system-instructions.md`** — Severity: Small. Resolution: Auto-amended (spec-lite S4 line).
- **[DEV-012] Reinstall Step 4 spells out the merge in full** — Severity: Small. Resolution: Auto-amended.
- **[DEV-013] Story 4 tests go beyond the listed cases** — Severity: Small. Resolution: Auto-amended.
