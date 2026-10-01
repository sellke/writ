# Story 5: exit-criteria.py Evidence Check, Mutation Test, and Eval Check

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer, or any developer whose `/implement-phase` run is checked at stop time
**I want to** have `exit-criteria.py` confirm that every machine-verified UAT scenario cites evidence that exists and records a `pass` verdict, and have `eval.sh` prove the whole path on the fixture app
**So that** a scenario reading "passed — evidence: `evidence/uat/<id>/result.json`" can't stand without a passing file on disk behind it, and the fixture's UAT scenarios pass end to end with machine evidence and no human step

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [x] Given a merged spec whose populated, correctly ordered `uat-plan.md` has `### Scenario N: <title>` blocks, when `exit-criteria.py check --command implement-phase` evaluates `implement-phase.c2`, then every scenario carrying `**Verification:** machine — evidence: <path>` has `<path>` resolved relative to that spec folder and is satisfied only when the file exists inside the spec folder and parses as JSON with `"verdict": "pass"`; a missing file, a verdict other than `pass` (including `fail (timeout)`), an unreadable or non-JSON `result.json`, a path that resolves outside the spec folder, or a `machine` line with no `evidence:` path each make c2 `unmet` with a reason naming the spec and the scenario (e.g. `evidence missing: <spec-id> / Scenario 3 (evidence/uat/home/result.json)`); `**Verification:** human — <reason>` scenarios are ignored; the existing presence and ordering halves are unchanged `[AC-5.1]`
- [x] Given a populated plan with no `**Verification:**` lines (pre-Phase-12), when c2 runs, then the evidence half is met and the c2 evidence string notes `legacy plan: <spec-id>`; a plan with `**Verification:**` lines but no `machine` scenarios is met and notes `no machine scenarios: <spec-id>`; `CRITERION_TEXT["implement-phase.c2"]` stays byte-identical to the `exit_criteria` line in `commands/implement-phase.md`; and `.writ/docs/exit-criteria-classification.md` records the evidence half under `## implement-phase.c2` with its Bucket Table row still parsing as `evaluable-now` `[AC-5.2]`
- [x] Given `exit-criteria.py check-uat --spec DIR`, when it runs, then it evaluates only the evidence half for that one spec folder and prints one JSON object (schema `exit-criteria-check-v1`, `verdict`, `spec`, `scenarios` with each machine scenario's path and outcome, plus `reason` or `evidence`), exiting 0 met, 1 unmet, and 2 impossible when DIR or its `uat-plan.md` is missing or unreadable; the module stays read-only (no file writes, no non-read-only git calls), stdlib-only, and green on Python 3.9 `[AC-5.3]`
- [x] Given a temp fixture spec whose `uat-plan.md` has one machine scenario citing `evidence/uat/home/result.json` with verdict `pass`, when `check-uat` and the c2 predicate run, then both report met; when that `result.json` is deleted and both run again, then both report `unmet` naming the spec and scenario — the missing-evidence mutation of Business Rule 6 `[AC-5.4]`
- [x] Given `scripts/eval.sh`, when `bash scripts/eval.sh --check=app-verify` runs outside the sandbox, then `check_app_verify` runs `scripts/app-verify.py run` against the Story 3 fixture recipes in a temp spec folder on 127.0.0.1 — `recipe-pass.md` exits 0 with a `pass` `result.json`, `recipe-fail.md` exits 1, `recipe-safety-refused.md` exits 2 with `refused` and no `_launch/` directory — then writes a fixture `uat-plan.md` whose machine scenarios cite the pass run's evidence, confirms `check-uat` exits 0 with no human step, deletes the cited `result.json`, and confirms `check-uat` exits 1; any deviation is an `add_finding`, `app-verify` is registered in `CHECKS=(...)`, `require_literal` pins the `check-uat` and `legacy plan` literals, no fixture process survives, and the full `eval.sh` reports Findings 0 `[AC-5.5]`

## Implementation Tasks

- [x] 5.1 Write failing tests in `scripts/tests/test_exit_criteria.py`: append `PhaseC2EvidenceTests` (reusing `PhaseGitFixture`) and `CheckUatTests` with a docstring naming `2026-10-01-behavioral-verification` Story 5, covering passing evidence, missing file, verdict `fail`, non-JSON `result.json`, path escaping the spec folder, `machine` with no path, human-only scenarios ignored, legacy plan, no-machine-scenarios plan, `check-uat` exit codes 0/1/2, the delete-`result.json` mutation for both entry points, and a byte-equality check of `CRITERION_TEXT["implement-phase.c2"]` against `commands/implement-phase.md` `[AC-5.1, AC-5.2, AC-5.3, AC-5.4]`
- [x] 5.2 Implement the evidence half in `scripts/exit-criteria.py`: a scenario parser over `### Scenario N:` blocks reading the `**Verification:**` line (grammar from Story 2 / spec.md → Detailed Requirements → UAT scenario lines), a resolver that rejects paths outside the spec folder, and a `result.json` reader. Call it from `_predicate_phase_c2` after the stub check, add an `evidence` problem bucket to the existing reason join, and append the `legacy plan` / `no machine scenarios` notes to the met evidence string, leaving `CRITERION_TEXT` untouched `[AC-5.1, AC-5.2]`
- [x] 5.3 Add the `check-uat --spec DIR` subparser in `build_parser`, reusing the same evidence-half function. Update the module docstring's subcommand list, and make `main`'s `Impossible` handler work without `args.command` (report `spec` instead) `[AC-5.3, AC-5.4]`
- [x] 5.4 Record the evidence half in `.writ/docs/exit-criteria-classification.md`: add an **Evidence — evidence half** paragraph under `## implement-phase.c2` covering the machine-scenario rule, the legacy-plan and vacuous notes, the unreadable-is-unmet rule, and the `check-uat` entry point. Widen its Bucket Table cell to `evaluable-now (split: presence + ordering + evidence)` only after confirming `_normalize_bucket` and `test_bucket_counts_match_the_docs_own_summary` still pass `[AC-5.2]`
- [x] 5.5 Write failing `scripts/tests/test_eval_app_verify.sh`, following `test_eval_spec_analyze.sh`, with a header naming Story 5 and the AC IDs. It asserts `app-verify` is in `CHECKS=(...)` and `check_app_verify()` is defined; `--check=app-verify` on the real repo exits 0 with no `FAIL` line; and a temp root with a stub `app-verify.py` that always exits 0 (so the fail and refuse expectations break) yields `add_finding` and exit 1 `[AC-5.5]`
- [x] 5.6 Implement `check_app_verify` in `scripts/eval.sh` and register `app-verify` in `CHECKS`. It works in a `mktemp -d` spec folder and picks a free port, rewriting it in copies of the fixture recipes. It runs the pass, fail, and safety-refused variants, writes the fixture `uat-plan.md` with `**Feature:**` / `**Verification:** machine — evidence:` lines, then runs `check-uat`, deletes the cited `result.json`, and runs `check-uat` again. Any unexpected exit code or verdict is an `add_finding`. Add `require_literal` pins for `check-uat` in `exit-criteria-classification.md` and `legacy plan` in `exit-criteria.py` `[AC-5.4, AC-5.5]`
- [x] 5.7 Verify: `uv run --python 3.9 pytest scripts/tests/test_exit_criteria.py` and the full `uv run pytest` pass; `bash scripts/tests/test_eval_app_verify.sh` and the bash suite pass; `bash scripts/eval.sh` (outside the sandbox) reports Findings 0; `ps` shows no fixture process left; `git diff` confirms `commands/implement-phase.md` is untouched; walk the four Evidence check Shadow Path cells against the tests `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

## Notes

- **The criterion prose does not change.** The evidence half reads "populated" the same way the presence half already does: a plan whose machine scenarios have no passing evidence is not populated with a true result. That is why `CRITERION_TEXT` and the `exit_criteria` line in `commands/implement-phase.md` stay verbatim. The classification doc is where the widened mechanism gets recorded, consistent with how the split entry already records presence and ordering.
- **Read-only stays true.** `check-uat` and the predicate only read `uat-plan.md` and `result.json`. The mutation (deleting `result.json`) happens in the test or eval harness, never in `exit-criteria.py`. The evidence half needs no git calls at all.
- **Fail closed.** Unreadable JSON, a path that escapes the spec folder, and a `machine` line with no path are all `unmet`, not `impossible`. Each is a defect in that plan, not a reason the checker can't trust its inputs, so a single bad spec doesn't poison the whole phase verdict. `impossible` is reserved for `check-uat` being unable to read the plan at all.
- **Paths, not IDs.** Per technical-spec → Interaction Edge Cases, a renamed feature leaves a stale path, and that path is `unmet`. The check never maps feature IDs back to the recipe, and it never reads `.writ/docs/app-verification.md`.
- **`main` regression risk.** `main`'s `Impossible` handler reads `args.command`, which `check-uat` doesn't define. Without the fix in task 5.3, an impossible `check-uat` raises `AttributeError` instead of exiting 2.
- **Check naming.** Existing `eval.sh` checks use kebab-case `CHECKS` entries with snake-case functions (`spec-analyze` / `check_spec_analyze`). The technical spec's "`app_verify` check" maps to `app-verify` / `check_app_verify`.
- **Sandbox and ports.** `eval.sh` runs a `git init` in a temp dir and this check spawns local processes, so run it outside the sandbox. Pick a free port per run so the check can't collide with a dev server or trip Story 3's `instance_already_running` refusal.
- **Integration.** Story 2 defines the `**Feature:**` and `**Verification:**` lines this story parses. Story 3 supplies `app-verify.py run`, the fixture recipes (`recipe-pass.md`, `recipe-fail.md`, `recipe-safety-refused.md`), and the `app-verify-result-v1` `result.json`. If Story 3's file names differ when it lands, update the eval check to match rather than renaming the fixtures. Plans that `scripts/recommend-state.py` renders carry no `**Verification:**` lines and fall under `legacy plan`.
- **Closes the spec's Success Criteria.** This story's eval check is the end-to-end proof: the fixture's UAT scenarios pass with machine-captured evidence and no human step, and the missing-evidence mutation reports `unmet`.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Evidence check] — from sub-specs/technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Evidence check (all four cells: all pass → met; no machine scenarios → met, vacuous, noted; no `**Verification:**` lines → met, `legacy plan`; unreadable `result.json` → unmet)] — from sub-specs/technical-spec.md → ## Shadow Paths
- **Business rules:** [6 Missing evidence file reports `unmet`, proven by mutation; Expanded 7 Evidence layout and `result.json` fields; Expanded 8 Evidence path resolved relative to the spec folder, verdict must be `pass`] — from spec.md → 📋 Business Rules and ## 📋 Business Rules (Expanded)
- **Experience:** [Moment of truth (passed — evidence line backed by a real file)] — from spec.md → Specification Contract → 🎯 Experience Design
- **Technical:** sub-specs/technical-spec.md → ## Files in Scope (rows for Story 5), ## Interaction Edge Cases (Feature ID renamed after evidence written), ## Integration Notes (`eval.sh` outside the sandbox); spec.md → ## Detailed Requirements → UAT scenario lines; spec.md → Success Criteria

## What Was Built

**Implementation Date:** 2026-10-01

### Files Created

1. **`scripts/tests/test_eval_app_verify.sh`** — registration; the real `--check=app-verify` run exits 0 with no `FAIL`; a stub that always exits 0 yields findings and exit 1; contract-honouring stubs prove the `_launch/`-on-refused finding and the surviving-process finding; a missing helper is a finding. [AC-5.4, AC-5.5]

### Files Modified

1. **`scripts/exit-criteria.py`** — `_uat_evidence_half` / `_evidence_outcome`: parses `### Scenario N:` blocks, reads each block's own `**Verification:**` line, resolves `machine — evidence: <path>` inside the spec folder (symlinks resolved), and requires a JSON object with `"verdict": "pass"`; missing, not-pass, unreadable, outside, and pathless lines are `unmet` naming spec and scenario; human scenarios ignored; `legacy plan` / `no machine scenarios` notes. Wired into `_predicate_phase_c2` after the stub check (presence and ordering halves unchanged; `CRITERION_TEXT` untouched). New `check-uat --spec DIR` (exit 0/1/2, `exit-criteria-check-v1` JSON with `scenarios`); `main`'s `Impossible` handler no longer reads `args.command` for `check-uat`. Read-only, stdlib, 3.9. [AC-5.1, AC-5.2, AC-5.3]
2. **`scripts/tests/test_exit_criteria.py`** — `PhaseC2EvidenceTests` (14) and `CheckUatTests` (14): every unmet outcome, human ignored, legacy and vacuous notes, ordering still enforced, criterion-text byte equality, classification record, read-only snapshot, exit codes, absolute/symlink/backticked paths, non-object JSON, non-string verdict, per-block attribution, bulleted lines, and the delete-`result.json` mutation through both entry points. [AC-5.1, AC-5.2, AC-5.3, AC-5.4]
3. **`.writ/docs/exit-criteria-classification.md`** — Bucket Table cell `evaluable-now (split: presence + ordering + evidence)`; **Evidence — evidence half** paragraph under `## implement-phase.c2`. [AC-5.2]
4. **`scripts/eval.sh`** — `check_app_verify` registered as `app-verify`: free port, pass (exit 0, pass `result.json`), fail (exit 1), safety-refused (exit 2, `refused`, no `_launch/`), PID-file survival check, fixture `uat-plan.md`, `check-uat` 0 then 1 after deleting the cited `result.json`; `require_literal` pins for `check-uat` and `legacy plan`; two `referenced_paths_allowlist` rows for the recipe paths `/create-uat-plan` creates. [AC-5.4, AC-5.5]

### Verification

- `test_exit_criteria.py` → 80 passed on 3.9; coverage of `scripts/exit-criteria.py` 91% (`test-integrity.py coverage` pass); authenticity pass.
- `bash scripts/eval.sh --check=app-verify` → PASS (~2 s); full `bash scripts/eval.sh` → Findings 0, Run errors 0; full `uv run pytest` → 2109 passed, 1 skipped; bash suite clean; `pgrep` shows no fixture process; `commands/implement-phase.md` untouched.
- Evidence check Shadow Paths: all pass → met; no machine scenarios → met, noted; no `**Verification:**` lines → met, `legacy plan`; unreadable `result.json` → unmet — each has a test.
- Gates: arch-check pass; boundary-map 0 crossings → `evaluator-agent`; Gate 3 iteration 1 FAIL (full eval Findings 2 from Story 2's unallowlisted recipe paths; untested edge cases), iteration 2 PASS (Small); docs-check unverifiable (no public exports); drift-format pass. Free-port race in `check_app_verify` noted as Minor.
- Drift: DEV-010..DEV-012, all Small.
- Iteration count: 2
