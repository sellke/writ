# UAT Plan: Rendering-Delegation Rows

> **Generated:** 2026-10-22
> **Spec:** `.writ/specs/2026-10-22-rendering-delegation-rows/`
> **Stories Covered:** 3 of 3 completed
> **Total Scenarios:** 12
> **Verification recipe:** does not apply. Writ is markdown plus Python and bash scripts with no application to boot, so no `.writ/docs/app-verification.md` was drafted, saved, or bound. Every scenario is `human — no recipe`.

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

**Conventions for this plan:**

- The point of this plan is Scenarios 7 and 8: the Cursor and Codex Desktop protocols the lane could not run. Scenarios 1, 2, 4, 5, 6, 11, 12 confirm the records and rows read as recorded; 9 and 10 run the tests; 3 is a Claude Code confirmation.
- **Never run `install.sh` or `update.sh` in the Writ repo.** `.claude/` and `.cursor/` there are symlinks into the source. The live scenarios install from a clone into a sample project inside `$W`.
- Every helper refuses to run unless the shell is inside `$W`. `$REPO` is cloned from and never written to. Run the plan in `bash` on macOS (`sed -i ''`), outside any sandbox.
- Paste this setup block once per shell. Stop if the first line does not print `W=/...`:

  ```bash
  W=$(mktemp -d "${TMPDIR:-/tmp}/writ-uat-rows.XXXXXX") && cd "$W" && echo "W=$W"
  REPO=/Users/asellke/Projects/writ            # read only: cloned from, never edited, never installed into
  CL="$W/clone"; git clone -q "$REPO" "$CL"    # committed tree on the current branch
  SAMPLE="$W/sample"                            # the project the live protocols install Writ into
  mkdir -p "$SAMPLE/src/components" && cd "$SAMPLE" && git init -q \
    && printf '<label class="toggle"><input type="checkbox"> Dark mode</label>\n' > src/components/DarkModeToggle.html \
    && git add -A && git commit -qm "sample UI component" && cd "$W"
  inW() { case "$PWD/" in "$W"/*) ;; *) echo "refusing: $PWD is outside $W" >&2; return 1;; esac; }
  # install <cursor|claude|codex>: install Writ from the clone into $SAMPLE, never into $REPO
  install() { inW && (cd "$SAMPLE" && bash "$CL/scripts/install.sh" --platform "$1" --no-commit); }
  # pt <pytest args>: run pytest on Python 3.9 inside the clone
  pt() { inW && (cd "$CL" && uv run --python 3.9 pytest "$@"); }
  # rec <adapter>: the adapter's canvas-preview row, then its verification record
  rec() { inW && grep -n '^| `canvas-preview`' "$CL/adapters/$1.md" \
          && awk '/^#### Verification record — /{p=1} p&&/^(### |---)/{exit} p' "$CL/adapters/$1.md"; }
  # reset: undo every edit to tracked files in the clone; prints nothing when clean
  reset() { inW && git -C "$CL" checkout -q -- . && git -C "$CL" status --short; }
  ```

- Record edits a protocol calls for (Scenarios 7 and 8) are made by hand in your Writ checkout's `adapters/*.md`, never through a helper and never in `$CL`.
- Expected output was observed on 2026-10-22 against `5da0b61` (branch `phase/14-front-door-and-distribution`); `21833ba` is the commit before Story 1, so diffs against it show what the spec changed. After each scenario that edits the clone, run `reset` and confirm it prints nothing. When done: `rm -rf "$W"`.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Claude Code Live Verification and Record | ✅ Covered | 3 | AC: 2, Errors: 0, Shadow: 0, Edge: 0, Experience: 1 |
| Story 2: Cursor, Codex, and OpenClaw Rows from First-Party Docs with UAT Protocols | ✅ Covered | 5 | AC: 3, Errors: 0, Shadow: 0, Edge: 0, Experience: 2 |
| Story 3: Verification-Record Tests, prototype.md Reconciliation, and Issue Note | ✅ Covered | 4 | AC: 3, Errors: 0, Shadow: 1, Edge: 0, Experience: 0 |

The technical spec's Error & Rescue Map is "Not required" (documentation and tests only), so there are no error scenarios. Shadow paths and edge cases that a scenario already exercises are named on its **Source** line and not counted twice. No pending stories: all three are Completed ✅.

---

## Story 1: Claude Code Live Verification and Record

### Scenario 1: The Claude Code record reads as recorded

**Source:** Acceptance Criteria (AC-1.3, AC-1.5) — Story 1; State Catalog "Claude Code, interactive desktop session" and "Claude Code, headless"; Edge case "`verified` without a version"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `rec claude-code`
2. `grep -n 'canvas-preview\|Verification record\|^### Agent Paths' "$CL/adapters/claude-code.md"`

**Expected Result:**
- Heading `#### Verification record — 2026-10-22`; header `| Check | Platform & version | Observed | Source | Status |`; four data rows: publish as an artifact, open in the preview (Browser) pane, native design surface from a command run, headless `claude -p`.
- Every Platform cell names `Claude Code 2.1.308 (\`claude --version\`)` and `desktop app session`; no `verified` row lacks a version.
- Rows 1–3: `verified 2026-10-22`. Row 4: `unverified 2026-10-22` with no parenthetical; its Platform cell says `-p` was not run; Observed says the docs list `-p` among the contexts where artifacts are off and that a headless run takes the row's no-renderer clause.
- Sources, in order: `https://code.claude.com/docs/en/artifacts`, `.../desktop#preview-your-app`, `.../artifacts#draft-a-design-canvas`, `.../artifacts#availability`.
- Observed cells claim only what was seen: row 2 says a screenshot of the `file://` tab was refused and that the page rendered when served over `http://127.0.0.1`; row 3 says the Claude Design type was listed with a `type_url`, nothing published, no canvas created.
- Step 2 line numbers ascend: the `canvas-preview` row, a blank line, the record heading, then `### Agent Paths`.

**Implementation Reference:** Story 1 — `adapters/claude-code.md` § Tool Mapping → Quick Reference; `test_claude_code_record_checks`.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: plan drift: a `Plan Mode` row added by a later spec now sits between the `canvas-preview` row (line 221) and the blank line before the record heading (224); order still ascends 221 < 224 < 233 (`### Agent Paths`). Record matches: four rows, every Platform cell names Claude Code 2.1.308 (`claude --version`) and desktop app session, rows 1-3 `verified 2026-10-22`, row 4 `unverified 2026-10-22` with `-p` not run, the four Sources in order, row 2 file:// screenshot refused and http://127.0.0.1 render, row 3 type listed with a `type_url` and nothing published.

---

### Scenario 2: The Claude Code `canvas-preview` row states facts, not status

**Source:** Acceptance Criteria (AC-1.4) — Story 1; Interaction Pattern "Rows state facts; records state evidence"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `grep -c '^| `canvas-preview`' "$CL/adapters/claude-code.md"`
2. `grep '^| `canvas-preview`' "$CL/adapters/claude-code.md"`
3. `git -C "$CL" diff 21833ba 5da0b61 -- adapters/claude-code.md | grep '^[-+]| `canvas-preview`'`

**Expected Result:**
- Step 1: `1`. The row is one line whose first cell is `` `canvas-preview` ``.
- Step 2: mapping cell `An artifact, or the preview pane`; notes cell ends with `No renderer: write a structural description of each draft and say the drafts were not rendered.`; the word `verified` does not appear in the row.
- Step 3 prints nothing: the row did not change across the spec's commits (no observation contradicted it).

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: count 1; row maps to `An artifact, or the preview pane`, ends with the no-renderer clause, contains no `verified`; the 21833ba..5da0b61 diff grep printed nothing.

---

### Scenario 3: `/prototype --diverge` on Claude Code desktop renders where the row says

**Source:** Experience Design (Moment of truth; State Catalog "Claude Code, interactive desktop session") — Story 1; traces AC-1.1, AC-1.2
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Claude Code desktop app installed; setup block pasted.

**Steps:**
1. `install claude`, then `ls "$SAMPLE/.claude/commands/prototype.md"`.
2. `echo "$SAMPLE"`; open that folder in the Claude Code desktop app.
3. Run `/prototype --diverge "a settings page with a dark-mode toggle"` and answer the discovery questions briefly.
4. At Step 2.5, note where each draft renders and what the agent says about it.
5. `ls "$SAMPLE"/.writ/prototypes/*/`

**Expected Result:**
- One self-contained HTML file per draft under `.writ/prototypes/<date>-<slug>/`, each path given to you.
- Drafts render as an artifact or in the Browser (preview) pane, as the row says; or the agent says plainly the drafts were not rendered and gives a structural description per draft. Silent degradation is a Fail.
- On a render: nothing to edit; the record's rows already read `verified 2026-10-22`.
- On no render in a desktop session: that contradicts record rows 1–2. Add a new row dated today with the observation to the record in your Writ checkout; do not rewrite the 2026-10-22 rows. File an issue.

**Implementation Reference:** Story 1 — `commands/prototype.md` Step 2.5 → "Render through the platform"; `adapters/claude-code.md` record rows 1–2.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 2: Cursor, Codex, and OpenClaw Rows from First-Party Docs with UAT Protocols

### Scenario 4: The Cursor record reads as recorded

**Source:** Acceptance Criteria (AC-2.2) — Story 2; State Catalog "Cursor, before UAT"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `rec cursor`
2. `grep -n 'canvas-preview\|Verification record — 2026-10-22\|^### Recommendation Interaction Mapping' "$CL/adapters/cursor.md"`

**Expected Result:**
- Heading `#### Verification record — 2026-10-22` after the Native Tool Availability table (blank line between) and before `### Recommendation Interaction Mapping`; Step 2 line numbers ascend in that order. (Cursor also carries an unrelated `Verification record — 2026-09-03` under § Sub-Agent Models; the test reads only the record inside the tool-table section.)
- Two rows. "Browser tool renders a local HTML draft" → Source `https://cursor.com/docs/agent/tools/browser`. "Canvas renders a local HTML draft from a command run" → Source `https://cursor.com/docs/agent/tools/canvas`.
- Both Platform cells read `Cursor, docs read 2026-10-22 (no run)`: no version is claimed. Both Status cells read `unverified 2026-10-22 (pending UAT)`.
- Observed cells report what the pages document (`@browser`, `browser_navigate`, an origin allowlist with `http://localhost:3000`, the settings "Enable Browser Automation Features" and "Browser Origin Allowlist") and end in "not documented" for rendering a local HTML file. `cursor-ide-browser` appears only as a tool the docs do not mention.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: two rows, both Platform `Cursor, docs read 2026-10-22 (no run)` and Status `unverified 2026-10-22 (pending UAT)`, Sources .../tools/browser and .../tools/canvas; lines ascend 155 < 158 < 165; Observed names `@browser`, `browser_navigate`, `http://localhost:3000` and both settings, and `cursor-ide-browser` only as undocumented. Wording note: the Browser row's Observed ends "no rendering of a local HTML file are documented", not the literal "not documented" (same meaning; text unchanged since 5da0b61).

---

### Scenario 5: Cursor, Codex, and OpenClaw rows claim only what the docs support

**Source:** Acceptance Criteria (AC-2.1, AC-2.3) — Story 2; Business Rules 2, 3, 6
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `for a in cursor codex openclaw; do echo "== $a"; grep -c '^| `canvas-preview`' "$CL/adapters/$a.md"; grep '^| `canvas-preview`' "$CL/adapters/$a.md"; done`
2. `git -C "$CL" diff 21833ba 5da0b61 -- adapters/openclaw.md | grep -c '^[-+]| `canvas-preview`'`

**Expected Result:**
- Count `1` for each adapter; each row is one line; each notes cell ends with `No renderer: write a structural description of each draft and say the drafts were not rendered.`; no row contains `verified`.
- Cursor: names `.writ/prototypes/<date>-<slug>/` and "one self-contained HTML file per draft", says the Browser tool opens only allowlisted origins such as `http://localhost:3000`, and says no canvas tool that renders a local HTML file is documented. `cursor-ide-browser` is absent.
- Codex: the mapping cell begins exactly ``CLI: `Write` one self-contained HTML file per draft to `.writ/prototypes/<date>-<slug>/`.`` followed by ` Desktop: the app's docs say it opens workspace files and has a browser, and do not document rendering an HTML draft; write the same files.`
- OpenClaw: `` `Write({ path: ".writ/prototypes/<date>-<slug>/<draft>.html" })` ``, one self-contained HTML file per draft. Step 2 prints `0`: the row is unchanged.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: count 1 for cursor, codex, openclaw; each row ends with the no-renderer clause and has no `verified` or `cursor-ide-browser`; Cursor names the folder, the allowlist and no canvas tool; Codex mapping cell matches the CLI and Desktop clauses exactly; OpenClaw row as expected and step 2 printed `0`.

---

### Scenario 6: The Codex and OpenClaw records read as recorded

**Source:** Acceptance Criteria (AC-2.2) — Story 2; Shadow Path "Nil input" (a silent page → "not documented" in Observed, the page read in Source; DEV-003)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `rec codex`
2. `rec openclaw`
3. `grep -n 'Verification record\|^### Writ agents\|^## Detailed Mappings' "$CL/adapters/codex.md" "$CL/adapters/openclaw.md"`
4. `grep -c '| not documented |' "$CL"/adapters/{cursor,claude-code,codex,openclaw}.md`

**Expected Result:**
- Codex: two rows. CLI row: Platform `Codex CLI, docs read 2026-10-22 (no run)`, Source `https://learn.chatgpt.com/docs/cli`, Observed says writing inside the workspace is documented and HTML preview is not. Desktop row: Platform `Codex Desktop, docs read 2026-10-22 (no run)`, Source `https://learn.chatgpt.com/docs/app`, Observed notes the 308 redirect from `https://developers.openai.com/codex/app` and that rendering a local HTML file is not documented. Both Status `unverified 2026-10-22 (pending UAT)`. The record precedes `### Writ agents ↔ Codex TOML`.
- OpenClaw: one row. Platform `OpenClaw, docs read 2026-10-22 (no deployment)`, Source `https://docs.openclaw.ai/tools`, Observed names `read`, `write`, `edit`, `apply_patch` and `message(action=send, media=<path>)`, Status `unverified 2026-10-22 (no deployment)`. The record precedes `## Detailed Mappings`.
- Step 4: `0` for every file. "not documented" never fills a Source cell; it appears only inside Observed text.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: Codex two rows and OpenClaw one row match the plan (Platform, Source, Observed, Status cells); record before `### Writ agents ↔ Codex TOML` (152 < 159) and before `## Detailed Mappings` (22 < 30); `| not documented |` count 0 in all four adapters.

---

### Scenario 7: Cursor protocol — run `/prototype --diverge` and flip the record

**Source:** Experience Design (State Catalog "Cursor, before UAT" → "Cursor, after UAT"; Moment of truth) — Story 2; technical-spec.md § UAT Protocols → Cursor; traces AC-2.4
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Cursor 2.1 or later; setup block pasted.
- Cursor settings: "Enable Browser Automation Features" on. Optional, so a draft can have an allowlisted origin: in a second shell run `cd "$SAMPLE" && python3 -m http.server 3000`, and add `http://localhost:3000` to "Browser Origin Allowlist".

**Steps:**
1. `install cursor`, then `ls "$SAMPLE/.cursor/commands/prototype.md"`.
2. `echo "$SAMPLE"`; open that folder in Cursor. Note the version (Cursor → About Cursor).
3. In Agent chat run `/prototype --diverge "a settings page with a dark-mode toggle"` and answer the discovery questions briefly.
4. At Step 2.5 note: the paths the agent gives; whether a draft opens in the Browser pane (`@browser`, `browser_navigate` on a served origin) or in a Canvas; which tool name the agent reports using; or whether it says nothing rendered and gives a structural description per draft.
5. `ls "$SAMPLE"/.writ/prototypes/*/`

**Expected Result:**
- One self-contained HTML file per draft under `.writ/prototypes/<date>-<slug>/`, each path given to you.
- Either a draft renders in a surface you can name, or the agent says plainly the drafts were not rendered and describes each. Silent degradation is a Fail of the run, recorded as "nothing rendered" below.

**Record edit** (by hand, in your Writ checkout: `adapters/cursor.md` → `#### Verification record — 2026-10-22`):
- **Pass (a draft rendered):** in the row for the surface that rendered (Browser tool row or Canvas row): Status → `verified <today>`; Platform & version → `Cursor <version>, run <today>`; Observed → what rendered and how. Then set the `canvas-preview` row's mapping to the tool the agent used, keeping `.writ/prototypes/<date>-<slug>/`, `HTML`, and the degradation clause at the end of the notes cell. Never write `verified <today>, Cursor <version>` in Status: the grammar rejects it.
- **Fail (nothing rendered):** both rows: Status → `unverified <today>` (drop `(pending UAT)`); Platform & version → `Cursor <version>, run <today>`; Observed → the observation. Leave the row text: it already names the HTML-file floor.
- **Follow-on either way:** the origin issue's `- \`adapters/cursor.md\`:` line under `### Verification` and the cursor pair in `test_issue_verification_note` pin `unverified 2026-10-22 (pending UAT)`. Update both in the same commit, then `uv run --python 3.9 pytest scripts/tests/test_platform_neutral_names.py` must pass.

**Implementation Reference:** Story 2 — `adapters/cursor.md` record rows "Browser tool …" and "Canvas …"; `test_cursor_row_names_the_floor`; `scripts/tests/test_platform_neutral_names.py::test_issue_verification_note`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 8: Codex Desktop protocol — run the prototype command and flip the record

**Source:** Experience Design (State Catalog "Codex Desktop, before UAT" → "Codex Desktop, after UAT") — Story 2; technical-spec.md § UAT Protocols → Codex Desktop; traces AC-2.4
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Codex Desktop (the desktop app `https://developers.openai.com/codex/app` redirects to) installed and signed in; `codex --version` works; setup block pasted.

**Steps:**
1. `install codex`, then `ls "$SAMPLE/.codex/commands/prototype.md" "$SAMPLE/AGENTS.md"`.
2. `echo "$SAMPLE"`; open that folder as the workspace in Codex Desktop. Note the app version (About) and `codex --version`.
3. Ask: `Follow .codex/commands/prototype.md with --diverge "a settings page with a dark-mode toggle"` and answer the discovery questions briefly.
4. At Step 2.5 note: the paths given; whether the app opens or previews any draft and by what mechanism (file preview, browser, none); or whether the agent says nothing rendered and gives a structural description per draft.
5. `ls "$SAMPLE"/.writ/prototypes/*/`

**Expected Result:**
- One self-contained HTML file per draft under `.writ/prototypes/<date>-<slug>/`, each path given to you.
- Either a draft is opened or previewed by a mechanism you can name, or the agent says plainly the drafts were not rendered and describes each.

**Record edit** (by hand, in your Writ checkout: `adapters/codex.md` → `#### Verification record — 2026-10-22`):
- **Pass (a draft rendered):** Desktop row: Status → `verified <today>`; Platform & version → `Codex Desktop <app version>, run <today>`; Observed → the mechanism. Rewrite the row's Desktop clause to that mechanism. The mapping cell must still begin exactly ``CLI: `Write` one self-contained HTML file per draft to `.writ/prototypes/<date>-<slug>/`.`` and contain ` Desktop: `.
- **Fail (nothing rendered):** Desktop row: Status → `unverified <today>`; Platform & version → `Codex Desktop <app version>, run <today>`; Observed → the observation. Leave the Desktop clause: it already says rendering is not documented.
- **CLI row, pass or fail:** when the files appeared under `.writ/prototypes/<date>-<slug>/`: Status → `verified <today>`; Platform & version → `Codex CLI <codex --version>, run <today>`; Observed → the paths written.
- **Follow-on either way:** the origin issue's `- \`adapters/codex.md\`:` line and the codex pair in `test_issue_verification_note` pin `unverified 2026-10-22 (pending UAT)`. Update both in the same commit; pytest must pass.

**Implementation Reference:** Story 2 — `adapters/codex.md` record rows "CLI writes …" and "Desktop app renders …"; `test_codex_row_has_cli_and_desktop_clauses`; `test_uat_protocol[Codex Desktop]`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 3: Verification-Record Tests, prototype.md Reconciliation, and Issue Note

### Scenario 9: Record, row, and protocol tests pass on Python 3.9

**Source:** Acceptance Criteria (AC-3.1, AC-3.3) — Story 3; Edge case "Two record headings in one adapter → keep one"
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `uv` installed.

**Steps:**
1. `pt scripts/tests/test_platform_neutral_names.py -q`
2. `pt scripts/tests/test_platform_neutral_names.py -v -k "verification_records or check_record or uat_protocol or render_table or issue_verification" 2>&1 | grep -E 'PASSED|FAILED'`
3. `grep -c '^#### Verification record — 2026-10-22' "$CL"/adapters/{cursor,claude-code,codex,openclaw}.md`

**Expected Result:**
- Step 1: `48 passed` (the count grows if tests are added later), no failures.
- Step 2: PASSED for `test_verification_records[cursor]`, `[claude-code]`, `[codex]`, `[openclaw]`; `test_check_record_rejects_bad_cells[source-not-documented]`, `[status-without-date]`, `[status-with-version]`; `test_uat_protocol[Cursor]`, `[Codex Desktop]`; `test_prototype_render_table_reconciled`; `test_issue_verification_note`. No FAILED line.
- Step 3: `1` for each of the four files: one dated record per adapter tool-table section.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: step 1 `48 passed` on CPython 3.9.6; step 2 all 11 named tests PASSED, no FAILED; step 3 `1` for each of the four adapters.

---

### Scenario 10: Removing a status date, a URL, or every row fails the test and names the adapter

**Source:** Shadow Paths (Nil input, Empty input, Upstream error) — Story 3; State Catalog "Maintainer removes a status mark or URL from a record"; traces AC-3.2
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted; `reset` prints nothing.

**Steps:**
1. Status without a date: `sed -i '' 's/| unverified 2026-10-22 (pending UAT) |$/| unverified (pending UAT) |/' "$CL/adapters/cursor.md"`, then `pt scripts/tests/test_platform_neutral_names.py -q -k "verification_records and cursor" 2>&1 | grep -E 'AssertionError|passed|failed'`, then `reset`.
2. Source that is not a URL: `sed -i '' 's#| https://cursor.com/docs/agent/tools/canvas |#| not documented |#' "$CL/adapters/cursor.md"`, then the same `pt` line, then `reset`.
3. Record with no rows: `sed -i '' '/^| Browser tool renders a local HTML draft |/d; /^| Canvas renders a local HTML draft from a command run |/d' "$CL/adapters/cursor.md"`, then the same `pt` line, then `reset`.

**Expected Result:**
- Step 1: `1 failed` and `AssertionError: adapters/cursor.md: Status 'unverified (pending UAT)' does not match the status grammar`.
- Step 2: `1 failed` and `AssertionError: adapters/cursor.md: Source 'not documented' does not start with https://`.
- Step 3: `1 failed` and `AssertionError: adapters/cursor.md: verification record has no data row`.
- Every message names the adapter and the failing cell. `reset` prints nothing after each step.

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: each mutation gave `1 failed` with the exact message: Status 'unverified (pending UAT)' does not match the status grammar / Source 'not documented' does not start with https:// / verification record has no data row, each prefixed `adapters/cursor.md:`; `reset` printed nothing after each step.

---

### Scenario 11: `commands/prototype.md` Step 2.5 is untouched and the drift log has no Step 2.5 entry

**Source:** Acceptance Criteria (AC-3.4) — Story 3; Business Rule 7
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `git -C "$CL" diff --stat 21833ba 5da0b61 -- commands/prototype.md`
2. `awk '/^#### Render through the platform/{p=1} p&&/^#### Present/{exit} p' "$CL/commands/prototype.md"`
3. `grep -c cursor-ide-browser "$CL/commands/prototype.md"`
4. `grep '^#### \[DEV-' "$CL/.writ/specs/2026-10-22-rendering-delegation-rows/drift-log.md"`

**Expected Result:**
- Step 1 prints nothing: the file did not change across the spec's commits.
- Step 2: a three-row table in this order: `Native artboard/design surface`, `` `canvas-preview` (the adapter maps it) ``, `Neither`; followed by the line ending "Never degrade silently."
- Step 3: `0`.
- Step 4: three titles, DEV-001 through DEV-003; none names `prototype.md` or Step 2.5. (Business Rule 7 did not fire: the Claude Code record shows the Claude Design type listable from a command run, so the first row stands.)

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: step 1 empty diff; step 2 three-row table in order (Native artboard/design surface, `canvas-preview` (the adapter maps it), Neither) then the line ending "Never degrade silently."; step 3 `0`; step 4 DEV-001..DEV-003, none names prototype.md or Step 2.5.

---

### Scenario 12: The origin issue carries `### Verification` under `## Resolution`

**Source:** Acceptance Criteria (AC-3.5) — Story 3; Business Rule 9
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `I="$CL/.writ/issues/bugs/2026-10-19-prototype-visual-preview-cursor-only.md"; grep -n '^## \|^### Verification' "$I"`
2. `awk '/^### Verification/{p=1} p' "$I"`
3. `pt scripts/tests/test_platform_neutral_names.py -q -k "issue_resolution or issue_verification"`

**Expected Result:**
- Step 1: `## Resolution` is the last `##` heading; `### Verification` appears once, after it.
- Step 2: the note names `` `2026-10-22-rendering-delegation-rows` `` and the Phase 14 lane, then four lines of the form `- \`adapters/<name>.md\`: <status>`: claude-code `verified 2026-10-22` (Claude Code 2.1.308, desktop app); cursor and codex `unverified 2026-10-22 (pending UAT)`, each pointing at technical-spec.md § UAT Protocols; openclaw `unverified 2026-10-22 (no deployment)`. The closing line says `commands/prototype.md` Step 2.5 is unchanged.
- Step 3: `3 passed` (`test_issue_resolution[...]` and `test_issue_verification_note`).
- After Scenario 7 or 8 flips a record, this note and `test_issue_verification_note` must change with it (see their Follow-on lines).

**Status:** [x] Pass  [ ] Fail — **Notes:** agent run 2026-10-23 at 0b033a3: `## Resolution` (line 44) is the last `##`, `### Verification` once at 58; note names the spec and Phase 14 lane, four adapter lines with the expected statuses and protocol pointers, closing line says Step 2.5 unchanged; step 3 `3 passed`.

---
