# `/prototype` Visual Preview names a Cursor-only tool no adapter translates

> **Type:** Bug
> **Priority:** Normal
> **Effort:** Small
> **Created:** 2026-10-19
> **spec_ref:** .writ/specs/2026-10-20-platform-neutral-names/

## TL;DR

`commands/prototype.md` Step 2.5 tells the agent to use the `cursor-ide-browser` canvas tool, but that name appears in no adapter, so the step has no runnable tool on Claude Code, Codex, or OpenClaw.

## Current State

- `cursor-ide-browser` appears twice in `commands/prototype.md`: line 89 (Figma MCP detection) and line 113 ("Generate a canvas-based HTML mockup using the `cursor-ide-browser` canvas tool").
- `grep -rc "cursor-ide-browser" adapters/` returns zero matches in all four adapter files.
- This breaks the convention `CLAUDE.md` states outright: "commands use platform-agnostic tool names — each adapter translates them to one platform's APIs."
- On Claude Code, Codex, and OpenClaw the agent reaching Step 2.5 is told to call a tool that does not exist. The step's own skip path only covers "no UI change", not "no canvas tool", so there is no defined degradation.
- Related gap in the same area: `adapters/claude-code.md:121` notes "There is no `visual-qa` equivalent here yet."
  - *(Update 2026-10-20:)* That gap is closed. Spec `2026-10-20-claude-agent-generator` added `claude-code/agents/writ-visual-qa.md`, generated from `agents/visual-qa-agent.md`, and the adapter line is gone. The Step 2.5 canvas-tool problem above is unchanged.

## Expected Outcome

- Step 2.5 names a platform-agnostic capability, not a vendor tool.
- All four adapters carry a row translating that capability to their own API, including an explicit degradation when the platform has none — Claude Code artifacts or its preview MCP, Cursor canvas, and a self-contained HTML file as the floor.
- A `/prototype` run on a platform with no canvas capability skips the preview and says why, rather than calling a tool that is not there.

## Relevant Files

- `commands/prototype.md` — lines 89 and 113, the two `cursor-ide-browser` references
- `adapters/claude-code.md` — no visual/canvas capability row (the `visual-qa` gap it once flagged is closed; see above)
- `adapters/cursor.md` — the only platform where the current text works

## Related Issues

- [2026-10-12-script-install-location](../improvements/2026-10-12-script-install-location.md) — same family: what Writ assumes about the platform it lands on

## Notes

Found during `/research` on pre-spec visual drafts; see `.writ/research/2026-10-19-prototype-visual-drafts-research.md` finding F6. That research recommends leaving Step 2.5's single-preview scope alone — this issue is only the tool-name and adapter fix, not a redesign of the step.

Worth checking whether an eval check can catch the general case: a command naming a tool that no adapter translates. That would stop the next one rather than this one.

## Resolution

2026-10-21, branch `writ/phase/13/2026-10-20-platform-neutral-names` (spec `2026-10-20-platform-neutral-names`, Story 1, commit 81c63c1). `commands/prototype.md` no longer names a vendor tool. Step 2 (Figma MCP detection) and Step 2.5 (the "Render through the platform" table) name the `canvas-preview` capability, and the sentence under the table says each adapter maps it and states its fallback. Each adapter maps the capability in one row of its tool table:

- `adapters/cursor.md`: the `cursor-ide-browser` canvas.
- `adapters/claude-code.md`: an artifact, or the preview pane, with one self-contained HTML page per draft.
- `adapters/codex.md` and `adapters/openclaw.md`: one self-contained HTML file per draft (inline CSS, no network fetch) under `.writ/prototypes/<date>-<slug>/`.

Every row ends with the same fallback: "No renderer: write a structural description of each draft and say the drafts were not rendered."

`scripts/tests/test_platform_neutral_names.py` pins this. `test_prototype_names_capability` checks both steps and the three-row render table. `test_adapter_canvas_row` checks for exactly one row per adapter, its platform keywords, and the fallback in its last cell. `test_cursor_ide_browser_confined` fails if `cursor-ide-browser` appears anywhere outside `adapters/cursor.md` and record paths.

Not done: no eval check catches the general case, a command naming a tool that no adapter translates (see Notes).

### Verification

2026-10-22, spec `2026-10-22-rendering-delegation-rows` (Phase 14, lane `writ/phase/14/2026-10-22-rendering-delegation-rows`). Each adapter's tool-table section now carries a `#### Verification record — 2026-10-22` whose rows cite a first-party page and a dated status; `test_verification_records` pins the record shape. Status at spec close:

- `adapters/claude-code.md`: verified 2026-10-22 (Claude Code 2.1.308, desktop app). The `Artifact` tool published and rendered a self-contained HTML draft; the Browser pane rendered it when served over `http://127.0.0.1`; the Claude Design type is listable from inside a command run. Headless `claude -p`: unverified 2026-10-22, docs only. Row unchanged.
- `adapters/cursor.md`: unverified 2026-10-22 (pending UAT). The Browser and Canvas pages document no canvas that renders a local HTML file, so the row now names the HTML-file floor and the Browser tool's allowlisted origins instead of `cursor-ide-browser`. Protocol: `.writ/specs/2026-10-22-rendering-delegation-rows/sub-specs/technical-spec.md` § UAT Protocols → Cursor.
- `adapters/codex.md`: CLI clause verified 2026-10-24 (codex-cli 0.163.0: three self-contained drafts written, paths listed, nothing rendered); Desktop clause unverified 2026-10-22 (pending UAT). Row rewritten as a CLI clause (the HTML-file floor) and a Desktop clause (the app's docs do not document rendering an HTML draft). Protocol: the same file, § UAT Protocols → Codex Desktop.
- `adapters/openclaw.md`: unverified 2026-10-22 (no deployment). Row unchanged; the Tools page documents file write and sending a local HTML file to the conversation, not rendering inside the agent.

`commands/prototype.md` Step 2.5 is unchanged: no recorded observation contradicts a render-table row.
