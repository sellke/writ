# Technical Spec: Harness Cuts

> Spec: [`../spec.md`](../spec.md) · Dependency: [`2026-10-20-ci-and-update-integrity`](../../2026-10-20-ci-and-update-integrity/spec.md) · ADR: [ADR-030](../../../decision-records/adr-030-contract-verifier-boundary-front-door.md)

Line numbers are from the tree on 2026-10-20 (branch `phase/13-subtract-and-repair`). The dependency spec edits `scripts/update.sh` first, so find `update.sh` code by function name.

## Current State (audit, 2026-10-20)

### Lean reference inventory

Source: `git grep -n -e WRIT_HARNESS_LEAN -e '\.lean\.md' -e 'lean twin' -e 'lean sibling'`, plus a word search for `lean`, `LEAN_`, `--lean`, `harness_lean`, and `lean-decision` in product source. Every non-historical hit is assigned to a story.

| File | Lines | Story | Change |
|---|---|---|---|
| `commands/_preamble.lean.md`, `create-spec.lean.md`, `implement-phase.lean.md`, `implement-story.lean.md`, `verify-spec.lean.md` | whole file | 1 | Delete |
| `scripts/install.sh` | 745-756 (`is_unshipped_lean_sibling`), 765, 1032 | 1 | Remove function and both calls |
| `scripts/update.sh` | 685-696, 707, 856-861 (lean arm of `detect_stale_files`) | 1 | Remove function, call, and arm; keep the `scripts/` filter-rejected arm |
| `README.md` | 63 | 1 | Drop the `WRIT_HARNESS_LEAN=1` sentence |
| `.writ/docs/agent-cli-contract.md` | 132 | 1 | Drop "including `*.lean.md` files" |
| `.writ/issues/improvements/2026-10-01-product-lint-misread-as-verify-spec.md` | 24, 30 | 1 | Drop `verify-spec.lean.md` from the file list |
| `scripts/eval.sh` | 4732, 4765-4771 (`check_review_panel`) | 1 | Pin `implement-story.md` only; drop the `$lean` loop arm and the lean report pin |
| `scripts/eval.sh` | 4783, 4788-4794 (`check_product_check_direction`) | 1 | Pin `verify-spec.md` and `plan-product.md` only |
| `scripts/tests/test_lean_commands.py` | whole file | 1 | Delete (reads the real lean files) |
| `scripts/tests/test_lean_preamble.py` | whole file | 1 | Delete (reads the real `_preamble.lean.md`) |
| `scripts/tests/test_install_update_lean_siblings.sh` | whole file | 1 | Delete; its upgrade-path cases move to `test_install_update_harness_cuts.sh` |
| `scripts/tests/test_agent_cli_contract.py` | 823, 825, 830 | 1 | Remove the three `implement-story.lean.md` tuples from `STORY5_STALE_CALLER_TEXT` |
| `scripts/tests/test_implement_story_default_path.py` | 309-316 | 1 | Remove `test_lean_gate_4_5_matches_default` |
| `scripts/tests/test_panel_trial_outcome.py` | 26 | 1 | Drop the lean entry from `COMMAND_FILES` |
| `scripts/tests/test_product_check_direction.py` | 31, 71, 110, 114 | 1 | Drop `verify-spec.lean.md` from `PINNED_FILES`, the AC-1.1 loop, and the mutations |
| `scripts/tests/test_quality_gate_wiring.py` | 439-442 | 1 | Remove `test_lean_sibling_is_untouched` |
| `scripts/tests/test_review_panel.py` | 688 and every `LEAN_CMD` use: 712, 720-730, 746, 754, 773, 807, 818, 823, 826, 850, 933, 943-944 | 1 | Remove `LEAN_CMD`, the lean-only tests and asserts (720-730, 818, 823, 943-944), and the lean arm of each `(STORY_CMD, LEAN_CMD)` loop; the eval fixture root (850) stops copying it |
| `scripts/tests/test_jev_setup_hooks.sh` | 11, 67-71 | 1 | Remove `LEAN` and its block |
| `scripts/tests/test_jev_shadow_hooks.sh` | 11, 44-45 | 1 | Remove `LEAN_CMD` and its check; keep the `ok` line's first half |
| `scripts/tests/test_uat_plan_verification_hooks.sh` | 128 | 1 | Remove the twin-absence line; drop "no twin" from the `ok` message |
| `scripts/story-context.py` | 9, 27-28, 101-106, 517-601, 606-613, 669-670, 689 | 2 | Remove spill; `--state-dir` hidden no-op |
| `scripts/measure-invocation.py` | 81, 150-190, 497, 546, 565-566, 578, 666-667, 712-715 | 2 | Remove the lean flag, resolver, and `harness_lean` report key |
| `scripts/eval-leanness.py` | 1040-1054, 1181-1185 | 2 | Remove `is_lean_sibling`; `all_command_files` and `metrics.commands` count every `commands/*.md` |
| `scripts/pipeline-baseline.py` | 30, 719-722, 901-914, 1119-1180, 1182-1207, 1256-1275, 2039, 2053, 2091-2102, 2225-2228 | 2 | Remove `run --lean` and everything only it uses |
| `scripts/eval.sh` | 581-584 (`check_manifest`) | 2 | Remove the lean exemption |
| `scripts/lean-decision.py` | whole file | 2 | Delete |
| `scripts/tests/test_lean_decision.py` | whole file | 2 | Delete |
| `scripts/tests/test_measure_invocation_lean.py` | whole file | 2 | Delete |
| `scripts/tests/test_eval_manifest_lean.sh` | whole file | 2 | Delete |
| `scripts/tests/test_story_context.py` | 41-62, 895-1116, 1128-1158 | 2 | Remove the flag helpers, `SpillFlagOn/Off/RescueTests`, `RealStateDirGuardTests`; keep `DefaultSkillFrozenTests` |
| `scripts/tests/test_measure_invocation.py` | 74-84 | 2 | Remove the env patch that pops `mi.LEAN_ENV` |
| `scripts/tests/test_pipeline_baseline.py` | 1233-1245 | 2 | Keep only the legacy-tolerance case (a record with `harness_lean` still validates) |
| `scripts/tests/test_pipeline_baseline_run.py` | 540-542, 1032, 1648-1758 (`LeanArmTest` and its fixtures) | 2 | New `WRIT_KEYS` and record shape; delete `LeanArmTest` |
| `scripts/install.sh` 931, `scripts/update.sh` 590, `scripts/unlink.sh` 162 | dev-only arm | 2 | Drop `lean-decision.py` |
| `scripts/tests/test_install_update_dev_scripts.sh` | 17, 100-156 | 2 | Drop `lean-decision.py` from `DEV_SCRIPTS`; use `prune-ledger.py` as the modified fixture |
| `scripts/tests/test_agent_cli_contract_doc.py` | 32-39 | 2 | Drop `lean-decision.py` from `DEV_ONLY` |
| `.writ/docs/agent-cli-contract.md` | 126 | 2 | Drop `lean-decision.py` ("Five dev-only scripts" until Story 4 adds one back) |
| `commands/update-writ.md` | 111 | 2 | Drop `lean-decision.py` from the dev-only list |
| `scripts/harness-cost.py` | 160-176 | — | No lean code. `static` sums `commands/*.md`, so its number drops when Story 1 deletes the files. No edit. |
| `scripts/tests/test_governor_enforcement.py` | 593 | — | Dated ledger comment ("the prose the lean twin already proves is sufficient"). History; not a path reference. No edit. |
| `scripts/tests/test_pipeline_baseline.py` | 1017 | — | False positive: "clean sibling". No edit. |

Historical, not edited (Business Rule 1): `CHANGELOG.md`, `.writ/decision-log.md`, `.writ/product/mission.md`, `.writ/product/roadmap.md`, `.writ/research/2026-10-19-writ-vs-pstack-research.md`, `.writ/specs/archive/` (`2026-09-24-flagged-harness-cuts`, `2026-09-25-jev-judgment-pilot`, `2026-09-26-arch-lint-and-follow-ups`, `2026-09-26-drift-arch-guards`, `2026-10-01-behavioral-verification`, `2026-10-01-cross-family-review-panel`, `2026-10-01-product-check-direction`), `.writ/specs/2026-10-12-agent-cli-contract/` (Complete; story 4 lines 21, 31, 40 and story 5 line 21), and `.writ/eval/baselines/2026-09-25-lean-arms/`.

### Recommended-delivery staging inventory

| File | Lines | Today |
|---|---|---|
| `scripts/install.sh`, `update.sh`, `unlink.sh` | `is_shippable_script` 922 / 581 / 153 | `recommend-state.py` passes the `*.py` arm and ships |
| `scripts/install.sh` | 1016-1022, 1148, 1240 | `append_manifest_writ_docs` records every local `.writ/docs/*.md`; `overlay_scan_flat_dir` for `.writ/docs` has no filter |
| `scripts/update.sh` | 677-683, 821-878, 900, 1077 | Same, plus `detect_stale_files` treats a `.writ/docs` path as stale only when upstream lacks it |
| `skills/drift-triage/SKILL.md` | 35-43, 79-82 | Small route captures a pre-edit SHA-256 and, in recommended mode, calls `scripts/recommend-state.py record-spec-lite-amendment`; "never batch" rule |
| `.writ/docs/agent-cli-contract.md` | 43, 111, 126, 137 | Row `recommend-state.py | data`; usage-error example; note |
| `.writ/docs/acceptance-criteria-ids.md` | 34, 43 | Names `scripts/recommend-state.py` by path as a parser constraint |
| `SKILL.md` 36-40 (generated by `scripts/gen-skill.sh` 612-616) | | "Install, update, and unlink manage this file alongside its reducer." |
| `.writ/manifest.yaml` | 6 | `metadata.runtime_contract` names the state doc. `gen-skill.sh:463` requires it to exist. Stays. |
| `commands/update-writ.md` | 111, 115, 124 | Step 3 prose for scripts, docs, and stale detection |
| `scripts/eval.sh` | 1793-1939 | Lifecycle scenarios require install, update, and unlink to ship both files on cursor, claude, codex |
| `scripts/eval.sh` | 1046-1792, 2013-2070 | Reducer, static, and staging-contract scenarios against the source tree. Stay. |

No command calls `recommend-state.py`. `commands/create-spec.md:33` and `commands/implement-phase.md:53` have `## Recommended Mode (--recommend)` sections, but neither creates `recommend-execution-*.json` (`.writ/docs/recommended-delivery-state-format.md:6-15`), and `implement-story.md` and `implement-spec.md` never mention recommend. The drift-triage branch has no state to write into.

### ADR-025 and `/ship` inventory

| File | Lines | Text |
|---|---|---|
| `commands/create-spec.md` | 773 | Step 2.6a item 4: emit line and "The line has no sink today…" |
| `commands/implement-story.md` | 192 | Gate 0 anchor confirmation: "On the re-run emit `(no-op until ADR-025 Story 1) escalated(...)`…" and "The line has no sink today…" |
| `scripts/eval.sh` | 2538-2563 | `check_model_escalation`: `noop_prefix`, `missing_sink`, six pins; two iteration pins and one forbid pin stay |
| `scripts/tests/test_implement_story_default_path.py` | 228-230 | `assertIn` for the emit, the prefix, and the sink sentence |
| `commands/ship.md` | 3, 17, 19, 25 | "to a merged PR", "gets it merged", "branch to merged", "→ merged PR" |
| `scripts/tests/test_governor_enforcement.py` | 597, 604, 610 | `KNOWN_OVER_BUDGET`: create-spec 29304, ship 4030, implement-story 12013. All three files sit exactly at their recorded overage. |

## Story 1 Design: delete the lean files and their install logic

After the deletion, a lean file in a user project has no upstream copy, so `detect_stale_files`'s existing `[ ! -f "$upstream_file" ]` test makes it stale. The lean arm is dead and goes. The `scripts/` filter-rejected arm stays:

```bash
    if [ ! -f "$upstream_file" ] \
        || { [ "$category" = "scripts" ] && ! is_shippable_script "$(basename "$manifest_path")"; }; then
```

Reword the comment above it to describe the remaining arm. The dependency spec may have changed the branch below it; keep its behavior.

### Guard test: `scripts/tests/test_harness_cuts.py` (new)

```python
GUARD_PATTERNS = ("-e", "WRIT_HARNESS_LEAN", "-e", r"\.lean\.md")
EXCLUDED = (":!CHANGELOG.md", ":!.writ/decision-log.md", ":!.writ/specs/archive",
            ":!.writ/research", ":!.writ/product", ":!.writ/decision-records",
            ":!.writ/specs/2026-10-12-agent-cli-contract", ":!.writ/specs/2026-10-20-harness-cuts",
            ":!scripts/tests/test_harness_cuts.py", ":!scripts/tests/test_install_update_harness_cuts.sh")
```

- `git grep -n <patterns> -- <paths>` exits 1 when nothing matches. The test fails on exit 0 and prints the hits. Any other exit is a test error.
- Story 1 scope: `commands README.md scripts/install.sh scripts/update.sh .writ/docs .writ/issues`. A Story 1 test that still reads a deleted lean file fails on its own with `FileNotFoundError`, so the suite covers the test edits. Story 2 replaces the path list with `.` plus `EXCLUDED`.
- `commands/` has no file whose name ends in `.lean.md`.
- Name the spec in the docstring (`Story 1 of \`2026-10-20-harness-cuts\``) before any `AC-N.M` token, per the ac-trace scan rules.

### Upgrade-path test: `scripts/tests/test_install_update_harness_cuts.sh` (new)

Follow `test_install_update_dev_scripts.sh`: committed source copy of the working tree in a temp dir, `fail` and `hash_file` helpers, `WRIT_REPO="$SRC"` for `update.sh`, a `trap` that removes the work dir. Never run against the Writ repo.

1. Install `--platform claude --no-commit` into a temp project. Assert no `*.lean.md` under `.claude/commands/` and none in `.claude/.writ-manifest`. Assert the dry run's command list has no `.lean.md` line.
2. Plant an old install: write `.claude/commands/implement-story.lean.md` and `.claude/commands/_preamble.lean.md` with any content, append `<sha256>  commands/<name>` for each to the manifest. Write `.claude/commands/verify-spec.lean.md`, append its hash, then append a local edit.
3. `update.sh --dry-run`: lists both unmodified files under stale, prints the kept warning for the modified one, changes nothing on disk.
4. `update.sh`: removes both unmodified files, prints `🗑  Removed: commands/<name>` for each, drops them from the manifest. Keeps the modified file byte for byte and prints `⚠️  Stale (no longer shipped, locally modified — kept): commands/verify-spec.lean.md`.
5. A second `update.sh` still prints that warning and leaves the file unchanged. Steps 4-5's kept-file assertions depend on the dependency spec's every-category carry-forward. Read `detect_stale_files` and assert the text it prints.

The removal in step 4 also makes run 1 rewrite the manifest. Without it, `update.sh` exits "Already up to date" before rewriting (dependency spec, Technical Concerns).

## Story 2 Design: remove the lean code paths

- **`story-context.py`.** `_payload` drops its `spill_path` parameter, the `_harness_lean` call, and the spill branch. Delete `LEAN_ENV`, `DEFAULT_STATE_DIR`, `SPILL_TAIL_BYTES`, `_harness_lean`, `_spill`, `_tail_cut_category`. `assemble` keeps a `state_dir=None` keyword that does nothing, so callers and tests that pass it still work. The CLI keeps `--state-dir` with `help=argparse.SUPPRESS`. Update the module docstring and usage line. Over-budget output is exactly today's flag-off output.
- **`measure-invocation.py`.** Delete `LEAN_ENV`, `LEAN_SUFFIX`, `LEAN_SIBLINGS`, `_harness_lean`, `_resolve_lean`. The preamble path is `commands/_preamble.md` and each command path is `commands/<stem>.md`. Remove the `.lean.md` filter, the per-command `source` key, and the `harness_lean` report key. Flag-off output was already byte-identical to this, so default output does not change.
- **`eval-leanness.py`.** Delete `is_lean_sibling`. `all_command_files` returns every `commands/*.md`; `metrics.commands` counts every file in the commands surface. `measure-invocation.py` reuses `all_command_files`, so the two still agree (`test_governor_enforcement.py` `test_command_bytes_agrees_with_measure_invocation_on_the_real_repo`).
- **`pipeline-baseline.py`.** Delete `LEAN_ENV`, `LEAN_SUFFIX`, `PLATFORM_COMMANDS_REL`, `RESTORED_FIELDS`, `REQUIRED_LEAN`, `LEAN_LINK`, `lean_siblings`, `restore_frontmatter`, `apply_lean_siblings`, the `lean` parameter of `overlay_writ`, `driver_env`, and the driver launcher, the `--lean` refusal and the one-arm-per-file check in `run`, and the `--lean` argument. `WRIT_KEYS` drops `harness_lean`, and `overlay_writ` stops writing it. `validate` keeps accepting a `writ` block that carries it. Grep the file for `lean` afterwards; the only hits left should be inside "clean".
- **`eval.sh` `check_manifest`.** Delete lines 581-584. A `commands/*.md` file missing from `.writ/manifest.yaml` is a finding whatever its name.
- **`lean-decision.py`.** Delete it and `test_lean_decision.py`. Drop it from the dev-only arm in all three ship filters. An installed copy from before v0.42.0 is then stale because upstream lacks it; `test_install_update_dev_scripts.sh`'s "upstream deleted the six" case already covers that path.
- **`test_install_update_dev_scripts.sh`.** `DEV_SCRIPTS` loses `lean-decision.py`. The kept-modified fixture moves to `prune-ledger.py` (still in the source repo, still filter-rejected), including `KEPT_WARNING` and every assertion that names the file.

## Story 3 Design: no-op lines and `/ship`

- `create-spec.md`: delete item 4 of Step 2.6a. Items 1-3 and the "Escalation fires only on a *returned* file…" paragraph stay byte-identical.
- `implement-story.md` Gate 0: delete from "On the re-run emit" through "…a `/retro --friction` consumer." and keep "Iteration accounting: …" verbatim.
- `check_model_escalation`: keep `create_spec_iteration_sentence`, `implement_story_iteration_sentence`, their two `require_literal` lines, and the `loop.max_iterations` forbid. Delete `noop_prefix`, `missing_sink`, and the six pins that use them or the `escalated(agent=` literals. The header comment says the check pins the escalate-once accounting at both floor-tier sites.
- `ship.md`: the description says `/ship` takes a green branch to an open PR. The Overview's "merged PR", "gets it merged", and "branch to merged" become open-PR wording. `exit_criteria`, `problem`, and `outcome` are unchanged. Measure with `wc -c`; the file must stay ≤ 28,990 bytes.
- `KNOWN_OVER_BUDGET`: set `commands/create-spec.md` and `commands/implement-story.md` (and `commands/ship.md` if it shrank) to `size - 24960` after the edit. Add one dated comment line per entry, like the existing ledger.

## Story 4 Design: staging becomes dev-only

### Ship filters

Dev-only arm, identical in `install.sh`, `update.sh`, and `unlink.sh`:

```bash
    pipeline-baseline.py|measure-invocation.py|harness-cost.py|prune-ledger.py|spawn-cap.py|recommend-state.py)
      # Dev-only tooling (eval.sh, measurement, ADR-013 dormant staging); not agent-facing. ADR-029.
      return 1 ;;
```

New function, identical in `install.sh` and `update.sh`, placed after `is_shippable_script`:

```bash
# Writ reference docs shipped to installed projects (.writ/docs/).
is_shippable_writ_doc() {
  case "$1" in
    recommended-delivery-state-format.md)
      # ADR-013 dormant staging contract; dev-only with recommend-state.py.
      return 1 ;;
  esac
  return 0
}
```

Wire it in:

1. `overlay_scan_flat_dir`: `if [ "$filter" = "doc" ] && ! is_shippable_writ_doc "$fname"; then continue; fi`. Pass `"doc"` as the fifth argument at the four `.writ/docs` call sites (`install.sh:1148,1240`, `update.sh:900,1077`).
2. `append_manifest_writ_docs` (both files): skip a name the function rejects.
3. `update.sh` `detect_stale_files`: add `|| { [ "$category" = ".writ" ] && ! is_shippable_writ_doc "$(basename "$manifest_path")"; }` beside the `scripts/` arm.

`unlink.sh` gets only the arm change. Its `.writ/docs` loop still converts a symlinked state doc to a copy, and the next `update.sh` removes that copy as stale.

### Eval lifecycle scenarios (`check_recommended_spec_implementation`, 1793-1939)

Keep the sandbox source build (it already copies the state doc into `update-source/.writ/docs`) and the three-platform loop. Replace the scenarios:

| Old | New assertion |
|---|---|
| `install-{p}-dry-run-helper`, `install-{p}-dry-run-state-doc` | Dry run exits 0 and its output names neither file |
| `install-{p}-helper-executable`, `install-{p}-state-doc` | `install-{p}-omits-helper`, `install-{p}-omits-state-doc`: install exits 0; neither file exists; the manifest names neither |
| `update-{p}-dry-run-*`, `update-{p}-restores-*` | Plant unmodified copies plus manifest lines. `update-{p}-dry-run-lists-stale`: dry run lists both as stale and both still exist. `update-{p}-removes-helper`, `update-{p}-removes-state-doc`: update exits 0, both files are gone, the manifest names neither |
| `unlink-{p}-dry-run-helper`, `unlink-{p}-copies-helper` | `unlink-{p}-skips-helper`: unlink exits 0, does not list the helper, leaves its symlink in place |
| `unlink-{p}-dry-run-state-doc`, `unlink-{p}-copies-state-doc` | Delete. Unlink's doc handling is unchanged and out of scope. |

Use the manifest path for each platform (`.cursor/.writ-manifest`, `.claude/.writ-manifest`, `.codex/.writ-manifest`).

### Prose and generated files

- `skills/drift-triage/SKILL.md` Small route: "Auto-amend **only** `spec-lite.md` and append **one unique `DEV-NNN` entry** to `drift-log.md`." The two recommended-mode bullets and the "never batch" bullet go. The pre-edit SHA-256 capture goes too: only the recommended-mode amendment record read it.
- `.writ/docs/agent-cli-contract.md`: delete row 111 and note 137. Line 126 lists six dev-only scripts: `pipeline-baseline.py`, `measure-invocation.py`, `harness-cost.py`, `prune-ledger.py`, `spawn-cap.py`, `recommend-state.py`, with "`recommend-state.py` holds ADR-013's dormant staging reducers". Line 43 keeps the rule (a JSON blocker on stdout is allowed) and drops "`recommend-state.py` does this."
- `.writ/docs/acceptance-criteria-ids.md:34,43`: say the parser is Writ's source-repo `recommend-state.py` (dev-only, not installed) and drop the `scripts/` path prefix. The table and the constraint stay.
- `commands/update-writ.md`: line 111 adds `recommend-state.py` to the dev-only list; line 115 says every upstream doc ships except `recommended-delivery-state-format.md` (ADR-013 dormant design, dev-only); line 124 adds "and manifest-listed docs the docs filter excludes". Keep the bold "**Apply same logic to Writ reference docs**" marker; `test_install_update_dev_scripts.sh:179` extracts up to it.
- `scripts/gen-skill.sh:612-616`: the Runtime Contract paragraph says the state doc records ADR-013's dormant staging design, stays in the Writ source repo, and is not installed. Run `bash scripts/gen-skill.sh`, then `bash scripts/gen-skill.sh --check` must print `pass`.

### Upgrade-path test additions (`test_install_update_harness_cuts.sh`)

1. Load both filter bodies with `sed -n '/^is_shippable_script() {/,/^}/p'` and `sed -n '/^is_shippable_writ_doc() {/,/^}/p'`. `is_shippable_script recommend-state.py` returns non-zero in all three files; `is_shippable_writ_doc recommended-delivery-state-format.md` returns non-zero and `is_shippable_writ_doc agent-cli-contract.md` returns zero in both; bodies are identical; both source files still exist.
2. On claude: plant unmodified `scripts/recommend-state.py` and `.writ/docs/recommended-delivery-state-format.md` with manifest baselines, plus modified copies in a second project. Assert removal and the `🗑  Removed:` lines in the first, kept-and-warned on two runs in the second.
3. Shipped-source grep: no hit for `scripts/recommend-state.py` or `recommend-state.py record-` in `commands agents skills adapters SKILL.md .writ/docs`, excluding `.writ/docs/recommended-delivery-state-format.md`.

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Fresh install | A cut file ships anyway (filter not wired at one call site) | Every `.writ/docs` call site passes `doc`; dry run and real run both checked | Eval lifecycle scenarios (3 platforms); bash test step 1 |
| Update removes an unmodified cut file | Manifest has no line for it | Not tracked, so update leaves it. Only files an earlier install recorded are removed. | Fixtures always append a manifest line; a fixture without one tests nothing |
| Update removes an unmodified cut file | Upstream still has the doc, so `! -f upstream` is false | Filter-rejected `.writ` arm in `detect_stale_files` | Bash test step 2; eval `update-{p}-removes-state-doc` |
| Update keeps a modified cut file | Second update deletes it because the manifest re-baselined it | Dependency spec carries the old baseline forward in every category; `append_manifest_writ_docs` skips rejected docs | Two consecutive updates in the bash test |
| Update keeps a modified cut file | Only the kept file differs, so update exits "Already up to date" before rewriting the manifest | Fixture also removes an unmodified file in run 1 | Bash test plants both kinds |
| Re-install over an old project | `install.sh` leaves old copies on disk, untracked | [OUT OF SCOPE — `install.sh` never removes files; same as the ADR-029 dev-only scripts] | — |
| Delete a lean file | A test or eval pin still reads it | Story 1 removes every read in the inventory before the suite runs | Full pytest, bash loop, eval.sh |
| Remove a lean code path | Code paths removed before the files, so the lean files count as commands | Story 1 deletes the files first | Story order; governor test |
| Remove a lean code path | A shipped caller passes `--state-dir` | Flag stays as a hidden no-op | `story-context.py assemble --story X --state-dir D` exits 0 |
| Delete lean-decision.py | `test_install_update_dev_scripts.sh` copies it as a fixture | Fixture moves to `prune-ledger.py` | That test passes |
| Remove the ADR-025 emit line | The iteration sentence is cut too | Delete only the named sentences; eval keeps the iteration pins | `check_model_escalation` require pins |
| Reword ship.md | File grows past its recorded overage | Byte-neutral or shorter wording; measure with `wc -c` | `test_no_command_acquires_a_new_or_larger_budget_violation` |
| Rewrite the eval lifecycle scenarios | Rewrite drops the reducer scenarios | Only lines 1793-1939 change | Compare the scenario names `check_recommended_spec_implementation` emits before and after: every non-lifecycle name is still present and passing |
| Regenerate SKILL.md | `SKILL.md` and `gen-skill.sh` disagree | Edit the generator, then regenerate | `gen-skill.sh --check` prints `pass`; eval `check_manifest` |

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| Install (any platform) | Every shipped file installs; no cut file appears | No `.writ/docs` in source: nothing to copy, no error | Empty project: fresh install | Source clone fails: install exits with today's clone error |
| Update over an old install | Unmodified cut files removed and reported | No manifest: update refuses as today | Manifest lists none of the cut files: nothing removed | Clone of `WRIT_REPO` fails: update exits with today's error, nothing removed |
| Update with a modified cut file | Kept, warned on every run | — | — | Same as above |
| Guard grep | Prints nothing; test passes | `git` missing: test errors with the command it ran | No tracked files match: pass | A new file reintroduces a pattern: test fails naming file and line |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Update run twice in a row | Second run removes nothing new, still warns on kept files |
| `update.sh --dry-run` | Lists stale files and warnings; writes nothing |
| `update.sh --force` | Stale handling is unchanged by `--force` (dependency spec) |
| User re-creates a lean file by hand after the update | Untracked; update never touches it |
| A future `.lean.md` command is added on purpose | It ships as a normal command; the guard test fails until the exclusion list or the test changes, which is the intended signal |
| Operator still exports the lean variable | Nothing reads it |

## Files in Scope

| File | Story | Change |
|---|---|---|
| `commands/*.lean.md` (5) | 1 | Delete |
| `scripts/install.sh`, `scripts/update.sh` | 1 | Remove lean skip function, calls, stale arm |
| `README.md`, `.writ/docs/agent-cli-contract.md`, `.writ/issues/improvements/2026-10-01-product-lint-misread-as-verify-spec.md` | 1 | Reword |
| `scripts/eval.sh` (`check_review_panel`, `check_product_check_direction`) | 1 | Drop lean pins |
| `scripts/tests/test_lean_commands.py`, `test_lean_preamble.py`, `test_install_update_lean_siblings.sh` | 1 | Delete |
| Mixed tests (9 files, inventory rows marked 1) | 1 | Remove lean reads |
| `scripts/tests/test_harness_cuts.py`, `scripts/tests/test_install_update_harness_cuts.sh` | 1 | New |
| `scripts/story-context.py`, `measure-invocation.py`, `eval-leanness.py`, `pipeline-baseline.py` | 2 | Remove lean arms |
| `scripts/eval.sh` (`check_manifest`) | 2 | Remove lean exemption |
| `scripts/lean-decision.py`, `test_lean_decision.py`, `test_measure_invocation_lean.py`, `test_eval_manifest_lean.sh` | 2 | Delete |
| `scripts/tests/test_story_context.py`, `test_measure_invocation.py`, `test_pipeline_baseline.py`, `test_pipeline_baseline_run.py` | 2 | Remove lean assertions |
| `scripts/install.sh`, `update.sh`, `unlink.sh` (dev-only arm), `test_install_update_dev_scripts.sh`, `test_agent_cli_contract_doc.py`, `.writ/docs/agent-cli-contract.md`, `commands/update-writ.md` | 2 | Drop `lean-decision.py` |
| `scripts/tests/test_harness_cuts.py` | 2 | Widen guard to the repo |
| `commands/create-spec.md`, `commands/implement-story.md`, `commands/ship.md` | 3 | Remove no-op lines; reword `/ship` |
| `scripts/eval.sh` (`check_model_escalation`) | 3 | Remove six pins |
| `scripts/tests/test_implement_story_default_path.py`, `test_governor_enforcement.py`, `test_harness_cuts.py` | 3 | Absence asserts; lower overages |
| `scripts/install.sh`, `update.sh`, `unlink.sh` | 4 | `recommend-state.py` arm; `is_shippable_writ_doc` (install, update) |
| `scripts/eval.sh` (`check_recommended_spec_implementation` lifecycle) | 4 | Invert scenarios |
| `skills/drift-triage/SKILL.md`, `.writ/docs/agent-cli-contract.md`, `.writ/docs/acceptance-criteria-ids.md`, `commands/update-writ.md`, `scripts/gen-skill.sh`, `SKILL.md` | 4 | Reword; regenerate |
| `scripts/tests/test_install_update_harness_cuts.sh`, `test_agent_cli_contract_doc.py` | 4 | Extend |
