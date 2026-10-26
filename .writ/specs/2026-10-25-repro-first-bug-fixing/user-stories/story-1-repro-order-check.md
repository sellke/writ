# Story 1: Repro-Order Check Script

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** developer fixing a bug through Writ, and the Writ maintainer who needs the repro-before-fix order checked
**I want to** run `scripts/repro-order.py check` on a branch and get a verdict re-derived from git
**So that** a bug fix's repro commit is proven to precede its fix, and a broken order fails with a named reason.

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given a git repository whose history is one repro commit that changes only test files and carries a `Repro:` trailer, followed by one fix commit that changes source files, when `repro-order.py check --base <commit before the repro>` runs, then the first output line is `pass`, one `reason:` line each names the repro and the fix commit, the summary line reads `repro-order: pass (1 repro, 1 fix commit(s))`, and the exit code is 0 `[AC-1.1]`
- [ ] Given six broken histories (no repro commit; a repro commit that also changes a source file; a repro commit with no test file; a source change before the repro; a repro with no later source change; a later commit that modifies a file the repro added), when the check runs on each, then the first output line is `fail`, a `reason:` line names the matching code (`no_repro_commit`, `repro_touches_source`, `repro_empty`, `source_before_repro`, `no_fix_after_repro`, `repro_test_modified`), and the exit code is 1 `[AC-1.2]`
- [ ] Given `.writ/config.md` contains the line `- **Repro First:** off`, when the check runs in any directory, then the output is `unverifiable` with `reason: repro-first off`, the exit code is 0, and no git command runs; and given a history whose range contains a merge commit, when the check runs, then the output is `unverifiable` with `reason: merge_in_range` and the exit code is 0 `[AC-1.3]`
- [ ] Given a missing `--base`, an unknown revision, a base that is not an ancestor of head, or a directory that is not a git repository, when the check runs, then the exit code is 2, stdout is empty, and the cause appears on stderr `[AC-1.4]`
- [ ] Given the Classification table in `.writ/docs/agent-cli-contract.md`, when the contract test reads it, then the table has a `repro-order.py` row, and the smoke entry in `scripts/tests/test_agent_cli_contract.py` runs the script and passes under `uv run pytest scripts/tests/test_agent_cli_contract.py` `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write `scripts/tests/test_repro_order.py`. Add `make_repo(tmp)` (git init, local `user.name` and `user.email`, a base commit with `src/app.py` and `tests/test_app.py`) and `commit(repo, files, message)`. Cover every row of the technical-spec test table for this file, including the `--test-glob` and unknown-switch-value cases. Run it and confirm every test fails because `scripts/repro-order.py` does not exist `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.2 Create `scripts/repro-order.py` with the `check` subcommand, `--repo` (default `.`), `--base` (required), `--head` (default `HEAD`), and repeatable `--test-glob`. Read `<repo>/.writ/config.md` with the single-line pattern from `scripts/review-panel.py` `config_value`. An absent file reads as `on`. `off` (case-insensitive) prints `unverifiable` and `reason: repro-first off`, exits 0, and makes no git call. Any other value reads as `on` and adds a reason line naming the value `[AC-1.3]`
- [ ] 1.3 Add one `_git()` helper with `check=False` and explicit error mapping, as `scripts/revert-resolve.py` does. Resolve `--base` and `--head` with `git rev-parse --verify <rev>^{commit}`, test ancestry with `git merge-base --is-ancestor`, and map each failure to exit 2 with the cause on stderr. Run `git rev-list --merges <base>..<head>`; a non-empty result prints `unverifiable` with `reason: merge_in_range` and exits 0 `[AC-1.3, AC-1.4]`
- [ ] 1.4 List commits oldest first with `git rev-list --reverse <base>..<head>`. Read each message with `git show -s --format=%B` and find a `Repro:` trailer with a non-empty value in the final paragraph. Read changed paths with `git diff-tree -r -M --name-status -z` and parse the NUL-separated output. Classify paths: `.writ/` is ignored, the test-file rule and `--test-glob` mark a test, and every other path is source. Both sides of a rename count `[AC-1.1, AC-1.2]`
- [ ] 1.5 Apply the six rules in technical-spec.md → ## Check Script: scripts/repro-order.py → ### Check Rules. Run every rule and print every finding; do not stop at the first. Print `pass` with one `reason:` line per repro and fix commit, or `fail` with one `reason:` line per finding. Print the summary line last. Exit 0 for `pass`, 1 for `fail` `[AC-1.1, AC-1.2]`
- [ ] 1.6 Add the `repro-order.py` row to the Classification table in `.writ/docs/agent-cli-contract.md`, and add the smoke entry to `scripts/tests/test_agent_cli_contract.py`. Run `uv run pytest scripts/tests/test_agent_cli_contract.py` and confirm it passes `[AC-1.5]`
- [ ] 1.7 Verify the criteria. Run `uv run --python 3.9 pytest scripts/tests/test_repro_order.py`, then `uv run --python 3.9 pytest`, then `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, then `bash scripts/eval.sh` outside any sandbox. Match each criterion to a passing test `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Notes

- **Python floor.** Python 3.9, stdlib only, no network imports. Avoid `match` statements and `X | Y` annotations unless `from __future__ import annotations` is present.
- **Exit 2 keeps stdout empty.** Every cause goes to stderr. The usage-error test must assert that stdout is exactly empty.
- **Shadow path, base equals head.** This is a `fail` with `no_repro_commit`, not an exit 2. Keep it distinct from the usage errors.
- **Path heuristic.** The test-file rule is path-only. The check proves order and file classes from git. It does not prove the repro failed at the repro commit. The failing output in the agent's report is the evidence for that. Re-running the test at the repro commit is deferred (spec.md → ## Specification Contract → Technical Concerns).
- **Shallow history.** An unresolvable revision in a shallow clone maps to exit 2 with `cannot resolve`. It is not a verdict.
- **Integration with Stories 2 to 4.** Story 2 names the script path in the skill. Story 4's consumers run `python3 scripts/repro-order.py check --repo . --base <SHA>` and parse line 1 and the `reason:` lines. Keep the flag names and the output shape fixed once this story lands.
- **Shipping.** `scripts/install.sh` ships every `scripts/*.py` not on its dev-only list. The contract row is required, or `scripts/tests/test_agent_cli_contract.py` fails.
- **Bare AC tokens in tests.** A bare `AC-1.N` token in a test module counts as a citation. Name `2026-10-25-repro-first-bug-fixing` in the docstring above any bare token, so the token attaches to this spec (acceptance-criteria-ids.md → ## Scan Bounds).

## Context for Agents

- **Error map rows:** `technical-spec.md → ## Error & Rescue Map` (Read `.writ/config.md`; Resolve `--base` / `--head`; Ancestry; Run git; Range shape)
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path; Nil input; Empty input; Upstream error)
- **Interaction edge cases:** `technical-spec.md → ## Interaction Edge Cases` (Repro un-skips an existing test; Fix commit also adds new tests; Repro test renamed after the fix; Paths with spaces or non-ASCII; Switch value `yes`)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 4 repro commit shape; Rule 5 fix commit constraints; Rule 9 the switch and what `off` changes)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Switch off; Merge commit in the range)
- **Check shape:** `technical-spec.md → ## Check Script: scripts/repro-order.py → ### CLI` and `### Check Rules` (the `pass` and `fail` output blocks show the exact line forms)
- **Test table:** `technical-spec.md → ## Tests → ### scripts/tests/test_repro_order.py (Story 1)`
- **Reference code:** `scripts/review-panel.py` (`config_value`), `scripts/revert-resolve.py` (`_git()`), `scripts/lint-skill.sh` (header and check-shape output), `.writ/docs/agent-cli-contract.md`, `scripts/tests/test_prompting_guide.py` (test style)
