# Story 2: `pr-ready.py` snapshot and blocker classes

> **Status:** Completed ✅ (2026-11-06)
> **Commit:** 5fbaa73f6fe6fbc0327ac6a625a3c54e62a668f3
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** `/ship --watch` loop, or a developer looking at a PR
**I want to** run one read-only script over a saved `gh` snapshot and get every reason the PR is not ready, typed by class, with one exit code per class
**So that** the loop can act on the first blocker without parsing prose, and nothing a reviewer wrote reaches the agent through this script

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given one fixture per blocker (`conflicting`, `dirty`, `unresolved-thread`, `outdated-thread`, `failing-check-run`, `failing-status`, `draft`, `changes-requested`, `review-required`, `closed`, `behind`, `blocked-unexplained`), when `pr-ready.py check --snapshot <fixture> --repo <tmp>` runs, then line 1 is `fail`, a reason line reads `<class>: <detail>` with the expected class and, for `merge_gates`, a detail that starts with the expected gate token, the last line starts `pr-ready: fail (`, and the exit code is 3, 4, 5, or 6 for that class `[AC-2.1]`
- [x] Given `all-four.json`, when `check` runs, then reason lines for `conflicts`, `unresolved_threads`, `failing_checks`, and `merge_gates` print in that order and the exit is 3; given each of `mergeable-unknown`, `checks-pending`, `threads-truncated`, `head-moved`, and `unstable-unexplained` alone, then line 1 is `unverifiable`, the reason reads `unknown: <code>`, and the exit is 0; given `pending-and-thread.json`, then line 1 is `fail`, the exit is 4, and the `unknown: checks_pending` line follows the thread line; given `blocked-review-required.json`, then `merge_gates: review_required` prints and `merge_state_blocked` does not `[AC-2.2]`
- [x] Given a missing file, `not-json.txt`, `bad-schema.json`, `graphql-errors.json`, `missing-field.json`, `pr-mismatch.json`, or `unknown-conclusion.json`, when `check` runs, then the exit is 2, stdout is empty, and stderr starts `pr-ready: `; and when `pr-ready.py --help` runs, then it exits 0 and prints the `gh pr view`, `gh api graphql`, and `printf` lines of technical-spec § Commands byte for byte `[AC-2.3]`
- [x] Given `hostile-thread.json`, whose thread path and author login hold a newline, an ESC, and U+2028, and whose comment node carries a `body` key holding the marker `IGNORE-PREVIOUS-MARKER`, when `check` runs, then every reason line is one line with those characters escaped, and neither stdout nor stderr contains the marker `[AC-2.4]`
- [x] Given the story's changes, when `test_agent_cli_contract.py` and `test_agent_cli_contract_doc.py` run, then `pr-ready.py` has a `check` row with the shared Callers text, a Notes entry naming exit codes 3 to 6 and the gate tokens, the Check-shape section names the exception, ADR-029 carries the 2026-11-06 amendment with rules 1-7 byte-identical, the `draft.json` smoke exits 6 and passes `test_exit_code_smoke` through `FAIL_EXITS`, any other `fail` exit still needs 1, and `python3 scripts/gen-platform-trees.py --check` reports no stale or missing file `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Write `scripts/tests/test_pr_ready.py`, with a module docstring that names `2026-11-06-pr-ready-and-ledger` Story 2 above every AC tag. Build the fixtures under `scripts/tests/fixtures/pr-ready/` listed in technical-spec § Test Plan. Each one is a complete `pr-ready-snapshot/1` object whose `view` matches the `gh pr view --json` field shapes and whose `threads` matches the S1 GraphQL shape. `clean.json` has head `3ddc8c8f0e1d2c3b4a5968778695a4b3c2d1e0f9`. Write one test per fixture, the `--help` byte-match test, and the hostile-text test. Run every case with `--repo` set to an empty `tmp_path`. Run them on Python 3.9 and confirm they fail `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [x] 2.2 Create `scripts/pr-ready.py`. The module docstring holds the CLI, the snapshot schema, the `gh` commands verbatim, the classes, gate tokens, unknown codes, exit codes, and reason grammar from technical-spec § S1 and § S2. Use argparse with `RawDescriptionHelpFormatter` and `description=__doc__`. The `check` subcommand takes `--snapshot` (required) and `--repo` (default `.`). Copy `printable` and the stdout `reconfigure(errors="backslashreplace")` call from `scripts/repro-order.py`. `main()` returns the exit code `[AC-2.3]`
- [x] 2.3 Add `load_snapshot(path) -> dict`, which raises `SnapshotError` for each exit-2 case in spec.md → § Snapshot validity and technical-spec § Fields read: file, JSON, schema, `view`/`threads` objects, `threads.errors`, required fields and types, 40-hex heads, enum tables, and PR-number equality. The CLI prints `pr-ready: snapshot <path>: <cause>` on stderr, leaves stdout empty, and exits 2 `[AC-2.3]`
- [x] 2.4 Add the class judges in technical-spec § Evaluation order: `conflicts`, `unresolved_threads` (one line per unresolved node; `?` for a null path, line, or login; ` outdated` suffix; never read `body`), `failing_checks` (per the `CheckRun` and `StatusContext` table), and the unknowns `mergeable_unknown`, `checks_pending` (names joined by `, `), `threads_truncated <fetched> of <total>`, `head_moved`, and `merge_state_unexplained UNSTABLE`. Every snapshot string goes through `printable` `[AC-2.1, AC-2.2, AC-2.4]`
- [x] 2.5 Add `merge_gates` (`draft`, `changes_requested`, `review_required`, `not_open <STATE>`, `behind`, then `merge_state_blocked` last, under the explanation rule in spec.md → § Merge gates) and `evaluate(snapshot, ledger=None) -> Result` with the verdict, the first-class exit code, and the three summary forms in technical-spec § Output. Keep `ledger` as a parameter that this story leaves `None`. Story 3 passes the loaded `ledger_check` `[AC-2.1, AC-2.2]`
- [x] 2.6 Register. In `.writ/docs/agent-cli-contract.md`, add the `pr-ready.py` row between `phase-state.py` and `quality-config-audit.py`, its Notes entry without the two `--json`/ledger sentences, and the Check-shape bullet from technical-spec § Check shape sentence. Insert the ADR-029 amendment from technical-spec § ADR-029 amendment before `### Contribution`. In `scripts/tests/test_agent_cli_contract.py`, add the `draft.json` smoke and `FAIL_EXITS`, make `check_exit_code` honor it, and append the doc-coverage test under a docstring naming this spec. Run `python3 scripts/gen-platform-trees.py` `[AC-2.5]`
- [x] 2.7 Verify. Run `test_pr_ready.py`, `test_verify_ledger.py`, and both contract tests on Python 3.9 and 3.14, each run alone. Then run `python3 scripts/gen-platform-trees.py --check` and `bash scripts/eval.sh --check=platform-trees`. Check each AC against the test that carries its tag `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Read snapshot, Validate snapshot (both rows), Judge threads (both rows)] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [`pr-ready.py check` (Nil, Empty, Upstream error)] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Business Rules 1-7 (read-only, verdict, exit codes, all blockers print, every failing check blocks, review decisions are gates, no comment bodies)] — spec.md → ## Specification Contract → 📋 Business Rules; spec.md → ## Business Rules (Expanded) → ### Verdict and exit code, ### Blocker classes, ### Merge gates, ### Unknowns, ### Snapshot validity (exit 2), ### Untrusted content
- **Experience:** [Feedback model (one reason line per blocker or unknown), Error experience (checks pending → `unverifiable`; bad snapshot → exit 2), State Catalog `pr-ready.py` table, Interaction patterns (line 1 decides; identifiers only)] — spec.md → ## Specification Contract → 🎯 Experience Design; spec.md → ## Experience Design

## What Was Built

**Implementation Date:** 2026-11-06

### Files Created

1. **`scripts/pr-ready.py`** (462 lines)
   - `check --snapshot <file> [--repo .]` in the check shape. `load_snapshot` / `validate` raise `SnapshotError` for every exit-2 case; `evaluate(snapshot, ledger=None) -> Result` judges `conflicts`, `unresolved_threads`, `failing_checks`, and `merge_gates` (every gate but `not_verified`) plus the five unknowns; `render` prints the verdict, reasons, and summary. `--help` prints the S1 `gh` commands from the module docstring.
2. **`scripts/tests/test_pr_ready.py`** (483 lines)
   - `BlockerTests`, `OrderAndUnknownTests`, `SnapshotValidityTests`, `UntrustedTextTests`, `ContractTests` (26 tests with the repro, 54 subtests on 3.14).
3. **`scripts/tests/test_pr_ready_head_repro.py`** (21 lines)
   - The Gate 3 reviewer's confirmed repro (a `headRefOid` with a trailing newline exits 2), kept byte for byte.
4. **`scripts/tests/fixtures/pr-ready/`** (28 files)
   - `clean.json`, one fixture per blocker and unknown, `all-four.json`, `pending-and-thread.json`, `blocked-review-required.json`, `hostile-thread.json`, and the exit-2 fixtures.
5. **`plugins/writ/scripts/pr-ready.py`** (462 lines)
   - Byte copy generated by `python3 scripts/gen-platform-trees.py`.

### Files Modified

- **`.writ/docs/agent-cli-contract.md`** (Check shape; Classification table; Notes)
  - The exit-code exception bullet, the `pr-ready.py` row between `phase-state.py` and `quality-config-audit.py`, and its Notes entry naming exit codes 3 to 6 and the gate tokens.
- **`.writ/decision-records/adr-029-agent-cli-contract.md`** (Amendments)
  - The 2026-11-06 amendment before `### Contribution`; rules 1-7 unchanged.
- **`scripts/tests/test_agent_cli_contract.py`** (smokes; `check_exit_code`; appended tests)
  - The `draft.json` smoke, `FAIL_EXITS = {"pr-ready.py": (3, 4, 5, 6)}`, `test_fail_exits_are_documented`, `test_fail_exits_apply_only_to_listed_scripts`, and the widened AC-ID guard (DEV-007).
- **`scripts/verify-ledger.py`** and its plugin copy; **`scripts/tests/test_verify_ledger.py`**
  - The review's cross-script fixes applied to Story 1's script too: `\Z` in `FULL_ID`, no raw U+2028/U+2029 in the source, `RecursionError` as not JSON, and stream guarding before argparse so `--help` cannot crash on a non-UTF-8 console.
- **`.writ/specs/2026-11-06-pr-ready-and-ledger/drift-log.md`**, **`spec-lite.md`**
  - DEV-005 to DEV-008 and their spec-lite amendments.

### Implementation Decisions

1. **No coding subagent** — the lane ran the coding role itself; Gate 3 ran as a spawned read-only `review-agent` (Gate 2.5 routed it). The first lane run stopped before closing the story; the retry run applied the review's Minor fix and ran the remaining gate scripts.
2. **Strict enums, bounded echo** — an unrecognized enum value is exit 2, and the rejected value prints cut to 80 characters, as a JSON scalar, or as `<type>` (DEV-008).
3. **`ledger` stays a parameter** — `evaluate` takes `ledger=None`; Story 3 passes the loaded `ledger_check`.

### Test Results

**Verification:** `uv run --isolated --python 3.9 --with pytest pytest -q scripts/tests/test_pr_ready.py scripts/tests/test_pr_ready_head_repro.py scripts/tests/test_verify_ledger.py scripts/tests/test_agent_cli_contract.py scripts/tests/test_agent_cli_contract_doc.py` and the same on 3.14: 381 passed each. `gen-platform-trees.py --check`: pass. Gate scripts: arch-lint 0 rulesets; build-smoke unsupported_stack (informational); change-surface cross-component, route review-agent; review-override check unverifiable (no_coverage_report); safety-fact pass (measured tested); evidence pass (prior_ok); drift-format pass; test-integrity authenticity pass; app-verify unverifiable (no_recipe); docs-check unverifiable (no public exports).
**Coverage:** 98%
- ✅ `test-integrity.py coverage --new-files scripts/pr-ready.py`: pass, re-derived from a subprocess-measured cobertura report (269 statements, 5 missed)
- ✅ Each blocker, unknown, and exit-2 fixture asserts line 1, every reason line, the summary, and the exit code
- ✅ The hostile fixture's comment-body marker never reaches stdout or stderr

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s)
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** All code changes are within Owned; the `verify-ledger.py` fixes are the review's cross-script findings, and the generated plugin copies and spec-healing files are justified.

### Deviations from Spec

- **[DEV-005] A running CheckRun may carry conclusion `""` or null** — Severity: Small
  - Spec said: any `conclusion` outside the table is exit 2.
  - Reality: `""` or null is accepted while `status` is not `COMPLETED`.
  - Resolution: Auto-amended spec-lite.md
- **[DEV-006] A missing key in the comments chain reads as null** — Severity: Small
  - Spec said: a missing required field is exit 2.
  - Reality: a missing `comments`, `nodes`, `author`, or `login` key prints `?`.
  - Resolution: Auto-amended spec-lite.md
- **[DEV-007] The contract test's AC-ID guard accepts a later spec's IDs, and two tests are appended** — Severity: Small
  - Spec said: append one doc-coverage test.
  - Reality: two appended tests and a widened AC-ID guard.
  - Resolution: Auto-amended spec-lite.md
- **[DEV-008] A rejected snapshot value prints in a bounded form** — Severity: Small
  - Spec said: nothing on how a rejected value prints.
  - Reality: cut to 80 characters, a JSON scalar, or `<type>`.
  - Resolution: Auto-amended spec-lite.md
