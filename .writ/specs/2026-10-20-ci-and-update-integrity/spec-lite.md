# CI and Update Integrity (Lite)

> Source: .writ/specs/2026-10-20-ci-and-update-integrity/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** CI runs every suite on every PR. `install.sh` and `update.sh` stop losing user files, user edits, and the Codex config baseline (contract amended 2026-10-20).

**Implementation Approach:**
- S1 CI: setup-uv (pinned), `uv run --python 3.9 pytest`, and a bash step that counts failures and exits non-zero. Runner `ubuntu-latest` unless evidence says otherwise.
- S2: read `.codex/config.toml.baseline` before `cat > "$target"`, as `unlink.sh:199-204` does.
- S3: per-run baseline file read by `manifest_hash_for`/`manifest_files`. `write_copy_manifest` (update and install) iterates the shipped set from `$WRIT_SRC`: upstream hash if local = upstream, else the previous baseline or none. Header `# baselines: shipped`.
- S4: `detect_stale_files` warns and carries the old baseline in every category.
- S5: a header-less manifest is legacy. Rebuild baselines from upstream at `# version:` (`--unshallow` once if needed). Unresolvable → no-manifest behavior plus a notice. Remove Codex skills from `$SKILLS_DIR`. Print "Removed" only when the file is gone.
- Tests first; each fails on the unchanged scripts.

**Files in Scope:**
- `.github/workflows/eval.yml`, `scripts/tests/test_ci_workflow.py` (S1)
- `scripts/update.sh`: `manifest_hash_for`/`manifest_files` `155-162`, `write_copy_manifest` `164-247`, `detect_stale_files` `821-877`, removal `1114-1129`, new legacy step (S2–S5)
- `scripts/install.sh`: `write_copy_manifest` `639-705` and its `append_manifest_*` `1006-1022` only (S3)
- `commands/update-writ.md`: frontmatter, Steps 3/6/7, Completion (S4, S5)
- New tests: `test_update_codex_config_baseline.sh` (S2), `test_manifest_shipped_baselines.sh` (S3), `test_update_kept_stale_files.sh` (S4), `test_update_legacy_manifest.sh` (S5)

**Error Handling:**
- Only a kept file differs → update exits before rewriting the manifest. Fixtures must force a rewrite.
- No prior baseline → write no line. A failed `rm` → no "Removed" line.

**Integration Points:**
- Keep the stale warning text byte-identical (`test_install_update_dev_scripts.sh:100`, platform-neutral-names).
- Out of scope: `unlink.sh`, other `install.sh` functions, which files ship. Never run install/update against the Writ repo; use temp dirs.

---

## For Review Agents

**Acceptance Criteria:**
1. The workflow keeps its steps and adds setup-uv, pytest 3.9, and a bash step that fails on any red test; the runner choice is evidenced `[AC-1.1, AC-1.2, AC-1.3]`
2. The Codex baseline line survives two updates and a dry run; with none, none is written `[AC-2.1, AC-2.2, AC-2.3]`
3. Install and update never record, call stale, or remove user-authored files; header written `[AC-3.1, AC-3.2]`
4. Customized files keep their install-time baseline and are preserved across upstream changes `[AC-3.3]`
5. Every shipped path has exactly one correct line `[AC-3.4]`
6. Modified stale files in five categories are kept, warned every run, with one old-baseline line; unmodified ones are removed `[AC-4.1, AC-4.2, AC-4.3]`
7. Legacy manifests: user files untouched, retired files removed, customizations preserved; unresolvable → nothing removed or overwritten `[AC-5.1, AC-5.2, AC-5.3]`
8. Codex stale skills are removed from `.agents/skills`; each "Removed" path is gone `[AC-5.4]`
9. Every new test fails on pre-fix scripts and passes after; suites green; docs and issues updated `[AC-1.4, AC-2.4, AC-3.5, AC-4.4, AC-4.5, AC-5.5]`

**Business Rules:**
- Baselines only for the shipped set. Preserved → previous baseline or none.
- Stale = in the manifest and no longer shipped. Modified → kept and warned; unmodified → removed.
- No header = legacy: repair from upstream at the recorded version, or fall back conservatively.
- Any red suite fails the CI job.

**Experience Design:**
- Entry: a PR opens; a user installs or updates.
- Happy path: suites green; user files and edits survive every run.
- Moment of truth: the first fixed update on an old install deletes nothing of the user's.
- Feedback: the stale warning; `FAIL <test>`; the legacy notice.
- Error: a red step names the failing test.

---

## For Testing Agents

**Success Criteria:**
1. Each new install/update test fails on the pre-fix scripts and passes after.
2. `test_ci_workflow.py` proves the bash step fails on a red fixture.
3. `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` pass.

**Shadow Paths to Verify:**
- **Happy path:** user files untracked; customizations preserved; kept stale files warned on runs 1–3.
- **Nil input:** no Codex baseline, no previous baseline, or version `unknown` → no line, or fallback.
- **Empty input:** no user files, or no stale paths → manifest equals the shipped set.
- **Upstream error:** clone or `--unshallow` fails → no write, or fallback.

**Edge Cases:**
- A user file present before install, or at a shipped path (`review.md`).
- A shallow clone needs `WRIT_REPO=file://…`; a plain path ignores `--depth`.
- Upstream re-adds a kept path → preserved via the carried baseline.

**Test Strategy:**
- Committed source copy, temp projects, `WRIT_REPO`. Build legacy manifests by stripping the header from a fixed install.
- Prove pre-fix failure before the fix; re-prove from a `git archive` extract.
