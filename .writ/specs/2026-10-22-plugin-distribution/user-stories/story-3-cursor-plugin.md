# Story 3: Cursor Plugin

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1, Story 2

## User Story

**As a** Cursor user who installs Writ from the local plugins folder now and from the marketplace later
**I want to** install Writ as one Cursor plugin built from this repository, with its rules, skills, and commands loaded from the plugin
**So that** I stop copying files into `.cursor/` by hand, and each release updates the plugin from the same generated source

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given the `cursor-plugin` target in `scripts/gen-platform-trees.py` and the `VERSION` file, when the driver writes the layout, then `.cursor-plugin/plugin.json` has `name` `writ`, a `description`, and a `version` equal to the `VERSION` file's content, and `--check` prints `fail` when the two disagree `[AC-3.1]`
- [ ] Given `cursor/writ.mdc` and the shipped skills, when the layout is generated, then `rules/writ.mdc` is byte-equal to `cursor/writ.mdc`, `skills/` holds every shipped skill folder with its `SKILL.md`, and `commands/` and `agents/` sit at the directories that Story 1's record verifies for Cursor `[AC-3.2]`
- [ ] Given Story 1's record for Cursor script calls, when the layout is generated, then either the record has a `verified` row for a plugin-root form, and the layout ships the `is_shippable_script` set with no dev-only script and the commands use the form that row names; or the record has no such row, and the commands keep `python3 scripts/<name>.py`, the layout has no `scripts/` directory, and `## Plugin` says the project still needs the `install.sh` script copy `[AC-3.3]`
- [ ] Given `adapters/cursor.md`, when a reader opens its `## Plugin` section, then it gives the local-install steps (copy the layout to `~/.cursor/plugins/local/writ`, then reload Cursor), states the marketplace submission as a maintainer step this story does not perform, and has one row per platform claim with a status in the Verification Record grammar and a source URL `[AC-3.4]`
- [ ] Given `sub-specs/technical-spec.md` § UAT Protocols, when a maintainer reads the Cursor local plugin protocol, then it lists a precondition (Cursor version recorded, sample project open), numbered steps (copy, reload, open the sample project), three things to look for (rules listed in the session, `/writ` visible, a script-calling command resolves; when Story 1 chose the `scripts/` form, the step first confirms the project has `scripts/` from `install.sh`), and the record edit to `adapters/cursor.md` § Plugin on pass and on fail `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write failing tests in `scripts/tests/test_plugin_distribution.py`. Create the file, or add a `TestCursorPlugin` class if Story 2 created it first. Cover: manifest keys, and `version` equal to `VERSION`; `rules/writ.mdc` byte-equal to `cursor/writ.mdc`; every `commands/*.md` and every shipped skill present in the layout; no dev-only script in the layout; the script form matches the AC-3.3 branch. Run them and confirm they fail on the current tree `[AC-3.1, AC-3.2, AC-3.3]`
- [ ] 3.2 Add a `cursor-plugin` target to the `TARGETS` table in `scripts/gen-platform-trees.py`. It writes `.cursor-plugin/plugin.json` (`name`, `description`, and `version` read from `VERSION` at generation time) and `rules/writ.mdc` as a byte copy of `cursor/writ.mdc`, into the layout directory Story 1's record names. Make the manifest and rules tests pass `[AC-3.1, AC-3.2]`
- [ ] 3.3 Extend the target to copy `commands/*.md`, the canonical `agents/*.md`, and the shipped skills into the directories Story 1's record verifies. Set the `script-root` token to the form AC-3.3 selects. With no `verified` plugin-root row, leave out any `scripts/` directory and keep the `scripts/` command form. Make the layout tests pass `[AC-3.2, AC-3.3]`
- [ ] 3.4 Add `## Plugin` to `adapters/cursor.md`: the local-install steps, the maintainer-only marketplace submission step, and one row per platform claim with its status, source URL, and read date. Mark each live-session claim `unverified <date> (pending UAT)` unless a Story 1 row verifies it `[AC-3.4]`
- [ ] 3.5 Expand the existing `Cursor local plugin` bullet in `sub-specs/technical-spec.md` § UAT Protocols into the full protocol: precondition, numbered steps, the three look-fors, and the record edit for pass and for fail `[AC-3.5]`
- [ ] 3.6 Verify: `uv run --python 3.9 pytest`; `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` prints no `FAIL` line; `python3 scripts/gen-platform-trees.py --check` prints `pass`; `bash scripts/eval.sh`, run outside any sandbox, reports 0 findings; the tests write nothing under `~/.cursor` `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

- **Verification first.** Story 1's record decides every layout choice here. A row marked `unverified` drives no layout decision (Business Rule 1). Cite the record as `technical-spec.md → ## Verification Record`.
- **Undocumented directories.** `cursor.com/docs/plugins` (read 2026-10-22) lists agents, commands, and hooks as components with no documented default directory. Place `commands/` and `agents/` only where Story 1's record verifies a load. Do not guess a directory.
- **Decision needed before 3.3.** No Cursor session runs in this lane, so Story 1 will likely mark Cursor command and agent placement as pending UAT. Business Rule 1 bars a layout decision from that row. Choose one before 3.3 starts and record it in What Was Built: (a) ship `commands/` and `agents/` at a documented-guess path labelled `unverified (pending UAT)`, or (b) hold those two components until the UAT runs. Business Rule 1 points to (b).
- **Script form.** `${CURSOR_PLUGIN_ROOT}` is documented only for `mcp.json` (cursor.com/docs/plugins, read 2026-10-22). A command-body root form needs a `verified` row. Without one, commands keep `python3 scripts/<name>.py`, and the adapter says the project needs the `install.sh` script copy.
- **Dev-only scripts.** When scripts ship in the layout, the set is what `is_shippable_script` admits. The dev-only denylist stays out. Reference: `technical-spec.md → ## Current State (audit, 2026-10-22)`.
- **Layout directory.** The default is `cursor/plugin/`. The path in Story 1's record wins. The local-install step copies that directory to `~/.cursor/plugins/local/writ`.
- **Shared test file.** `scripts/tests/test_plugin_distribution.py` may already exist from Story 2. Add a class to it. Do not rewrite Story 2's tests.
- **File overlap with Story 2.** Story 2 also edits the `TARGETS` table in `scripts/gen-platform-trees.py`. Run the two in sequence, or merge the table by hand. Both targets read `VERSION` the same way, so use one helper.
- **Live check.** This story does not run Cursor. The live load stays `unverified <date> (pending UAT)` until the maintainer runs the protocol.
- **Marketplace.** Cursor reviews official marketplace entries. Team marketplaces import repository URLs (cursor.com/docs/plugins, read 2026-10-22). Until a listing exists, `## Plugin` says "marketplace listing pending". Submission is a maintainer action after the phase (`spec.md → ## Specification Contract`, Scope out).
- **Risk: install.sh dependency.** Under the `scripts/` form, a plugin-only install has commands that fail until the project also runs `install.sh`. `## Plugin` says so. Story 5's `cursor-plugin` check runs `spec-status.py --help` from the resolved root. Under the `scripts/` form there is no root in the layout, so Story 5 must define how that check reports. Do not copy scripts in just to make it pass.
- **Risk: marketplace claim before UAT.** Neither `## Plugin` nor the README may state a live load or a marketplace listing without a dated row behind it. Story 5 reads this section for the README order (`spec.md → ## Business Rules (Expanded)`, Rule 10).
- **Integration.** Story 1 supplies the Cursor rows. Story 2 supplies the `TARGETS` table and the `VERSION` read. Story 5 adds the `cursor-plugin` smoke target: commands at the layout's commands path, instructions at `rules/writ.mdc`, and the scaffold check.
- **Version.** `VERSION` reads `0.43.0` on 2026-10-22.

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
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 1 Verification record first; Rule 2 Plugin target; Rule 3 Scripts in the plugin; Rule 6 Cursor layout; Rule 12 Runtime)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Cursor local plugin)
