# Story 5: Bring Shell Scripts and app-verify into Conformance

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** Story 4

## User Story

**As an** agent running Writ commands in an installed project, and the Writ maintainer
**I want to** get a verdict line first from the three shipped shell scripts and from `app-verify.py`, in every mode
**So that** every shipped script follows one contract, `KNOWN_VIOLATIONS` is empty, and the origin issue can close

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [x] Given `scripts/lint-skill.sh` and `scripts/gen-skill.sh` (`--check` and write mode), when each runs on a passing input, a failing input, and an unusable input, then stdout line 1 is `pass`, `fail`, or `unverifiable`, a summary line is last, and the exit code is 0 when the check ran (`pass` or `unverifiable`), 1 on `fail`, 2 on usage or could-not-start; `gen-skill.sh` no longer exits 3 for a missing `SKILL.md` `[AC-5.1]`
- [x] Given `scripts/check-agent-parity.sh`, when it runs on a tree with no drift and on one with drift, then line 1 is `pass` (exit 0) or `fail` (exit 1), each drift is a `reason:` line, and a summary is last; `commands/refresh-command.md` still treats parity drift as a warning that never blocks, by reading the verdict instead of relying on exit 0 `[AC-5.2]`
- [x] Given `scripts/app-verify.py` `validate`, `touched`, and `run`, when each runs, then stdout line 1 is the bare verdict, the `app-verify: …` summary is last, `touched` prints each matched feature as a `feature: <id>` line between them, `unverifiable` (no recipe, invalid recipe, refused) exits 0 instead of 2, and `--json` still prints one JSON object after the summary `[AC-5.3]`
- [x] Given every caller of the four scripts in `commands/` (including `*.lean.md`), `agents/`, `skills/`, `adapters/`, `codex/`, and `.writ/docs/`, when each is read after this story, then none relies on the old output (a bare ✅/❌ line, a diff without a verdict, exit 3, a summary on line 1, or bare feature IDs), and the regenerated `codex/agents/*.toml` match their `agents/*.md` sources `[AC-5.4]`
- [x] Given the finished spec, when `uv run pytest scripts/tests/test_agent_cli_contract.py` runs, then `KNOWN_VIOLATIONS` is `{}` and no `xfail` mark remains; `.writ/issues/features/2026-10-12-agent-facing-writ-cli.md` ends with a `## Resolution` section giving the date, what changed, and the spec path; and `.writ/issues/improvements/2026-10-12-script-install-location.md` exists in the `create-issue` template with `Type: Improvement` `[AC-5.5]`

## Implementation Tasks

- [x] 5.1 Write failing tests first: add `scripts/tests/test_shell_check_shape.sh` (no shell tests exist today for these three scripts) for line 1, last line, and exit codes on pass, fail, and unusable inputs; extend `scripts/tests/test_app_verify.py` for line-1 verdict, `feature:` lines, and the `--json` object `[AC-5.1, AC-5.2, AC-5.3]`
- [x] 5.2 Fix `lint-skill.sh` and `gen-skill.sh`: `--help` prints a `usage:` line naming the script; an unknown flag is a usage error (exit 2, usage on stderr); verdict first, per-file results as `reason:` lines, summary last, exit 0 ran / 1 fail / 2 usage or could-not-start (missing `SKILL.md` → `unverifiable`, exit 0). Update `commands/new-skill.md`, `commands/refresh-command.md`, `commands/update-writ.md`, and any `.writ/docs/` or `skills/` text that quotes the old output, in the same commit `[AC-5.1, AC-5.4]`
- [x] 5.3 Fix `check-agent-parity.sh`: `--help` prints a `usage:` line naming the script; any argument other than `--help` is a usage error (exit 2, usage on stderr); verdict first, `reason:` per drift, summary last, exit 1 on drift. Change `commands/refresh-command.md` (line ~431 and the table row "always exit 0") so a `fail` stays a warning `[AC-5.2, AC-5.4]`
- [x] 5.4 Fix `app-verify.py`: bare verdict on line 1, `feature: <id>` lines for `touched`, summary last, exit 0 on `unverifiable`. Update `commands/implement-story.md` Gate 4.5 (its exit-2 branch becomes "line 1 `unverifiable`"; Gate 2.5's `--surface <class>` says to pass the `class` value from `change-surface.py`'s JSON, keeping the file's byte pin balanced) and its `.lean` twin, `commands/create-uat-plan.md`, `agents/coding-agent.md`, `agents/visual-qa-agent.md`, `adapters/codex.md`, and `.writ/docs/app-verification-format.md`; regenerate `codex/agents/*.toml` with `python3 scripts/gen-codex-agent-tomls.py` `[AC-5.3, AC-5.4]`
- [x] 5.5 Fix `review-panel.py` `tally` (prints `block`) and `trial-report` (prints `keep`/`remove`): line 1 becomes `fail`/`pass`/`unverifiable` with the panel word on a `reason:` line, and Gate 3's review-panel paragraph in `implement-story.md` and its `.lean` twin reads the new line (a `fail` from `tally` is the Gate 3 FAIL `block` was). Add `SMOKE_INVOCATIONS` cases for each mode this story fixes that the contract test does not yet run (`app-verify.py touched`, `gen-skill.sh` write mode into a temp copy), so the fixes are enforced. Delete or rewrite the contract doc's notes for the four scripts, empty `KNOWN_VIOLATIONS`, and remove the xfail plumbing that becomes unused `[AC-5.5]`
- [x] 5.6 Write the `## Resolution` section on the origin issue and create `.writ/issues/improvements/2026-10-12-script-install-location.md` with the `create-issue` template: whether shipped scripts should move out of the project-root `scripts/` folder the way pstack keeps tools inside the skill folder (ADR-029 consequences) `[AC-5.5]`
- [x] 5.7 Verify all tests pass: the contract test with `KNOWN_VIOLATIONS == {}`, `uv run pytest`, `uv run --python 3.9 pytest`, the bash test loop, `bash scripts/gen-skill.sh --check`, `python3 scripts/gen-codex-agent-tomls.py --check`, and `bash scripts/eval.sh` outside the sandbox `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

## Notes

- **Origin.** Added 2026-10-12 when the maintainer kept the check-shape rule strict and split conformance work (drift-log DEV-001, DEV-002). Story 4 owns the Python data and check tools.
- **check-agent-parity exit code.** `/refresh-command` says parity drift warns and never blocks. Moving to exit 1 keeps the contract; the caller, not the script, decides that `fail` is a warning. Update the caller in the same commit.
- **app-verify callers are many.** Gate 4.5 reads the exit code and the `app-verify:` line, and treats "printed no IDs" as a skip. Every caller and the codex TOML copies must move together, or Gate 4.5 misreads `touched`.
- **eval.sh pins.** `eval.sh` may `require_literal` text from these commands or scripts. Run it after each commit and update pins in the same commit.
- **Installed-project window.** As in Story 4: `update.sh` copies commands and scripts together, so mismatched pairs exist only during an interrupted update.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** spec.md → Business Rules (Expanded) 4 (check shape), 5 (usage errors), 9 (caller updates travel with the change), 10 (`KNOWN_VIOLATIONS` is strict debt)
- **Contract:** `.writ/docs/agent-cli-contract.md` → Check shape, Classification, Notes for `app-verify.py`, `check-agent-parity.sh`, `gen-skill.sh`, `lint-skill.sh`
- **Drift:** drift-log.md → Story 1 DEV-001 and DEV-002
- **Error map rows:** technical-spec.md → Error & Rescue Map, "Default output change"
- **Issue template:** commands/create-issue.md → Step 5 template and "Closing an issue"
- **Consequences for the new improvement issue:** `.writ/decision-records/adr-029-agent-cli-contract.md`, consequences section

## What Was Built

**Implementation Date:** 2026-10-12

Commits: d29bf3d (AC-4.5 citation), f65d8f8 (lint-skill), d2d1dc1 (gen-skill), 2d3d730 (check-agent-parity), c336f9d (app-verify), d89438c (review-panel), 19a3ea9 (issues), 615865f (Gate 3 follow-ups).

### Files Created

1. **`scripts/tests/test_shell_check_shape.sh`** — 24 assertions: lint-skill and gen-skill on pass, fail, unusable, usage, and `--help`; gen-skill `--check`, write, `--dry-run`, invalid and missing manifest, missing and read-only SKILL.md; check-agent-parity on fixtures and on this repo (shape, not zero drift). [AC-5.1, AC-5.2]
2. **`.writ/issues/improvements/2026-10-12-script-install-location.md`** — whether shipped scripts should move out of project-root `scripts/`, as pstack keeps tools inside the skill folder. [AC-5.5]

### Files Modified

1. **`scripts/lint-skill.sh`** — verdict first, per-file `reason:` lines, `lint-skill:` summary last; missing file `unverifiable` (exit 0); `--help` and usage errors. Callers: `commands/new-skill.md`, `commands/refresh-command.md`. [AC-5.1, AC-5.4]
2. **`scripts/gen-skill.sh`** — every mode (`--check`, write, `--dry-run`) prints the check shape; drift and invalid manifest `fail`; missing manifest or SKILL.md `unverifiable` (no exit 3); write mode temp beside SKILL.md, mode kept, read-only SKILL.md `fail`. Callers: `commands/new-skill.md`, `.github/workflows/eval.yml` (line 1 must be `pass`), `scripts/eval.sh` (`--dry-run` line 1). [AC-5.1, AC-5.4]
3. **`scripts/check-agent-parity.sh`** — `--help`, usage errors, verdict first, `reason:` per drift, exit 1 on drift, `unverifiable` with no `agents/`. `commands/refresh-command.md` reads line 1 and keeps drift a warning; `adapters/codex.md`. [AC-5.2, AC-5.4]
4. **`scripts/app-verify.py`** — bare verdict on line 1, `feature: <id>` lines from `touched`, summary last, `unverifiable` exits 0, `--json` object after the summary. Callers: Gate 4.5 and Gate 2.5 (`--surface` takes the `class` value) in `commands/implement-story.md` and `.lean`, `commands/create-uat-plan.md`, `.writ/docs/app-verification-format.md`, `scripts/eval.sh`. [AC-5.3, AC-5.4]
5. **`scripts/review-panel.py`** — `tally` prints `fail` with `reason: block`; `trial-report` prints `pass` with `reason: keep`/`remove`. Gate 3 panel paragraph in both implement-story files reads `fail` as the Gate 3 FAIL. [AC-5.4]
6. **`scripts/tests/test_agent_cli_contract.py`** — `KNOWN_VIOLATIONS = {}`; smokes for `gen-skill.sh write`, `app-verify.py touched`, `review-panel.py tally`, `trial-report`; retired-phrase caller guard. [AC-5.4, AC-5.5]
7. **`.writ/docs/agent-cli-contract.md`** — Story 5 notes rewritten; Notes intro says every script conforms; `--json` placement rule. **`.writ/issues/features/2026-10-12-agent-facing-writ-cli.md`** — `## Resolution`. [AC-5.5]
8. `commands/implement-story.md` stays at its exact byte pin (36973 bytes) through small wording trims; `test_lean_commands.py` hashes repinned with dated comments.

### Verification

- After 615865f: `uv run --python 3.9 pytest -q` → 2614 passed, 2 skipped, 0 xfailed; bash loop → 0 failures; `bash scripts/eval.sh` → exit 0, Findings: 0. `gen-skill.sh --check`, `gen-codex-agent-tomls.py --check`, and `check-agent-parity.sh` print `pass`.
- Gate 0 arch-check pass. Gate 2.5: full-stack, route review-agent.
- Gate 3 review-agent: PASS, iteration 1. Minor findings fixed in 615865f. review-override: pass (Python tests); the shell test hits the known authenticity false positive (`.writ/issues/improvements/2026-10-12-test-integrity-shell-tests.md`).
- Gate 3.5 drift-format: pass. Drift: DEV-001 Small, DEV-002 Medium, DEV-003 Medium, DEV-004 Small, DEV-005 Small.
- Gate 4 test-integrity authenticity: pass (Python tests). Gate 4.5: app-verify `unverifiable` (no recipe), now exit 0. Gate 5: docs-check unverifiable.
- Iteration count: 1
