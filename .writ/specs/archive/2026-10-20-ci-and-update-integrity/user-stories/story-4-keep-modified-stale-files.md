# Story 4: Keep Modified Stale Files in Every Category

> **Status:** Completed ✅
> **Commit:** 3960d723a092dd54b2d055a09e13c3ccbcfcde1c
> **Priority:** High
> **Dependencies:** Story 3

## User Story

**As a** user of a project with Writ installed
**I want to** have `update.sh` keep, and warn about, any file I edited that upstream stopped shipping, on every run, until I delete it
**So that** my edits are never lost on the second update, whatever folder the file lives in

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [x] Given a temp Claude Code project installed from a source that ships `commands/zz-kept.md`, `claude-code/agents/zz-kept.md`, `skills/zz-kept/SKILL.md`, `.writ/docs/zz-kept.md`, and `scripts/zz_kept.py`, each then edited locally, and a later source that drops all five, when `update.sh` runs three times and each run rewrites the manifest, then all five local files exist and are byte-identical after every run `[AC-4.1]`
- [x] Given the same project, when each of the three updates and a `--dry-run` runs, then each output contains `⚠️  Stale (no longer shipped, locally modified — kept): <path>` for all five manifest paths (`commands/zz-kept.md`, `agents/zz-kept.md`, `skills/zz-kept/SKILL.md`, `.writ/docs/zz-kept.md`, `scripts/zz_kept.py`), and the dry run leaves the manifest byte-identical `[AC-4.2]`
- [x] Given the manifest after each run, when it is read, then each kept path has exactly one line carrying the hash recorded at install, not the local hash; an unmodified `commands/zz-clean.md` dropped by the same source is removed on run 1 with `🗑  Removed: commands/zz-clean.md` and leaves the manifest; and after the user deletes one kept file, the next run prints no warning for it and drops its line `[AC-4.3]`
- [x] Given `scripts/tests/test_update_kept_stale_files.sh` and the pre-fix `update.sh`, when the test runs, then it fails, naming a kept file the update removed; after the fix it passes, and `scripts/tests/test_install_update_dev_scripts.sh` still passes unchanged `[AC-4.4]`
- [x] Given `commands/update-writ.md` and the issue `.writ/issues/bugs/2026-10-12-update-deletes-modified-stale-files.md`, when the story closes, then the frontmatter `outcome` (line 5) and exit criterion (line 10), Steps 3, 6, and 7 (lines 124, 194, 199-223, with `# baselines: shipped` in the Step 7 template), and Completion (lines 286-288) all say three things: only shipped paths get baselines, a kept customized or stale file keeps its previous baseline, and a modified stale file is flagged on every run. The issue ends with a `## Resolution` section naming the fix and the test `[AC-4.5]`

## Implementation Tasks

- [x] 4.1 Write a new `scripts/tests/test_update_kept_stale_files.sh`, reusing the committed-source-copy, `plant`/`check_update`, `fail`, and `hash_file` patterns of `scripts/tests/test_install_update_dev_scripts.sh` (lines 19-39, 61-72, 116-158). Cover the five categories, three manifest-rewriting runs, the dry run, the unmodified removal, and delete-then-run. Run it against the unchanged `scripts/update.sh`, confirm it fails, and save the failing line for What Was Built `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`
- [x] 4.2 In `detect_stale_files` (`scripts/update.sh:821-877`), remove the `category = scripts` condition from the modified branch (`868-874`), so every category prints the existing warning text and appends `<baseline>  <path>` to `STALE_KEPT_ENTRIES` `[AC-4.2]`
- [x] 4.3 In `write_copy_manifest`, confirm that each `STALE_KEPT_ENTRIES` path is written exactly once with its old baseline. After Story 3 no kept path is in the shipped set, so the "already recorded" check at the end of the function is only a duplicate guard. Keep it or simplify it, but do not drop the entry `[AC-4.1, AC-4.3]`
- [x] 4.4 Edit `commands/update-writ.md` so the frontmatter `outcome` and exit criterion, Steps 3, 6, and 7, and Completion match AC-4.5. Add the `# baselines: shipped` header line to the Step 7 manifest template. Change no other section `[AC-4.5]`
- [x] 4.5 Verify the fix: `bash scripts/tests/test_update_kept_stale_files.sh` and `bash scripts/tests/test_install_update_dev_scripts.sh` pass. Re-prove the pre-fix failure by copying the new test into a temp `git archive <pre-fix commit>` extract and running it there; this leaves git state unchanged `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`
- [x] 4.6 Verify the regression surface: `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` (no `FAIL` lines), and `bash scripts/eval.sh` outside any sandbox; all pass `[AC-4.4, AC-4.5]`
- [x] 4.7 Append `## Resolution` to `.writ/issues/bugs/2026-10-12-update-deletes-modified-stale-files.md`, naming the shipped-only recording (Story 3), the `detect_stale_files` change, and `scripts/tests/test_update_kept_stale_files.sh` `[AC-4.5]`

## Notes

- **Run 1 must rewrite the manifest.** `update.sh` exits "Already up to date" before `write_copy_manifest` (`scripts/update.sh:1024-1038`) when nothing is actionable. If a kept file is the only change, the pre-fix script keeps it, and the test proves nothing. `commands/zz-clean.md` (unmodified, dropped) forces a rewrite on run 1. An unrelated upstream edit to a locally unmodified shipped command forces runs 2 and 3.
- **The shippable-named script case.** Before the fix, `scripts/zz_kept.py` gets a warning on run 1 and is removed on run 2, because the pre-fix `append_manifest_shippable_scripts` re-records it. The fixture covers this on purpose.
- **Paths.** The agent's upstream path is `claude-code/agents/zz-kept.md` (`AGENTS_SRC`), with manifest path `agents/zz-kept.md`. The skill's local path is `.claude/skills/zz-kept/SKILL.md`, with manifest path `skills/zz-kept/SKILL.md`. Scripts and `.writ/docs` resolve at the project root.
- **Keep the warning text.** `test_install_update_dev_scripts.sh:100` and `2026-10-20-platform-neutral-names` match `⚠️  Stale (no longer shipped, locally modified — kept): <path>` byte for byte.
- **Wording now covers line-level detail.** Line numbers are from 2026-10-20. Re-read the file before editing. The old Completion line says the manifest "re-baselines, so the next update compares against what is on disk". Under the fix, a kept customized file keeps its previous baseline, so the next update asks again when upstream differs.
- **Never run `install.sh` or `update.sh` against the Writ repo.** It is symlinked into `.claude/` and `.cursor/`. Run everything in temp directories. The test does `git init`, so run it outside any sandbox.
- **Other Phase 13 work touches `update.sh`.** The Cuts feature removes `is_unshipped_lean_sibling`, which `detect_stale_files` calls at `859-860`. Run `git diff scripts/update.sh` before editing, and change only the targeted lines.
- **Citations.** Name this spec (`2026-10-20-ci-and-update-integrity`) in the comment that carries `AC-4.n` tokens.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Rewrite manifest (kept stale path), Stale removal (user deleted the kept file), Update early exit (only kept stale files differ)] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Kept stale file across updates] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Rule 4 (stale definition), Rule 5 (unmodified removed), Rule 6 (modified kept in every category), Rule 7 (dry run, `--force`), Rule 13 (temp dirs only)] — spec.md → ## Business Rules (Expanded)
- **Experience:** [State Catalog rows "Update, modified stale file", "Update, second and later runs", "User deletes a kept stale file"] — spec.md → ## Experience Design → ### State Catalog
- **Technical:** technical-spec.md → ## Story 4 Design: Kept stale files

---

## What Was Built

**Implementation Date:** 2026-10-20

### Files Created

1. **`scripts/tests/test_update_kept_stale_files.sh`** (233 lines, about 45 s) — source A ships five kept fixtures (`commands/zz-kept.md`, `claude-code/agents/zz-kept.md`, `skills/zz-kept/SKILL.md`, `.writ/docs/zz-kept.md`, `scripts/zz_kept.py`) and an unmodified `commands/zz-clean.md`. Install, edit the five, then run against a source that drops all six. Three rewriting updates (`check_rewritten`), an "Already up to date" run, a dry run with a change pending, and a delete-then-update. After each: kept files byte-identical, the exact warning for all five manifest paths, one manifest line per kept path with the install-time hash; `zz-clean.md` removed on run 1; the dry and up-to-date runs leave the manifest byte-identical; the deleted file gets no warning and its line drops. A doc check covers the Step 7 template header and the four retired claims. [AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]

### Files Modified

- **`scripts/update.sh`** — `detect_stale_files`: the modified branch is now `else`, so every category prints the unchanged warning text and appends `<baseline>  <path>` to `STALE_KEPT_ENTRIES`. `write_copy_manifest`: comment on the carry-forward only; the duplicate guard stays. [AC-4.1, AC-4.2, AC-4.3]
- **`commands/update-writ.md`** — frontmatter `outcome` and the line-10 exit criterion, Step 3 "Detect stale files", Step 6 item 6, Step 7 (prose, `# baselines: shipped` in the template after the `# Tracks…` line, a kept-stale template line, four bullets on baseline values), and Completion. No other section changed. [AC-4.5]
- **`.writ/issues/bugs/2026-10-12-update-deletes-modified-stale-files.md`** — appended `## Resolution`. [AC-4.5]

### Implementation Decisions

1. **Task 4.3 check** — a kept stale path cannot be in the shipped set, because the stale conditions (upstream absent, unshipped lean sibling, filter-rejected script) are the walk's own filters. The duplicate guard only fires when the old manifest lists a path twice; that case writes one line and prints the warning twice (left as is).
2. **Doc check in the test** — gives AC-4.5 a test citation for `ac-trace.py`.

### Test Results

**Verification:** test-first, then regression and full suites.

- Pre-fix: on `git archive ce2f049` (lane HEAD before this story) and on `git archive 953f47e` (before the spec), both exit 1 with `FAIL: update 1: no stale warning for the kept commands/zz-kept.md. Stale lines: ⚠️  Stale (no longer shipped, locally modified — kept): scripts/zz_kept.py;🗑  Removed: commands/zz-clean.md` (orchestrator re-proof). On `953f47e`, a variant with only the existence checks fails with `FAIL: update 2: update removed the kept commands/zz-kept.md` (evaluator).
- Mutations caught (coding agent): dropping the `STALE_KEPT_ENTRIES` append; skipping the warning on dry runs.
- After: `PASS test_update_kept_stale_files`; `test_install_update_dev_scripts.sh` passes unchanged. Passes under bash 3.2 and 5.3.
- Full suites (orchestrator run): `uv run --python 3.9 pytest` → `2623 passed, 2 skipped in 160.11s`; bash loop → 38 run, 0 failed; `bash scripts/eval.sh` → exit 0, `Findings: 0`, `Run errors: 0`; `gen-skill.sh --check` → `pass`.
- Evaluator probes: `--force` leaves stale handling unchanged (Rule 7); upstream re-adding `agents/zz-kept.md` gives `⚡ Preserved` with the carried baseline; reverting a kept file to its install-time content removes it.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-004, DEV-005)
- **Security:** None.
- **Boundary Compliance:** 0 crossings; route evaluator-agent.
- Gate 0 arch-check: pass. Gate 2: `bash -n` clean; `lint-skill.sh commands/update-writ.md` passes. Gate 2.5: cross-component. review-override: unverifiable (no coverage report). Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable. Gate 4 authenticity: `test_imports_no_source`, the known false positive for bash tests (open issue `.writ/issues/improvements/2026-09-03-test-integrity-authenticity-flags-every-bash-test.md`); carried on the pre-fix proof and mutations. Not DEGRADED. Gate 4.5: app-verify unverifiable (no recipe). Gate 5: docs-check unverifiable.
- Evaluator residuals: a build with Story 4 but not Story 5 would stamp the header over a legacy manifest and leave a permanent stale warning on an edited user file the old scripts recorded; Story 5 ships in this spec. Step 7 bullet 2 and Completion say a kept customized file is asked about again "when upstream changes" it; it is in fact reported every run while it differs from upstream.

### Deviations from Spec

- **[DEV-004] Pre-fix failure names a missing warning, not a removal** — Severity: Small
  - Spec said: AC-4.4 names "a kept file the update removed".
  - Reality: after Story 3 the pre-fix script drops the line instead of removing the file; the test fails on the missing warning.
  - Resolution: accepted.
- **[DEV-005] Steps 3 and 6 state two of the three doc claims** — Severity: Small
  - Spec said: each edited section states all three claims.
  - Reality: the two stale-file passages omit the customized-file claim; four sections state all three.
  - Resolution: accepted.
