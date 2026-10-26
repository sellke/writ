# Story 4: Divergence Trial Harness

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** prepare, record, blind, rate, and score a trial of declared-axes drafts against naive "give me three options" drafts, using `scripts/divergence-trial.py` with `init`, `record`, `blind`, `rate`, and `report` subcommands
**So that** whether the design-divergence skill stays or is removed is decided by a committed trial file, a blinded human rating, and a mechanical `report` verdict

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [ ] Given a briefs directory, when `python3 scripts/divergence-trial.py init --briefs DIR --out FILE` runs, then it writes a `divergence-trial-v1` skeleton with each brief's `id`, `medium`, and `brief_sha256` and empty `arms` when there are exactly six briefs, two each of `ui`, `api`, and `data-model`; any other count or split, a brief missing its `id:` or `medium:` line, or an existing `--out` without `--force` exits 2 and writes nothing `[AC-4.1]`
- [ ] Given a drafts file, when `record --trial FILE --brief ID --arm axes|naive --drafts FILE` runs, then it stores the drafts file's sha256 and count and copies the file to `.writ/eval/divergence-trial/raw/<brief>/<arm>.md` when the file has exactly three `## Draft` blocks, each with `Title:`, `Structure:`, and `Trade-off:`, `Commitment:` present in every `axes` draft and absent from every `naive` draft; otherwise it exits 2 and leaves the trial file unchanged `[AC-4.2]`
- [ ] Given all twelve arms recorded, when `blind --trial FILE --sheet OUT [--seed N]` runs, then for each brief it assigns the two arms to Set X and Set Y at random, shuffles drafts within each set, replaces titles with `Draft 1` to `Draft 3`, drops every `Commitment:` line, and leaves blank `distinct_X`, `distinct_Y`, `more_distinct`, `render_only_enough`, and `note` fields; it writes `key.json` beside the sheet and records `sheet_body_sha256` and `key_sha256` in the trial file; a missing arm exits 2 and writes neither sheet nor key `[AC-4.3]`
- [ ] Given a filled sheet, when `rate --trial FILE --sheet FILE --rated-by NAME` runs, then it stores every brief's ratings by set label and `rated_by`; a body-hash mismatch after the rating fields are blanked, a blank or out-of-range field, a note over 200 characters or containing a newline, or an empty `--rated-by` exits 2 and leaves the trial file unchanged `[AC-4.4]`
- [ ] Given a trial file, when `report --trial FILE [--json]` runs, then it prints `keep` when the axes arm is `more_distinct` on at least 4 of 6 briefs and its total distinct count exceeds the naive arm's, `remove` otherwise (a tie on a brief is not a win), and `unverifiable` with a `reason:` line (`unrated`, `missing_arm`, `key_missing`, or `key_changed`) when it cannot decide; the output is verdict first, then one `brief:` line per brief, a `render-only:` tally, the caveat line `sample: 6 briefs, one rater; declared axes must win 4 of 6 — a small sample, not a general result`, the line `blinding: honor-system; the rater opened only the sheet`, and a `divergence-trial:` summary last; it exits 0 `[AC-4.5]`

## Implementation Tasks

- [ ] 4.1 Write failing tests in `scripts/tests/test_divergence_trial.py` with fixtures under `scripts/tests/fixtures/divergence-trial/` (six briefs, valid and invalid drafts files, a filled sheet) covering every refusal and verdict branch; use `tmp_path` only and no network `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`
- [ ] 4.2 Implement `init` in `scripts/divergence-trial.py`, including the six-brief split check, header parsing, and the `--force` guard `[AC-4.1]`
- [ ] 4.3 Implement `record` with the `## Draft` template parser, the per-arm `Commitment:` rule, and the raw copy under `.writ/eval/divergence-trial/raw/` `[AC-4.2]`
- [ ] 4.4 Implement `blind` with a seeded RNG, the sheet writer, `key.json`, and the `sheet_body_sha256` and `key_sha256` hashes `[AC-4.3]`
- [ ] 4.5 Implement `rate` with the blank-and-hash check, per-field validation, and an atomic write of the trial file `[AC-4.4]`
- [ ] 4.6 Implement `report`, its verdict and `unverifiable` branches, the caveat and blinding lines, and `--json` `[AC-4.5]`
- [ ] 4.7 Verify acceptance criteria are met: `uv run pytest` and `uv run --python 3.9 pytest` pass, then the bash tests and `bash scripts/eval.sh` pass outside the sandbox with 0 findings `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`

## Notes

- **Dev-only (orchestrator amendment, D25):** list `divergence-trial.py` in every dev-only script list, as `pipeline-baseline.py` is (`DEV_ONLY_SCRIPTS` in `scripts/gen-platform-trees.py`; the dev-only cases in `scripts/install.sh`, `scripts/update.sh`, `scripts/unlink.sh`), so it never ships and needs no agent CLI contract row. Story 6 removes those entries with the harness.

- **Python 3.9 floor.** Use only 3.9 syntax and stdlib. No `match` statements. No `str | None` annotations evaluated at runtime; use `typing.Optional`. The suite must pass under `uv run --python 3.9 pytest`.
- **Stdlib only.** No third-party packages. The script is `python3 scripts/divergence-trial.py`.
- **Exit codes.** 0 when the command ran, 2 for a usage error or refusal. A refusal leaves the trial file unchanged and writes no sheet or key.
- **Ratings stored by set label.** The trial file records ratings under Set X and Set Y, never under arm names. The file therefore reveals no arm before `report` reads `key.json`.
- **Blinding is honor-system.** `key.json` and the raw drafts are committed so they survive a lane worktree. The rater is told to open only the sheet. The report prints the `blinding:` line to say so.
- **Byte-stable sheet body.** `blind` hashes the sheet body with rating fields blanked. `rate` recomputes that hash. A seeded `--seed N` must produce the same sheet and key for the same trial file, so tests can assert exact output.
- **Summary line position.** Every subcommand prints its `divergence-trial:` summary as the last line of output (spec.md → Interaction Patterns; technical-spec.md → Report output).
- **Temporary script.** `scripts/divergence-trial.py`, its unit tests, and its fixtures are deleted in Story 6, after the report is committed. Story 5's outcome test (`scripts/tests/test_divergence_trial_outcome.py`) must not import the harness. Story 5 drives these subcommands on real inputs through the CLI.
- **Pattern source.** Follow the Phase 12 panel-trial harness (`scripts/review-panel.py` `trial-*` subcommands, archived in `.writ/specs/archive/2026-10-01-cross-family-review-panel/`). Copy its shape: schema-tagged JSON, one subcommand per step, a `reason:` line on `unverifiable`, and a summary line.
- **Schema and field definitions.** The `divergence-trial-v1` schema and the sheet's rating fields are in `sub-specs/technical-spec.md` → Trial Harness. Do not restate them in the code's docstrings beyond what the tests need.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [init, record, blind, rate, report] — from technical-spec.md → Error & Rescue Map
- **Shadow paths:** [Trial report] — from technical-spec.md → Shadow Paths
- **Business rules:** [Trial integrity (both arms share model, brief, and template; blinding strips `Commitment:` and renames titles), Trial verdict (keep at 4 of 6 briefs plus a higher total distinct count; a tie is not a win; unverifiable reasons)] — from spec.md → ## Business Rules (Expanded), items 10 and 11
- **Experience:** [Report output (verdict first, `brief:` lines, caveat and blinding lines, `divergence-trial:` summary last), Refusal output (exit 2 with the file unchanged)] — from spec.md → ## Interaction Patterns and ## Experience Design
