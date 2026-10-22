# Story 5: Install Evidence and Issue Closure

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 4

## User Story

**As a** maintainer closing the adapter-mappings issue, and a user of an installed Cursor, Claude Code, or Codex project
**I want to** have a test install Writ into fresh projects and check the capability map in the root file each platform loads
**So that** the issue closes on installed-file evidence, and the installed agent resolves each capability without reading `adapters/`

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [ ] Given a committed temp copy of the working tree and a fresh `git init` project for each of `cursor`, `claude`, and `codex`, when `install.sh --platform <platform>` runs from that copy, then `## Capability Map` appears in the installed `.cursor/rules/writ.mdc`, inside the `<!-- writ:start -->` to `<!-- writ:end -->` block of `CLAUDE.md`, and inside that block of `AGENTS.md` `[AC-5.1]`
- [ ] Given the installed Codex Writ block in `AGENTS.md`, when it is searched for the substring `adapters/`, then the search finds no match `[AC-5.2]`
- [ ] Given each installed capability map, when its rows are read, then it has a `canvas-preview` row and a `Plan Mode` row, and the Claude Code map's `Plan Mode` row names `EnterPlanMode` `[AC-5.3]`
- [ ] Given `.writ/issues/improvements/2026-10-21-adapter-mappings-never-reach-installed-projects.md`, when its `## Resolution` section is read, then it names spec `2026-10-22-generated-platform-trees`, the three install paths (`.cursor/rules/writ.mdc`, the `CLAUDE.md` Writ block, the `AGENTS.md` Writ block), and the date `2026-10-22`, and its `> **spec_ref:**` line is `.writ/specs/2026-10-22-generated-platform-trees/spec.md` `[AC-5.4]`
- [ ] Given the `## Installation` sections of `adapters/codex.md` and `adapters/claude-code.md`, when they are searched for a sentence that tells an installed user to read `adapters/<x>.md` for tool mappings, then each such sentence is replaced by one that points at the Capability Map in the file the platform loads, and no other line in either section changes `[AC-5.5]`

## Implementation Tasks

- [ ] 5.1 Write `scripts/tests/test_install_platform_trees.sh` in the style of `scripts/tests/test_install_update_claude_parity.sh`. Commit a copy of the working tree into a temp source repo. Run `install.sh --platform cursor`, `claude`, and `codex` from that copy into three fresh `git init` projects. Assert only on the installed files: the map in the three locations, no `adapters/` in the Codex block, a `canvas-preview` and a `Plan Mode` row in each map, and `EnterPlanMode` in the Claude Code `Plan Mode` row. Red check: run the test once on a second temp source copy with `## Capability Map` stripped from the three source root files (`cursor/writ.mdc`, `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`). Confirm it fails on the map assertions, then discard that copy. `[AC-5.1, AC-5.2, AC-5.3]`
- [ ] 5.2 Make the test pass on the final tree: `bash scripts/tests/test_install_platform_trees.sh`, run outside the sandbox. If an assertion fails, fix the generator or the template and rerun. Do not change an assertion to fit the output. `[AC-5.1, AC-5.2, AC-5.3]`
- [ ] 5.3 Search the `## Installation` sections of `adapters/codex.md` and `adapters/claude-code.md` for `adapters/`. As of 2026-10-22 neither section contains a sentence that sends an installed user to an adapter file, so make no edit there and record that result for 5.4. If a sentence does match, replace only that sentence, found by its text, with one that points at the Capability Map in `AGENTS.md` (codex) or `CLAUDE.md` (claude). Confirm with `git diff` that no other line in either section changed. `[AC-5.5]`
- [ ] 5.4 Append `## Resolution` to `.writ/issues/improvements/2026-10-21-adapter-mappings-never-reach-installed-projects.md`, dated 2026-10-22. Name spec `2026-10-22-generated-platform-trees`, the three observed install paths, and the result of the 5.2 run. Set the `> **spec_ref:**` line to `.writ/specs/2026-10-22-generated-platform-trees/spec.md`, the format other closed issues use. `[AC-5.4]`
- [ ] 5.5 Run the verification set on the final tree, outside the sandbox: `uv run --python 3.9 pytest`; `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` with no `FAIL` lines; `bash scripts/eval.sh` with 0 findings, which includes `check_platform_trees` passing. Record the results in What Was Built. `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

## Notes

- **Source copy.** `install.sh` uses the tree above its own `scripts/` directory when `SKILL.md` and `commands/` are present. The test therefore runs the copy's `scripts/install.sh`, not the repo's. Commit the copy as the parity test does. `update.sh` clones `WRIT_REPO`, so the commit matters if an update case is added later.
- **Run outside the sandbox.** Temp projects run `git init`. Never point the test at the Writ repo.
- **Block extraction.** Take the Writ block between `<!-- writ:start -->` and `<!-- writ:end -->`. Reuse the marker-split logic in the parity test's `BLOCK_PY`, or copy it. The Cursor file has no markers, so search all of `.cursor/rules/writ.mdc`.
- **Row matching.** Match each row by its first cell with backticks stripped. The generated map writes `` `Plan Mode` `` and `` `canvas-preview` ``.
- **Installed files only.** A test that reads `$SRC` proves nothing about what installs. The red check in 5.1 guards this.
- **Adapter prose.** The one-sentence edit in 5.3 is the only prose change this story allows. The line in `adapters/codex.md` § Installation that says "see Story 4 merge semantics" refers to a different plan. It does not point at tool mappings, so leave it alone.
- **Risks.** A codex check that searches all of `AGENTS.md` can pass on map text outside the Writ block. Keep the search inside the markers.
- **Integration.** Stories 1 to 4 supply the map, the generated Codex template, the Plan Mode and `canvas-preview` rows, and `check_platform_trees` in `eval.sh`. `2026-10-22-plugin-distribution` later adds plugin targets to this evidence pattern.

---

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 14 Install evidence test; Rule 5 Capability Map section; Rule 9 Plan Mode rows)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Installed Cursor project; Installed Claude Code project; Installed Codex project)
