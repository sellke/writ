# Story 2: Trial Harness: record, sheet, label, and report

> **Status:** Completed ✅ (2026-10-29)
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer
**I want to** record each arm's evidence, write the labeling sheet, import human labels, and print the per-upgrade verdict report
**So that** each upgrade is kept or removed on a committed, text-free trial file and human labels, not on lane judgment

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given a trial file with a story whose `off-1` and `off-2` arms are recorded, when `record` stores a `safety-fact` arm whose output has no `Safety Fact` heading, or an `off-1` arm whose output has one, or whose `--state` values do not match the arm, then it exits 2 and the trial file is unchanged `[AC-2.1]`
- [x] Given a Gate 0 comparison output with and without `**Avoided by:**` lines and a repro result, when `record` stores the `gate0-divergence` arm, then only issues under `### Issues Found` that carry `**Avoided by:**` produce keys, and when a `repro-first` arm records `--at-parent fail --at-commit fail`, then it stores key `ac:<repro-ac>` at `Critical`, while any other pair stores no key `[AC-2.2]`
- [x] Given a trial file with upgrade-only findings and one `ack:` field per never-exercised upgrade, when `sheet` runs and then `label --sheet FILE --labeled-by NAME` imports the filled sheet, then `sheet` writes shuffled IDs `F01` onward with one excerpt file each and records the body hash, and `label` stores the labels only when the hash matches, every `label:` is `valid` or `invalid`, every note is one line of at most 200 characters with no backtick, every `ack:` is `remove` or `amend`, and `NAME` names no agent or model; any failure exits 2 with the trial file unchanged `[AC-2.3]`
- [x] Given a trial file with arms, labels, and acknowledgments, when `report [--json]` runs, then line 1 is `pass` or `unverifiable`, it prints one `reason:` line per unverifiable upgrade, one `upgrade:` line per upgrade with its verdict and counts, the `sample:`, `proxy:`, and `yuss:` lines, and `gate-upgrade-trial:` as the last line, it applies technical-spec § Verdict in order, and it exits 0; a missing trial file or one whose `schema` is not `gate-upgrade-trial-v1` exits 2 with nothing printed on stdout `[AC-2.4]`
- [x] Given fixture trial files written by `init`, `record`, `sheet`, and `label`, when the test scans each file's text, then it fails on any reviewer output line, diff marker (`@@`, `+++`), or story text, and passes only IDs, paths, SHAs, keys, severities, labels, notes, and acknowledgments `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Write failing tests in `scripts/tests/test_gate_upgrade_trial.py` (groups for `record`, `sheet`, `label`, `report`, and the no-text scan) with fixtures under `scripts/tests/fixtures/gate-upgrade-trial/`: reviewer outputs with and without a `Safety Fact` section, a Gate 0 comparison with and without `**Avoided by:**` lines, verifier outputs (`pass`, `fail`, `unverifiable`), and a repro pair `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [x] 2.2 Implement `record` arm-evidence checks (switch states from `review-override.py switch` line 1, `Safety Fact` heading presence, verifier file, `gate0-divergence: chose` report line, `--kind` and repro results), the arm-applicability and `--origin` refusals, and the atomic write; re-recording an arm replaces it `[AC-2.1]`
- [x] 2.3 Implement key extraction in `record` through `scripts/review-panel.py`'s `parse_output` and `trial_key`, the `**Avoided by:**` filter for Gate 0, the repro-to-key rule, raw-output copy to `.writ/state/gate-upgrade-trial/`, and recomputation of `upgrade_only` and `off_only` with labels kept on keys that stay upgrade-only `[AC-2.2]`
- [x] 2.4 Implement `sheet` (seeded shuffle, `F01…` IDs, excerpt files under `.writ/state/gate-upgrade-trial/findings/`, blank fields, one `ack:` per never-exercised upgrade, body hash) and `label` (hash check with fields blanked, field validation, agent-like name refusal, atomic write) `[AC-2.3]`
- [x] 2.5 Implement `report` per technical-spec § Verdict, the output shape in § Verdict, and `--json` with the same fields; the `gate-upgrade-trial:` summary line goes last `[AC-2.4]`
- [x] 2.6 Verify acceptance criteria: run `record`, `sheet`, `label`, and `report` on the fixtures end to end, and scan each fixture trial file for reviewer, diff, and story text `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [x] 2.7 Verify all tests pass: `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` run outside the sandbox with 0 findings `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

- **Reuse, don't re-parse.** `record` loads `scripts/review-panel.py` by path (`importlib.util.spec_from_file_location`) and calls its `parse_output`, `trial_key`, and `_key_order`. If the file or a name is missing, `record` exits 2 with `reason: review_panel_missing`.
- **Hash scope.** The sheet hash covers the body with every `label:` and `note:` blank and every `ack:` blank. `label` recomputes it the same way. Any other edit to the sheet fails the check.
- **Gate 0 and Repro are proxies.** Keys from these two arms come from a comparison reviewer and a repro re-run, not a full replay. The report prints the `proxy:` line for this reason. Do not add logic that treats them as equivalent to Gate 3 keys.
- **Off-only is information only.** `off_only` counts keys that both "current gates" runs raised and the upgrade arm missed. It never feeds a verdict.
- **Coarse keys.** Two defects in one file share a key. The harness does not split them.
- **Integration.** Story 1 writes the skeleton that these subcommands read. Story 3 runs `record`, `sheet`, and `report`. The maintainer runs `label` between Story 3 and Story 4.
- **Dev-only harness.** The file lives under `.writ/eval/`. It must not import from `scripts/` except `review-panel.py`, and must not add a Classification row.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [record (arm not applicable, switch or report-line mismatch, origin mismatch, output unreadable), sheet (applicable arm missing), label (sheet body changed, blank or bad field, agent-like `--labeled-by`), report (unlabeled, missing arm, missing ack)] — from technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Report: happy, no labels, malformed trial file] — from technical-spec.md → ## Shadow Paths, row "Report"
- **Business rules:** [Upgrade-only finding (Rule 5: Gate 0 needs `**Avoided by:**`, repro fail/fail yields `ac:<repro-ac>` Critical), Labels (Rule 6: valid or invalid, one-line notes ≤200 chars, no code block), Acknowledgments (Rule 7: `remove` or `amend`), Verdict (Rule 8: per-upgrade states)] — from spec.md → ## Business Rules (Expanded), rules 5–8
- **Experience:** [Report lines (State Catalog: unlabeled, missing arm, not exercised, keep, remove, absent), harness summary line `gate-upgrade-trial:`] — from spec.md → ## Experience Design → State Catalog and Interaction Patterns
- **Technical:** technical-spec.md → ### Subcommands (rows `record`, `sheet`, `label`, `report`); ## Arm Evidence (checked by `record`); ## Upgrade-Only and Off-Only; ## Verdict; ### Schema `gate-upgrade-trial-v1`; ## Trial Inputs (Story 3), "Sheet entry" format

## What Was Built

**Implementation Date:** 2026-10-29

### Files Created

1. **`scripts/tests/fixtures/gate-upgrade-trial/`** (12 files) — reviewer outputs with and without a `Safety Fact` section (`off-fail.md`, `off-pass.md`, `safety-on.md`, `safety-on-pass.md`, `filters-on.md`), Gate 0 comparisons with and without `**Avoided by:**` (`gate0-comparison.md`, `gate0-no-avoided.md`), repro reports (`repro-bug.md`, `repro-not-bug.md`), and verifier results (`verifier-pass.txt`, `verifier-fail.txt`, `verifier-unverifiable.txt`).

### Files Modified

- **`.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py`** (578 → 1446 lines) — adds `record` (arm applicability, `--origin`, switch-state and Safety Fact heading evidence, verifier line 1, Gate 0 `**Avoided by:**` filter, repro fail/fail → `ac:<id>` Critical, raw copy to the state dir, one `recompute(story)` for `upgrade_only`/`off_only` with labels carried by `(upgrade, key)`), `snapshot` (yuss after-snapshot and `unchanged`), `sheet` (seeded `F01…` IDs, excerpt files, one `ack:` per never-exercised upgrade, blanked-field body hash), `label` (agent-like name refusal, hash and staleness checks, field validation, atomic store), and `report` (one pure `trial_report(doc)` for text and `--json`, technical-spec § Verdict order). Fixes Story 1's `_plural`.
- **`scripts/tests/test_gate_upgrade_trial.py`** (1034 → 2816 lines, 309 tests) — record evidence and refusals, keys, state dir, snapshot, sheet, label, report verdicts and output, an end-to-end fixture run (keep, remove, not_exercised, absent, unlabeled, missing_arm), and the AC-2.5 no-text scan.

### Implementation Decisions

1. **Sketch A (Gate 0 divergence)** — computed on write with mutable rows; chosen over the append-only, computed-on-read sketch, which replaced the spec's `arms`/`upgrade_only`/`off_only` schema with new fields and needed a Story 1 change.
2. **`snapshot` subcommand** for the yuss after-snapshot (DEV-004).
3. **`sheet_stale`** refusal in `label` when a `record` ran after `sheet` (DEV-005).
4. **`blinding:` report line** so `trial-report.md` carries the honor-system caveat (DEV-006).

### Test Results

**Verification:** orchestrator run `uv run pytest scripts/tests/test_gate_upgrade_trial.py -q` → 309 passed, exit 0; coder: 309 passed on Python 3.9 and the default interpreter, full suite 3950 passed, 3 skipped, bash 51/51, `eval.sh` 0 findings, `gen-platform-trees.py --check` pass, `ac-trace.py` no findings.
**Coverage:** 99% (coverage.py, orchestrator-measured)
- ✅ test-integrity authenticity: pass

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-004, DEV-005, DEV-006)
- **Security:** Clean (no network; read-only git with `GIT_OPTIONAL_LOCKS=0`; write paths built from validated IDs)
- **Boundary Compliance:** owned paths only
- **gate3-route:** review-agent (outside_boundary against the computed map for the harness, test module, and 12 fixtures)
- **reviewer-filters:** on
- **gate0-divergence:** chose A (computed on write, mutable rows) — B replaced the spec's trial-file schema and needed a Story 1 change
- **review-panel:** skipped — platform cannot spawn other vendors
- **review-override check:** unverifiable (test-integrity coverage: no_coverage_report)
- **safety-fact:** tested (claimed tested) — a refused `record`, `sheet`, or `label` raises before its trial-file write
- **jev shadow:** unverifiable (state_too_large) — advisory only
- **arch-lint:** none — see .writ/docs/architecture-lint.md
- **build-smoke:** unverifiable (unsupported_stack)
- **Recommendations carried to Story 3:** show the exact `**Avoided by:**` field in the comparison prompt and require it to quote the sketch line; tell off-arm reviewers to omit the Safety Fact section; run `record` one at a time and pass `--origin` every time.
