# Story 3: Run Script and Fixture App (Safety, Launch, Check, Evidence, Cleanup)

> **Status:** Completed ✅
> **Commit:** d992dc4b56817eeeaac178f16230adb5e53709c4
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** developer using Writ on their own project
**I want to** have `scripts/app-verify.py` find the features my changed files touch, then start my app, run my project's own checks against it, save the evidence, and stop what it started
**So that** a feature passes or fails on a machine verdict (an exit code) with evidence on disk. The run refuses unsafe targets by default and never leaves a process behind

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given a valid recipe whose feature map has `Paths` globs, when `app-verify.py touched --recipe PATH --changed FILE...` runs, then it prints the ID of each feature with a check whose comma-separated globs match at least one repo-relative changed path (feature-map order, one per line), prints nothing for `human-only` rows, prints `app-verify: no mapped features touched by this story` when none match, and exits 0. A missing recipe exits 2 with `unverifiable (no_recipe)`, and an invalid recipe exits 2 with `unverifiable (recipe_invalid: <finding>)` `[AC-3.1]`
- [x] Given a recipe with `- **Variable:**` entries, when `run` resolves each variable from the process environment and then from the named `- **Env file:**` (read-only, `KEY=VALUE` lines only), then a value that is unset, matches no `Allowed` fnmatch pattern, or matches a `Never` pattern exits 2 with `refused (<var> …)`, and nothing launches. A missing or unreadable env file counts as unset. When the readiness URL already answers before launch and `Reuse running instance` is not `yes`, the run exits 2 with `refused (instance_already_running)`. On a non-POSIX platform it exits 2 with `unverifiable (unsupported_platform)` `[AC-3.2]`
- [x] Given the fixture pass recipe, when `run --recipe PATH --spec DIR --run-label LABEL` runs, then the app launches in its own process group (`start_new_session=True`) bound to 127.0.0.1, readiness is polled every 0.5 s (any HTTP status below 500, or a TCP connect for `port N`), each selected check runs with `APP_VERIFY_EVIDENCE_DIR` set to its feature directory, and `{spec}/evidence/<label>/<feature>/` holds a `result.json` (schema `app-verify-result-v1`: feature, command, exit_code, verdict, started_at, ended_at, duration_s, recipe_sha256, truncated.stdout/stderr, artifacts) and `stdout.log`/`stderr.log`, each truncated to 256 KB. Recipe `## Evidence` artifacts up to 5 MB per feature are copied; larger ones are recorded by path, and absent ones are recorded as `missing` without failing the run. Launch output goes to `{spec}/evidence/<label>/_launch/`. `--features id,...` restricts the run to those IDs `[AC-3.3]`
- [x] Given the fail, not-ready, and immediately-exiting launch variants, and a check that outlives a small timeout, when `run` executes, then the result is a fail with exit 1: `check_fail.py` writes verdict `fail`, a never-ready app gives `fail (not_ready <N>s)`, a launch command that exits before ready gives `fail (launch_exited <code>)` with the launch logs kept, and a timed-out check has its own process group killed and gets verdict `fail (timeout)` (300 s default) `[AC-3.4]`
- [x] Given any run that launched the app, including fail, not-ready, and timeout runs, when it finishes, then cleanup runs in `finally`: SIGTERM to the started process group, a 10 s wait, then SIGKILL. The optional `After` command runs next, and its failure is a note, never a fail. Evidence is always kept, no fixture PID survives, and no process the script did not start is signalled. The run prints exactly one `app-verify:` summary line (plus a JSON object under `--json`) and exits 0 when every check passed, 1 when any failed, and 2 when nothing ran `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Build the stdlib-only fixture under `scripts/tests/fixtures/app-verify/`. It holds `app.py` (an `http.server` bound to 127.0.0.1 on `PORT`, stateless, plus a `--never-ready` or equivalent mode for the not-ready variant), `check_home.py` (GET `/` and assert the body, exit 0/1), `check_fail.py` (always exits 1), and the recipe variants `recipe-pass.md`, `recipe-fail.md`, `recipe-safety-refused.md`, and `recipe-not-ready.md`. Each variant must pass Story 1's `validate` except where a variant tests an invalid recipe `[AC-3.3, AC-3.4]`
- [x] 3.2 Extend `scripts/tests/test_app_verify.py` with failing tests that name `2026-10-01-behavioral-verification` in the section docstring. Cover `touched` (match, multiple globs, `human-only` excluded, no match, no recipe, invalid recipe); safety (env override with a non-matching value, a `Never` match, an env-file-only value, a missing env file); the pre-launch probe (start the fixture first, refuse, then allow with reuse `yes`); and `unsupported_platform` via a patched platform check `[AC-3.1, AC-3.2]`
- [x] 3.3 Add failing tests for every run-time Error & Rescue Map row: pass with the full `result.json` schema and `_launch/` logs; `check_fail.py` fail; a `false` launch giving `launch_exited`; a never-ready recipe with a short `Ready timeout` giving `not_ready`; a sleep check with a small timeout giving `timeout`; artifacts that are over 5 MB, missing, or copied; log truncation at 256 KB; a failing `After` command as a note; and after every launched run, an assertion that no fixture PID survives. Each test picks a free port and rewrites the recipe's port, so runs never collide `[AC-3.3, AC-3.4, AC-3.5]`
- [x] 3.4 Implement `touched` and the run's pre-launch half in `scripts/app-verify.py` (stdlib, Python 3.9, reusing Story 1's recipe parser and validator). This covers comma-separated `Paths` globs, the `no_recipe`/`recipe_invalid` unverifiable paths, env-then-env-file safety resolution with `fnmatch` `Allowed`/`Never`, the ready probe with the reuse rule, and the POSIX guard `[AC-3.1, AC-3.2]`
- [x] 3.5 Implement the run's launch-to-cleanup half following technical-spec Run Contract steps 4–8. `Popen(shell=True, start_new_session=True)` launches the app; readiness is polled with an early `launch_exited` exit; each check runs in its own session with a timeout that kills its group; `result.json`, the truncated logs, and capped artifact copies are written; cleanup in `finally` does `killpg` SIGTERM, a 10 s wait, SIGKILL, then `After`; the run ends with one `app-verify:` summary line, `--json`, and exit 0/1/2 `[AC-3.3, AC-3.4, AC-3.5]`
- [x] 3.6 Verify the acceptance criteria against the State Catalog lines: run `run` on each fixture variant by hand, inspect `evidence/<label>/`, and confirm with `ps` that no fixture process remains `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
- [x] 3.7 Verify that `uv run --python 3.9 pytest scripts/tests/test_app_verify.py` and the full `uv run pytest` pass, and that the new tests leave no stray processes and write no files outside their temp spec folders `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

- **Runtime boundary.** The script runs only commands the recipe names, keeps no state between runs, and runs no daemon. This is the `build-smoke.py` posture, and Story 1's ADR amendment records it. `build-smoke.py` uses `subprocess.run(timeout=...)`, which kills only the direct child. Here the app and each check must run in their own session so `os.killpg` reaches grandchildren too (a `shell=True` wrapper plus the real server).
- **Testable timeouts.** The recipe grammar has `Ready timeout` but no per-check timeout key, so do not add one. Expose the 300 s check timeout and the 10 s cleanup grace as keyword parameters or module constants that tests can pass or patch, rather than a new CLI flag. Spec changes go through `/edit-spec`.
- **Port collisions.** The recipe variants hardcode a port such as 8765. Tests should copy each variant into a temp dir with a free port substituted, so parallel or repeated runs cannot hit the `instance_already_running` refusal by accident.
- **PID-survival assertion.** Record the launched group's PID (and the fixture's own PID, which the app can write to a file under `APP_VERIFY_EVIDENCE_DIR` or a temp path), then assert `os.kill(pid, 0)` raises `ProcessLookupError` after `run` returns. Reap zombies so the check is not flaky.
- **Safety never edits.** Env files are read, never written, and secret values never appear in `result.json`, logs written by the script, or the summary line. Only the variable name is named in a refusal.
- **Integration.** Story 1 provides the recipe parser and `validate`, which this story imports rather than re-parsing. Stories 2 and 4 consume `touched` and `run` with run labels `uat` and `story-N`, so keep the CLI surface, exit codes, and `app-verify:` line forms exactly as the State Catalog shows them. Story 5's eval check drives these same fixture variants.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Read recipe, Validate recipe, Resolve safety variable, Read env file, Pre-launch probe, Launch, Readiness, Run check (non-zero exit), Run check (timeout), Copy artifacts, Cleanup] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Gate 4.5 (happy, nil: no recipe, empty: no mapped features, upstream error: app never ready) — mechanics only; the gate wiring is Story 4] — technical-spec.md → ## Shadow Paths
- **Business rules:** [2 Machine verdicts only (exit code decides), 3 Safety (refuse by default, env then env file, reuse rule), 4 Cleanup (own process group only, evidence kept), 7 Evidence (result.json fields, 256 KB logs, 5 MB artifacts, `<run>` label)] — spec.md → ## 📋 Business Rules (Expanded)
- **Technical:** [Run Contract steps 1–8, `result.json` schema `app-verify-result-v1`, Interaction Edge Cases (two runs on one port, check writes outside evidence dir, Windows)] — sub-specs/technical-spec.md → ## Run Contract, ## Interaction Edge Cases
- **Experience:** [State Catalog (No recipe, Recipe invalid, Safety refused, No features touched, Checks pass, Check fails, Launch fails), Interaction Patterns (every line starts `app-verify:`, no questions)] — spec.md → ## 🎯 Experience Design → State Catalog

## What Was Built

**Implementation Date:** 2026-10-01

### Files Created

1. **`scripts/tests/fixtures/app-verify/`** — `app.py` (stdlib `http.server` on 127.0.0.1:`$PORT`, stateless, `--never-ready` mode, optional PID file), `check_home.py` (GET `/`, assert body, save it under `APP_VERIFY_EVIDENCE_DIR`), `check_fail.py`, `fixture.env`, and recipes `recipe-pass.md`, `recipe-fail.md`, `recipe-safety-refused.md` (env-file value matches `Never`), `recipe-not-ready.md` (2 s timeout); each validates. [AC-3.3, AC-3.4]

### Files Modified

1. **`scripts/app-verify.py`** — `touched` (comma-separated `Paths` globs via `fnmatchcase`, `./` stripped, human-only rows never printed, `no mapped features` line) and `run` (`run_verification`): POSIX guard, validate, feature selection (`--features`, `unknown_feature`, `no_runnable_features`), env-then-env-file safety with `Allowed`/`Never`, pre-launch probe with the reuse rule, `Popen(shell=True, start_new_session=True)` launch with 0.5 s readiness polling (HTTP < 500 or TCP `port N`) and early `launch_exited`, per-check sessions with `APP_VERIFY_EVIDENCE_DIR` and a 300 s timeout that kills the check's group, `result.json` (`app-verify-result-v1`), 256 KB log caps, 5 MB artifact copies (`copied`/`too_large`/`missing`/`outside_project`), `finally` cleanup (SIGTERM, 10 s grace, SIGKILL, then `After` as a note), SIGTERM-to-exit handler so a killed run still cleans up. Timeouts are module constants and keyword parameters, not CLI flags. [AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]
2. **`scripts/tests/test_app_verify.py`** — Story 3 classes (`TouchedTests`, `SafetyTests`, `PreLaunchProbeTests`, `RunTests`, `RunCliTests`): every run-time Error & Rescue Map row, free port per run, fixture-PID survival asserted after every launched run, SIGTERM-to-CLI cleanup. Also added `ProductAmendmentTests` for Story 1's AC-1.5, which `ac-trace` flagged `untested_criterion` once Story 1 read complete (eval `review-override` went red between the two stories; fixed here). [AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]

### Verification

- `uv run --python 3.9 pytest scripts/tests/test_app_verify.py` → 71 passed (68 at Gate 3 + 3 amendment tests); repeated runs stable; full `uv run pytest` → 2075 passed, 1 skipped; bash suite clean; `ps` shows no fixture process after the suite or the manual walk.
- Manual walk: pass → `app-verify: 1/1 pass — evidence/manual-pass/` (0); fail → `app-verify: 1/2 fail — broken (exit 1) — evidence/manual-fail/broken/` (1); safety → `app-verify: refused (APP_VERIFY_FIXTURE_DB matches a Never pattern)` (2, no `_launch/`); not-ready → `app-verify: fail (not_ready 2s) — evidence/manual-not-ready/_launch/` (1).
- Coverage of `scripts/app-verify.py`: 90% (coverage.py; `test-integrity.py coverage --report` pass); authenticity pass.
- Gates: arch-check pass; 0 boundary crossings → `evaluator-agent`; Gate 3 evaluator PASS with Medium drift (human-only features missing from full runs) — fixed in place along with two Minor findings (SIGTERM orphaning, artifact path confinement); drift-format pass; `eval.sh --check=review-override` and `--check=ac-trace` Findings 0.
- Drift: DEV-002..DEV-005, all Small after the fix.
- Iteration count: 1
