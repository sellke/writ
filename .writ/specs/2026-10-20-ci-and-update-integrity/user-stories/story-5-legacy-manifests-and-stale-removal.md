# Story 5: Repair Legacy Manifests and Remove Stale Files From Their Real Path

> **Status:** Completed ✅
> **Commit:** a805e09abf6cecd48fe723126f40e4ff31025592
> **Priority:** High
> **Dependencies:** Story 4

## User Story

**As a** user upgrading a project whose manifest was written by a pre-fix Writ release
**I want to** have the first fixed `update.sh` run leave my own files and my edits alone, and remove only retired Writ files, from the folder they actually live in
**So that** the fixes in Stories 3 and 4 protect me on the first update, not only from the second update on

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [x] Given a legacy manifest (no `# baselines: shipped` header) whose `# version:` resolves upstream and which records user-authored `.writ/docs/tech-stack.md`, `scripts/deploy.sh`, and `.claude/commands/my-own.md` with their local hashes, when `update.sh` runs, then the three files are byte-identical, no stale or removal line names them, and the rewritten manifest has the header and no line for them; a second update also leaves them alone `[AC-5.1]`
- [x] Given the same kind of legacy manifest, plus an unmodified `commands/zz-retired.md` that upstream shipped at the recorded version and no longer ships, plus a customized `commands/status.md` whose recorded baseline equals its local hash (re-baselined by the old scripts), when `update.sh` runs after an upstream change to `status.md`, then `zz-retired.md` is removed with `🗑  Removed: commands/zz-retired.md`, and `status.md` is preserved byte-identical with its baseline set to the upstream content at the recorded version `[AC-5.2]`
- [x] Given a legacy manifest whose version does not resolve (`unknown`, or a commit upstream lacks), when `update.sh` runs, then it prints one notice naming the reason, removes nothing, overwrites no file that differs from upstream, keeps the `.codex/config.toml.baseline` line on Codex, and writes a manifest with the header. With `WRIT_REPO=file://…` (a shallow clone) and a version older than the clone's tip, the version resolves after one `git fetch --unshallow`, and AC-5.1 and AC-5.2 hold. `commands/update-writ.md` Step 3 describes this legacy handling in one sentence `[AC-5.3]`
- [x] Given a Codex project with an unmodified stale skill at `.agents/skills/zz-old/SKILL.md`, when `update.sh` runs, then the file is removed and `🗑  Removed: skills/zz-old/SKILL.md` is printed; on Claude Code and Codex, each path printed as `🗑  Removed:` is absent from disk after the run `[AC-5.4]`
- [x] Given `scripts/tests/test_update_legacy_manifest.sh` and the pre-fix `update.sh`, when the test runs, then it fails, naming a removed user file, an overwritten customization, or a Codex skill still on disk after a Removed line; after the fix it passes, and every existing install/update bash test passes `[AC-5.5]`

## Implementation Tasks

- [x] 5.1 Write a new `scripts/tests/test_update_legacy_manifest.sh` covering AC-5.1 through AC-5.4. Build each legacy manifest by installing with the fixed `install.sh`, deleting the `# baselines: shipped` line, rewriting `# version:` (a source commit, `unknown`, or a bogus hash), and appending the lines a pre-fix script would have written. Use `WRIT_REPO=file://$SRC` for the shallow case. Run the test against the unchanged `scripts/update.sh`, confirm it fails, and save the failing line `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`
- [x] 5.2 Add a legacy-baseline step to `scripts/update.sh`, after the clone and before the scan. When the manifest lacks the header, resolve `# version:` in `$WRIT_SRC`, running `git fetch --quiet --unshallow` once if the clone is shallow and the commit is missing. Then build the per-run baseline file (Story 3) from upstream content at that version: an upstream blob hash for each manifest path whose source exists there, the inner hash of the template at that version for the Writ blocks, and `.codex/config.toml.baseline` as recorded. Drop every other path `[AC-5.1, AC-5.2, AC-5.3]`
- [x] 5.3 Add the unresolvable fallback. When the version cannot be resolved or the fetch fails, the per-run baseline file holds only `.codex/config.toml.baseline`, so the run behaves like the existing no-manifest path. Print one notice: `⚠️  Manifest predates shipped-only baselines and version <v> was not found upstream; files that differ from upstream are preserved this run.` Add one sentence on legacy manifests to `commands/update-writ.md` Step 3 `[AC-5.3]`
- [x] 5.4 Fix the stale-removal block (`scripts/update.sh:1114-1129`). Resolve skills paths through `$SKILLS_DIR` (`.agents/skills` on Codex, `update.sh:86`) instead of `$PLATFORM_DIR`, and print `🗑  Removed: <path>` only when the file is gone after `rm` `[AC-5.4]`
- [x] 5.5 Verify: run the new test and every `scripts/tests/test_install_update_*.sh` and `test_update_*.sh`, and all pass. Re-prove the pre-fix failure by copying the new test into a temp `git archive <pre-fix commit>` extract and running it there `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`
- [x] 5.6 Verify the regression surface: `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` (no `FAIL` lines), and `bash scripts/eval.sh` outside any sandbox; all pass `[AC-5.5]`

## Notes

- **Why this story exists.** Every manifest written before this spec was produced by the pre-fix scripts. It records user files (probe: `/initialize`'s `.writ/docs/tech-stack.md`) and customizations re-baselined to their local hash. Without the legacy step, the first fixed update removes the former and overwrites the latter. The maintainer's rule says "on the first or any later update".
- **Why not just never remove legacy stale files.** It is simpler, but Writ files retired in this release would then never leave existing installs. One example is `commands/design.md` (`2026-10-20-platform-neutral-names` relies on stale removal). The version lookup removes them precisely and falls back to keeping everything when it cannot be sure.
- **Shallow clones.** `update.sh` clones with `--depth 1`, and git ignores `--depth` for a plain local path (`warning: --depth is ignored in local clones`). Only `file://` or a network URL is shallow, so the shallow case needs `WRIT_REPO=file://…`. Grounding: the Writ pack is 4.9 MiB, and `--unshallow` took under a second locally.
- **Source path mapping.**

  | Manifest path | Source path |
  |---|---|
  | `commands/x` | `commands/x` |
  | `agents/x` | `$AGENTS_SRC/x` |
  | `skills/n/SKILL.md` | `skills/n/SKILL.md` |
  | `scripts/x`, `.writ/docs/x` | same path |
  | `rules/writ.mdc` | `cursor/writ.mdc` |
  | `system-instructions.md` | `system-instructions.md` |
  | `CLAUDE.md.writ-block` | `claude-code/CLAUDE.md` |
  | `AGENTS.md.writ-block` | `codex/AGENTS.md.template` |
- **Dry runs** build the same per-run file in a temp path and never write the manifest. The fetch only touches the temp clone.
- **Removal message.** Detection already requires the local file to exist (`update.sh:838`). After the path fix, a "Removed" line without a removal can only come from a failed `rm`. Do not count such a path in the summary.
- **Out of scope:** `unlink.sh` writes header-less manifests. This story reads them as legacy and does not change `unlink.sh`. Stale-skill sidecars stay behind, and only `SKILL.md` is removed, as today.
- **Never run `install.sh` or `update.sh` against the Writ repo.** It is symlinked into `.claude/` and `.cursor/`. Run everything in temp directories. The test does `git init`, so run it outside any sandbox.
- **Citations.** Name this spec (`2026-10-20-ci-and-update-integrity`) in the comment that carries `AC-5.n` tokens.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Legacy manifest (version found), Legacy manifest (version not found or fetch fails), Stale removal (Codex skills path), Stale removal (rm fails)] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Legacy manifest upgrade] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Rule 5 (removal path and message), Rule 9 (legacy manifests), Rule 13 (temp dirs only)] — spec.md → ## Business Rules (Expanded)
- **Experience:** [State Catalog rows "Update from a legacy manifest, version found", "Update from a legacy manifest, version not found", "Codex update"] — spec.md → ## Experience Design → ### State Catalog
- **Technical:** technical-spec.md → ## Story 5 Design: Legacy manifests and removal paths

---

## What Was Built

**Implementation Date:** 2026-10-20

### Files Created

1. **`scripts/tests/test_update_legacy_manifest.sh`** (588 lines, about 2 min 16 s) — builds legacy manifests from a fixed install (header removed, `# version:` set, pre-fix-style lines appended). Case A (resolved, plain-path clone): user files untouched and unrecorded, `commands/zz-retired.md` removed, customized `status.md` preserved with its baseline at the recorded version, and a second update leaves the user files alone. Case B (unresolved: `unknown`, missing, `0000000` over a shallow `file://` clone; Codex `unknown`): one notice, no Removed line, no file changed, header written, Codex config line kept. Cursor unresolved (`unknown`, `0000000`) plus a second update, and Cursor resolved. Case C (shallow `file://`, version older than the tip): same as A after one `--unshallow`, plus a dry run that leaves the manifest byte-identical. Case D (Codex): `.agents/skills/zz-old/SKILL.md` removed; a `chmod 555` skill gets no Removed line, keeps its line, and is removed on the next run. Every update: each `🗑  Removed:` path is absent from disk. A doc check covers the Step 3 sentence. [AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]

### Files Modified

- **`scripts/update.sh`**
  - `load_baselines`: a manifest with `# baselines: shipped` is copied as before; one without it goes to `load_legacy_baselines`; no manifest means no baselines.
  - New `legacy_source_path` (the Story 5 mapping table; any other path, such as an old bare `CLAUDE.md` line, is dropped), `legacy_resolve_commit` (4-40 lowercase hex only; `rev-parse --verify "$v^{commit}"`; one `fetch --quiet --unshallow` when the clone is shallow; every failure returns 1 inside an `if`), and `load_legacy_baselines` (keeps the Codex config line; resolved → `<hash of the blob at v>  <path>` for each mapped path that existed at v; unresolved → only the Codex line, with `LEGACY_FALLBACK_REASON` set).
  - Notice: `⚠️  Manifest predates shipped-only baselines and <reason>; files that differ from upstream are preserved this run.`, in an `if/elif` with the old no-manifest notice so only one prints.
  - Stale-removal block: skills resolve through `$SKILLS_DIR`; the loop reads a here-string so counts reach the main shell; `🗑  Removed:` is printed and counted only when the path is gone; a path `rm` could not remove keeps its manifest line.
  - Cursor `rules/writ.mdc` and `system-instructions.md` scan blocks: a unit with no baseline is updated only when no manifest file exists; with a manifest, a differing unit with no baseline is preserved (`no baseline, assuming modified`). `--force` still updates. (Iteration 2, DEV-007.)
- **`commands/update-writ.md`** — Step 3 gains one `**Legacy manifests:**` sentence. [AC-5.3]

### Implementation Decisions

1. **Notice reasons** — empty or `unknown` version: "its version is unknown"; invalid, missing, or unfetchable commit: "version <v> was not found upstream".
2. **Blob hashing** — `git cat-file blob` into a temp file, hashed with `hash_file`. `cat-file --filters` would match CRLF checkouts under `core.autocrlf=true`, but needs a type guard (it prints raw tree bytes for a directory path); not adopted. A mismatch there keeps files rather than overwriting them.
3. **Failed `rm`** — keeps the manifest line so the next run retries (DEV-006).
4. **Cursor no-baseline rule** — decided from the manifest file as it was at the start of the run; `write_copy_manifest` runs after the scan.

### Test Results

**Verification:** test-first, one recode, then regression and full suites.

- Pre-fix: on `git archive 6f24327` (lane HEAD before this story), exit 1 with `FAIL: A update 1: user file .writ/docs/tech-stack.md was removed. Stale lines: 🗑  Removed: commands/zz-retired.md;🗑  Removed: skills/zz-locked/SKILL.md;🗑  Removed: skills/zz-old/SKILL.md;🗑  Removed: .writ/docs/tech-stack.md;🗑  Removed: scripts/deploy.sh;🗑  Removed: commands/my-own.md` (orchestrator re-proof, both iterations). Scratch variants: B alone fails `want one legacy notice, got 0`; D alone fails `printed '🗑  Removed: skills/zz-locked/SKILL.md' but .agents/skills/zz-locked/SKILL.md is still on disk`.
- Iteration 2 Cursor case on the iteration-1 code: `FAIL: B update (cursor, version unknown): customized rules/writ.mdc was overwritten`.
- After: `PASS test_update_legacy_manifest` (136 s). Passes under bash 3.2 and 5.3.
- Regression: `test_install_update_dev_scripts`, `_lean_siblings`, `_thresholds`, `test_update_codex_config_baseline`, `test_update_kept_stale_files`, `test_manifest_shipped_baselines`, `test_update_claude_md` pass; the evaluator also ran `test_merge_claude_md`, `test_merge_agents_md`, `test_remove_agents_md_block`.
- Full suites (orchestrator run, iteration 2): `uv run --python 3.9 pytest` → `2623 passed, 2 skipped in 155.35s`; bash loop → 39 run, 0 failed; `bash scripts/eval.sh` → exit 0, `Findings: 0`, `Run errors: 0`; `gen-skill.sh --check` → `pass`.
- Evaluator probes: modified retired file kept and warned with its at-version hash; unmodified dev-only script recorded by a legacy manifest removed; dry run over a shallow clone leaves the project byte-identical; customized Codex `AGENTS.md` block preserved; versions `HEAD`, `main`, uppercase, 3 or 41 characters, `--help` all fall back; a header manifest's output and manifest match pre-fix; an `unlink.sh`-written manifest is repaired; Cursor header manifests with lines behave as before and no-manifest Cursor still updates.

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s)
- **Drift:** Medium (DEV-006 Small, DEV-007 Medium, DEV-008 Small, DEV-009 Small). ⚠️ DEV-007 widened the change to update.sh's Cursor scan blocks.
- **Security:** None. The version must be 4-40 lowercase hex before git sees it; manifest paths reach git only as `$commit:$src`.
- **Boundary Compliance:** 0 crossings; route evaluator-agent.
- Gate 3 iteration 1: PAUSE (Large drift DEV-007, AC-5.3 unmet on Cursor). Resolved against the contract (reject → recode); no User Challenge, since the choice keeps the contract. Iteration 2: PASS.
- Gate 0 arch-check: pass. Gate 2: `bash -n` clean. Gate 2.5: cross-component. review-override: unverifiable (no coverage report). Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable. Gate 4 authenticity: `test_imports_no_source`, the known false positive for bash tests (open issue `.writ/issues/improvements/2026-09-03-test-integrity-authenticity-flags-every-bash-test.md`); carried on the pre-fix proofs. Not DEGRADED. Gate 4.5: app-verify unverifiable (no recipe). Gate 5: docs-check unverifiable.
- Evaluator residuals: after a fallback run, an unedited but outdated file shows as "Preserved (no baseline)" every run until the user deletes it or uses `--force` (conservative by design); the no-manifest notice says Cursor files are treated conservatively but they are still updated there (pre-existing); the `core.autocrlf` blob mismatch errs toward keeping files.

### Deviations from Spec

- **[DEV-006] A path rm cannot remove keeps its manifest line** — Severity: Small
  - Spec said: no Removed line, not counted.
  - Reality: also keeps the line so the next run retries.
  - Resolution: auto-amended (spec-lite S5).
- **[DEV-007] Cursor units on an unresolved legacy manifest** — Severity: Medium (Large at iteration 1)
  - Spec said: keep only the Codex line and behave as with no manifest; differing files preserved.
  - Reality: Cursor's no-baseline update overwrote customized units; recoded so a unit with no baseline is preserved whenever a manifest exists.
  - Resolution: rejected at iteration 1, recoded, accepted at iteration 2.
- **[DEV-008] A legacy run that ends "Already up to date" writes no header manifest** — Severity: Small
  - Resolution: accepted; the repair repeats until a run rewrites.
- **[DEV-009] The recorded version must be 4-40 lowercase hex** — Severity: Small
  - Resolution: auto-amended (spec-lite S5).
