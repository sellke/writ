# Story 2: /prototype Step 2.5 Loads the Skill

> **Status:** Completed ✅ (2026-10-26)
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer
**I want to** replace the inline divergence rules in `/prototype` Step 2.5 with a `Read` of `skills/design-divergence/SKILL.md`, leaving the gate, draft definition, render table, present-and-choose, and exploration record in the command
**So that** the rules for getting differing drafts live in one place, and the Gate 0 caller added in Story 3 can use the same skill without a second copy of the rules

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.4

- [x] Given commands/prototype.md, when Step 2.5's `#### Getting drafts that actually differ` subsection is read, then it contains `Read skills/design-divergence/SKILL.md`, states that the step owns when drafts are made, what a draft is, how they render, and the record, and no longer contains the inline rules "Declare the axes first." or "Use ordinary personas, not visionary ones." `[AC-2.1]`
- [x] Given the existing pins, when `uv run pytest scripts/tests/test_platform_neutral_names.py` runs, then the prototype tests pass unchanged: the render table under `#### Render through the platform` keeps its three rows in order, `Never degrade silently.` stays, Step 2 still names `.writ/docs/design-system.md` and `canvas-preview`, and "Mockups for a spec that already exists" and "Terminal constraint:" stay. `[AC-2.2]`
- [x] Given the diff to commands/prototype.md, when it is inspected, then only the replaced subsection body and one added `## References` link changed: the gate paragraph, the `--diverge`/`--no-diverge` rows, `#### What a draft is`, `#### Present and choose`, the exploration.md paragraph, and the frontmatter are byte-identical, and the file is smaller than before. `[AC-2.3]`
- [x] Given `python3 scripts/gen-platform-trees.py` was run, when `python3 scripts/gen-platform-trees.py --check`, `uv run pytest`, `uv run --python 3.9 pytest`, and `bash scripts/eval.sh` run, then all pass with 0 findings and the generated plugin copy of prototype.md matches the source. `[AC-2.4]`

## Implementation Tasks

- [x] 2.1 Add tests to `scripts/tests/test_design_divergence_wiring.py` asserting the `Read skills/design-divergence/SKILL.md` line in Step 2.5, the absence of the two inline rules, and the References link `[design-divergence](../skills/design-divergence/SKILL.md)` `[AC-2.1, AC-2.3]`
- [x] 2.2 Replace the body under `#### Getting drafts that actually differ` in `commands/prototype.md` Step 2.5 (the five numbered rules) with the `Read` note from `technical-spec.md` → `/prototype` Step 2.5 `[AC-2.1]`
- [x] 2.3 Add `[design-divergence](../skills/design-divergence/SKILL.md)` to the `## References` section of `commands/prototype.md` `[AC-2.3]`
- [x] 2.4 Regenerate the platform trees with `python3 scripts/gen-platform-trees.py`; do not hand-edit `plugins/writ/commands/prototype.md` `[AC-2.4]`
- [x] 2.5 Verify acceptance criteria: run the Step 2.5 wiring tests, the `test_platform_neutral_names.py` prototype tests, and a byte-count comparison of `commands/prototype.md` against its pre-change version to confirm the file shrank and the untouched sections are identical `[AC-2.1, AC-2.2, AC-2.3]`
- [x] 2.6 Verify all tests pass: `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests in `scripts/tests/test_*.sh`, and `bash scripts/eval.sh` (run outside the sandbox) `[AC-2.4]`

## Notes

- `scripts/tests/test_platform_neutral_names.py` pins `### Step 2.5: Diverge & Choose` followed by `#### Render through the platform`, and the three render-table labels. Keep that heading order and the table unchanged.
- The replacement note must not reuse the exact strings the new test forbids. "axes declared first" (lowercase, from the technical spec note) is fine. "Declare the axes first." and "Use ordinary personas, not visionary ones." must not appear.
- `scripts/tests/test_prototype_worktree_integration.py` reads Step 3 of both `commands/prototype.md` and `plugins/writ/commands/prototype.md`. Regenerate the plugin copy rather than hand-editing it.
- `scripts/tests/test_design_divergence_wiring.py` is created by Story 1. Story 2 adds to it. Story 3 adds the Gate 0 assertions.
- `/prototype` is the first live caller of the skill. Story 3 adds the second caller (Gate 0 in `commands/implement-story.md`).
- The Gate 0 switch from Story 3 (`- **Gate 0 Divergence:** off`) does not affect `/prototype`. Do not add a switch check to Step 2.5.
- Risk: the skill's `## How to Apply` rules must cover everything the removed inline rules said, or `/prototype` loses guidance. Check Story 1's skill against the five removed rules before replacing them.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** [Solo builder running /prototype on an unsettled idea (spec.md → Experience Design → Who uses it)]
- **Business rules:** [Skill boundary: the skill owns how to get differing alternatives; the caller owns when to run it, what a draft is, how drafts render, and where the decision is recorded (spec.md → Business Rules (Expanded) → 9)]
- **Experience:** [/prototype behavior unchanged except that divergence rules come from the skill (spec.md → Experience Design → Who uses it)]

Replacement text for the Step 2.5 subsection: technical-spec.md → `/prototype` Step 2.5 (Story 2). Frontmatter, gate paragraph, render table, and `Never degrade silently.` stay as they are (technical-spec.md → `/prototype` Step 2.5).

---

## What Was Built

**Implementation Date:** 2026-10-26

### Files Created

[None created]

### Files Modified

- **`commands/prototype.md`** (Step 2.5 `#### Getting drafts that actually differ`; `## References`)
  - The lead-in and five numbered rules are replaced by the technical-spec note: `Read skills/design-divergence/SKILL.md`, what the step owns, "Default to three drafts." One References link added. 18773 → 18034 bytes.
- **`plugins/writ/commands/prototype.md`**, **`cursor/plugin/commands/prototype.md`** — regenerated by `scripts/gen-platform-trees.py`.
- **`scripts/tests/test_design_divergence_wiring.py`** (Story 2 section)
  - 8 tests: the Read line and ownership clause, the two removed rule strings absent from the whole file, no numbered rules left, render-table row order and `Never degrade silently.`, one References link, the plugin copy carries the skill path.

### Implementation Decisions

1. **Lead-in removed with the rules** — it only introduced them; the skill's rule 7 carries the anti-pattern.
2. **Byte-identity checked at verification time, not as a test** — HEAD moves; the gate paragraph, `--diverge`/`--no-diverge` rows, What a draft is, Render through the platform, Present and choose, `exploration.md`, Step 2, and the frontmatter matched `git show HEAD:commands/prototype.md` section by section.

### Test Results

**Verification:** `uv run pytest scripts/tests/test_design_divergence_wiring.py scripts/tests/test_platform_neutral_names.py scripts/tests/test_prototype_worktree_integration.py -q` → 84 passed; full `uv run pytest` and `uv run --python 3.9 pytest` → 3180 passed, 2 skipped; bash tests 0 FAIL; `bash scripts/eval.sh` → 0 findings; `gen-platform-trees.py --check` → pass.
- ✅ test-integrity authenticity: pass

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** hand edits inside owned files; the Cursor copy is generator output
- **gate3-route:** review-agent (outside_boundary cursor/plugin/commands/prototype.md)
- **review-panel:** skipped — platform cannot spawn other vendors

### Deviations from Spec

None
