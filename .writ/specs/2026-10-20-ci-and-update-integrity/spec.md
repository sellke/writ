# CI and Update Integrity

> **Status:** Not Started
> **Created:** 2026-10-20
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Phase:** 13 — Subtract and Repair ([roadmap](../../product/roadmap.md), [ADR-030](../../decision-records/adr-030-contract-verifier-boundary-front-door.md))
> **Origin:** Phase 13 decomposition pre-pass (`/implement-phase 13`, 2026-10-20). Closes `.writ/issues/bugs/2026-10-12-update-deletes-modified-stale-files.md` and `.writ/issues/bugs/2026-10-12-codex-config-baseline-dropped-on-update.md`.

## Specification Contract

*Fields marked (amended) reflect the Contract Amendment below. The original wording is kept in the amendment block.*

**Deliverable (amended):** CI runs every test suite on every PR. `scripts/install.sh` and `scripts/update.sh` stop losing user-authored files, user edits, and the Codex config baseline.

**Must Include (amended):** Each install and update fix is proven by a test that fails against the pre-fix scripts and passes after.

**Hardest Constraint:** The bash tests create temp git repos and run install/update. Writ is developed on macOS, and some tests may assume BSD userland (for example `stat -f`, `date -r`). CI must run them reliably. Choosing the runner OS (`ubuntu-latest` vs `macos-latest`, or per suite) is an implementation decision the CI story makes with evidence: run the suite and inspect it for BSD-only calls.

**🎯 Experience Design:**
- A developer opens a PR. CI runs `eval.sh`, `gen-skill.sh --check` (existing), `pytest` on Python 3.9, and every bash test. Any red suite fails the job.
- A user runs update. A locally modified file that upstream no longer ships is kept and warned about on every run. The Codex config baseline line is kept.
- *(amended)* A user's own files in Writ's folders (`.writ/docs/tech-stack.md`, `scripts/deploy.sh`, `.claude/commands/my-own.md`) are never recorded, never called stale, and never removed. A customized Writ file is preserved on every later update, not overwritten.

**📋 Business Rules:**
1. A locally modified file that upstream no longer ships is kept, with a stale warning naming it, on every `update.sh` run, in every category (commands, agents, skills, `.writ/docs`, scripts), until the user deletes it. Unmodified stale files are still removed. (Today `write_copy_manifest` re-records the kept file from its local copy, so run 2 deletes it; `scripts/` alone carries the old baseline via `STALE_KEPT_ENTRIES`. Fix direction from the issue: carry the old baseline forward for every category and stop re-recording a stale path from its local copy; widen the warning.)
2. The `.codex/config.toml.baseline` manifest line survives `update.sh` unchanged. (Today `write_copy_manifest` truncates the manifest with `cat > "$target"` before `manifest_hash_for` reads it. `scripts/unlink.sh` reads before truncating; copy that pattern.)
3. `.github/workflows/eval.yml` runs `uv run --python 3.9 pytest` (uv installed with `astral-sh/setup-uv`) and every `scripts/tests/test_*.sh`, each failing the job on failure, alongside the existing steps.
4. *(amendment 1)* `install.sh` and `update.sh` record manifest baselines only for paths upstream ships (the install set), never for user-authored files in the tracked folders. A user-authored file is never recorded, never treated as stale, and never removed, on the first or any later update.
5. *(amendment 2)* A preserved, locally customized file keeps its previous baseline. It is not re-baselined to its local hash, so a later upstream change is detected as a preserve, not a silent overwrite. This matches `update.sh`'s header ("Files you've customized are never overwritten").
6. *(amendment 3)* Codex stale skills are removed from the folder they live in (`.agents/skills/…`), not `.codex/skills/…`. `🗑  Removed:` is printed only when a file was removed.
7. *(amendment 4)* `commands/update-writ.md` Step 7 and its frontmatter line about every kept file getting a fresh baseline are corrected to match.

**Success Criteria (amended):** Every new install and update test fails on the pre-fix scripts and passes after. The workflow runs all three suites. Local pytest, bash tests, and eval pass. Each of the two issue files gets a `## Resolution` section naming the fix, written as the last task of the story that fixes it.

**Scope Boundaries (amended):**
- Included: `scripts/update.sh` (`write_copy_manifest`, `detect_stale_files`, `manifest_hash_for`, `manifest_files`, the warning path, the stale-removal block, and a new legacy-baseline step); `scripts/install.sh` `write_copy_manifest` and the two `append_manifest_*` helpers that only it calls; `.github/workflows/eval.yml`; new tests under `scripts/tests/`; `commands/update-writ.md` frontmatter `outcome` and exit criteria, Steps 3, 6, and 7, and Completion, where they misdescribe the fixed behavior.
- Excluded: `unlink.sh`; every other `install.sh` function; an OS matrix beyond what the bash tests need; any change to which files ship.

### Contract Amendment — 2026-10-20 (maintainer-approved)

The maintainer widened the spec to fix the update data-loss class found while grounding. Grounding probes ran on 2026-10-20 in temp projects (see `sub-specs/technical-spec.md` → ## Current State):
- `install.sh` recorded pre-existing `.writ/docs/tech-stack.md`, `scripts/deploy.sh`, and `.claude/commands/my-own.md`, and the first update removed all three.
- A user-written `.claude/commands/review.md` that install preserved was overwritten by the first update that changed it upstream.

1. Baselines are recorded only for paths upstream ships, in `update.sh` and in `install.sh`'s `write_copy_manifest`, which has the same flaw. User-authored files are never recorded, stale, or removed.
2. A preserved customized file keeps its previous baseline.
3. Codex stale skills are removed from `.agents/skills`. "Removed" is printed only when a file was removed.
4. `commands/update-writ.md` Step 7 and the frontmatter re-baseline lines are corrected.

Each fix is proven by a test that fails on the pre-fix scripts.

Original wording, superseded above:
- Deliverable: "CI runs every test suite on every PR, and `scripts/update.sh` stops losing user edits and the Codex config baseline."
- Must Include: "each update fix is proven by a test that fails against the pre-fix `update.sh` and passes after."
- Success: "the two new update tests fail on pre-fix `update.sh` and pass after."
- Scope in: "`scripts/update.sh` (`write_copy_manifest`, `detect_stale_files`, `manifest_hash_for`, warning path), `.github/workflows/eval.yml`, new tests under `scripts/tests/`, wording in `commands/update-writ.md` Steps 3/6 only if it now misdescribes behavior."
- Scope out: "`install.sh`, `unlink.sh`, an OS matrix beyond what the bash tests need, any change to which files ship."

**Derived requirement (authoring decision; flag for review):** Amendment 1 says user files are safe "on the first or any later update". Existing manifests were written by the pre-fix scripts and already record user files and re-baselined customizations. To keep the first fixed update from deleting or overwriting them, `update.sh` must treat a manifest without the new `# baselines: shipped` header as legacy. It rebuilds that manifest's baselines from upstream at the manifest's recorded `# version:`, fetching history once if the clone is shallow. When that version can't be resolved, it falls back to its existing no-manifest behavior. Story 5 owns this. The cheaper alternative is to never remove anything a legacy manifest calls stale. It was rejected because Writ files retired in this release, such as `commands/design.md` (`2026-10-20-platform-neutral-names`), would then never leave existing installs.

**Stories (renumbered from the first draft for edit order):**
1. CI runs every suite.
2. Codex baseline survives update.
3. Baselines only for shipped paths; customized files keep their baseline.
4. Modified stale files are kept in every category.
5. Legacy manifests and stale removal paths.

Stories 2 through 5 are serial because they edit the same `update.sh` functions. Story 1 is independent.

**Test pattern:** reuse the second-run fixture in `scripts/tests/test_install_update_dev_scripts.sh`.

**⚠️ Technical Concerns (found while grounding, 2026-10-20):**
- `update.sh` exits early with "Already up to date" (`scripts/update.sh:1024-1038`) before it rewrites the manifest. A fixture whose run changes nothing else never exercises the manifest rewrite and passes on the pre-fix script. Every fixture must force a rewrite.
- Shipped-only recording (Story 3) removes the cause of the stale-file bug: a kept stale path is not shipped, so it is never re-recorded from its local copy. Story 4 then only needs the every-category warning and the carry-forward.
- Story 5 adds one network call to `update.sh`, a `git fetch --unshallow` of the Writ repo (4.9 MiB packed), only for a legacy manifest whose version is not in the shallow clone. A failed fetch falls back to conservative behavior.
- Residual risks after this spec are listed in `sub-specs/technical-spec.md` → ## Residual Risks (Not Fixed Here).

**💡 Recommendations:**
- Write each test first and run it against the unchanged scripts. Record the failing line in the story's What Was Built. That run is the "fails against pre-fix" evidence.
- Keep the stale warning text byte-identical to today's (`⚠️  Stale (no longer shipped, locally modified — kept): <path>`). `test_install_update_dev_scripts.sh` and `2026-10-20-platform-neutral-names` match it.

## Experience Design

### Who uses it

- **The maintainer and contributors** opening PRs against Writ. They need a red CI job when any suite fails, not only when `eval.sh` fails.
- **Users of installed projects** running `install.sh`, `update.sh`, or `/update-writ` (which mirrors `update.sh`). They need their own files and their edits to Writ files to survive every install and update, and the Codex install-once config to stay recognized.

### User Journey

1. A developer opens a PR. The `Eval Tier 1` workflow runs the SKILL.md check, `eval.sh`, `pytest` on Python 3.9, and every `scripts/tests/test_*.sh`. One red suite turns the job red, and the log names the failing test.
2. A user runs `/initialize`, which writes `.writ/docs/tech-stack.md`. They also keep `scripts/deploy.sh` and their own `.claude/commands/my-own.md`. No update ever records, mentions, or removes these files.
3. The user edits `.claude/commands/status.md`. Each update that changes `status.md` upstream reports it as preserved and leaves it alone.
4. A later release drops `commands/old-cmd.md`, which the user had edited. Every update prints `⚠️  Stale (no longer shipped, locally modified — kept): commands/old-cmd.md` until the user deletes it.
5. A user upgrades from a pre-fix release. The first fixed update leaves their own files and edits alone, removes retired Writ files they never edited, and writes a manifest with the new header.
6. A Codex user runs `update.sh`. The `.codex/config.toml.baseline` line keeps its hash. A retired skill they never edited leaves `.agents/skills/`.

### State Catalog

| State | What the developer or user sees |
|---|---|
| PR, all suites green | One green job. Each suite is its own step. |
| PR, one suite red | Red job. The failing step's log names the test (pytest summary, or `FAIL scripts/tests/<name>.sh`). |
| PR, several bash tests red | One `FAIL` line per failing test. The step exits non-zero after running every test. |
| Install into a project with user files in tracked folders | Files untouched. The manifest has no line for them and starts with `# baselines: shipped`. |
| Install over a user file at a shipped path | The file is preserved ("no baseline"). No manifest line, so later updates keep preserving it. |
| Update, user-authored file in a tracked folder | Nothing printed about it. Never recorded, never removed. |
| Update, customized shipped file, upstream changes it again | `⚡ Preserved: <path> (local modifications)` on every such update. The baseline is unchanged. |
| Update, unmodified stale file | `🗑  Removed: <path>`. The file and its manifest line are gone. |
| Update, modified stale file (any category) | The stale warning; the file is byte-identical; the manifest keeps its original baseline. |
| Update, second and later runs | The same stale warning every run, including dry runs and "Already up to date" runs. |
| User deletes a kept stale file | No warning on the next update, and its line drops. |
| Update from a legacy manifest, version found | User files are left alone, retired unedited Writ files are removed, and customizations are preserved. The new manifest has the header. |
| Update from a legacy manifest, version not found | One notice. Nothing that differs from upstream is removed or overwritten. The new manifest has the header. |
| Codex update | The `.codex/config.toml.baseline` line is unchanged. A retired unedited skill is removed from `.agents/skills`. |
| Codex manifest with no baseline line | Update writes none and exits 0. |

### Interaction Patterns

- Stale and removal lines name the manifest-relative path (`commands/x.md`, `skills/x/SKILL.md`, `.writ/docs/x.md`, `scripts/x.py`).
- `🗑  Removed: <path>` appears only for a path that is gone from disk after the run.
- The legacy fallback notice says why it fell back (version unknown, or not found upstream) and that differing files were preserved.

## Business Rules (Expanded)

1. **The shipped set is the install set.** It contains:
   - top-level `scripts/*` that pass `is_shippable_script`
   - `.writ/docs/*.md`
   - `commands/*.md` minus unshipped lean siblings
   - `$AGENTS_SRC/$AGENT_FILE_GLOB`, recorded as `agents/<name>`
   - `skills/*/SKILL.md`
   - the platform units: Cursor `rules/writ.mdc` and `system-instructions.md`; `CLAUDE.md.writ-block`; `AGENTS.md.writ-block`; `.codex/config.toml.baseline`

   Both scripts compute it from the source tree (`$WRIT_SRC`), never from the project's folders.
2. **The manifest records shipped paths plus kept stale entries, nothing else.** A file in a tracked folder that upstream does not ship gets no line, and a path with no line is never stale. Manifests written by the fixed scripts carry the header line `# baselines: shipped`.
3. **The baseline value.** If the local file equals upstream after the run, record the upstream hash. If it was preserved (it differs from upstream), record its previous baseline, or no line when there was none. A Writ block that was preserved, or a Cursor rule that was preserved, follows the same rule.
4. **Stale is defined as before.** A stale path is one the manifest lists that upstream no longer ships: the upstream file is absent, it is a lean sibling update does not ship, or it is a script the filter rejects.
5. **Unmodified stale files are removed.** That includes Codex skills, from `$SKILLS_DIR` (`.agents/skills`). `🗑  Removed: <path>` is printed only when the file is gone after `rm`.
6. **Modified stale files are kept, in every category.** The file stays byte-identical. Each run prints the stale warning, including dry runs and "Already up to date" runs. The manifest keeps one line with the original baseline. When the user deletes the file, its line drops.
7. **Dry runs report and never write.** `--force` does not change stale handling.
8. **The Codex baseline is read before the manifest is truncated.** With no prior line, none is written.
9. **Legacy manifests.** A manifest without `# baselines: shipped` was written by pre-fix scripts. `update.sh` resolves its `# version:` in the upstream clone, running `git fetch --unshallow` once if the clone is shallow.
   - **Version found:** baselines for this run come from upstream content at that version. A path that did not exist upstream at that version is a user file: untracked, never stale. `.codex/config.toml.baseline` is kept as recorded.
   - **Version not found** (`unknown`, absent upstream, or fetch failed): the run behaves as if there were no manifest, except that `.codex/config.toml.baseline` is kept. Differing files are preserved, nothing is stale, and one notice is printed.
10. **`install.sh` writes the header** for a fresh install or over a manifest that already has it. Over a legacy manifest it writes none, so the next `update.sh` repairs it.
11. **CI fails on any red suite.** Each suite is its own step. The bash step counts failures and exits non-zero. The loop in `CLAUDE.md` (`|| echo "FAIL $t"`) always exits 0.
12. **Python 3.9 floor in CI**, via `uv run --python 3.9 pytest`, with `astral-sh/setup-uv` pinned to a major tag.
13. **Never run install.sh or update.sh against the Writ repo.** It is symlinked into `.claude/` and `.cursor/`. Tests and probes use temp directories only.

## Detailed Requirements

### Story 1: CI runs every suite
- `eval.yml` keeps its trigger, checkout, SKILL.md check, `eval.sh`, and report upload. It adds setup-uv, `uv run --python 3.9 pytest`, and a bash step that fails on any red test.
- The runner OS is chosen with evidence. A grounding scan on 2026-10-20 found no BSD-only calls.
- New `scripts/tests/test_ci_workflow.py` checks the steps and executes the bash step's block against fixtures.

### Story 2: Codex baseline survives update
- `write_copy_manifest` reads the `.codex/config.toml.baseline` hash before truncating, following `scripts/unlink.sh:199-204`.
- New `scripts/tests/test_update_codex_config_baseline.sh`.
- `## Resolution` on the Codex issue.

### Story 3: Baselines only for shipped paths; customized files keep their baseline
- In `update.sh`, snapshot the old baselines into a temp file before truncation. `write_copy_manifest` iterates the shipped set from `$WRIT_SRC`, applies Business Rule 3, and writes the header.
- In `install.sh`, `write_copy_manifest` gets the same change, plus the header rule (Business Rule 10).
- New `scripts/tests/test_manifest_shipped_baselines.sh` covers install and update on Claude Code, and `rules/writ.mdc` on Cursor.

### Story 4: Modified stale files kept in every category
- `detect_stale_files` warns and records `STALE_KEPT_ENTRIES` for every category. `write_copy_manifest` appends each kept entry once. After Story 3, kept paths are not in the shipped set and so are never re-recorded.
- New `scripts/tests/test_update_kept_stale_files.sh`: five categories, three runs, a dry run.
- `commands/update-writ.md`: frontmatter `outcome` and exit criterion, and Steps 3, 6, and 7 (including the header in the manifest template), and Completion, describe the fixed baseline behavior.
- `## Resolution` on the stale-files issue.

### Story 5: Legacy manifests and stale removal paths
- `update.sh` gets a legacy-baseline step (Business Rule 9), feeding `manifest_hash_for` and `manifest_files` for the run.
- The stale-removal block removes Codex skills from `$SKILLS_DIR` and prints "Removed" only for paths that are gone.
- `commands/update-writ.md` Step 3 gets one sentence on legacy manifests.
- New `scripts/tests/test_update_legacy_manifest.sh`.

## Implementation Approach

- **One baseline source per run.** At the start of the run, `update.sh` writes the baselines it trusts to a temp file. That is the manifest itself, the repaired legacy map, or only the Codex config line. `manifest_hash_for` and `manifest_files` read that file, so truncating the manifest never affects a lookup. Story 2's read-before-truncate fix is the first step; Story 3 generalizes it.
- **Iterate the source, not the project.** `write_copy_manifest` loops over `$WRIT_SRC` paths with the same filters the overlay scans use (`is_shippable_script`, `is_unshipped_lean_sibling`, `AGENT_FILE_GLOB`).
- **Tests run the real scripts in temp projects.** They use a committed source copy of the working tree (`test_install_update_dev_scripts.sh:61-72`) and `WRIT_REPO` pointed at it. `WRIT_REPO=file://…` forces a shallow clone, because git ignores `--depth` for plain local paths.
- **Legacy fixtures are built, not recorded.** Install with the fixed `install.sh`, delete the `# baselines: shipped` line, and append the entries a pre-fix script would have written. This needs no pre-fix scripts at test time, so the test keeps working in CI after the fix lands.
- **CI runner:** `ubuntu-latest` unless Story 1's evidence shows a suite needs macOS.
- **Ordering:** Story 1 is independent. Then Story 2 → Story 3 → Story 4 → Story 5.
- **Verification:** `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` (outside any sandbox). Then the first CI run on the phase PR.
