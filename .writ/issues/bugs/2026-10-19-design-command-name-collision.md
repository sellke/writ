# Writ's `/design` collides with Claude Code's native `/design`

> **Type:** Bug
> **Priority:** Normal
> **Effort:** Medium
> **Created:** 2026-10-19
> **spec_ref:** .writ/specs/2026-10-20-platform-neutral-names/

## TL;DR

Claude Code shipped its own `/design` command in August 2026, so a user on Claude Code typing `/design` cannot tell whether they get Writ's wireframe command or the platform's artboard skill.

## Current State

- Writ installs commands into `.claude/commands/` on Claude Code (`scripts/install.sh:76`, `PLATFORM_DIR=".claude"`), which includes `design.md`.
- Claude Code added a `/design` skill (research preview) the week of 17–21 August 2026: it drafts editable UI artboards from a brief, before code, and implements the one the user picks. One source cites v2.1.233+ as the floor.
- In this repo's own session — Claude Code 2.1.287, above that floor — the skill listing resolves `design` to Writ's command, and no native artboard skill appears. That is consistent with shadowing but does not prove the mechanism.
- The two commands do different things. Writ's generates Excalidraw wireframes into a spec's `mockups/`; the native one generates several artboards from a brief with no spec involved.
- Evidence for the native command is secondary reporting only — Anthropic's own changelog and docs did not surface in searches.

## Expected Outcome

- Verify first, in a clean install into a fresh project on 2.1.233+: does Writ's project command shadow the native skill, is it the other way round, or do both appear?
- Then resolve it deliberately, one of:
  - rename Writ's command (`/writ-design`), accepting the breaking change for existing installs; or
  - have Writ's `/design` detect the native skill and delegate the rendering step to it, keeping Writ's spec-linking and cataloguing.
- Whichever is chosen, a user on Claude Code can predict which command runs.

## Relevant Files

- `commands/design.md` — the colliding command
- `scripts/install.sh` — line 76, `PLATFORM_DIR=".claude"`; the install fanout that places it
- `adapters/claude-code.md` — where a detect-and-delegate rule would live

## Related Issues

- [2026-10-19-prototype-visual-preview-cursor-only](2026-10-19-prototype-visual-preview-cursor-only.md) — the other half of the visual-path platform gap
- [2026-10-12-script-install-location](../improvements/2026-10-12-script-install-location.md) — same family: what Writ drops into a project and what it may collide with

## Notes

Found during `/research` on pre-spec visual drafts; see `.writ/research/2026-10-19-prototype-visual-drafts-research.md` findings F5 and F6. Verification of the native command's behavior against first-party docs is the first step in that document's Further Research list, and it blocks this issue.

The collision is also a live instance of Design Principle 4 ("if the harness does it natively, adapt to it; never re-implement it"). A rename settles the name; it does not settle whether Writ should still ship a wireframe generator at all. That question belongs with the roadmap's `/design` Mode A modernization item, not here.

Worth a general check: Writ ships 32 commands into a namespace the platform also writes to. Nothing today detects a second collision.

## Resolution

2026-10-21, branch `writ/phase/13/2026-10-20-platform-neutral-names` (spec `2026-10-20-platform-neutral-names`, Stories 2 and 3; Story 2 is commit d36a283). Writ's command is renamed to `/writ-design`, with no alias. `commands/design.md` moved to `commands/writ-design.md` with `git mv`, and only its self-naming lines changed. The manifest entry, `SKILL.md`, `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, `README.md`, the commands and adapter that named it, and the five `scripts/eval.sh` allowlist rows now say `/writ-design`. The commit carries a `BREAKING CHANGE:` footer, and the spec's Upgrade Note is written for the CHANGELOG.

Old installs upgrade through stale detection; `update.sh` has no rename map. When the project manifest lists `commands/design.md` and upstream no longer ships it:

- An unmodified copy is removed, and the update prints `🗑  Removed: commands/design.md`.
- A locally modified copy is kept, and every update prints `⚠️  Stale (no longer shipped, locally modified — kept): commands/design.md` until the user deletes it. Until then, `/design` in that project still opens the old copy.

`/update-writ` states the same stale rules (Step 3 and Step 6). Only `update.sh` was run in a test.

`scripts/tests/test_platform_neutral_names.py` pins the registration (file and frontmatter, manifest entry, `SKILL.md`, `claude-code/CLAUDE.md`, allowlist rows) and runs the reference gate `writ_design_refs`, which fails on any tracked line outside the record list that names `/design` or `commands/design.md`. `scripts/tests/test_install_update_writ_design.sh` runs the real `install.sh` and `update.sh` from committed copies of the tree: a fresh install on Cursor, Claude Code, and Codex; an upgrade from a stand-in for the last release with the old file unmodified on all three; and a locally modified old file on Claude Code across two updates.

Not verified: nobody checked in a live Claude Code session (2.1.233 or later) whether a project command shadows the native `/design`, or the reverse. The rename removes the collision either way. Nothing detects a second collision between a Writ command and a platform command (see Notes).
