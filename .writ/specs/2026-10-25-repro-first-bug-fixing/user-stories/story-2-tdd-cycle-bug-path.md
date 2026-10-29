# Story 2: The tdd-cycle Bug Path

> **Status:** Completed ✅ (2026-10-29)
> **Commit:** c687fab2d5597b715f99886383f29af690cf0695
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** developer fixing a bug through Writ, whose coding agent reads `skills/tdd-cycle/SKILL.md` **I want to** find one bug path in that skill that says where to reproduce the bug, what to commit before the fix, and how to check the order **So that** my fix arrives with a failing repro committed first and a check that proves the order.

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given `skills/tdd-cycle/SKILL.md`, when its headings and text are read, then a `### Bug fixes: repro first` section follows `### Staying honest` and holds the skip line naming `- **Repro First:** off`, a recognition rule (an issue with `**Type:** Bug`, a file under `.writ/issues/bugs/`, a spec Origin citing such a file, or wording that existing behavior is wrong), the deciding test (a test can fail today because the code does the wrong thing, not because code is missing), and a surface rule that names the entry point where the bug shows `[AC-2.1]`
- [x] Given that section, when its steps are read, then it requires a failing repro that fails for the bug's reason, a repro commit that changes test files only and carries a `Repro:` trailer, a fix commit that leaves the repro's test files untouched, the command `python3 scripts/repro-order.py check`, and the escape `Repro: none` with a stated reason and no `Repro:` trailer `[AC-2.2]`
- [x] Given the When to Use section and the Examples section, when the bug bullet and the bug example are read, then the bullet names `### Bug fixes: repro first`, and the example shows a repro commit line with its `Repro:` trailer, a fix commit line, and a `repro-order: pass` check line in place of the former `parseDate('')` example `[AC-2.3]`
- [x] Given `.writ/docs/config-format.md`, when its Supported Keys table and sections are read, then a `Repro First` row exists and a `## Repro First` section gives the values `on` and `off` (case-insensitive), states that an absent key means `on`, states that commands never detect or offer to save the key, and lists what `off` changes per Business Rule 9 `[AC-2.4]`
- [x] Given the finished change, when the checks run, then `bash scripts/lint-skill.sh skills/tdd-cycle/SKILL.md` exits 0, the step 1 scan in `skills/plain-prose/SKILL.md` reports no unresolved hit in the new text, `python3 scripts/gen-platform-trees.py --check` exits 0, and `scripts/tests/test_repro_first_wiring.py` passes `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Write `test_section_present`, `test_skip_line`, `test_recognition_and_surface`, `test_repro_fix_check_order`, `test_no_repro_escape`, `test_when_to_use_points_here`, `test_example_shows_bug_path`, `test_config_row`, and `test_config_section` in `scripts/tests/test_repro_first_wiring.py`. Read the files as text, stdlib only, in the style of `scripts/tests/test_prompting_guide.py`. Run the file and confirm the tests fail because the section, example, and config entries do not exist yet `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [x] 2.2 Write `### Bug fixes: repro first` after `### Staying honest` in `skills/tdd-cycle/SKILL.md`, from the skill section draft in the technical spec. Keep the skip line, the recognition rule, the surface rule, the steps, and the no-repro escape. Use the Business Rules listed in Context for Agents `[AC-2.1, AC-2.2]`
- [x] 2.3 In `skills/tdd-cycle/SKILL.md`, point the bug bullet under `## When to Use` at `### Bug fixes: repro first`, and replace the bug example under `## Examples` with the repro commit, fix commit, and check lines `[AC-2.3]`
- [x] 2.4 Add a `Repro First` row to the Supported Keys table in `.writ/docs/config-format.md`, and add a `## Repro First` section after `## Review Panel` that follows that section's pattern `[AC-2.4]`
- [x] 2.5 Run the step 1 scan from `skills/plain-prose/SKILL.md` on the new skill text and on the new config section. Fix each hit without dropping a rule. Run `bash scripts/lint-skill.sh skills/tdd-cycle/SKILL.md` and fix any finding `[AC-2.1, AC-2.5]`
- [x] 2.6 Run `python3 scripts/gen-platform-trees.py`, then `python3 scripts/gen-platform-trees.py --check`. Do not hand-edit any generated tree `[AC-2.5]`
- [x] 2.7 Verify: `uv run --python 3.9 pytest scripts/tests/test_repro_first_wiring.py` passes; then run `uv run --python 3.9 pytest`, the bash test loop, and `bash scripts/eval.sh` outside any sandbox. All must pass `[AC-2.5]`

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Notes

- **Story 1 must exist first.** The skill names `scripts/repro-order.py check`. `scripts/eval.sh` `check_referenced_paths` resolves that path, so `eval.sh` fails until Story 1 lands the script.
- **Keep the bug path one removable section.** All bug-path prose sits under `### Bug fixes: repro first`, plus the bug bullet and the bug example. The removal inventory restores the original two-line `parseDate('')` example from git HEAD. Do not spread bug-path text into other parts of the skill.
- **lint-skill body patterns.** The section must not contain `Read skills/` or `Read commands/`, must not start a line with a slash command, and must not dispatch a subagent. The Examples block uses `red:`, `commit:`, `check:` line labels, which pass. Leave the frontmatter `description` as a verb phrase.
- **Exact skip line.** Write `- **Repro First:** off` with the same spacing as `.writ/docs/config-format.md`. The wiring test matches it as text, and the config reader in Story 1 reads the same line.
- **Wiring test file.** Stories 3 and 4 extend `scripts/tests/test_repro_first_wiring.py`. Keep the helper functions and constants at module level and simple.
- **ac-trace attribution.** Name the spec `2026-10-25-repro-first-bug-fixing` in the module docstring of `test_repro_first_wiring.py`, and give each test an AC comment or docstring token. The file is test-shaped, so bare AC tokens count as test citations, and naming the spec keeps them from attaching to other specs.
- **Generated trees.** The skill text appears in the generated platform trees. Task 2.6 regenerates them. Do not edit `claude-code/`, `cursor/`, `codex/`, or plugin trees by hand.
- **Plain prose.** Apply `skills/plain-prose/SKILL.md` to the new text. Use few em-dashes.

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path: repro commit, fix commit, check `pass`)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` Rule 1 (Recognition, with the deciding test), Rule 2 (Surface and the harness-gap note), Rule 3 (Valid red), Rule 4 (Repro commit), Rule 5 (Fix commits and the wrong-repro reset), Rule 8 (No repro possible and its reason), Rule 9 (The switch and what `off` changes)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Switch off; Bug, no repro possible)
- **Skill text source:** `technical-spec.md → ## Skill Section Draft` and its Examples block; `technical-spec.md → ## Consumer Lines` is out of scope for this story
- **Config row and section:** `technical-spec.md → ## Config Row`; the section pattern is `.writ/docs/config-format.md → ## Review Panel`
- **Test list:** `technical-spec.md → ## Tests → ### scripts/tests/test_repro_first_wiring.py (Stories 2–4)`; this story covers the skill and config-row assertions only
- **Story boundary:** `spec.md → ## Detailed Requirements → ### Story 2` names this story's scope. Stories 3 and 4 own the agent report and the consumer lines.

## What Was Built

**Implementation Date:** 2026-10-29

### Files Created

- **`scripts/tests/test_repro_first_wiring.py`** — 10 text tests (AC-2.1..AC-2.5): section present after `### Staying honest`, exact skip line, recognition and surface rules, repro / fix / check steps, the scoped `Repro: none` escape, the When to Use pointer, the example (trailer on its own line, order red < repro commit < green < fix commit < check), the config row and section (order after `## Reviewer Filters`, not adjacency), and `bash scripts/lint-skill.sh skills/tdd-cycle/SKILL.md`. Module-level helpers (`read`, `headings`, `section`, `flat`, `table_rows`, `bug_section`, `assert_in_order`) for Stories 3 and 4.

### Files Modified

- **`skills/tdd-cycle/SKILL.md`** (120 → 160 lines) — `### Bug fixes: repro first` after `### Staying honest`: skip line `- **Repro First:** off`, recognition rule with the deciding test, six steps (reproduce on the surface, valid red, repro commit with the `Repro:` trailer in the last paragraph with other trailers, separate fix, `python3 scripts/repro-order.py check --repo . --base <commit before the repro>`, carry forward), and the `Repro: none` escape. The When to Use bug bullet points at the section; the bug example shows red / repro commit with its trailer line / green / fix commit / `repro-order: pass`.
- **`.writ/docs/config-format.md`** — `Repro First` row (technical-spec Config Row text) and a `## Repro First` section after `## Reviewer Filters`: values, defaults, never detected or saved, first match, key case, the value reason line, and every Business Rule 9 effect of `off`.
- Regenerated: `plugins/writ/skills/tdd-cycle/SKILL.md` (script path rewritten to `${CLAUDE_PLUGIN_ROOT}`), `cursor/plugin/skills/tdd-cycle/SKILL.md`.

### Implementation Decisions

1. **Trailer layout** — `Repro:` shares the last paragraph with `Ref:` / `Co-Authored-By:`; the example shows it on its own line (DEV-006).
2. **Config placement** — after `## Reviewer Filters` with the switch sections (DEV-005).
3. **Clauses beyond the draft** — each traces to Business Rules 1–5 and 8 (bug-or-not sentence, valid red, at least one test file, fixtures and un-skipping, reset only unpushed commits).
4. **Leanness** — the skills-surface warning predates this story (2396 lines vs a 1833 ceiling); no baseline edit.

### Test Results

**Verification:** `uv run --python 3.9 pytest scripts/tests/test_repro_first_wiring.py scripts/tests/test_repro_order.py -q` → 46 passed; full `uv run --python 3.9 pytest -q` → 3491 passed, 3 skipped; coding agent's bash loop → 51/51; `bash scripts/eval.sh` → 0 findings; `lint-skill.sh skills/tdd-cycle/SKILL.md` → pass; plain-prose step 1 scan → 0 hits; `gen-platform-trees.py --check` → pass.
- ✅ test-integrity authenticity: pass
- coverage: no new source files in this story

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Clean (markdown plus a text test; one list-argv `bash` call)
- **Boundary Compliance:** three owned files; two generated copies justified
- **gate3-route:** review-agent (outside_boundary cursor/plugin/skills/tdd-cycle/SKILL.md; outside_boundary plugins/writ/skills/tdd-cycle/SKILL.md)
- **reviewer-filters:** on
- **gate0-divergence:** skip (route evaluator-agent)
- **review-panel:** skipped — platform cannot spawn other vendors
- **review-override check:** pass (no blocking helper finding)
- **safety-fact:** traced (claimed traced) — no file depends on the replaced bullet or example
- **arch-lint:** none — see .writ/docs/architecture-lint.md
- **app-verify:** unverifiable (no_recipe)
- **docs-check:** unverifiable (no public exports in the changed set)

### Deviations from Spec

- **[DEV-005] `## Repro First` after `## Reviewer Filters`** — Severity: Small — Resolution: Auto-amended
- **[DEV-006] `Repro:` trailer shares the last paragraph; example shows it on its own line** — Severity: Small — Resolution: Auto-amended
- **[DEV-007] Removal Inventory row 1 omits the When to Use bullet** — Severity: Small — Resolution: Auto-amended
