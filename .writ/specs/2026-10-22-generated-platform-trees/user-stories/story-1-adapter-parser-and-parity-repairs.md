# Story 1: Adapter Table Parser and Parity Repairs

> **Status:** Completed ✅ (2026-10-22)
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer who edits adapter tool-table rows, and an agent on any platform that needs `Plan Mode` mapped
**I want to** parse the four adapter tool tables strictly, fail on a malformed row or a missing capability, and give every neutral name and `Plan Mode` a row in all four adapters
**So that** a table edit cannot silently drop a capability, and the generated capability maps in Stories 2 to 5 come from source instead of hand-kept copies

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given the four adapters in their repaired state, when `parse_adapter` runs on each and `vocabulary` combines the results, then all four parse, the neutral set equals {Task, AskQuestion, codebase_search, file_search, todo_write, read_file, run_terminal_cmd, list_dir, canvas-preview, Plan Mode}, the `Task` variants share one name, and `vendor_only` contains `EnterPlanMode` but not `Read`, `Write`, or `Bash` `[AC-1.1]`
- [x] Given a fixture adapter whose tool table has a row with the wrong cell count, a row with an empty first cell, or a header with no body rows, when `parse_adapter` runs, then the verdict is `fail` with `reason: malformed adapters/<x>.md:<line>` (the 1-based line of the bad row), or `reason: empty adapters/<x>.md` for the header-only table `[AC-1.2]`
- [x] Given a fixture adapter with no tool-table heading, when `parse_adapter` runs, then the verdict is `unverifiable` with `reason: section <heading> in adapters/<x>.md`, and the call returns without raising `[AC-1.3]`
- [x] Given a fixture adapter set in which `codex.md` has no `file_search` row, when the unmapped check runs, then the verdict is `fail` with `reason: unmapped file_search in adapters/codex.md` `[AC-1.4]`
- [x] Given the repaired tables, the three command files, and the Plan Mode issue, when each is read, then every tool table has a `Plan Mode` row whose mapping and notes text matches technical-spec.md → ## Plan Mode Rows; `adapters/codex.md` has a `file_search` row; `adapters/openclaw.md` has a `Task({ readonly: true })` row and no `readonly: true` row; create-spec Step 1.3, plan-product Step 1.2, and new-command Step 1.2 each point at the adapter's `Plan Mode` row; the issue has a `## Resolution` and a set `spec_ref`; and `test_adapter_canvas_row` passes `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write the failing tests first in `scripts/tests/test_gen_platform_trees.py` (Python 3.9 stdlib, pytest): `test_parse_real_adapters` (golden neutral set; `EnterPlanMode` in `vendor_only`; no `Read`, `Write`, or `Bash` there), `test_malformed_row` parametrized over wrong cell count, empty first cell, and header-only table, `test_missing_section`, and `test_parity`. Run the file and confirm all four fail for the expected reason (missing module, missing fixture, golden mismatch), not a syntax error `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.2 Create fixtures under `scripts/tests/fixtures/platform-trees/`, one subdirectory per case. Name each fixture file after its adapter (`codex.md`, `cursor.md`, and so on) so `parse_adapter` selects the right heading. Cases: a two-cell body row; an empty first cell; a header with no body rows; the tool-table heading removed; and a parity gap, a minimal codex-style table that lists every neutral name except `file_search` `[AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.3 Implement `parse_adapter(path) -> AdapterTable` in `scripts/gen-platform-trees.py` per technical-spec.md → ## Adapter Table Grammar. Find the adapter's heading, take the first table under it, and keep each row's name, variant text, mapping, notes, and 1-based line. Return `fail` for a malformed row or an empty table, `unverifiable` for a missing heading, and never raise on bad input. Apply the cursor column rule in Notes `[AC-1.1, AC-1.2, AC-1.3]`
- [x] 1.4 Implement `vocabulary(adapters) -> (neutral, vendor_only)` per technical-spec.md → ## Vocabulary Rule, with `ALLOWLIST = {"Read", "Write", "Bash"}` and one comment per entry. Implement the unmapped check from spec.md → ## Business Rules (Expanded) Rule 3: each neutral name missing from an adapter yields `reason: unmapped <name> in adapters/<x>.md` with verdict `fail` `[AC-1.1, AC-1.4]`
- [x] 1.5 Repair the tables. In `adapters/codex.md`, add a `file_search` row to the `### Quick reference — orchestration primitives` table. In `adapters/openclaw.md`, replace the `readonly: true` row with a `Task({ readonly: true })` row that keeps the same mapping and notes. In all four tool tables, append a `Plan Mode` row as the last row, using the Plan Mode Rows mapping and notes text. In the cursor table, put `create-spec, plan-product, new-command` in column 2 and the mapping sentence followed by the degradation sentence in column 3. Run `test_adapter_canvas_row` after the edit `[AC-1.1, AC-1.5]`
- [x] 1.6 Make the command and issue edits. In `commands/create-spec.md`, § Step 1.3 (Discovery Conversation), replace the first sentence with the wording in technical-spec.md → ## Plan Mode Rows. In `commands/plan-product.md` § Step 1.2 and `commands/new-command.md` § Step 1.2, add "through the adapter's `Plan Mode` row" to the sentence that switches to Plan Mode. Append `## Resolution` to `.writ/issues/improvements/2026-10-22-create-spec-discovery-skips-plan-mode-on-claude-code.md`, naming this spec and the decision (the agent enters Plan Mode: `EnterPlanMode` on Claude Code, a question to the user on Cursor, a read-only conversation on Codex and OpenClaw), and set `spec_ref`. `git diff` each command file and confirm one sentence changed `[AC-1.5]`
- [x] 1.7 Verify: `uv run --python 3.9 pytest`, the bash loop (`for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`), and `bash scripts/eval.sh` run outside the sandbox. All pass, with 0 findings from eval. Record the counts in What Was Built `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Nil input, Empty input)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 2 Adapter parsing; Rule 3 Vocabulary and parity; Rule 4 Vendor-only names; Rule 9 Plan Mode rows; Rule 10 Command sentences; Rule 15 Runtime)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Malformed table row (wrong column count, empty first cell); Adapter section heading missing; Capability used in a command with no row in one adapter; `/create-spec` discovery on Claude Code)

---

## What Was Built

**Implementation Date:** 2026-10-22

### Files Created

1. **`scripts/gen-platform-trees.py`** (282 lines)
   - Adapter tool-table parser and vocabulary rule: `ADAPTERS`, `HEADINGS` (heading chain per adapter), `MAPPING_COLUMN` (cursor → column 3), `ALLOWLIST` (`Read`, `Write`, `Bash`, one comment each), `NAME_RE`, `Row(name, variant, mapping, notes, line)`, `AdapterTable(adapter, path, verdict, reasons, rows)` with `names` (ordered, variants collapsed) and `rel` (`adapters/<basename>`), `capability_name`, `section`, `first_table`, `parse_adapter(path, adapter=None)` (never raises; `fail` on `malformed adapters/<x>.md:<line>` or `empty adapters/<x>.md`; `unverifiable` on `section <heading> in adapters/<x>.md`, an unreadable file, or an unknown stem), `identifiers`, `vocabulary(tables) -> (neutral list in first-seen order, vendor_only set)`, `unmapped(tables)`. `main()` is a stub (`unverifiable`, `reason: not-implemented <mode>`, exit 0; `--help` exit 0; unknown flag exit 2) until Stories 2–4 add the writers, `--check`, and `coverage`. Python 3.9 stdlib only.
2. **`scripts/tests/test_gen_platform_trees.py`** (363 lines)
   - 30 tests, module loaded by path: `test_parse_real_adapters`, `test_capability_name` ×9, `test_vendor_only_tokens` (AC-1.1); `test_malformed_row` ×3 (AC-1.2); `test_missing_section` (AC-1.3); `test_parity` (AC-1.4); `test_plan_mode_row` ×4, `test_codex_file_search_row`, `test_openclaw_readonly_folded`, `test_command_sentence` ×3, `test_issue_resolution` (AC-1.5); `test_cli_help`, `test_cli_stub` ×3 (stub shape; Story 4 replaces them with the real CLI).
3. **`scripts/tests/fixtures/platform-trees/{malformed-cells,malformed-empty-first-cell,empty-table,missing-section,parity-no-file-search}/codex.md`** (17, 11, 14, 13, 23 lines)
   - One case per directory, each named `codex.md` so the stem selects the codex headings. Three carry a trailing `#### Verification record` table so first-table selection is exercised.

### Files Modified

- **`adapters/codex.md`** (`### Quick reference — orchestration primitives` table)
  - Line 142: `| \`file_search\` | \`Glob("**/pattern*")\` | Built-in Glob tool |` after `codebase_search`. Line 148: the `Plan Mode` row (last).
- **`adapters/openclaw.md`** (`## Quick Reference` table)
  - Line 18: `readonly: true` row → `| \`Task({ readonly: true })\` | Add constraint to task prompt | "Do NOT modify any files" |`. Line 20: the `Plan Mode` row (last).
- **`adapters/cursor.md`** (`## Native Tool Availability` table)
  - Line 116: `| \`Plan Mode\` | create-spec, plan-product, new-command | Ask the user to switch to Plan Mode; continue when they have. If the platform has no toggle, say so and proceed read-only. |` (DEV-003 records the column layout).
- **`adapters/claude-code.md`** (`### Quick Reference` table)
  - Line 199: `| \`Plan Mode\` | \`EnterPlanMode\`; present the contract proposal as the plan; after \`ExitPlanMode\` approval, lock with AskQuestion | If the platform has no toggle, say so and proceed read-only. |`.
- **`commands/create-spec.md`** (Step 1.3, line 246, one sentence)
  - "After the context scan, run discovery in Plan Mode, entered through the adapter's `Plan Mode` row; the user controls when to switch back." The rest of the line is unchanged.
- **`commands/plan-product.md`** (Step 1.2, line 178, one sentence)
  - "**After context scan and initial product direction selection, run discovery in Plan Mode through the adapter's `Plan Mode` row.**"
- **`commands/new-command.md`** (Step 1.2, line 45, one sentence)
  - "After the context scan, switch to Plan Mode through the adapter's `Plan Mode` row."
- **`.writ/issues/improvements/2026-10-22-create-spec-discovery-skips-plan-mode-on-claude-code.md`** (header `spec_ref`; new last H2 `## Resolution`)
  - `> **spec_ref:** .writ/specs/2026-10-22-generated-platform-trees/spec.md`. The Resolution (2026-10-22) names this spec, the lane, the per-platform decision (the agent enters Plan Mode: `EnterPlanMode` on Claude Code with the contract proposal as the plan and AskQuestion locking after `ExitPlanMode`; a question to the user on Cursor; a read-only conversation, said so, on Codex and OpenClaw), the four rows, the three sentences, the pinning tests, and that hygiene Scenario 29 is not re-run here (UAT).
- **`scripts/install.sh`, `scripts/update.sh`, `scripts/unlink.sh`** (`is_shippable_script`, dev-only case)
  - `gen-platform-trees.py` added beside `gen-claude-md.py`; the comment gains "platform trees"; three bodies byte-identical. Pulled forward from Story 4 because `test_agent_cli_contract.py::test_table_complete` and `test_agent_cli_contract_doc.py::test_every_shipped_script_has_exactly_one_row` derive the shipped set from this function (DEV-001). Story 4 task 4.6 is therefore already satisfied; it must not re-add the entry.
- **`scripts/tests/test_governor_enforcement.py`** (`KNOWN_OVER_BUDGET`)
  - `commands/create-spec.md` 13602 → 13654 with the dated comment the ledger convention uses; the Step 1.3 sentence is 52 bytes longer. Forced by `CreateSpecRepinTests` and `test_harness_cuts.py::OverageLedgerFellTest`.
- **`.writ/specs/2026-10-22-generated-platform-trees/spec-lite.md`** — three Implementation Approach lines amended (DEV-001, DEV-002, DEV-003).
- **`.writ/specs/2026-10-22-generated-platform-trees/drift-log.md`** — created; Story 1 section (DEV-001 to DEV-003).

### Implementation Decisions

1. **URL-shaped tokens are not identifiers** — `identifiers()` skips a backticked token containing `://` (and one starting `.`, `/`, `@`, `~`, which `NAME_RE` already rejects). Real-tree `vendor_only` = {EnterPlanMode, ExitPlanMode, Glob, Grep, TodoWrite, browser_navigate, disallowedTools, exec, message, permissionMode, sandbox_mode, sessions_spawn, subagents}; `http` is not in it (DEV-002).
2. **Missing-heading reason names the first heading in the chain that was not found** — for the fixture that is the innermost `### Quick reference — orchestration primitives`; an absent outer heading names the outer one, the actionable line.
3. **`unmapped` reads only tables with verdict `pass`** — a table that failed or is unverifiable already carries its own reason; `vocabulary` uses whatever rows parsed.
4. **Fail closed on every malformed row** — the separator row is validated against the header width; a first cell with no identifier is malformed like an empty cell; every bad row is reported with its own 1-based line and the good rows are kept; `empty` covers no table, header only, and header plus separator.
5. **Cursor `Plan Mode` row layout follows task 1.5** — command list in `Used By`, mapping sentence plus degradation sentence in `Purpose`, which the grammar reads as both mapping and notes (DEV-003).

### Story 4 forewarning (from review)

On this tree the leading-identifier match the spec prescribes finds, besides `` `Grep` ``/`` `Glob` `` in `commands/create-issue.md`, `` `message.usage` `` in `commands/retro.md:61,85` (→ `message`, an OpenClaw tool name, here a JSON field) and `` `browser_navigate` `` in `commands/writ-design.md:137`. Story 4 decides the call-syntax and field-access edge cases in task 4.2 and records them.

### Test Results

**Verification:** Automated, test-first (`uv run --python 3.9 pytest scripts/tests/test_gen_platform_trees.py` red: 8 failed, 22 errors — module absent, fixtures absent, content assertions; green: 30 passed).
**Coverage:** Not measured by the script (`test-integrity.py coverage`: unverifiable, no_coverage_report).

- ✅ Targeted: `uv run --python 3.9 pytest scripts/tests/test_gen_platform_trees.py scripts/tests/test_platform_neutral_names.py -q` → 78 passed (orchestrator's own run; `test_adapter_canvas_row` green on all four adapters).
- ✅ Full pytest (3.9): 2837 passed, 2 skipped (141s).
- ✅ Bash tests: 45 run, 0 failed (`for t in scripts/tests/test_*.sh`), including `test_install_update_dev_scripts.sh` and `test_gen_claude_md_not_shipped.sh`.
- ✅ `bash scripts/eval.sh` (outside the sandbox): Findings 0, Run errors 0 (`.writ/state/eval-20261023-040640.md`); the pre-existing leanness WARNINGs are notes, not findings.
- ✅ `python3 scripts/ac-trace.py check --spec .writ/specs/2026-10-22-generated-platform-trees` → 0 findings.
- ✅ Gate 0 arch-check: pass (rederived proceed). Gate 2: no linter configured; arch-lint: none — see .writ/docs/architecture-lint.md; build-smoke unverifiable (unsupported_stack). Gate 2.5: cross-component, 5 crossings, route review-agent. Gate 3 review-override: unverifiable (no_coverage_report). Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable (no_coverage_report); authenticity: pass. Gate 4.5 app-verify: unverifiable (no_recipe). Gate 5 docs-check: unverifiable (no_public_exports).

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-001, DEV-002, DEV-003)
- **Security:** Clean (stdlib only; file reads; no subprocess, network, or shell in the script)
- **Boundary Compliance:** owned paths plus five justified Readable deviations (`adapters/claude-code.md`, which task 1.5 edits; the three ship-filter bodies; the byte-ledger re-pin), all test-forced and byte-minimal; no violation.
- gate3-route: review-agent (outside_boundary adapters/claude-code.md; outside_boundary scripts/install.sh; outside_boundary scripts/update.sh; outside_boundary scripts/unlink.sh; outside_boundary scripts/tests/test_governor_enforcement.py). review-panel: unverifiable (platform_cannot_spawn_other_vendors). jev-shadow: unverifiable (no_api_key). arch-lint: none — see .writ/docs/architecture-lint.md.
- Reviewer re-ran the parser on the real tree and `bash scripts/eval.sh` (0 findings) independently of the coder's claims. Minor, non-blocking: the unreadable-file reason reuses the `missing` kind; the stub summary line is not the five-count shape (Story 4 replaces it with `test_cli_stub`); the separator and unreadable-file paths have no test.
- Coding agent and review agent ran as nested `general-purpose` spawns with the prompt templates from `agents/coding-agent.md` and `agents/review-agent.md`, working directly in the lane worktree (no nested worktree, so nothing to reconcile).

### Deviations from Spec

- **[DEV-001] `is_shippable_script` entry pulled forward from Story 4** — Severity: Small
  - Spec said: technical-spec.md → Eval Wiring assigns the denylist entry to Story 4 (`install.sh`, `update.sh`).
  - Reality: Landed in Story 1 in three scripts (`unlink.sh` too) because the CLI-contract tests derive the shipped set from the function.
  - Resolution: Auto-amended; spec-lite.md check-shape line names Story 1 and the three scripts.
- **[DEV-002] URL-shaped tokens excluded from vendor identifiers** — Severity: Small
  - Spec said: `vendor_only` = backticked identifiers in mapping cells minus neutral minus ALLOWLIST.
  - Reality: a token containing `://` is skipped; only `http` drops out on the real tree.
  - Resolution: Auto-amended; spec-lite.md vocabulary line gains the clause.
- **[DEV-003] Cursor `Plan Mode` row split across columns 2 and 3** — Severity: Small
  - Spec said: technical-spec.md → Plan Mode Rows gives cursor a Mapping cell and a Notes cell.
  - Reality: command list in `Used By`, mapping plus degradation sentence in `Purpose`, per task 1.5.
  - Resolution: Auto-amended; spec-lite.md Story 1 line names the layout.
