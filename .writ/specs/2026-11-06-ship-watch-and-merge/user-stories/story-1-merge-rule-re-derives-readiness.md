# Story 1: The merge rule re-derives readiness

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None (spec dependency: `2026-11-06-pr-ready-and-ledger` complete)

## User Story

**As a** command that wants to merge a PR without asking
**I want to** pass `jev-judge.py doubt` a merge record that names the PR, its head, and the snapshot I judged
**So that** a merge acts only when `pr-ready.py`, re-run locally by the doubt check, passes for that exact head, and a calibrated Jev threshold agrees, while every other merge and every release still asks

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given a `site: merge` record with `pr`, `head_sha`, and `snapshot`, a stub `pr-ready.py` that prints a `pass` JSON object for that PR and head, a calibrated threshold of 0.6, and a fake transport returning p 0.8, when `jev-judge.py doubt` runs, then line 1 is `pass`, `reason: jev_clear` prints, the exit code is 0, and the logged row carries `pr` and `head_sha` `[AC-1.1]`
- [ ] Given the same record and stub, when the provider is enabled with no calibrated threshold, and separately when no provider is configured, then line 1 is `fail`, `reason: fallback_merge` prints, the exit code is 1, and with the provider enabled the row logs Jev's p `[AC-1.2]`
- [ ] Given a temp git repo where `verify-ledger.py record` verified head A of PR 7, when the record and the snapshot name a new head B with a different diff, then the real `pr-ready.py` reports `not_verified`, `doubt` prints `fail` with `reason: merge_not_verified`, and the fake transport is called zero times; and when they name A rebased onto a moved `main` with the same diff, the merge rules pass and the transport is called once `[AC-1.3]`
- [ ] Given a merge record missing `pr`, `head_sha`, or `snapshot`; a stub that is missing, exits 1 or 2, sleeps past the timeout, or prints non-JSON; a stub whose `head` or `pr` differs from the record; a stub reporting another blocker or only an unknown; or a `release` record, when `doubt` runs, then it exits 1 with `no_verification_ledger`, `merge_unverifiable`, `merge_head_mismatch`, `merge_not_ready` (plus `pr_ready_unresolved_threads` or `pr_ready_checks_pending`), or `outward`, and a `pr` of the wrong type or a `head_sha` that is not 40 hex characters exits 2 `[AC-1.4]`
- [ ] Given the Story 1 changes, when the text pins run, then `_preamble.md` has separate `release` and `merge` rows in the Doubt Rule table, `recommendation-semantics.md` lists the three record fields and the new step 1 and step 4 text, `system-instructions.md` and `README.md:66` no longer say a merge always waits, `eval.sh` pins `A merge waits too unless`, ADR-033 has a 2026-11-06 amendment, and the `pr-ready.py` Callers cell in `agent-cli-contract.md` reads `scripts/jev-judge.py` `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Append a section to `scripts/tests/test_jev_doubt.py` under a comment naming `2026-11-06-ship-watch-and-merge` Story 1. Add a `_stub_pr_ready(tmp_path, monkeypatch, payload, exit=0, sleep=None)` helper that writes `pr-ready.py` into a temp dir (prints the file named by `PR_READY_STUB_OUT`, exits with `PR_READY_STUB_EXIT`, sleeps `PR_READY_STUB_SLEEP` first) and sets `jev.SCRIPTS_DIR`. Write one test per stub case in technical-spec § Test Plan, plus the release and malformed-field cases. Run on Python 3.9 and confirm they fail `[AC-1.1, AC-1.2, AC-1.4]`
- [ ] 1.2 Add the real-script tests: build the temp repo in technical-spec § Real-script fixture, record head A with the real `scripts/verify-ledger.py`, write the clean snapshot, and assert the new-head and rebased-head outcomes and the fake transport's call counts `[AC-1.3]`
- [ ] 1.3 In `scripts/jev-judge.py`, add `pr`, `head_sha`, and `snapshot` to `DoubtRecord` and `parse_doubt_record` with the type rules in technical-spec § `jev-judge.py` Merge Rule; set `DOUBT_ALWAYS_ASK = {"release": "outward"}` and add `"merge"` to `DOUBT_FALLBACK_ASK`; add `SCRIPTS_DIR`, `PR_READY`, `MERGE_CHECK_TIMEOUT`, and `import subprocess` `[AC-1.2, AC-1.4]`
- [ ] 1.4 Implement `merge_rule(rec, repo)` exactly as technical-spec steps 1-8 describe, call it from `doubt()` before `doubt_rule(rec)` when the site is `merge`, append its info reasons, and add `pr` and `head_sha` to merge log rows. Update the module docstring and the `--record` help with the new rule and fields `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.5 Change the text: the `_preamble.md:49` row into two rows; `recommendation-semantics.md` record table and steps 1 and 4; `system-instructions.md:38-40`; `README.md:66`; the `eval.sh:1081` message and the new `require_literal`; the ADR-033 amendment; the `pr-ready.py` Callers cell. Use the exact text in technical-spec § Text Changes Outside `ship.md`. Add text-pin tests for each to the Story 1 section `[AC-1.5]`
- [ ] 1.6 Run `python3 scripts/gen-platform-trees.py`, then `--check`. Run `python3 scripts/prune-ledger.py check --repo . --base-commit cf84742` and confirm no ledger row is needed for the two base files `[AC-1.5]`
- [ ] 1.7 Verify. Run `uv run --isolated --python 3.9 --with pytest pytest scripts/tests/test_jev_doubt.py scripts/tests/test_agent_cli_contract.py scripts/tests/test_agent_cli_contract_doc.py`, the same on 3.14, then the full suite on both interpreters, each run alone, then `bash scripts/eval.sh`. Check each AC against the test carrying its tag `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

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

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Merge rule: run `pr-ready.py`, Merge rule: compare, Merge rule: ledger, Doubt check] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Merge rule] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Merge rule table (reason order), Business Rule 3 (no calibrated threshold or no provider → merge asks), release stays always-ask] — spec.md → ## Business Rules (Expanded) → ### Merge rule; spec.md → ## Specification Contract → 📋 Business Rules
- **Experience:** [Error experience (with no calibrated threshold a ready PR ends at `asked` with `fallback_merge`)] — spec.md → ## Specification Contract → 🎯 Experience Design
