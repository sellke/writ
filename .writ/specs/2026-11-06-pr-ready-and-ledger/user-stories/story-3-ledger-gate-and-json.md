# Story 3: Ledger gate and machine output

> **Status:** Completed ✅ (2026-11-06)
> **Priority:** High
> **Dependencies:** Story 1, Story 2

## User Story

**As a** `/ship --watch` loop and the `merge` site of `jev-judge.py doubt` (second spec)
**I want to** have `pr-ready.py` pass only when the verification ledger reads VERIFIED for the snapshot's exact head, and to read its result as one JSON object
**So that** an autonomous merge is gated by the code that was tested, enforced in a script and not in prose, and the merge rule can parse the result without scraping text

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given a temp git repo whose head H has a `verify-ledger.py record` row for PR 66, and a clean snapshot for PR 66 whose `headRefOid` is H, when `pr-ready.py check --snapshot <file> --repo <repo>` runs, then line 1 is `pass`, the summary reads `pr-ready: pass (PR 66 head <short H>, ledger VERIFIED)`, and the exit is 0; and when only `headRefOid` changes to a commit with a one-byte change and no row, then line 1 is `fail`, a reason reads `merge_gates: not_verified head <short>: patch_id_mismatch ...`, and the exit is 6 `[AC-3.1]`
- [x] Given H's commit rebased unchanged onto a moved `main` and a snapshot naming the rebased head, when `check` runs, then line 1 is `pass` through the ledger's `verified_patch_id`; and given a whitespace-only re-indent of H, then `merge_gates: not_verified` prints and the exit is 6 `[AC-3.2]`
- [x] Given a ledger file holding `{"schema": "x"}` and a snapshot with an unresolved thread, when `check` runs, then the reason lines include `unresolved_threads: ...` and `merge_gates: not_verified ledger_unreadable (...)`, line 1 is `fail`, and the exit is 4, not 2 `[AC-3.3]`
- [x] Given every fixture in `scripts/tests/fixtures/pr-ready/` and the AC-3.1 repo, when `check --json` runs, then stdout is one JSON object with exactly the keys `verdict`, `exit`, `pr`, `head`, `blockers`, `unknowns`, and `ledger`, `head` is the full 40-hex `headRefOid`, each `blockers[]` item is `{class, detail}` with a `merge_gates` detail starting with its gate token, each `unknowns[]` item is `{code, detail}`, `exit` and the process exit code equal the text run's, and the exit-2 cases still print nothing on stdout `[AC-3.4]`
- [x] Given `pr-ready.py` and `verify-ledger.py` copied together into a temp directory, when the copy runs the AC-3.1 case, then it gives the same line 1 and exit; given `pr-ready.py` copied alone, then the exit is 2, stdout is empty, and stderr reads `pr-ready: cannot load verify-ledger.py (...)`; and when the contract tests and `python3 scripts/gen-platform-trees.py --check` run, then they pass with the `pr-ready.py` Notes entry naming `--json` and the ledger requirement `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Extend `scripts/tests/test_pr_ready.py` with a section whose docstring names `2026-11-06-pr-ready-and-ledger` Story 3. Add `LedgerGateTests`: the test builds a temp repo, records with `scripts/verify-ledger.py`, and writes the snapshot from `clean.json` with `headRefOid` and the threads `headRefOid` set to the head under test. Add `JsonTests`, looping over every fixture, and `SiblingLoadTests`. Update Story 2's clean-fixture tests to write a `verify-ledger.json` row for `clean.json`'s head into their `--repo`. Run on Python 3.9 and confirm the new tests fail `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
- [x] 3.2 Add `_load_sibling("verify-ledger.py", "verify_ledger_for_pr_ready")` in the `scripts/exit-criteria.py` pattern, deferred to first use, from `Path(__file__).resolve().parent`. A missing file or any load error exits 2 with `pr-ready: cannot load verify-ledger.py (<cause>)` on stderr and stdout empty `[AC-3.5]`
- [x] 3.3 Wire the ledger gate into `evaluate` (technical-spec § S3). Call `ledger_check(Path(args.repo), pr=view.number, head=view.headRefOid)`. On `fail`, add `not_verified head <short>: <first reason>` to `merge_gates`. On `LedgerError`, add `not_verified ledger_unreadable (<detail>)`. Keep `not_verified` out of the `merge_state_blocked` explanation. Change the `pass` summary to end `ledger VERIFIED` `[AC-3.1, AC-3.2, AC-3.3]`
- [x] 3.4 Add `--json` to `check` (technical-spec § `--json`). Build the object from `Result`, with `head` as the full `headRefOid` and `ledger` as `{verdict, reasons}`. Print it with `json.dumps(..., sort_keys=True)` as the only stdout, keep the exit code, and leave exit-2 paths unchanged `[AC-3.4]`
- [x] 3.5 Update the module docstring (`--json`, the ledger gate, sibling loading) and the `pr-ready.py` Notes entry in `.writ/docs/agent-cli-contract.md` with the two sentences in technical-spec § Notes entries. Run `python3 scripts/gen-platform-trees.py` `[AC-3.4, AC-3.5]`
- [x] 3.6 Verify. Run the full pytest suite on Python 3.9 and then on 3.14, each run alone (`uv run --isolated --python 3.9 --with pytest pytest`, then 3.14). Then run `python3 scripts/gen-platform-trees.py --check` and `bash scripts/eval.sh --check=platform-trees`. Check each AC against the test that carries its tag `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

- **The contract smoke is stable.** `draft.json` with `--repo {tmp}` and no ledger prints `merge_gates: draft` and `merge_gates: not_verified head ...: no_rows PR ...`, and exits 6 in Story 2 and here.
- **Story 2's clean tests change here.** With the gate in place, `clean.json` in an empty `--repo` reads NOT VERIFIED. Task 3.1 gives those tests a ledger row in the same commit as the gate, so the suite stays green. An exact-head row needs no git, so a plain temp dir with only `.writ/state/verify-ledger.json` is enough.
- **The second spec reads this JSON.** `jev-judge.py doubt` (site `merge`) compares `pr` and `head` with its record, maps a `merge_gates` detail starting `not_verified` to `merge_not_verified`, and any other non-`pass` verdict to `merge_not_ready`. Keep the key names and the detail grammar exactly as specified.
- **JSON escaping.** Do not run `printable` on JSON strings. `json.dumps` with the default `ensure_ascii=True` already escapes control characters and non-ASCII.
- **Same directory.** The sibling load uses the script's own directory, so `plugins/writ/scripts/pr-ready.py` loads `plugins/writ/scripts/verify-ledger.py`. Both are byte copies from `gen-platform-trees.py`.
- **Snapshots in tests.** Write each snapshot with the head under test in both `view.headRefOid` and the threads `headRefOid`. A mismatch adds `unknown: head_moved`.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Load ledger module, Read ledger (pr-ready), Check, Compute patch-id] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [`pr-ready.py check` (Happy)] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Business Rule 2 (`pass` requires the ledger to read VERIFIED), Business Rule 9 (exact or same-PR patch-id), Merge gates table (`not_verified`; it never explains `BLOCKED`)] — spec.md → ## Specification Contract → 📋 Business Rules; spec.md → ## Business Rules (Expanded) → ### Merge gates, ### Ledger check; spec.md → ### Locked Answers and Reconciliation (`--json` head, second spec parses the JSON)
- **Experience:** [Moment of truth (`ledger VERIFIED` summary), Error experience (new head → `not_verified`, exit 6), State Catalog rows "New head, not verified" and "Ledger file unreadable"] — spec.md → ## Specification Contract → 🎯 Experience Design; spec.md → ## Experience Design → ### State Catalog

## What Was Built

**Implementation Date:** 2026-11-06

### Files Created

None. Story 3 extends Story 2's files.

### Files Modified

1. **`scripts/pr-ready.py`** (588 lines, from 462)
   - `_load_sibling` / `_verify_ledger` load `verify-ledger.py` from the script's own directory on first use, with `sys.dont_write_bytecode` set; any load failure, or a module without `ledger_check` or `LedgerError`, exits 2 with `pr-ready: cannot load verify-ledger.py (<cause>)`.
   - `ledger_gate(repo)` wraps `ledger_check(repo, pr=, head=)` and maps `LedgerError` to `fail` with `ledger_unreadable (<detail>)`.
   - `evaluate` adds `not_verified head <short>: <first reason>` (or `not_verified ledger_unreadable (...)`) after `behind` and before `merge_state_blocked`, computed after the BLOCKED explanation so it never explains BLOCKED. The pass summary ends `, ledger VERIFIED`.
   - `--json` prints one `json.dumps(..., sort_keys=True)` object (`verdict`, `exit`, `pr`, `head`, `blockers`, `unknowns`, `ledger`) with the text run's exit code. The module docstring documents the gate, sibling loading, and `--json`.
2. **`scripts/tests/test_pr_ready.py`** (802 lines, from 483)
   - `PrReadyCase.setUp` writes an exact-head ledger row for `clean.json`'s head, so Story 2's cases still pass; their pass summary now ends `ledger VERIFIED`.
   - Story 3 section: `LedgerRepoCase` (test-free base: temp git repo plus a real `verify-ledger.py record`), `LedgerGateTests` (5), `JsonTests` (3), `SiblingLoadTests` (4).
3. **`plugins/writ/scripts/pr-ready.py`**
   - Byte copy regenerated by `python3 scripts/gen-platform-trees.py`.
4. **`.writ/docs/agent-cli-contract.md`** (Notes)
   - The two `pr-ready.py` sentences from technical-spec § Notes entries (`--json`; `pass` requires `verify-ledger.py`).
5. **`.writ/specs/2026-11-06-pr-ready-and-ledger/drift-log.md`**, **`spec-lite.md`**
   - DEV-009 and its spec-lite amendment.

### Implementation Decisions

1. **No coding subagent** — the lane ran the coding role itself (tests first: 11 new tests failed before the script changed); Gate 3 ran as a spawned read-only `review-agent` (Gate 2.5 routed it).
2. **A `(pr, head)` gate, not the raw `ledger_check`** — keeps `evaluate` free of the ledger module's exception type (DEV-009).
3. **No bytecode from the sibling load** — the review found `exec_module` wrote `__pycache__/verify-ledger.*.pyc` beside the script under a default Python; `test_check_writes_no_bytecode` fails on an unfixed copy under 3.9 and 3.14.
4. **Ledger kept out of test commits** — the temp repo excludes `.writ/` so `git add -A` on a test branch cannot carry the ledger away on checkout.

### Test Results

**Verification:** `uv run --isolated --python 3.9 --with pytest pytest -q scripts/tests/test_pr_ready.py scripts/tests/test_pr_ready_head_repro.py scripts/tests/test_verify_ledger.py scripts/tests/test_agent_cli_contract.py scripts/tests/test_agent_cli_contract_doc.py` and the same on 3.14: 393 passed each (`test_pr_ready.py` alone: 37 passed, 86 subtests on 3.14). `gen-platform-trees.py --check`: pass. Gate scripts: arch-check pass (rederived proceed); boundary-map crossings pass, 2 crossings (the map lists `pr-ready.py` without its directory), route review-agent; change-surface cross-component; review-override check unverifiable (no_coverage_report); safety-fact pass (measured tested); evidence not run (PASS); drift-format pass; test-integrity authenticity pass; app-verify unverifiable (no_recipe); docs-check unverifiable (no public exports); jev ac-shadow unverifiable (no_evaluator_ids).
**Coverage:** 96%
- ✅ `test-integrity.py coverage --new-files scripts/pr-ready.py`: pass, re-derived from a subprocess-measured cobertura report (325 statements, 13 missed)
- ✅ The verified head passes and a one-byte change exits 6 against a real `verify-ledger.py record` row
- ✅ `--json` checked against the text run for every fixture and the AC-3.1 repo

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** All changes are within Owned paths or the generated plugin copy. The review's Minor (bytecode write) and two recommended tests were applied after the PASS.

### Deviations from Spec

- **[DEV-009] `evaluate` takes a `(pr, head)` gate that wraps `ledger_check`, and the loader checks the module and writes no bytecode** — Severity: Small
  - Spec said: Story 3 passes the loaded `ledger_check`; a load error exits 2.
  - Reality: `ledger_gate(repo)` maps `LedgerError` to `ledger_unreadable`; a module without `ledger_check` or `LedgerError` exits 2; the load sets `sys.dont_write_bytecode`.
  - Resolution: Auto-amended spec-lite.md
