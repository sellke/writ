# Story 4: Bring Data Tools and Python Check Tools into Conformance

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 3

## User Story

**As a** agent running Writ commands in an installed project, and the Writ maintainer
**I want to** get one JSON document from every Python data script by default, and a verdict line first from every Python check script, in every mode
**So that** agents parse script output without guessing, and only the Story 5 entries (shell scripts and `app-verify.py`) remain in `KNOWN_VIOLATIONS`

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [ ] Given `scripts/revert-resolve.py` with no output flag, when it resolves a story in a fixture repo, then stdout is one JSON document equal to the object `--json` printed before this story, exit is 0, `--json` still exits 0 with the same document, and `--pretty` prints the former human summary `[AC-4.1]`
- [ ] Given a fixture knowledge ledger and the markdown report captured from the unmodified `scripts/knowledge-consolidate.py` before any change, when the script runs with `--pretty` in `--dry-run` and in `--apply` on a temp copy, then stdout is byte-identical to the capture for each mode, after replacing run-dependent values (dates, temp paths) with fixed placeholders on both sides; if the report has no such values, the comparison is raw `[AC-4.2]`
- [ ] Given `scripts/tests/test_agent_cli_contract.py`, when `uv run pytest scripts/tests/test_agent_cli_contract.py` runs, then the only `KNOWN_VIOLATIONS` entries left name `lint-skill.sh`, `gen-skill.sh`, `check-agent-parity.sh`, or `app-verify.py` (Story 5), and every Python script other than `app-verify.py` passes every rule in every mode the contract test exercises `[AC-4.3]`
- [ ] Given a grep for `revert-resolve.py` and `knowledge-consolidate.py` across `commands/` (including `*.lean.md`), `agents/`, `skills/`, `adapters/`, and `.writ/docs/`, when each hit is read, then no caller passes `--json` to `revert-resolve.py`, every caller that shows `knowledge-consolidate.py` output to a user passes `--pretty`, and every caller of a fixed script relies on its new default `[AC-4.4]`
- [ ] Given `.writ/docs/agent-cli-contract.md` `### Notes` and its State section, when a reader opens them after this story, then no note describes a Story 4 script's old output, and `roadmap-sync.py` and `goal-emit.py` write their files through a temp file and rename (a test asserts no partial file is left when the write is interrupted) `[AC-4.5]`

## Implementation Tasks

- [ ] 4.1 Write failing tests first. In `scripts/tests/test_revert_resolve.py`, add cases for JSON default, `--pretty` text, and `--json` as a no-op. Before editing `scripts/knowledge-consolidate.py`, capture its current markdown report for a fixture ledger into `scripts/tests/fixtures/`. Add `scripts/tests/test_knowledge_consolidate.py` (no test file exists today) that asserts `--pretty` matches that capture `[AC-4.1, AC-4.2]`
- [ ] 4.2 Fix `scripts/revert-resolve.py`: JSON default, `--pretty` calls `_render_human`, `--json` kept with `help=argparse.SUPPRESS` and no effect. Update the module docstring CLI block. Drop `--json` from `commands/revert.md` line 52. Remove the script's `KNOWN_VIOLATIONS` entries. Commit script, tests, caller, and delisting together `[AC-4.1, AC-4.4]`
- [ ] 4.3 Fix `scripts/knowledge-consolidate.py`: JSON default, `--pretty` calls `render_markdown`, `--json` kept as a no-op. Change `commands/knowledge.md` lines 74 and 92 to `--pretty`. Confirm `commands/retro.md` line 152 (`--json`) still works without an edit. Remove the script's `KNOWN_VIOLATIONS` entries. Commit as one unit `[AC-4.2, AC-4.4]`
- [ ] 4.4 Fix the remaining Python entries in `KNOWN_VIOLATIONS`, one script per commit with its callers, following each script's note in `.writ/docs/agent-cli-contract.md`: `change-surface.py`, `boundary-map.py` (`crossings` and the `compute` story-error blocker), `arch-lint.py` (exit 2 on `unverifiable`), `goal-emit.py` (summary last), `verdict-provenance.py` (verdict first), `review-panel.py` (`trial-init`/`trial-prepare`), `gen-codex-agent-tomls.py` (write mode), and `test-integrity.py` (replace the `while True` parent walk with a loop bounded by the filesystem root). Data tools get JSON default plus `--pretty` and a no-op `--json`; check tools get the verdict-line shape. `change-surface.py` and `boundary-map.py crossings` are read by `commands/implement-story.md` Gate 2.5 and its `.lean` twin, so update those callers in the same commit `[AC-4.3, AC-4.4]`
- [ ] 4.5 Make `roadmap-sync.py` and `goal-emit.py` write atomically (temp file in the same directory, then `os.replace`), with a test each. Delete or rewrite the contract doc's note for every script fixed in this story, and the State section's in-place-writer sentence `[AC-4.5]`
- [ ] 4.6 Verify the contract. Run the contract test with only Story 5 entries left in `KNOWN_VIOLATIONS`, then run the caller grep from AC-4.4 across every listed path, including `*.lean.md` `[AC-4.3, AC-4.4]`
- [ ] 4.7 Verify all tests pass. Run `uv run pytest`, `uv run --python 3.9 pytest`, the bash test loop from the project CLAUDE.md, and `bash scripts/eval.sh` outside the sandbox. Confirm `git status` shows no unrelated files staged `[AC-4.1, AC-4.2, AC-4.3, AC-4.5]`

## Notes

- **Scope split (2026-10-12).** The maintainer kept the check rule strict and split conformance in two. This story fixes the Python data tools and Python check tools. Story 5 fixes `lint-skill.sh`, `gen-skill.sh`, `check-agent-parity.sh`, and `app-verify.py`'s line-1 format, and closes the origin issue. Story 1's table (`.writ/docs/agent-cli-contract.md`) is the authority on each script's shape. If Story 3 records a Python entry not listed in task 4.4, fix it here too.
- **Preserve each script's JSON formatting.** `revert-resolve.py` indents JSON by 2. `knowledge-consolidate.py` `--json` prints compact JSON. Keep each as it is so existing eval checks and parsers see no change.
- **Golden capture comes first.** Task 4.1 must record the `knowledge-consolidate.py` markdown before any edit. Without that capture, AC-4.2 cannot be tested.
- **Installed-project window.** `--json` as a no-op protects callers that pass `--json`. It does not protect a caller that relies on the default text output. An installed project running old `commands/knowledge.md` against the new script gets JSON where it expected markdown. `update.sh` copies commands and scripts together, so the window exists only for an interrupted or partial update. Raise this with the maintainer before merge.
- **Lean twins.** Grep `commands/*.lean.md` along with the main files. None of the five existing lean twins reference either script today, but a later edit could add one.
- **Stage explicit paths only.** `.writ/specs/2026-10-12-agent-cli-contract/` is untracked. Do not stage it in a fix commit. Leave unrelated working-tree edits alone.
- **Integration.** Story 3 supplies the test file, the table parser, and `KNOWN_VIOLATIONS`. Story 1 supplies the classification table in `.writ/docs/agent-cli-contract.md`. Story 2 removes the six dev-only scripts from the shipped set, so they drop out of scope.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** spec.md → Business Rules (Expanded) 3 (data shape), 9 (caller updates travel with the change), 10 (`KNOWN_VIOLATIONS` is strict debt)
- **Technical spec:** technical-spec.md → Conformance Fixes (Story 4) for the five-step pattern and known callers; → Files in Scope, Story 4 rows
- **Error map rows:** technical-spec.md → Error & Rescue Map, "Default output change"
- **Experience:** spec.md → Experience Design → State Catalog, "Known violation fixed but still listed" (strict xfail) and "Conforming script, runtime failure" (failure shapes)
- **Technical concerns:** spec.md → Technical Concerns, first bullet (knowledge-consolidate markdown rendered to the user by `/knowledge`)
- **Contract:** `.writ/docs/agent-cli-contract.md` (Story 1), sections Data shape, Check shape, Classification
- **Issue template:** commands/create-issue.md → Step 5 template and "Closing an issue"
- **Consequences for the new improvement issue:** `.writ/decision-records/adr-029-agent-cli-contract.md`, consequences section
