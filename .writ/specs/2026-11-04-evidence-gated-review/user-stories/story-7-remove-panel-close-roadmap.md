# Story 7: Remove the review panel and close out the roadmap

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 6

## User Story

**As a** Writ maintainer
**I want to** remove the review panel from every shipped surface and point leftover config at ADR-032
**So that** Gate 3 has one review path, and the roadmap records what shipped

## Acceptance Criteria

> **AC IDs assigned through:** AC-7.5

- [ ] Given `scripts/review-panel.py` after the trim, when `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py` loads it by path, then the load succeeds with `_prepare_run`, `parse_output`, `trial_key`, `_key_order`, and `PrepareError` present, the parser has no `status` or `tally` subcommand, and every `trial-*` subcommand still parses. `[AC-7.1]`
- [ ] Given `commands/implement-story.md` after the edit, when the wiring tests read it, then it has no panel invocation row, panel paragraph, `review-panel:` report line, or panel mention in the spawn count, the Gate 0 route, the safety-fact paragraph, or the Gate 3.5 drift clause. It carries `review-panel: removed (ADR-032)` and `--panel was removed (ADR-032)`, and those are its only lines containing `removed (ADR-032)`. `[AC-7.2]`
- [ ] Given the four adapter files, `.writ/docs/config-format.md`, `.writ/docs/agent-cli-contract.md`, `scripts/eval.sh`, and this repo's `.writ/config.md` after the edit, when the tests that read them run, then no adapter has a `Review panel (ADR-028)` paragraph, `config-format.md` has no `Review Panel` row or section and has one `Removed keys` line that points to ADR-032, the `review-panel.py` row and bullet name only the kept subcommands, `eval.sh` has no `review-panel` check, and `.writ/config.md` has no `Review Panel` line. `[AC-7.3]`
- [ ] Given the shipped surfaces (`commands/`, `agents/`, `skills/`, `adapters/`, `claude-code/`, `cursor/`, `plugins/`, `codex/`, `README.md`, and `SKILL.md`), when the Story 6 scan runs with `Review Panel` and `--panel` added, then every match is a line containing `removed (ADR-032)`. `[AC-7.4]`
- [ ] Given `.writ/product/roadmap.md` after the edit, when Phase 15 is read, then this spec's feature line is checked, the `Reviewer prompts carry lead-judgment filters` criterion is replaced with evidence-gated wording, the Gate 2.5 criterion reads "the evidence rung that fact reached, at or above `tested`", and the Phase 15 status line cites ADR-032. `[AC-7.5]`

## Implementation Tasks

- [ ] 7.1 Update `scripts/tests/test_review_panel.py` and `scripts/tests/test_panel_trial_outcome.py` test-first. In `test_review_panel.py`, delete `VendorTableTests` (it calls `slug_vendor` and `origin_vendor`), the `status` classes, `ConfigDocTests`, the adapter-row test in `ProductAmendmentTests`, and the `tally` classes and `_tally` helper. Keep `ParserTests`, the trial classes, and the ADR-028 decision 3 and roadmap pointer tests. Add an assertion that the parser has no `status` or `tally`. In `test_panel_trial_outcome.py`, make `test_panel_wiring_matches_the_verdict` assert the panel paragraph is absent for every verdict. Keep every other check in that file. Expected red until tasks 7.3 to 7.5 land `[AC-7.1, AC-7.2, AC-7.3]`
- [ ] 7.2 Extend the Story 6 scan test to `Review Panel` and `--panel` test-first. Locate it with `grep -rl review-judgment-filters scripts/tests/`. Allow a match only on a line containing `removed (ADR-032)`. Then update `test_agent_cli_contract.py` (drop the `review-panel.py status` Smoke entry, keep the trial Smokes), `test_harness_cuts.py` (`EVAL_CHECKS` loses `check_review_panel`), and `test_design_divergence_wiring.py` (drop `--panel` from the Gate 0 trigger, position, and predictor assertions). Check `test_eval_shipped_refs.py` and change it only if an assertion names the panel. Add an assertion that this repo's `.writ/config.md` has no `Review Panel` line `[AC-7.2, AC-7.3, AC-7.4]`
- [ ] 7.3 Trim `scripts/review-panel.py`. Remove the `status` and `tally` code paths and the helpers listed in technical-spec.md → ## Removals → ### Review panel (Story 7), plus their parser entries. Rewrite the module docstring to describe only the kept subcommands. Grep the file for each removed name before deleting it. Run `uv run --isolated --python 3.9 --with pytest pytest scripts/tests/test_review_panel.py scripts/tests/test_gate_upgrade_trial.py` `[AC-7.1]`
- [ ] 7.4 Edit `commands/implement-story.md`. Record `wc -c` before the edit. Replace the `--panel` invocation row and its conflict clause with the `--panel` rejection. Remove the panel clause from the Gate 0 route line, the panel mention from the default spawn count, the `review-panel:` report item, and the panel clause from Gate 3.5. Remove the `Review panel (opt-in)` paragraph, and put the `review-panel: removed (ADR-032)` line once in its place. Rewrite the safety-fact sentence to "A fail is one review-loop increment." Record `wc -c` after the edit. Run the governor test, read the value it measures, and re-pin `KNOWN_OVER_BUDGET` in `test_governor_enforcement.py` with a dated comment `[AC-7.2]`
- [ ] 7.5 Remove the panel from shipped docs and checks. Delete the `Review panel (ADR-028)` paragraph from `adapters/openclaw.md`, `codex.md`, `claude-code.md`, and `cursor.md`. In `.writ/docs/config-format.md`, delete the `Review Panel` row and the `## Review Panel` section, and add one `Removed keys` line that points to ADR-032. In `.writ/docs/agent-cli-contract.md`, rewrite the `review-panel.py` row (including its consumers column) and bullet to the kept subcommands. In `scripts/eval.sh`, delete `review-panel` from the check list and delete `check_review_panel`. In this repo's `.writ/config.md`, delete the `- **Review Panel:**` line (line 18 at authoring) `[AC-7.3]`
- [ ] 7.6 Close out the roadmap in `.writ/product/roadmap.md`. Check off this spec's Phase 15 feature line, which Story 1 adds. If that line is absent, stop with a blocker. Replace the `Reviewer prompts carry lead-judgment filters` criterion with evidence-gated wording. Replace the rung wording in the Gate 2.5 criterion with evidence-gated wording. Add ADR-032 to the Phase 15 status line `[AC-7.5]`
- [ ] 7.7 Verify, one run at a time. Run `python3 scripts/gen-platform-trees.py`, then `--check`. Run the scan test. Confirm `wc -c commands/implement-story.md` is at most 40759. Run pytest on Python 3.9, then on 3.14, each alone with `uv run --isolated --python <v> --with pytest pytest`. Run the bash suite in the background after pytest finishes. Run `bash scripts/eval.sh` last. Never overlap these runs `[AC-7.1, AC-7.2, AC-7.3, AC-7.4, AC-7.5]`

## Notes

**Codebase facts (verify at implementation; line numbers are from authoring)**
- `scripts/review-panel.py` is 991 lines. Removal targets: `slug_vendor` (107), `origin_vendor` (117), `config_value` (131), `CONFIG_LINE` (72), `Panel` and `resolve` (147 to 234), `tally` (360), `load_tally` (432), `cmd_tally` (452), `cmd_status` (485), and the `status` and `tally` parsers (922, 930). Keep `Source` because `_arm_keys` takes it. Delete `TallyFinding`, `TallyResult`, `_print_verdict`, `_parse_reviewer_arg`, `_drop_list`, and `_read_output` only when no kept function calls them.
- The module docstring (lines 1 to 44) describes `status`, `tally`, and `Review Panel`. Rewrite it. `plugins/writ/scripts/review-panel.py` is generated from this file, and `plugins/` is in the scan set.
- `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py` loads this file by path (`REVIEW_PANEL`, line 70) and checks `REQUIRED_NAMES` (line 86). `scripts/tests/test_gate_upgrade_trial.py` covers that load.
- `commands/implement-story.md` panel lines at authoring: 54, 74, 76, 198, 302, 330, 342, 449. Re-grep after Stories 3, 4, and 6 edit the file.
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
  - `test_review_route_rigor.py` (near line 408) asserts `panel reviewers` inside the reviewer-filters paragraph. Story 6 removes that paragraph. If the test still fails here, Story 6 is incomplete.
- `eval.sh`: `review-panel` is in the check list (line 90). `check_review_panel` spans lines 4911 to 4959, including the `--panel` row check at line 4954.
- Adapter paragraphs: `adapters/openclaw.md:76`, `codex.md:167`, `claude-code.md:177`, `cursor.md:254`.
- Generated trees: `python3 scripts/gen-platform-trees.py` rewrites `cursor/plugin/` and `plugins/writ/`. Do not hand-edit them.
- Ledger: spec.md → ## Specification Contract → Corrections made at authoring, item 1. Add no `pruned-instructions-ledger.md` rows. ADR-032's inventory records the removals.

**Resolved questions**
- Resolved (2026-11-04): this repo's `.writ/config.md` line 18 holds a live `- **Review Panel:**` line. The user chose to remove it. Task 7.5 deletes it, and task 7.2 asserts it is gone. No test reads that line: `test_review_panel.py` and `test_gate_upgrade_trial.py` write their own temp configs.
- Resolved (2026-11-04): the roadmap's Gate 2.5 criterion reads "the evidence rung that fact reached" and has no `traced` token. spec.md → Story 7 now says to add "at or above `tested`" to it. Task 7.6 makes that change.

**Byte budget**
- `commands/implement-story.md` is 40,759 bytes at authoring, before Story 3. Record `wc -c` before and after this story's edit in the What Was Built record. The final file must be at most 40,759 bytes, so the net across Stories 3, 4, 6, and 7 is zero or less.
- The panel paragraph alone is about 1,100 bytes.

**Risks**
- Trimming `review-panel.py` must not break `gate-upgrade-trial.py`. Run its load test in task 7.3.
- The scan allowance is exact. It allows only lines containing `removed (ADR-032)`. Do not widen it.

**Assumptions**
- `user_type` was not supplied. "Writ maintainer" comes from the spec owner.
- Python 3.9 floor. The trimmed script uses stdlib only.
- Run pytest alone. `eval.sh`, the bash suite, and writes under `.writ/state/` must not overlap a pytest run.

**Integration**
- Depends on Story 6: the scan test, the reviewer-filters removal, and the Safety Fact floor edits.
- Stories 3, 4, 6, and 7 all edit Gate 3 of `commands/implement-story.md`. Run them in sequence.
- Story 1 creates `.writ/decision-records/adr-032-evidence-gated-review.md`. The roadmap link depends on it.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** [Leftover `Review Panel` line prints `review-panel: removed (ADR-032)` once per story and does nothing else; `--panel` stops with `--panel was removed (ADR-032)`] — `spec.md` → `## Business Rules (Expanded)` → `### Removals`; `spec.md` → `## Specification Contract` → Business Rules item 6. Removal file table: `technical-spec.md` → `## Removals` → `### Review panel (Story 7)`. Scan test scope: `technical-spec.md` → `## Test Plan`. Story scope: `spec.md` → `## Detailed Requirements` → `### Story 7`.
