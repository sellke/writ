# Claude Code Parity (Lite)

> Source: .writ/specs/2026-10-20-claude-code-parity/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Claude Code installs get `.claude/system-instructions.md` and a generated `CLAUDE.md` Writ block that imports it; uninstall and reinstall touch only that block; the adapter stops documenting things that don't exist. (Amended 2026-10-20: Story 4, AC-3.5.)

**Implementation Approach:**
- `scripts/gen-claude-md.py` (stdlib, 3.9, dev-only) renders `claude-code/CLAUDE.md`: commands from `.writ/manifest.yaml`, agents from `claude-code/agents/*.md` frontmatter (D1), a pipeline constant, and the line `@.claude/system-instructions.md` outside any code span. `--check` reports `missing`/`extra`/`stale`.
- Check shape: line 1 `pass`/`fail`/`unverifiable`, `reason:` lines, `gen-claude-md:` summary last; exit 0/1, 2 on usage.
- Eval check `claude-md` mirrors `check_codex_tomls`; one finding per reason.
- Install copies `system-instructions.md` into `.claude/` like Cursor; update reuses Cursor's `SYSINST_ACTION` three-way; uninstall adds it to `EXTRA_FILES`.
- Uninstall: new `remove_claude_md_block` keeps every byte outside the block (`head`/`tail`, no trimming, unlike Codex; D5); deletes `CLAUDE.md` only at zero bytes. `/reinstall-writ` and the adapter's manual step merge between markers.
- `merge_claude_md` (both bundles) still writes only template bytes; its preserved branch warns when the block lacks the import line (D3).
- Edit by function or block; `2026-10-20-harness-cuts` edits the same scripts first.

**Files in Scope:**
- `scripts/gen-claude-md.py`, `claude-code/CLAUDE.md`, `scripts/eval.sh` (S1)
- `is_shippable_script` in `scripts/install.sh`, `update.sh`, `unlink.sh`; `.writ/docs/agent-cli-contract.md`; `commands/update-writ.md` (S1)
- S1 as built (DEV-001–004): `claude-md` follows `claude-agents` in `CHECKS`; the agent list comes from `claude-code/agents/*.md` (eight today); the CLI contract note keeps "Six dev-only scripts" and adds a sentence for `gen-claude-md.py`.
- `scripts/install.sh`, `update.sh`, `uninstall.sh`; Claude rows of `update-writ.md`, `reinstall-writ.md`, `uninstall-writ.md` (S2)
- `adapters/claude-code.md`: claims, install section, `SubagentStop` hook (D6), seven agents (S3)
- S3 as built (DEV-005–008): eight agents read from frontmatter; manual Step 1 says a manual install has no manifest baseline, so later runs keep a differing block, and `--force` also overwrites other differing Writ files; Gotcha 1 names both stale-worktree causes; the no-copy regex also catches bare `CLAUDE.md`.
- `scripts/uninstall.sh` block removal; Claude bullets of `uninstall-writ.md`, `reinstall-writ.md` (S4)
- Tests: `test_gen_claude_md.py`, `test_eval_claude_md.sh`, `test_gen_claude_md_not_shipped.sh`, `test_install_update_claude_parity.sh`, `test_claude_code_adapter_claims.py`, `test_remove_claude_md_block.sh`, `test_uninstall_claude_md.sh`, `test_lifecycle_commands_claude_md.py`; new cases in `test_merge_claude_md.sh`, `test_update_claude_md.sh`

**Error Handling:**
- Manifest missing → `unverifiable` (eval still files a finding); `@` outside backticks in a purpose → `fail` (`import-token`).
- Modified local system instructions → preserved; modified block → preserved + warning.
- Uninstall, malformed markers → return 13, `CLAUDE.md` untouched (as Codex).

**Integration Points:**
- CI runs `bash scripts/eval.sh` (do not edit `.github/workflows/eval.yml`). Pinned adapter text (lanes, quarantine, recommendation semantics, review panel, `/goal`) must survive.

See technical-spec.md → Generator, Install/Update/Uninstall, CLAUDE.md Ownership (Story 4), Adapter Corrections.

---

## For Review Agents

**Acceptance Criteria:**
1. Generated template: 32 command rows, 7 agents, pipeline, import line outside code; deterministic, LF, one final newline `[AC-1.1]`
2. `--check` passes on the committed file; a removed row gives exactly one `missing` reason and exit 1 `[AC-1.2]`
3. Error paths: unverifiable, usage (exit 2), named `fail` reasons; no write on failure `[AC-1.3]`
4. Generator never ships; filter bodies identical in three scripts; docs name it dev-only `[AC-1.4]`
5. Eval `claude-md` passes fresh, fails with one finding naming the command and remedy; in `CHECKS` `[AC-1.5]`
6. Temp install has `.claude/system-instructions.md` with `## Prime Directive` and the import line in the block `[AC-2.1]`
7. Bytes outside the markers identical across install, update, `--force` `[AC-2.2]`
8. Update: unmodified updated, modified preserved, `--force` overwrites, pre-parity install upgraded `[AC-2.3]`
9. Preserved block without the import line: file unchanged, warning printed `[AC-2.4]`
10. Uninstall removes the file; lifecycle command docs name it `[AC-2.5]`
11. Adapter: no `--all`, no agent teams, no merge-back claims `[AC-3.1]`
12. Worktree text matches the docs and links the skill; gotchas and parallel text corrected `[AC-3.2, AC-3.3]`
13. Installation section covers the copy, the import, and a marker merge instead of `cp` `[AC-3.4]`
14. No `SubagentCompleted` or `$WORKTREE`; `SubagentStop` example; all seven agents named `[AC-3.5]`
15. Uninstall removes only the block, byte-exact; block-only file deleted; error cases untouched `[AC-4.1, AC-4.2]`
16. Install → uninstall round trip returns the user's file; dry run changes nothing `[AC-4.3]`
17. `/uninstall-writ` and `/reinstall-writ` never delete or overwrite `CLAUDE.md` `[AC-4.4]`

**Business Rules:**
- `CLAUDE.md` is user-owned on install, update, uninstall, reinstall: only an append's single `\n` may change bytes outside the markers.
- The import line reaches a project only through the template.
- Cursor and Codex behavior unchanged. No test runs lifecycle scripts in the Writ repo.

**Experience Design:**
- Entry: `install.sh --platform claude`, or a maintainer edits the manifest.
- Happy path: block lists every command and imports the system instructions.
- Moment of truth: forgetting to regenerate fails eval with the command and remedy.
- Feedback: existing `✨`/`🔄`/`⚡` lines; one `⚠️` for a block missing the import.
- Error: preserved files are listed; nothing user-owned is rewritten.

---

## For Testing Agents

**Success Criteria:**
1. `uv run --python 3.9 pytest`, the bash test loop, and `bash scripts/eval.sh` (0 findings) pass.
2. `python3 scripts/gen-claude-md.py --check` prints `pass`.
3. The eval mutation test fails the check when a row is deleted or a manifest command added.

**Shadow Paths to Verify:**
- **Happy path:** fresh temp install → block created with import, file copied.
- **Nil input:** no `CLAUDE.md` → created; no manifest → `unverifiable`.
- **Empty input:** empty `CLAUDE.md` → block with no leading blank line.
- **Upstream error:** template missing → return 12; source lacks `system-instructions.md` → install aborts.

**Edge Cases:**
- CRLF user lines, trailing spaces, non-ASCII, a user `@notes.md` line, no final newline → preserved.
- Pre-parity install (no file, old block at baseline) → file added, block updated.
- Blank lines next to the block on uninstall → kept; whitespace-only remainder → file kept.
- Preserved block that already has the import → no warning.
- `|` in a purpose → escaped; `@` in a purpose → `fail`.

**Test Strategy:**
- Temp projects and a committed temp source copy; `WRIT_REPO="$SRC"` for update.
- Byte identity by a `python3 -c` prefix/suffix split and `cmp`.
- Eval mutation in temp roots, like `test_eval_codex_tomls.sh`.
