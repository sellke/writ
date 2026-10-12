# Story 3: Agent CLI Contract Test

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1, Story 2

## User Story

**As a** Writ maintainer adding or changing scripts
**I want to** run one pytest file that checks every shipped script against the agent CLI contract and names the script, the broken rule, and the fix when it fails
**So that** contract breaks fail before review, the agent-facing output shapes stay stable, and remaining debt is listed in one place

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given a shipped script with no row in the `## Classification` table of `.writ/docs/agent-cli-contract.md`, when `test_table_complete` runs, then it fails with a message that starts with the script name and ends with "add a row"; a table row with no shipped script fails the same way, naming the row `[AC-3.1]`
- [ ] Given one fixture script per rule in a temp directory (a network import without `network: opt-in`, an agent CLI launch literal, a `time.sleep` without `bounded-wait`, a `--zz-contract-probe` that prints prose to stdout, a `--help` that exits non-zero, and a shell script whose bad flag prints prose to stdout), when the rule checks run against each fixture, then each fails with a message naming the script, the rule number, and the fix; a conforming Python fixture and a conforming shell fixture pass; and shell scripts get only the table, help, and bad-flag checks `[AC-3.2]`
- [ ] Given a `(script, rule)` entry in `KNOWN_VIOLATIONS`, when the script still violates that rule, then the case reports xfail with the recorded reason; when the script no longer violates it and the entry remains, then the case fails as a strict XPASS with a message to remove the entry `[AC-3.3]`
- [ ] Given the current repo after the first red run, when `uv run --python 3.9 pytest scripts/tests/test_agent_cli_contract.py` and `uv run pytest` run, then both exit 0, and every `KNOWN_VIOLATIONS` entry has a non-empty reason `[AC-3.4]`
- [ ] Given a read-only invocation listed in `SMOKE_INVOCATIONS`, when the test runs it from a temp cwd, then a data script's stdout parses as one JSON value, a check script's first stdout line is `pass`, `fail`, or `unverifiable`, and `git status` of the repo is unchanged `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write tests in `scripts/tests/test_agent_cli_contract.py` first: table completeness in both directions, and one fixture script per rule in a `tmp_path` directory (network import, agent launch literal, unbounded wait, bad-flag stdout, `--help` exit code), plus a conforming fixture for each `[AC-3.1, AC-3.2]`
- [ ] 3.2 Implement the shipped-set loader: extract only the `is_shippable_script` function text from `scripts/install.sh` (line 922 at audit time), run it over each `scripts/*` name, and fail with `cannot load is_shippable_script from scripts/install.sh` if extraction fails. Implement the classification parser for the first table under `## Classification` in `.writ/docs/agent-cli-contract.md`, with the setup error `no classification table in .writ/docs/agent-cli-contract.md` `[AC-3.1]`
- [ ] 3.3 Implement the per-script checks: `--help` exit 0 (Python) or usage output (shell), the `--zz-contract-probe` bad-flag check (non-zero exit; stdout empty or one JSON object with `blocker`), and the `ast` scans for network imports, agent-CLI launch targets, and `time.sleep` or `while True` outside `bounded-wait`. Each failure message names script, rule, and fix. Scan import statements and call nodes only, so string literals such as `"socket hang up"` in `build-smoke.py` do not trigger `[AC-3.2]`
- [ ] 3.4 Implement `SMOKE_INVOCATIONS` as a list of read-only commands against this repo, run from a temp cwd with `sys.executable`, and assert the declared shape per script. Add a `git status` before-and-after comparison on the repo `[AC-3.5]`
- [ ] 3.5 Run the test against the real repo, record every red case in `KNOWN_VIOLATIONS` as `(script, rule): reason`, mark each with `pytest.param(..., marks=pytest.mark.xfail(strict=True, reason=...))`, and add a fixture case where a listed script is fixed so the strict XPASS failure is shown `[AC-3.3, AC-3.4]`
- [ ] 3.6 Verify on the 3.9 floor: `uv run --python 3.9 pytest scripts/tests/test_agent_cli_contract.py` and `uv run pytest` both exit 0 `[AC-3.4]`
- [ ] 3.7 Verify the full suite: `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, `uv run pytest`, `bash scripts/eval.sh` run outside the sandbox, and confirm `git status` shows no changes under the real `scripts/` or `.writ/` after the smoke run `[AC-3.4, AC-3.5]`

## Notes

- **Shape of `KNOWN_VIOLATIONS`.** The technical spec keys entries as `(script, rule) -> reason`. spec.md Business Rule 10 writes `(script, rule, reason)`. Both carry the same data. Use the technical-spec form.
- **Sourcing `install.sh`.** Do not source the whole file. Extract the function text. Sourcing the full script runs its install logic.
- **Heuristic scans.** The import and call scans are heuristics. They catch regressions and do not prove conformance. Per-script tests still own success-output shape. Keep the scans on AST nodes, not text, so string literals do not match.
- **`recommend-state.py` on bad flags.** A JSON blocker on stdout is conforming (spec.md Business Rule 5). The bad-flag check must accept it and must not require empty stdout.
- **`test-integrity.py` `while True`.** Technical spec line 320 is unresolved between a bounded parse loop and a wait. The `while True` rule applies to it. Its status is decided in the first red run. Either add it to `KNOWN_VIOLATIONS` with a reason or mark the row `bounded-wait` if it has a timeout.
- **`app-verify.py` and `jev-judge.py`.** Both are allowed `network: opt-in` and `bounded-wait` per the technical spec. A missing allowance in the table is a failure, not a skip.
- **Smoke invocations.** Read-only only. Scripts that take `--repo` get the repo path. Scripts that write state run in the temp cwd or not at all. Remove any invocation that writes state from `SMOKE_INVOCATIONS`.
- **Python 3.9 floor.** No `match` statements, no `X | Y` annotations evaluated at runtime, no 3.10+ stdlib calls. `from __future__ import annotations` is allowed.
- **Message format.** Every failure message starts with the script name and ends with the fix, per spec.md Interaction Patterns.
- **Story 4 dependency.** Story 4 removes `KNOWN_VIOLATIONS` entries. This story must stay green while entries exist. Do not delete xfail entries here.
- **eval.sh.** It creates a temp git repo, so it runs outside the sandbox.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `uv run --python 3.9 pytest` and `uv run pytest` pass
- [ ] Bash test loop and `bash scripts/eval.sh` pass
- [ ] `KNOWN_VIOLATIONS` entries each carry a reason
- [ ] Code reviewed
- [ ] Documentation updated (classification table references in `.writ/docs/agent-cli-contract.md` match the test's parser)

## Context for Agents

- **Error map rows:** [Read ship filter from install.sh, Parse classification table, Run a script's --help, Shape smoke] — from technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** []
- **Business rules:** spec.md → ## Business Rules (Expanded) (1 Scope follows the ship filter, 2 Classification table format, 3 Data shape, 4 Check shape, 5 Usage errors, 6 No agent spawning, 7 Bounded waits only, 8 Network opt-in, 10 KNOWN_VIOLATIONS is strict debt)
- **Experience:** [State Catalog → Conforming script (success and runtime failure), Bad arguments, New script with no table row, Script imports a network module without network: opt-in, Script names an agent CLI, Known violation not yet fixed, Known violation fixed but still listed; Interaction Patterns → failure messages] — from spec.md → ## Experience Design
- **Technical:** sub-specs/technical-spec.md → ## Current State (audit, 2026-10-12) (shape groups, allowances); ## Contract Test (Story 3) (test table, xfail mechanics); ## Error & Rescue Map
- **Dependencies:** sub-specs/technical-spec.md → ## Ship Filter (Story 2) for the function being extracted; ## Contract Doc (Story 1) for the table format
