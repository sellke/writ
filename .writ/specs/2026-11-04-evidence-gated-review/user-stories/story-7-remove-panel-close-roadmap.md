# Story 7: Remove the review panel and close out the roadmap

> **Status:** Completed ✅ (2026-11-04)
> **Priority:** Medium
> **Dependencies:** Story 6

## User Story

**As a** Writ maintainer
**I want to** remove the review panel from every shipped surface and point leftover config at ADR-032
**So that** Gate 3 has one review path, and the roadmap records what shipped

## Acceptance Criteria

> **AC IDs assigned through:** AC-7.5

- [x] Given `scripts/review-panel.py` after the trim, when `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py` loads it by path, then the load succeeds with `_prepare_run`, `parse_output`, `trial_key`, `_key_order`, and `PrepareError` present, the parser has no `status` or `tally` subcommand, and every `trial-*` subcommand still parses. `[AC-7.1]`
- [x] Given `commands/implement-story.md` after the edit, when the wiring tests read it, then it has no panel invocation row, panel paragraph, `review-panel:` report line, or panel mention in the spawn count, the Gate 0 route, the safety-fact paragraph, the Gate 3.5 drift clause, or the "Reviewer filters." paragraph, which stays. It carries `review-panel: removed (ADR-032)` and `--panel was removed (ADR-032)`, and those are its only lines containing `removed (ADR-032)`. `[AC-7.2]`
- [x] Given the four adapter files, `.writ/docs/config-format.md`, `.writ/docs/agent-cli-contract.md`, `scripts/eval.sh`, and this repo's `.writ/config.md` after the edit, when the tests that read them run, then no adapter has a `Review panel (ADR-028)` paragraph, `config-format.md` has no `Review Panel` row or section and has one `Removed keys` line that points to ADR-032, the `review-panel.py` row and bullet name only the kept subcommands, `eval.sh` has no `review-panel` check, and `.writ/config.md` has no `Review Panel` line. `[AC-7.3]`
- [x] Given the shipped surfaces (`commands/`, `agents/`, `skills/`, `adapters/`, `claude-code/`, `cursor/`, `plugins/`, `codex/`, `README.md`, and `SKILL.md`), when `ShippedPanelScanTests` scans them for `Review Panel` and `--panel`, then every match is on a line containing `removed (ADR-032)`, `.writ/` is skipped, and the same scan fails on a temp fixture root with a planted `Review Panel` token. `[AC-7.4]`
- [x] Given `.writ/product/roadmap.md` after the edit, when Phase 15 is read, then this spec's feature line is checked, the `Reviewer prompts carry lead-judgment filters` criterion is unchanged, the Gate 2.5 criterion reads "the evidence rung that fact reached, at or above `tested`", and the Phase 15 status line cites ADR-032. `[AC-7.5]`

## Implementation Tasks

- [x] 7.1 Update `scripts/tests/test_review_panel.py` and `scripts/tests/test_panel_trial_outcome.py` test-first. In `test_review_panel.py`, delete `VendorTableTests` (it calls `slug_vendor` and `origin_vendor`), the `status` classes, `ConfigDocTests`, the adapter-row test in `ProductAmendmentTests`, and the `tally` classes and `_tally` helper. Keep `ParserTests`, the trial classes, and the ADR-028 decision 3 and roadmap pointer tests. Add an assertion that the parser has no `status` or `tally`. In `test_panel_trial_outcome.py`, make `test_panel_wiring_matches_the_verdict` assert the panel paragraph is absent for every verdict. Keep every other check in that file. Expected red until tasks 7.3 to 7.5 land `[AC-7.1, AC-7.2, AC-7.3]`
- [x] 7.2 Write the shipped-file scan test first. Add `ShippedPanelScanTests` to `scripts/tests/test_evidence_gate_wiring.py`, which Story 3 creates. It scans the shipped paths in AC-7.4 for `Review Panel` and `--panel` and skips `.writ/`. It allows a match only on a line containing `removed (ADR-032)`. It takes the root as an argument, and one case plants a token in a temp fixture root to prove the scan fails. Then update `test_agent_cli_contract.py` (drop the `review-panel.py status` Smoke entry, keep the trial Smokes), `test_harness_cuts.py` (`EVAL_CHECKS` loses `check_review_panel`), `test_design_divergence_wiring.py` (drop `--panel` from the Gate 0 trigger, position, and predictor assertions), and `test_review_route_rigor.py` (`Gate3WiringTest` asserts that the reviewer-filters paragraph no longer says `panel reviewers`; its other assertions stay). Check `test_eval_shipped_refs.py` and change it only if an assertion names the panel. Add an assertion that this repo's `.writ/config.md` has no `Review Panel` line `[AC-7.2, AC-7.3, AC-7.4]`
- [x] 7.3 Trim `scripts/review-panel.py`. Remove the `status` and `tally` code paths and the helpers listed in technical-spec.md → ## Removals → ### Review panel (Story 7), plus their parser entries. Rewrite the module docstring to describe only the kept subcommands. Grep the file for each removed name before deleting it. Run `uv run --isolated --python 3.9 --with pytest pytest scripts/tests/test_review_panel.py scripts/tests/test_gate_upgrade_trial.py` `[AC-7.1]`
- [x] 7.4 Edit `commands/implement-story.md`. Record `wc -c` before the edit. Replace the `--panel` invocation row and its conflict clause with the `--panel` rejection. Remove the panel clause from the Gate 0 route line, the panel mention from the default spawn count, the `review-panel:` report item, and the panel clause from Gate 3.5. Remove the `Review panel (opt-in)` paragraph, and put the `review-panel: removed (ADR-032)` line once in its place. In Gate 3's "Reviewer filters." paragraph, remove the words "panel reviewers" and keep the rest of the paragraph. Rewrite the safety-fact sentence to "A fail is one review-loop increment." Record `wc -c` after the edit. Run the governor test, read the value it measures, and re-pin `KNOWN_OVER_BUDGET` in `test_governor_enforcement.py` with a dated comment `[AC-7.2]`
- [x] 7.5 Remove the panel from shipped docs and checks. Delete the `Review panel (ADR-028)` paragraph from `adapters/openclaw.md`, `codex.md`, `claude-code.md`, and `cursor.md`. In `.writ/docs/config-format.md`, delete the `Review Panel` row and the `## Review Panel` section, and add one `Removed keys` line that points to ADR-032. In `.writ/docs/agent-cli-contract.md`, rewrite the `review-panel.py` row (including its consumers column) and bullet to the kept subcommands. In `scripts/eval.sh`, delete `review-panel` from the check list and delete `check_review_panel`. In this repo's `.writ/config.md`, delete the `- **Review Panel:**` line (line 18 at authoring) `[AC-7.3]`
- [x] 7.6 Close out the roadmap in `.writ/product/roadmap.md`. Check off this spec's Phase 15 feature line, which Story 1 adds. If that line is absent, stop with a blocker. Leave the `Reviewer prompts carry lead-judgment filters` criterion unchanged. Change the Gate 2.5 criterion to read "the evidence rung that fact reached, at or above `tested`". Add ADR-032 to the Phase 15 status line `[AC-7.5]`
- [x] 7.7 Verify, one run at a time. Run `python3 scripts/gen-platform-trees.py`, then `--check`. Run the scan test. Confirm `wc -c commands/implement-story.md` is at most 40759. Run pytest on Python 3.9, then on 3.14, each alone with `uv run --isolated --python <v> --with pytest pytest`. Run the bash suite in the background after pytest finishes. Run `bash scripts/eval.sh` last. Never overlap these runs `[AC-7.1, AC-7.2, AC-7.3, AC-7.4, AC-7.5]`

## Notes

**Codebase facts (verify at implementation; line numbers are from authoring)**
- `scripts/review-panel.py` is 991 lines. Removal targets: `slug_vendor` (107), `origin_vendor` (117), `config_value` (131), `CONFIG_LINE` (72), `Panel` and `resolve` (147 to 234), `tally` (360), `load_tally` (432), `cmd_tally` (452), `cmd_status` (485), and the `status` and `tally` parsers (922, 930). Keep `Source` because `_arm_keys` takes it. Delete `TallyFinding`, `TallyResult`, `_print_verdict`, `_parse_reviewer_arg`, `_drop_list`, and `_read_output` only when no kept function calls them.
- The module docstring (lines 1 to 44) describes `status`, `tally`, and `Review Panel`. Rewrite it. `plugins/writ/scripts/review-panel.py` is generated from this file, and `plugins/` is in the scan set.
- `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py` loads this file by path (`REVIEW_PANEL`, line 70) and checks `REQUIRED_NAMES` (line 86). `scripts/tests/test_gate_upgrade_trial.py` covers that load.
- `commands/implement-story.md` panel lines at authoring: 54, 74, 76, 198, 298 ("panel reviewers"), 302, 330, 342, 449. Re-grep after Stories 3 and 4 edit the file.
- Lines 198 and 342 are not in the locked removal list. Line 198 is the Gate 0 route. It must go, because the scan forbids `--panel` and `test_design_divergence_wiring.py` asserts it. Line 342 describes a panel `block` that can no longer occur. Both are removed here.
- Line 198 is Gate 0 text. `2026-10-25-design-divergence` is In Progress, and its Story 6 is pending. Run this story after that spec's Story 6, or rebase onto it. See spec.md → ## Specification Contract → Cross-Spec Overlap.
- The governor pin for `commands/implement-story.md` is 15799 at authoring (`KNOWN_OVER_BUDGET`). It is a governor measure, not `wc -c`. The test asserts `total_overage` exactly, so the re-pin must match the measured value.
- Tests to change, by file:
  - `test_review_panel.py`: see task 7.1.
  - `test_panel_trial_outcome.py`: `test_panel_wiring_matches_the_verdict` (line 108). `PANEL_PARAGRAPH` (line 27) stays.
  - `test_agent_cli_contract.py`: the `review-panel.py status` Smoke (line 605). Keep the trial Smokes and `panel_trial_setup`.
  - `test_harness_cuts.py`: `EVAL_CHECKS` (line 105) names `check_review_panel`. Check the guard at lines 190 to 205 before you change `MIXED_TESTS` (lines 89 to 100).
  - `test_design_divergence_wiring.py`: `test_triggers` (near line 556), the position list (near line 572), and `test_predictor_runs_only_off_the_forced_triggers` (near line 583).
  - `test_eval_shipped_refs.py`: only a docstring mention (line 9). Probably no change.
  - `test_review_route_rigor.py` (near line 408): `Gate3WiringTest` asserts `panel reviewers` inside the reviewer-filters paragraph, and its docstring (line 391) names them. The paragraph stays (spec.md → Amendment). Story 7 updates that assertion in task 7.2 and trims the words in task 7.4.
- `eval.sh`: `review-panel` is in the check list (line 90). `check_review_panel` spans lines 4911 to 4959, including the `--panel` row check at line 4954.
- Adapter paragraphs: `adapters/openclaw.md:76`, `codex.md:167`, `claude-code.md:177`, `cursor.md:254`.
- Generated trees: `python3 scripts/gen-platform-trees.py` rewrites `cursor/plugin/` and `plugins/writ/`. Do not hand-edit them.
- Ledger: spec.md → ## Specification Contract → Corrections made at authoring, item 1. Add no `pruned-instructions-ledger.md` rows. ADR-032's inventory records the removals.

**Updated 2026-11-04, after merge `a6a8e8c` (design-divergence Story 6) and Stories 3 to 6. These facts override the authoring notes above.**
- `scripts/tests/test_design_divergence_wiring.py` is deleted. Drop the task 7.2 and Notes items that edit it.
- The Gate 0 `--panel` route line (authoring line 198) went with the Gate 0 divergence block. AC-7.2's Gate 0 clause has nothing left to remove; the scan test still covers it.
- `commands/implement-story.md` panel lines now: 54 (Overview spawn count), 74 (`--panel` row), 76 (conflict clause), 280 ("panel reviewers" in the filters paragraph), 286 (panel paragraph), 315 ("A fail counts as a panel `block`"), 346 (Gate 3.5 panel `block` clause), 453 (`review-panel:` report item). Re-grep before editing.
- The cross-spec overlap with `2026-10-25-design-divergence` is resolved: that spec is archived at `.writ/specs/archive/2026-10-25-design-divergence/`.
- Byte budget: the file is 39929 bytes. Stories 3 and 4 added +1378 (drift-log DEV-010), so this story must free at least 1378 to keep the net across Stories 3, 4 and 7 at or below 0. The design-divergence removal does not count toward this spec. If the panel removals free less, report the shortfall; the user decides.
- `KNOWN_OVER_BUDGET` for `commands/implement-story.md` is 14969 (39929 − 24960).
- Task 7.6 must also update `RoadmapLineTest` in `scripts/tests/test_adr_032_inventory.py`, which asserts the roadmap line is unchecked.

**Resolved questions**
- Resolved (2026-11-04): this repo's `.writ/config.md` line 18 holds a live `- **Review Panel:**` line. The user chose to remove it. Task 7.5 deletes it, and task 7.2 asserts it is gone. No test reads that line: `test_review_panel.py` and `test_gate_upgrade_trial.py` write their own temp configs.
- Resolved (2026-11-04): the roadmap's Gate 2.5 criterion reads "the evidence rung that fact reached" and has no `traced` token. spec.md → Story 7 now says to add "at or above `tested`" to it. Task 7.6 makes that change.

**Byte budget**
- `commands/implement-story.md` is 40,759 bytes at authoring, before Story 3. Record `wc -c` before and after this story's edit in the What Was Built record. The final file must be at most 40,759 bytes, so the net across the stories that edit it (3, 4, and 7, plus 6 if it did) is zero or less.
- The panel paragraph alone is about 1,100 bytes.

**Risks**
- Trimming `review-panel.py` must not break `gate-upgrade-trial.py`. Run its load test in task 7.3.
- The scan allowance is exact. It allows only lines containing `removed (ADR-032)`. Do not widen it.

**Assumptions**
- `user_type` was not supplied. "Writ maintainer" comes from the spec owner.
- Python 3.9 floor. The trimmed script uses stdlib only.
- Run pytest alone. `eval.sh`, the bash suite, and writes under `.writ/state/` must not overlap a pytest run.

**Integration**
- Runs after Story 6, which raises the Safety Fact floor. Story 7 writes its own scan test.
- Stories 3, 4, and 7 edit Gate 3 of `commands/implement-story.md`. Run them in sequence.
- Story 1 creates `.writ/decision-records/adr-032-evidence-gated-review.md`. The roadmap link depends on it.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Leftover `Review Panel` line prints `review-panel: removed (ADR-032)` once per story and does nothing else; `--panel` stops with `--panel was removed (ADR-032)`] — `spec.md` → `## Business Rules (Expanded)` → `### Removals`; `spec.md` → `## Specification Contract` → Business Rules item 6. Removal file table: `technical-spec.md` → `## Removals` → `### Review panel (Story 7)`. Scan test scope: `technical-spec.md` → `## Test Plan`. Story scope: `spec.md` → `## Detailed Requirements` → `### Story 7`.

---

## What Was Built

**Implementation Date:** 2026-11-04

### Files Created

[None created]

### Files Modified

- **`scripts/review-panel.py`** (991 → 712 lines; +29 −308)
  - Removed the `status` and `tally` subcommands, their parser entries, and the helpers only they used: `resolve`, `config_value`, `Panel`, `_drop_list`, `tally`, `TallyFinding`, `TallyResult`, `key_display`, `load_tally`, `cmd_tally`, `cmd_status`, `CONFIG_LINE`, and the `PLATFORMS` constants.
  - Kept what `gate-upgrade-trial.py` and the `trial-*` subcommands call: `_prepare_run`, `PrepareError`, `parse_output`, `trial_key`, `_key_order`, `Source`, `_parse_reviewer_arg`, `_read_output`, `_print_verdict`, `PANEL_WORD_VERDICT` (without `block`), and the vendor table with `slug_vendor` and `origin_vendor` (DEV-029).
  - The module docstring describes only the five `trial-*` subcommands and the exit codes that remain.
- **`commands/implement-story.md`** (39929 → 38551 bytes; +7 −8)
  - Removed the `--panel` invocation row and its `--quick` conflict clause. The mutual-exclusion sentence now ends "`--panel` stops: `--panel was removed (ADR-032)`."
  - Replaced the **Review panel (opt-in)** paragraph with one line: "A `Review Panel` config line prints only `review-panel: removed (ADR-032)` once per story."
  - Removed the panel from the Overview spawn count, the words "panel reviewers" from the **Reviewer filters.** paragraph (the paragraph stays), the panel `block` clause from Gate 3.5 § A, and `review-panel:` from the Step 4 report item.
  - The safety-fact sentence now reads "A fail is one review-loop increment."
- **`cursor/plugin/commands/implement-story.md`, `plugins/writ/commands/implement-story.md`, `plugins/writ/scripts/review-panel.py`**: generated by `python3 scripts/gen-platform-trees.py`.
- **`adapters/claude-code.md`, `adapters/codex.md`, `adapters/cursor.md`, `adapters/openclaw.md`** (−2 each): the `Review panel (ADR-028)` paragraph is gone.
- **`scripts/eval.sh`** (−51): `review-panel` is out of `CHECKS`, and `check_review_panel` is deleted.
- **`.writ/docs/config-format.md`** (+2 −21): the `Review Panel` row and `## Review Panel` section are gone. One `**Removed keys:**` line points to ADR-032.
- **`.writ/docs/agent-cli-contract.md`** (+2 −2): the `review-panel.py` row's callers column reads "none shipped" and names the five `trial-*` subcommands and the harness. The bullet names only the trial subcommands.
- **`.writ/config.md`** (−1): the `- **Review Panel:**` line is deleted.
- **`.writ/product/roadmap.md`** (+3 −3): the Phase 15 feature line for this spec is checked, the Gate 2.5 criterion ends "at or above `tested`", and the Phase 15 status line cites ADR-032. The reviewer-filters criterion is unchanged.
- **`.writ/decision-records/adr-032-evidence-gated-review.md`** (+1 −1): the Removals row for `scripts/review-panel.py` lists `slug_vendor` and `origin_vendor` as kept, because `trial-record` calls them (DEV-029).
- **`drift-log.md`** (+17): Story 7 drift report with DEV-029. **`spec-lite.md`** (+1 −1): DEV-029 auto-amendment.
- **`scripts/tests/test_review_panel.py`** (1544 → 997 lines; +118 −665)
  - Deleted the `status` classes, `ConfigDocTests`, the `tally` classes and `_tally` helper, and the panel-wiring classes (`Gate3PanelPlacementTests`, `Gate3PanelCombinationTests`, `InvocationAndReportTests`, `EvalPinMutationTests`).
  - Kept `VendorTableTests` (DEV-029), `ParserTests`, and the trial classes.
  - New `TrimmedScriptTests` (5 tests): the harness loads the script with its reused names, the parser has no `status` or `tally`, both exit 2, every `trial-*` argv parses, and the docstring names no removed subcommand or key.
  - New `PanelRemovedFromDocsTests` (5 tests): adapters, `config-format.md`, the CLI contract row and bullet, `eval.sh`, and this repo's `.writ/config.md`.
- **`scripts/tests/test_evidence_gate_wiring.py`** (1073 → 1229 lines; +156)
  - New `PanelRemovalWiringTest` (6 tests) checks each removed clause in `commands/implement-story.md` and that the two pointers are its only `removed (ADR-032)` lines. After review it also pins "stop with a usage error before any gate; pick no winner".
  - New `ShippedPanelScanTests` (4 tests) and `panel_scan(root)`: scans the ten shipped paths for `Review Panel` and `--panel`, skips `.writ/`, allows a match only on a `removed (ADR-032)` line, and fails on a planted token in a temp root.
- **`scripts/tests/test_adr_032_inventory.py`** (+56 −8)
  - `RoadmapLineTest` expects the line checked.
  - New `RoadmapCloseOutTest` (3 tests) for AC-7.5.
  - `REMOVED_CODE_NAMES` drops the two vendor helpers. New `KEPT_PANEL_NAMES` and `RemovalListTest.test_names_the_vendor_helpers_as_kept` (DEV-029).
- **`scripts/tests/test_agent_cli_contract.py`** (+2 −8): the `status` and `tally` Smokes are gone. `trial-init` is the default `review-panel.py` smoke.
- **`scripts/tests/test_governor_enforcement.py`** (+7 −1): `KNOWN_OVER_BUDGET` for `commands/implement-story.md` re-pinned 14969 → 13591, with a dated comment.
- **`scripts/tests/test_harness_cuts.py`** (+7 −3): `EVAL_CHECKS = ()`. `test_ac_1_5_eval_checks_pin_no_lean_file` gains a whole-file `.lean.md` guard, so it still asserts something with an empty tuple.
- **`scripts/tests/test_panel_trial_outcome.py`** (+3 −5): `test_panel_wiring_matches_the_verdict` asserts the panel paragraph is absent for every verdict.
- **`scripts/tests/test_review_route_rigor.py`** (+4 −3): `Gate3WiringTest` asserts the reviewer-filters paragraph no longer says `panel reviewers`.

### Implementation Decisions

1. **`slug_vendor` and `origin_vendor` stay.** `cmd_trial_record` calls both (`scripts/review-panel.py:527`, `:542`). The contract keeps the trial subcommands, so the technical-spec removal list was wrong (DEV-029).
2. **A helper was removed only when no kept function called it.** pyflakes is clean on the trimmed file, so no kept code names a removed function.
3. **Two pointer lines, nothing else.** `--panel` is rejected inside the mutual-exclusion sentence, and the leftover config line takes the removed paragraph's place in Gate 3. These are the file's only `removed (ADR-032)` lines, and the scan allows nothing wider.
4. **The scan takes its root as an argument.** The real tree and a planted temp fixture run the same function. It is case-sensitive, as AC-7.4 specifies.
5. **Two pins moved after review.** The `--panel` conflict test was the only pin on "stop with a usage error before any gate; pick no winner", so `PanelRemovalWiringTest` re-pins it. `EVAL_CHECKS = ()` left a loop over nothing, so a whole-file `.lean.md` guard replaces it.

### Test Results

**Verification:** Automated, test-first
**Coverage:** unverifiable (no coverage report)

- ✅ Gate 1 red: 20 failed. Green: 1072 passed on 3.9 and on 3.14.
- ✅ Gate 3 recorded run (the 8 changed test files, 3.9): 634 passed, 1 skipped, `exit code: 0`.
- ✅ Gate 3 mutations: 26 of 27 caught. The survivor changed the `Removed keys` link text from ADR-032 to ADR-028. The line still names ADR-032 in its URL and its `removed (ADR-032)` message, so it was a weak mutation, not a test gap.
- ✅ After the review corrections: all 153 tests in the files changed after review pass.
- ✅ Full suite on 3.9: 4166 passed, 2 skipped, 0 failed.
- ✅ Full suite on 3.14: 4166 passed, 2 skipped, 0 failed, 1243 subtests.
- ✅ Bash suite: all green.
- ✅ `python3 scripts/gen-platform-trees.py --check`: pass.
- ✅ `bash scripts/eval.sh`: exit 0.
- Authenticity: `test_imports_no_source` on `test_adr_032_inventory.py` and `test_panel_trial_outcome.py`. Both read docs, not code. This is the known false positive (open issue 2026-09-03).

### Byte count

- `commands/implement-story.md`: 39929 → 38551 bytes (−1378). The cap is 40759.
- Net across Stories 3, 4, and 7: +1180 +198 −1378 = 0. This meets the spec's byte budget.
- `KNOWN_OVER_BUDGET`: 14969 → 13591 (38551 − 24960).

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** Every change is in Owned files, generated trees, or `test_adr_032_inventory.py`, which the story's updated Notes require.

### Gate record

**REVIEW_RESULT:** PASS

Iteration 1, `review-agent`, saved at `.writ/state/gate3-review-story-7-remove-panel-close-roadmap.md`. No Critical or Major issues. All five ACs are met. After the PASS, the orchestrator applied the reviewer's DEV-029 corrections (ADR-032 row, `KEPT_PANEL_NAMES`, `test_names_the_vendor_helpers_as_kept`) and two test recommendations (the `.lean.md` guard and the mutual-exclusion re-pin).

- **Gate 0:** arch-check pass (rederived proceed).
- **Gate 0.5:** boundary map computed (`.writ/state/boundary-story-7-remove-panel-close-roadmap.json`).
- **Gate 1:** coding-agent, test-first. Red: 20 failed. Green: 1072 passed on 3.9 and 3.14.
- **Gate 2:** no linters; pyflakes clean on the changed Python. `arch-lint: none — see .writ/docs/architecture-lint.md`. `build-smoke: unverifiable (unsupported_stack)`
- **Gate 2.5:** cross-component. `gate3-route: review-agent (outside_boundary test_adr_032_inventory.py, generated trees)`
- **Gate 3:** `reviewer-filters: on`. 1 iteration: PASS. Mutations: 26 of 27 caught. `review-override check`: pass. `safety-fact: tested (claimed tested), floor tested`. No `review-panel:` line prints: the report line is now `review-panel: removed (ADR-032)` only when a config line exists, and this story deleted this repo's line. `jev: not run`. `evidence-gate: not run (PASS)`.
- **Gate 3.5:** drift Small. DEV-029 logged, spec-lite auto-amended. drift-format: `fail large_drift_without_pause`. This is the known false positive from Story 1's DEV-001, so no PAUSE line was added.
- **Gate 4:**
  - Full suite: 4166 passed, 2 skipped, 0 failed on 3.9 and on 3.14. 3.14 also ran 1243 subtests.
  - Bash suite: all green. `gen-platform-trees.py --check`: pass. `eval.sh`: exit 0.
  - Coverage: unverifiable. Authenticity: `test_imports_no_source` on two doc-reading tests, the known false positive (open issue 2026-09-03).
- **Gate 4.5:** `app-verify: unverifiable (no_recipe)`
- **Gate 5:** `docs-check: unverifiable (no public exports in the changed set)`

### Deviations from Spec

- **[DEV-029] `slug_vendor` and `origin_vendor` kept for `trial-record`** — Severity: Small
  - Spec said: technical-spec.md § Removals → Review panel (Story 7) lists `slug_vendor` and `origin_vendor` for removal, and ADR-032 § Removals recorded them as removed. The locked contract says only the `status`/`tally` path goes and the trial subcommands stay; spec-lite says "trial helpers kept".
  - Reality: Kept both functions and `VendorTableTests`. `cmd_trial_record` calls them (`scripts/review-panel.py:527`, `:542`), so removing them would break a kept subcommand. ADR-032's Removals row now lists them as kept, and `test_adr_032_inventory.py::RemovalListTest::test_names_the_vendor_helpers_as_kept` checks it.
  - Resolution: Auto-amended spec-lite.md
  - Spec amendment: spec-lite.md Files in Scope: "`scripts/review-panel.py`: `status`/`tally` removed, trial helpers kept, including `slug_vendor` and `origin_vendor`, which `trial-record` calls (DEV-029)". technical-spec.md § Removals still lists them; the user amends it.

### Follow-ups (not fixed)

- `.writ/product/mission.md:126` and `:178`, and `mission-lite.md:53`, still describe the review panel as live.
- `technical-spec.md` § Removals still lists `slug_vendor` and `origin_vendor` as removed (DEV-029). The user amends it.
- `ShippedPanelScanTests` is case-sensitive, per AC-7.4. A lowercase `review panel` line in a shipped command would pass it.
- `scripts/review-panel.py` still ships with no shipped caller. Its removal waits for the gate-upgrade-trial harness to be deleted.
- Stale panel-era test names and docstrings remain in `test_review_panel.py`, and `scripts/review-override.py:615` still says the file "is being trimmed".
