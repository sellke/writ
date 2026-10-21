# Story 1: CI Runs Every Suite

> **Status:** Completed ✅
> **Commit:** 0eb7561b6bdc39b462b7f75908fca93f2ff449fc
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer or contributor opening a PR
**I want to** have CI run pytest on the Python 3.9 floor and every bash test alongside `eval.sh` and the SKILL.md check
**So that** a red suite fails the PR instead of surfacing only when someone runs it locally

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.4

- [x] Given `.github/workflows/eval.yml`, when it is read, then it still triggers on `pull_request` and `push`, still runs `bash scripts/gen-skill.sh --check` and `bash scripts/eval.sh` as before, installs uv with an `astral-sh/setup-uv` step pinned to a major version tag, and runs `uv run --python 3.9 pytest` as its own step `[AC-1.1]`
- [x] Given the workflow's bash-tests step and a temp directory holding one passing and one failing `scripts/tests/test_*.sh`, when the step's `run:` block is executed with `bash -e`, then both tests run, the output contains `FAIL scripts/tests/test_fail.sh`, and the block exits non-zero; with only passing tests it exits 0 `[AC-1.2]`
- [x] Given the bash tests and the scripts they run, when the story picks a runner OS, then the choice (`ubuntu-latest` unless a suite needs BSD userland) is backed by a scan for BSD-only calls and a Linux run of the bash tests, and the evidence is recorded in a comment in `eval.yml` and in this story's What Was Built `[AC-1.3]`
- [x] Given the finished workflow and the working tree, when `uv run --python 3.9 pytest`, the bash-test loop, and `bash scripts/eval.sh` run locally, then all three pass, and `scripts/tests/test_ci_workflow.py` passes on Python 3.9 `[AC-1.4]`

## Implementation Tasks

- [x] 1.1 Write failing tests in a new `scripts/tests/test_ci_workflow.py` (Python 3.9 stdlib only, no YAML parser): trigger, kept steps, setup-uv pin, the pytest command, the bash step's glob, and execution of the extracted bash `run:` block against pass and fail fixtures in `tmp_path`. Run it and confirm it fails on today's `eval.yml` `[AC-1.1, AC-1.2]`
- [x] 1.2 Scan `scripts/tests/*.sh` and every script they invoke (`install.sh`, `update.sh`, `unlink.sh`, `eval.sh`, `gen-skill.sh`, `lint-skill.sh`, `check-agent-parity.sh`, and others they call) for BSD-only calls. Run the bash tests on Linux, in a container if one is available, otherwise in the first CI run of a branch push the maintainer approves. Record the commands and results `[AC-1.3]`
- [x] 1.3 Edit `.github/workflows/eval.yml`: add the `astral-sh/setup-uv` step (look up the current major tag), the `uv run --python 3.9 pytest` step, and the bash-tests step that counts failures and exits non-zero when any test fails. Keep the checkout, SKILL.md check, eval, and upload steps unchanged `[AC-1.1, AC-1.2]`
- [x] 1.4 Set the runner per task 1.2's evidence. Default to `ubuntu-latest`; move only a suite that needs BSD userland into a `macos-latest` job. Add a comment above `runs-on` naming the evidence `[AC-1.3]`
- [x] 1.5 Verify the workflow tests: `uv run --python 3.9 pytest scripts/tests/test_ci_workflow.py` passes, and a manual run of the extracted bash block against the fixtures matches AC-1.2 `[AC-1.1, AC-1.2]`
- [x] 1.6 Verify the full suites locally: `uv run --python 3.9 pytest`, then `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` (no `FAIL` lines), then `bash scripts/eval.sh` outside any sandbox; all pass `[AC-1.4]`

## Notes

- **The documented loop never fails.** `CLAUDE.md`'s `bash "$t" || echo "FAIL $t"` exits 0 when a test fails. The CI step must count failures and end with a non-zero exit. AC-1.2 tests exactly this.
- **Default shell.** Without `shell: bash`, Actions runs `run:` blocks on Linux as `bash -e {0}` (no `pipefail`). Execute the extracted block the same way in the test.
- **Grounding evidence (2026-10-20).** A grep for `stat -f`, `date -r`, `sed -i ''`, `readlink -f`, `grep -P`, `md5`, `gdate`, `gsed`, `mktemp -t` in `scripts/tests/*.sh` and the lifecycle scripts found nothing. `eval.sh` already runs on `ubuntu-latest`. Locally, 35 bash tests passed in about 106 s. Confirm all of this. Do not rely on it.
- **Run every suite.** `if: ${{ !cancelled() }}` on the later suite steps lets one run report every red suite. It is recommended, not required.
- **Bash tests run install and update in temp directories.** Never run `install.sh` or `update.sh` against the Writ repo. It is symlinked into `.claude/` and `.cursor/`. The bash tests and `eval.sh` do `git init` in temp dirs, so run them outside any sandbox.
- **Python 3.9 managed by uv.** If uv cannot provide 3.9 on the runner, the step fails red. Switch to `actions/setup-python` only with that failure as evidence.
- **Citations.** Name this spec (`2026-10-20-ci-and-update-integrity`) in the module docstring that carries the `AC-1.n` tokens (`.writ/docs/acceptance-criteria-ids.md` → Scan Bounds).
- **Independence.** Stories 2 to 5 add new `scripts/tests/test_*.sh` files. The glob picks them up with no workflow change. They also lengthen the bash step, which ran about 106 s locally before this spec.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated
- [ ] The first CI run on the phase PR shows each suite step green

## Context for Agents

- **Error map rows:** [CI bash step, CI pytest step, CI runner] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [CI run] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Rule 9 (CI fails on any red suite; count failures), Rule 10 (Python 3.9 via uv, pinned setup-uv), Rule 11 (temp dirs only)] — spec.md → ## Business Rules (Expanded)
- **Experience:** [State Catalog rows "PR, one suite red" and "PR, several bash tests red"] — spec.md → ## Experience Design → ### State Catalog
- **Technical:** technical-spec.md → ## Current State → ### CI and ## Story 1 Design: CI

---

## What Was Built

**Implementation Date:** 2026-10-20

### Files Created

1. **`scripts/tests/test_ci_workflow.py`** (9 tests, stdlib only) — reads `eval.yml` as text. Checks the triggers, the kept steps, the `astral-sh/setup-uv@v<N>` pin and its order before pytest, and the `uv run --python 3.9 pytest` step. Extracts the bash step's `run:` block and runs it with `bash -e` against pass, fail, two-fail, and empty fixtures in `tmp_path`. [AC-1.1, AC-1.2]

### Files Modified

- **`.github/workflows/eval.yml`** — added `astral-sh/setup-uv@v7`, a `uv run --python 3.9 pytest` step, and a bash-tests step that skips an unmatched glob, prints `FAIL <path>` per failure, prints `bash tests failed: N`, and ends with `[ "$fails" -eq 0 ]`. All three new steps use `if: ${{ !cancelled() }}`. A comment above `runs-on` records the runner evidence. Checkout, the SKILL.md check, eval, and the upload step are unchanged. [AC-1.1, AC-1.2, AC-1.3]

### Implementation Decisions

1. **`setup-uv@v7`** — `git ls-remote --tags https://github.com/astral-sh/setup-uv` lists bare major tags `v1` to `v7` only. v8.0.0 to v10.3.0 exist as full version tags, so `@v10` would not resolve. v7 is the newest tag that meets "pinned to a major version tag".
2. **Runner: `ubuntu-latest`** — the evidence below shows no suite needs BSD userland. No macOS job was added.
3. **Glob guard** — `[ -f "$t" ] || continue` keeps an empty test folder at exit 0, per the "CI run" shadow path (DEV-001).

### Test Results

**Verification:** test-first, then full suites.

- Pre-fix: `uv run --python 3.9 pytest scripts/tests/test_ci_workflow.py` against the unchanged `eval.yml` → `7 failed, 2 passed`. The orchestrator re-proved this in a `git archive 953f47e` extract: `7 failed, 2 passed in 0.06s`. The 2 that pass check the trigger and kept steps, which held before the change.
- After: `9 passed in 0.06s` on Python 3.9.
- Mutation runs (coding agent): the `CLAUDE.md` loop (`|| echo "FAIL $t"`) fails 3 of 4 block tests; dropping the guard fails the empty-folder test; stopping at the first failure fails 2 of 4.
- BSD scan (AC-1.3): `grep -nE "stat -f|date -r|sed -i ''|sed -i \"\"|readlink -f|grep -P|(^|[^a-z_])md5( |$)|gdate|gsed|pbcopy|sw_vers|xcrun|mktemp -t" scripts/tests/*.sh scripts/*.sh` → no matches. A second pattern set (`date -j`, `date -v`, `base64 -D`, `stat -x`, `find -E`, `xargs -J`, `sed -i`, `pbpaste`, `defaults read|write`, `sysctl`, `open -a`) and the same patterns as subprocess arguments in `scripts/*.py` and `scripts/tests/*.py` → no matches. `hash_file` falls back from `shasum` to `sha256sum`; tests that commit set their own git identity.
- Linux run (AC-1.3): `ubuntu:24.04` container (aarch64; bash 5.2.21, git 2.43.0, Python 3.12.3), non-root user, no git identity, source copied to a writable dir. The bash-tests block extracted from `eval.yml` ran with `bash -e`: exit 0, 35 tests, `bash tests failed: 0`. `gen-skill.sh --check` → `pass`; `eval.sh` → exit 0; `python3 -m pytest` → `2623 passed, 2 skipped`.
- Full suites on macOS (orchestrator run, AC-1.4): `uv run --python 3.9 pytest` → `2623 passed, 2 skipped in 154.90s`; bash loop → 35 run, 0 failed; `bash scripts/eval.sh` → exit 0, `Findings: 0`, `Run errors: 0`.
- Not yet run: pytest with uv-managed Python 3.9 on an x86_64 GitHub runner. That is the first CI run, pending the phase orchestrator's push.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-001)
- **Security:** No risk found. The trigger is `pull_request`, not `pull_request_target`, and the job uses no secrets.
- **Boundary Compliance:** 0 crossings; route evaluator-agent.
- Gate 0 arch-check: pass. Gate 2: no linter or build configured (build-smoke unverifiable, unsupported stack). Gate 2.5: cross-component. Review panel: skipped (platform cannot spawn other vendors). review-override: unverifiable (no coverage report). Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable (no report). Gate 4 authenticity: `test_imports_no_source`, the known checker false positive for tests that read a file rather than import a module (open issue `.writ/issues/improvements/2026-09-03-test-integrity-authenticity-flags-every-bash-test.md`); carried on the pre-fix and mutation evidence above, not DEGRADED. Gate 4.5: app-verify unverifiable (no recipe). Gate 5: docs-check unverifiable (no public exports).
- Evaluator residual (Minor, taste): `@v7` is frozen at v7.6.0; moving to a newer major needs a full-version pin, which the AC wording rules out. The unchanged upload step also fires when pytest or the bash tests fail.

### Deviations from Spec

- **[DEV-001] Bash step skips an unmatched glob** — Severity: Small
  - Spec said: the technical-spec sketch has no guard; the "CI run" shadow path says no `test_*.sh` means zero tests and exit 0.
  - Reality: the step skips an unmatched glob, so an empty folder exits 0.
  - Resolution: auto-amended.
  - Spec amendment: spec-lite.md S1 line.
