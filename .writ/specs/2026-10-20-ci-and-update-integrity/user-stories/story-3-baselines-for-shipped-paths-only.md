# Story 3: Record Baselines Only for Shipped Paths; Customized Files Keep Their Baseline

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** user of a project with Writ installed
**I want to** have `install.sh` and `update.sh` record baselines only for files Writ ships, and keep a customized file's previous baseline
**So that** my own files in Writ's folders are never deleted and my edits to Writ files are never silently overwritten by a later update

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given a temp project that already holds `.writ/docs/tech-stack.md`, `scripts/deploy.sh`, `.claude/commands/my-own.md`, and a user-written `.claude/commands/review.md`, when `install.sh --platform claude --no-commit` runs, then all four files are byte-identical; the manifest contains the header line `# baselines: shipped`; and it has no line for any of the four paths, because `review.md` was preserved with no baseline. Run over an existing manifest that lacks the header, install writes no header `[AC-3.1]`
- [x] Given that project after install, plus `.writ/docs/code-style.md` and `.claude/agents/my-agent.md` created afterward, when `update.sh` runs three times and each run rewrites the manifest, then no user-authored file is ever recorded, named in a stale or removal line, or removed, and `commands/review.md` is reported preserved and stays byte-identical on every run `[AC-3.2]`
- [x] Given a Claude Code project with a locally customized `commands/status.md` and a customized CLAUDE.md Writ block, and a Cursor project with a customized `rules/writ.mdc`, when a manifest-rewriting update runs, upstream then changes each of the three again, and update runs once more, then each is preserved and byte-identical after both runs, and the manifest still carries each one's install-time baseline `[AC-3.3]`
- [x] Given a fresh install and one update, when the manifest is read, then every path in the shipped set (filter-passing scripts, `.writ/docs`, commands minus unshipped lean siblings, agents, skills, platform units) has exactly one line. Its hash is the upstream file's hash, or the previous baseline for a preserved file. The Codex `.codex/config.toml.baseline` line from Story 2 is still present once `[AC-3.4]`
- [x] Given `scripts/tests/test_manifest_shipped_baselines.sh` and the pre-fix `install.sh` and `update.sh`, when the test runs, then it fails, naming a recorded or removed user file or an overwritten customization; after the fix it passes, and every existing `scripts/tests/test_install_update_*.sh` and `test_update_*.sh` passes `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Write a new `scripts/tests/test_manifest_shipped_baselines.sh` (committed source copy, temp projects, `WRIT_REPO`; the pattern of `scripts/tests/test_install_update_dev_scripts.sh` lines 19-39 and 61-72). Cover AC-3.1 through AC-3.4 on Claude Code, plus `rules/writ.mdc` on Cursor. Run it against the unchanged scripts, confirm it fails, and save the failing line `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
- [x] 3.2 In `scripts/update.sh`, generalize Story 2's read-before-truncate: before any lookup, copy the manifest's baseline lines into a per-run temp file. Point `manifest_hash_for` and `manifest_files` (`155-162`) at it, and have `write_copy_manifest` read previous baselines from it `[AC-3.3, AC-3.4]`
- [x] 3.3 Rewrite `write_copy_manifest` in `scripts/update.sh` (`164-247`) to iterate the shipped set from `$WRIT_SRC` (Business Rule 1), not the project's folders. For each path, record the upstream hash when local equals upstream, or the previous baseline, or no line, when preserved. Write `# baselines: shipped` in the header. Keep the `STALE_KEPT_ENTRIES` carry-forward and the Codex config line. `append_manifest_shippable_scripts` and `append_manifest_writ_docs` (`667-683`) are called only here; replace or delete them `[AC-3.2, AC-3.3, AC-3.4]`
- [x] 3.4 Apply Business Rule 3 to the platform units in `update.sh`'s `write_copy_manifest`. When `CLAUDE_MD_ACTION` or `AGENTS_MD_ACTION` is `preserved`, write the previous Writ-block baseline instead of the recomputed inner hash. When `RULE_ACTION` or `SYSINST_ACTION` is `preserved`, write the previous baseline for `rules/writ.mdc` or `system-instructions.md` `[AC-3.3]`
- [x] 3.5 Make the same change to `write_copy_manifest` in `scripts/install.sh` (`639-705`) and its two `append_manifest_*` helpers (`1006-1022`, called only at `653-654`): iterate the shipped set, apply Business Rule 3 using the existing manifest (read before truncation) for re-installs, and write the header only for a fresh install or over a manifest that has it (Business Rule 10). Change no other `install.sh` function `[AC-3.1, AC-3.4]`
- [x] 3.6 Verify: run the new test, `test_install_update_dev_scripts.sh`, `test_install_update_lean_siblings.sh`, `test_install_update_thresholds.sh`, and `test_update_codex_config_baseline.sh`, and all pass. Re-prove the pre-fix failure by copying the new test into a temp `git archive <pre-fix commit>` extract and running it there. Then run `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` (no `FAIL` lines), and `bash scripts/eval.sh` outside any sandbox `[AC-3.5]`

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Rewrite manifest (user-authored file recorded), Rewrite manifest (preserved file re-baselined), Install over a user file at a shipped path] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [User-authored file across installs and updates, Customized shipped file across upstream changes] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Rule 1 (shipped set), Rule 2 (shipped paths only, header), Rule 3 (baseline value), Rule 10 (install header rule), Rule 13 (temp dirs only)] — spec.md → ## Business Rules (Expanded)
- **Experience:** [State Catalog rows "Install into a project with user files in tracked folders", "Install over a user file at a shipped path", "Update, user-authored file in a tracked folder", "Update, customized shipped file, upstream changes it again"] — spec.md → ## Experience Design → ### State Catalog
- **Technical:** technical-spec.md → ## Story 3 Design: Shipped-only baselines

---

## What Was Built

**Implementation Date:** 2026-10-20

### Files Created

1. **`scripts/tests/test_manifest_shipped_baselines.sh`** (~5 installs, 6 updates, about 65 s) — committed source copy, `WRIT_REPO=$SRC`. Each update follows an upstream change to `commands/create-issue.md`, and `check_rewritten` proves the manifest was rewritten. Covers install over four pre-existing user files and re-install over a header-less manifest (AC-3.1); three updates with user files added after install (AC-3.2); a customized `status.md` and CLAUDE.md Writ block, and a Cursor `rules/writ.mdc`, across an upstream change to each (AC-3.3); and `check_complete`, which compares the sorted manifest to a shipped set computed independently from the source on claude, cursor, and codex, and rejects any line that is not `<64-hex>  <path>` (AC-3.4). The Codex project also holds byte-equal copies of an unshipped lean sibling and `scripts/harness-cost.py` to exercise the filters. [AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]

### Files Modified

- **`scripts/update.sh`**
  - New `BASELINES_FILE` and `load_baselines` (the one place that fills the per-run baseline file; runs right after the clone and `trap cleanup EXIT`). `cleanup` removes it.
  - `manifest_hash_for`: exact match on the path field, first line wins. `manifest_files`: reads the per-run file.
  - New `record_file_baseline`: local equals upstream → upstream hash; local differs → previous baseline, or no line; no local copy → no line. Never writes an empty hash.
  - `write_copy_manifest`: writes `# baselines: shipped`; walks the shipped set from `$WRIT_SRC` (scripts via `is_shippable_script`, `.writ/docs/*.md`, commands and agents minus unshipped lean siblings, `skills/*/SKILL.md`, Cursor `rules/writ.mdc` and `system-instructions.md`); Writ block recorded when its inner hash equals the template hash, else previous baseline or none. Story 2's Codex config read and the `STALE_KEPT_ENTRIES` carry-forward are unchanged.
  - `append_manifest_shippable_scripts`, `append_manifest_writ_docs`: walk `$WRIT_SRC` and call `record_file_baseline`.
- **`scripts/install.sh`** — `write_copy_manifest` snapshots the previous baselines before truncating and writes `# baselines: shipped` only on a fresh install or over a manifest that has it. Same shipped-set walk and Writ-block rule. New helpers `previous_manifest_hash_for` and `record_file_baseline`, called only from `write_copy_manifest` and its two `append_manifest_*` helpers. No other function changed.

### Implementation Decisions

1. **Post-run comparison instead of the `*_ACTION` variables** (DEV-002). It is equivalent for every reachable action and works in `install.sh`, which has no action variables for this.
2. **Inline Writ-block rule and `${AGENTS_SRC:-}` / `${AGENT_FILE_GLOB:-}` defaults** — `scripts/tests/test_update_claude_md.sh` case 7 runs `write_copy_manifest` alone without those globals.
3. **`.writ/docs/*.md` only** — per Business Rule 1. The overlay copies every file in `.writ/docs/`; all are `.md` today.

### Test Results

**Verification:** test-first, then regression and full suites.

- Pre-fix: `FAIL: AC-3.1 install: manifest records user file .writ/docs/tech-stack.md` on the unchanged scripts; same line in a `git archive ef012f5` extract (orchestrator re-proof, exit 1). With the fixed `install.sh` and the pre-fix `update.sh`: `FAIL: AC-3.2/AC-3.3 claude update 1: manifest records user file .writ/docs/tech-stack.md`.
- Mutations caught (coding agent and evaluator): update re-baselines a differing file; update re-baselines a preserved block; install writes the header over a header-less manifest; install records a preserved user file; update writes no header; lean or ship filter removed in either script; `record_file_baseline` records the local hash.
- After: `PASS test_manifest_shipped_baselines` (65 s). Also passed under bash 5.2 (evaluator).
- Regression: `test_install_update_dev_scripts`, `test_install_update_lean_siblings`, `test_install_update_thresholds`, `test_update_codex_config_baseline`, `test_update_claude_md`, `test_merge_claude_md`, `test_merge_agents_md` all pass.
- Full suites (orchestrator run): `uv run --python 3.9 pytest` → `2623 passed, 2 skipped in 154.49s`; bash loop → 37 run, 0 failed; `bash scripts/eval.sh` → exit 0, `Findings: 0`, `Run errors: 0` (includes the cursor, claude, and codex install/update/unlink sandbox checks).
- Evaluator probes (temp projects): re-install over a customized file keeps its baseline; `update --force` and `install --force` record the upstream hash; a deleted shipped file is re-copied with the upstream hash; a dry run leaves the manifest byte-identical; a pre-existing customized Writ block on a fresh install is preserved with no line; a user skill under `.agents/skills` is never recorded; malformed Writ-block markers abort before the manifest is written.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-002, DEV-003)
- **Security:** None. Manifest data is read through `awk -v`; the temp file comes from `mktemp` and the trap removes it.
- **Boundary Compliance:** 0 crossings; route evaluator-agent.
- Gate 0 arch-check: pass. Gate 2: `bash -n` clean. Gate 2.5: cross-component. review-override: unverifiable (no coverage report). Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable. Gate 4 authenticity: `test_imports_no_source`, the known false positive for bash tests (open issue `.writ/issues/improvements/2026-09-03-test-integrity-authenticity-flags-every-bash-test.md`); carried on the pre-fix proof and the mutation runs. Not DEGRADED. Gate 4.5: app-verify unverifiable (no recipe). Gate 5: docs-check unverifiable.
- Evaluator residuals: `update.sh` now stamps the header on every rewrite, including over a legacy manifest, so Story 5 must ship in the same release. `2026-10-20-claude-code-parity` edits both `write_copy_manifest` bodies; expect a merge conflict, and it should use `record_file_baseline`. The Story 2 read-before-truncate is now redundant at runtime. `record_file_baseline` is duplicated in both scripts with "keep synced" comments.

### Deviations from Spec

- **[DEV-002] Baseline rule applied by a post-run comparison, not the action variables** — Severity: Small
  - Spec said: task 3.4 keys on `*_ACTION == preserved`.
  - Reality: compares local to upstream after the run; equivalent for every reachable action.
  - Resolution: auto-amended.
  - Spec amendment: spec-lite.md S3 line.
- **[DEV-003] install.sh gained helpers called only by write_copy_manifest** — Severity: Small
  - Spec said: change only `write_copy_manifest` and its two helpers.
  - Reality: three new helpers, used only by those functions; no other function changed.
  - Resolution: auto-amended.
  - Spec amendment: spec-lite.md Files in Scope.
