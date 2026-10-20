# Story 1: CI Runs Every Suite

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer or contributor opening a PR
**I want to** have CI run pytest on the Python 3.9 floor and every bash test alongside `eval.sh` and the SKILL.md check
**So that** a red suite fails the PR instead of surfacing only when someone runs it locally

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.4

- [ ] Given `.github/workflows/eval.yml`, when it is read, then it still triggers on `pull_request` and `push`, still runs `bash scripts/gen-skill.sh --check` and `bash scripts/eval.sh` as before, installs uv with an `astral-sh/setup-uv` step pinned to a major version tag, and runs `uv run --python 3.9 pytest` as its own step `[AC-1.1]`
- [ ] Given the workflow's bash-tests step and a temp directory holding one passing and one failing `scripts/tests/test_*.sh`, when the step's `run:` block is executed with `bash -e`, then both tests run, the output contains `FAIL scripts/tests/test_fail.sh`, and the block exits non-zero; with only passing tests it exits 0 `[AC-1.2]`
- [ ] Given the bash tests and the scripts they run, when the story picks a runner OS, then the choice (`ubuntu-latest` unless a suite needs BSD userland) is backed by a scan for BSD-only calls and a Linux run of the bash tests, and the evidence is recorded in a comment in `eval.yml` and in this story's What Was Built `[AC-1.3]`
- [ ] Given the finished workflow and the working tree, when `uv run --python 3.9 pytest`, the bash-test loop, and `bash scripts/eval.sh` run locally, then all three pass, and `scripts/tests/test_ci_workflow.py` passes on Python 3.9 `[AC-1.4]`

## Implementation Tasks

- [ ] 1.1 Write failing tests in a new `scripts/tests/test_ci_workflow.py` (Python 3.9 stdlib only, no YAML parser): trigger, kept steps, setup-uv pin, the pytest command, the bash step's glob, and execution of the extracted bash `run:` block against pass and fail fixtures in `tmp_path`. Run it and confirm it fails on today's `eval.yml` `[AC-1.1, AC-1.2]`
- [ ] 1.2 Scan `scripts/tests/*.sh` and every script they invoke (`install.sh`, `update.sh`, `unlink.sh`, `eval.sh`, `gen-skill.sh`, `lint-skill.sh`, `check-agent-parity.sh`, and others they call) for BSD-only calls. Run the bash tests on Linux, in a container if one is available, otherwise in the first CI run of a branch push the maintainer approves. Record the commands and results `[AC-1.3]`
- [ ] 1.3 Edit `.github/workflows/eval.yml`: add the `astral-sh/setup-uv` step (look up the current major tag), the `uv run --python 3.9 pytest` step, and the bash-tests step that counts failures and exits non-zero when any test fails. Keep the checkout, SKILL.md check, eval, and upload steps unchanged `[AC-1.1, AC-1.2]`
- [ ] 1.4 Set the runner per task 1.2's evidence. Default to `ubuntu-latest`; move only a suite that needs BSD userland into a `macos-latest` job. Add a comment above `runs-on` naming the evidence `[AC-1.3]`
- [ ] 1.5 Verify the workflow tests: `uv run --python 3.9 pytest scripts/tests/test_ci_workflow.py` passes, and a manual run of the extracted bash block against the fixtures matches AC-1.2 `[AC-1.1, AC-1.2]`
- [ ] 1.6 Verify the full suites locally: `uv run --python 3.9 pytest`, then `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` (no `FAIL` lines), then `bash scripts/eval.sh` outside any sandbox; all pass `[AC-1.4]`

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

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] The first CI run on the phase PR shows each suite step green

## Context for Agents

- **Error map rows:** [CI bash step, CI pytest step, CI runner] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [CI run] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Rule 9 (CI fails on any red suite; count failures), Rule 10 (Python 3.9 via uv, pinned setup-uv), Rule 11 (temp dirs only)] — spec.md → ## Business Rules (Expanded)
- **Experience:** [State Catalog rows "PR, one suite red" and "PR, several bash tests red"] — spec.md → ## Experience Design → ### State Catalog
- **Technical:** technical-spec.md → ## Current State → ### CI and ## Story 1 Design: CI
