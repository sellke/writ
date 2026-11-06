# Story 2: `pr-ready.py` snapshot and blocker classes

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** `/ship --watch` loop, or a developer looking at a PR
**I want to** run one read-only script over a saved `gh` snapshot and get every reason the PR is not ready, typed by class, with one exit code per class
**So that** the loop can act on the first blocker without parsing prose, and nothing a reviewer wrote reaches the agent through this script

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given one fixture per blocker (`conflicting`, `dirty`, `unresolved-thread`, `outdated-thread`, `failing-check-run`, `failing-status`, `draft`, `changes-requested`, `review-required`, `closed`, `behind`, `blocked-unexplained`), when `pr-ready.py check --snapshot <fixture> --repo <tmp>` runs, then line 1 is `fail`, a reason line reads `<class>: <detail>` with the expected class and, for `merge_gates`, a detail that starts with the expected gate token, the last line starts `pr-ready: fail (`, and the exit code is 3, 4, 5, or 6 for that class `[AC-2.1]`
- [ ] Given `all-four.json`, when `check` runs, then reason lines for `conflicts`, `unresolved_threads`, `failing_checks`, and `merge_gates` print in that order and the exit is 3; given each of `mergeable-unknown`, `checks-pending`, `threads-truncated`, `head-moved`, and `unstable-unexplained` alone, then line 1 is `unverifiable`, the reason reads `unknown: <code>`, and the exit is 0; given `pending-and-thread.json`, then line 1 is `fail`, the exit is 4, and the `unknown: checks_pending` line follows the thread line; given `blocked-review-required.json`, then `merge_gates: review_required` prints and `merge_state_blocked` does not `[AC-2.2]`
- [ ] Given a missing file, `not-json.txt`, `bad-schema.json`, `graphql-errors.json`, `missing-field.json`, `pr-mismatch.json`, or `unknown-conclusion.json`, when `check` runs, then the exit is 2, stdout is empty, and stderr starts `pr-ready: `; and when `pr-ready.py --help` runs, then it exits 0 and prints the `gh pr view`, `gh api graphql`, and `printf` lines of technical-spec § Commands byte for byte `[AC-2.3]`
- [ ] Given `hostile-thread.json`, whose thread path and author login hold a newline, an ESC, and U+2028, and whose comment node carries a `body` key holding the marker `IGNORE-PREVIOUS-MARKER`, when `check` runs, then every reason line is one line with those characters escaped, and neither stdout nor stderr contains the marker `[AC-2.4]`
- [ ] Given the story's changes, when `test_agent_cli_contract.py` and `test_agent_cli_contract_doc.py` run, then `pr-ready.py` has a `check` row with the shared Callers text, a Notes entry naming exit codes 3 to 6 and the gate tokens, the Check-shape section names the exception, ADR-029 carries the 2026-11-06 amendment with rules 1-7 byte-identical, the `draft.json` smoke exits 6 and passes `test_exit_code_smoke` through `FAIL_EXITS`, any other `fail` exit still needs 1, and `python3 scripts/gen-platform-trees.py --check` reports no stale or missing file `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write `scripts/tests/test_pr_ready.py`, with a module docstring that names `2026-11-06-pr-ready-and-ledger` Story 2 above every AC tag. Build the fixtures under `scripts/tests/fixtures/pr-ready/` listed in technical-spec § Test Plan. Each one is a complete `pr-ready-snapshot/1` object whose `view` matches the `gh pr view --json` field shapes and whose `threads` matches the S1 GraphQL shape. `clean.json` has head `3ddc8c8f0e1d2c3b4a5968778695a4b3c2d1e0f9`. Write one test per fixture, the `--help` byte-match test, and the hostile-text test. Run every case with `--repo` set to an empty `tmp_path`. Run them on Python 3.9 and confirm they fail `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [ ] 2.2 Create `scripts/pr-ready.py`. The module docstring holds the CLI, the snapshot schema, the `gh` commands verbatim, the classes, gate tokens, unknown codes, exit codes, and reason grammar from technical-spec § S1 and § S2. Use argparse with `RawDescriptionHelpFormatter` and `description=__doc__`. The `check` subcommand takes `--snapshot` (required) and `--repo` (default `.`). Copy `printable` and the stdout `reconfigure(errors="backslashreplace")` call from `scripts/repro-order.py`. `main()` returns the exit code `[AC-2.3]`
- [ ] 2.3 Add `load_snapshot(path) -> dict`, which raises `SnapshotError` for each exit-2 case in spec.md → § Snapshot validity and technical-spec § Fields read: file, JSON, schema, `view`/`threads` objects, `threads.errors`, required fields and types, 40-hex heads, enum tables, and PR-number equality. The CLI prints `pr-ready: snapshot <path>: <cause>` on stderr, leaves stdout empty, and exits 2 `[AC-2.3]`
- [ ] 2.4 Add the class judges in technical-spec § Evaluation order: `conflicts`, `unresolved_threads` (one line per unresolved node; `?` for a null path, line, or login; ` outdated` suffix; never read `body`), `failing_checks` (per the `CheckRun` and `StatusContext` table), and the unknowns `mergeable_unknown`, `checks_pending` (names joined by `, `), `threads_truncated <fetched> of <total>`, `head_moved`, and `merge_state_unexplained UNSTABLE`. Every snapshot string goes through `printable` `[AC-2.1, AC-2.2, AC-2.4]`
- [ ] 2.5 Add `merge_gates` (`draft`, `changes_requested`, `review_required`, `not_open <STATE>`, `behind`, then `merge_state_blocked` last, under the explanation rule in spec.md → § Merge gates) and `evaluate(snapshot, ledger=None) -> Result` with the verdict, the first-class exit code, and the three summary forms in technical-spec § Output. Keep `ledger` as a parameter that this story leaves `None`. Story 3 passes the loaded `ledger_check` `[AC-2.1, AC-2.2]`
- [ ] 2.6 Register. In `.writ/docs/agent-cli-contract.md`, add the `pr-ready.py` row between `phase-state.py` and `quality-config-audit.py`, its Notes entry without the two `--json`/ledger sentences, and the Check-shape bullet from technical-spec § Check shape sentence. Insert the ADR-029 amendment from technical-spec § ADR-029 amendment before `### Contribution`. In `scripts/tests/test_agent_cli_contract.py`, add the `draft.json` smoke and `FAIL_EXITS`, make `check_exit_code` honor it, and append the doc-coverage test under a docstring naming this spec. Run `python3 scripts/gen-platform-trees.py` `[AC-2.5]`
- [ ] 2.7 Verify. Run `test_pr_ready.py`, `test_verify_ledger.py`, and both contract tests on Python 3.9 and 3.14, each run alone. Then run `python3 scripts/gen-platform-trees.py --check` and `bash scripts/eval.sh --check=platform-trees`. Check each AC against the test that carries its tag `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

- **No ledger gate in this story.** `merge_gates` holds every gate except `not_verified`. With `ledger=None`, `clean.json` prints `pass`. Story 3 adds the gate and changes the clean-fixture tests to supply a ledger row in their `--repo`. Nothing calls `pr-ready.py` before the second spec, which depends on this whole spec.
- **Exit 1 is never deliberate.** An uncaught exception exits 1. Leave it that way, so a crash cannot pass for any class.
- **Enum strictness.** An unrecognized enum value is exit 2, not a guess (technical-spec § Fields read). `unknown-conclusion.json` pins this.
- **Hostile fixture.** The S1 query never requests `body`. The fixture adds one anyway, to prove the script ignores it even when a snapshot was built some other way.
- **`--help` test.** Compare against the three command lines copied into the test as constants, and assert each appears as a full line in `--help` stdout. A docstring containing `%(prog)` would be %-formatted by argparse; the block has `%s` only.
- **`FAIL_EXITS`.** Map only `pr-ready.py` to `(3, 4, 5, 6)`. The doc-coverage test fails if the Notes line drops a code or the Check-shape bullet goes missing.
- **ADR-029 bytes.** `RULES_SHA256` covers `### The agent CLI contract` through rule 7. The amendment goes after the 2026-10-12 block's last line. `test_amendment_records_each_change` reads that block up to `### Contribution`, so text added there must not remove its needles.
- **Shared files with Story 1.** This story edits the same contract doc, contract test, and plugin tree. Rebase on Story 1 before editing.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Read snapshot, Validate snapshot (both rows), Judge threads (both rows)] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [`pr-ready.py check` (Nil, Empty, Upstream error)] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Business Rules 1-7 (read-only, verdict, exit codes, all blockers print, every failing check blocks, review decisions are gates, no comment bodies)] — spec.md → ## Specification Contract → 📋 Business Rules; spec.md → ## Business Rules (Expanded) → ### Verdict and exit code, ### Blocker classes, ### Merge gates, ### Unknowns, ### Snapshot validity (exit 2), ### Untrusted content
- **Experience:** [Feedback model (one reason line per blocker or unknown), Error experience (checks pending → `unverifiable`; bad snapshot → exit 2), State Catalog `pr-ready.py` table, Interaction patterns (line 1 decides; identifiers only)] — spec.md → ## Specification Contract → 🎯 Experience Design; spec.md → ## Experience Design
