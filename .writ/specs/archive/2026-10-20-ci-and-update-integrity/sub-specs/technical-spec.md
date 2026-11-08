# Technical Spec: CI and Update Integrity

> Spec: [`../spec.md`](../spec.md) · Stories: [`../user-stories/README.md`](../user-stories/README.md)

*Amended 2026-10-20 (maintainer-approved contract amendment). The section "Adjacent Defects (Not Fixed Here)" is gone. Items 1–4 of it are now Story 3 (user files, customized baselines, and `install.sh`), Story 5 (Codex skill removal and legacy manifests), and Story 4 (`update-writ.md` wording). What remains is under ## Residual Risks.*

## Current State (audit, 2026-10-20)

### CI

`.github/workflows/eval.yml` (29 lines) runs one job, `eval`, on `ubuntu-latest`, triggered by `pull_request` and `push`. Its steps:

- `actions/checkout@v4` with `fetch-depth: 0`
- `bash scripts/gen-skill.sh --check`, asserting the first line is `pass`
- `bash scripts/eval.sh --report=eval-report.md`
- upload `eval-report.md` on failure

It runs neither pytest nor any `scripts/tests/test_*.sh`.

Portability evidence for the runner choice:

- A grep of `scripts/tests/*.sh` and the lifecycle and skill scripts found none of these BSD-only calls: `stat -f`, `date -r`, `sed -i ''`, `readlink -f`, `grep -P`, `md5`, `gdate`, `gsed`, `pbcopy`, `sw_vers`, `xcrun`, `mktemp -t`.
- `hash_file` falls back from `shasum` to `sha256sum`. Tests that commit set their own git identity.
- `eval.sh` already runs green on `ubuntu-latest`.
- Locally on macOS: 35 bash tests, 0 failures, about 106 s.

The bash loop in `CLAUDE.md` (`… || echo "FAIL $t"`) exits 0 even when a test fails.

### update.sh

| Site | Lines | Behavior today |
|---|---|---|
| `manifest_hash_for`, `manifest_files` | `155-162` | Read `$MANIFEST_FILE` on disk |
| `write_copy_manifest` | `164-247` | `cat > "$target"` at `167` truncates. It then records every local script that passes the filter (`append_manifest_shippable_scripts`, `667-675`), every local `.writ/docs/*.md` (`677-683`), and every local command, agent, and skill (`180-210`), all from local copies, shipped or not |
| Codex baseline | `225-234` | Looked up at `230`, after the truncation, so the line is dropped |
| Writ blocks, Cursor units | `212-229` | Recomputed or rehashed from local files, so a preserved block or rule is re-baselined |
| Kept-stale carry-forward | `236-246` | Skips paths already recorded (`243`), so a kept command, agent, skill, doc, or shippable-named script loses its old baseline |
| `detect_stale_files` | `821-877` | Warns and records `STALE_KEPT_ENTRIES` only when `category = scripts` (`868-874`) |
| Early exits | `1024-1038` | Exit before `write_copy_manifest` when nothing is actionable or only preserved files differ |
| Stale removal | `1114-1129` | `rm -f "$PLATFORM_DIR/$sf"` for skills (`1124`), wrong for Codex, whose `SKILLS_DIR` is `.agents/skills` (`86`). Prints `Removed` whatever `rm` did |
| Clone | `549-550` | `git clone --depth 1 "$WRIT_REPO"`. A plain local path ignores `--depth`; `file://` honors it |

### install.sh

| Site | Lines | Behavior today |
|---|---|---|
| `write_copy_manifest` | `639-705` | Same shape as `update.sh`: truncates, then records local files via `append_manifest_*` (`1006-1022`, called only at `653-654`) and the local command, agent, and skill folders |
| Overlay scans | `946-1132` | Same three-way logic as update. A user file at a shipped path with no baseline is preserved ("no baseline, assuming modified") |
| Codex config | `566-597`, `701` | Baseline captured before the write. Correct |
| Version | `740` | `git log -1 --format="%h"` of the source, or `unknown` |

### Probe results (temp projects, committed working-tree copy, 2026-10-20)

| Probe | Result |
|---|---|
| Modified stale `commands/old-cmd.md` | Run 1: kept, no warning. Run 2: removed |
| Modified stale `scripts/old-tool.py` (shippable name) | Run 1: warned as kept. Run 2: removed |
| Only a kept stale file differs | Both runs "Already up to date"; the file survives |
| Codex install, then update | `.codex/config.toml.baseline` lines: 1, then 0 |
| User files created after install (`tech-stack.md`, `deploy.sh`, `my-own.md`) | Recorded by update 1, removed by update 2 |
| The same files present before install | Recorded by install, removed by update 1 |
| User `review.md` present before install | Preserved by install with its local hash recorded, then overwritten by the first upstream change |
| Customized `commands/review.md`, update with another change | Re-baselined. The next upstream change overwrote it (`🔄 Update`) |
| Codex stale skill `skills/zz-old/SKILL.md` | `🗑  Removed:` printed, but the file is still in `.agents/skills` |

## Story 1 Design: CI

Target workflow shape. Names are suggestions; the test keys on commands, not step names.

```yaml
jobs:
  eval:
    runs-on: ubuntu-latest   # Story 1 records the evidence for this choice
    steps:
      - uses: actions/checkout@v4        # unchanged, fetch-depth: 0
      - name: Verify SKILL.md is up to date with manifest   # unchanged
      - name: Run Writ Eval Tier 1                           # unchanged
      - uses: astral-sh/setup-uv@<pinned major>
        if: ${{ !cancelled() }}
      - name: Run pytest (Python 3.9 floor)
        if: ${{ !cancelled() }}
        run: uv run --python 3.9 pytest
      - name: Run bash tests
        if: ${{ !cancelled() }}
        run: |
          fails=0
          for t in scripts/tests/test_*.sh; do
            echo "== $t"
            bash "$t" || { echo "FAIL $t"; fails=$((fails + 1)); }
          done
          echo "bash tests failed: $fails"
          [ "$fails" -eq 0 ]
      - name: Upload eval report   # unchanged, if: failure()
```

- `if: ${{ !cancelled() }}` lets later suites run after a failure. It is recommended, not required.
- On Linux, Actions runs a `run:` block with `bash -e {0}` unless `shell:` is set. Pin `setup-uv` to a major tag that exists when the story runs.
- If a bash test needs BSD userland, move that suite to a `macos-latest` job and write the reason in a comment. Add no matrix.

`scripts/tests/test_ci_workflow.py` (Python 3.9 stdlib, no YAML parser):

| Test | Assertion |
|---|---|
| Trigger | `on:` names `pull_request` |
| Existing steps kept | `bash scripts/gen-skill.sh --check` and `bash scripts/eval.sh` |
| uv and pytest | A `uses: astral-sh/setup-uv@v<N>` line, and `uv run --python 3.9 pytest` |
| Bash step | Its `run:` block iterates `scripts/tests/test_*.sh` |
| Fails on red | Run the extracted block with `bash -e` in a temp dir holding a passing and a failing `scripts/tests/test_*.sh`. Expect a non-zero exit, `FAIL scripts/tests/test_fail.sh`, and both tests run |
| Passes on green | Only passing fixtures: exit 0 |

## Story 2 Design: Codex baseline

In `write_copy_manifest`, before `cat > "$target"`:

```bash
local config_baseline=""
if [ "$PLATFORM" = "codex" ]; then
  config_baseline=$(manifest_hash_for ".codex/config.toml.baseline")
fi
```

The Codex block writes `$config_baseline` when it is non-empty.

Test: install Codex into a temp project. Then run two updates, each after an upstream change to a locally unmodified command, and a dry run. Each time, check that the baseline line is present once with the same hash and that `config.toml` is byte-identical. Nil case: delete the line, update, and expect none written and exit 0.

## Story 3 Design: Shipped-only baselines

**Per-run baseline file.** At the start of the run, copy the manifest's non-comment lines to a temp file, `BASELINES_FILE`, removed by the existing `cleanup` trap. `manifest_hash_for` and `manifest_files` read `BASELINES_FILE`. `manifest_version` and `manifest_mode` keep reading the manifest. This subsumes Story 2's single read. Story 5 changes only how the file is filled.

**Shipped set** (computed from `$WRIT_SRC`, with the overlay scans' own predicates):

| Manifest path | Source | Filter |
|---|---|---|
| `scripts/<f>` | `$WRIT_SRC/scripts/<f>` (top level) | `is_shippable_script` |
| `.writ/docs/<f>.md` | `$WRIT_SRC/.writ/docs/<f>.md` | — |
| `commands/<f>.md` | `$WRIT_SRC/commands/<f>.md` | not `is_unshipped_lean_sibling` |
| `agents/<f>` | `$WRIT_SRC/$AGENTS_SRC/<f>` | `$AGENT_FILE_GLOB` |
| `skills/<n>/SKILL.md` | `$WRIT_SRC/skills/<n>/SKILL.md` | — |
| `rules/writ.mdc`, `system-instructions.md` | `cursor/writ.mdc`, `system-instructions.md` | Cursor only |
| `CLAUDE.md.writ-block` / `AGENTS.md.writ-block` | Writ block in `CLAUDE.md` / `AGENTS.md` | Claude / Codex |
| `.codex/config.toml.baseline` | previous baseline (install: seed hash) | Codex |

**Baseline value per path:**

| After the run | Line written |
|---|---|
| Local file equals upstream (new, updated, unchanged, forced) | upstream hash |
| Local differs from upstream (preserved) and has a previous baseline | previous baseline |
| Preserved with no previous baseline | none |
| Local file missing | none |
| Writ block: action `preserved` | previous baseline, or none |
| Writ block: otherwise | recomputed inner hash (equals the template hash) |

Then append `STALE_KEPT_ENTRIES` (Story 4), and write `# baselines: shipped` among the header comments.

**`install.sh`:** apply the same change in `write_copy_manifest` and the two helpers it alone calls. The previous baseline comes from the existing manifest, read before truncation, when re-installing. Write the header only for a fresh install or when the existing manifest already has it. Over a legacy manifest, write none, so `update.sh` repairs it (Story 5).

**Test (`test_manifest_shipped_baselines.sh`)** checks three things:

- **Install.** With `.writ/docs/tech-stack.md`, `scripts/deploy.sh`, `.claude/commands/my-own.md`, and a user `.claude/commands/review.md` present before install, none is recorded, and the header is present.
- **Update.** With `.writ/docs/code-style.md` and `.claude/agents/my-agent.md` added after install, three manifest-rewriting updates never record or remove any user file.
- **Customized files.** `commands/status.md` and the CLAUDE.md Writ block (Claude Code) and `rules/writ.mdc` (Cursor) are preserved across two upstream changes, keeping their install-time baselines. A completeness check confirms that every shipped path has one line.

## Story 4 Design: Kept stale files

`detect_stale_files` modified branch (`868-874`): drop the `category = scripts` condition, so every category warns and appends `${baseline_hash}  ${manifest_path}` to `STALE_KEPT_ENTRIES`. Keep the warning text. After Story 3, no kept path is in the shipped set, so `write_copy_manifest` appends each kept entry once.

Fixture for `test_update_kept_stale_files.sh` (Claude Code):

| Category | Kept (modified locally) | Removed (unmodified) |
|---|---|---|
| commands | `commands/zz-kept.md` | `commands/zz-clean.md` |
| agents | `claude-code/agents/zz-kept.md` → `agents/zz-kept.md` | — |
| skills | `skills/zz-kept/SKILL.md` | — |
| `.writ/docs` | `.writ/docs/zz-kept.md` | — |
| scripts | `scripts/zz_kept.py` (shippable name) | — |

Steps:

1. Install from source A, which has the `zz-*` files.
2. Edit each kept file locally.
3. Run 1 against source B, which drops them. `zz-clean.md` is removed, which forces a manifest rewrite.
4. Commit an unrelated upstream change, then run 2. Repeat for run 3.
5. Do a dry run.
6. Delete one kept file and update again.

After each run, check that each kept file is byte-identical, that one warning line per kept path is printed, and that the manifest has one line per kept path with its install-time hash.

`commands/update-writ.md`: correct the frontmatter `outcome` (line 5) and exit criterion (line 10), Step 3 (line 124), Step 6 item 6 (line 194), Step 7 (lines 199, 223, plus the header in the template), and Completion (lines 286, 288). Each of them should state:

- only shipped paths get baselines
- a kept customized file or kept stale file keeps its previous baseline
- a modified stale file is flagged on every run

## Story 5 Design: Legacy manifests and removal paths

**Legacy step.** It runs after the clone and before the scan, only when `MANIFEST_FILE` exists without `# baselines: shipped`:

1. `v=$(manifest_version)`. If `v` is `unknown` or empty, the version is unresolved.
2. If `git -C "$WRIT_SRC" cat-file -e "$v^{commit}"` fails and the clone is shallow (`git rev-parse --is-shallow-repository`), run `git -C "$WRIT_SRC" fetch --quiet --unshallow` once and retry.
3. **Resolved.** For each manifest path, map it to its source path. The mapping table is in Story 5's Notes:
   - If `"$v:<source>"` exists, write `<sha256 of that blob>  <path>` to `BASELINES_FILE`.
   - For Writ blocks, write the hash of the template at `$v`.
   - Copy `.codex/config.toml.baseline` as recorded.
   - Drop every other path. It is a user file.
4. **Unresolved, or the fetch failed.** `BASELINES_FILE` holds only `.codex/config.toml.baseline`, so the run takes the existing no-manifest path. Print one notice naming `v` and the reason.

Hash a blob with `git -C "$WRIT_SRC" show "$v:<source>"` into a temp file and `hash_file` it, so the hash matches the one the overlay computes.

**Removal block** (`1114-1129`):

- For `skills/*`, remove `"$SKILLS_DIR/${sf#skills/}"`.
- Otherwise use today's mapping.
- Print `🗑  Removed: $sf` only if the file is gone after `rm -f`.

**Test** (`test_update_legacy_manifest.sh`). Build each legacy manifest by installing with the fixed `install.sh`, removing the header, setting `# version:`, and appending pre-fix-style lines. The cases:

| Case | Setup | Expected |
|---|---|---|
| A, resolved | User files recorded with their local hashes; `commands/zz-retired.md` shipped at `v`; `status.md` re-baselined to its local hash; an upstream change to `status.md` | User files kept and untracked; `zz-retired.md` removed; `status.md` preserved |
| B, unresolved | `v` set to `unknown`, then to a bogus hash | Notice printed; nothing removed or overwritten; header written |
| C, shallow | `WRIT_REPO=file://$SRC`, `v` older than the tip | Same results as case A |
| D, Codex skill | Unmodified stale skill on Codex | Removed from `.agents/skills` |
| All runs | — | Every `Removed` path is absent from disk |

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Rewrite manifest | User-authored file recorded | Iterate the shipped set from `$WRIT_SRC`; never list project folders | Story 3 install and update cases |
| Rewrite manifest | Preserved file re-baselined | Previous baseline, or no line | Story 3 customized-file case |
| Install over a user file at a shipped path | Local hash recorded as baseline | Preserved with no baseline → no line | Story 3 install case (`review.md`) |
| Rewrite manifest | Codex baseline read after truncation | Read before truncation (Story 2), then the per-run file (Story 3) | Story 2 test |
| Rewrite manifest | No prior Codex baseline | Write none; exit 0 | Story 2 nil case |
| Rewrite manifest | Kept stale path | Appended once with its old baseline | Story 4 three-run fixture |
| Stale removal | User deleted the kept file | Skipped at `838`; no warning; line drops | Story 4 delete step |
| Stale removal | Codex skill path wrong | Resolve through `$SKILLS_DIR` | Story 5 case D |
| Stale removal | `rm` fails | No `Removed` line; not counted | Story 5 "every Removed path is absent" check |
| Update early exit | Only kept stale files differ | Warning still prints; the manifest is not rewritten, so its baselines stand | Fixtures force rewrites; dry-run step |
| Legacy manifest | Version found | Baselines from upstream at that version; user paths dropped | Story 5 cases A, C |
| Legacy manifest | Version not found, or fetch fails | No-manifest behavior, keeping the Codex line; one notice | Story 5 case B |
| CI bash step | A test fails | Count failures, run all, exit non-zero | `test_ci_workflow.py` |
| CI pytest step | uv cannot provide 3.9 | Red step. Switch to `setup-python` only with that failure as evidence | First CI run |
| CI runner | A test needs BSD userland | That suite moves to `macos-latest`, with a comment | Linux run first |

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| User-authored file across installs and updates | Never recorded, mentioned, or removed | No manifest: overlay as today; the file is not in the shipped set | No user files: manifest = shipped set | Clone fails: no write |
| Customized shipped file across upstream changes | Preserved every time; baseline unchanged | No baseline: preserved; still no line | — | Clone fails: no write |
| Kept stale file across updates | Kept, warned, old baseline, every run | No manifest: no stale detection | No stale paths: no warning | Clone fails: no write |
| Legacy manifest upgrade | Version found: precise repair | `# version:` missing or `unknown`: fallback | Legacy manifest with no stale paths: repair only | `--unshallow` fails: fallback |
| Codex baseline | Line survives, same hash | No line: none written | — | Clone fails: no write |
| CI run | All suites green | No `test_*.sh`: zero tests, exit 0 | — | uv install fails: red step |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Upstream re-adds a path the user kept | Not stale anymore. The carried baseline ≠ local, so it is preserved |
| User reverts a kept file to the original | Local = baseline, so it is removed as an unmodified stale file |
| `--force` with a kept stale file | Unchanged: stale handling ignores `FORCE` |
| `--force` with a preserved file | Overwritten; local = upstream, so the upstream hash is recorded |
| User deletes a shipped file | Re-copied as new (as today); upstream hash recorded |
| Legacy manifest written by `unlink.sh` | Read as legacy; repaired like any other |
| Path containing spaces | `[OUT OF SCOPE — manifest format is "<hash>  <path>"; manifest_files splits on whitespace today]` |

## Residual Risks (Not Fixed Here)

1. **Re-running `install.sh` over a legacy manifest** trusts that manifest's baselines in the overlay. The overlay functions are outside the one-function `install.sh` scope, so a customization the old scripts re-baselined can be overwritten. Install writes no header in that case, so the next `update.sh` repairs the remaining entries. `update.sh` is the supported upgrade path.
2. **Install over a legacy manifest drops retired Writ entries.** It records only shipped paths, so a retired unedited Writ file that the legacy manifest listed is no longer tracked and stays on disk.
3. **Stale-skill sidecars** stay behind; only `SKILL.md` is removed, as today.
4. **`unlink.sh`** still writes manifests from local copies (header-less). Story 5 reads them as legacy.

## Files in Scope

| File | Story | Change |
|---|---|---|
| `.github/workflows/eval.yml` | 1 | setup-uv, pytest 3.9, bash step; runner evidence comment |
| `scripts/tests/test_ci_workflow.py` | 1 | New |
| `scripts/update.sh` | 2 | `write_copy_manifest` reads the Codex baseline before truncation |
| `scripts/tests/test_update_codex_config_baseline.sh` | 2 | New |
| `.writ/issues/bugs/2026-10-12-codex-config-baseline-dropped-on-update.md` | 2 | `## Resolution` |
| `scripts/update.sh` | 3 | Per-run baseline file; `manifest_hash_for`/`manifest_files`; `write_copy_manifest` shipped set, baseline rule, header; `append_manifest_*` |
| `scripts/install.sh` | 3 | `write_copy_manifest` and its two `append_manifest_*` helpers only |
| `scripts/tests/test_manifest_shipped_baselines.sh` | 3 | New |
| `scripts/update.sh` | 4 | `detect_stale_files` warning branch; carry-forward check |
| `commands/update-writ.md` | 4 | Frontmatter `outcome` and exit criterion, Steps 3, 6, 7, and Completion |
| `scripts/tests/test_update_kept_stale_files.sh` | 4 | New |
| `.writ/issues/bugs/2026-10-12-update-deletes-modified-stale-files.md` | 4 | `## Resolution` |
| `scripts/update.sh` | 5 | Legacy-baseline step; stale-removal block |
| `commands/update-writ.md` | 5 | One Step 3 sentence on legacy manifests |
| `scripts/tests/test_update_legacy_manifest.sh` | 5 | New |
