# Story 1: Canvas-Preview Capability in `/prototype` and the Four Adapters

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** developer running `/prototype` on Cursor, Claude Code, Codex, or OpenClaw
**I want to** have Step 2.5 name a capability my platform's adapter translates
**So that** my drafts render with a tool that exists on my platform, or I am told plainly that they were not rendered

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given `commands/prototype.md`, when it is read, then § Step 2's "Figma MCP detection" sentence and § Step 2.5 → "Render through the platform" both name `canvas-preview`, the file contains no `cursor-ide-browser`, the render table keeps its three rows in the same order, and "Never degrade silently." is still present `[AC-1.1]`
- [ ] Given `adapters/cursor.md` § Native Tool Availability, when it is read, then exactly one row starts with `` | `canvas-preview` | ``, and it maps the capability to the `cursor-ide-browser` canvas and ends with the clause "No renderer: write a structural description of each draft and say the drafts were not rendered." `[AC-1.2]`
- [ ] Given `adapters/claude-code.md` § Tool Mapping → Quick Reference, when it is read, then exactly one `canvas-preview` row maps the capability to an artifact or the preview pane and carries the same degradation clause `[AC-1.3]`
- [ ] Given `adapters/codex.md` and `adapters/openclaw.md`, when each tool table is read, then exactly one `canvas-preview` row maps the capability to one self-contained HTML file per draft under `.writ/prototypes/<date>-<slug>/` and carries the same degradation clause `[AC-1.4]`
- [ ] Given the finished story, when `git grep -n cursor-ide-browser` runs, then every hit is `adapters/cursor.md` or a record path from the technical spec's record list; `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` (0 findings) all pass `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write failing tests in a new `scripts/tests/test_platform_neutral_names.py`: `test_prototype_names_capability`, `test_adapter_canvas_row` parametrized over the four adapters with the keywords from technical-spec.md → Canvas-Preview Capability → Test, and `test_cursor_ide_browser_confined` using the shared `RECORD_PREFIXES` and `DATED_SNAPSHOTS` constants. Cite the AC IDs in each test's docstring. Run them and confirm they fail for the stated reason `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [ ] 1.2 Edit `commands/prototype.md`: the Step 2 "Figma MCP detection" sentence, the Step 2.5 render table's middle-row label, and the sentence under that table, using the exact text in technical-spec.md → `commands/prototype.md`. Leave the first and third rows and every other line unchanged `[AC-1.1]`
- [ ] 1.3 Add the `canvas-preview` row to `adapters/cursor.md` § Native Tool Availability, at the end of the table `[AC-1.2]`
- [ ] 1.4 Add the `canvas-preview` row to `adapters/claude-code.md` § Tool Mapping (Cursor → Claude Code) → Quick Reference. Find the table by heading: `2026-10-20-claude-code-parity` rewrites parts of this file first `[AC-1.3]`
- [ ] 1.5 Add the `canvas-preview` rows to `adapters/codex.md` § Tool Mapping (Cursor → Codex CLI) → Quick reference — orchestration primitives and `adapters/openclaw.md` § Quick Reference `[AC-1.4]`
- [ ] 1.6 Verify: run `uv run --python 3.9 pytest scripts/tests/test_platform_neutral_names.py`, then `git grep -n cursor-ide-browser` and check each hit against the record list `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [ ] 1.7 Verify the regression surface: `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` outside the sandbox. All pass and eval reports 0 findings `[AC-1.5]`

## Notes

- **Name only, no redesign.** PR #59 wrote Step 2.5's rendering delegation. This story changes one row label and one sentence there, plus one sentence in Step 2. The research behind the issue says to leave the step's scope alone.
- **Codex and OpenClaw rows have no runtime evidence.** The prototype research (Further Research item 4) found no usable capability matrix for Cursor, Codex, or OpenClaw. The rows follow the locked contract. Do not add claims about platform features beyond it.
- **Shared constants.** Define `RECORD_PREFIXES` and `DATED_SNAPSHOTS` once at the top of the test module, exactly as technical-spec.md → Reference Gate → Record list gives them. Story 3's gate reuses them.
- **Parse `git grep` with `--null`.** `.writ/explanations/2026-03-20-WritPipelineArchitecture .md` has a space in its name.
- **Leanness.** Each adapter grows by one row and `prototype.md` stays the same length. If `eval-leanness.py` notes change, they must stay warn-only.
- **Symlinks.** `.claude/commands` and `.cursor/commands` link to `commands/`. Edit `commands/prototype.md` only, and never replace a symlink with a copy.
- **Unrelated working-tree edits.** Other Phase 13 work may be uncommitted. Run `git diff` before and after each shared file and change only the targeted lines.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Render drafts via `canvas-preview`, Write HTML drafts (Codex, OpenClaw)] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [`/prototype` Step 2.5 render] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Rule 1 (capability name), Rule 2 (adapter row shape and fixed clause), Rule 3 (platform mappings), Rule 4 (Step 2.5 stays as PR #59 wrote it)] — spec.md → ## Business Rules (Expanded)
- **Experience:** [State Catalog rows for `/prototype` Step 2.5 on each platform, including the headless and read-only cases] — spec.md → ## Experience Design → ### State Catalog
- **Technical:** technical-spec.md → ## Canvas-Preview Capability (Story 1), ## Reference Gate → ### Record list
