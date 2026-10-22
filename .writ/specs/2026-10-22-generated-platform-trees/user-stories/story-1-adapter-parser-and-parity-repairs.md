# Story 1: Adapter Table Parser and Parity Repairs

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer who edits adapter tool-table rows, and an agent on any platform that needs `Plan Mode` mapped
**I want to** parse the four adapter tool tables strictly, fail on a malformed row or a missing capability, and give every neutral name and `Plan Mode` a row in all four adapters
**So that** a table edit cannot silently drop a capability, and the generated capability maps in Stories 2 to 5 come from source instead of hand-kept copies

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given the four adapters in their repaired state, when `parse_adapter` runs on each and `vocabulary` combines the results, then all four parse, the neutral set equals {Task, AskQuestion, codebase_search, file_search, todo_write, read_file, run_terminal_cmd, list_dir, canvas-preview, Plan Mode}, the `Task` variants share one name, and `vendor_only` contains `EnterPlanMode` but not `Read`, `Write`, or `Bash` `[AC-1.1]`
- [ ] Given a fixture adapter whose tool table has a row with the wrong cell count, a row with an empty first cell, or a header with no body rows, when `parse_adapter` runs, then the verdict is `fail` with `reason: malformed adapters/<x>.md:<line>` (the 1-based line of the bad row), or `reason: empty adapters/<x>.md` for the header-only table `[AC-1.2]`
- [ ] Given a fixture adapter with no tool-table heading, when `parse_adapter` runs, then the verdict is `unverifiable` with `reason: section <heading> in adapters/<x>.md`, and the call returns without raising `[AC-1.3]`
- [ ] Given a fixture adapter set in which `codex.md` has no `file_search` row, when the unmapped check runs, then the verdict is `fail` with `reason: unmapped file_search in adapters/codex.md` `[AC-1.4]`
- [ ] Given the repaired tables, the three command files, and the Plan Mode issue, when each is read, then every tool table has a `Plan Mode` row whose mapping and notes text matches technical-spec.md → ## Plan Mode Rows; `adapters/codex.md` has a `file_search` row; `adapters/openclaw.md` has a `Task({ readonly: true })` row and no `readonly: true` row; create-spec Step 1.3, plan-product Step 1.2, and new-command Step 1.2 each point at the adapter's `Plan Mode` row; the issue has a `## Resolution` and a set `spec_ref`; and `test_adapter_canvas_row` passes `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write the failing tests first in `scripts/tests/test_gen_platform_trees.py` (Python 3.9 stdlib, pytest): `test_parse_real_adapters` (golden neutral set; `EnterPlanMode` in `vendor_only`; no `Read`, `Write`, or `Bash` there), `test_malformed_row` parametrized over wrong cell count, empty first cell, and header-only table, `test_missing_section`, and `test_parity`. Run the file and confirm all four fail for the expected reason (missing module, missing fixture, golden mismatch), not a syntax error `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.2 Create fixtures under `scripts/tests/fixtures/platform-trees/`, one subdirectory per case. Name each fixture file after its adapter (`codex.md`, `cursor.md`, and so on) so `parse_adapter` selects the right heading. Cases: a two-cell body row; an empty first cell; a header with no body rows; the tool-table heading removed; and a parity gap, a minimal codex-style table that lists every neutral name except `file_search` `[AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.3 Implement `parse_adapter(path) -> AdapterTable` in `scripts/gen-platform-trees.py` per technical-spec.md → ## Adapter Table Grammar. Find the adapter's heading, take the first table under it, and keep each row's name, variant text, mapping, notes, and 1-based line. Return `fail` for a malformed row or an empty table, `unverifiable` for a missing heading, and never raise on bad input. Apply the cursor column rule in Notes `[AC-1.1, AC-1.2, AC-1.3]`
- [ ] 1.4 Implement `vocabulary(adapters) -> (neutral, vendor_only)` per technical-spec.md → ## Vocabulary Rule, with `ALLOWLIST = {"Read", "Write", "Bash"}` and one comment per entry. Implement the unmapped check from spec.md → ## Business Rules (Expanded) Rule 3: each neutral name missing from an adapter yields `reason: unmapped <name> in adapters/<x>.md` with verdict `fail` `[AC-1.1, AC-1.4]`
- [ ] 1.5 Repair the tables. In `adapters/codex.md`, add a `file_search` row to the `### Quick reference — orchestration primitives` table. In `adapters/openclaw.md`, replace the `readonly: true` row with a `Task({ readonly: true })` row that keeps the same mapping and notes. In all four tool tables, append a `Plan Mode` row as the last row, using the Plan Mode Rows mapping and notes text. In the cursor table, put `create-spec, plan-product, new-command` in column 2 and the mapping sentence followed by the degradation sentence in column 3. Run `test_adapter_canvas_row` after the edit `[AC-1.1, AC-1.5]`
- [ ] 1.6 Make the command and issue edits. In `commands/create-spec.md`, § Step 1.3 (Discovery Conversation), replace the first sentence with the wording in technical-spec.md → ## Plan Mode Rows. In `commands/plan-product.md` § Step 1.2 and `commands/new-command.md` § Step 1.2, add "through the adapter's `Plan Mode` row" to the sentence that switches to Plan Mode. Append `## Resolution` to `.writ/issues/improvements/2026-10-22-create-spec-discovery-skips-plan-mode-on-claude-code.md`, naming this spec and the decision (the agent enters Plan Mode: `EnterPlanMode` on Claude Code, a question to the user on Cursor, a read-only conversation on Codex and OpenClaw), and set `spec_ref`. `git diff` each command file and confirm one sentence changed `[AC-1.5]`
- [ ] 1.7 Verify: `uv run --python 3.9 pytest`, the bash loop (`for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`), and `bash scripts/eval.sh` run outside the sandbox. All pass, with 0 findings from eval. Record the counts in What Was Built `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

- **Name normalization.** Strip backticks from column 1. Take the leading run of `[A-Za-z_][A-Za-z0-9_ -]*`, stopping at `(` or `{`, then rstrip. `Plan Mode` and `canvas-preview` keep their inner space or hyphen. Source: technical-spec.md → ## Adapter Table Grammar.
- **`readonly: true` is not a name.** The name rule stops at `:`, so the openclaw row would yield the neutral name `readonly`. The fold in task 1.5 removes it. The golden set has no `readonly`.
- **`Task` variants.** `Task({ prompt })`, `Task({ readonly: true })`, `Task({ resume: id })`, and `Task({ prompt, readonly })` share the name `Task`. Keep each variant's text on its row. Story 2 renders variants as sub-rows. Parity counts the base name only.
- **Cursor column mapping (decision to record).** The cursor header is `Tool | Used By | Purpose`. `Used By` holds command lists such as `Most commands`, so it is not a mapping. The spec, technical spec, and spec-lite all say (aligned 2026-10-22): column 1 is the name, column 3 (Purpose) is the mapping and notes. That matches the cursor Plan Mode row, which carries the Ask-the-user sentence in column 3.
- **Over-strict parsing risk.** The cursor table has three columns like the others, but its column 2 is prose. Do not reject a row because column 2 is not a mapping.
- **Verification-record tables are not tool tables.** The `#### Verification record` headings in `adapters/cursor.md` sit under `## Agent Configuration Notes`, outside the tool section. The parser reads only the first table under each grammar heading and ends the section at the next heading of the same or higher level. Do not parse, edit, or reformat these tables.
- **Table repairs only.** Edit the four tool tables and the three command sentences. Do not touch the `## Command Workflow Integrity` prose in `adapters/cursor.md` and `adapters/codex.md`, the `canvas-preview` rows, or any verification-record table. Prose outside tool tables is out of scope.
- **Rendering-rows ordering.** `2026-10-22-rendering-delegation-rows` owns the canvas rows and verification records. Confirm its changes are in `adapters/` before task 1.5. Read them; do not rewrite them.
- **Canvas test.** `scripts/tests/test_platform_neutral_names.py::test_adapter_canvas_row` pins the canvas rows. Run it after each table edit. A red run means a repair touched a canvas row.
- **TodoWrite is not in the tree yet.** `2026-10-22-front-door` adds a `TodoWrite` mapping to the Claude Code `todo_write` row. As of 2026-10-22, no `adapters/*.md` file contains `TodoWrite`. Do not assert it in Story 1 tests. Once it lands, it is a vendor-only name in a mapping cell, which is correct.
- **`vendor_only` is broad.** It holds every backticked identifier in a mapping cell that is neither neutral nor allowlisted, for example `EnterPlanMode`, `ExitPlanMode`, `Grep`, `Glob`, and `sandbox_mode`. Story 4 intersects this set with shipped text. Story 1 only computes it.
- **Command sentences.** For create-spec Step 1.3, use the wording in technical-spec.md → ## Plan Mode Rows. For plan-product Step 1.2 and new-command Step 1.2, add the phrase to the existing sentence. Check with `git diff` that each command file changes by one sentence.
- **Check shape.** Parse and unmapped results carry a verdict (`pass`, `fail`, `unverifiable`) and reason strings in the formats above. Story 4 prints them using the output contract in the `scripts/gen-claude-agents.py` docstring: verdict line, `reason:` lines, summary line.
- **Python 3.9.** Start modules with `from __future__ import annotations`. Avoid `X | Y` unions, `match`, and other 3.10+ syntax. Run tests with `uv run --python 3.9 pytest`.
- **Test docstring.** Cite AC-1.1 through AC-1.5 in the test module docstring, following `.writ/docs/acceptance-criteria-ids.md`.
- **Golden set.** Expected neutral set after repairs: {Task, AskQuestion, codebase_search, file_search, todo_write, read_file, run_terminal_cmd, list_dir, canvas-preview, Plan Mode}. Source: technical-spec.md → ## Vocabulary Rule.
- **Issue spec_ref.** Point `spec_ref` at `.writ/specs/2026-10-22-generated-platform-trees/spec.md`, in the format the issue template uses.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Nil input, Empty input)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 2 Adapter parsing; Rule 3 Vocabulary and parity; Rule 4 Vendor-only names; Rule 9 Plan Mode rows; Rule 10 Command sentences; Rule 15 Runtime)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Malformed table row (wrong column count, empty first cell); Adapter section heading missing; Capability used in a command with no row in one adapter; `/create-spec` discovery on Claude Code)
