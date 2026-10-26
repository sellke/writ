# Story 1: Upgrade switches

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** maintainer running the Phase 15 removal trial, and the `/implement-story` orchestrator
**I want to** resolve the `safety-fact` and `reviewer-filters` switches from one config line each
**So that** a trial arm flips with one line, and every Gate 3 run reads the same switch state

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.4

- [ ] Given `.writ/config.md` contains `- **Safety Fact:** off` (or `OFF`, or any other letter case), when `review-override.py switch --name safety-fact` runs, then line 1 of stdout is `off`, a `reason: config_off` line follows, and the exit code is 0 `[AC-1.1]`
- [ ] Given no `.writ/config.md`, or the file exists with no line for the switch, or the line's value is `on` or empty, when `review-override.py switch --name <switch>` runs, then line 1 is `on` with `reason: no_config`, `reason: no_config_line`, or `reason: config_on` respectively, and the exit code is 0 `[AC-1.2]`
- [ ] Given `.writ/config.md` contains `- **Reviewer Filters:** of`, when `review-override.py switch --name reviewer-filters` runs, then line 1 is `on`, a `reason: malformed_value of` line follows, and the exit code is 0 `[AC-1.3]`
- [ ] Given `--name` is unknown or omitted, when `review-override.py switch` runs, then stdout is empty, usage text goes to stderr, and the exit code is 2; and `review-override.py check` prints the same output and exit codes as before this story `[AC-1.4]`

## Implementation Tasks

- [ ] 1.1 Write pytest cases first in `scripts/tests/test_review_override.py` (extend the existing file) for every resolver row, both names, `OFF` and `on` values, and unknown or missing `--name` `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.2 Implement the `switch` subcommand in `scripts/review-override.py`: read `.writ/config.md` with the `^- \*\*Safety Fact:\*\*[ \t]*(.*)$` and `^- \*\*Reviewer Filters:\*\*[ \t]*(.*)$` patterns (multiline, first match wins), and print the check shape (line 1 state, `reason:` lines, summary last) `[AC-1.1, AC-1.2, AC-1.3]`
- [ ] 1.3 Make `switch` exit 2 with empty stdout and usage on stderr for an unknown or missing `--name`, and leave the `check` subcommand code path unchanged `[AC-1.4]`
- [ ] 1.4 Update the `review-override.py` module docstring to document the `switch` subcommand and both config lines (`- **Safety Fact:** off`, `- **Reviewer Filters:** off`); add a row and a short section for each switch to `.writ/docs/config-format.md` (line format, default on, malformed rule); confirm no generated tree changes are needed for a script-only edit `[AC-1.1, AC-1.2, AC-1.3]`
- [ ] 1.5 Run `uv run --python 3.9 pytest scripts/tests/test_review_override.py` and confirm all tests pass, including the existing `check` tests `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.6 Run `bash scripts/eval.sh --check=review-override`, then verify each acceptance criterion against the script output `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`

## Notes

- Switches default to on. Only the exact value `off` (any case) turns a switch off. Surrounding whitespace is ignored.
- First match wins, anywhere in `.writ/config.md`.
- A line with a bad value prints `on` with `reason: malformed_value <value>`. It does not fail the command. The trial operator sees the arm did not switch.
- The summary line is `review-override switch: <name> <state> (.writ/config.md)`.
- Python 3.9 floor. No `match`, no `X | Y` unions at runtime, no 3.10+ `pathlib` or `str` methods. Use `from __future__ import annotations`.
- The later spec `2026-10-25-gate-upgrade-removal-measurement` flips these config lines. This story does not own that.
- Stories 2, 3, and 4 call this resolver. Its output shape is a contract for them. Do not change it after this story lands.
- Risk: `check` shares the script. Keep the `switch` branch separate so existing `check` tests stay green.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [`switch` reads `.writ/config.md` (file absent or unreadable), `switch` parses value (typo such as `of`)] — from technical-spec.md § Error & Rescue Map
- **Shadow paths:** [Switch resolution] — from technical-spec.md § Shadow Paths
- **Business rules:** [Switch resolution (first match wins, `off` in any case only, default on, unknown `--name` is exit 2)] — from spec.md → Business Rules (Expanded) → Switch resolution
- **Experience:** [State catalog row for a config line with a bad value, and the `safety-fact` / `reviewer-filters` off rows] — from spec.md → Experience Design → State Catalog

Resolver contract: technical-spec.md → ## Switches → ### Resolver (table of inputs, line 1, `reason:`, and exit codes).
