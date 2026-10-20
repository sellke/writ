# Harness Cuts

> **Status:** Not Started
> **Created:** 2026-10-20
> **Owner:** @AdamSellke
> **Dependencies:** [2026-10-20-ci-and-update-integrity]
> **Phase:** 13 — Subtract and Repair ([roadmap](../../product/roadmap.md), [ADR-030](../../decision-records/adr-030-contract-verifier-boundary-front-door.md))
> **Origin:** Phase 13 decomposition pre-pass (`/implement-phase 13`, 2026-10-20).

## Specification Contract

**Deliverable:** Writ stops shipping and maintaining four things that no longer earn their place: the lean command siblings, the ADR-025 no-op emit lines, the dormant recommended-delivery staging machinery in user projects, and a `/ship` description that overstates what it does.

**Must Include:**
1. **Lean siblings:** delete `commands/_preamble.lean.md`, `create-spec.lean.md`, `implement-phase.lean.md`, `implement-story.lean.md`, `verify-spec.lean.md`, and every `WRIT_HARNESS_LEAN` code path and lean-arm test in `scripts/`: the lean skip logic in `install.sh`/`update.sh`, `story-context.py`'s lean behavior, the lean arms of `eval-leanness.py`, `measure-invocation.py`, `pipeline-baseline.py`, `harness-cost.py`, and `eval.sh`; delete `scripts/lean-decision.py` and its tests; drop lean-only tests (e.g. `test_lean_commands.py`, `test_lean_preamble.py`, `test_measure_invocation_lean.py`, `test_install_update_lean_siblings.sh`, `test_eval_manifest_lean.sh`) and remove lean assertions from mixed tests. README mention removed. Historical records stay untouched: `CHANGELOG.md`, `.writ/decision-log.md`, `.writ/specs/archive/`, `.writ/research/`, `.writ/product/`, `.writ/decision-records/`. `.writ/docs/agent-cli-contract.md` loses `lean-decision.py` from its tables if listed.
2. **ADR-025 no-op lines:** remove the `(no-op until ADR-025 Story 1) escalated(...)` emit lines and their "The line has no sink today…" sentences from `commands/create-spec.md` (Step 2.6a item 4) and `commands/implement-story.md` (Gate 0 anchor confirmation), and the matching pins in `scripts/eval.sh` `check_model_escalation` (`noop_prefix`, `missing_sink`, the `escalated(agent=...` emit pins). The escalate-once rule itself (re-run once at anchor; the floor attempt and its anchor re-run count as one attempt) and its iteration-sentence pins stay. ADR-030 already records that friction signals are retired.
3. **recommended-delivery staging becomes dev-only:** `is_shippable_script` in BOTH `scripts/install.sh` and `scripts/update.sh` (their bodies must stay byte-identical) excludes `recommend-state.py`; the `.writ/docs` ship set excludes `recommended-delivery-state-format.md` (find how `.writ/docs` is filtered on install/update; add the minimum exclusion); `skills/drift-triage/SKILL.md` loses its recommended-mode branch (verified: no command mentions recommended mode or `recommend-execution`; the branch calls `recommend-state.py record-spec-lite-amendment`); `.writ/docs/agent-cli-contract.md` reclassifies `recommend-state.py` as dev-only. The script, its eval checks (`eval-recommend-*`, recommended-spec-impl scenarios), and ADR-013's preserved design stay in the source repo and keep running there.
4. **`/ship`:** `commands/ship.md` frontmatter `description` and Overview stop saying "merged PR"; they say it opens a PR (its exit criteria already stop at an open PR).

**Upgrade path:** `update.sh` removes previously installed lean files and `recommend-state.py` / the state-format doc from user projects as stale files when unmodified; modified copies are kept with a warning. This relies on the dependency spec `2026-10-20-ci-and-update-integrity` (kept-file carry-forward in every category). Include a test for this path.

**Hardest Constraint:** About 30 files reference the lean variants, and several tests pin lean files' hashes and headings. Removal must keep every non-lean test green and leave no dangling reference.

**Success Criteria:** No `*.lean.md` file exists. `git grep -e WRIT_HARNESS_LEAN -e '\.lean\.md'` returns nothing outside the historical records listed above. A temp-project install for each of claude, cursor, and codex contains no `recommend-state.py` and no `recommended-delivery-state-format.md`. Updating a project that has unmodified copies removes them. `grep -rn "no-op until ADR-025" commands` returns nothing. Full `eval.sh` reports 0 findings. pytest and the bash tests pass.

**Scope Out:** Deleting `recommend-state.py` or its eval checks from the repo; editing ADR-013; changing escalate-once behavior; stripping other internal references or converting other eval pins (that is `2026-10-20-shipped-command-hygiene`).

**⚠️ Technical Concerns (found while grounding):**
- `is_shippable_script` has a third byte-identical copy in `scripts/unlink.sh:153`, and `scripts/tests/test_install_update_dev_scripts.sh:53-56` fails if the three bodies differ. Every ship-filter edit goes to all three files.
- `.writ/docs` has no ship filter today. `overlay_scan_flat_dir` copies every file in the source `.writ/docs/` (`install.sh:1148,1240`, `update.sh:900,1077`), and `append_manifest_writ_docs` records every local `.writ/docs/*.md`. The minimum exclusion is a new `is_shippable_writ_doc` used in those two places plus a filter-rejected arm in `update.sh` `detect_stale_files`, mirroring the `scripts/` arm. Without that arm the state doc stays upstream, is never stale, and is never removed.
- `scripts/eval.sh` `check_recommended_spec_implementation` (`1793-1939`) has 12 lifecycle scenarios per platform that require install, update, and unlink to ship `recommend-state.py` and the state doc. They pin the behavior this spec removes, so they are inverted, not kept. The reducer and state-doc scenarios in the same check keep running.
- The root `SKILL.md` "Runtime Contract" (generated by `scripts/gen-skill.sh:612-616` from `.writ/manifest.yaml` `metadata.runtime_contract`) says "Install, update, and unlink manage this file alongside its reducer." That becomes false and is reworded. `gen-skill.sh` requires `runtime_contract` to name an existing file, and the doc stays in the source repo, so the metadata line stays.
- `harness-cost.py` has no lean code path. Its `static` section sums `commands/*.md`, which includes the lean files today; the number falls when they are deleted. No edit is needed.
- `commands/ship.md` is 28,990 bytes, exactly its recorded overage of 4,030 in `scripts/tests/test_governor_enforcement.py:604`. The rewording must not add bytes.
- The success-criteria grep cannot be literally empty: this spec's own folder, the Complete spec `2026-10-12-agent-cli-contract` (its Story 4 and 5 files name `*.lean.md`), and the two guard tests this spec adds all contain the patterns. Business Rule 2 defines the exact exclusion list.

## Experience Design

### Who uses it

- **Users of installed projects** who run `install.sh` or `update.sh`. They get fewer files and no files nothing calls.
- **The Writ maintainer.** Fewer files to keep in sync, fewer pins that move on every edit, and no flag nobody sets.
- **Agents** reading `/ship`, `/create-spec`, and `/implement-story`. They stop reading instructions to print lines nothing consumes, and `/ship` stops promising a merge it does not do.

### State Catalog

| State | What the user or maintainer sees |
|---|---|
| Fresh install, any platform | No `*.lean.md` in the commands folder, no `scripts/recommend-state.py`, no `.writ/docs/recommended-delivery-state-format.md`, none of them in the manifest. Every other command, script, and doc installs as before. |
| Update, old unmodified copies present | Dry run lists each under "Stale files (removed upstream, would be deleted)". The real run prints `🗑  Removed: <path>` for each and drops it from the manifest. |
| Update, a copy edited locally | The file is kept byte for byte. Each run prints `⚠️  Stale (no longer shipped, locally modified — kept): <path>`. The manifest keeps its old baseline (dependency spec). |
| Re-install with `install.sh` over an old project | `install.sh` never removes files. Old copies stay on disk, untracked by the manifest. Same as the ADR-029 dev-only scripts today. |
| Writ source repo | `recommend-state.py`, the state doc, `eval-recommend-*.py`, and the reducer scenarios are present and `eval.sh` runs them. |
| Agent reads `/create-spec` Step 2.6a or `/implement-story` Gate 0 | It re-runs a failing floor result once at anchor and counts the pair as one attempt. It prints no `escalated(...)` line. |
| Agent or user reads `/ship` | The description and Overview say it opens a PR. |
| Maintainer exports the old lean variable | Nothing reads it. No script changes behavior. |

## Business Rules (Expanded)

1. **Historical records are not edited.** `CHANGELOG.md`, `.writ/decision-log.md`, `.writ/specs/archive/`, `.writ/research/`, `.writ/product/`, `.writ/decision-records/`, and `.writ/eval/baselines/` keep their lean, ADR-025, and staging references. The Complete spec `.writ/specs/2026-10-12-agent-cli-contract/` is also a record of finished work and is not edited.
2. **The guard grep.** "No lean reference remains" means this command prints nothing:
   `git grep -n -e WRIT_HARNESS_LEAN -e '\.lean\.md' -- . ':!CHANGELOG.md' ':!.writ/decision-log.md' ':!.writ/specs/archive' ':!.writ/research' ':!.writ/product' ':!.writ/decision-records' ':!.writ/specs/2026-10-12-agent-cli-contract' ':!.writ/specs/2026-10-20-harness-cuts' ':!scripts/tests/test_harness_cuts.py' ':!scripts/tests/test_install_update_harness_cuts.sh'`
3. **Ship filters stay identical.** `is_shippable_script` is byte-identical in `install.sh`, `update.sh`, and `unlink.sh`. The new `is_shippable_writ_doc` is byte-identical in `install.sh` and `update.sh`. A test compares the bodies.
4. **Dev-only means four things.** The file stays in the source repo. `eval.sh` keeps running it there. Install and update do not copy it or record it in the manifest. Update treats a manifest-listed copy as stale: unmodified → removed; modified → kept with a warning on every run.
5. **Escalate-once is unchanged.** Both sites still re-run a failing floor result once at `anchor`. The iteration sentences stay verbatim: `the floor attempt and its anchor re-run count as one attempt — there is no second regeneration` (create-spec) and ``the floor attempt and its anchor re-run count as one attempt against `loop.max_iterations` `` (implement-story). `check_model_escalation` keeps both pins and the `loop.max_iterations` forbid pin.
6. **Byte budgets only go down.** `commands/ship.md` must not grow past 28,990 bytes. `create-spec.md` and `implement-story.md` shrink; their `KNOWN_OVER_BUDGET` entries in `test_governor_enforcement.py` drop to the measured overage with a dated comment, matching the existing ledger.
7. **Removed flags.** `story-context.py` ships, so its spill-only `--state-dir DIR` stays accepted as a hidden no-op (ADR-029 contract rule: a removed flag stays accepted). `pipeline-baseline.py` is dev-only; `run --lean` is removed outright.
8. **Legacy data stays readable.** `pipeline-baseline.py validate` accepts a run record whose `writ` block carries the old `harness_lean` key. The committed files in `.writ/eval/baselines/2026-09-25-lean-arms/` carry it. New records omit it.
9. **No dangling reference.** A shipped file that names a removed or dev-only file is fixed in the same story: shipped docs stop pointing at `scripts/recommend-state.py` by path, `SKILL.md` stops claiming install manages the state doc, and the open issue `.writ/issues/improvements/2026-10-01-product-lint-misread-as-verify-spec.md` stops listing `verify-spec.lean.md`.
10. **Never run `install.sh` or `update.sh` against the Writ repo.** `.claude/` and `.cursor/` are symlinks into the source. Every install and update test uses temp directories.
11. **Every story leaves the tree green.** `uv run --python 3.9 pytest`, every `scripts/tests/test_*.sh`, and `bash scripts/eval.sh` (outside any sandbox) pass at the end of each story.

## Detailed Requirements

### Story 1: Lean siblings stop existing and stop shipping

- Delete the five `commands/*.lean.md` files.
- Remove `is_unshipped_lean_sibling` from `install.sh` (definition `745-756`, calls `765` and `1032`) and from `update.sh` (definition `685-696`, call `707`, and the lean arm of `detect_stale_files` at `856-861`). The deleted files are then stale because upstream no longer has them.
- Delete the lean-only tests that read the real lean files: `test_lean_commands.py`, `test_lean_preamble.py`, `test_install_update_lean_siblings.sh`.
- Remove lean-file reads from mixed tests and eval pins: `test_agent_cli_contract.py:823,825,830`; `test_implement_story_default_path.py:309-316`; `test_panel_trial_outcome.py:26`; `test_product_check_direction.py:31,71,110,114`; `test_quality_gate_wiring.py:439-442`; `test_review_panel.py` (`LEAN_CMD` and its tests); `test_jev_setup_hooks.sh:11,67-71`; `test_jev_shadow_hooks.sh:11,44-45`; `test_uat_plan_verification_hooks.sh:128`; `eval.sh` `check_review_panel` (`4732,4765-4771`) and `check_product_check_direction` (`4783,4788-4794`).
- Reword `README.md:63`, `.writ/docs/agent-cli-contract.md:132`, and `.writ/issues/improvements/2026-10-01-product-lint-misread-as-verify-spec.md:24,30`.
- New `scripts/tests/test_harness_cuts.py` (guard grep, scoped to the paths this story cleans) and `scripts/tests/test_install_update_harness_cuts.sh` (lean upgrade path).

### Story 2: Lean code paths leave the scripts

- `story-context.py`: remove the spill path; `--state-dir` becomes a hidden no-op.
- `measure-invocation.py`, `eval-leanness.py`, `pipeline-baseline.py`, `eval.sh` `check_manifest` (`581-584`): remove the lean arms.
- Delete `scripts/lean-decision.py`, `test_lean_decision.py`, `test_measure_invocation_lean.py`, `test_eval_manifest_lean.sh`.
- Remove lean assertions from `test_story_context.py`, `test_measure_invocation.py`, `test_pipeline_baseline.py`, `test_pipeline_baseline_run.py`.
- Drop `lean-decision.py` from the dev-only arm in all three ship filters and from `test_install_update_dev_scripts.sh`, `test_agent_cli_contract_doc.py`, `.writ/docs/agent-cli-contract.md:126`, and `commands/update-writ.md:111`.
- Widen the guard grep in `test_harness_cuts.py` to Business Rule 2.

### Story 3: ADR-025 no-op lines go, and `/ship` says what it does

- Delete `commands/create-spec.md:773` (Step 2.6a item 4).
- Delete the emit sentence and the "no sink today" sentence from `commands/implement-story.md:192`.
- In `eval.sh` `check_model_escalation` (`2538-2563`), remove `noop_prefix`, `missing_sink`, and their six pins; update the header comment.
- Flip `test_implement_story_default_path.py:228-230` to assert the emit, its prefix, and the sink sentence are absent.
- Reword `commands/ship.md` lines 3, 17, 19, and 25 to say `/ship` opens a PR, without adding bytes.
- Lower the `KNOWN_OVER_BUDGET` entries for the files that shrank.

### Story 4: Recommended-delivery staging becomes dev-only

- Add `recommend-state.py` to the dev-only arm of `is_shippable_script` in `install.sh`, `update.sh`, and `unlink.sh`.
- Add `is_shippable_writ_doc` (rejects `recommended-delivery-state-format.md`) to `install.sh` and `update.sh`. Use it in `overlay_scan_flat_dir` for `.writ/docs`, in `append_manifest_writ_docs`, and in `update.sh` `detect_stale_files`.
- Remove the recommended-mode branch from `skills/drift-triage/SKILL.md` (lines `37-43` and `79-82`, plus the pre-edit SHA-256 capture at `35`).
- `.writ/docs/agent-cli-contract.md`: remove the `recommend-state.py` row (`111`) and note (`137`), add it to the dev-only list (`126`), and drop it as the shipped example at line 43.
- Reword `.writ/docs/acceptance-criteria-ids.md:34,43`, `commands/update-writ.md:111,115,124`, and the `gen-skill.sh` Runtime Contract sentence; regenerate `SKILL.md`.
- Invert the lifecycle scenarios in `eval.sh` `check_recommended_spec_implementation`.
- Extend `test_install_update_harness_cuts.sh` with the staging upgrade path, and add `recommend-state.py` to `DEV_ONLY` in `test_agent_cli_contract_doc.py`.

## Implementation Approach

- **Order:** Story 1 first. Deleting the files before the code paths keeps every intermediate tree green. If the code paths went first, `eval-leanness.py`, `eval.sh` `check_manifest`, and `measure-invocation.py` would count the five lean files as commands, and the governor test would flag `implement-story.lean.md` (32,187 bytes) as a new over-budget command. Story 2 needs Story 1. Stories 3 and 4 need Story 2 (shared test files, the ship-filter arm, and the agent CLI contract doc) and can run in parallel; they share only `scripts/eval.sh`, in different functions.
- **Tests first.** For a deletion, the failing test is the guard grep, an absence assertion, or an inverted eval scenario. Write it, watch it fail on the current tree, then delete.
- **Read before editing `update.sh`.** The dependency spec rewrites `detect_stale_files` and `write_copy_manifest`. Line numbers here are from 2026-10-20; find the code by function name.
- **Verification per story:** `uv run --python 3.9 pytest`; `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`; `bash scripts/eval.sh` outside the sandbox; install and update dry runs in temp directories only.
- **Full inventory and line references:** `sub-specs/technical-spec.md`.
