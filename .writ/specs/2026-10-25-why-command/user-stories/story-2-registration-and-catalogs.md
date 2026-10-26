# Story 2: Registration and Catalogs

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** user reading a catalog on any platform, and the maintainer who keeps the generated trees honest
**I want to** find `/why` on every surface that lists commands, with generated files produced by their generators
**So that** every platform ships the command and a missed or stale surface fails a test

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.4

- [ ] Given `.writ/manifest.yaml`, when `commands:` is read, then it holds a `why` entry with `file: commands/why.md`, `category: planning`, and the purpose and tags from technical-spec.md → Registration Edits, placed between `verify-spec` and `writ`, and `commands:` stays sorted by name `[AC-2.1]`
- [ ] Given the generators, when `bash scripts/gen-skill.sh --check` and `python3 scripts/gen-platform-trees.py --check` run, then each prints `pass` as its first stdout line, and `SKILL.md`, `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, `cursor/plugin/commands/why.md`, and `plugins/writ/commands/why.md` exist with `/why` present, none of them hand-edited `[AC-2.2]`
- [ ] Given `README.md` § Commands → Planning & Specification, `adapters/cursor.md` § Directory Structure, both allowlists in `commands/status.md`, and the `high` row in `.writ/docs/model-tiers.md`, when each is read, then README has a `/why` row after `/research`, the cursor tree has `why.md` between `verify-spec.md` and `writ.md` with the `#` column aligned and the count comment at `(34)`, the slash list has `` `/why` `` after `` `/research` `` and the bare list has `` `why` `` after `` `research` ``, and the `high` row lists `why` between `security-audit` and `writ` with its count at `(17)` `[AC-2.3]`
- [ ] Given `scripts/eval-command-structure.py` and `scripts/tests/test_front_door.py`, when the full test suite and `bash scripts/eval.sh` run, then `ROWS` holds the `commands/why.md` heading row for `Confidence Tiers` and the frontmatter row for `entry_level`, `CURSOR_COUNT` reads `"(34)"`, pytest and the bash tests pass, and eval reports 0 findings `[AC-2.4]`

## Implementation Tasks

- [ ] 2.1 Write the failing test first. Add `test_registration` to `scripts/tests/test_why_command.py` covering every surface in technical-spec.md → Registration Edits; run the two `--check` commands through `subprocess.run` with an argv list and `cwd` at the repository root, as `scripts/tests/test_front_door.py` does. Change `CURSOR_COUNT` in `scripts/tests/test_front_door.py` to `"(34)"`. Run both and confirm they fail on the missing registration `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [ ] 2.2 Add the `why` entry to `.writ/manifest.yaml` between `verify-spec` and `writ`. Re-read the block to confirm `commands:` is still sorted `[AC-2.1]`
- [ ] 2.3 Regenerate. Run `bash scripts/gen-skill.sh`, then `python3 scripts/gen-platform-trees.py`. Confirm both `--check` commands print `pass`. Do not hand-edit any generated file `[AC-2.2]`
- [ ] 2.4 Add the `/why` row to `README.md` § Commands → Planning & Specification after the `/research` row, with the text from technical-spec.md → Registration Edits. Locate the table by its heading `[AC-2.3]`
- [ ] 2.5 Update the hand-maintained lists. In `adapters/cursor.md` § Directory Structure add the `why.md` line and change `(33)` to `(34)`. In `commands/status.md` add `/why` and `why` to the two allowlists. In `.writ/docs/model-tiers.md` add `why` to the `high` row and change `(16)` to `(17)`. Check each current count before editing; stop and report a mismatch `[AC-2.3]`
- [ ] 2.6 Add the two `commands/why.md` rows to `ROWS` in `scripts/eval-command-structure.py`, in the shape of the `commands/writ.md` rows `[AC-2.4]`
- [ ] 2.7 Verify. Run `uv run --python 3.9 pytest` alone, then the bash test loop, then `bash scripts/eval.sh` outside any sandbox. Confirm `test_registration`, `test_cursor_tree` in `scripts/tests/test_platform_neutral_names.py`, and `scripts/tests/test_front_door.py` pass, and eval reports 0 findings. Run `git diff --stat` and confirm no edits under `.claude/` or `.cursor/` `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`

## Notes

- **Generated files.** `SKILL.md` comes from `bash scripts/gen-skill.sh`. `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, and both plugin trees come from `python3 scripts/gen-platform-trees.py`. Change the manifest or the source, then regenerate. A hand edit fails `--check`.
- **Edit by heading.** Locate every edit by section heading or list text, never by line number.
- **Status lists.** The allowlists are ordered by use, not by name. Put `why` next to `research`, its closest neighbour.
- **Repository instruction files.** The repository's `CLAUDE.md` and `AGENTS.md` list no commands. Leave them.
- **Source edits only.** `.claude/` and `.cursor/` are symlinks to the product source. Never edit them or run `install.sh` on this repository.
- **Concurrent specs.** Sibling Phase 15 specs may add manifest or skill entries. Rebase onto the phase branch and regenerate if `--check` reports a stale file that this story did not touch.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** [Happy path]
- **Business rules:** [Generated files are regenerated, Entry level]
- **Experience:** [Entry Point]
