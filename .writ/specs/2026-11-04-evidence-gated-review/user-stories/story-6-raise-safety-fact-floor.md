# Story 6: Raise the Safety Fact floor to `tested`

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 4, Story 5

## User Story

**As a** Writ maintainer
**I want to** raise the Safety Fact floor from `traced` to `tested`
**So that** a Safety Fact passes Gate 3 only when a test from the recorded run backs it

## Acceptance Criteria

> **AC IDs assigned through:** AC-6.5

- [ ] Given the shipped source after the edit, when its floor wording is read, then every place names `tested` as the floor: `FLOOR` in `scripts/review-override.py`, that file's docstring `Floor:` line and output example, `skills/blast-radius/SKILL.md`, and any other shipped floor wording, and no shipped text names `traced` as the floor. `[AC-6.1]`
- [ ] Given the source edits, when `python3 scripts/gen-platform-trees.py` rebuilds the generated trees, then `python3 scripts/gen-platform-trees.py --check` passes, and the generated copies (`cursor/plugin/skills/blast-radius/SKILL.md`, `plugins/writ/skills/blast-radius/SKILL.md`, `plugins/writ/scripts/review-override.py`) name `tested` as the floor. `[AC-6.2]`
- [ ] Given a Safety Fact section whose highest accepted rung is `traced`, when `review-override.py safety-fact` runs, then its output includes `reason: safety_fact_below_floor traced`. `[AC-6.3]`
- [ ] Given a Safety Fact section whose highest accepted rung is `tested`, when `review-override.py safety-fact` runs, then its output has no `safety_fact_below_floor` reason line and no other reason line changes from before the floor change. `[AC-6.4]`
- [ ] Given the updated tests, when pytest runs on Python 3.9 and 3.14, then no test asserts the `traced` floor, the trial-record checks in `test_gate_upgrade_trial.py` and `test_gate_upgrade_trial_outcome.py` still pass, and the reviewer-filters tests still pass unchanged. `[AC-6.5]`

## Implementation Tasks

- [ ] 6.1 Write the failing behavior tests first. In `scripts/tests/test_review_override.py`, add `safety-fact` cases: a `traced`-only section returns `safety_fact_below_floor traced`, and a `tested` section returns no `safety_fact_below_floor` line and the same other reason lines as before. Name spec `2026-11-04-evidence-gated-review` in a comment above the cases. Run them and confirm the `traced` case is red on the current tree `[AC-6.3, AC-6.4]`
- [ ] 6.2 Write a failing wording test in the same file. Read `scripts/review-override.py` and `skills/blast-radius/SKILL.md`. Assert `FLOOR = "tested"`, a docstring `Floor:` line that names `tested`, the output example `floor tested`, and "The floor is `tested`" in the skill. Assert that neither file names `traced` as the floor. Confirm it is red on the current tree `[AC-6.1]`
- [ ] 6.3 Update the existing tests that assert the `traced` floor. In `test_review_override.py`, change `_sf_expected` to print `floor tested`. Change each `SafetyFactVerdictTests` case that expects `pass` at measured `traced` (technical-spec.md → `### Safety Fact floor (Story 6)` names them) to `tested` evidence, or to expect `safety_fact_below_floor traced`. Keep what each case tests. Re-grep `scripts/tests/` for `floor traced` and `traced` floor docstrings. Do not touch the reviewer-filters tests or the trial-record checks `[AC-6.5]`
- [ ] 6.4 Set `FLOOR = "tested"` in `scripts/review-override.py`. Update the docstring `Floor:` line and the `floor traced` output example. Run the 6.1 and 6.2 tests to green `[AC-6.1, AC-6.3, AC-6.4]`
- [ ] 6.5 Edit `skills/blast-radius/SKILL.md`: the Evidence Ladder floor sentence and the re-review `safety_fact_below_floor` advice, as technical-spec.md lists them. Grep `commands/`, `agents/`, `skills/`, `adapters/`, `.writ/docs/config-format.md`, `README.md`, and `SKILL.md` for any other `traced` floor wording and change it to `tested`. If this edits `commands/implement-story.md`, record `wc -c commands/implement-story.md` before and after in the What Was Built record `[AC-6.1]`
- [ ] 6.6 Regenerate the platform trees with `python3 scripts/gen-platform-trees.py`, then run it with `--check`. Confirm the generated copies of the skill and the script name `tested` as the floor `[AC-6.2]`
- [ ] 6.7 Verify with nothing else running in the checkout. Run `uv run --isolated --python 3.9 --with pytest pytest`, then the same with `--python 3.14`. Run `bash scripts/eval.sh`. Start the bash suite last, in the background, and wait for its completion notice `[AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5]`

## Notes

**Codebase facts (verify at implementation; line numbers are from 2026-11-04)**
- `scripts/review-override.py`: `FLOOR = "traced"` at line 276. The docstring `Floor:` line is at lines 43 to 44, and the output example `(measured <m>, floor traced)` is at line 48. The printed summary line already formats `FLOOR`, so only the constant and the docstring change.
- `skills/blast-radius/SKILL.md`: "The floor is `traced`" at lines 34 to 35, and the re-review `safety_fact_below_floor` advice at line 119. The file-by-file list is `technical-spec.md` → `## Removals` → `### Safety Fact floor (Story 6)`.
- Only `test_review_override.py` asserts the `traced` floor today: `_sf_expected` (line 731) and the `SafetyFactVerdictTests` pass cases that use `TRACED` evidence.
- `commands/implement-story.md` and `agents/review-agent.md` say "below floor" without naming a rung, so this story should not need to edit them.
- Generated trees are rebuilt, never hand-edited. `gen-platform-trees.py` writes the skill copies under `cursor/plugin/` and `plugins/writ/`, and the script copy under `plugins/writ/scripts/`.
- Python 3.9 floor: stdlib only, no `match` statements, no 3.10+ `pathlib` or `str` methods.

**Scope limits**
- The reviewer filters stay (`spec.md` → `### Amendment (2026-11-04, during /implement-spec)`). Do not edit the filters skill, the `reviewer-filters` switch, its config key, the agents' `reviewer_filters` lines, or their tests.
- Do not touch the review panel. Story 7 owns it.
- Do not edit ADRs, specs, other `.writ/` history, or `pruned-instructions-ledger.md` (`spec.md` → `### Corrections made at authoring (2026-11-04)`, item 1).
- Gate 3's Safety Fact routing is unchanged (Business Rule 4). Only the floor moves.

**Ordering and gates**
- Story 6 follows Stories 4 and 5, which also edit `scripts/review-override.py` and `scripts/tests/test_review_override.py`.
- Run pytest alone. `eval.sh`, the bash suite, and writes under `.writ/state/` must not overlap a pytest run.

**Byte budget**
- This story is not expected to edit `commands/implement-story.md`. If it does, record `wc -c` before and after. The net across the stories that edit it must be zero or less (`technical-spec.md` → `## Byte Budget`).

**Assumptions**
- `user_type` was not supplied. "Writ maintainer" is inferred from the spec owner and the repo's purpose.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** []
- **Business rules:** `spec.md → ## Business Rules (Expanded) → ### Removals`, `technical-spec.md → ## Removals → ### Safety Fact floor (Story 6)`, `spec.md → ## Specification Contract → ### Amendment (2026-11-04, during /implement-spec)`
- **Experience:** []
