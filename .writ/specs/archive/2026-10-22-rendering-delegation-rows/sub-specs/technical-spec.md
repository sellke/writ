# Technical Spec: Rendering-Delegation Rows

> Spec: [`../spec.md`](../spec.md) · Research: [`2026-10-19-prototype-visual-drafts-research.md`](../../../research/2026-10-19-prototype-visual-drafts-research.md) F5, F6, Further Research 1 and 4

## Current State (audit, 2026-10-22)

| Adapter | Table | Row text today | Evidence behind it |
|---|---|---|---|
| `adapters/cursor.md:114` | § Native Tool Availability (`Tool \| Used By \| Purpose`) | The `cursor-ide-browser` canvas renders each draft. + clause | Contract only. Research found no Cursor canvas docs. |
| `adapters/claude-code.md:198` | § Tool Mapping → Quick Reference (`Cursor Tool \| Claude Code Native \| Notes`) | An artifact, or the preview pane; one self-contained HTML page per draft + clause | Secondary reporting (research F5). |
| `adapters/codex.md:146` | § Tool Mapping → Quick reference — orchestration primitives | `Write` one HTML file per draft to `.writ/prototypes/<date>-<slug>/` … Includes a read-only sandbox. + clause | Contract only. |
| `adapters/openclaw.md:19` | § Quick Reference | `Write({ path: … })`, one HTML file per draft … Includes a run that cannot write files. + clause | Contract only. |

`commands/prototype.md` Step 2.5 → "Render through the platform" has three rows: native artboard/design surface; `canvas-preview` (the adapter maps it); neither. The first row is unverified on every platform.

Precedent for records: `adapters/cursor.md` § Sub-Agent Models → "#### Verification record — 2026-09-03", a table of spawns with tool-level results and self-reports, each with a confidence note.

Tests: `scripts/tests/test_platform_neutral_names.py` → `test_adapter_canvas_row[<adapter>]` pins per-adapter keywords and the degradation clause; `test_prototype_names_capability` pins Step 2.5's three row labels in order.

## Verification Record Format

Under each adapter's tool-table section, after the table:

```markdown
#### Verification record — 2026-10-2x

| Check | Platform & version | Observed | Source | Status |
|---|---|---|---|---|
| Render one self-contained HTML draft | Claude Code 2.1.3xx (desktop) | <what happened> | https://code.claude.com/docs/… | verified 2026-10-2x |
| Native design surface reachable from a command run | Claude Code 2.1.3xx | <what happened> | https://… | verified 2026-10-2x |
```

Status grammar (test-pinned, anchored): `^(verified|unverified) \d{4}-\d{2}-\d{2}( \((pending UAT|no deployment)\))?$`. Versions and any other reason text go in the Platform & version or Observed cell, never in Status. Source grammar: starts with `https://`; "not documented" goes in Observed with the docs index URL in Source. The record is its own table under its own `####` heading, separated from the tool table by a blank line.

## Claude Code Protocol (lane, Story 1)

1. Record `claude --version` and whether the session is the desktop app or terminal.
2. Write `draft-a.html` to a temp folder outside the repo (the session scratchpad on Claude Code) (inline CSS, no network fetch, a labeled region per component) and attempt to render it through the artifact mechanism, then through the preview pane if available. Record which rendered, with the docs URL for each mechanism.
3. Attempt to reach the native design surface from inside a command run (not by the user typing `/design`). Record whether a Writ command can delegate to it.
4. If neither renders (for example, a headless run), record that the degradation path was taken and that the structural description was produced.

## UAT Protocols (maintainer, Story 2 writes; `/create-uat-plan` derives scenarios)

Both protocols use the same sample idea: `"a settings page with a dark-mode toggle"`. The Status grammar is anchored, so a pass writes `verified <date>` in the Status cell and the platform version in the Platform & version cell, never `verified <date>, Cursor <version>`.

### Cursor

- **Precondition:** Cursor with Writ installed (`install.sh`, cursor platform) in a sample project that has at least one UI component file. The Browser tool is enabled ("Enable Browser Automation Features") and, if the project has a dev server, its origin is on the Browser Origin Allowlist.
- **Run:** `/prototype --diverge "a settings page with a dark-mode toggle"`.
- **Look for:** Step 2.5 writes one self-contained HTML file per draft under `.writ/prototypes/<date>-<slug>/` and gives each path. Does the agent open a draft in the Browser pane (`@browser`, `browser_navigate` on a served origin) or in a Canvas? Which tool name does the agent report using? If nothing renders, does it say so and produce a structural description per draft?
- **On pass (a draft rendered):** in the `adapters/cursor.md` record, edit the row for the surface that rendered: Status `verified <date>`, the Cursor version in the Platform & version cell, and what rendered in Observed. Adjust the `canvas-preview` row text to the tool the agent used.
- **On fail (nothing rendered):** Status `unverified <date>` (drop the `(pending UAT)` reason), the Cursor version in the Platform & version cell, and the observation in Observed. The row already names the HTML-file floor; leave it.

### Codex Desktop

- **Precondition:** Codex Desktop (the desktop app the Codex app docs redirect to) with the sample project open; Writ installed with the codex platform.
- **Run:** ask Codex to follow `.codex/commands/prototype.md` with `--diverge "a settings page with a dark-mode toggle"`.
- **Look for:** one self-contained HTML file per draft under `.writ/prototypes/<date>-<slug>/`, each path given to the user. Does the app open or preview any of them, and by what mechanism (file preview, browser, none)? If nothing renders, does the agent say so and produce a structural description per draft?
- **On pass (a draft rendered):** in the `adapters/codex.md` record, edit the Desktop row: Status `verified <date>`, the app version in the Platform & version cell, the mechanism in Observed. Rewrite the row's Desktop clause to that mechanism.
- **On fail (nothing rendered):** Status `unverified <date>`, the app version in the Platform & version cell, the observation in Observed. The Desktop clause already says rendering is not documented; leave it.
- **CLI row (pass or fail):** when the files appear under `.writ/prototypes/<date>-<slug>/`, edit the record's CLI row too: Status `verified <date>`, the Codex version in the Platform & version cell, and the paths written in Observed.

## Codex Row Shape (Story 2)

```
| `canvas-preview` | CLI: `Write` one self-contained HTML file per draft to `.writ/prototypes/<date>-<slug>/`. Desktop: <docs-supported statement>. | Inline CSS, no network fetch; give the user each path. A read-only sandbox cannot write drafts. No renderer: write a structural description of each draft and say the drafts were not rendered. |
```

The keywords `.writ/prototypes/<date>-<slug>/` and `HTML` stay in the row so `test_adapter_canvas_row[codex]` passes unchanged.

## Tests (Story 3)

| Test | Assertion |
|---|---|
| `test_verification_records[<adapter>]` | A heading matching `^#### Verification record — \d{4}-\d{2}-\d{2}$` exists in the adapter; its first table has ≥1 data row; every row's Status cell matches the status grammar and its Source cell starts with `https://`. |
| `test_adapter_canvas_row[<adapter>]` | Unchanged assertions; keyword list updated only if a row changed. |
| `test_prototype_names_capability` | Unchanged unless Business Rule 7 fired; then updated in the same commit with a drift-log entry. |

## Shadow Paths

- **Happy path:** Claude Code renders via artifact; records written; rows unchanged.
- **Nil input:** a platform page gives no statement about rendering → cell reads "not documented", status unverified.
- **Empty input:** a live run that produces no drafts (Step 2.5 skipped) → not a verification; rerun with `--diverge`.
- **Upstream error:** a docs URL that 404s → do not cite it; find the current page or record "no first-party page found on <date>".

## Error & Rescue Map

Not required: this spec edits documentation and tests only; no data flow.
