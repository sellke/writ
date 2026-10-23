# Story 2: Driver Write Mode for the Cursor and Claude Code Root Files

> **Status:** Completed ✅ (2026-10-22)
> **Commit:** 19ffbc5e97db0f4bb6691d7a0d517e521d2efba1
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer who edits an adapter or agent file
**I want to** run `python3 scripts/gen-platform-trees.py` once and get `cursor/writ.mdc` and `claude-code/CLAUDE.md` regenerated with each platform's capability map, plus the sub-generators' outputs
**So that** an installed Cursor or Claude Code project's agent resolves every capability in the root file it already loads, without reading `adapters/`

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given `system-instructions.md` with its `alwaysApply: true` frontmatter and the Cursor adapter, when the driver writes `cursor/writ.mdc`, then the file starts with `---`, `alwaysApply: true`, `---`, then the generated-file comment, then the `system-instructions.md` body with its own frontmatter removed, then the Cursor `## Capability Map` as the last section, and its `## Prime Directive` section is byte-equal to the source's `## Prime Directive` section `[AC-2.1]`
- [x] Given the Cursor and Claude Code tool tables read by Story 1's parser, when the driver renders each `## Capability Map`, then the section opens with "Commands name capabilities; this table maps them to this platform.", has a `Capability | On this platform | When unavailable` table with one row per neutral name in the adapter's row order, and each "When unavailable" cell holds the notes-cell sentence that starts with `No renderer:`, `If the platform`, or `No agent-side`, or `—` when none does `[AC-2.2]`
- [x] Given the `{capability_map}` slot added to `gen-claude-md.py`'s TEMPLATE after the Commands table, when the driver writes `claude-code/CLAUDE.md`, then `## Capability Map` with the Claude Code rows follows the Commands table, and `python3 scripts/gen-claude-md.py --check` prints `pass` `[AC-2.3]`
- [x] Given a clean tree, when the driver runs in write mode, then it prints `pass`, one `wrote <path>` line per file, and `gen-platform-trees: pass (…)`; given any reason, or a sub-generator that exits 2 or higher, then it prints `fail`, folds each sub-generator reason as `reason: <gen>: <kind> <stem>` (or `reason: <gen> --check exited <rc>`), and writes no file `[AC-2.4]`
- [x] Given the hand-maintained `cursor/writ.mdc` at git HEAD, when the first write replaces it, then the diff is recorded in this story's What Was Built, and every sentence of the old file is either present in the new file or listed there as a bug to fix `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Write failing tests in `scripts/tests/test_gen_platform_trees.py`: `test_writ_mdc` (composition and byte-equal Prime Directive), `test_claude_md_map` (map after the Commands table; `gen-claude-md.py --check` prints `pass`), a write-mode check-shape case (`pass` with `wrote` lines; a seeded bad row writes nothing), and a sub-generator exit-2 case (`fail`, nothing written). Each case runs on a temp copy of the tree. Run them and confirm all fail on the current tree `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [x] 2.2 Add `capability_map(adapter, root)` to `scripts/gen-platform-trees.py` on Story 1's `parse_adapter`: the lead sentence, the three-column table, adapter row order, and the degradation-sentence rule. Check the rendered Cursor and Claude Code maps against the rule by reading the output `[AC-2.2]`
- [x] 2.3 Write `cursor/writ.mdc` in write mode: `---\nalwaysApply: true\n---\n`, the generated-file comment naming the driver and its sources, the `system-instructions.md` body with its frontmatter removed, then the Cursor map. Make `test_writ_mdc` pass `[AC-2.1]`
- [x] 2.4 Add the `{capability_map}` slot to `scripts/gen-claude-md.py`'s TEMPLATE after the Commands table. Load `capability_map` by path with `importlib.util.spec_from_file_location`. Regenerate `claude-code/CLAUDE.md`. Make `test_claude_md_map` pass and keep `test_gen_claude_md.py` and `test_eval_claude_md.sh` green `[AC-2.3]`
- [x] 2.5 Add write mode to the driver. Run `--check` on the driver's own checks and on all three sub-generators (`gen-claude-md.py`, `gen-claude-agents.py`, `gen-codex-agent-tomls.py`) before writing anything. Fold each `reason:` line as `reason: <gen>: <kind> <stem>`. Any reason or any exit of 2 or higher prints `fail` (with `reason: <gen> --check exited <rc>` for the exit case) and writes nothing. Otherwise write `cursor/writ.mdc`, write `claude-code/CLAUDE.md` and the two agent outputs, and print one `wrote <path>` per file plus the summary line. Make the check-shape and sub-generator cases from 2.1 pass `[AC-2.4]`
- [x] 2.6 Diff the hand copy against the first generated `cursor/writ.mdc`: `git show HEAD:cursor/writ.mdc` against the new file. Record the diff in a What Was Built section of this story. Any sentence the new file drops is a bug: fix the generator or `system-instructions.md`, regenerate, and note the fix in What Was Built `[AC-2.5]`
- [x] 2.7 Verify: run the driver twice and confirm the second run leaves the tree byte-identical; `uv run --python 3.9 pytest`; `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` with no `FAIL` lines; `python3 scripts/gen-claude-md.py --check` prints `pass`; `bash scripts/eval.sh` outside any sandbox reports 0 findings `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

- **Frontmatter strip.** Remove only the leading `---` block of `system-instructions.md`. Keep every other byte. The Prime Directive test compares bytes, not rendered text. See the `## Generated Files` section of the technical spec.
- **Map placement.** `cursor/writ.mdc`: map last. `claude-code/CLAUDE.md`: map at the `{capability_map}` slot after the Commands table. See `## Capability Map Section` in the technical spec.
- **Import by path.** `gen-platform-trees.py` has a hyphen, so `gen-claude-md.py` cannot `import` it. Load it with `importlib.util.spec_from_file_location`. If that import runs driver code, or the driver's sub-generator calls create a cycle, move `capability_map` into an underscore-prefixed module under `scripts/`, following `scripts/_archival_hook_model.py`. Underscore files are not shipped.
- **Root parameter.** `gen-claude-md.py`'s `main(argv, root)` already accepts a root. Tests pass a temp root. The renderer must also resolve `adapters/` from that root, or temp-root tests read the real adapters.
- **Check first, then write.** The spec says the driver invokes the sub-generators in write mode and writes nothing when any reason exists. Those rules conflict when one sub-generator writes before another reports. Resolution used here: run every `--check` first, then write only when all are clean. This is a decision made for this story, not a rule quoted from the spec.
- **Temp-copy tests.** Tests copy `scripts/`, `adapters/`, `agents/`, `commands/`, `skills/`, `cursor/`, `claude-code/`, `codex/`, `system-instructions.md`, and `.writ/manifest.yaml` into `tmp_path` and run the driver there. No test writes into the repo.
- **Risk: lost sentence.** The first write replaces the hand copy. Task 2.6 is the guard. Diff against `git show HEAD:cursor/writ.mdc`, not the working tree.
- **Risk: pinned tests.** `test_gen_claude_md.py` and `test_eval_claude_md.sh` pin `gen-claude-md.py` output. Update the expected output only for the new map slot.
- **Integration.** Story 1 supplies `parse_adapter` and the neutral set. Story 3 reuses `capability_map` for the Codex template. Story 4 adds `--check`, `coverage`, eval wiring, and the dev-only denylist entry; this story's reason lines must use the shape Story 4 parses.
- **Scope.** This story changes no file under `commands/`, `skills/`, or `adapters/`.

---

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Upstream error)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 1 Driver CLI, default write mode and exit codes; Rule 6 `cursor/writ.mdc` composition; Rule 7 `claude-code/CLAUDE.md` slot; Rule 12 generated-file comment)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Clean tree; Installed Cursor project; Installed Claude Code project)

---

## What Was Built

**Implementation Date:** 2026-10-22

### Files Created

[None created]

### Files Modified

- **`scripts/gen-platform-trees.py`** (new sections "Capability map", "cursor/writ.mdc", "Sub-generators and write mode"; docstring)
  - `degradation(notes)` (first sentence starting `No renderer:`, `If the platform`, or `No agent-side`, else `—`), `render_map(table)` (pure; first row of a name carries `` `<name>` ``, each further variant a sub-row such as `` `Task({ readonly: true })` ``; mapping verbatim; one trailing newline), `capability_map(adapter, root)` (raises `ValueError` with the table's reasons joined by `; ` when the table is not `pass`), `strip_frontmatter`, `render_writ_mdc(root)`, `GENERATED = [("cursor/writ.mdc", render_writ_mdc)]` (Story 3 appends the Codex template), `write_file` (temp file + `os.replace`, mode kept), `run_subgenerator` (`[sys.executable, scripts/<gen>.py, …]`, `cwd=root`, no shell), `fold_check`, `verdict_of`, `finish`, `write_mode(root)`. `SUBGENERATORS = ("gen-claude-agents", "gen-codex-agent-tomls", "gen-claude-md")`, producers first. `REPAIRED_KINDS = {stale, missing, absent, extra}`. Write-mode summary `gen-platform-trees: <verdict> (<n> written, <r> reasons)`. `--check`, `coverage`, `--target`/`--out-dir` keep the Story 1 stub (`reason: not-implemented check|coverage|target`).
- **`scripts/gen-claude-md.py`** (TEMPLATE; `read_capability_map`, `render`, `render_reasons`, `finish`, `write`, `main`; docstring)
  - `{capability_map}` slot directly after `{rows}`, before `## Agents`. `read_capability_map(root)` loads the driver by `importlib.util.spec_from_file_location` and calls `capability_map("claude-code", root)`; a `ValueError` becomes one `reason: capability-map <reason>` per reason. `render(commands, agents, capability_map)`; `render_reasons` adds `import-token capability-map` for an `@` outside backticks in the map. New `unverifiable` inputs: `platform-trees missing: scripts/gen-platform-trees.py`, `adapter missing: adapters/claude-code.md`. Write mode prints `wrote claude-code/CLAUDE.md` between `pass` and the summary.
- **`cursor/writ.mdc`** (generated; first write replaces the hand copy — see Takeover Diff)
  - Frontmatter, the generated-file comment on line 4, the `system-instructions.md` body verbatim (its own frontmatter removed), then the Cursor `## Capability Map` (10 rows). 6148 bytes.
- **`claude-code/CLAUDE.md`** (generated by `gen-claude-md.py`)
  - `## Capability Map` with the 11 Claude Code rows (10 names plus the `Task({ readonly: true })` sub-row) between the Commands table and `## Agents`. 8094 bytes. No generated-file comment (DEV-006).
- **`scripts/tests/test_gen_platform_trees.py`** (docstring cites AC-2.1 to AC-2.5; Story 2 section with `tmp_tree`, `run_tree`, `generated_bytes`, `prime_directive`, `seed_bad_row`, `wrote_lines` helpers)
  - `test_degradation`, `test_capability_map[cursor|claude-code]`, `test_capability_map_rejects_bad_table` (AC-2.2); `test_writ_mdc` (AC-2.1); `test_claude_md_map` (AC-2.3); `test_write_mode_shape` (with the byte-identical second run), `test_write_blocked_by_bad_row`, `test_write_blocked_by_subgenerator_exit`, `test_write_folds_subgenerator_reason`, `test_write_ignores_stale_outputs`, `test_unverifiable_heading` (AC-2.4); `test_cli_unknown_flag_is_usage_error`; `test_cli_stub[check|coverage|target]`. Every write-mode case runs in a `tmp_path` copy of `scripts/*.py`, `adapters/`, `agents/`, `commands/`, `skills/`, `cursor/`, `claude-code/`, `codex/`, `system-instructions.md`, and `.writ/manifest.yaml`; nothing writes into the repo.
- **`scripts/tests/test_gen_claude_md.py`** (`TempRoot.setUp`; `expected_fixture()`; new end-of-file class `CapabilityMapTests`)
  - The temp root also receives `scripts/gen-platform-trees.py` and the real `adapters/claude-code.md`; `EXPECTED_FIXTURE` became `EXPECTED_HEAD` + `expected_fixture()`, which splices the map computed by the driver (no hard-coded adapter rows); `test_ac_1_1_render_matches_cli` passes the map. `CapabilityMapTests`: map between Commands and Agents, the `wrote` line, missing adapter and missing driver → `unverifiable`, malformed adapter row → `capability-map malformed adapters/claude-code.md:<line>` in both modes, `@` in the map → `import-token capability-map`. The module docstring names this spec and then the parity spec last, so ac-trace attributes each class's AC tokens to its own spec.
- **`scripts/tests/test_eval_claude_md.sh`** (`new_root`)
  - Also copies `scripts/gen-platform-trees.py` and `adapters/claude-code.md` into the temp root; every existing assertion kept (7/7).
- **`.writ/specs/2026-10-22-generated-platform-trees/spec-lite.md`** — three lines amended (DEV-004, DEV-005, DEV-006).
- **`.writ/specs/2026-10-22-generated-platform-trees/drift-log.md`** — Story 2 section (DEV-004 to DEV-006).

### Takeover Diff (AC-2.5)

`git show HEAD:cursor/writ.mdc` is byte-identical to `system-instructions.md` (4572 bytes), so the hand copy carried no sentence of its own. `git show HEAD:cursor/writ.mdc | diff - cursor/writ.mdc`:

```
3a4
> <!-- generated by scripts/gen-platform-trees.py from system-instructions.md and adapters/cursor.md — do not hand-edit; regenerate -->
82a84,100
> 
> ## Capability Map
> 
> Commands name capabilities; this table maps them to this platform.
> 
> | Capability | On this platform | When unavailable |
> |---|---|---|
> | `Task` | Spawn sub-agents (coding, review, testing, docs, story generator) | — |
> | `AskQuestion` | Structured multi-choice questions with UI rendering | — |
> | `codebase_search` | Semantic code search across the project | — |
> | `file_search` | Find files by name/pattern | — |
> | `todo_write` | Visual progress tracking in Cursor sidebar | — |
> | `read_file` | Read file contents | — |
> | `run_terminal_cmd` | Run shell commands | — |
> | `list_dir` | List directory contents | — |
> | `canvas-preview` | Write one self-contained HTML file per draft to `.writ/prototypes/<date>-<slug>/` and give the user each path. The documented Browser tool (`@browser`, `browser_navigate`) opens only origins on its allowlist, such as `http://localhost:3000`, so a draft renders there only when the project serves that folder; no canvas tool that renders a local HTML file is documented. No renderer: write a structural description of each draft and say the drafts were not rendered. | No renderer: write a structural description of each draft and say the drafts were not rendered. |
> | `Plan Mode` | Ask the user to switch to Plan Mode; continue when they have. If the platform has no toggle, say so and proceed read-only. | If the platform has no toggle, say so and proceed read-only. |
```

Only `>` lines: every sentence of the old file is present in the new one. No bug to fix in the generator or in `system-instructions.md`.

### Implementation Decisions

1. **Producers first** — `SUBGENERATORS` runs `gen-claude-agents` and `gen-codex-agent-tomls` before `gen-claude-md`, because `gen-claude-md` reads `claude-code/agents/*.md`, which `gen-claude-agents` writes; one run converges (`test_write_ignores_stale_outputs`). The spec lists the three without an order.
2. **Output-state reasons do not block a write** — a sub-generator `--check` reason of kind `stale`, `missing`, `absent`, or `extra` is what write mode repairs, so `fold_check` drops it; `orphan`, `unmapped`, and every input kind block (DEV-005). An `unverifiable` sub-generator verdict folds every reason and makes the driver `unverifiable`; a `fail` with no reason line is `reason: <gen> --check printed fail without a reason`.
3. **Line 1 is always the final verdict** — output is buffered (verdict, reasons, `wrote` lines, summary) so a sub-generator failing at write time cannot leave a `pass` on line 1 above a `fail`.
4. **`gen-claude-md.py` prints its own `wrote` line** — the driver relays every sub-generator's `wrote <path>` lines verbatim, so the Claude Code template generator prints one like the agent generators do.
5. **No comment in `claude-code/CLAUDE.md`** — technical-spec.md → Generated Files ("existing header + the slot") and Rule 12's carve-out for existing generators (DEV-006).
6. **Map rendering reuses the adapter's row order and cell text** — the mapping cell is reproduced verbatim (escaped pipes stay escaped), so the map can never disagree with the adapter table it was read from.

### Test Results

**Verification:** Automated, test-first (`uv run --python 3.9 pytest scripts/tests/test_gen_platform_trees.py scripts/tests/test_gen_claude_md.py -q` red: 20 failed, 59 passed — `AttributeError` on the missing functions, write-mode assertions on the stub, fixture bytes; green: targeted 149 passed).
**Coverage:** Not measured by the script (`test-integrity.py coverage`: unverifiable, no_coverage_report).

- ✅ Targeted: `uv run --python 3.9 pytest scripts/tests/test_gen_platform_trees.py scripts/tests/test_gen_claude_md.py scripts/tests/test_platform_neutral_names.py scripts/tests/test_lifecycle_commands_claude_md.py scripts/tests/test_front_door.py -q` → 149 passed (orchestrator's own run).
- ✅ Real tree: `python3 scripts/gen-platform-trees.py` → `pass`, `wrote cursor/writ.mdc`, 16 agent `wrote` lines, `wrote claude-code/CLAUDE.md`, `gen-platform-trees: pass (18 written, 0 reasons)`; a second run is byte-identical (same 7 changed files; the 16 agent files regenerate byte-identical). `python3 scripts/gen-claude-md.py --check` → `pass (33 commands, 8 agents)`.
- ✅ Full pytest (3.9): 2856 passed, 2 skipped (142s).
- ✅ Bash tests: 45 run, 0 failed, including `test_eval_claude_md.sh` (7/7) and `test_gen_claude_md_not_shipped.sh`.
- ✅ `bash scripts/eval.sh` (outside the sandbox): Findings 0, Run errors 0 (`.writ/state/eval-20261023-045050.md`); `check_prime_directive_sync` and `check_claude_md` pass on the generated files.
- ✅ `python3 scripts/ac-trace.py check --spec .writ/specs/2026-10-22-generated-platform-trees` → 0 findings.
- ✅ Gate 0 arch-check: pass (rederived proceed). Gate 2: no linter configured; arch-lint: none — see .writ/docs/architecture-lint.md; build-smoke unverifiable (unsupported_stack). Gate 2.5: cross-component, 0 crossings, route evaluator-agent. Gate 3 review-override: pass. Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable (no_coverage_report); authenticity: pass. Gate 4.5 app-verify: unverifiable (no_recipe). Gate 5 docs-check: unverifiable (no_public_exports).

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-004, DEV-005, DEV-006)
- **Security:** None (subprocess with `sys.executable`, list argv, `cwd=root`, no shell; the driver is loaded by path and has no import-time side effects; the Claude Code map has no `@` outside backticks and `render_reasons` fails `import-token capability-map` if one appears)
- **Boundary Compliance:** all seven changed files are owned; no deviation, no violation.
- gate3-route: evaluator-agent. review-panel: unverifiable (platform_cannot_spawn_other_vendors). jev-shadow: unverifiable (no_api_key). arch-lint: none — see .writ/docs/architecture-lint.md.
- Evaluator residuals, not drift: `run_subgenerator` discards stderr, so a crashing sub-generator surfaces only as `<gen> --check exited <rc>`; `fold_check` returns no reason for an `unverifiable` verdict with no reason line (latent; no sub-generator emits that); the write phase is not atomic across files after the pre-checks; the Cursor map repeats the degradation sentence in both cells because the Cursor adapter's column 3 is both mapping and notes (DEV-003); `degradation()` would truncate a degradation sentence containing an internal `. ` (none does).
- Evaluator reproduced the clean, bad-row, and sub-generator-exit cases in a scratchpad copy and the 149-pass run on the lane tree; it also confirmed the takeover diff is purely additive.
- Coding agent and evaluator ran as nested `general-purpose` spawns with the prompt templates from `agents/coding-agent.md` and `agents/evaluator-agent.md`, working directly in the lane worktree.

### Deviations from Spec

- **[DEV-004] Driver summary line in write mode is `(<n> written, <r> reasons)`, not the per-kind counts** — Severity: Small
  - Spec said: technical-spec.md → Driver CLI gives the per-kind summary `(<n> stale, <m> missing, <o> orphan, <u> unmapped, <v> vendor)`.
  - Reality: write mode prints `(<n> written, <r> reasons)`; `--check` (Story 4) carries the per-kind counts, as the sibling generators do.
  - Resolution: Auto-amended; spec-lite.md check-shape line names the write-mode summary.
- **[DEV-005] Sub-generator output-state kinds do not block write mode** — Severity: Small
  - Spec said: nothing is written when any reason exists.
  - Reality: `stale`/`missing`/`absent`/`extra` sub-generator reasons are what write repairs and are dropped; every other kind blocks.
  - Resolution: Auto-amended; spec-lite.md Business Rules check-shape line gains the clause.
- **[DEV-006] `claude-code/CLAUDE.md` carries no generated-file comment** — Severity: Small
  - Spec said: Rule 12, every generated file carries the comment; technical-spec.md, "existing header + the slot".
  - Reality: the slot only; the file still opens with `# Writ`.
  - Resolution: Auto-amended; spec-lite.md regenerate line says which files carry the comment.
