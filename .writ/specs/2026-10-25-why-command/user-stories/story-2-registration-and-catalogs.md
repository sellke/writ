# Story 2: Registration and Catalogs

> **Status:** Completed ✅
> **Commit:** d47bcec2298f344b483bd4d8bb50153c59b9a3dd
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** user reading a catalog on any platform, and the maintainer who keeps the generated trees honest
**I want to** find `/why` on every surface that lists commands, with generated files produced by their generators
**So that** every platform ships the command and a missed or stale surface fails a test

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.4

- [x] Given `.writ/manifest.yaml`, when `commands:` is read, then it holds a `why` entry with `file: commands/why.md`, `category: planning`, and the purpose and tags from technical-spec.md → Registration Edits, placed between `verify-spec` and `writ`, and `commands:` stays sorted by name `[AC-2.1]`
- [x] Given the generators, when `bash scripts/gen-skill.sh --check` and `python3 scripts/gen-platform-trees.py --check` run, then each prints `pass` as its first stdout line, and `SKILL.md`, `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, `cursor/plugin/commands/why.md`, and `plugins/writ/commands/why.md` exist with `/why` present, none of them hand-edited `[AC-2.2]`
- [x] Given `README.md` § Commands → Planning & Specification, `adapters/cursor.md` § Directory Structure, both allowlists in `commands/status.md`, and the `high` row in `.writ/docs/model-tiers.md`, when each is read, then README has a `/why` row after `/research`, the cursor tree has `why.md` between `verify-spec.md` and `writ.md` with the `#` column aligned and the count comment at `(34)`, the slash list has `` `/why` `` after `` `/research` `` and the bare list has `` `why` `` after `` `research` ``, and the `high` row lists `why` between `security-audit` and `writ` with its count at `(17)` `[AC-2.3]`
- [x] Given `scripts/eval-command-structure.py` and `scripts/tests/test_front_door.py`, when the full test suite and `bash scripts/eval.sh` run, then `ROWS` holds the `commands/why.md` heading row for `Confidence Tiers` and the frontmatter row for `entry_level`, `CURSOR_COUNT` reads `"(34)"`, pytest and the bash tests pass, and eval reports 0 findings `[AC-2.4]`

## Implementation Tasks

- [x] 2.1 Write the failing test first. Add `test_registration` to `scripts/tests/test_why_command.py` covering every surface in technical-spec.md → Registration Edits; run the two `--check` commands through `subprocess.run` with an argv list and `cwd` at the repository root, as `scripts/tests/test_front_door.py` does. Change `CURSOR_COUNT` in `scripts/tests/test_front_door.py` to `"(34)"`. Run both and confirm they fail on the missing registration `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [x] 2.2 Add the `why` entry to `.writ/manifest.yaml` between `verify-spec` and `writ`. Re-read the block to confirm `commands:` is still sorted `[AC-2.1]`
- [x] 2.3 Regenerate. Run `bash scripts/gen-skill.sh`, then `python3 scripts/gen-platform-trees.py`. Confirm both `--check` commands print `pass`. Do not hand-edit any generated file `[AC-2.2]`
- [x] 2.4 Add the `/why` row to `README.md` § Commands → Planning & Specification after the `/research` row, with the text from technical-spec.md → Registration Edits. Locate the table by its heading `[AC-2.3]`
- [x] 2.5 Update the hand-maintained lists. In `adapters/cursor.md` § Directory Structure add the `why.md` line and change `(33)` to `(34)`. In `commands/status.md` add `/why` and `why` to the two allowlists. In `.writ/docs/model-tiers.md` add `why` to the `high` row and change `(16)` to `(17)`. Check each current count before editing; stop and report a mismatch `[AC-2.3]`
- [x] 2.6 Add the two `commands/why.md` rows to `ROWS` in `scripts/eval-command-structure.py`, in the shape of the `commands/writ.md` rows `[AC-2.4]`
- [x] 2.7 Verify. Run `uv run --python 3.9 pytest` alone, then the bash test loop, then `bash scripts/eval.sh` outside any sandbox. Confirm `test_registration`, `test_cursor_tree` in `scripts/tests/test_platform_neutral_names.py`, and `scripts/tests/test_front_door.py` pass, and eval reports 0 findings. Run `git diff --stat` and confirm no edits under `.claude/` or `.cursor/` `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`

## Notes

- **Generated files.** `SKILL.md` comes from `bash scripts/gen-skill.sh`. `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, and both plugin trees come from `python3 scripts/gen-platform-trees.py`. Change the manifest or the source, then regenerate. A hand edit fails `--check`.
- **Edit by heading.** Locate every edit by section heading or list text, never by line number.
- **Status lists.** The allowlists are ordered by use, not by name. Put `why` next to `research`, its closest neighbour.
- **Repository instruction files.** The repository's `CLAUDE.md` and `AGENTS.md` list no commands. Leave them.
- **Source edits only.** `.claude/` and `.cursor/` are symlinks to the product source. Never edit them or run `install.sh` on this repository.
- **Concurrent specs.** Sibling Phase 15 specs may add manifest or skill entries. Rebase onto the phase branch and regenerate if `--check` reports a stale file that this story did not touch.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** [Happy path]
- **Business rules:** [Generated files are regenerated, Entry level]
- **Experience:** [Entry Point]

---

## What Was Built

**Implementation Date:** 2026-10-26

### Files Created

1. **`cursor/plugin/commands/why.md`**, **`plugins/writ/commands/why.md`** — generated by `python3 scripts/gen-platform-trees.py`; not hand-edited.

### Files Modified

- **`.writ/manifest.yaml`** (`commands:`) — `why` entry between `verify-spec` and `writ`, purpose and tags from technical-spec.md → Registration Edits.
- **`SKILL.md`** — regenerated by `bash scripts/gen-skill.sh`.
- **`claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, `plugins/writ/.claude-plugin/plugin.json`, `cursor/plugin/commands/status.md`, `plugins/writ/commands/status.md`, `plugins/writ/commands/writ.md`** — regenerated by `python3 scripts/gen-platform-trees.py` (the plugin `writ.md` copy now namespaces the interim `/why` mention as `/writ:why`; Story 3 removes that sentence).
- **`README.md`** (§ Commands → Planning & Specification) — `/why` row after `/research`.
- **`adapters/cursor.md`** (§ Directory Structure) — `why.md  # /why` line between `verify-spec.md` and `writ.md`, column aligned; count `(33)` → `(34)`.
- **`commands/status.md`** — `/why` after `/research` in the slash allowlist; `why` after `research` in § Maintainer Note: Command Allowlist.
- **`.writ/docs/model-tiers.md`** — `why` in the `high` row between `security-audit` and `writ`; count `(16)` → `(17)`.
- **`scripts/eval-command-structure.py`** (`ROWS`) — `commands/why.md` heading `Confidence Tiers` (`check_command_structure`) and frontmatter `entry_level` (`check_entry_level`).
- **`scripts/tests/test_why_command.py`** — `test_registration` (AC-2.1–AC-2.4).
- **`scripts/tests/test_front_door.py`** — `CURSOR_COUNT` "(34)", `HIGH_COUNT` "(17)", `test_manifest` neighbor pin (DEV-003).
- **`scripts/tests/test_platform_neutral_names.py`**, **`scripts/tests/test_gen_platform_trees.py`** — Planning-table neighbor pins include `/why` (DEV-003).

### Implementation Decisions

1. **Counts checked before editing** — the cursor tree read `(33)` and the model-tiers `high` row `(16)`, matching technical-spec.md → Current State.
2. **Generated files only through generators** — both `--check` commands print `pass`; `git diff --stat` shows no edit under `.claude/` or `.cursor/`.
3. **`test_registration` pins the exact README row text, the codex row, both `ROWS` entries (through the checker's PASS lines), and `CURSOR_COUNT`** — Gate 3 review recommendations, applied before completion.

### Test Results

**Verification:** Automated, test-first (`test_registration` red on the missing manifest entry; green after the edits).
**Coverage:** Not measured by the script (no coverage report; markdown and test changes only).

- ✅ Targeted: `uv run --python 3.9 pytest -q scripts/tests/test_why_command.py scripts/tests/test_front_door.py scripts/tests/test_platform_neutral_names.py scripts/tests/test_gen_platform_trees.py scripts/tests/test_agent_cli_contract.py` → 447 passed.
- ✅ First full run (before the DEV-003 pin fixes): pytest 3067 passed, 2 failed (`test_gen_platform_trees.py::test_codex_template`, the pin DEV-003 moved; `test_agent_cli_contract.py::test_smoke_leaves_repo_unchanged[app-verify.py touched]`, which passed on rerun: gate scripts were writing `.writ/state/` concurrently); bash loop 0 FAIL; eval 4 findings, all `review-override` from `scripts/ac-trace.py` (AC-1.5 uncited; AC-2.5 from the front-door spec attributed to this spec by a comment naming this spec's folder id). Both fixed. Full re-run recorded in the spec-level verification.
- ✅ `python3 scripts/ac-trace.py check --spec .writ/specs/2026-10-25-why-command --repo .` → no findings.
- ✅ Gate 0 arch-check: pass (rederived proceed). Gate 2: no linter configured; arch-lint: none — see .writ/docs/architecture-lint.md; build-smoke unverifiable (unsupported_stack). Gate 2.5: cross-component, 3 crossings (`SKILL.md`, `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, all generated and named in AC-2.2), route review-agent. Gate 3 review-override: pass. Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable (no_coverage_report); authenticity: pass (the `subprocess` calls give the file a project-script reference). Gate 4.5 app-verify: unverifiable (no_recipe). Gate 5 docs-check: unverifiable (no_public_exports).

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-003)
- **Security:** Clean (markdown and tests; subprocess calls use argv lists)
- **Boundary Compliance:** 3 crossings, all generated files the story names
- gate3-route: review-agent (outside_boundary SKILL.md; outside_boundary claude-code/CLAUDE.md; outside_boundary codex/AGENTS.md.template)
