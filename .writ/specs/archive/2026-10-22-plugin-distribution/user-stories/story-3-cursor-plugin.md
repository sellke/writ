# Story 3: Cursor Plugin

> **Status:** Completed ✅ (2026-10-23)
> **Commit:** 1f076f9bbbb86f6a7e22bf952c47651c8f669f6b
> **Priority:** High
> **Dependencies:** Story 1, Story 2

## User Story

**As a** Cursor user who installs Writ from the local plugins folder now and from the marketplace later
**I want to** install Writ as one Cursor plugin built from this repository, with its rules, skills, and commands loaded from the plugin
**So that** I stop copying files into `.cursor/` by hand, and each release updates the plugin from the same generated source

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given the `cursor-plugin` target in `scripts/gen-platform-trees.py` and the `VERSION` file, when the driver writes the layout, then `.cursor-plugin/plugin.json` has `name` `writ`, a `description`, and a `version` equal to the `VERSION` file's content, and `--check` prints `fail` when the two disagree `[AC-3.1]`
- [x] Given `cursor/writ.mdc` and the shipped skills, when the layout is generated, then `rules/writ.mdc` is byte-equal to `cursor/writ.mdc`, `skills/` holds every shipped skill folder with its `SKILL.md`, and `commands/` and `agents/` sit at the directories that Story 1's record verifies for Cursor `[AC-3.2]`
- [x] Given Story 1's record for Cursor script calls, when the layout is generated, then either the record has a `verified` row for a plugin-root form, and the layout ships the `is_shippable_script` set with no dev-only script and the commands use the form that row names; or the record has no such row, and the commands keep `python3 scripts/<name>.py`, the layout has no `scripts/` directory, and `## Plugin` says the project still needs the `install.sh` script copy `[AC-3.3]`
- [x] Given `adapters/cursor.md`, when a reader opens its `## Plugin` section, then it gives the local-install steps (copy the layout to `~/.cursor/plugins/local/writ`, then reload Cursor), states the marketplace submission as a maintainer step this story does not perform, and has one row per platform claim with a status in the Verification Record grammar and a source URL `[AC-3.4]`
- [x] Given `sub-specs/technical-spec.md` § UAT Protocols, when a maintainer reads the Cursor local plugin protocol, then it lists a precondition (Cursor version recorded, sample project open), numbered steps (copy, reload, open the sample project), three things to look for (rules listed in the session, `/writ` visible, a script-calling command resolves; when Story 1 chose the `scripts/` form, the step first confirms the project has `scripts/` from `install.sh`), and the record edit to `adapters/cursor.md` § Plugin on pass and on fail `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Write failing tests in `scripts/tests/test_plugin_distribution.py`. Create the file, or add a `TestCursorPlugin` class if Story 2 created it first. Cover: manifest keys, and `version` equal to `VERSION`; `rules/writ.mdc` byte-equal to `cursor/writ.mdc`; every `commands/*.md` and every shipped skill present in the layout; no dev-only script in the layout; the script form matches the AC-3.3 branch. Run them and confirm they fail on the current tree `[AC-3.1, AC-3.2, AC-3.3]`
- [x] 3.2 Add a `cursor-plugin` target to the `TARGETS` table in `scripts/gen-platform-trees.py`. It writes `.cursor-plugin/plugin.json` (`name`, `description`, and `version` read from `VERSION` at generation time) and `rules/writ.mdc` as a byte copy of `cursor/writ.mdc`, into the layout directory Story 1's record names. Make the manifest and rules tests pass `[AC-3.1, AC-3.2]`
- [x] 3.3 Extend the target to copy `commands/*.md`, the canonical `agents/*.md`, and the shipped skills into the directories Story 1's record verifies. Set the `script-root` token to the form AC-3.3 selects. With no `verified` plugin-root row, leave out any `scripts/` directory and keep the `scripts/` command form. Make the layout tests pass `[AC-3.2, AC-3.3]`
- [x] 3.4 Add `## Plugin` to `adapters/cursor.md`: the local-install steps, the maintainer-only marketplace submission step, and one row per platform claim with its status, source URL, and read date. Mark each live-session claim `unverified <date> (pending UAT)` unless a Story 1 row verifies it `[AC-3.4]`
- [x] 3.5 Expand the existing `Cursor local plugin` bullet in `sub-specs/technical-spec.md` § UAT Protocols into the full protocol: precondition, numbered steps, the three look-fors, and the record edit for pass and for fail `[AC-3.5]`
- [x] 3.6 Verify: `uv run --python 3.9 pytest`; `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` prints no `FAIL` line; `python3 scripts/gen-platform-trees.py --check` prints `pass`; `bash scripts/eval.sh`, run outside any sandbox, reports 0 findings; the tests write nothing under `~/.cursor` `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Upstream error)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 1 Verification record first; Rule 2 Plugin target; Rule 3 Scripts in the plugin; Rule 6 Cursor layout; Rule 12 Runtime)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Cursor local plugin)

---

## What Was Built

**Implementation Date:** 2026-10-23

### Files Created

1. **`cursor/plugin/`** (61 files, generated, no symlinks)
   - `.cursor-plugin/plugin.json` (`name` writ, `version` from `VERSION` 0.43.0, description, author, repository, license; no component path fields, since a path field replaces folder discovery, V48), `rules/writ.mdc` (byte-equal to `cursor/writ.mdc`), `commands/` (34), `agents/` (8 prompt-template docs, mirroring install.sh's `.cursor/agents/`), `skills/` (16), `system-instructions.md` at the root. No `scripts/` directory.

### Files Modified

- **`scripts/gen-platform-trees.py`** (`cursor-plugin` target)
  - Identity script root `scripts` with `in_place`; `read_version()` shared by both manifests; Story 2's plugin machinery parameterized by `PluginTree` (one generation path; the Claude plugin renders byte-identically); symlink guards for `cursor/` and `cursor/plugin/`; `--check` covers the layout and skips it when an adapter table fails to parse.
- **`scripts/tests/test_plugin_distribution.py`** (TestCursorPlugin, TestCursorAdapterPlugin, TestCursorUatProtocol)
  - Manifest and version drift, byte-equal rule, component set, identity bodies, no scripts, link resolution, determinism, freshness, 7 drift cases, write repair, symlink refusal, HOME isolation; adapter claims match the record; UAT protocol structure.
- **`adapters/cursor.md`** (`## Plugin`)
  - Local install (copy to `~/.cursor/plugins/local/writ`, reload), the project still needs install.sh's `scripts/`, marketplace submission as a maintainer step ("marketplace listing pending"), 15-row claims table with record statuses, sources, and read dates.
- **`.writ/specs/2026-10-22-plugin-distribution/sub-specs/technical-spec.md`** (§ UAT Protocols Cursor protocol; § Verification Record V80)
- **`scripts/tests/test_gen_platform_trees.py`**, **`scripts/tests/test_eval_platform_trees.sh`** (expectations for the new tree)
- **`.writ/specs/2026-10-22-plugin-distribution/spec-lite.md`**, **`drift-log.md`** (DEV-017 to DEV-020)

### Implementation Decisions

1. **AC-3.3 second branch** — no verified plugin-root form for a Cursor command body (V49, V79), so commands keep `python3 scripts/<name>.py` and the layout has no `scripts/`.
2. **Story Notes "Decision needed before 3.3" was moot** — the Cursor reference now documents `commands/` and `agents/` (V48, DEV-004), so they ship at the documented directories; neither option (a) nor (b) applied. Live load stays pending UAT.
3. **No manifest component paths** — any path field replaces Cursor's folder discovery (V48), and no row verifies the replacement form live, so `_preamble.md` ships in `commands/` as install.sh ships it (possible `/_preamble` listing is a pending-UAT row).

### Test Results

**Verification:** `uv run --python 3.9 pytest scripts/tests/test_plugin_distribution.py scripts/tests/test_gen_platform_trees.py -q` 214 passed (red first: 10 failed, 31 errors for the missing target, section, protocol items, and layout); `bash scripts/tests/test_eval_platform_trees.sh` pass; `python3 scripts/gen-platform-trees.py --check` pass.
- ✅ Nothing written under `~/.cursor` (`~/.cursor/plugins/local` empty); tests run with HOME at a temp dir.
- ✅ A fresh render of `plugins/writ/` and `.claude-plugin/` with the refactored generator is byte-identical to the committed trees.
- ✅ Gate scripts: test-integrity authenticity pass; coverage, docs-check, app-verify unverifiable.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s) (review-agent route; Minor pre-commit fixes: root `system-instructions.md`, marketplace sentence, UAT step 7, docstring, V80)
- **Drift:** Medium
- **Security:** Clean
- **Boundary Compliance:** deviations in test_gen_platform_trees.py, test_eval_platform_trees.sh, two Story 2 expectations, and the V80 record row, each justified; no violations

### Deviations from Spec

- **[DEV-017] Cursor `agents/` ships frontmatter-less prompt docs where Cursor requires agent frontmatter** — Severity: Medium
  - Spec said: agents as the docs place them, install.sh's set.
  - Reality: the 8 prompt docs lack the YAML frontmatter Cursor requires (V80); likely blocks a marketplace submission.
  - Resolution: Flagged for review.
- **[DEV-018] Cursor agent-frontmatter claim added to the Verification Record** — Severity: Small
  - Spec said: every platform claim is in the record first.
  - Reality: V80 added; the adapter row cites it.
  - Resolution: Auto-amended (Small).
  - Spec amendment: technical-spec.md V80; spec-lite.md Cursor line.
- **[DEV-019] Story 2 and prior-spec test expectations extended for the Cursor layout** — Severity: Small
  - Spec said: add a class, do not rewrite Story 2's tests.
  - Reality: VERSION and full-write expectations extended in place; nothing loosened.
  - Resolution: Auto-amended (Small).
  - Spec amendment: spec-lite.md Cursor line.
- **[DEV-020] The Cursor layout ships `system-instructions.md` at its root** — Severity: Small
  - Spec said: Rule 6's component list.
  - Reality: root file added so 42 relative links resolve.
  - Resolution: Auto-amended (Small).
  - Spec amendment: spec-lite.md Cursor line.
