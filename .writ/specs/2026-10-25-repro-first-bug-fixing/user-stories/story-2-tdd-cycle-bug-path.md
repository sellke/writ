# Story 2: The tdd-cycle Bug Path

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** developer fixing a bug through Writ, whose coding agent reads `skills/tdd-cycle/SKILL.md` **I want to** find one bug path in that skill that says where to reproduce the bug, what to commit before the fix, and how to check the order **So that** my fix arrives with a failing repro committed first and a check that proves the order.

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given `skills/tdd-cycle/SKILL.md`, when its headings and text are read, then a `### Bug fixes: repro first` section follows `### Staying honest` and holds the skip line naming `- **Repro First:** off`, a recognition rule (an issue with `**Type:** Bug`, a file under `.writ/issues/bugs/`, a spec Origin citing such a file, or wording that existing behavior is wrong), the deciding test (a test can fail today because the code does the wrong thing, not because code is missing), and a surface rule that names the entry point where the bug shows `[AC-2.1]`
- [ ] Given that section, when its steps are read, then it requires a failing repro that fails for the bug's reason, a repro commit that changes test files only and carries a `Repro:` trailer, a fix commit that leaves the repro's test files untouched, the command `python3 scripts/repro-order.py check`, and the escape `Repro: none` with a stated reason and no `Repro:` trailer `[AC-2.2]`
- [ ] Given the When to Use section and the Examples section, when the bug bullet and the bug example are read, then the bullet names `### Bug fixes: repro first`, and the example shows a repro commit line with its `Repro:` trailer, a fix commit line, and a `repro-order: pass` check line in place of the former `parseDate('')` example `[AC-2.3]`
- [ ] Given `.writ/docs/config-format.md`, when its Supported Keys table and sections are read, then a `Repro First` row exists and a `## Repro First` section gives the values `on` and `off` (case-insensitive), states that an absent key means `on`, states that commands never detect or offer to save the key, and lists what `off` changes per Business Rule 9 `[AC-2.4]`
- [ ] Given the finished change, when the checks run, then `bash scripts/lint-skill.sh skills/tdd-cycle/SKILL.md` exits 0, the step 1 scan in `skills/plain-prose/SKILL.md` reports no unresolved hit in the new text, `python3 scripts/gen-platform-trees.py --check` exits 0, and `scripts/tests/test_repro_first_wiring.py` passes `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write `test_section_present`, `test_skip_line`, `test_recognition_and_surface`, `test_repro_fix_check_order`, `test_no_repro_escape`, `test_when_to_use_points_here`, `test_example_shows_bug_path`, `test_config_row`, and `test_config_section` in `scripts/tests/test_repro_first_wiring.py`. Read the files as text, stdlib only, in the style of `scripts/tests/test_prompting_guide.py`. Run the file and confirm the tests fail because the section, example, and config entries do not exist yet `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [ ] 2.2 Write `### Bug fixes: repro first` after `### Staying honest` in `skills/tdd-cycle/SKILL.md`, from the skill section draft in the technical spec. Keep the skip line, the recognition rule, the surface rule, the steps, and the no-repro escape. Use the Business Rules listed in Context for Agents `[AC-2.1, AC-2.2]`
- [ ] 2.3 In `skills/tdd-cycle/SKILL.md`, point the bug bullet under `## When to Use` at `### Bug fixes: repro first`, and replace the bug example under `## Examples` with the repro commit, fix commit, and check lines `[AC-2.3]`
- [ ] 2.4 Add a `Repro First` row to the Supported Keys table in `.writ/docs/config-format.md`, and add a `## Repro First` section after `## Review Panel` that follows that section's pattern `[AC-2.4]`
- [ ] 2.5 Run the step 1 scan from `skills/plain-prose/SKILL.md` on the new skill text and on the new config section. Fix each hit without dropping a rule. Run `bash scripts/lint-skill.sh skills/tdd-cycle/SKILL.md` and fix any finding `[AC-2.1, AC-2.5]`
- [ ] 2.6 Run `python3 scripts/gen-platform-trees.py`, then `python3 scripts/gen-platform-trees.py --check`. Do not hand-edit any generated tree `[AC-2.5]`
- [ ] 2.7 Verify: `uv run --python 3.9 pytest scripts/tests/test_repro_first_wiring.py` passes; then run `uv run --python 3.9 pytest`, the bash test loop, and `bash scripts/eval.sh` outside any sandbox. All must pass `[AC-2.5]`

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

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
