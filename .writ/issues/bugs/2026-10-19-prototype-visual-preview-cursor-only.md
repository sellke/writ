# `/prototype` Visual Preview names a Cursor-only tool no adapter translates

> **Type:** Bug
> **Priority:** Normal
> **Effort:** Small
> **Created:** 2026-10-19
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

`commands/prototype.md` Step 2.5 tells the agent to use the `cursor-ide-browser` canvas tool, but that name appears in no adapter, so the step has no runnable tool on Claude Code, Codex, or OpenClaw.

## Current State

- `cursor-ide-browser` appears twice in `commands/prototype.md`: line 89 (Figma MCP detection) and line 113 ("Generate a canvas-based HTML mockup using the `cursor-ide-browser` canvas tool").
- `grep -rc "cursor-ide-browser" adapters/` returns zero matches in all four adapter files.
- This breaks the convention `CLAUDE.md` states outright: "commands use platform-agnostic tool names — each adapter translates them to one platform's APIs."
- On Claude Code, Codex, and OpenClaw the agent reaching Step 2.5 is told to call a tool that does not exist. The step's own skip path only covers "no UI change", not "no canvas tool", so there is no defined degradation.
- Related gap in the same area: `adapters/claude-code.md:121` notes "There is no `visual-qa` equivalent here yet."

## Expected Outcome

- Step 2.5 names a platform-agnostic capability, not a vendor tool.
- All four adapters carry a row translating that capability to their own API, including an explicit degradation when the platform has none — Claude Code artifacts or its preview MCP, Cursor canvas, and a self-contained HTML file as the floor.
- A `/prototype` run on a platform with no canvas capability skips the preview and says why, rather than calling a tool that is not there.

## Relevant Files

- `commands/prototype.md` — lines 89 and 113, the two `cursor-ide-browser` references
- `adapters/claude-code.md` — no visual/canvas capability row; already flags the `visual-qa` gap at line 121
- `adapters/cursor.md` — the only platform where the current text works

## Related Issues

- [2026-10-12-script-install-location](../improvements/2026-10-12-script-install-location.md) — same family: what Writ assumes about the platform it lands on

## Notes

Found during `/research` on pre-spec visual drafts; see `.writ/research/2026-10-19-prototype-visual-drafts-research.md` finding F6. That research recommends leaving Step 2.5's single-preview scope alone — this issue is only the tool-name and adapter fix, not a redesign of the step.

Worth checking whether an eval check can catch the general case: a command naming a tool that no adapter translates. That would stop the next one rather than this one.
