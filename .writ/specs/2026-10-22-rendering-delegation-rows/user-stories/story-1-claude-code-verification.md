# Story 1: Claude Code Live Verification and Record

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer, or a `/prototype` user on Claude Code whose run reaches Step 2.5
**I want to** run the Claude Code render check inside the lane and record what the run observed
**So that** the Claude Code `canvas-preview` row states only behavior that was seen, backed by a dated record that names the version and the docs

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given a self-contained HTML draft (inline CSS, no network fetch) in a temp folder outside the repo, when the lane runs the Claude Code protocol in an interactive session, then the draft is attempted through the artifact mechanism and then the preview pane, each attempt records whether it rendered with a first-party Claude Code docs URL, and if neither renders the record names the degradation path and claims no render `[AC-1.1]`
- [ ] Given the same session, when the run tries to reach the native design surface from inside a command run (not by the user typing `/design`), then the record states whether a Writ command can reach it, what the run observed, and a docs URL `[AC-1.2]`
- [ ] Given the run's observations, when the record is written into `adapters/claude-code.md` under § Tool Mapping → Quick Reference, after the tool table and before `### Agent Paths`, then it is headed `#### Verification record — YYYY-MM-DD`, its table has the columns `Check | Platform & version | Observed | Source | Status`, the Platform cell carries the `claude --version` output and desktop or terminal session, every Observed cell states only what the run saw, and every Status cell matches `^(verified|unverified) \d{4}-\d{2}-\d{2}( \((pending UAT|no deployment)\))?$` `[AC-1.3]`
- [ ] Given the `canvas-preview` row in the Claude Code table, when the row is compared with the observations, then its text changes only where an observation contradicts it, it stays one line with `` `canvas-preview` `` as its first cell, it keeps the clause "No renderer: write a structural description of each draft and say the drafts were not rendered.", it does not contain the word "verified", and `test_adapter_canvas_row[claude-code]` passes `[AC-1.4]`
- [ ] Given the finished record in `adapters/claude-code.md`, when `test_verification_records[claude-code]` runs, then the record heading matches `^#### Verification record — \d{4}-\d{2}-\d{2}$`, its first table has at least one data row, every Status cell matches the status grammar, every Source cell starts with `https://`, and the test makes no network call `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write failing record-format tests for `adapters/claude-code.md` in `scripts/tests/test_platform_neutral_names.py`: add `test_verification_records[claude-code]` using the `section`, `first_table`, and `cells` helpers. Locate the table under the record heading itself, since `first_table` on the Quick Reference section returns the tool table. Assert the heading regex, at least one data row, the status grammar on every Status cell, and an `https://` prefix on every Source cell. Run it and confirm it fails on the file as it stands `[AC-1.3, AC-1.5]`
- [ ] 1.2 Run the artifact and preview-pane check. Record `claude --version` and whether the session is the desktop app or the terminal. Write `draft-a.html` (inline CSS, no network fetch, one labeled region per component) to a temp folder outside the repo. Attempt the artifact mechanism, then the preview pane. Note each outcome and the first-party Claude Code docs URL for each mechanism `[AC-1.1]`
- [ ] 1.3 Run the native design surface check from inside a command run, not by typing `/design`. Record whether a Writ command can reach it and the docs URL that describes it. If the docs name no such surface, record "not documented". If neither draft mechanism rendered (for example, a headless `claude -p` run), record the degradation path and write a structural description of each draft `[AC-1.1, AC-1.2]`
- [ ] 1.4 Write `#### Verification record — YYYY-MM-DD` into `adapters/claude-code.md` after the Quick Reference tool table (its last row is the `canvas-preview` row) and before the `### Agent Paths` heading. Find both by text, never by line number. Use the columns `Check | Platform & version | Observed | Source | Status` and one row per check, per technical-spec.md § Verification Record Format. Cite only pages read on the run date `[AC-1.1, AC-1.2, AC-1.3]`
- [ ] 1.5 Reconcile the `canvas-preview` row with the record. Change the row only where an observation contradicts it. Keep one line, the first cell, the degradation clause verbatim, and no "verified" wording. If an edit removes a pinned keyword (`artifact`, `preview pane`), update `test_adapter_canvas_row[claude-code]` in the same edit `[AC-1.4]`
- [ ] 1.6 Verify: `uv run --python 3.9 pytest` passes, including the 1.1 test. `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` prints no `FAIL` line. `bash scripts/eval.sh`, run outside any sandbox, reports 0 findings `[AC-1.4, AC-1.5]`

## Notes

- **Evidence rule.** A check the run did not reach gets `unverified YYYY-MM-DD` and the reason goes in Observed. The grammar accepts only `(pending UAT)` or `(no deployment)` in parentheses, so a reason such as `(headless)` fails the test. Neither parenthetical applies to a lane run.
- **Version.** The Platform cell carries the `claude --version` output. A `verified` row without a version passes the grammar but gets flagged in review.
- **Temp path.** The technical spec's protocol says `/tmp`. Session rules put temp files in the session scratchpad, so write `draft-a.html` there. Keep it out of the repo.
- **Docs URLs.** The spec's example host is `https://code.claude.com/docs/…`. Confirm each page exists on the run date. For a page that 404s, do not cite it. Use the docs index page as Source and say in Observed that no first-party page was found on that date.
- **Headless run.** `claude -p` has no artifact or preview pane. Record the degradation path and leave the row clause unchanged. A headless run is a valid outcome, not a failed story. Run the protocol again in an interactive session to get the render observations.
- **Native surface.** The spec does not name the design surface. Record what the run finds. Claude Code's native `/design` as a Writ feature is out of scope.
- **Step 2.5 contradiction.** If the native-surface result contradicts the first row of `commands/prototype.md` Step 2.5 ("native artboard/design surface"), record the observation in this story's What Was Built. Story 3 edits `commands/prototype.md` and `drift-log.md` (Business Rule 7). This story does not.
- **Record placement.** The record table must follow the tool table with a blank line between them. `first_table` stops at the first non-`|` line, so the tool table stays the first table in the Quick Reference section.
- **Test ownership.** This story adds `test_verification_records` with the `claude-code` case only. Story 2 extends the same function with `cursor`, `codex`, and `openclaw`; Story 3 adds a negative case. A pinned-keyword change to `test_adapter_canvas_row` is made in the same commit as the row that caused it, by whichever story made it.
- **Order.** Story 2 runs after this story (both edit `scripts/tests/test_platform_neutral_names.py`). Story 2 edits `adapters/cursor.md`, `adapters/codex.md`, `adapters/openclaw.md`, and technical-spec.md § UAT Protocols; this story does not touch those files.
- **Technical references.** technical-spec.md → ## Claude Code Protocol (lane, Story 1), ## Verification Record Format, ## Tests (Story 3).
- **Symlinks.** `.claude/` points at `adapters/` and the product source. Edit `adapters/claude-code.md` only. Do not run `install.sh` on this repo.
- **Lane.** The run must happen in Claude Code, the platform the row describes. The lane cannot run Cursor or Codex Desktop.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Nil input, Empty input, Upstream error)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rules 1 record shape, 2 one row per adapter, 3 row text follows evidence, 4 Claude Code live check, 8 tests)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Claude Code interactive and headless rows), `spec.md → ## Experience Design → ### Interaction Patterns`
