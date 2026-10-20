# Story 2: Keep the Codex Config Baseline on Update

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** Codex CLI user of a project with Writ installed
**I want to** have `update.sh` keep the `.codex/config.toml.baseline` line in `.codex/.writ-manifest`
**So that** `.codex/config.toml` stays install-once and its customization check keeps working after every update

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.4

- [ ] Given a temp project installed with `install.sh --platform codex --no-commit`, whose manifest carries one `.codex/config.toml.baseline` line, when `update.sh --platform codex --no-commit` runs against a source with an upstream change that makes it rewrite the manifest, then the manifest still has exactly one `.codex/config.toml.baseline` line with the same hash, and `.codex/config.toml` is byte-identical `[AC-2.1]`
- [ ] Given the same project, when a second manifest-rewriting update and then a `--dry-run` run, then the baseline line is unchanged after each, and the dry run leaves the manifest byte-identical `[AC-2.2]`
- [ ] Given a Codex project whose manifest has no `.codex/config.toml.baseline` line, when `update.sh` runs, then it exits 0 and writes no baseline line `[AC-2.3]`
- [ ] Given `scripts/tests/test_update_codex_config_baseline.sh` and the pre-fix `update.sh`, when the test runs, then it fails at AC-2.1 (baseline line count 1 → 0); after the fix it passes; and `.writ/issues/bugs/2026-10-12-codex-config-baseline-dropped-on-update.md` ends with a `## Resolution` section naming the fix and the test `[AC-2.4]`

## Implementation Tasks

- [ ] 2.1 Write a new `scripts/tests/test_update_codex_config_baseline.sh`, reusing the committed-source-copy, `commit_src`, `fail`, and `hash_file` patterns of `scripts/tests/test_install_update_dev_scripts.sh` (lines 19-39, 61-72). Cover two manifest-rewriting updates, a dry run, and the no-baseline case. Run it against the unchanged `scripts/update.sh`, confirm it fails at the first update, and save the failing line for What Was Built `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [ ] 2.2 In `write_copy_manifest` (`scripts/update.sh:164`), read `manifest_hash_for ".codex/config.toml.baseline"` into a local before `cat > "$target"` (line 167), following `scripts/unlink.sh:199-204`. Have the Codex block (`225-234`) write that value when non-empty `[AC-2.1, AC-2.2, AC-2.3]`
- [ ] 2.3 Confirm that no other line `write_copy_manifest` writes today reads the old manifest after truncation. `AGENTS.md.writ-block` is recomputed from `AGENTS.md`. `STALE_KEPT_ENTRIES` is filled earlier by `detect_stale_files`. Record the check in What Was Built `[AC-2.1]`
- [ ] 2.4 Verify the fix: `bash scripts/tests/test_update_codex_config_baseline.sh` passes. Re-prove the pre-fix failure by copying the new test into a temp `git archive <pre-fix commit>` extract and running it there `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [ ] 2.5 Verify the regression surface: `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` (no `FAIL` lines), and `bash scripts/eval.sh` outside any sandbox; all pass `[AC-2.4]`
- [ ] 2.6 Append `## Resolution` to `.writ/issues/bugs/2026-10-12-codex-config-baseline-dropped-on-update.md`, naming the read-before-truncate change and `scripts/tests/test_update_codex_config_baseline.sh` `[AC-2.4]`

## Notes

- **The update must rewrite the manifest.** With nothing actionable, `update.sh` exits "Already up to date" before `write_copy_manifest` (`scripts/update.sh:1024-1038`), and the pre-fix script keeps the line. Commit an upstream change to a locally unmodified shipped command before each update.
- **Grounding probe (2026-10-20).** A Codex install recorded one baseline line. One update with an upstream change left zero.
- **Codex paths.** The manifest is `.codex/.writ-manifest`, skills live in `.agents/skills`, and agents are `codex/agents/*.toml`. `install.sh` seeds `.codex/config.toml` from `codex/config.toml.template` and records its hash as `.codex/config.toml.baseline` (`scripts/install.sh:566-597`, `701`).
- **Later stories build on this.** Story 3 generalizes the read-before-truncate into a per-run baseline file that every lookup reads. Keep this change to the Codex line so Story 3 starts from a small diff.
- **Out of scope:** `unlink.sh` (already correct) and `install.sh` (Story 3 owns its `write_copy_manifest`).
- **Never run `install.sh` or `update.sh` against the Writ repo.** It is symlinked into `.claude/` and `.cursor/`. Run everything in temp directories. The test does `git init`, so run it outside any sandbox.
- **Citations.** Name this spec (`2026-10-20-ci-and-update-integrity`) in the comment that carries `AC-2.n` tokens.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Rewrite manifest (Codex baseline read after truncation), Rewrite manifest (no prior baseline line)] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Codex baseline] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Rule 8 (read the Codex baseline before truncating), Rule 7 (dry runs never write), Rule 13 (temp dirs only)] — spec.md → ## Business Rules (Expanded)
- **Experience:** [State Catalog rows "Codex update", "Codex manifest with no baseline line"] — spec.md → ## Experience Design → ### State Catalog
- **Technical:** technical-spec.md → ## Story 2 Design: Codex baseline
