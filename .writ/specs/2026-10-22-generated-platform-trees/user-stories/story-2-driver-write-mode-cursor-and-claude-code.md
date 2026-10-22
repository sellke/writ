# Story 2: Driver Write Mode for the Cursor and Claude Code Root Files

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer who edits an adapter or agent file
**I want to** run `python3 scripts/gen-platform-trees.py` once and get `cursor/writ.mdc` and `claude-code/CLAUDE.md` regenerated with each platform's capability map, plus the sub-generators' outputs
**So that** an installed Cursor or Claude Code project's agent resolves every capability in the root file it already loads, without reading `adapters/`

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given `system-instructions.md` with its `alwaysApply: true` frontmatter and the Cursor adapter, when the driver writes `cursor/writ.mdc`, then the file starts with `---`, `alwaysApply: true`, `---`, then the generated-file comment, then the `system-instructions.md` body with its own frontmatter removed, then the Cursor `## Capability Map` as the last section, and its `## Prime Directive` section is byte-equal to the source's `## Prime Directive` section `[AC-2.1]`
- [ ] Given the Cursor and Claude Code tool tables read by Story 1's parser, when the driver renders each `## Capability Map`, then the section opens with "Commands name capabilities; this table maps them to this platform.", has a `Capability | On this platform | When unavailable` table with one row per neutral name in the adapter's row order, and each "When unavailable" cell holds the notes-cell sentence that starts with `No renderer:`, `If the platform`, or `No agent-side`, or `—` when none does `[AC-2.2]`
- [ ] Given the `{capability_map}` slot added to `gen-claude-md.py`'s TEMPLATE after the Commands table, when the driver writes `claude-code/CLAUDE.md`, then `## Capability Map` with the Claude Code rows follows the Commands table, and `python3 scripts/gen-claude-md.py --check` prints `pass` `[AC-2.3]`
- [ ] Given a clean tree, when the driver runs in write mode, then it prints `pass`, one `wrote <path>` line per file, and `gen-platform-trees: pass (…)`; given any reason, or a sub-generator that exits 2 or higher, then it prints `fail`, folds each sub-generator reason as `reason: <gen>: <kind> <stem>` (or `reason: <gen> --check exited <rc>`), and writes no file `[AC-2.4]`
- [ ] Given the hand-maintained `cursor/writ.mdc` at git HEAD, when the first write replaces it, then the diff is recorded in this story's What Was Built, and every sentence of the old file is either present in the new file or listed there as a bug to fix `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write failing tests in `scripts/tests/test_gen_platform_trees.py`: `test_writ_mdc` (composition and byte-equal Prime Directive), `test_claude_md_map` (map after the Commands table; `gen-claude-md.py --check` prints `pass`), a write-mode check-shape case (`pass` with `wrote` lines; a seeded bad row writes nothing), and a sub-generator exit-2 case (`fail`, nothing written). Each case runs on a temp copy of the tree. Run them and confirm all fail on the current tree `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [ ] 2.2 Add `capability_map(adapter, root)` to `scripts/gen-platform-trees.py` on Story 1's `parse_adapter`: the lead sentence, the three-column table, adapter row order, and the degradation-sentence rule. Check the rendered Cursor and Claude Code maps against the rule by reading the output `[AC-2.2]`
- [ ] 2.3 Write `cursor/writ.mdc` in write mode: `---\nalwaysApply: true\n---\n`, the generated-file comment naming the driver and its sources, the `system-instructions.md` body with its frontmatter removed, then the Cursor map. Make `test_writ_mdc` pass `[AC-2.1]`
- [ ] 2.4 Add the `{capability_map}` slot to `scripts/gen-claude-md.py`'s TEMPLATE after the Commands table. Load `capability_map` by path with `importlib.util.spec_from_file_location`. Regenerate `claude-code/CLAUDE.md`. Make `test_claude_md_map` pass and keep `test_gen_claude_md.py` and `test_eval_claude_md.sh` green `[AC-2.3]`
- [ ] 2.5 Add write mode to the driver. Run `--check` on the driver's own checks and on all three sub-generators (`gen-claude-md.py`, `gen-claude-agents.py`, `gen-codex-agent-tomls.py`) before writing anything. Fold each `reason:` line as `reason: <gen>: <kind> <stem>`. Any reason or any exit of 2 or higher prints `fail` (with `reason: <gen> --check exited <rc>` for the exit case) and writes nothing. Otherwise write `cursor/writ.mdc`, write `claude-code/CLAUDE.md` and the two agent outputs, and print one `wrote <path>` per file plus the summary line. Make the check-shape and sub-generator cases from 2.1 pass `[AC-2.4]`
- [ ] 2.6 Diff the hand copy against the first generated `cursor/writ.mdc`: `git show HEAD:cursor/writ.mdc` against the new file. Record the diff in a What Was Built section of this story. Any sentence the new file drops is a bug: fix the generator or `system-instructions.md`, regenerate, and note the fix in What Was Built `[AC-2.5]`
- [ ] 2.7 Verify: run the driver twice and confirm the second run leaves the tree byte-identical; `uv run --python 3.9 pytest`; `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` with no `FAIL` lines; `python3 scripts/gen-claude-md.py --check` prints `pass`; `bash scripts/eval.sh` outside any sandbox reports 0 findings `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

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

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Upstream error)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 1 Driver CLI, default write mode and exit codes; Rule 6 `cursor/writ.mdc` composition; Rule 7 `claude-code/CLAUDE.md` slot; Rule 12 generated-file comment)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Clean tree; Installed Cursor project; Installed Claude Code project)
