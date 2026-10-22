# Story 2: Registration and Catalogs

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** new user reading the README or a platform catalog, and the maintainer who keeps the generated catalogs honest **I want to** find `/writ` first on every surface, with the generated files produced by their generators **So that** every catalog agrees on the front door, and a missed or stale surface fails a test.

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given `.writ/manifest.yaml`, when `categories:` and `commands:` are read, then `categories:` starts with `- id: entry` and `label: "Start here"`, and `commands:` holds a `writ` entry with `file: commands/writ.md`, `category: entry`, and `tags: [entry, routing]`, placed after `verify-spec` and before `writ-design` `[AC-2.1]`
- [ ] Given `scripts/gen-claude-md.py` with its TEMPLATE edit, `SKILL.md`, and `claude-code/CLAUDE.md`, when both generators run and both `--check` commands run, then each `--check` prints `pass` as its first line, `SKILL.md` renders the `entry` table first with a `/writ` row, and `claude-code/CLAUDE.md` has a "Start with" line that names `/writ "<what you want>"` above its Commands table `[AC-2.2]`
- [ ] Given `codex/AGENTS.md.template` and the Commands section of `README.md`, when each is read, then the Codex template has a `### Start here` table with a `/writ` row above `Planning & Specification`, and README § Commands has a `### Start here` table with a `/writ` row `[AC-2.3]`
- [ ] Given `README.md` § Quick Start, when read from its top, then `/writ` and its two-line example appear before the first table, the prompting-guide pointer sentence ends with "then type `/writ` followed by what you want.", and the five-command table sits under the heading "What `/writ` routes to" `[AC-2.4]`
- [ ] Given `adapters/cursor.md` § Directory Structure, `commands/status.md`'s command list, `.writ/docs/model-tiers.md`'s `high` row, and `adapters/claude-code.md` § Tool Mapping → Quick Reference, when each is read, then the tree line `writ.md  # /writ` sits between `verify-spec.md` and `writ-design.md` with its count comment at 33, the status list starts with `/writ`, the `high` row lists `writ` in sorted order with its count at (16), and the Claude Code `todo_write` row's second cell is `TodoWrite` with Notes "Native todo list; phases mirror here" `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write the failing tests first. Add `test_manifest`, `test_catalogs`, `test_readme`, and `test_surfaces` to `scripts/tests/test_front_door.py`, which Story 1 created with its command-section tests. Assert what technical-spec.md → ## Tests lists for each. Follow the registration style in `scripts/tests/test_platform_neutral_names.py`: Python 3.9 stdlib, `subprocess` for the two `--check` calls. Run them and confirm each fails on the missing registration, not on an import or syntax error `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [ ] 2.2 Register `/writ` in `.writ/manifest.yaml`. Add `- id: entry` with `label: "Start here"` as the first `categories:` entry. Add the `writ` command entry with the `purpose` and `tags` from technical-spec.md → ## Registration Edits, placed after `verify-spec`. Run `test_manifest` and confirm it passes `[AC-2.1]`
- [ ] 2.3 Regenerate the generated catalogs. Run `bash scripts/gen-skill.sh` to regenerate `SKILL.md`. Add the "Start with" line to the TEMPLATE in `scripts/gen-claude-md.py`, above the Commands table, then run `python3 scripts/gen-claude-md.py`. Confirm both `--check` commands print `pass`. Do not hand-edit `SKILL.md` or `claude-code/CLAUDE.md` `[AC-2.2]`
- [ ] 2.4 Hand-edit the Codex template and the README Commands section. In `codex/AGENTS.md.template`, add a `### Start here` table with the `/writ` row above `Planning & Specification`. In README § Commands, add a `### Start here` table with the `/writ` row. Locate both by heading text `[AC-2.3]`
- [ ] 2.5 Rewrite README § Quick Start. Put `/writ` and a two-line example first. Complete the prompting-guide pointer sentence with its `/writ` clause, so it ends "then type `/writ` followed by what you want." Place the five-command table under the heading "What `/writ` routes to". Run `test_readme` and confirm it passes `[AC-2.4]`
- [ ] 2.6 Update the remaining surfaces. In `adapters/cursor.md` § Directory Structure, add `writ.md  # /writ` after `verify-spec.md` and change the count comment from 32 to 33. In `commands/status.md`, add `` `/writ` `` first in the command list. In `.writ/docs/model-tiers.md`, add `writ` to the `high` row in sorted order and change its count from 15 to 16. In `adapters/claude-code.md` § Tool Mapping → Quick Reference, set the `todo_write` row's second cell to `` `TodoWrite` `` and its Notes to "Native todo list; phases mirror here". Run `test_surfaces` and confirm it passes `[AC-2.5]`
- [ ] 2.7 Verify. Run `uv run --python 3.9 pytest`, then `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, then `bash scripts/eval.sh` outside any sandbox. Confirm all four registration tests pass, both `--check` commands print `pass`, and eval reports 0 findings. Run `git diff --stat` and confirm no edits under `.claude/` or `.cursor/` `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

- **Generated files.** `SKILL.md` comes from `bash scripts/gen-skill.sh`. `claude-code/CLAUDE.md` comes from `python3 scripts/gen-claude-md.py`. Change the generator or the manifest, then regenerate. A hand edit fails the `--check`. See technical-spec.md → ## Registration Edits.
- **Edit by heading.** Locate every edit by section heading or list text, never by line number. technical-spec.md → ## Registration Edits cites `commands/status.md` line 249 only for orientation. The list text is the anchor.
- **Manifest order.** `commands:` stays sorted by name, so `writ` sits between `verify-spec` and `writ-design`. `scripts/gen-skill.sh` renders categories in manifest order, so `entry` renders first with no script change. `scripts/gen-claude-md.py` has no category handling, so its TEMPLATE gains the "Start with" line instead. See spec.md → ## Business Rules (Expanded), Rules 8 and 9.
- **Count comments.** The cursor tree comment goes 32 to 33. The model-tiers `high` count goes 15 to 16. Check the current count before each edit. If it differs from these numbers, stop and report the mismatch.
- **Stale README sentence.** Task 2.5 replaces "Writ ships 32 commands, but you only need five." The spec gives no replacement wording. Drop the count rather than add a new hard-coded one.
- **Risks.**
  - A missed surface leaves one catalog without the front door. `test_catalogs` and `test_surfaces` catch it.
  - `check_manifest` in `scripts/eval.sh` fails for any `commands/*.md` with no manifest entry. Once Story 1's `commands/writ.md` exists, eval fails until task 2.2 lands. Land 2.2 before any eval run.
  - Task 2.5 completes the pointer sentence from `2026-10-22-prompting-guide`. If that sentence is absent, stop at 2.5 and report it. The prompting-guide spec owns that line.
  - The Claude Code `todo_write` row still maps to a file write (`Write(".writ/state/tracking.json")`). Until task 2.6 lands, `/writ` mirroring on Claude Code would write a file instead of using the native list.
- **Integration.** Story 1 wrote `commands/writ.md` and the command-section tests in `scripts/tests/test_front_door.py`. Story 2 adds the registration tests to that file. Story 3 adds the `scripts/eval-command-structure.py` rows, the issue Resolution, and the routing fixture.
- **Shadow path mapping.** In this story, "Upstream error" means a stale generated file. `test_catalogs` fails on it, and the fix is a regeneration. The missing routed-command case in technical-spec.md → ## Shadow Paths belongs to Story 1.
- **Source edits only.** Edit `commands/` and `adapters/` sources. `.claude/` and `.cursor/` are symlinks to them. Never edit those copies or run `install.sh` on this repo.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Upstream error)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (rules 8 Registration order, 9 Generated files are regenerated, 10 README, 11 Entry level, 12 Runtime)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Platform maps `todo_write` to a file)
