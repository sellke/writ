# Story 5: Install Evidence and Issue Closure

> **Status:** Completed ✅ (2026-10-23)
> **Priority:** High
> **Dependencies:** Story 4

## User Story

**As a** maintainer closing the adapter-mappings issue, and a user of an installed Cursor, Claude Code, or Codex project
**I want to** have a test install Writ into fresh projects and check the capability map in the root file each platform loads
**So that** the issue closes on installed-file evidence, and the installed agent resolves each capability without reading `adapters/`

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [x] Given a committed temp copy of the working tree and a fresh `git init` project for each of `cursor`, `claude`, and `codex`, when `install.sh --platform <platform>` runs from that copy, then `## Capability Map` appears in the installed `.cursor/rules/writ.mdc`, inside the `<!-- writ:start -->` to `<!-- writ:end -->` block of `CLAUDE.md`, and inside that block of `AGENTS.md` `[AC-5.1]`
- [x] Given the installed Codex Writ block in `AGENTS.md`, when it is searched for the substring `adapters/`, then the search finds no match `[AC-5.2]`
- [x] Given each installed capability map, when its rows are read, then it has a `canvas-preview` row and a `Plan Mode` row, and the Claude Code map's `Plan Mode` row names `EnterPlanMode` `[AC-5.3]`
- [x] Given `.writ/issues/improvements/2026-10-21-adapter-mappings-never-reach-installed-projects.md`, when its `## Resolution` section is read, then it names spec `2026-10-22-generated-platform-trees`, the three install paths (`.cursor/rules/writ.mdc`, the `CLAUDE.md` Writ block, the `AGENTS.md` Writ block), and the date `2026-10-22`, and its `> **spec_ref:**` line is `.writ/specs/2026-10-22-generated-platform-trees/spec.md` `[AC-5.4]`
- [x] Given the `## Installation` sections of `adapters/codex.md` and `adapters/claude-code.md`, when they are searched for a sentence that tells an installed user to read `adapters/<x>.md` for tool mappings, then each such sentence is replaced by one that points at the Capability Map in the file the platform loads, and no other line in either section changes `[AC-5.5]`

## Implementation Tasks

- [x] 5.1 Write `scripts/tests/test_install_platform_trees.sh` in the style of `scripts/tests/test_install_update_claude_parity.sh`. Commit a copy of the working tree into a temp source repo. Run `install.sh --platform cursor`, `claude`, and `codex` from that copy into three fresh `git init` projects. Assert only on the installed files: the map in the three locations, no `adapters/` in the Codex block, a `canvas-preview` and a `Plan Mode` row in each map, and `EnterPlanMode` in the Claude Code `Plan Mode` row. Red check: run the test once on a second temp source copy with `## Capability Map` stripped from the three source root files (`cursor/writ.mdc`, `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`). Confirm it fails on the map assertions, then discard that copy. `[AC-5.1, AC-5.2, AC-5.3]`
- [x] 5.2 Make the test pass on the final tree: `bash scripts/tests/test_install_platform_trees.sh`, run outside the sandbox. If an assertion fails, fix the generator or the template and rerun. Do not change an assertion to fit the output. `[AC-5.1, AC-5.2, AC-5.3]`
- [x] 5.3 Search the `## Installation` sections of `adapters/codex.md` and `adapters/claude-code.md` for `adapters/`. As of 2026-10-22 neither section contains a sentence that sends an installed user to an adapter file, so make no edit there and record that result for 5.4. If a sentence does match, replace only that sentence, found by its text, with one that points at the Capability Map in `AGENTS.md` (codex) or `CLAUDE.md` (claude). Confirm with `git diff` that no other line in either section changed. `[AC-5.5]`
- [x] 5.4 Append `## Resolution` to `.writ/issues/improvements/2026-10-21-adapter-mappings-never-reach-installed-projects.md`, dated 2026-10-22. Name spec `2026-10-22-generated-platform-trees`, the three observed install paths, and the result of the 5.2 run. Set the `> **spec_ref:**` line to `.writ/specs/2026-10-22-generated-platform-trees/spec.md`, the format other closed issues use. `[AC-5.4]`
- [x] 5.5 Run the verification set on the final tree, outside the sandbox: `uv run --python 3.9 pytest`; `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` with no `FAIL` lines; `bash scripts/eval.sh` with 0 findings, which includes `check_platform_trees` passing. Record the results in What Was Built. `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 14 Install evidence test; Rule 5 Capability Map section; Rule 9 Plan Mode rows)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Installed Cursor project; Installed Claude Code project; Installed Codex project)

---

## What Was Built

**Implementation Date:** 2026-10-23

### Files Created

1. **`scripts/tests/test_install_platform_trees.sh`** (163 lines)
   - Install evidence test in the style of `test_install_update_claude_parity.sh`: `set -euo pipefail`, `mktemp` work dir normalized with `pwd` (macOS `TMPDIR` ends in `/`), `trap` cleanup, `fail`/`ok`, `commit_src`, `BLOCK_PY` copied from the parity test. It tars the working tree (excluding `.git`, `.cursor`, `.claude`, `.codex`, `.writ`, `.writ-lanes-*`, caches), re-adds `.writ/docs/*.md`, commits the copy, and for each of `cursor`, `claude`, `codex` makes a fresh `git init -b main` project and runs `bash "$SRC/scripts/install.sh" --platform <p> --no-commit` from inside it, failing unless the output says `Using local writ: $SRC` (the copy, not a clone, was the source). Eight assertion groups on installed files only: `.cursor/rules/writ.mdc` has exactly one `## Capability Map` heading and `canvas-preview` and `Plan Mode` rows (`map_row`: first cell, backticks stripped, scoped under the heading to the next `## `); the `CLAUDE.md` Writ block (extracted between the markers by `writ_block`) has the heading, both rows, and `EnterPlanMode` in its `Plan Mode` row; the `AGENTS.md` Writ block has the heading, both rows, and no `adapters/` substring. The source copy is read only for a file-existence check.

### Files Modified

- **`.writ/issues/improvements/2026-10-21-adapter-mappings-never-reach-installed-projects.md`** (header; new `## Resolution`)
  - `> **spec_ref:**` → `.writ/specs/2026-10-22-generated-platform-trees/spec.md`. `## Resolution` dated 2026-10-22 names the spec and Story 5, how each root file now carries the map, the test and its three observed install paths (`.cursor/rules/writ.mdc`; the `CLAUDE.md` Writ block; the `AGENTS.md` Writ block), the 5.2 result (8 assertions), the stripped-copy red check, the CI half of the issue's Expected Outcome (`gen-platform-trees.py --check` through `check_platform_trees`, Story 4), and the adapter Installation audit. `## Resolution` is a bare last H2, the shape `test_issue_closure_wiring.py` and `test_front_door.py` parse.
- **`.writ/specs/2026-10-22-generated-platform-trees/spec-lite.md`** — Test Strategy line names `--no-commit` (DEV-010).
- **`.writ/specs/2026-10-22-generated-platform-trees/drift-log.md`** — Story 5 section (DEV-010).
- Not modified: `adapters/codex.md`, `adapters/claude-code.md` — task 5.3's search of both `## Installation` sections for a sentence that sends an installed user to `adapters/<x>.md` for tool mappings found none (the Codex section's "see Story 4 merge semantics" line is a merge note, per the story Notes), so no edit; `git diff -- adapters/` is empty and the Resolution records the result (AC-5.5 satisfied vacuously). Also unchanged: the generators, templates, and install scripts — the test passed on the real tree first time, so task 5.2 needed no fix and no assertion was changed to fit output.

### Implementation Decisions

1. **Installed files only** — every assertion reads a file the install wrote, or a block extracted from one; `$SRC` is checked only for the files the install needs. The red check (task 5.1) proves it: a source copy with `## Capability Map` stripped from `cursor/writ.mdc`, `claude-code/CLAUDE.md`, and `codex/AGENTS.md.template` fails on the heading assertion of each stripped file.
2. **Block extraction inside the markers** — `writ_block` writes only the lines between `<!-- writ:start -->` and `<!-- writ:end -->`, so map text outside the block cannot satisfy a Claude Code or Codex check (the story's risk note; the reviewer's outside-marker probe extracted nothing).
3. **Exactly one heading** — stricter than AC-5.1's "appears"; it also guards a doubled block (a duplicate heading in a copy's `cursor/writ.mdc` fails with `found 2`).
4. **`--no-commit` on each install** — `NO_COMMIT` gates only the install's trailing `git commit`; every file written is identical; the parity sibling passes the same flag; it keeps the install's commit output out of failure messages (DEV-010).
5. **`Using local writ: $SRC` is asserted** — `install.sh` would otherwise fall back to cloning `WRIT_REPO`; the assertion fails that path, so the test cannot reach the network or the repo silently.
6. **`.writ-lanes-*` excluded from the tar** — the primary checkout holds `/implement-phase` lane worktrees; without the exclude each lane's full tree would be copied into the temp source (the parity sibling has the same trait; left as is, outside this story's files).

### Test Results

**Verification:** Automated, test-first. Red (task 5.1, on scratch copies run from the copy, never the worktree): all three root files stripped of `## Capability Map` → `FAIL: cursor: .cursor/rules/writ.mdc: expected one '## Capability Map' heading, found 0`; each file stripped alone fails on its own heading assertion. Mutation kills: `EnterPlanMode` → `SomeOtherTool` in the copy's `claude-code/CLAUDE.md` → `FAIL: claude: the Plan Mode row does not name EnterPlanMode: …`; `Read adapters/codex.md for tool mappings.` appended to the copy's `codex/AGENTS.md.template` → `FAIL: codex: the AGENTS.md Writ block mentions adapters/: 147:…`; a duplicate heading in the copy's `cursor/writ.mdc` → `found 2` (reviewer); map text placed before `<!-- writ:start -->` is invisible to the extractor (reviewer). Green on the real tree: 8 assertions passed, exit 0, about 10s.
**Coverage:** Not measured by the script (`test-integrity.py coverage`: unverifiable, no_coverage_report).

- ✅ `bash scripts/tests/test_install_platform_trees.sh` → 8 PASS lines, `All 8 install platform-trees assertions passed.`, exit 0 (orchestrator's own run, inside the sandbox: `git init` was not blocked).
- ✅ `python3 scripts/gen-platform-trees.py --check` → `pass` (five zeros) before and after the issue edit.
- ✅ Full pytest (3.9), on the lane tree after the phase-branch merge (9ba1e36): 2913 passed, 2 skipped (150s).
- ✅ Bash tests, same tree: 47 run, 0 failed (includes `test_install_platform_trees.sh` and the five `test_install_update_*.sh`; temp projects only).
- ✅ `bash scripts/eval.sh`, same tree (outside the sandbox): Findings 0, Run errors 0 (`.writ/state/eval-20261023-080557.md`); `## platform-trees` PASS.
- ✅ Gate 0 arch-check: pass (rederived proceed; attempt 1's run and the replay with explicit paths). Gate 2: `bash -n` clean; no linter configured; arch-lint: none — see .writ/docs/architecture-lint.md; build-smoke unverifiable (unsupported_stack). Gate 2.5: cross-component, 0 crossings (both files owned; route evaluator-agent) — Gate 3 ran review-agent instead, because the first crossings run was fed the changed set as one space-joined token (zsh does not split an unquoted variable) and routed review-agent; the review-agent rubric is a superset of the evaluator's, so the stricter review stands. Gate 3 review-override: unverifiable (no_coverage_report). Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable (no_coverage_report); authenticity: `test_imports_no_source` on the new bash test, the known checker false positive for bash tests (open issue `.writ/issues/improvements/2026-09-03-test-integrity-authenticity-flags-every-bash-test.md`); carried on the red check and the mutation kills above, not DEGRADED. Gate 4.5 app-verify: unverifiable (no_recipe). Gate 5 docs-check: unverifiable (no_public_exports).

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-010)
- **Security:** Low (temp-dir-only writes with trap cleanup; no network — the `Using local writ:` assertion fails the clone path; no repo mutation, verified by `git status` after the run)
- **Boundary Compliance:** both changed files are owned by the Gate 0.5 map and named by tasks 5.1 and 5.4; adapters untouched (task 5.3 vacuous); no deviation, no violation.
- gate3-route: review-agent (see Gate 2.5 above). review-panel: unverifiable (platform_cannot_spawn_other_vendors). jev-shadow: unverifiable (no_api_key). arch-lint: none — see .writ/docs/architecture-lint.md.
- The review agent re-ran the test (8/8) and `--check`, probed five failure modes on scratch copies, read both adapter Installation sections, and checked the Resolution against the issue-closure consumers (`test_issue_closure_wiring.py`, `test_front_door.py`, `goal-emit.py`). Its one Minor nit (the header comment overstated "nothing reads the source copy") and its `.writ-lanes-*` tar-exclude recommendation were applied to the new test post-review and re-run (8/8). Its note that the cursor `canvas-preview` and `Plan Mode` rows carry the degradation text in two cells is Story 2 output under DEV-003, already logged.
- Coding agent and review agent ran as nested `general-purpose` spawns with the prompt templates from `agents/coding-agent.md` and `agents/review-agent.md`, working directly in the lane worktree; the orchestrator committed.

### Deviations from Spec

- **[DEV-010] Install evidence test passes `--no-commit`** — Severity: Small
  - Spec said: AC-5.1 "when `install.sh --platform <platform>` runs from that copy"; Rule 14 names no flags.
  - Reality: `install.sh --platform <p> --no-commit`; the flag skips only the install's own commit and the files written are the same.
  - Resolution: Auto-amended; spec-lite Test Strategy line names the flag.
