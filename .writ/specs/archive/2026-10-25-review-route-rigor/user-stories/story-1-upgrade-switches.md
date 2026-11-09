# Story 1: Upgrade switches

> **Status:** Completed ✅ (2026-10-29)
> **Commit:** 35d670fe77d22fe47ba4d23894d86f4148e6f7c9
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** maintainer running the Phase 15 removal trial, and the `/implement-story` orchestrator
**I want to** resolve the `safety-fact` and `reviewer-filters` switches from one config line each
**So that** a trial arm flips with one line, and every Gate 3 run reads the same switch state

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.4

- [x] Given `.writ/config.md` contains `- **Safety Fact:** off` (or `OFF`, or any other letter case), when `review-override.py switch --name safety-fact` runs, then line 1 of stdout is `off`, a `reason: config_off` line follows, and the exit code is 0 `[AC-1.1]`
- [x] Given no `.writ/config.md`, or the file exists with no line for the switch, or the line's value is `on` or empty, when `review-override.py switch --name <switch>` runs, then line 1 is `on` with `reason: no_config`, `reason: no_config_line`, or `reason: config_on` respectively, and the exit code is 0 `[AC-1.2]`
- [x] Given `.writ/config.md` contains `- **Reviewer Filters:** of`, when `review-override.py switch --name reviewer-filters` runs, then line 1 is `on`, a `reason: malformed_value of` line follows, and the exit code is 0 `[AC-1.3]`
- [x] Given `--name` is unknown or omitted, when `review-override.py switch` runs, then stdout is empty, usage text goes to stderr, and the exit code is 2; and `review-override.py check` prints the same output and exit codes as before this story `[AC-1.4]`

## Implementation Tasks

- [x] 1.1 Write pytest cases first in `scripts/tests/test_review_override.py` (extend the existing file) for every resolver row, both names, `OFF` and `on` values, and unknown or missing `--name` `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.2 Implement the `switch` subcommand in `scripts/review-override.py`: read `.writ/config.md` with the `^- \*\*Safety Fact:\*\*[ \t]*(.*)$` and `^- \*\*Reviewer Filters:\*\*[ \t]*(.*)$` patterns (multiline, first match wins), and print the check shape (line 1 state, `reason:` lines, summary last) `[AC-1.1, AC-1.2, AC-1.3]`
- [x] 1.3 Make `switch` exit 2 with empty stdout and usage on stderr for an unknown or missing `--name`, and leave the `check` subcommand code path unchanged `[AC-1.4]`
- [x] 1.4 Update the `review-override.py` module docstring to document the `switch` subcommand and both config lines (`- **Safety Fact:** off`, `- **Reviewer Filters:** off`); add a row and a short section for each switch to `.writ/docs/config-format.md` (line format, default on, malformed rule); confirm no generated tree changes are needed for a script-only edit `[AC-1.1, AC-1.2, AC-1.3]`
- [x] 1.5 Run `uv run --python 3.9 pytest scripts/tests/test_review_override.py` and confirm all tests pass, including the existing `check` tests `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.6 Run `bash scripts/eval.sh --check=review-override`, then verify each acceptance criterion against the script output `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [`switch` reads `.writ/config.md` (file absent or unreadable), `switch` parses value (typo such as `of`)] — from technical-spec.md § Error & Rescue Map
- **Shadow paths:** [Switch resolution] — from technical-spec.md § Shadow Paths
- **Business rules:** [Switch resolution (first match wins, `off` in any case only, default on, unknown `--name` is exit 2)] — from spec.md → Business Rules (Expanded) → Switch resolution
- **Experience:** [State catalog row for a config line with a bad value, and the `safety-fact` / `reviewer-filters` off rows] — from spec.md → Experience Design → State Catalog

Resolver contract: technical-spec.md → ## Switches → ### Resolver (table of inputs, line 1, `reason:`, and exit codes).

## What Was Built

**Implementation Date:** 2026-10-29

### Files Created

[None created]

### Files Modified

- **`scripts/review-override.py`** (`switch` subcommand)
  - `SWITCH_LINES` holds the two spec patterns; `_resolve_switch()` returns `(state, reason)` and never raises on a bad config; `switch()` prints through the existing `_emit()`; `main()` dispatches on the subcommand. `check` code path untouched. Module docstring documents `switch`, both config lines, every reason, and the exit codes.
- **`scripts/tests/test_review_override.py`** (new section at the end, naming Story 1 of `2026-10-25-review-route-rigor`)
  - `SwitchSubcommandTests` (15 tests): every resolver row for both names, `OFF`/`oFf`/padded `Off`, `on`/`ON`, empty value, malformed `of`, unreadable config (directory, non-UTF-8), first match wins, `--repo` default, unknown and missing `--name`.
  - `CheckUnchangedBySwitchTests` (4 tests): exact `check` stdout and exit codes.
- **`.writ/docs/config-format.md`** (Supported Keys; new `## Safety Fact` and `## Reviewer Filters`)
  - Line format, default on, only `off` (any case) turns a switch off, malformed value reads as on with its reason, the key must match the case shown, resolver command.
- **`.writ/docs/agent-cli-contract.md`** (Notes)
  - One bullet: `review-override.py switch` prints a state word on line 1, a documented exception to the Check shape (DEV-001).
- **`plugins/writ/scripts/review-override.py`** — regenerated by `python3 scripts/gen-platform-trees.py` (DEV-003).

### Implementation Decisions

1. **One `reason:` line per resolution** — every resolver row prints exactly one reason, so a trial operator reads the arm state and why in two lines.
2. **`on` in any case is `config_on`** — only the reason text differs from `malformed_value ON`; line 1 is `on` either way (DEV-002).
3. **Key match stays case-sensitive** — the spec's patterns are exact; the config-format sections now say the key must match the case shown.

### Test Results

**Verification:** `uv run --python 3.9 pytest scripts/tests/test_review_override.py scripts/tests/test_agent_cli_contract.py -q` → 307 passed; coding agent's full `uv run --python 3.9 pytest -q` → 3293 passed, 3 skipped; `bash scripts/eval.sh --check=review-override` → pass; `gen-platform-trees.py --check` → pass; `ac-trace.py check` → 0 findings.
- ✅ test-integrity authenticity: pass
- coverage: no new files in this story

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Medium
- **Security:** Clean
- **Boundary Compliance:** three owned files; `agent-cli-contract.md` (requested doc note) and the generated plugin copy justified
- **gate3-route:** review-agent (outside_boundary .writ/docs/agent-cli-contract.md; outside_boundary plugins/writ/scripts/review-override.py)
- **review-panel:** skipped — platform cannot spawn other vendors
- **review-override check:** pass (no blocking helper finding)
- **jev shadow:** pass (judged) criteria=4 agree=4

### Deviations from Spec

- **[DEV-001] `switch` prints a state word on line 1, an exception to the agent CLI check shape** — Severity: Medium
  - Spec said: line 1 `on`/`off`, called "check shape"
  - Reality: built as specified; agent-cli-contract.md records the exception
  - Resolution: Flagged for review
- **[DEV-002] `on` is matched in any case** — Severity: Small
  - Resolution: Auto-amended (Small)
- **[DEV-003] A script edit regenerates the plugin tree** — Severity: Small
  - Resolution: Auto-amended (Small)
