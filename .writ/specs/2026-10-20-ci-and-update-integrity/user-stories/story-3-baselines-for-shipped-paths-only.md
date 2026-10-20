# Story 3: Record Baselines Only for Shipped Paths; Customized Files Keep Their Baseline

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** user of a project with Writ installed
**I want to** have `install.sh` and `update.sh` record baselines only for files Writ ships, and keep a customized file's previous baseline
**So that** my own files in Writ's folders are never deleted and my edits to Writ files are never silently overwritten by a later update

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given a temp project that already holds `.writ/docs/tech-stack.md`, `scripts/deploy.sh`, `.claude/commands/my-own.md`, and a user-written `.claude/commands/review.md`, when `install.sh --platform claude --no-commit` runs, then all four files are byte-identical; the manifest contains the header line `# baselines: shipped`; and it has no line for any of the four paths, because `review.md` was preserved with no baseline. Run over an existing manifest that lacks the header, install writes no header `[AC-3.1]`
- [ ] Given that project after install, plus `.writ/docs/code-style.md` and `.claude/agents/my-agent.md` created afterward, when `update.sh` runs three times and each run rewrites the manifest, then no user-authored file is ever recorded, named in a stale or removal line, or removed, and `commands/review.md` is reported preserved and stays byte-identical on every run `[AC-3.2]`
- [ ] Given a Claude Code project with a locally customized `commands/status.md` and a customized CLAUDE.md Writ block, and a Cursor project with a customized `rules/writ.mdc`, when a manifest-rewriting update runs, upstream then changes each of the three again, and update runs once more, then each is preserved and byte-identical after both runs, and the manifest still carries each one's install-time baseline `[AC-3.3]`
- [ ] Given a fresh install and one update, when the manifest is read, then every path in the shipped set (filter-passing scripts, `.writ/docs`, commands minus unshipped lean siblings, agents, skills, platform units) has exactly one line. Its hash is the upstream file's hash, or the previous baseline for a preserved file. The Codex `.codex/config.toml.baseline` line from Story 2 is still present once `[AC-3.4]`
- [ ] Given `scripts/tests/test_manifest_shipped_baselines.sh` and the pre-fix `install.sh` and `update.sh`, when the test runs, then it fails, naming a recorded or removed user file or an overwritten customization; after the fix it passes, and every existing `scripts/tests/test_install_update_*.sh` and `test_update_*.sh` passes `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write a new `scripts/tests/test_manifest_shipped_baselines.sh` (committed source copy, temp projects, `WRIT_REPO`; the pattern of `scripts/tests/test_install_update_dev_scripts.sh` lines 19-39 and 61-72). Cover AC-3.1 through AC-3.4 on Claude Code, plus `rules/writ.mdc` on Cursor. Run it against the unchanged scripts, confirm it fails, and save the failing line `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
- [ ] 3.2 In `scripts/update.sh`, generalize Story 2's read-before-truncate: before any lookup, copy the manifest's baseline lines into a per-run temp file. Point `manifest_hash_for` and `manifest_files` (`155-162`) at it, and have `write_copy_manifest` read previous baselines from it `[AC-3.3, AC-3.4]`
- [ ] 3.3 Rewrite `write_copy_manifest` in `scripts/update.sh` (`164-247`) to iterate the shipped set from `$WRIT_SRC` (Business Rule 1), not the project's folders. For each path, record the upstream hash when local equals upstream, or the previous baseline, or no line, when preserved. Write `# baselines: shipped` in the header. Keep the `STALE_KEPT_ENTRIES` carry-forward and the Codex config line. `append_manifest_shippable_scripts` and `append_manifest_writ_docs` (`667-683`) are called only here; replace or delete them `[AC-3.2, AC-3.3, AC-3.4]`
- [ ] 3.4 Apply Business Rule 3 to the platform units in `update.sh`'s `write_copy_manifest`. When `CLAUDE_MD_ACTION` or `AGENTS_MD_ACTION` is `preserved`, write the previous Writ-block baseline instead of the recomputed inner hash. When `RULE_ACTION` or `SYSINST_ACTION` is `preserved`, write the previous baseline for `rules/writ.mdc` or `system-instructions.md` `[AC-3.3]`
- [ ] 3.5 Make the same change to `write_copy_manifest` in `scripts/install.sh` (`639-705`) and its two `append_manifest_*` helpers (`1006-1022`, called only at `653-654`): iterate the shipped set, apply Business Rule 3 using the existing manifest (read before truncation) for re-installs, and write the header only for a fresh install or over a manifest that has it (Business Rule 10). Change no other `install.sh` function `[AC-3.1, AC-3.4]`
- [ ] 3.6 Verify: run the new test, `test_install_update_dev_scripts.sh`, `test_install_update_lean_siblings.sh`, `test_install_update_thresholds.sh`, and `test_update_codex_config_baseline.sh`, and all pass. Re-prove the pre-fix failure by copying the new test into a temp `git archive <pre-fix commit>` extract and running it there. Then run `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` (no `FAIL` lines), and `bash scripts/eval.sh` outside any sandbox `[AC-3.5]`

## Notes

- **Grounding probes (2026-10-20).** `install.sh` recorded pre-existing `.writ/docs/tech-stack.md`, `scripts/deploy.sh`, and `.claude/commands/my-own.md`, and the first update removed all three. A user-written `review.md` that install preserved was recorded with its local hash, and the first upstream change to `review.md` overwrote it. On update alone, files created after install were recorded at the next manifest rewrite and removed on the update after that.
- **Each update needs a manifest rewrite.** "Already up to date" (`scripts/update.sh:1024-1038`) skips `write_copy_manifest`. Commit an upstream change to a locally unmodified shipped command before each update.
- **Shipped set filters.** Use the same predicates the overlay scans use: `is_shippable_script`, `is_unshipped_lean_sibling`, `AGENT_FILE_GLOB`, and `skills/*/SKILL.md` folders. Do not keep a second list. Agents record as `agents/<name>`, and skills as `skills/<name>/SKILL.md`.
- **Writ-block hash.** `merge_claude_md` and `merge_agents_md` compare the inner hash with `hash_file` of the template (`update.sh:499`). The recorded value for an unpreserved block is unchanged.
- **Story 4 depends on this.** After this story, a kept stale path is not in the shipped set, so it is never re-recorded from its local copy. Story 4 only widens the warning and keeps the carry-forward.
- **Legacy manifests are Story 5's.** This story writes the header but does not change how a header-less manifest is read.
- **`install.sh` scope.** Change only `write_copy_manifest` and the two helpers it alone calls. Grep before deleting a helper.
- **Never run `install.sh` or `update.sh` against the Writ repo.** It is symlinked into `.claude/` and `.cursor/`. Run everything in temp directories. The tests do `git init`, so run them outside any sandbox.
- **Other Phase 13 work.** `2026-10-20-claude-code-parity` adds `system-instructions.md` for Claude Code to both `write_copy_manifest` functions. Run `git diff` before editing shared files and change only the targeted lines.
- **Citations.** Name this spec (`2026-10-20-ci-and-update-integrity`) in the comment that carries `AC-3.n` tokens.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Rewrite manifest (user-authored file recorded), Rewrite manifest (preserved file re-baselined), Install over a user file at a shipped path] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [User-authored file across installs and updates, Customized shipped file across upstream changes] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Rule 1 (shipped set), Rule 2 (shipped paths only, header), Rule 3 (baseline value), Rule 10 (install header rule), Rule 13 (temp dirs only)] — spec.md → ## Business Rules (Expanded)
- **Experience:** [State Catalog rows "Install into a project with user files in tracked folders", "Install over a user file at a shipped path", "Update, user-authored file in a tracked folder", "Update, customized shipped file, upstream changes it again"] — spec.md → ## Experience Design → ### State Catalog
- **Technical:** technical-spec.md → ## Story 3 Design: Shipped-only baselines
