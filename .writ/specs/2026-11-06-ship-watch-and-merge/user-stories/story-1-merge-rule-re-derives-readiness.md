# Story 1: The merge rule re-derives readiness

> **Status:** Completed ✅ (2026-11-06)
> **Commit:** 67952bf2edea0bca007d533b5c8376f7772e98aa
> **Priority:** High
> **Dependencies:** None (spec dependency: `2026-11-06-pr-ready-and-ledger` complete)

## User Story

**As a** command that wants to merge a PR without asking
**I want to** pass `jev-judge.py doubt` a merge record that names the PR, its head, and the snapshot I judged
**So that** a merge acts only when `pr-ready.py`, re-run locally by the doubt check, passes for that exact head, and a calibrated Jev threshold agrees, while every other merge and every release still asks

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given a `site: merge` record with `pr`, `head_sha`, and `snapshot`, a stub `pr-ready.py` that prints a `pass` JSON object for that PR and head, a calibrated threshold of 0.6, and a fake transport returning p 0.8, when `jev-judge.py doubt` runs, then line 1 is `pass`, `reason: jev_clear` prints, the exit code is 0, and the logged row carries `pr` and `head_sha` `[AC-1.1]`
- [x] Given the same record and stub, when the provider is enabled with no calibrated threshold, and separately when no provider is configured, then line 1 is `fail`, `reason: fallback_merge` prints, the exit code is 1, and with the provider enabled the row logs Jev's p `[AC-1.2]`
- [x] Given a temp git repo where `verify-ledger.py record` verified head A of PR 7, when the record and the snapshot name a new head B with a different diff, then the real `pr-ready.py` reports `not_verified`, `doubt` prints `fail` with `reason: merge_not_verified`, and the fake transport is called zero times; and when they name A rebased onto a moved `main` with the same diff, the merge rules pass and the transport is called once `[AC-1.3]`
- [x] Given a merge record missing `pr`, `head_sha`, or `snapshot`; a stub that is missing, exits 1 or 2, sleeps past the timeout, or prints non-JSON; a stub whose `head` or `pr` differs from the record; a stub reporting another blocker or only an unknown; or a `release` record, when `doubt` runs, then it exits 1 with `no_verification_ledger`, `merge_unverifiable`, `merge_head_mismatch`, `merge_not_ready` (plus `pr_ready_unresolved_threads` or `pr_ready_checks_pending`), or `outward`, and a `pr` of the wrong type or a `head_sha` that is not 40 hex characters exits 2 `[AC-1.4]`
- [x] Given the Story 1 changes, when the text pins run, then `_preamble.md` has separate `release` and `merge` rows in the Doubt Rule table, `recommendation-semantics.md` lists the three record fields and the new step 1 and step 4 text, `system-instructions.md` and `README.md:66` no longer say a merge always waits, `eval.sh` pins `A merge waits too unless`, ADR-033 has a 2026-11-06 amendment, and the `pr-ready.py` Callers cell in `agent-cli-contract.md` reads `scripts/jev-judge.py` `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Append a section to `scripts/tests/test_jev_doubt.py` under a comment naming `2026-11-06-ship-watch-and-merge` Story 1. Add a `_stub_pr_ready(tmp_path, monkeypatch, payload, exit=0, sleep=None)` helper that writes `pr-ready.py` into a temp dir (prints the file named by `PR_READY_STUB_OUT`, exits with `PR_READY_STUB_EXIT`, sleeps `PR_READY_STUB_SLEEP` first) and sets `jev.SCRIPTS_DIR`. Write one test per stub case in technical-spec § Test Plan, plus the release and malformed-field cases. Run on Python 3.9 and confirm they fail `[AC-1.1, AC-1.2, AC-1.4]`
- [x] 1.2 Add the real-script tests: build the temp repo in technical-spec § Real-script fixture, record head A with the real `scripts/verify-ledger.py`, write the clean snapshot, and assert the new-head and rebased-head outcomes and the fake transport's call counts `[AC-1.3]`
- [x] 1.3 In `scripts/jev-judge.py`, add `pr`, `head_sha`, and `snapshot` to `DoubtRecord` and `parse_doubt_record` with the type rules in technical-spec § `jev-judge.py` Merge Rule; set `DOUBT_ALWAYS_ASK = {"release": "outward"}` and add `"merge"` to `DOUBT_FALLBACK_ASK`; add `SCRIPTS_DIR`, `PR_READY`, `MERGE_CHECK_TIMEOUT`, and `import subprocess` `[AC-1.2, AC-1.4]`
- [x] 1.4 Implement `merge_rule(rec, repo)` exactly as technical-spec steps 1-8 describe, call it from `doubt()` before `doubt_rule(rec)` when the site is `merge`, append its info reasons, and add `pr` and `head_sha` to merge log rows. Update the module docstring and the `--record` help with the new rule and fields `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.5 Change the text: the `_preamble.md:49` row into two rows; `recommendation-semantics.md` record table and steps 1 and 4; `system-instructions.md:38-40`; `README.md:66`; the `eval.sh:1081` message and the new `require_literal`; the ADR-033 amendment; the `pr-ready.py` Callers cell. Use the exact text in technical-spec § Text Changes Outside `ship.md`. Add text-pin tests for each to the Story 1 section `[AC-1.5]`
- [x] 1.6 Run `python3 scripts/gen-platform-trees.py`, then `--check`. Run `python3 scripts/prune-ledger.py check --repo . --base-commit cf84742` and confirm no ledger row is needed for the two base files `[AC-1.5]`
- [x] 1.7 Verify. Run `uv run --isolated --python 3.9 --with pytest pytest scripts/tests/test_jev_doubt.py scripts/tests/test_agent_cli_contract.py scripts/tests/test_agent_cli_contract_doc.py`, the same on 3.14, then the full suite on both interpreters, each run alone, then `bash scripts/eval.sh`. Check each AC against the test carrying its tag `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

- **Depends on the first spec.** The real-script tests need `scripts/pr-ready.py` (with `--json`) and `scripts/verify-ledger.py` on disk. Do not start until `2026-11-06-pr-ready-and-ledger` is complete.
- **No ledger subprocess.** The locked seam sheet replaced the contract's separate `verify-ledger.py check` call. A pr-ready `pass` already needs the ledger to read VERIFIED (spec.md → Reconciliations, item 1).
- **Reason order.** `merge_head_mismatch` is checked before `merge_not_verified`, so a stale snapshot never reads as a ledger failure.
- **Exit codes 3-6 are normal.** `pr-ready.py` exits 3, 4, 5, or 6 with a JSON object on stdout when a blocker holds. Only 1, 2, and other codes are `merge_unverifiable`.
- **Existing row stays.** `({"site": "merge"}, "no_verification_ledger")` in `test_rules_ask_without_calling_jev` keeps passing: the base record has no `pr`.
- **Timeout test.** Monkeypatch `jev.MERGE_CHECK_TIMEOUT` to 1 and sleep 3 in the stub, so the test stays short.
- **Git in tests.** Pass `-c user.name=t -c user.email=t@t` on every commit, and set `GIT_CONFIG_GLOBAL=/dev/null` for the temp repo so hostile user config cannot change the patch-id.
- **No network.** The merge rule runs two local processes at most: the stub or real `pr-ready.py`, and git inside it. The fake transport is the only network stand-in.
- **Base files.** `system-instructions.md` and `_preamble.md` are the pruned base. The changed lines date from 2026-11-05, after `cf84742`, so `prune-ledger.py check` should need no row. If it asks for one, add the row to `.writ/decision-records/pruned-instructions-ledger.md`.
- **Generated copies.** `plugins/writ/scripts/jev-judge.py`, the `_preamble.md` copies, and the `system-instructions.md` copies (including `cursor/writ.mdc` and `plugins/writ/output-styles/writ.md`) come from `gen-platform-trees.py`. Never hand-edit them.
- **Callers cell.** Edit only the Callers cell of the `pr-ready.py` row. Story 3 extends it to `commands/ship.md, scripts/jev-judge.py`.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Merge rule: run `pr-ready.py`, Merge rule: compare, Merge rule: ledger, Doubt check] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Merge rule] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Merge rule table (reason order), Business Rule 3 (no calibrated threshold or no provider → merge asks), release stays always-ask] — spec.md → ## Business Rules (Expanded) → ### Merge rule; spec.md → ## Specification Contract → 📋 Business Rules
- **Experience:** [Error experience (with no calibrated threshold a ready PR ends at `asked` with `fallback_merge`)] — spec.md → ## Specification Contract → 🎯 Experience Design

## What Was Built

**Implementation Date:** 2026-11-06

### Files Created

None.

### Files Modified

1. **`scripts/jev-judge.py`** (2,570 lines, from 2,466)
   - `DOUBT_ALWAYS_ASK = {"release": "outward"}`; `DOUBT_FALLBACK_ASK` gains `"merge"`. New `SCRIPTS_DIR`, `PR_READY`, `MERGE_CHECK_TIMEOUT = 120`, `HEAD_SHA`, and `import subprocess`.
   - `DoubtRecord` gains `pr`, `head_sha`, `snapshot` (defaults `None`, `""`, `""`); `parse_doubt_record` exits 2 on a `pr` that is not an int ≥ 1 (bools refused), a `head_sha` that is not exactly 40 hex, or a blank `snapshot`.
   - `merge_rule(rec, repo)` follows technical-spec steps 1-8: resolves `repo`, runs `pr-ready.py check --snapshot <s> --repo <r> --json` from `SCRIPTS_DIR` with a timeout, and maps the result to `no_verification_ledger`, `merge_unverifiable` (+ `pr_ready_missing|timeout|not_run|exit_<n>|unparseable`), `merge_head_mismatch`, `merge_not_verified`, or `merge_not_ready` (+ `pr_ready_<first class or code>`). `doubt()` calls it before `doubt_rule` on `site: merge` and logs `pr` and `head_sha` on merge rows only.
   - Module docstring (`--help`) and the `--record` help state the new rule and fields.
2. **`scripts/tests/test_jev_doubt.py`** (903 lines, from 451) — Story 1 section: a `_stub_pr_ready` helper (stub `pr-ready.py` driven by `PR_READY_STUB_OUT`, `_EXIT`, `_SLEEP`), stub cases for every reason in the merge rule table, malformed fields, release, argv and relative-repo checks, two real-script cases (temp git repo, real `verify-ledger.py record` and `pr-ready.py`), and text pins.
3. **`commands/_preamble.md`** — Doubt Rule table: separate `release` and `merge` rows.
4. **`.writ/docs/recommendation-semantics.md`** — record table rows `pr`, `head_sha`, `snapshot`; "How the check decides" steps 1 and 4.
5. **`system-instructions.md`** — "Release stays a person's call" names when a merge may proceed.
6. **`README.md`** — the Initiative bullet no longer says a merge always waits.
7. **`scripts/eval.sh`** — reworded message on the `Release stays a person's call` pin; new `require_literal "$system" "A merge waits too unless"`.
8. **`.writ/decision-records/adr-033-doubt-gated-autonomy.md`** — `### 2026-11-06 — Merge acts under the ledger (Phase 16)` amendment and the header's Amended line.
9. **`.writ/docs/agent-cli-contract.md`** — `pr-ready.py` Callers cell: `scripts/jev-judge.py`.
10. **Generated copies** — `plugins/writ/scripts/jev-judge.py`, `plugins/writ/commands/_preamble.md`, `plugins/writ/system-instructions.md`, `plugins/writ/output-styles/writ.md`, `cursor/plugin/commands/_preamble.md`, `cursor/plugin/system-instructions.md`, `cursor/plugin/rules/writ.mdc`, `cursor/writ.mdc`, all by `python3 scripts/gen-platform-trees.py`.
11. **`.writ/specs/2026-11-06-ship-watch-and-merge/drift-log.md`** (created), **`spec-lite.md`** — DEV-001 and its amendment.

### Implementation Decisions

1. **No coding subagent.** This harness registers no `coding-agent` type, so the lane wrote the code itself, tests first: 37 new tests failed before `jev-judge.py` changed. Gate 3 ran as a spawned read-only `review-agent` (Gate 2.5 routed it).
2. **Stub through the environment.** `merge_rule` passes no `env`, so the stub reads `PR_READY_STUB_*` from the inherited environment (`monkeypatch.setenv`).
3. **Review findings applied after the PASS.** `repo.resolve()` before building the child's paths (a relative `--repo` doubled them), and tests for reason order (mismatch before `not_verified`), rule order (merge rule before the generic rules), case-insensitive heads, an `OSError` start, an absolute snapshot, a verdict-only `fail`, and a relative `--repo`.

### Test Results

**Verification:** `uv run --isolated --python 3.9 --with pytest pytest -q` on `test_jev_doubt.py`, `test_agent_cli_contract.py`, `test_agent_cli_contract_doc.py`, `test_gen_platform_trees.py`, `test_prune_ledger.py`, `test_plugin_distribution.py`, `test_front_door.py`, `test_eval_shipped_refs.py`, `test_governor_enforcement.py`, `test_adr_032_inventory.py`: 780 passed; the same on 3.14: 780 passed. After the review fixes, `test_jev_doubt.py`: 90 passed on 3.9 and 3.14. `gen-platform-trees.py --check`: pass. `prune-ledger.py check --base-commit cf84742`: exit 0, no row needed (base 8,861 bytes, cap 10,000). `bash scripts/eval.sh --report=<scratch>`: exit 0. Full pytest and the bash suite run once at spec close-out. Gate scripts: arch-check pass (rederived proceed); boundary-map crossings pass, 11 crossings (generated copies, the ADR, the contract doc), route review-agent; change-surface cross-component; review-override check pass; safety-fact pass (measured tested); evidence-gate not run (PASS); drift-format pass; test-integrity authenticity pass, coverage unverifiable (no coverage report; no new source file); app-verify unverifiable (no_recipe); docs-check unverifiable (no public exports); jev ac-shadow unverifiable (no_evaluator_ids).
**Coverage:** `merge_rule` and `_merge_token`: every line and branch run (`coverage run --branch` over `test_jev_doubt.py`, Python 3.9).
- ✅ AC-1.1 to AC-1.4 by stub and real-script tests; AC-1.5 by text pins.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** 11 crossings, each named by the story or the lock reconciliations (generated copies, ADR-033, the contract doc's Callers cell).
- `reviewer-filters: on` · `evidence-gate: not run (PASS)` · `safety-fact: tested (claimed tested)` · `gate3-route: review-agent (boundary-map crossings)` · `arch-lint: none — see .writ/docs/architecture-lint.md`

### Deviations from Spec

- **[DEV-001] The merge rule validates a little more than the technical spec, and resolves `--repo` first** — Severity: Small
  - Spec said: step 7 token as printed; `head_sha` regex; non-empty `snapshot`; child paths built from `repo` as given.
  - Reality: normalized token, whitespace-strict fields, `repo.resolve()` first.
  - Resolution: Auto-amended spec-lite.md
