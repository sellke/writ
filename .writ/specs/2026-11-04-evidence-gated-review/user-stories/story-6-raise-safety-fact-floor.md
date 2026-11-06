# Story 6: Raise the Safety Fact floor to `tested`

> **Status:** Completed ✅ (2026-11-04)
> **Commit:** 6af93b432efcc4f8cd426797902fe127112f5647
> **Priority:** Medium
> **Dependencies:** Story 4, Story 5

## User Story

**As a** Writ maintainer
**I want to** raise the Safety Fact floor from `traced` to `tested`
**So that** a Safety Fact passes Gate 3 only when a test from the recorded run backs it

## Acceptance Criteria

> **AC IDs assigned through:** AC-6.5

- [x] Given the shipped source after the edit, when its floor wording is read, then every place names `tested` as the floor: `FLOOR` in `scripts/review-override.py`, that file's docstring `Floor:` line and output example, `skills/blast-radius/SKILL.md`, and any other shipped floor wording, and no shipped text names `traced` as the floor. `[AC-6.1]`
- [x] Given the source edits, when `python3 scripts/gen-platform-trees.py` rebuilds the generated trees, then `python3 scripts/gen-platform-trees.py --check` passes, and the generated copies (`cursor/plugin/skills/blast-radius/SKILL.md`, `plugins/writ/skills/blast-radius/SKILL.md`, `plugins/writ/scripts/review-override.py`) name `tested` as the floor. `[AC-6.2]`
- [x] Given a Safety Fact section whose highest accepted rung is `traced`, when `review-override.py safety-fact` runs, then its output includes `reason: safety_fact_below_floor traced`. `[AC-6.3]`
- [x] Given a Safety Fact section whose highest accepted rung is `tested`, when `review-override.py safety-fact` runs, then its output has no `safety_fact_below_floor` reason line and no other reason line changes from before the floor change. `[AC-6.4]`
- [x] Given the updated tests, when pytest runs on Python 3.9 and 3.14, then no test asserts the `traced` floor, the trial-record checks in `test_gate_upgrade_trial.py` and `test_gate_upgrade_trial_outcome.py` still pass, and the reviewer-filters tests still pass unchanged. `[AC-6.5]`

## Implementation Tasks

- [x] 6.1 Write the failing behavior tests first. In `scripts/tests/test_review_override.py`, add `safety-fact` cases: a `traced`-only section returns `safety_fact_below_floor traced`, and a `tested` section returns no `safety_fact_below_floor` line and the same other reason lines as before. Name spec `2026-11-04-evidence-gated-review` in a comment above the cases. Run them and confirm the `traced` case is red on the current tree `[AC-6.3, AC-6.4]`
- [x] 6.2 Write a failing wording test in the same file. Read `scripts/review-override.py` and `skills/blast-radius/SKILL.md`. Assert `FLOOR = "tested"`, a docstring `Floor:` line that names `tested`, the output example `floor tested`, and "The floor is `tested`" in the skill. Assert that neither file names `traced` as the floor. Confirm it is red on the current tree `[AC-6.1]`
- [x] 6.3 Update the existing tests that assert the `traced` floor. In `test_review_override.py`, change `_sf_expected` to print `floor tested`. Change each `SafetyFactVerdictTests` case that expects `pass` at measured `traced` (technical-spec.md → `### Safety Fact floor (Story 6)` names them) to `tested` evidence, or to expect `safety_fact_below_floor traced`. Keep what each case tests. Re-grep `scripts/tests/` for `floor traced` and `traced` floor docstrings. Do not touch the reviewer-filters tests or the trial-record checks `[AC-6.5]`
- [x] 6.4 Set `FLOOR = "tested"` in `scripts/review-override.py`. Update the docstring `Floor:` line and the `floor traced` output example. Run the 6.1 and 6.2 tests to green `[AC-6.1, AC-6.3, AC-6.4]`
- [x] 6.5 Edit `skills/blast-radius/SKILL.md`: the Evidence Ladder floor sentence and the re-review `safety_fact_below_floor` advice, as technical-spec.md lists them. Grep `commands/`, `agents/`, `skills/`, `adapters/`, `.writ/docs/config-format.md`, `README.md`, and `SKILL.md` for any other `traced` floor wording and change it to `tested`. If this edits `commands/implement-story.md`, record `wc -c commands/implement-story.md` before and after in the What Was Built record `[AC-6.1]`
- [x] 6.6 Regenerate the platform trees with `python3 scripts/gen-platform-trees.py`, then run it with `--check`. Confirm the generated copies of the skill and the script name `tested` as the floor `[AC-6.2]`
- [x] 6.7 Verify with nothing else running in the checkout. Run `uv run --isolated --python 3.9 --with pytest pytest`, then the same with `--python 3.14`. Run `bash scripts/eval.sh`. Start the bash suite last, in the background, and wait for its completion notice `[AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5]`

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** []
- **Business rules:** `spec.md → ## Business Rules (Expanded) → ### Removals`, `technical-spec.md → ## Removals → ### Safety Fact floor (Story 6)`, `spec.md → ## Specification Contract → ### Amendment (2026-11-04, during /implement-spec)`
- **Experience:** []

---

## What Was Built

**Implementation Date:** 2026-11-04

### Files Created

[None created]

### Files Modified

- **`scripts/review-override.py`** (`FLOOR`, module docstring; +3 −3)
  - `FLOOR = "traced"` is now `FLOOR = "tested"`.
  - The docstring `Floor:` line and the output example `(measured <m>, floor tested)` name `tested`.
  - The comparison and the printed summary line already read `FLOOR`, so no other line changed.
- **`skills/blast-radius/SKILL.md`** (Evidence Ladder, re-review advice; +3 −3)
  - Evidence Ladder: "The floor is `tested`."
  - Re-review `safety_fact_below_floor` advice: "the measured rung is under `tested`. Cite a test from the recorded run; only the coder can add one." This is technical-spec.md's wording, word for word.
  - The rung definitions did not change.
- **`plugins/writ/scripts/review-override.py`, `cursor/plugin/skills/blast-radius/SKILL.md`, `plugins/writ/skills/blast-radius/SKILL.md`**: generated by `python3 scripts/gen-platform-trees.py`. Each differs from its source only by the generated-header line.
- **`scripts/tests/test_review_override.py`** (3455 → 3591 lines; +176 −40)
  - New: `SafetyFactTestedFloorTests` (2 tests) and `SafetyFactFloorWordingTests` (2 tests), under a comment that names `2026-11-04-evidence-gated-review`.
  - New constant `SF_TESTED`, the `tested` evidence line that `SF_TESTS_OK` backs.
  - `_sf_expected` prints `floor tested`.
  - 13 existing cases now cite `tested` evidence. Two of them were re-shaped:
    - `test_overclaim_alone_is_not_a_reason`: claimed `reproduced`, measured `tested`, pass.
    - `test_underclaim_prints_measured`: claimed `read`, measured `tested`, pass.
  - 3 cases keep `traced` and now expect `safety_fact_below_floor traced`:
    - `test_fields_case_insensitive_bold_optional`
    - `test_repo_defaults_to_cwd`
    - `SafetyFactRungTests.test_traced_existence_only_when_blast_path_missing`. technical-spec.md did not list it. Gate 1 found it and fixed it.
  - `test_below_floor_alone`: the docstring names the `tested` floor.
  - The reviewer-filters tests and the trial-record checks have no diff.

### Implementation Decisions

1. **The script change is the constant and two docstring lines.** The floor comparison and the summary line already format `FLOOR`. Gate 3 routes on the reason name `safety_fact_below_floor`, never on the rung, so no routing changed (Business Rule 4).
2. **Re-shaped tests keep what they guarded.** Cases that tested parsing, cwd resolution, or an unreadable blast-radius path keep `traced` evidence and assert the below-floor result. Every other case moved to `tested` evidence, so its single-reason assertion still isolates one reason.
3. **The wording tests read all three generated copies.** A stale generated copy fails the test (mutants M8, M9 killed).
4. **The AC-6.4 guard passes on the old source.** `test_tested_section_keeps_every_other_reason` covers 8 reason combinations at measured `tested`. Passing at HEAD shows those reason lines did not change. Mutant M3 (`<` → `<=`) turns it red.

### Test Results

**Verification:** Automated, test-first
**Coverage:** unverifiable (no coverage report)

- ✅ Gate 1 red: 3 failed, 1 passed. The passing test is the AC-6.4 guard, which passes on the old source on purpose.
- ✅ Gate 1 green: `test_review_override.py` 201 passed. That is the recorded run, `exit code: 0`.
- ✅ Gate 3 mutations: 12 of 14 killed. The survivors M12 and M13 were wording-test gaps. The orchestrator closed both, and both mutants are now killed.
- ✅ Full suite on 3.9: 4216 passed, 2 skipped, 0 failed.
- ✅ Full suite on 3.14: 4216 passed, 2 skipped, 0 failed, 1246 subtests.
- ✅ Bash suite: all green.
- ✅ `python3 scripts/gen-platform-trees.py --check`: pass.
- ✅ `bash scripts/eval.sh`: exit 0.

### Byte count

`commands/implement-story.md` was not edited: 39929 bytes before and after.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** Every coder change is Owned or a required generated copy. The Story 7 file holds an orchestrator note, which is outside this story's change set and was left out of this commit.

### Gate record

**REVIEW_RESULT:** PASS

Iteration 1, `review-agent`, saved at `.writ/state/gate3-review-story-6-raise-safety-fact-floor.md`.

- No Critical or Major issues. All five ACs are met.
- 12 of 14 mutations killed. The two survivors were wording-test gaps:
  - M12: an added sentence "`traced` is the floor." survived.
  - M13: the old advice text survived.
- After the PASS, the orchestrator closed both gaps. `test_skill_floor_is_tested` now asserts the exact advice sentence, and `TRACED_FLOOR` now matches `traced` as the floor in either word order. Both mutants are killed.

- **Gate 0:** arch-check pass (rederived proceed). No `gate0-divergence:` line applies, because design-divergence Story 6 removed that surface.
- **Gate 0.5:** boundary map computed (`.writ/state/boundary-story-6-raise-safety-fact-floor.json`)
- **Gate 1:** coding-agent, test-first. Red: 3 failed, 1 passed (the AC-6.4 guard, on purpose). Green: 201 passed.
- **Gate 2:** no linters. `arch-lint: none — see .writ/docs/architecture-lint.md`. `build-smoke: unverifiable (unsupported_stack)`
- **Gate 2.5:** cross-component. `gate3-route: review-agent (outside_boundary generated copies)`
- **Gate 3:** `reviewer-filters: on`. 1 iteration: PASS. `review-override check`: pass. `safety-fact: tested (claimed tested), floor tested`, the first Gate 3 under the new floor. `review-panel: skipped — platform cannot spawn other vendors`. `jev: not run`. `evidence-gate: not run (PASS)`, because there was no agent FAIL.
- **Gate 3.5:** drift None. drift-format: `fail large_drift_without_pause`. This is the known false positive from Story 1's DEV-001, so no PAUSE line was added.
- **Gate 4:**
  - Full suite: 4216 passed, 2 skipped, 0 failed on 3.9 and on 3.14. 3.14 also ran 1246 subtests.
  - Bash suite: green. `gen-platform-trees.py --check`: pass. `eval.sh`: exit 0.
  - Coverage: unverifiable (no report).
- **Gate 4.5:** `app-verify: unverifiable (no_recipe)`
- **Gate 5:** `docs-check: unverifiable (no public exports in the changed set)`

### Deviations from Spec

None

### Notes for Downstream Stories

- **Behavior change.** A Safety Fact that can only reach `traced` now fails Gate 3. That includes `- traced: none` for a no-consumer change. To pass, the reviewer cites `- tested:` from the recorded run, or the coder adds a test, at the cost of one loop increment. The contract chose this (Must Include 6, Business Rule 4).
- **Follow-up candidate, not fixed.** A `Holds: no` section always hits the floor. That spends one reviewer re-spawn before Gate 3 FAILs, which is the right outcome. A possible issue: skip the re-spawn when `Holds: no` agrees with a FAIL or PAUSE verdict.
- **Dev-only.** `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py:427` strips `exit code:` lines. A rerun of its safety-fact arm would always measure below the floor.
