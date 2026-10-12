# Story 5: Bring Shell Scripts and app-verify into Conformance

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 4

## User Story

**As an** agent running Writ commands in an installed project, and the Writ maintainer
**I want to** get a verdict line first from the three shipped shell scripts and from `app-verify.py`, in every mode
**So that** every shipped script follows one contract, `KNOWN_VIOLATIONS` is empty, and the origin issue can close

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [ ] Given `scripts/lint-skill.sh` and `scripts/gen-skill.sh` (`--check` and write mode), when each runs on a passing input, a failing input, and an unusable input, then stdout line 1 is `pass`, `fail`, or `unverifiable`, a summary line is last, and the exit code is 0 when the check ran (`pass` or `unverifiable`), 1 on `fail`, 2 on usage or could-not-start; `gen-skill.sh` no longer exits 3 for a missing `SKILL.md` `[AC-5.1]`
- [ ] Given `scripts/check-agent-parity.sh`, when it runs on a tree with no drift and on one with drift, then line 1 is `pass` (exit 0) or `fail` (exit 1), each drift is a `reason:` line, and a summary is last; `commands/refresh-command.md` still treats parity drift as a warning that never blocks, by reading the verdict instead of relying on exit 0 `[AC-5.2]`
- [ ] Given `scripts/app-verify.py` `validate`, `touched`, and `run`, when each runs, then stdout line 1 is the bare verdict, the `app-verify: …` summary is last, `touched` prints each matched feature as a `feature: <id>` line between them, `unverifiable` (no recipe, invalid recipe, refused) exits 0 instead of 2, and `--json` still prints one JSON object after the summary `[AC-5.3]`
- [ ] Given every caller of the four scripts in `commands/` (including `*.lean.md`), `agents/`, `skills/`, `adapters/`, `codex/`, and `.writ/docs/`, when each is read after this story, then none relies on the old output (a bare ✅/❌ line, a diff without a verdict, exit 3, a summary on line 1, or bare feature IDs), and the regenerated `codex/agents/*.toml` match their `agents/*.md` sources `[AC-5.4]`
- [ ] Given the finished spec, when `uv run pytest scripts/tests/test_agent_cli_contract.py` runs, then `KNOWN_VIOLATIONS` is `{}` and no `xfail` mark remains; `.writ/issues/features/2026-10-12-agent-facing-writ-cli.md` ends with a `## Resolution` section giving the date, what changed, and the spec path; and `.writ/issues/improvements/2026-10-12-script-install-location.md` exists in the `create-issue` template with `Type: Improvement` `[AC-5.5]`

## Implementation Tasks

- [ ] 5.1 Write failing tests first: add `scripts/tests/test_shell_check_shape.sh` (no shell tests exist today for these three scripts) for line 1, last line, and exit codes on pass, fail, and unusable inputs; extend `scripts/tests/test_app_verify.py` for line-1 verdict, `feature:` lines, and the `--json` object `[AC-5.1, AC-5.2, AC-5.3]`
- [ ] 5.2 Fix `lint-skill.sh` and `gen-skill.sh`: `--help` prints a `usage:` line naming the script; an unknown flag is a usage error (exit 2, usage on stderr); verdict first, per-file results as `reason:` lines, summary last, exit 0 ran / 1 fail / 2 usage or could-not-start (missing `SKILL.md` → `unverifiable`, exit 0). Update `commands/new-skill.md`, `commands/refresh-command.md`, `commands/update-writ.md`, and any `.writ/docs/` or `skills/` text that quotes the old output, in the same commit `[AC-5.1, AC-5.4]`
- [ ] 5.3 Fix `check-agent-parity.sh`: `--help` prints a `usage:` line naming the script; any argument other than `--help` is a usage error (exit 2, usage on stderr); verdict first, `reason:` per drift, summary last, exit 1 on drift. Change `commands/refresh-command.md` (line ~431 and the table row "always exit 0") so a `fail` stays a warning `[AC-5.2, AC-5.4]`
- [ ] 5.4 Fix `app-verify.py`: bare verdict on line 1, `feature: <id>` lines for `touched`, summary last, exit 0 on `unverifiable`. Update `commands/implement-story.md` Gate 4.5 (its exit-2 branch becomes "line 1 `unverifiable`"; Gate 2.5's `--surface <class>` says to pass the `class` value from `change-surface.py`'s JSON, keeping the file's byte pin balanced) and its `.lean` twin, `commands/create-uat-plan.md`, `agents/coding-agent.md`, `agents/visual-qa-agent.md`, `adapters/codex.md`, and `.writ/docs/app-verification-format.md`; regenerate `codex/agents/*.toml` with `python3 scripts/gen-codex-agent-tomls.py` `[AC-5.3, AC-5.4]`
- [ ] 5.5 Fix `review-panel.py` `tally` (prints `block`) and `trial-report` (prints `keep`/`remove`): line 1 becomes `fail`/`pass`/`unverifiable` with the panel word on a `reason:` line, and Gate 3's review-panel paragraph in `implement-story.md` and its `.lean` twin reads the new line (a `fail` from `tally` is the Gate 3 FAIL `block` was). Add `SMOKE_INVOCATIONS` cases for each mode this story fixes that the contract test does not yet run (`app-verify.py touched`, `gen-skill.sh` write mode into a temp copy), so the fixes are enforced. Delete or rewrite the contract doc's notes for the four scripts, empty `KNOWN_VIOLATIONS`, and remove the xfail plumbing that becomes unused `[AC-5.5]`
- [ ] 5.6 Write the `## Resolution` section on the origin issue and create `.writ/issues/improvements/2026-10-12-script-install-location.md` with the `create-issue` template: whether shipped scripts should move out of the project-root `scripts/` folder the way pstack keeps tools inside the skill folder (ADR-029 consequences) `[AC-5.5]`
- [ ] 5.7 Verify all tests pass: the contract test with `KNOWN_VIOLATIONS == {}`, `uv run pytest`, `uv run --python 3.9 pytest`, the bash test loop, `bash scripts/gen-skill.sh --check`, `python3 scripts/gen-codex-agent-tomls.py --check`, and `bash scripts/eval.sh` outside the sandbox `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

## Notes

- **Origin.** Added 2026-10-12 when the maintainer kept the check-shape rule strict and split conformance work (drift-log DEV-001, DEV-002). Story 4 owns the Python data and check tools.
- **check-agent-parity exit code.** `/refresh-command` says parity drift warns and never blocks. Moving to exit 1 keeps the contract; the caller, not the script, decides that `fail` is a warning. Update the caller in the same commit.
- **app-verify callers are many.** Gate 4.5 reads the exit code and the `app-verify:` line, and treats "printed no IDs" as a skip. Every caller and the codex TOML copies must move together, or Gate 4.5 misreads `touched`.
- **eval.sh pins.** `eval.sh` may `require_literal` text from these commands or scripts. Run it after each commit and update pins in the same commit.
- **Installed-project window.** As in Story 4: `update.sh` copies commands and scripts together, so mismatched pairs exist only during an interrupted update.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** spec.md → Business Rules (Expanded) 4 (check shape), 5 (usage errors), 9 (caller updates travel with the change), 10 (`KNOWN_VIOLATIONS` is strict debt)
- **Contract:** `.writ/docs/agent-cli-contract.md` → Check shape, Classification, Notes for `app-verify.py`, `check-agent-parity.sh`, `gen-skill.sh`, `lint-skill.sh`
- **Drift:** drift-log.md → Story 1 DEV-001 and DEV-002
- **Error map rows:** technical-spec.md → Error & Rescue Map, "Default output change"
- **Issue template:** commands/create-issue.md → Step 5 template and "Closing an issue"
- **Consequences for the new improvement issue:** `.writ/decision-records/adr-029-agent-cli-contract.md`, consequences section
