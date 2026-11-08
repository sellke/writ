# Rendering-Delegation Rows

> **Status:** Complete
> **Created:** 2026-10-22
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Phase:** 14 — Front Door and Distribution ([roadmap](../../product/roadmap.md), [ADR-030](../../decision-records/adr-030-contract-verifier-boundary-front-door.md))
> **Origin:** Phase 14 decomposition pre-pass (`/implement-phase 14`, 2026-10-22). Prototype research Further Research items 1 and 4 (`.writ/research/2026-10-19-prototype-visual-drafts-research.md`). Completes the verification half of `.writ/issues/bugs/2026-10-19-prototype-visual-preview-cursor-only.md`, whose rows Phase 13 wrote from the contract with no runtime evidence.

## Specification Contract

**Deliverable:** Each adapter's `canvas-preview` row names the renderer `/prototype` delegates to on that platform, cites first-party documentation, and carries a dated verification status. Live runs on Claude Code, Cursor, and Codex Desktop decide the rows; OpenClaw is marked unverified.

**Must Include:**

1. A `Verification record — <date>` subsection per adapter, in the shape `adapters/cursor.md` § Sub-Agent Models already uses: platform and version, what was run, what was observed, the first-party URL, and a status of `verified <date>` or `unverified <date>` (with the reason: `pending UAT` or `no deployment`).
2. Claude Code is verified in the lane: the artifact and preview-pane path for a self-contained HTML draft, and whether the native design surface that `/prototype`'s first render-table row names is reachable from a Writ command. Cursor and Codex Desktop get the row text their first-party docs support, a written protocol the UAT plan carries, and status `unverified (pending UAT)` until the maintainer runs it. OpenClaw is `unverified (no deployment)`, docs only.
3. The Codex row covers both surfaces: Codex CLI keeps the HTML-file floor; Codex Desktop records what the app renders, if anything, once verified.
4. `commands/prototype.md` Step 2.5's "Render through the platform" table changes only where a verification contradicts it. The step's scope stays as PR #59 wrote it.
5. `scripts/tests/test_platform_neutral_names.py::test_adapter_canvas_row` keeps passing or is updated in the same story as the row it pins. A new test checks that each adapter's verification record carries a status mark and an `https://` URL.

**Hardest Constraint:** The lane runs on Claude Code and cannot drive Cursor or Codex Desktop. Rows for those platforms are written from docs and flipped to `verified` only by the maintainer's UAT run. Nothing in the adapters claims a live result the run did not observe.

**Success Criteria:** four `canvas-preview` rows with citations and status; a UAT plan whose scenarios are the Cursor and Codex Desktop protocols; `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` (0 findings) pass.

**Scope out:** `/writ-design`, Claude Code's native `/design` as a Writ feature, any new renderer, the adapter tables' structure (owned by `2026-10-22-generated-platform-trees`, which lands after this spec).

## Technical Concerns

*Found while grounding the contract on 2026-10-22. None changes scope.*

- The current rows were written on 2026-10-21 from the Phase 13 contract. The story file records "Codex and OpenClaw rows have no runtime evidence" and that the prototype research found "nothing usable on Cursor canvas". This spec is the evidence pass those rows were waiting for.
- The Codex adapter is titled "Codex CLI Platform Adapter". Codex Desktop is a second surface of the same product. The adapter gains a Desktop clause inside the existing row rather than a new adapter.
- First-party sources were thin on 2026-10-22: the Codex app overview page lists a browser and "interactive visuals" without describing HTML preview; Cursor's docs describe a browser tool but the research found no canvas documentation. A row may legitimately end as "HTML file floor, verified; canvas unverified" when the docs do not support more.
- `test_adapter_canvas_row` pins keywords per adapter (cursor: `cursor-ide-browser`; claude-code: `artifact` and `preview pane`; codex and openclaw: `.writ/prototypes/<date>-<slug>/` and `HTML`) and the degradation clause. A verification that removes a keyword must update the test in the same commit.
- `2026-10-22-generated-platform-trees` will parse the tool tables by heading. Keep every `canvas-preview` row inside the tool table its adapter already has and keep the first cell `` `canvas-preview` ``; add no second tool table. The verification record is its own table under its own `####` heading, after a blank line, so `first_table` on the tool-table section still returns the tool table.

## Experience Design

### Who uses it

- **A `/prototype` user on Claude Code, Cursor, or Codex** whose run reaches Step 2.5. The adapter tells the agent what renders drafts on that platform and what to do when nothing does, and the user can see how recently that was checked.
- **The maintainer** running UAT on Cursor and Codex Desktop from a protocol short enough to finish in one sitting.
- **A reader of the adapter** deciding whether to trust a row: the record names the version and the date.

### Journey

1. Entry: the lane agent runs the Claude Code protocol; the maintainer runs the Cursor and Codex Desktop protocols during UAT.
2. Happy path: each run produces an observation (rendered where, or not rendered), which goes into the adapter's verification record; the row text is adjusted to match.
3. Moment of truth: a `/prototype` run on that platform renders drafts where the row says, or says plainly that drafts were not rendered.
4. Feedback: the adapter row and its record agree; the test proves each record has a status and a source.

### State Catalog

| State | What the reader sees |
|---|---|
| Claude Code, interactive desktop session | Record: `verified 2026-10-2x, Claude Code <version>`: artifact or preview pane rendered the HTML draft; native design surface reachable or not, as observed. |
| Claude Code, headless (`claude -p`) | Record notes the degradation path was exercised or cites the docs; row's clause unchanged. |
| Cursor, before UAT | Row text from first-party docs; record `unverified 2026-10-22 (pending UAT)`; protocol in the UAT plan. |
| Cursor, after UAT | Maintainer edits the record to `verified <date>, Cursor <version>` and adjusts the row if the run contradicted it. |
| Codex Desktop, before UAT | Row names the CLI HTML-file floor and a Desktop clause ("Desktop: <docs-supported statement>"); record `unverified (pending UAT)`. |
| Codex Desktop, after UAT | Record updated as for Cursor. |
| OpenClaw | Row unchanged unless docs contradict it; record `unverified 2026-10-22 (no deployment)` with the docs URL. |
| Maintainer removes a status mark or URL from a record | `test_verification_records` fails and names the adapter. |

### Interaction Patterns

- Rows state facts; records state evidence. A row never says "verified"; the record does.
- Unverified is a status, not a defect. A platform the maintainer has not run stays `unverified` indefinitely and the row still has a documented floor.

## Business Rules (Expanded)

1. **Record shape.** Each adapter gets `#### Verification record — YYYY-MM-DD` under the section that holds its tool table (cursor: § Native Tool Availability; claude-code: § Tool Mapping → Quick Reference; codex: § Tool Mapping → Quick reference — orchestration primitives; openclaw: § Quick Reference). The record is a table with columns `Check | Platform & version | Observed | Source | Status`. Status values: `verified YYYY-MM-DD` or `unverified YYYY-MM-DD (pending UAT|no deployment)`.
2. **One row per adapter.** The `canvas-preview` row stays exactly one line starting with `` | `canvas-preview` | `` inside the existing table. The degradation clause "No renderer: write a structural description of each draft and say the drafts were not rendered." stays verbatim.
3. **Row text follows evidence.** A row claims only what a first-party source or a live run supports. Where neither supports a canvas, the row names the HTML-file floor and the record says why.
4. **Claude Code live check.** The lane writes one self-contained HTML draft to a temp folder and renders it through the platform's artifact or preview mechanism, records what happened, then checks whether the native design surface is invocable from inside a command run. The record cites the Claude Code docs page for each mechanism.
5. **Protocols are the UAT scenarios.** `sub-specs/technical-spec.md` § UAT Protocols is the source `/create-uat-plan` derives the Cursor and Codex Desktop scenarios from. Each protocol: precondition, the exact `/prototype --diverge` invocation on a fixed sample idea, what to look for, and the record edit to make on pass or fail.
6. **Codex CLI and Desktop.** One row, two clauses: "CLI: `Write` one self-contained HTML file per draft …" and "Desktop: <statement>". The CLI clause keeps today's text.
7. **`prototype.md` is read-only unless contradicted.** If a live run shows a render-table row is wrong (for example, no platform has a "native artboard/design surface" reachable from a command), the row is corrected and the change is recorded in the drift log. Otherwise the file is untouched.
8. **Tests.** `test_platform_neutral_names.py` gains `test_verification_records[<adapter>]`: the record heading exists, every row has a Status cell matching the anchored grammar `^(verified|unverified) \d{4}-\d{2}-\d{2}( \((pending UAT|no deployment)\))?$` and a Source cell starting with `https://`. Versions go in the Platform & version cell, never in Status. Existing canvas tests stay green.
9. **Issue note.** `2026-10-19-prototype-visual-preview-cursor-only.md` gets a `### Verification` subsection at the end of its `## Resolution` section (which `test_issue_resolution` requires to stay the last H2) naming this spec and the per-platform status at spec close.
10. **Runtime.** Python 3.9 standard library and POSIX bash. No network calls from tests.

## Detailed Requirements

### Story 1: Claude Code live verification and record

- Run the Claude Code protocol in the lane (Business Rule 4). Write the `Verification record — <date>` into `adapters/claude-code.md` with the artifact or preview-pane observation, the native design-surface observation, versions, and docs URLs.
- Adjust the `canvas-preview` row text only where the observation contradicts it.

### Story 2: Cursor, Codex, and OpenClaw rows from first-party docs, with UAT protocols

- Collect first-party URLs for Cursor's browser or canvas tool, the Codex app's rendering surface (or the absence of one), and OpenClaw's file-write capability. Write each adapter's record with `unverified` status and the reason.
- Rewrite the Codex row as CLI plus Desktop clauses. Adjust the Cursor row if the docs do not support `cursor-ide-browser` as a canvas that renders a local HTML file.
- Finalize `sub-specs/technical-spec.md` § UAT Protocols for Cursor and Codex Desktop against the rows as written.

### Story 3: Tests, `prototype.md` reconciliation, and issue note

- Extend `test_verification_records` with a negative case and confirm all four parametrizations pass. Update `test_adapter_canvas_row` keywords if Story 1 or 2 changed a pinned word and did not already update the test.
- Reconcile `commands/prototype.md` Step 2.5 with the records (Business Rule 7). Record any change in `drift-log.md`.
- Append `### Verification` under `## Resolution` in the origin issue.

## Implementation Approach

- **Order.** Story 1, then Story 2, then Story 3. Stories 1 and 2 both add cases to `test_verification_records` in `scripts/tests/test_platform_neutral_names.py` (Story 1 the `claude-code` case, Story 2 the other three), so they run sequentially.
- **Evidence over inference.** Every record cell is something that was read on a dated page or seen in a run. When a page does not say, the cell says "not documented" and the status stays unverified.
- **Shared constants.** Reuse `section`, `first_table`, and `cells` helpers from `scripts/tests/test_platform_neutral_names.py`.
- **Verification.** `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` after every story.
