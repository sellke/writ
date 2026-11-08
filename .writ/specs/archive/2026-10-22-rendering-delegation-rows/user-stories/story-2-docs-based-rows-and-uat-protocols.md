# Story 2: Cursor, Codex, and OpenClaw Rows from First-Party Docs with UAT Protocols

> **Status:** Completed ✅
> **Commit:** 45ce90e7df1737ed0dc7cc2d4afa19bc93c4ee04
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer running UAT on Cursor and Codex Desktop, and a `/prototype` user on those platforms **I want to** each adapter's `canvas-preview` row to name the renderer `/prototype` delegates to, cite first-party docs, and carry a dated status, with a UAT protocol short enough to finish in one sitting **So that** each row claims only what the docs or a live run supports, and a record reads `verified` only after an observed run.

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given the `canvas-preview` rows in `adapters/cursor.md`, `adapters/codex.md`, and `adapters/openclaw.md`, when each row is checked against the first-party page its record cites, then each row stays one line in its existing tool table with `` `canvas-preview` `` as its first cell, claims only what that page supports, names `cursor-ide-browser` only if the page documents it as a canvas that renders a local HTML file (otherwise the row names the HTML-file floor), and keeps the degradation clause verbatim `[AC-2.1]`
- [x] Given the Cursor, Codex, and OpenClaw adapters, when each gets a `#### Verification record — 2026-10-22` after its tool table, then the table columns are `Check | Platform & version | Observed | Source | Status`, every Source cell starts with `https://`, a silent page is written as "not documented" in the Observed cell with the docs index URL in Source, every Status cell is `unverified 2026-10-22 (pending UAT)` for Cursor and Codex or `unverified 2026-10-22 (no deployment)` for OpenClaw `[AC-2.2]`
- [x] Given the Codex `canvas-preview` row, when it is rewritten, then its cell reads a "CLI:" clause followed by a "Desktop:" clause, the CLI clause keeps "`Write` one self-contained HTML file per draft to `.writ/prototypes/<date>-<slug>/`", the Desktop clause states only what the cited Codex docs say about rendering, the row still contains `.writ/prototypes/<date>-<slug>/` and `HTML`, and `test_adapter_canvas_row[codex]` passes without a keyword change `[AC-2.3]`
- [x] Given `sub-specs/technical-spec.md` § UAT Protocols, when `/create-uat-plan` reads it, then the Cursor and Codex Desktop protocols each state a precondition, a `--diverge` run on the same fixed sample idea, what to look for, and the record edit on pass and on fail, and the on-pass edit writes `verified <date>` in the Status cell with the version in the Platform & version cell `[AC-2.4]`
- [x] Given the finished changes, when `uv run --python 3.9 pytest`, the bash test loop, and `bash scripts/eval.sh` run outside the sandbox, then `test_verification_records` passes for `cursor`, `codex`, and `openclaw`, `test_adapter_canvas_row` passes for every adapter, eval reports 0 findings, and the diff touches neither `adapters/claude-code.md` nor `commands/prototype.md` `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Write the failing record-format test first. In `scripts/tests/test_platform_neutral_names.py`, extend `test_verification_records` (added by Story 1 with the `claude-code` case) so its parametrization also covers `cursor`, `codex`, and `openclaw`, using the `section`, `first_table`, and `cells` helpers. Assert: the heading `#### Verification record — YYYY-MM-DD` exists in the adapter file; the first table under it has at least one data row; every Status cell matches `^(verified|unverified) \d{4}-\d{2}-\d{2}( \((pending UAT|no deployment)\))?$`; every Source cell starts with `https://`. Assertion messages name the adapter and the failing cell. Run it and confirm it fails on the current files `[AC-2.2]`
- [x] 2.2 Collect first-party sources and read each on 2026-10-22: Cursor's browser or canvas tool docs, the Codex app's rendering surface (or its absence), and OpenClaw's file-write capability. Keep one URL and one observation per check. Where a page is silent, the Observed cell says "not documented". Do not cite a URL that 404s: find the current page, or cite the docs index and write "no first-party page found on 2026-10-22" in Observed `[AC-2.1, AC-2.2]`
- [x] 2.3 Write `#### Verification record — 2026-10-22` into each adapter, after its tool table and before the next heading: `adapters/cursor.md` (after § Native Tool Availability's table, before `### Recommendation Interaction Mapping`), `adapters/codex.md` (after `### Quick reference — orchestration primitives`, before `### Writ agents ↔ Codex TOML`), `adapters/openclaw.md` (after § Quick Reference's table, before `## Detailed Mappings`). Use the five columns. Leave a blank line between the tool table and the record. The Platform & version cell names the platform and the docs read date; claim no version without a run `[AC-2.2]`
- [x] 2.4 Rewrite the Codex `canvas-preview` row in `adapters/codex.md` (find it by its first cell, never by line number) to the shape in `technical-spec.md` § Codex Row Shape. The Desktop clause states only what the cited docs support, for example that they do not document rendering of `.writ/prototypes/` HTML files. Keep the row on one line in the existing table, keep the degradation clause verbatim, keep `.writ/prototypes/<date>-<slug>/` and `HTML` `[AC-2.3]`
- [x] 2.5 Set the Cursor row in `adapters/cursor.md` § Native Tool Availability to what the cited docs support. Keep `cursor-ide-browser` only if the page documents it as a canvas that renders a local HTML file; otherwise name the HTML-file floor and keep the degradation clause. Check the OpenClaw row (`adapters/openclaw.md` § Quick Reference) against its cited page and change it only if the docs contradict it. If a pinned word changes, update `test_adapter_canvas_row[<adapter>]` in the same commit as the row `[AC-2.1]`
- [x] 2.6 Finalize `sub-specs/technical-spec.md` § UAT Protocols for Cursor and Codex Desktop against the rows as written. Each protocol keeps: precondition, the `--diverge` run on the same sample idea, what to look for, and the record edit on pass and on fail. Change the on-pass edit to write `verified <date>` in the Status cell and the version in the Platform & version cell, because the status grammar rejects `verified <date>, Cursor <version>`. Align each "look for" with the row's wording `[AC-2.4]`
- [x] 2.7 Verify. Run `uv run --python 3.9 pytest`, then `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, then `bash scripts/eval.sh` outside any sandbox. Confirm 0 findings and no `FAIL` line. Run `git diff --stat` and confirm no change to `adapters/claude-code.md` or `commands/prototype.md` `[AC-2.5]`

## Notes

- **Order and files.** Story 1 lands first: it adds `test_verification_records` with the `claude-code` case and edits `adapters/claude-code.md`. This story extends that one function with its three adapters and does not touch `adapters/claude-code.md`. Story 3 depends on this story and reads the three records and the protocols. Nobody adds a second copy of the test.
- **Source cell.** Must start `https://`. "not documented" and "no first-party page found" go in Observed, never in Source. Either one in Source fails the test.
- **Status cell.** The grammar is anchored at both ends, so `verified 2026-10-22, Cursor 2.x` fails. The version goes in the Platform & version cell. Spec Business Rule 8 and technical-spec.md § Verification Record Format state the same anchored grammar.
- **Pinned words.** `test_adapter_canvas_row[cursor]` pins `cursor-ide-browser`. `test_adapter_canvas_row[codex]` pins `.writ/prototypes/<date>-<slug>/` and `HTML`. Changing a pinned word updates the test in the same commit.
- **Codex Desktop.** A second surface of the Codex product. The clause goes in the existing Codex row, not a new adapter. The CLI protocol path is `.codex/commands/prototype.md`, per the native-integration note in `adapters/codex.md`.
- **Known state, 2026-10-22 (from spec audit).** The Codex app overview (learn.chatgpt.com/docs/app) lists a browser and "interactive visuals" without describing HTML preview. Cursor's docs describe a browser tool; no canvas page was found. The rows may end at the HTML-file floor with the record saying canvas is unverified. That outcome is valid.
- **Context hints.** The Context for Agents section uses only the four categories `story-context.py` recognizes. Technical references live here: `sub-specs/technical-spec.md` § UAT Protocols (maintainer, Story 2 writes), § Codex Row Shape (Story 2), and § Verification Record Format.
- **Commit size.** One commit per adapter file, then one for the protocols, then one for the test if it lands separately. Small commits, per the project principle.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths`
- **Business rules:** `spec.md → ## Business Rules (Expanded)`
- **Experience:** `spec.md → ## Experience Design → ### State Catalog`

## What Was Built

**Implementation Date:** 2026-10-22

### Files Created

None.

### Files Modified

- **`adapters/cursor.md`** — the `canvas-preview` row now names the HTML-file floor (`.writ/prototypes/<date>-<slug>/`, one self-contained HTML file per draft) and what the Browser docs support (the `@browser` pane and `browser_navigate` open only allowlisted origins such as `http://localhost:3000`); it no longer names `cursor-ide-browser`, which neither Cursor page documents. `#### Verification record — 2026-10-22` added after the Native Tool Availability table: Browser tool row and Canvas row, both `unverified 2026-10-22 (pending UAT)`, citing https://cursor.com/docs/agent/tools/browser and https://cursor.com/docs/agent/tools/canvas.
- **`adapters/codex.md`** — the row is now "CLI: `Write` one self-contained HTML file per draft to `.writ/prototypes/<date>-<slug>/`. Desktop: the app's docs say it opens workspace files and has a browser, and do not document rendering an HTML draft; write the same files." Notes cell per § Codex Row Shape. Record added after the orchestration-primitives table: CLI row (https://learn.chatgpt.com/docs/cli) and Desktop row (https://learn.chatgpt.com/docs/app, reached by a 308 redirect from the Codex app URL), both `unverified 2026-10-22 (pending UAT)`.
- **`adapters/openclaw.md`** — row unchanged (the Tools page does not contradict it). Record added after the Quick Reference table: one row, `unverified 2026-10-22 (no deployment)`, citing https://docs.openclaw.ai/tools and noting the documented `message(action=send, media=<path>)` publish path.
- **`.writ/specs/2026-10-22-rendering-delegation-rows/sub-specs/technical-spec.md`** — § UAT Protocols rewritten against the rows: shared sample idea, Cursor and Codex Desktop protocols each with precondition, `--diverge` run, look-for aligned to the row wording, on-pass (`verified <date>` in Status, version in Platform & version) and on-fail edits, plus a CLI-row edit for Codex.
- **`scripts/tests/test_platform_neutral_names.py`** — `VERIFICATION_RECORDS` is derived from `ADAPTER_TABLES` (all four adapters); the cursor keywords are now `.writ/prototypes/<date>-<slug>/` and `HTML`; new tests `test_cursor_row_names_the_floor` (AC-2.1), `test_codex_row_has_cli_and_desktop_clauses` (AC-2.3), `test_uat_protocol[Cursor|Codex Desktop]` (AC-2.4); `test_verification_records` cites AC-2.2 and AC-2.5.
- **`spec-lite.md`** — Shadow Paths "Nil input" line amended (DEV-003). **`drift-log.md`** — DEV-003 appended.

### Implementation Decisions

1. **Cursor row drops the vendor tool name** — neither first-party page documents `cursor-ide-browser` or a canvas that renders a local HTML file, so AC-2.1 puts the row at the HTML-file floor; the pinned keyword moved in the same commit. The name survives only in the record's Observed cell as the thing the docs do not mention.
2. **Codex Desktop clause states the docs' silence** — the app page lists opening workspace files and a browser; rendering an HTML draft is not documented, so the clause says so rather than promising a preview.
3. **OpenClaw row left alone** — the docs document `write` and a media-send publish path; nothing contradicts the row, and task 2.5 changes it only on contradiction.
4. **Specific pages cited for silence** — the page read and found silent is the Source; the index URL is reserved for a missing page (DEV-003).
5. **Two evaluator residuals fixed in place** — the Codex record's CLI row gained a UAT edit path, and two Check cells that read "one HTML draft per file" now read "one HTML file per draft".

### Test Results

**Verification:** Automated, test-first (extended `test_verification_records` red for cursor, codex, openclaw before the records existed: 3 failed, 1 passed; green after).
**Coverage:** Not measured by the script (documentation and test changes only).

- ✅ Targeted: `scripts/tests/test_platform_neutral_names.py` → 43 passed.
- ✅ Full pytest (3.9): 2784 passed, 2 skipped.
- ✅ Bash tests: 45/45.
- ✅ `bash scripts/eval.sh`: Findings 0, run errors 0.
- ✅ Gate 3 review-override, Gate 3.5 drift-format, Gate 4 authenticity: pass; coverage, app-verify, docs-check: unverifiable (no coverage report, no recipe, no public exports). ac-trace: 0 findings.
- ✅ `git diff --stat`: no change to `adapters/claude-code.md` or `commands/prototype.md`.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-003)
- **Security:** Clean
- **Boundary Compliance:** all five changed files are owned; `adapters/claude-code.md` and `commands/prototype.md` untouched (Story 1's `> **Commit:**` header line landed in this commit as provenance bookkeeping).
- gate3-route: evaluator-agent. review-panel: off. arch-lint: none — see .writ/docs/architecture-lint.md.
- Gate 0 arch-check: pass (rederived proceed). Gate 2: no linter configured; build-smoke unverifiable (unsupported_stack). Gate 2.5: cross-component; boundary-map crossings 0.
- Residuals left as taste: the OpenClaw row keeps "Includes a run that cannot write files." (Writ's own degradation condition, not a docs claim) and does not mention the media-send path; `test_uat_protocol` binds to the UAT heading text (same precedent as `test_issue_resolution`).

### Deviations from Spec

- **[DEV-003] Silent-page rows cite the specific page, not the docs index URL** — Severity: Small
  - Spec said: a silent page is written as "not documented" in Observed with the docs index URL in Source.
  - Implementation did: the page that was read and found silent is cited, with "not documented" in Observed.
  - Resolution: Auto-amended
  - Spec amendment: spec-lite.md Shadow Paths "Nil input" line.
