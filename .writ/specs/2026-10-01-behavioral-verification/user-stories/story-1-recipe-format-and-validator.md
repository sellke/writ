# Story 1: Recipe Format, Validator, and Product Amendments

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** developer using Writ on my own project (and the Writ maintainer)
**I want to** have one written grammar for the per-project app-verification recipe and a validator that tells me exactly what is wrong with mine
**So that** every later consumer (the run script, `/create-uat-plan`, Gate 4.5) reads a recipe whose shape was checked by a machine, and the product docs describe the design Writ is actually building

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given `.writ/docs/app-verification-format.md`, when a reader opens it, then it defines the six `##` sections (Launch, Safety, Login, Feature Map, Evidence, Cleanup), `- **Key:** value` settings in the `.writ/config.md` format, the `ID | Feature | Paths | Check` feature table (kebab-case unique IDs; `Check` is a backticked command or `human-only: <reason>`), the `fnmatch` semantics of `Allowed`/`Never`/`Paths`, the names-only rule for secrets, and one worked example matching technical-spec.md → Recipe Grammar `[AC-1.1]`
- [ ] Given a valid recipe, when `python3 scripts/app-verify.py validate --recipe PATH` runs under Python 3.9 with stdlib only, then it exits 0 with one `app-verify:` summary line, and under `--json` prints a single JSON object carrying the verdict and an empty findings list `[AC-1.2]`
- [ ] Given one fixture recipe per defect, when `validate` runs, then it exits 1 and reports exactly the matching finding code — `missing_section`, `missing_launch_command`, `missing_ready`, `missing_safety` (neither a `- **Variable:**` entry nor `- **Safety:** none — <reason>`), `bad_feature_row`, `duplicate_feature_id`, `bad_feature_id`, `secret_value` (a value containing `://user:pass@`, or a 32+ character token outside a backticked command), `bad_timeout` — and a missing or undecodable recipe path exits 2 `[AC-1.3]`
- [ ] Given the Writ repository, when the test suite runs, then a test asserts that `.writ/docs/app-verification.md` does not exist, so install's three-way overlay of `.writ/docs/*.md` can never collide with a project-authored recipe `[AC-1.4]`
- [ ] Given ADR-028 and the product docs, when the amendments land, then ADR-028 Decisions 1 and 2 name the recipe at `.writ/docs/app-verification.md` drafted by `/create-uat-plan` (replacing the `/initialize`-generated `verify-<app>` skill), record that Features 1 and 2 merged, and state that a script which launches only recipe-named commands and holds no state between runs is not a Writ runtime; `roadmap.md` Phase 12 merges Features 1 and 2, replaces the yuss.app success criterion with a fixture app, and drops the `/initialize` wording; `mission.md` and `mission-lite.md` Phase 12 lines match; and every pre-existing uncommitted edit in those files is preserved `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write failing tests in `scripts/tests/test_app_verify.py` (docstring naming `2026-10-01-behavioral-verification`): a valid recipe exits 0 with an `app-verify:` line and `--json` object; one temp-file recipe per finding code exits 1 with that code; missing and undecodable paths exit 2; a backticked long command is not `secret_value`; and the repo has no `.writ/docs/app-verification.md` `[AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.2 Write `.writ/docs/app-verification-format.md`: section list, settings format, feature-table grammar, safety and pattern semantics, secret rule, the finding vocabulary, and one worked example; reserve a pointer to the Story 3 fixture recipe as the second example `[AC-1.1]`
- [ ] 1.3 Implement `scripts/app-verify.py` with argparse subcommand `validate --recipe PATH [--json]` only (stdlib, Python 3.9 floor, exit 0 valid / 1 findings / 2 unreadable), following `scripts/build-smoke.py` and `scripts/exit-criteria.py` conventions, until 1.1 passes; leave `touched` and `run` to Story 3 `[AC-1.2, AC-1.3]`
- [ ] 1.4 Amend `.writ/decision-records/adr-028-behavioral-verification-and-cross-family-panels.md` Decisions 1 and 2 and its Implementation Plan item 1 per the spec's Origin and Technical Concerns, adding the runtime-boundary note `[AC-1.5]`
- [ ] 1.5 Edit `.writ/product/roadmap.md` Phase 12 (merged feature, fixture-app success criterion, Dependencies line, no `/initialize` generation wording) plus the Phase 12 lines in `.writ/product/mission.md` and `.writ/product/mission-lite.md`, with targeted `StrReplace` edits on top of the current working tree — never a checkout, restore, or whole-file rewrite `[AC-1.5]`
- [ ] 1.6 Verify acceptance criteria: run `validate` against the worked example in the format doc; `rg -n "verify-<app>" .writ/product .writ/decision-records` returns only historical or explicitly superseded mentions; `git diff` on the three product files shows the pre-existing edits intact `[AC-1.1, AC-1.5]`
- [ ] 1.7 Verify all tests pass: `uv run --python 3.9 pytest scripts/tests/test_app_verify.py`, full `uv run pytest`, the bash tests, and `bash scripts/eval.sh` (outside the sandbox) with Findings 0 `[AC-1.2, AC-1.3, AC-1.4]`

## Notes

- **Uncommitted product edits.** `roadmap.md`, `mission.md`, and `mission-lite.md` already carry uncommitted changes (including the 2026-10-01 reconcile pass and the in-flight `2026-10-01-product-check-direction` spec). Edit only the Phase 12 lines; do not stash, reset, or regenerate these files. Check `git diff` before and after.
- **Story 3 extends the same files.** `touched` and `run` land in `scripts/app-verify.py` and `scripts/tests/test_app_verify.py` later. Keep the recipe parser a reusable function (sections, settings, feature rows) so Story 3 reuses it rather than re-parsing.
- **Secret heuristic false positives.** The 32+ character token rule must skip backticked commands, or long `check` commands and globs would trip `secret_value`. URL credentials (`://user:pass@`) are flagged anywhere, including inside backticks.
- **eval.sh pins.** If the format doc or a command cites validator behavior, add `require_literal` pins in the Story 5 `app_verify` check, not here; this story adds no eval check.
- **Shipped doc, project-owned recipe.** The format doc ships to every project through the `.writ/docs/` overlay; the recipe it describes never does. Task 1.1's guard test is the only enforcement of that.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Read recipe, Validate recipe]
- **Shadow paths:** []
- **Business rules:** spec.md → ## 📋 Business Rules (Expanded) (1 Recipe shape, 3 Safety — names and patterns only, secret rejection); spec.md → ## 📋 Business Rules (1 Recipe sections)
- **Experience:** [State Catalog → Recipe invalid (`app-verify: recipe invalid — <first finding>`), Interaction Patterns → every line starts with `app-verify:`]
- **Technical:** sub-specs/technical-spec.md → ## Recipe Grammar (validator findings, pattern syntax); ## Integration Notes (install overlay); ## Files in Scope (Story 1 rows)
- **Product amendments:** spec.md → Origin header; spec.md → ⚠️ Technical Concerns (runtime boundary); spec.md → 💡 Recommendations (never ship `.writ/docs/app-verification.md`)
