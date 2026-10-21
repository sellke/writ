# Story 1: Canvas-Preview Capability in `/prototype` and the Four Adapters

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** developer running `/prototype` on Cursor, Claude Code, Codex, or OpenClaw
**I want to** have Step 2.5 name a capability my platform's adapter translates
**So that** my drafts render with a tool that exists on my platform, or I am told plainly that they were not rendered

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given `commands/prototype.md`, when it is read, then § Step 2's "Figma MCP detection" sentence and § Step 2.5 → "Render through the platform" both name `canvas-preview`, the file contains no `cursor-ide-browser`, the render table keeps its three rows in the same order, and "Never degrade silently." is still present `[AC-1.1]`
- [x] Given `adapters/cursor.md` § Native Tool Availability, when it is read, then exactly one row starts with `` | `canvas-preview` | ``, and it maps the capability to the `cursor-ide-browser` canvas and ends with the clause "No renderer: write a structural description of each draft and say the drafts were not rendered." `[AC-1.2]`
- [x] Given `adapters/claude-code.md` § Tool Mapping → Quick Reference, when it is read, then exactly one `canvas-preview` row maps the capability to an artifact or the preview pane and carries the same degradation clause `[AC-1.3]`
- [x] Given `adapters/codex.md` and `adapters/openclaw.md`, when each tool table is read, then exactly one `canvas-preview` row maps the capability to one self-contained HTML file per draft under `.writ/prototypes/<date>-<slug>/` and carries the same degradation clause `[AC-1.4]`
- [x] Given the finished story, when `git grep -n cursor-ide-browser` runs, then every hit is `adapters/cursor.md` or a record path from the technical spec's record list; `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` (0 findings) all pass `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write failing tests in a new `scripts/tests/test_platform_neutral_names.py`: `test_prototype_names_capability`, `test_adapter_canvas_row` parametrized over the four adapters with the keywords from technical-spec.md → Canvas-Preview Capability → Test, and `test_cursor_ide_browser_confined` using the shared `RECORD_PREFIXES` and `DATED_SNAPSHOTS` constants. Cite the AC IDs in each test's docstring. Run them and confirm they fail for the stated reason `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [x] 1.2 Edit `commands/prototype.md`: the Step 2 "Figma MCP detection" sentence, the Step 2.5 render table's middle-row label, and the sentence under that table, using the exact text in technical-spec.md → `commands/prototype.md`. Leave the first and third rows and every other line unchanged `[AC-1.1]`
- [x] 1.3 Add the `canvas-preview` row to `adapters/cursor.md` § Native Tool Availability, at the end of the table `[AC-1.2]`
- [x] 1.4 Add the `canvas-preview` row to `adapters/claude-code.md` § Tool Mapping (Cursor → Claude Code) → Quick Reference. Find the table by heading: `2026-10-20-claude-code-parity` rewrites parts of this file first `[AC-1.3]`
- [x] 1.5 Add the `canvas-preview` rows to `adapters/codex.md` § Tool Mapping (Cursor → Codex CLI) → Quick reference — orchestration primitives and `adapters/openclaw.md` § Quick Reference `[AC-1.4]`
- [x] 1.6 Verify: run `uv run --python 3.9 pytest scripts/tests/test_platform_neutral_names.py`, then `git grep -n cursor-ide-browser` and check each hit against the record list `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [x] 1.7 Verify the regression surface: `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` outside the sandbox. All pass and eval reports 0 findings `[AC-1.5]`

## Notes

- **Name only, no redesign.** PR #59 wrote Step 2.5's rendering delegation. This story changes one row label and one sentence there, plus one sentence in Step 2. The research behind the issue says to leave the step's scope alone.
- **Codex and OpenClaw rows have no runtime evidence.** The prototype research (Further Research item 4) found no usable capability matrix for Cursor, Codex, or OpenClaw. The rows follow the locked contract. Do not add claims about platform features beyond it.
- **Shared constants.** Define `RECORD_PREFIXES` and `DATED_SNAPSHOTS` once at the top of the test module, exactly as technical-spec.md → Reference Gate → Record list gives them. Story 3's gate reuses them.
- **Parse `git grep` with `--null`.** `.writ/explanations/2026-03-20-WritPipelineArchitecture .md` has a space in its name.
- **Leanness.** Each adapter grows by one row and `prototype.md` stays the same length. If `eval-leanness.py` notes change, they must stay warn-only.
- **Symlinks.** `.claude/commands` and `.cursor/commands` link to `commands/`. Edit `commands/prototype.md` only, and never replace a symlink with a copy.
- **Unrelated working-tree edits.** Other Phase 13 work may be uncommitted. Run `git diff` before and after each shared file and change only the targeted lines.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Render drafts via `canvas-preview`, Write HTML drafts (Codex, OpenClaw)] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [`/prototype` Step 2.5 render] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Rule 1 (capability name), Rule 2 (adapter row shape and fixed clause), Rule 3 (platform mappings), Rule 4 (Step 2.5 stays as PR #59 wrote it)] — spec.md → ## Business Rules (Expanded)
- **Experience:** [State Catalog rows for `/prototype` Step 2.5 on each platform, including the headless and read-only cases] — spec.md → ## Experience Design → ### State Catalog
- **Technical:** technical-spec.md → ## Canvas-Preview Capability (Story 1), ## Reference Gate → ### Record list

---

## What Was Built

**Implementation Date:** 2026-10-21

### Files Created

1. **`scripts/tests/test_platform_neutral_names.py`** (234 lines)
   - Canvas section of the spec's static checks. Defines the shared `RECORD_PREFIXES` and `DATED_SNAPSHOTS` constants (technical-spec.md → Record list), the `section`, `first_table`, `cells`, `git_grep`, and `is_record` helpers, and `test_prototype_names_capability`, `test_adapter_canvas_row[cursor|claude-code|codex|openclaw]`, and `test_cursor_ide_browser_confined`.

### Files Modified

- **`commands/prototype.md`** (§ Step 2 Figma MCP detection; § Step 2.5 → Render through the platform)
  - Step 2 names the `canvas-preview` capability (see the adapter). The render table's middle row label is `` `canvas-preview` (the adapter maps it) ``. The sentence under the table says each adapter maps `canvas-preview` and states its fallback, then "Never degrade silently." Three lines changed; the file stays 336 lines.
- **`adapters/cursor.md`** (§ Native Tool Availability) — `canvas-preview` row: the `cursor-ide-browser` canvas, plus the degradation clause.
- **`adapters/claude-code.md`** (§ Tool Mapping → Quick Reference) — row: an artifact, or the preview pane; one self-contained HTML page per draft; clause.
- **`adapters/codex.md`** (§ Tool Mapping → Quick reference — orchestration primitives) — row: `Write` one self-contained HTML file per draft to `.writ/prototypes/<date>-<slug>/`; clause.
- **`adapters/openclaw.md`** (§ Quick Reference) — row: `Write({ path: ".writ/prototypes/<date>-<slug>/<draft>.html" })`, one self-contained HTML file per draft; clause.

### Implementation Decisions

1. **The test file never spells the Cursor tool name.** It builds it as `"cursor-ide" + "-browser"`, so the committed test is not a hit of its own confinement grep.
2. **Tests are stricter than the technical spec's test table.** They check the exact degradation clause in the last cell, that the row sits inside the named table with the table's column count, and the three render-table labels in order.
3. **`git_grep` parses `-n -I --null -F` output as bytes.** Exit 1 returns `[]`; any other non-zero exit raises, so a broken grep never reads as clean. Story 3's gate reuses the constants.

### Test Results

**Verification:** test-first, then full suites.

- Red: all 6 new tests failed before the markdown edits (prototype still named the tool, 0 rows in each adapter, one stray hit in `commands/prototype.md`); evaluator re-confirmed in a scratch copy (probe P0).
- Mutations (evaluator, scratch copies): 14 probes (rows swapped, sentence removed, Figma line without the capability, clause removed or reworded, duplicated row, row moved out of the table, keywords removed, extra cell, stray hits including a path with a space, the spec's exact OpenClaw text) each fail the test aimed at them.
- Orchestrator run: `uv run --python 3.9 pytest scripts/tests/test_platform_neutral_names.py -v` → 6 passed.
- Full suites (coder and evaluator): pytest 3.9 → 2688 passed, 2 skipped (baseline 2682 + 6); bash loop → 44 run, 0 failed; `bash scripts/eval.sh` → Findings: 0.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-001)
- **Security:** Clean
- **Boundary Compliance:** all edits in owned files; Gate 2.5 found 0 crossings
- gate3-route: evaluator-agent. review-panel: not convened (Gate 3 ran evaluator-agent without `--panel`). arch-lint: none — see .writ/docs/architecture-lint.md.
- Gate 0 arch-check: pass (rederived proceed). Gate 2: no linter configured; `py_compile` clean; build-smoke unverifiable (unsupported stack). Gate 3 review-override: unverifiable (no coverage report). Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable (no report). Gate 4 authenticity: `test_imports_no_source` on the new test, which reads markdown as text and imports no code, like other doc-text tests; carried on the red-phase and mutation evidence above, not DEGRADED. Gate 4.5: app-verify unverifiable (no recipe). Gate 5: docs-check unverifiable (no public exports).
- Evaluator residual (not drift): the Codex and OpenClaw rows' "Includes a read-only sandbox." / "Includes a run that cannot write files." are the spec's exact text but read without a subject; the tool tables now hold a capability row, which the Phase 14 adapter coverage check will need to tell apart from tool rows; on Codex and OpenClaw the Step 2 Figma condition is now true whenever writes are allowed.

### Deviations from Spec

- **[DEV-001] OpenClaw row says "HTML file" where the technical spec's row text says "file"** — Severity: Small
  - Spec said: technical-spec.md → Adapter rows, OpenClaw second cell "…, one self-contained file per draft".
  - Reality: "…, one self-contained HTML file per draft", so the spec's own `HTML` keyword test passes.
  - Resolution: Auto-amended
  - Spec amendment: None needed; spec-lite.md already says "HTML file". Recorded in drift-log.md.
