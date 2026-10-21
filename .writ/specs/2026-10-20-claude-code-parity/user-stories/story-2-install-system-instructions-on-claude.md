# Story 2: Install the System Instructions and Import Line on Claude Code

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** developer installing or updating Writ in a Claude Code project
**I want to** get `.claude/system-instructions.md` installed, kept current, and imported from my `CLAUDE.md` without Writ touching my own text
**So that** the Prime Directive loads in every session, the `../system-instructions.md` links in installed commands resolve, and my `CLAUDE.md` stays mine

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given a temp project with no `CLAUDE.md` and a committed temp source copy of this tree, when `install.sh --platform claude --no-commit` runs, then `.claude/system-instructions.md` is byte-identical to the source `system-instructions.md` and contains `## Prime Directive`; the manifest records it under the key `system-instructions.md`; the `CLAUDE.md` Writ block contains the line `@.claude/system-instructions.md`; the output shows a `System instructions` step and no `(skipped — no system-instructions for Claude Code)` line; and `--dry-run` into a second temp project prints `system-instructions.md → always updated` and writes no file `[AC-2.1]`
- [x] Given a `CLAUDE.md` with user content before and after the markers (CRLF lines, trailing spaces, a non-ASCII line, a user `@notes.md` line, no final newline), when install appends the block, update replaces a baseline-matching block with a longer template, and `install.sh --force` replaces a modified block, then the bytes before the `<!-- writ:start -->` line and after the `<!-- writ:end -->` line equal the originals, except the single `\n` an append adds when the file had no final newline `[AC-2.2]`
- [x] Given an installed project, when `update.sh --platform claude --no-commit` runs against a source whose `system-instructions.md` changed, then an unmodified local copy is updated; a locally modified copy is preserved and listed as `system-instructions.md` among the preserved files; `--force` overwrites it; and a project in the pre-parity state (no local copy, no manifest entry, an old block that matches its `CLAUDE.md.writ-block` baseline) gets `✨ New:       system-instructions.md` and a block that contains the import line `[AC-2.3]`
- [x] Given a `CLAUDE.md` whose Writ block has local modifications and no `@.claude/system-instructions.md` line, when install or update preserves the block, then `CLAUDE.md` is byte-identical before and after and the run prints a `⚠️` warning that names `@.claude/system-instructions.md` and `--force`; given a preserved block that already contains the line, then no such warning prints `[AC-2.4]`
- [x] Given an installed Claude Code project, when `uninstall.sh --platform claude --dry-run` and then `uninstall.sh --platform claude --no-commit` run, then the dry run lists `.claude/system-instructions.md` and the real run removes it with the other platform files; and the Claude rows in `commands/update-writ.md`, `commands/reinstall-writ.md`, and `commands/uninstall-writ.md` name `.claude/system-instructions.md` `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Write failing shell tests in a new `scripts/tests/test_install_update_claude_parity.sh`, following `scripts/tests/test_install_update_lean_siblings.sh` (committed temp source copy, `WRIT_REPO="$SRC"` for update, `fail` and `hash_file` helpers), with a `python3 -c` prefix/suffix extractor compared by `cmp`, covering the install, update, force, upgrade, and uninstall cases `[AC-2.1, AC-2.2, AC-2.3, AC-2.5]`
- [x] 2.2 Add failing cases to `scripts/tests/test_merge_claude_md.sh` and `scripts/tests/test_update_claude_md.sh`: preserved block without the import line (warning printed, file unchanged by `cmp`), preserved block with the line (no warning), and CRLF user content outside the markers on the replace path `[AC-2.2, AC-2.4]`
- [x] 2.3 Edit `scripts/install.sh`: Claude branch of the inventory block, the dry-run platform-files block, and the platform step block (replace the skipped step with the copy); `write_copy_manifest` records `system-instructions.md` for Claude; the scoped git commit adds the file `[AC-2.1]`
- [x] 2.4 Edit `scripts/update.sh`: run the `SYSINST_ACTION` scan for `cursor` or `claude`, count it as actionable for Claude, copy on `update`/`new` in the Claude apply branch, record it in `write_copy_manifest`, and add it to the scoped git commit `[AC-2.3]`
- [x] 2.5 Add `writ_block_inner_has_line` inside the `writ-merge-bundled` region of both `install.sh` and `update.sh`, and print the warning from the preserved branch of each `merge_claude_md` in preview and apply; keep both bundles in sync `[AC-2.4]`
- [x] 2.6 Edit `scripts/uninstall.sh` (Claude branch of the `EXTRA_FILES` block) and the Claude rows and bullets in `commands/update-writ.md` (platform table, Step 3 platform files), `commands/reinstall-writ.md` (platform table, Step 3 removal list, Step 4 copy list), and `commands/uninstall-writ.md` (Step 3 platform files) `[AC-2.5]`
- [x] 2.7 Verify: `uv run --python 3.9 pytest`, then `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, then `bash scripts/eval.sh` outside the sandbox with 0 findings; also run `install.sh --platform claude --dry-run` in a temp directory and read the output `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Install copies system instructions, Install merges block, Update system instructions, Install or update block, Uninstall system instructions]
- **Shadow paths:** [Happy, Nil input, Empty input, Upstream error]
- **Business rules:** [User-owned bytes, The block comes only from the template, System instructions copy, Update decision, Uninstall, Test isolation]
- **Experience:** [State Catalog, Interaction Patterns]

## What Was Built

**Implementation Date:** 2026-10-21

### Files Created

- **`scripts/tests/test_install_update_claude_parity.sh`** — temp projects from a committed temp source copy (pattern from `test_install_update_harness_cuts.sh`). Covers the dry run and fresh install (AC-2.1); bytes outside the markers across append, update to a longer template, and `--force`, compared with a `python3 -c` prefix/suffix split and `cmp` (AC-2.2); update of an unmodified copy, a preserved modified copy, `--force`, the pre-parity upgrade, and the scoped commits (AC-2.3); the preserved-block warning in install and update, dry run and real run (AC-2.4); uninstall and the command-doc rows (AC-2.5).

### Files Modified

- **`scripts/install.sh`** — `writ_block_inner_has_line` inside `writ-merge-bundled`; the `merge_claude_md` preserved branch prints the import-line warning in preview and apply; `write_copy_manifest` records `system-instructions.md` for Cursor or Claude; the Claude inventory, dry run, platform step (`System instructions...` and the copy), and scoped commit include the file.
- **`scripts/update.sh`** — the same bundle helper and warning (ending `update.sh --force`); the `SYSINST_ACTION` scan runs for Cursor or Claude (`RULE_ACTION` stays Cursor-only); the Claude actionable count, apply, `write_copy_manifest`, and scoped commit include the file.
- **`scripts/uninstall.sh`** — the Claude branch of `EXTRA_FILES` gains `.claude/system-instructions.md`.
- **`commands/update-writ.md`**, **`commands/reinstall-writ.md`**, **`commands/uninstall-writ.md`** — the Claude rows and bullets name `.claude/system-instructions.md`.
- **`scripts/tests/test_merge_claude_md.sh`** (cases 8–11), **`scripts/tests/test_update_claude_md.sh`** (cases 8–12) — the helper counts only lines between the markers; the warning prints with the file unchanged; no warning when the block has the line; CRLF user bytes stay exact on replace and `--force`; update case 12 records the key only when the local copy exists. Case 7 of the update test now also loads `record_file_baseline`.
- **`scripts/tests/test_manifest_shipped_baselines.sh`** — the Claude expected shipped set lists `system-instructions.md` (DEV-010).
- **`scripts/eval.sh`** — one `referenced_paths_allowlist` row for `.claude/system-instructions.md` (DEV-010).

### Implementation Decisions

1. **Separate `git add` line.** The scoped commit adds `.claude/system-instructions.md` on its own line, because a combined `git add` that names a missing path stages nothing.
2. **The warning line goes through `ENVIRON`.** The helper passes the line to awk through the environment so backslashes are not interpreted.
3. **Cursor's rule copied as written** (DEV-009).

### Test Results

**Verification:** test-first, then full suites.

- Red: the parity test failed on the original scripts at "install --dry-run does not print the system-instructions.md copy", and after the install and update edits at "uninstall --dry-run does not list .claude/system-instructions.md"; both bundle tests failed with `writ_block_inner_has_line: command not found` on the new cases.
- Mutations: the coder's seven (drop the Claude copy, either warning, the actionable count, the uninstall line; helper scans the whole file; manifest records Cursor only) and the reviewer's three (drop either `git add` line; update records Cursor only) were each caught.
- Reviewer probes: Cursor and Codex dry run, install, update, modified-file update, `--force`, and uninstall produce the same output, trees, manifests, and commits as HEAD's scripts after SHA normalization. A real pre-parity upgrade (install with HEAD's scripts and the pre-Story-1 template, then update) gave `✨ New` and a block with the import line.
- Orchestrator run: `test_install_update_claude_parity.sh`, `test_merge_claude_md.sh`, `test_update_claude_md.sh`, `test_manifest_shipped_baselines.sh`, `test_install_update_harness_cuts.sh`, `test_install_update_dev_scripts.sh` → exit 0; `eval.sh --check=referenced-paths` → Findings 0.
- Full suites (coder and reviewer): pytest 3.9 → 2672 passed, 2 skipped; bash loop → 42 run, 0 failed; `bash scripts/eval.sh` → Findings 0; `ac-trace.py check` → 0 findings for this spec and for `2026-10-20-ci-and-update-integrity`.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-009, DEV-010)
- **Security:** Clean
- **Boundary Compliance:** two one-line edits outside the map (`test_manifest_shipped_baselines.sh`, `eval.sh`), both judged required by the reviewer.
- gate3-route: review-agent (outside_boundary scripts/tests/test_manifest_shipped_baselines.sh; outside_boundary scripts/eval.sh). review-panel: skipped — platform cannot spawn other vendors. arch-lint: none — see .writ/docs/architecture-lint.md.
- Gate 0 arch-check: pass (rederived proceed). Gate 2: `bash -n` clean on every changed script; no linter configured. Gate 3.5 drift-format: pass. Gate 3 review-override and Gate 4 authenticity: `test_imports_no_source` on the three bash tests, the known false positive for shell tests (`.writ/issues/improvements/2026-10-12-test-integrity-shell-tests.md`); carried on the red-phase and mutation evidence above, not DEGRADED. Gate 4 coverage: unverifiable (no report). Gate 4.5: app-verify unverifiable (no recipe). Gate 5: docs-check unverifiable (no public exports).
- Reviewer notes, not fixed here: the comment in `update.sh` `write_copy_manifest` about running without other helpers is stale now that case 7 loads `record_file_baseline`; the "manifest present, no baseline line, local differs" branch has no test on either platform; `update.sh` prints the `⚠️` line flush-left under the indented `⚡ Preserved` line, as the spec's exact text has no indent; `unlink.sh` does not record `system-instructions.md` for Claude (matters only for legacy symlinked installs).

### Deviations from Spec

- **[DEV-009] Business Rule 5's "no baseline → update" is not Cursor's actual rule** — Severity: Small. Resolution: Auto-amended (spec-lite S2 line).
- **[DEV-010] Two files changed outside the Story 2 task list** — Severity: Small. Resolution: Auto-amended (spec-lite S2 line).
