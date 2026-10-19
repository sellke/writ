# Writ's `/design` collides with Claude Code's native `/design`

> **Type:** Bug
> **Priority:** Normal
> **Effort:** Medium
> **Created:** 2026-10-19
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

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
