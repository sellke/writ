# Story 2: Trial Harness: record, sheet, label, and report

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer
**I want to** record each arm's evidence, write the labeling sheet, import human labels, and print the per-upgrade verdict report
**So that** each upgrade is kept or removed on a committed, text-free trial file and human labels, not on lane judgment

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given a trial file with a story whose `off-1` and `off-2` arms are recorded, when `record` stores a `safety-fact` arm whose output has no `Safety Fact` heading, or an `off-1` arm whose output has one, or whose `--state` values do not match the arm, then it exits 2 and the trial file is unchanged `[AC-2.1]`
- [ ] Given a Gate 0 comparison output with and without `**Avoided by:**` lines and a repro result, when `record` stores the `gate0-divergence` arm, then only issues under `### Issues Found` that carry `**Avoided by:**` produce keys, and when a `repro-first` arm records `--at-parent fail --at-commit fail`, then it stores key `ac:<repro-ac>` at `Critical`, while any other pair stores no key `[AC-2.2]`
- [ ] Given a trial file with upgrade-only findings and one `ack:` field per never-exercised upgrade, when `sheet` runs and then `label --sheet FILE --labeled-by NAME` imports the filled sheet, then `sheet` writes shuffled IDs `F01` onward with one excerpt file each and records the body hash, and `label` stores the labels only when the hash matches, every `label:` is `valid` or `invalid`, every note is one line of at most 200 characters with no backtick, every `ack:` is `remove` or `amend`, and `NAME` names no agent or model; any failure exits 2 with the trial file unchanged `[AC-2.3]`
- [ ] Given a trial file with arms, labels, and acknowledgments, when `report [--json]` runs, then line 1 is `pass` or `unverifiable`, it prints one `reason:` line per unverifiable upgrade, one `upgrade:` line per upgrade with its verdict and counts, the `sample:`, `proxy:`, and `yuss:` lines, and `gate-upgrade-trial:` as the last line, it applies technical-spec § Verdict in order, and it exits 0; a missing trial file or one whose `schema` is not `gate-upgrade-trial-v1` exits 2 with nothing printed on stdout `[AC-2.4]`
- [ ] Given fixture trial files written by `init`, `record`, `sheet`, and `label`, when the test scans each file's text, then it fails on any reviewer output line, diff marker (`@@`, `+++`), or story text, and passes only IDs, paths, SHAs, keys, severities, labels, notes, and acknowledgments `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write failing tests in `scripts/tests/test_gate_upgrade_trial.py` (groups for `record`, `sheet`, `label`, `report`, and the no-text scan) with fixtures under `scripts/tests/fixtures/gate-upgrade-trial/`: reviewer outputs with and without a `Safety Fact` section, a Gate 0 comparison with and without `**Avoided by:**` lines, verifier outputs (`pass`, `fail`, `unverifiable`), and a repro pair `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [ ] 2.2 Implement `record` arm-evidence checks (switch states from `review-override.py switch` line 1, `Safety Fact` heading presence, verifier file, `gate0-divergence: chose` report line, `--kind` and repro results), the arm-applicability and `--origin` refusals, and the atomic write; re-recording an arm replaces it `[AC-2.1]`
- [ ] 2.3 Implement key extraction in `record` through `scripts/review-panel.py`'s `parse_output` and `trial_key`, the `**Avoided by:**` filter for Gate 0, the repro-to-key rule, raw-output copy to `.writ/state/gate-upgrade-trial/`, and recomputation of `upgrade_only` and `off_only` with labels kept on keys that stay upgrade-only `[AC-2.2]`
- [ ] 2.4 Implement `sheet` (seeded shuffle, `F01…` IDs, excerpt files under `.writ/state/gate-upgrade-trial/findings/`, blank fields, one `ack:` per never-exercised upgrade, body hash) and `label` (hash check with fields blanked, field validation, agent-like name refusal, atomic write) `[AC-2.3]`
- [ ] 2.5 Implement `report` per technical-spec § Verdict, the output shape in § Verdict, and `--json` with the same fields; the `gate-upgrade-trial:` summary line goes last `[AC-2.4]`
- [ ] 2.6 Verify acceptance criteria: run `record`, `sheet`, `label`, and `report` on the fixtures end to end, and scan each fixture trial file for reviewer, diff, and story text `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [ ] 2.7 Verify all tests pass: `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` run outside the sandbox with 0 findings `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

- **Reuse, don't re-parse.** `record` loads `scripts/review-panel.py` by path (`importlib.util.spec_from_file_location`) and calls its `parse_output`, `trial_key`, and `_key_order`. If the file or a name is missing, `record` exits 2 with `reason: review_panel_missing`.
- **Hash scope.** The sheet hash covers the body with every `label:` and `note:` blank and every `ack:` blank. `label` recomputes it the same way. Any other edit to the sheet fails the check.
- **Gate 0 and Repro are proxies.** Keys from these two arms come from a comparison reviewer and a repro re-run, not a full replay. The report prints the `proxy:` line for this reason. Do not add logic that treats them as equivalent to Gate 3 keys.
- **Off-only is information only.** `off_only` counts keys that both "current gates" runs raised and the upgrade arm missed. It never feeds a verdict.
- **Coarse keys.** Two defects in one file share a key. The harness does not split them.
- **Integration.** Story 1 writes the skeleton that these subcommands read. Story 3 runs `record`, `sheet`, and `report`. The maintainer runs `label` between Story 3 and Story 4.
- **Dev-only harness.** The file lives under `.writ/eval/`. It must not import from `scripts/` except `review-panel.py`, and must not add a Classification row.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [record (arm not applicable, switch or report-line mismatch, origin mismatch, output unreadable), sheet (applicable arm missing), label (sheet body changed, blank or bad field, agent-like `--labeled-by`), report (unlabeled, missing arm, missing ack)] — from technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Report: happy, no labels, malformed trial file] — from technical-spec.md → ## Shadow Paths, row "Report"
- **Business rules:** [Upgrade-only finding (Rule 5: Gate 0 needs `**Avoided by:**`, repro fail/fail yields `ac:<repro-ac>` Critical), Labels (Rule 6: valid or invalid, one-line notes ≤200 chars, no code block), Acknowledgments (Rule 7: `remove` or `amend`), Verdict (Rule 8: per-upgrade states)] — from spec.md → ## Business Rules (Expanded), rules 5–8
- **Experience:** [Report lines (State Catalog: unlabeled, missing arm, not exercised, keep, remove, absent), harness summary line `gate-upgrade-trial:`] — from spec.md → ## Experience Design → State Catalog and Interaction Patterns
- **Technical:** technical-spec.md → ### Subcommands (rows `record`, `sheet`, `label`, `report`); ## Arm Evidence (checked by `record`); ## Upgrade-Only and Off-Only; ## Verdict; ### Schema `gate-upgrade-trial-v1`; ## Trial Inputs (Story 3), "Sheet entry" format
