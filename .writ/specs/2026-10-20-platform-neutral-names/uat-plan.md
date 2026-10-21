# UAT Plan: Platform-Neutral Names

> **Generated:** 2026-10-21
> **Spec:** `.writ/specs/2026-10-20-platform-neutral-names/`
> **Stories Covered:** 3 of 3 completed
> **Total Scenarios:** 41
> **Verification recipe:** does not apply. Writ has no running app, so no `.writ/docs/app-verification.md` was drafted, saved, or bound. Every scenario is `human — no recipe`. The `**Automated Test:**` line on each scenario names the committed test that already asserts the same behavior, if any.

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

**Conventions for this plan:**

- **Never run `install.sh` or `update.sh` in the Writ repo.** Its `.claude/` and `.cursor/` are symlinks into the product source. Every scenario installs into a temp folder under `$W`, from a committed copy of the tree. (`update.sh` also refuses to run in the source repo.)
- Run the shell steps in `bash`, outside any sandbox. They run `git init` and `git commit` in temp folders.
- Paste this setup block once per shell. Story 1 adds one more function.

  ```bash
  REPO=/Users/asellke/Projects/writ          # read from, never installed into
  W=$(mktemp -d "${TMPDIR:-/tmp}/writ-uat.XXXXXX")
  h()  { shasum -a 256 "$1" | cut -d' ' -f1; }
  gc() { git -C "$1" -c user.name=t -c user.email=t@example.invalid add -A &&
         git -C "$1" -c user.name=t -c user.email=t@example.invalid commit -q -m "$2"; }
  EXCL=(--exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex --exclude='.writ-lanes-*'
        --exclude=__pycache__ --exclude=.venv --exclude=.pytest_cache)
  # src_copy <dir>: committed copy of what install.sh ships from (no .writ/ except .writ/docs/*.md).
  src_copy() { mkdir -p "$1"; (cd "$REPO" && tar "${EXCL[@]}" --exclude=.writ -cf - .) | (cd "$1" && tar -xf -)
    mkdir -p "$1/.writ/docs" && cp "$REPO"/.writ/docs/*.md "$1/.writ/docs/"
    git -C "$1" init -q -b main && gc "$1" "source"; }
  # full_copy <dir>: the whole tree, .writ/ included, files staged, for the gate and eval demos.
  full_copy() { mkdir -p "$1"; (cd "$REPO" && tar "${EXCL[@]}" -cf - .) | (cd "$1" && tar -xf -)
    git -C "$1" init -q -b main && git -C "$1" add -A; }
  NEW="$W/src-new"; OLD="$W/src-old"
  src_copy "$NEW"
  cp -R "$NEW" "$OLD"                                   # stand-in for the last release
  git -C "$OLD" mv commands/writ-design.md commands/design.md
  sed 's/^name: writ-design$/name: design/' "$OLD/commands/design.md" > "$W/old.md" && mv "$W/old.md" "$OLD/commands/design.md"
  gc "$OLD" "old release"
  # inst <project> <source dir> <cursor|claude|codex>
  inst() { mkdir -p "$1" && (cd "$1" && bash "$2/scripts/install.sh" --platform "$3" --no-commit); }
  # upd <project> <platform> [flags]: update from $NEW, or from $UPSTREAM when set.
  upd()  { local p="$1" pf="$2" up="${UPSTREAM:-$NEW}"; shift 2
    (cd "$p" && WRIT_REPO="$up" bash "$up/scripts/update.sh" --platform "$pf" --no-commit "$@"); }
  ```

- `$OLD` differs from `$NEW` only in the command file: `commands/design.md` with `name: design`. It is the same stand-in the committed bash test uses. Scenario 40 upgrades from the real `v0.42.0` release instead.
- Platform folders: Cursor `.cursor/`, Claude Code `.claude/`, Codex `.codex/`. Each holds a `.writ-manifest` whose lines read `<sha256>  <path>`. OpenClaw has no install path, so only the three install platforms get install and update scenarios.
- Expected output was observed on 2026-10-21 from the `phase/13-subtract-and-repair` working tree when this plan was generated. Hashes, short SHAs, line numbers, and temp paths will differ.
- **Live-session scenarios** (6–14, 22, 23, 39) need a person at Cursor, Claude Code, Codex, or OpenClaw. If you do not have a platform, mark the scenario Fail with "Not run: no <platform>" in Notes rather than leaving it blank.
- **Automated Test line:** names the test in `scripts/tests/` that asserts the behavior, `partial` when a test covers part of it, or `none — manual only`. CI runs pytest, every bash test, and `eval.sh` on each PR.
- When done: `rm -rf "$W"`.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Canvas-Preview Capability in `/prototype` and the Four Adapters | ✅ Covered | 14 | AC: 5, Errors: 4, Shadow: 1, Edge: 0, Experience: 4 |
| Story 2: Rename `/design` to `/writ-design` Across Every Reference | ✅ Covered | 9 | AC: 5, Errors: 2, Shadow: 0, Edge: 0, Experience: 2 |
| Story 3: Upgrade-Path Test, Reference Gate, and Issue Resolutions | ✅ Covered | 18 | AC: 8, Errors: 2, Shadow: 2, Edge: 4, Experience: 2 |

Error-map, shadow-path, and state-catalog items that an AC scenario already exercises are folded into that scenario and named on its **Source** line, not counted twice. Story 3's AC count includes three scenarios that check parts of AC-3.4 and AC-3.5 separately, and the suite run that AC-1.5, AC-2.5, and AC-3.5 share.

**Automated vs. manual:** 15 scenarios are asserted by a committed test, 5 partly, 9 are scripted shell checks with no committed test, and 12 need a person in a live AI session. See the table at the end.

---

## Story 1: Canvas-Preview Capability in `/prototype` and the Four Adapters

### Scenario 1: `/prototype` names the `canvas-preview` capability, not a vendor tool

**Source:** Acceptance Criteria — Story 1 (AC-1.1)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_platform_neutral_names.py` (`test_prototype_names_capability`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `sed -n '/^### Step 2: Context Scan/,/^### Step 2.5/p' "$REPO/commands/prototype.md" | grep -n 'canvas-preview'`
2. `sed -n '/^#### Render through the platform/,/^#### Present and choose/p' "$REPO/commands/prototype.md"`
3. `grep -c 'cursor-ide-browser' "$REPO/commands/prototype.md"`
4. `cd "$REPO" && uv run --python 3.9 pytest -q scripts/tests/test_platform_neutral_names.py -k prototype_names_capability`

**Expected Result:**
- Step 1 prints one line, the Figma MCP detection sentence: "if the `canvas-preview` capability (see the adapter) and `design-system.md` or a Figma MCP server are available, …"
- Step 2 shows a three-row table in this order: `Native artboard/design surface`, `` `canvas-preview` (the adapter maps it) ``, `Neither`. The sentence under it reads: "Each adapter maps `canvas-preview` to its own tool and states what to do when it has none. Never degrade silently."
- Step 3 prints `0`.
- Step 4 prints `1 passed`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — `commands/prototype.md` (§ Step 2 Figma MCP detection; § Step 2.5 → Render through the platform). Three lines changed; the file is 336 lines.

---

### Scenario 2: The Cursor adapter maps `canvas-preview` to the `cursor-ide-browser` canvas

**Source:** Acceptance Criteria — Story 1 (AC-1.2)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_platform_neutral_names.py` (`test_adapter_canvas_row[cursor]`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Find the row and the section it sits in:
   ```bash
   grep -n '^| `canvas-preview` |' "$REPO/adapters/cursor.md"
   awk '/^## /{s=$0} /^\| `canvas-preview` \|/{print s}' "$REPO/adapters/cursor.md"
   ```
2. `cd "$REPO" && uv run --python 3.9 pytest -q scripts/tests/test_platform_neutral_names.py -k "adapter_canvas_row and cursor"`

**Expected Result:**
- Step 1 prints exactly one row:
  `` | `canvas-preview` | prototype (Step 2.5) | The `cursor-ide-browser` canvas renders each draft. No renderer: write a structural description of each draft and say the drafts were not rendered. | ``
  and then `## Native Tool Availability`.
- Step 2 prints `1 passed`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — `adapters/cursor.md` § Native Tool Availability, last row of the table.

---

### Scenario 3: The Claude Code adapter maps `canvas-preview` to an artifact or the preview pane

**Source:** Acceptance Criteria — Story 1 (AC-1.3)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_platform_neutral_names.py` (`test_adapter_canvas_row[claude-code]`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Find the row and its section:
   ```bash
   grep -n '^| `canvas-preview` |' "$REPO/adapters/claude-code.md"
   awk '/^## /{s2=$0} /^### /{s3=$0} /^\| `canvas-preview` \|/{print s2 " > " s3}' "$REPO/adapters/claude-code.md"
   ```
2. `cd "$REPO" && uv run --python 3.9 pytest -q scripts/tests/test_platform_neutral_names.py -k "adapter_canvas_row and claude"`

**Expected Result:**
- Step 1 prints exactly one row:
  `` | `canvas-preview` | An artifact, or the preview pane | One self-contained HTML page per draft. No renderer: write a structural description of each draft and say the drafts were not rendered. | ``
  and then `## Tool Mapping (Cursor → Claude Code) > ### Quick Reference`.
- Step 2 prints `1 passed`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — `adapters/claude-code.md` § Tool Mapping → Quick Reference.

---

### Scenario 4: The Codex and OpenClaw adapters map `canvas-preview` to one HTML file per draft

**Source:** Acceptance Criteria — Story 1 (AC-1.4); Shadow Path (`/prototype` Step 2.5 render — nil input: an adapter with no `canvas-preview` row, which the test prevents)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_platform_neutral_names.py` (`test_adapter_canvas_row[codex]`, `test_adapter_canvas_row[openclaw]`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Find each row and its section:
   ```bash
   for a in codex openclaw; do
     grep -n '^| `canvas-preview` |' "$REPO/adapters/$a.md"
     awk '/^## /{s2=$0; s3=""} /^### /{s3=$0} /^\| `canvas-preview` \|/{print s2 " > " s3}' "$REPO/adapters/$a.md"
   done
   ```
2. `cd "$REPO" && uv run --python 3.9 pytest -q scripts/tests/test_platform_neutral_names.py -k "adapter_canvas_row and (codex or openclaw)"`

**Expected Result:**
- Codex prints one row:
  `` | `canvas-preview` | `Write` one self-contained HTML file per draft to `.writ/prototypes/<date>-<slug>/` | Inline CSS, no network fetch; give the user each path. Includes a read-only sandbox. No renderer: write a structural description of each draft and say the drafts were not rendered. | ``
  in `## Tool Mapping (Cursor → Codex CLI) > ### Quick reference — orchestration primitives`.
- OpenClaw prints one row:
  `` | `canvas-preview` | `Write({ path: ".writ/prototypes/<date>-<slug>/<draft>.html" })`, one self-contained HTML file per draft | Inline CSS, no network fetch; send the user each path. Includes a run that cannot write files. No renderer: write a structural description of each draft and say the drafts were not rendered. | ``
  in `## Quick Reference > ` (no subsection).
- Step 2 prints `2 passed`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — `adapters/codex.md`, `adapters/openclaw.md`. The OpenClaw row says "HTML file" where the technical spec's row text says "file" (DEV-001), so the spec's own `HTML` keyword test passes.

---

### Scenario 5: `cursor-ide-browser` appears only in the Cursor adapter and record paths

**Source:** Acceptance Criteria — Story 1 (AC-1.5, grep part; the suite part is Scenario 31)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_platform_neutral_names.py` (`test_cursor_ide_browser_confined`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `cd "$REPO" && git grep -l cursor-ide-browser`
2. `uv run --python 3.9 pytest -q scripts/tests/test_platform_neutral_names.py -k cursor_ide_browser_confined`
3. Plant a stray mention in a full copy and run the checks there:
   ```bash
   full_copy "$W/confine"
   printf '\nThe canvas is cursor-ide-browser.\n' >> "$W/confine/commands/prototype.md"
   git -C "$W/confine" add -A
   (cd "$W/confine" && uv run --python 3.9 pytest -q scripts/tests/test_platform_neutral_names.py \
      -k "cursor_ide_browser_confined or prototype_names_capability" 2>&1 \
      | grep -E '^E +(AssertionError|commands/)| failed')
   ```

**Expected Result:**
- Step 1 lists `adapters/cursor.md` plus paths under `.writ/decision-records/`, `.writ/issues/`, `.writ/product/`, `.writ/research/`, and `.writ/specs/` only. No `commands/`, other `adapters/`, `agents/`, `scripts/`, or root file.
- Step 2 prints `1 passed`.
- Step 3 prints `AssertionError: commands/prototype.md still names cursor-ide-browser`, `AssertionError: cursor-ide-browser outside adapters/cursor.md and record paths:`, the line `commands/prototype.md:<line>: The canvas is cursor-ide-browser.`, and `2 failed`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — the test builds the tool name from two parts so the test file is not a hit of its own grep. The record list counts all of `.writ/specs/` (DEV-004, flagged for review).

---

**Story 1 live-session setup.** Scenarios 6–14 run `/prototype` in a temp project with a small UI surface. Paste this after the main setup block:

```bash
# proto <dir> <claude|cursor|codex>: an installed project with a small UI surface.
proto() { inst "$1" "$NEW" "$2" > "$1.install.log" 2>&1 || { echo "install failed: $1.install.log"; return 1; }
  mkdir -p "$1/src/components"
  printf '<!doctype html>\n<html><head><link rel="stylesheet" href="styles.css"></head>\n<body><main id="app"></main></body></html>\n' > "$1/index.html"
  printf ':root { --accent: #2f6fde; --surface: #f6f7f9; --radius: 8px; }\n' > "$1/styles.css"
  printf 'export function Card({ title, children }) { return null; }\nexport function Toggle({ label, on }) { return null; }\n' > "$1/src/components/index.js"
  git -C "$1" init -q -b main && gc "$1" "app"; }
IDEA='a settings page with a profile card and a notifications toggle'
```

An installed project has no `adapters/` folder: `install.sh` does not ship it (see Known Gaps 1). These scenarios check what a user gets. In Notes, record whether the agent said where its renderer choice came from.

### Scenario 6: On Cursor, the drafts render in the browser canvas

**Source:** Experience Design — Story 1 (State: `/prototype` Step 2.5 on Cursor; Journey step 2)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Cursor with its built-in browser tool turned on.
- Story 1 live-session setup pasted.

**Steps:**
1. `proto "$W/proto-cursor" cursor && echo "$W/proto-cursor"`
2. Open the printed folder in Cursor (File → Open Folder).
3. In a new Agent chat, type `/prototype --diverge "a settings page with a profile card and a notifications toggle"` and press Enter. Approve tool calls when Cursor asks.
4. Wait for the agent to present the drafts.

**Expected Result:**
- The agent presents three drafts (A, B, C), each with its axis combination and trade-off.
- Each draft renders in Cursor's browser canvas, and the message says so.
- The message does not say the drafts were unrendered.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — `adapters/cursor.md` `canvas-preview` row; `commands/prototype.md` § Step 2.5.

---

### Scenario 7: On Cursor without the browser tool, the agent says the drafts were not rendered

**Source:** Error Map — Story 1 (Render drafts via `canvas-preview`: no artifact, canvas, or preview tool); Shadow Path (`/prototype` Step 2.5 render — upstream error: renderer unavailable)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `test_adapter_canvas_row[cursor]` checks the clause is in the row; the agent's behavior is manual only

**Preconditions:**
- Scenario 6's project exists (`$W/proto-cursor`).

**Steps:**
1. In Cursor's settings, turn off the built-in browser tool (it is listed with the MCP tools; the label varies by Cursor version).
2. Start a new Agent chat in `$W/proto-cursor`.
3. Type `/prototype --diverge "a settings page with a profile card and a notifications toggle"` and press Enter.
4. Read the message that presents the drafts. Then turn the browser tool back on.

**Expected Result:**
- Each draft arrives as a written structural description: its regions and the components it uses.
- The same message says plainly that the drafts were not rendered.
- The agent does not claim a canvas or a rendered page.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 8: On Claude Code with an artifact or preview tool, the drafts render there

**Source:** Experience Design — Story 1 (State: `/prototype` Step 2.5 on Claude Code, interactive)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- A Claude Code session that has an artifact or preview tool (for example the desktop app with its preview pane).
- Story 1 live-session setup pasted.

**Steps:**
1. `proto "$W/proto-claude" claude && echo "$W/proto-claude"`
2. Open that folder in Claude Code.
3. Type `/prototype --diverge "a settings page with a profile card and a notifications toggle"` and press Enter. Approve tool calls when asked.
4. Wait for the drafts.

**Expected Result:**
- Three drafts, each shown as an artifact or in the preview pane, one self-contained HTML page per draft.
- The message says where each draft rendered.
- The message does not say the drafts were unrendered.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — `adapters/claude-code.md` `canvas-preview` row.

---

### Scenario 9: Headless Claude Code says the drafts were not rendered

**Source:** Error Map — Story 1 (Render drafts via `canvas-preview`: no artifact or preview tool); Experience Design (State: Claude Code, no artifact or preview tool, e.g. headless `claude -p`)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `test_adapter_canvas_row[claude-code]` checks the clause; the agent's behavior is manual only

**Preconditions:**
- Claude Code CLI on `PATH`.
- Scenario 8's project exists (`$W/proto-claude`), or run `proto "$W/proto-claude" claude`.

**Steps:**
1. Run headless with default permissions:
   ```bash
   (cd "$W/proto-claude" && claude -p "/prototype --diverge \"$IDEA\"") > "$W/headless.txt" 2>&1; echo "exit $?"
   ```
2. `cat "$W/headless.txt"`
3. `grep -n -i 'not rendered' "$W/headless.txt"`

**Expected Result:**
- Step 1 prints `exit 0`.
- Step 2 shows a structural description for each draft (regions and components).
- Step 3 finds at least one line saying the drafts were not rendered.
- No line claims an artifact or preview pane.

**Status:** [ ] Pass  [ ] Fail

**Notes:** If the agent writes HTML files instead and names their paths, record that here; it is not a silent skip. Fail only if drafts arrive with no statement about how they were rendered, or with a claim of rendering that did not happen.

---

### Scenario 10: On Codex, the agent writes one HTML file per draft and gives the paths

**Source:** Experience Design — Story 1 (State: `/prototype` Step 2.5 on Codex)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Codex CLI on `PATH`.
- Story 1 live-session setup pasted.

**Steps:**
1. `proto "$W/proto-codex" codex && cd "$W/proto-codex" && codex --sandbox workspace-write`
2. Writ does not register slash commands in Codex. Type: `Follow .codex/commands/prototype.md with --diverge for: a settings page with a profile card and a notifications toggle`
3. When the drafts are presented, in a second shell (setup block pasted, same `$W`): `find "$W/proto-codex/.writ/prototypes" -name '*.html'`
4. `grep -nE '(src|href)="?(https?:)?//' "$W"/proto-codex/.writ/prototypes/*/*.html; echo "remote refs: $?"`

**Expected Result:**
- The reply lists one path per draft under `.writ/prototypes/<date>-<slug>/`.
- Step 3 prints those same paths, one `.html` file per draft.
- Step 4 prints `remote refs: 1` (no stylesheet or script fetched from the network; CSS is inline).
- After you pick a draft or stop, `exploration.md` is in the same folder.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — `adapters/codex.md` `canvas-preview` row. `codex/AGENTS.md.template` tells Codex to map tools via `adapters/codex.md`, which is not in an installed project (Known Gaps 1).

---

### Scenario 11: Codex in a read-only sandbox says the drafts were not rendered and claims no files

**Source:** Error Map — Story 1 (Write HTML drafts: read-only sandbox or the write fails); Experience Design (State: Codex run that cannot write files)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `test_adapter_canvas_row[codex]` checks the row text; the agent's behavior is manual only

**Preconditions:**
- Codex CLI on `PATH`.
- Story 1 live-session setup pasted.

**Steps:**
1. `proto "$W/proto-codex-ro" codex && cd "$W/proto-codex-ro" && codex --sandbox read-only`
2. Type: `Follow .codex/commands/prototype.md with --diverge for: a settings page with a profile card and a notifications toggle`
3. Read the message that presents the drafts. Exit Codex.
4. `ls "$W/proto-codex-ro/.writ/prototypes" 2>&1`

**Expected Result:**
- Each draft arrives as a written structural description.
- The same message says plainly that the drafts were not rendered.
- The reply names no HTML file path as written.
- Step 4 prints `No such file or directory`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 12: On OpenClaw, the agent writes one HTML file per draft and gives the paths

**Source:** Experience Design — Story 1 (State: `/prototype` Step 2.5 on OpenClaw)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- An OpenClaw agent whose workspace you can point at a folder.
- Setup block pasted. OpenClaw has no install path, so the workspace gets the files by copy:
  ```bash
  O="$W/proto-openclaw"; mkdir -p "$O/commands" "$O/adapters" "$O/src/components"
  cp "$REPO/commands/prototype.md" "$O/commands/"; cp "$REPO/adapters/openclaw.md" "$O/adapters/"
  cp "$REPO/system-instructions.md" "$O/"
  printf '<!doctype html>\n<html><head><link rel="stylesheet" href="styles.css"></head>\n<body><main id="app"></main></body></html>\n' > "$O/index.html"
  printf ':root { --accent: #2f6fde; --surface: #f6f7f9; --radius: 8px; }\n' > "$O/styles.css"
  git -C "$O" init -q -b main && gc "$O" "app"; echo "$O"
  ```

**Steps:**
1. Point the OpenClaw agent's workspace at the printed folder.
2. Send: `Read commands/prototype.md and adapters/openclaw.md, then run /prototype --diverge for: a settings page with a profile card and a notifications toggle`
3. When the drafts are presented: `find "$O/.writ/prototypes" -name '*.html'`
4. `grep -nE '(src|href)="?(https?:)?//' "$O"/.writ/prototypes/*/*.html; echo "remote refs: $?"`

**Expected Result:**
- The reply lists one path per draft under `.writ/prototypes/<date>-<slug>/`.
- Step 3 prints those paths.
- Step 4 prints `remote refs: 1`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — `adapters/openclaw.md` `canvas-preview` row. Story 1's notes say the OpenClaw and Codex rows have no runtime evidence behind them.

---

### Scenario 13: OpenClaw without file writes says the drafts were not rendered

**Source:** Error Map — Story 1 (Write HTML drafts: the run cannot write files); Experience Design (State: OpenClaw run that cannot write files)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `test_adapter_canvas_row[openclaw]` checks the row text; the agent's behavior is manual only

**Preconditions:**
- Scenario 12's workspace exists. Remove its drafts: `rm -rf "$O/.writ/prototypes"`
- The OpenClaw agent is configured so it cannot write files (deny `Write` and `exec` in its tool policy).

**Steps:**
1. Send the same message as Scenario 12, step 2.
2. Read the message that presents the drafts.
3. `ls "$O/.writ/prototypes" 2>&1`

**Expected Result:**
- Each draft arrives as a written structural description.
- The same message says plainly that the drafts were not rendered.
- No file path is claimed. Step 3 prints `No such file or directory`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 14: Stopping before the drafts renders nothing

**Source:** Shadow Path — Story 1 (`/prototype` Step 2.5 render — empty input: the user stops before drafts)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- An interactive Claude Code session.
- Story 1 live-session setup pasted.

**Steps:**
1. `proto "$W/proto-stop" claude && echo "$W/proto-stop"`
2. Open that folder in Claude Code and type `/prototype --diverge "a settings page with a profile card and a notifications toggle"`.
3. As soon as the agent states the axes, press Esc and type: `Stop here. Do not draft or render anything.`
4. `find "$W/proto-stop/.writ/prototypes" -type f 2>&1`

**Expected Result:**
- The agent says it stopped before drafting. No draft is shown or rendered.
- Step 4 prints `No such file or directory`, or lists only an `exploration.md` that records the axes and that no draft was chosen. No `.html` file.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 2: Rename `/design` to `/writ-design` Across Every Reference

### Scenario 15: The rename is a git rename that changes only the self-naming lines

**Source:** Acceptance Criteria — Story 2 (AC-2.1)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `scripts/tests/test_platform_neutral_names.py` (`test_writ_design_file`) checks the file and its frontmatter; the commit diff is manual only

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `cd "$REPO" && C=$(git log --follow --diff-filter=R --format=%h -1 -- commands/writ-design.md); git log -1 --format='%h %s' "$C"`
2. `git show -M --format= --stat "$C" | grep 'design.md'`
3. `git show -M --format= "$C" -- commands/design.md commands/writ-design.md | grep -E '^(rename|similarity|[-+])' | grep -v '^+++\|^---'`
4. `git show -s --format=%B "$C" | grep 'BREAKING CHANGE'`
5. `ls commands/design.md; sed -n 2p commands/writ-design.md`
6. `uv run --python 3.9 pytest -q scripts/tests/test_platform_neutral_names.py -k writ_design_file`

**Expected Result:**
- Step 1: `d36a283 feat(design)!: rename /design to /writ-design` (a different SHA if history was rewritten).
- Step 2 includes `commands/{design.md => writ-design.md} | 18 +-`.
- Step 3: `similarity index 95%`, `rename from commands/design.md`, `rename to commands/writ-design.md`, then 9 removed and 9 added lines: `name:`, the H1 `# Design Command (writ-design)`, the five invocation rows (`/writ-design`, `/writ-design 2026-03-01-dashboard`, `--wireframe`, `--screenshot`, `--compare`), "added by `/writ-design` or `/create-spec`", and "Generates specs that `/writ-design` adds visuals to". No mode, flag, exit criterion, or output text changed.
- Step 4: `BREAKING CHANGE: /design is renamed to /writ-design`.
- Step 5: `ls: commands/design.md: No such file or directory`, then `name: writ-design`.
- Step 6: `1 passed`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 2 — `git mv commands/design.md commands/writ-design.md`. `/release` Step 1.2 reads the `BREAKING CHANGE` footer.

---

### Scenario 16: The manifest and `SKILL.md` list `writ-design`, sorted, with no alias

**Source:** Acceptance Criteria — Story 2 (AC-2.2); Error Map (`SKILL.md` drifts from the manifest)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_platform_neutral_names.py` (`test_manifest_entry`, `test_skill_catalog`); eval `manifest`

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `cd "$REPO" && grep -n -A4 '^  - name: writ-design$' .writ/manifest.yaml`
2. `grep -nE '^  - name: design$|aliases:.*design' .writ/manifest.yaml; echo "matches: $?"`
3. `awk '/^commands:/{f=1;next} /^[a-z_]+:/{f=0} f && /^  - name: /{print $3}' .writ/manifest.yaml > "$W/cmds.txt"; tail -2 "$W/cmds.txt"; sort -c "$W/cmds.txt" && echo sorted`
4. ``bash scripts/gen-skill.sh --check 2>/dev/null | head -1; grep -n '`/writ-design`' SKILL.md``
5. `uv run --python 3.9 pytest -q scripts/tests/test_platform_neutral_names.py -k "manifest_entry or skill_catalog"`

**Expected Result:**
- Step 1: `name: writ-design`, `file: commands/writ-design.md`, `category: planning`, `purpose: "Create and compare visual references for Writ specifications."`, `tags: [planning, design, visual]`.
- Step 2: `matches: 1`.
- Step 3: `verify-spec`, `writ-design`, `sorted`.
- Step 4: `pass`, then one row: `` | `/writ-design` | `commands/writ-design.md` | Create and compare visual references for Writ specifications. | ``. It is the last row of the Planning & Specification table, right after `/verify-spec`.
- Step 5: `2 passed`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 17: Every Writ file that named the command now says `/writ-design`

**Source:** Acceptance Criteria — Story 2 (AC-2.3); Error Map (Rename sweep: a reference is missed)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_platform_neutral_names.py` (`test_rename_class_references[*]`, `test_status_allowlists`, `test_cursor_tree`, `test_codex_template_row`, `test_model_tiers_entry_level`, `test_eval_allowlist_rows`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. List the renamed lines:
   ```bash
   cd "$REPO" && grep -n 'writ-design' README.md adapters/cursor.md codex/AGENTS.md.template \
     commands/create-spec.md commands/create-adr.md commands/research.md commands/status.md \
     commands/prototype.md .writ/docs/model-tiers.md scripts/eval.sh | cut -c1-140
   ```
2. Search shipped paths for any Writ-command `/design` or `design.md` left:
   ```bash
   git grep -n -I -E -e '(^|[^[:alnum:]_-])/design([^[:alnum:]_-]|$)' -e '(^|[^[:alnum:]_-])design\.md' -- \
     commands agents adapters scripts claude-code codex cursor SKILL.md README.md system-instructions.md \
     .writ/manifest.yaml .writ/docs ':!.writ/docs/leanness-audit-2026-07-11.md' ':!.writ/docs/swot-2026-03-01.md'
   echo "exit $?"
   ```
3. `uv run --python 3.9 pytest -q scripts/tests/test_platform_neutral_names.py -k "rename_class_references or status_allowlists or cursor_tree or codex_template_row or model_tiers_entry_level or eval_allowlist_rows"`

**Expected Result:**
- Step 1 shows `/writ-design` or `writ-design` in each file: the README Planning & Specification row; the Cursor directory tree's last entry `└── writ-design.md         # /writ-design`; the Codex template row with `.codex/commands/writ-design.md`; create-spec Step 1.5 "wireframe conventions from `/writ-design` command"; the create-adr and research related-commands rows; both status.md command lists (lines near 249 and 442); prototype.md's When to Use row and terminal constraint; the model-tiers `high` row, which ends `writ-design` (15); and the five `scripts/eval.sh` allowlist rows (lines 620–625).
- Step 2 prints nothing, then `exit 1` (no match).
- Step 3 prints `14 passed`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 2 — DEV-003 renamed the bare `design` in the `/status` Maintainer Note list too, which the inventory missed.

---

### Scenario 18: `claude-code/CLAUDE.md` is generated and lists `/writ-design`

**Source:** Acceptance Criteria — Story 2 (AC-2.4); Error Map (Regenerate `claude-code/CLAUDE.md`)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_platform_neutral_names.py` (`test_claude_md_generated`); eval `claude-md`

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `cd "$REPO" && python3 scripts/gen-claude-md.py --check`
2. ``grep -n '`/writ-design`\|`/design`' claude-code/CLAUDE.md``
3. `bash scripts/eval.sh --check=claude-md --report="$W/claude-md.md" >/dev/null 2>&1; echo "exit $?"; grep -E '^- (Findings|Run errors)' "$W/claude-md.md"`
4. `uv run --python 3.9 pytest -q scripts/tests/test_platform_neutral_names.py -k claude_md_generated`

**Expected Result:**
- Step 1: `pass`, then `gen-claude-md: pass (32 commands, 8 agents)`.
- Step 2: one line, `` | `/writ-design` | `.claude/commands/writ-design.md` | Create and compare visual references for Writ specifications. | ``. No `` `/design` `` row.
- Step 3: `exit 0`, `- Findings: 0`, `- Run errors: 0`.
- Step 4: `1 passed`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 2 — before regenerating, `--check` printed `reason: missing writ-design`, `reason: extra design`, `gen-claude-md: fail (1 missing, 1 extra)`. Scenario 21 reproduces that.

---

### Scenario 19: Lines that only look like the old name are unchanged

**Source:** Acceptance Criteria — Story 2 (AC-2.5, keep-class part; the suite part is Scenario 31)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `scripts/tests/test_platform_neutral_names.py` (`test_keep_class_lines_in_swept_files[*]`, `test_keep_class_roadmap_pair`); the commit's file list is manual only

**Preconditions:**
- Scenario 15 run in this shell (`$C` set), or `C=d36a283`.

**Steps:**
1. Check the rename commit touched no keep-class file:
   ```bash
   cd "$REPO" && git show --format= --name-only "$C" | grep -E '^(agents/|codex/agents/|commands/implement-story|CHANGELOG\.md|\.writ/(research|decision-records|product|issues|explanations|specs/archive)/|\.writ/docs/(leanness|swot))'
   echo "keep-class files in commit: $?"
   ```
2. `grep -c '\.writ/docs/design-system\.md' commands/writ-design.md commands/create-spec.md commands/prototype.md commands/implement-story.md agents/visual-qa-agent.md`
3. `grep -c 'roadmap/design' .writ/docs/model-tiers.md; grep -c 'Native artboard/design surface' commands/prototype.md`
4. `uv run --python 3.9 pytest -q scripts/tests/test_platform_neutral_names.py -k keep_class`

**Expected Result:**
- Step 1 prints nothing, then `keep-class files in commit: 1`.
- Step 2: `commands/writ-design.md:2`, `commands/create-spec.md:1`, `commands/prototype.md:1`, `commands/implement-story.md:1`, `agents/visual-qa-agent.md:2`.
- Step 3: `1`, `1`.
- Step 4: `4 passed`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 20: An allowlist row left as `/design` passes eval silently, and the test catches it

**Source:** Error Map — Story 2 (Eval allowlist rows left as `/design`: the stale-row check skips them, no finding)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `test_eval_allowlist_rows` asserts the rows; showing eval's silence is manual only

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Make a full copy and confirm eval is clean there:
   ```bash
   full_copy "$W/allow" && cd "$W/allow"
   bash scripts/eval.sh --check=referenced-paths --report="$W/rp1.md" >/dev/null 2>&1; echo "exit $?"; grep '^- Findings' "$W/rp1.md"
   ```
2. Set one row's creating command back to the old name:
   ```bash
   sed 's#^mockups/README.md|/writ-design|#mockups/README.md|/design|#' scripts/eval.sh > "$W/eval.sh" && cat "$W/eval.sh" > scripts/eval.sh
   grep -n '^mockups/README.md|' scripts/eval.sh
   ```
3. `bash scripts/eval.sh --check=referenced-paths --report="$W/rp2.md" >/dev/null 2>&1; echo "exit $?"; grep '^- Findings' "$W/rp2.md"`
4. `uv run --python 3.9 pytest -q scripts/tests/test_platform_neutral_names.py -k eval_allowlist_rows 2>&1 | grep -E '^E +(AssertionError|mockups/)| failed'; cd "$REPO"`

**Expected Result:**
- Step 1: `exit 0`, `- Findings: 0`.
- Step 2: `624:mockups/README.md|/design|Written by /writ-design under the spec's mockups/ folder; spec-relative.`
- Step 3: `exit 0`, `- Findings: 0`. Eval does not notice, because `commands/design.md` no longer exists and the stale-row pass skips the row.
- Step 4: `AssertionError: allowlist rows still name /design:`, the row from step 2, and `1 failed`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 2 — `scripts/eval.sh` `check_referenced_paths` skips a row unless `commands/<cmd>.md` exists. `test_eval_allowlist_rows` requires every row's creating command to exist.

---

### Scenario 21: A hand edit to either generated catalog fails its `--check`

**Source:** Error Map — Story 2 (`SKILL.md` drifts from the manifest; Regenerate `claude-code/CLAUDE.md`, never hand-edit)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_platform_neutral_names.py` (`test_skill_catalog`, `test_claude_md_generated`); eval `manifest` and `claude-md`

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Put the old row back in the Claude Code template of a full copy:
   ```bash
   full_copy "$W/catalog" && cd "$W/catalog"
   sed 's#^| `/writ-design` | `.claude/commands/writ-design.md` |#| `/design` | `.claude/commands/design.md` |#' claude-code/CLAUDE.md > "$W/c.md" && cat "$W/c.md" > claude-code/CLAUDE.md
   python3 scripts/gen-claude-md.py --check; echo "exit $?"
   ```
2. Do the same to `SKILL.md`:
   ```bash
   sed 's#^| `/writ-design` | `commands/writ-design.md` |#| `/design` | `commands/design.md` |#' SKILL.md > "$W/s.md" && cat "$W/s.md" > SKILL.md
   bash scripts/gen-skill.sh --check 2>/dev/null > "$W/gs.txt"; echo "exit $?"; head -2 "$W/gs.txt"; cd "$REPO"
   ```

**Expected Result:**
- Step 1: `fail`, `reason: missing writ-design`, `reason: extra design`, `gen-claude-md: fail (1 missing, 1 extra)`, `exit 1`.
- Step 2: `exit 1`, `fail`, `reason: SKILL.md drifts from .writ/manifest.yaml; run bash scripts/gen-skill.sh`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 22: On Claude Code, `/writ-design` opens Writ's command and `/design` does not

**Source:** Experience Design — Story 2 (Moment of truth; State: user types `/design` on Claude Code after upgrade)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Claude Code CLI on `PATH`. The collision report concerns Claude Code 2.1.233 or later.
- Setup block pasted. `inst "$W/live-claude" "$NEW" claude > "$W/live-claude.log" 2>&1 && echo ok`

**Steps:**
1. `claude --version` and write the version in Notes.
2. `cd "$W/live-claude" && claude`
3. Type `/writ-design` without pressing Enter and read the command menu. Then press Enter.
4. Read the reply, then press Esc and type `/exit`.
5. Start `claude` again in `$W/live-claude`. Type `/design` without pressing Enter and read the menu. Then press Enter.

**Expected Result:**
- Step 3: the menu shows `writ-design` from the project, described as "Produce wireframes and store screenshots or mockups as visual references the coding agent uses during implementation. …"
- Step 4: Writ's flow starts and asks you to pick a mode: wireframe, attach, capture, compare, or review.
- Step 5: the menu shows no Writ entry named `design`. If this Claude Code version has its own `/design`, Enter runs that command. If it does not, Claude Code reports no such command. In both cases Writ's mode list does not appear.

**Status:** [ ] Pass  [ ] Fail

**Notes:** Record what `/design` did. Nobody has checked the native command in a live session; the spec's evidence for it is secondary reporting (`.writ/research/2026-10-19-prototype-visual-drafts-research.md` F5).

---

### Scenario 23: On Cursor and Codex after the upgrade, `/design` reaches no Writ command

**Source:** Experience Design — Story 2 (State: user types `/design` on Cursor or Codex after upgrade)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `scripts/tests/test_install_update_writ_design.sh` (AC-3.2) checks the files; the Cursor menu is manual only

**Preconditions:**
- Scenario 25 run in this shell (`$W/up-cursor` and `$W/up-codex` exist).
- Cursor installed.

**Steps:**
1. `ls "$W/up-cursor/.cursor/commands" "$W/up-codex/.codex/commands" | grep design`
2. Open `$W/up-cursor` in Cursor. In a new Agent chat, type `/design` without pressing Enter and read the command menu.
3. Clear the input, type `/writ-design`, and press Enter.

**Expected Result:**
- Step 1 prints `writ-design.md` twice and nothing named `design.md`.
- Step 2: the menu has no Writ command named `design`.
- Step 3: Writ's flow starts and asks you to pick a mode.
- Codex has no Writ slash commands; users ask it to follow `.codex/commands/writ-design.md`, which step 1 shows exists.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 3: Upgrade-Path Test, Reference Gate, and Issue Resolutions

### Scenario 24: A fresh install on each platform has `writ-design.md` and no `design.md`

**Source:** Acceptance Criteria — Story 3 (AC-3.1); Error Map (Fresh install: `design.md` still shipped or `writ-design.md` missing); Experience Design (State: fresh install, any of the three install platforms)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_install_update_writ_design.sh` (AC-3.1 block)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Install from `$NEW` on each platform:
   ```bash
   for pf in cursor claude codex; do p="$W/fresh-$pf"; m="$p/.$pf/.writ-manifest"
     inst "$p" "$NEW" $pf > "$p.log" 2>&1; echo "$pf exit $?"
     ls "$p/.$pf/commands" | grep design
     grep -c ' commands/writ-design.md$' "$m"; grep -c ' commands/design.md$' "$m"
   done
   ```
2. Run the committed test (about 70 seconds): `cd "$REPO" && bash scripts/tests/test_install_update_writ_design.sh; echo "exit $?"`

**Expected Result:**
- Step 1, for each of `cursor`, `claude`, `codex`: `exit 0`, `writ-design.md`, `1`, `0`.
- Step 2: `PASS test_install_update_writ_design`, `exit 0`. The test also covers Scenarios 25 and 26.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 25: Updating an old install removes an unmodified `design.md` and installs `writ-design.md`

**Source:** Acceptance Criteria — Story 3 (AC-3.2); Error Map (Update, unmodified `design.md` listed in manifest); Interaction Edge Case (Dry run); Experience Design (State: update, old `design.md` unmodified; Journey step 3)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_install_update_writ_design.sh` (AC-3.2 block)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. For each platform, install from `$OLD`, dry-run the update, then run it:
   ```bash
   for pf in cursor claude codex; do p="$W/up-$pf"; m="$p/.$pf/.writ-manifest"
     inst "$p" "$OLD" $pf > "$p.log" 2>&1; ls "$p/.$pf/commands" | grep design; cp "$m" "$W/m-$pf.before"
     upd "$p" $pf --dry-run > "$W/dry-$pf.txt" 2>&1; echo "$pf dry exit $?"; grep -E 'DRY RUN|🗑' "$W/dry-$pf.txt"
     ls "$p/.$pf/commands" | grep design; cmp -s "$m" "$W/m-$pf.before" && echo "manifest unchanged"
     upd "$p" $pf > "$W/upd-$pf.txt" 2>&1; echo "$pf exit $?"; grep -E 'New:|🗑' "$W/upd-$pf.txt"
     ls "$p/.$pf/commands" | grep design; cmp -s "$p/.$pf/commands/writ-design.md" "$NEW/commands/writ-design.md" && echo "matches source"
     grep -c ' commands/design.md$' "$m"
   done
   ```

**Expected Result:**
- For each platform, in order:
  - `design.md` (the old install)
  - `<platform> dry exit 0`, `🏃 DRY RUN — No changes applied.`, `    🗑  commands/design.md`
  - `design.md` and `manifest unchanged` (the dry run changed nothing)
  - `<platform> exit 0`, `    ✨ New:       commands/writ-design.md`, `  🗑  Removed: commands/design.md`
  - `writ-design.md`, `matches source`, `0`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 3 — `scripts/update.sh` stale detection; no rename map. Scenarios 23, 30, and 36 reuse these projects and logs.

---

### Scenario 26: A locally modified `design.md` is kept byte for byte and warned about on every update

**Source:** Acceptance Criteria — Story 3 (AC-3.3); Error Map (Update, modified `design.md`); Experience Design (State: update, old `design.md` locally modified)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_install_update_writ_design.sh` (AC-3.3 block)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Install from `$OLD` on Claude Code and edit the old command:
   ```bash
   p="$W/mod-claude"; m="$p/.claude/.writ-manifest"; inst "$p" "$OLD" claude > "$p.log" 2>&1
   printf '# local edit\n' >> "$p/.claude/commands/design.md"; H0=$(h "$p/.claude/commands/design.md")
   ```
2. Update twice:
   ```bash
   for run in 1 2; do upd "$p" claude > "$W/mod-$run.txt" 2>&1; echo "run $run exit $?"
     grep -E 'Stale|Removed|Already' "$W/mod-$run.txt"
     [ "$(h "$p/.claude/commands/design.md")" = "$H0" ] && echo "byte-identical"; ls "$p/.claude/commands" | grep design
   done
   ```
3. `[ "$(awk '$2=="commands/design.md"{print $1}' "$m")" = "$(h "$OLD/commands/design.md")" ] && echo "install-time baseline kept"`

**Expected Result:**
- Run 1: `run 1 exit 0`, `  ⚠️  Stale (no longer shipped, locally modified — kept): commands/design.md`, `byte-identical`, `design.md`, `writ-design.md`.
- Run 2: `run 2 exit 0`, the same warning, `✅ Already up to date! (<sha>)`, `byte-identical`, `design.md`, `writ-design.md`.
- No `Removed` line in either run.
- Step 3: `install-time baseline kept`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 3 — relies on `2026-10-20-ci-and-update-integrity`, which keeps and warns about a modified stale file in every category, including on the "Already up to date" path. Scenarios 30 and 39 reuse this project.

---

### Scenario 27: The reference gate is clean on the repo, exact on its fixture, and fails on a git error

**Source:** Acceptance Criteria — Story 3 (AC-3.4); Error Map (Gate run: `git grep` errors); Shadow Path (Reference gate — empty input: no matches is a pass; upstream error: exit 2 or higher fails)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_platform_neutral_names.py` (`test_no_writ_design_reference`, `test_gate_fixture`, `test_gate_git_error`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `cd "$REPO" && uv run --python 3.9 pytest -v scripts/tests/test_platform_neutral_names.py -k "no_writ_design_reference or gate_fixture or gate_git_error" 2>&1 | grep -E 'PASSED|FAILED|passed|failed'`
2. Read `GATE_FIXTURE` in `scripts/tests/test_platform_neutral_names.py` (search for `GATE_FIXTURE = [`).

**Expected Result:**
- Step 1: `test_no_writ_design_reference PASSED`, `test_gate_fixture PASSED`, `test_gate_git_error PASSED`, `3 passed`.
- Step 2: the fixture reports four lines (`commands/a.md` with the slash name, `commands/b.md` with the file name, `commands/f.md` where "native" appears elsewhere on the line, and `.writ/docs/other.md`) and ignores nine: a `design-system.md` path, `/writ-design`, "roadmap/design", a "native `/design`" line, `CHANGELOG.md`, two dated snapshots (one with a space in its path), and two `.writ/specs/` folders.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 3 — `writ_design_refs(root)`. The fixture's fourth reported line moved from a spec folder to `.writ/docs/other.md` (DEV-005), because the record list now covers all of `.writ/specs/` (DEV-004, flagged for review).

---

### Scenario 28: A leftover `/design` in a shipped file fails the gate with `path:line: text`

**Source:** Acceptance Criteria — Story 3 (AC-3.4, real-repo gate); Error Map (Rename sweep: a reference is missed); Experience Design (States: maintainer leaves a Writ `/design` reference; maintainer adds a line about native `/design`)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_platform_neutral_names.py` (`test_no_writ_design_reference`, `test_gate_fixture`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Make a full copy and run the gate:
   ```bash
   full_copy "$W/gate" && cd "$W/gate"
   uv run --python 3.9 pytest -q scripts/tests/test_platform_neutral_names.py -k no_writ_design_reference 2>&1 | tail -1
   ```
2. Plant two Writ references and one native mention:
   ```bash
   printf '\n%s\n' 'See `/design` for mockups.' >> commands/prototype.md
   printf '\n%s\n' 'Open `.claude/commands/design.md`.' >> README.md
   printf '\n%s\n' "Claude Code's native \`/design\` is separate." >> adapters/claude-code.md
   git add -A
   ```
3. `uv run --python 3.9 pytest -q scripts/tests/test_platform_neutral_names.py -k no_writ_design_reference 2>&1 | grep -E '^E +(AssertionError|README|commands/|adapters/)| failed'; cd "$REPO"`

**Expected Result:**
- Step 1: `1 passed, 32 deselected`.
- Step 3: `AssertionError: 2 line(s) still name /design or commands/design.md outside the record list:`, then `README.md:<line>: Open `.claude/commands/design.md`.` and `commands/prototype.md:<line>: See `/design` for mockups.`, then `1 failed`.
- No line for `adapters/claude-code.md`: a line that writes "native `/design`" passes.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 29: Both origin issues end with a Resolution and point at this spec

**Source:** Acceptance Criteria — Story 3 (AC-3.5, issue part)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** `scripts/tests/test_platform_neutral_names.py` (`test_issue_resolution[*]`)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Check each issue's `spec_ref` and last heading:
   ```bash
   cd "$REPO"; for f in .writ/issues/bugs/2026-10-19-prototype-visual-preview-cursor-only.md \
                        .writ/issues/bugs/2026-10-19-design-command-name-collision.md; do
     grep 'spec_ref' "$f"; grep '^## ' "$f" | tail -1
   done
   ```
2. Read both `## Resolution` sections.
3. `uv run --python 3.9 pytest -q scripts/tests/test_platform_neutral_names.py -k issue_resolution`

**Expected Result:**
- Step 1, for each issue: `> **spec_ref:** .writ/specs/2026-10-20-platform-neutral-names/` and `## Resolution`.
- Step 2: the canvas issue names `canvas-preview`, the four adapter rows and their mappings, the fallback clause, the three tests, and what is not done (no eval check for the general case). The collision issue names `/writ-design` with no alias, the two printed update lines, the two test files, and says nobody checked native `/design` shadowing in a live Claude Code session.
- Step 3: `2 passed`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 30: The spec's Upgrade Note quotes the lines `update.sh` prints

**Source:** Acceptance Criteria — Story 3 (AC-3.5, Upgrade Note part)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — `test_install_update_writ_design.sh` asserts the exact printed lines; matching them to the spec text is manual only

**Preconditions:**
- Scenarios 25 and 26 run in this shell (`$W/upd-claude.txt` and `$W/mod-1.txt` exist).

**Steps:**
1. ``sed -n '/^## Upgrade Note/,$p' "$REPO/.writ/specs/2026-10-20-platform-neutral-names/spec.md" | grep -oE '(🗑  Removed|⚠️  Stale)[^`]*'``
2. `grep -hoE '(🗑  Removed|⚠️  Stale)[^`]*commands/design\.md' "$W/upd-claude.txt" "$W/mod-1.txt"`
3. Read spec.md § Upgrade Note.

**Expected Result:**
- Steps 1 and 2 print the same two lines:
  `🗑  Removed: commands/design.md`
  `⚠️  Stale (no longer shipped, locally modified — kept): commands/design.md`
- Step 3: the note says to type `/writ-design` from now on, that modes, flags (`--wireframe`, `--screenshot`, `--compare`), and output are unchanged, that a kept copy keeps answering `/design` in that project until deleted, and that Writ does not rewrite the user's own files.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 31: The full suites pass

**Source:** Acceptance Criteria — Stories 1, 2, 3 (AC-1.5, AC-2.5, AC-3.5: pytest, bash tests, eval with 0 findings)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** partial — CI runs all three on each PR; this is the same run by hand

**Preconditions:**
- A clean checkout of the branch (no merge or cherry-pick in progress). Run outside any sandbox.

**Steps:**
1. `cd "$REPO" && uv run --python 3.9 pytest -q 2>&1 | tail -1`
2. `n=0; f=0; for t in scripts/tests/test_*.sh; do n=$((n+1)); bash "$t" >/dev/null 2>&1 || { f=$((f+1)); echo "FAIL $t"; }; done; echo "$n run, $f failed"`
3. `bash scripts/eval.sh --report="$W/eval.md" >/dev/null 2>&1; echo "exit $?"; grep -E '^- (Findings|Run errors)' "$W/eval.md"`

**Expected Result:**
- Step 1: `<N> passed, 2 skipped` with no `failed`. (Story 3 recorded 2715 passed, 2 skipped; later Phase 13 work changes N.)
- Step 2: no `FAIL` line; `<n> run, 0 failed` (45 run at Story 3).
- Step 3: `exit 0`, `- Findings: 0`, `- Run errors: 0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 32: The upgrade test fails when it is pointed at the old source

**Source:** Error Map — Story 3 (Fresh install: the test fails naming the platform and path)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only (a mutation check of the committed test)

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Copy the tree and make the test install from the old source:
   ```bash
   full_copy "$W/mutant"; T="$W/mutant/scripts/tests/test_install_update_writ_design.sh"
   awk '/^# ----- AC-3.1/{print "SRC_NEW=\"$SRC_OLD\""} {print}' "$T" > "$W/t.sh" && cat "$W/t.sh" > "$T"
   grep -n '^SRC_NEW="\$SRC_OLD"' "$T"
   ```
2. `bash "$T"; echo "exit $?"`

**Expected Result:**
- Step 1 prints one line number with `SRC_NEW="$SRC_OLD"`.
- Step 2: `FAIL: AC-3.1 cursor: .cursor/commands/writ-design.md not installed`, then `exit 1`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 33: A `design.md` the manifest does not track is left alone

**Source:** Error Map — Story 3 (Update, unmodified `design.md` not listed in the project's manifest: out of scope; `update.sh` only removes what its manifest recorded)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Install from `$OLD`, then drop `design.md` from the manifest, as a hand-copied file would be:
   ```bash
   p="$W/hand-claude"; m="$p/.claude/.writ-manifest"; inst "$p" "$OLD" claude > "$p.log" 2>&1
   grep -v ' commands/design.md$' "$m" > "$W/m.tmp" && mv "$W/m.tmp" "$m"; H0=$(h "$p/.claude/commands/design.md")
   ```
2. `upd "$p" claude > "$W/hand.txt" 2>&1; echo "exit $?"; grep 'design' "$W/hand.txt"`
3. `[ "$(h "$p/.claude/commands/design.md")" = "$H0" ] && echo "untouched"; ls "$p/.claude/commands" | grep design`

**Expected Result:**
- Step 2: `exit 0`, and only `    ✨ New:       commands/writ-design.md`. No `Removed` or `Stale` line.
- Step 3: `untouched`, `design.md`, `writ-design.md`.

**Status:** [ ] Pass  [ ] Fail

**Notes:** The Upgrade Note does not mention this case (Known Gaps 2).

---

### Scenario 34: An install with no commands folder is refused by update and fixed by install

**Source:** Shadow Path — Story 3 (Upgrade an old install — empty input: project with no commands dir)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `p="$W/nocmd-claude"; inst "$p" "$OLD" claude > "$p.log" 2>&1; rm -rf "$p/.claude/commands"`
2. `upd "$p" claude; echo "exit $?"`
3. `inst "$p" "$NEW" claude > "$p.log2" 2>&1; echo "install exit $?"; ls "$p/.claude/commands" | grep design; grep -c ' commands/design.md$' "$p/.claude/.writ-manifest"`

**Expected Result:**
- Step 2: `❌ Writ doesn't appear to be installed for Claude Code in this project.`, `   Run install.sh --platform claude first.`, `exit 1`.
- Step 3: `install exit 0`, `writ-design.md`, `0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:** The technical spec's Shadow Paths row says the update installs `writ-design.md` here. What was built: `update.sh` refuses and `install.sh` does it. This plan expects the observed behavior.

---

### Scenario 35: A failed clone changes nothing

**Source:** Shadow Path — Story 3 (Upgrade an old install — upstream error: `WRIT_REPO` clone fails)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `p="$W/clone-claude"; inst "$p" "$OLD" claude > "$p.log" 2>&1; cp "$p/.claude/.writ-manifest" "$W/clone.before"`
2. `(cd "$p" && WRIT_REPO="$W/no-such-repo" bash "$NEW/scripts/update.sh" --platform claude --no-commit); echo "exit $?"`
3. `ls "$p/.claude/commands" | grep design; cmp -s "$W/clone.before" "$p/.claude/.writ-manifest" && echo "manifest unchanged"`

**Expected Result:**
- Step 2: `❌ Failed to clone <W>/no-such-repo`, `   Check your network connection and try again.`, `exit 1`.
- Step 3: `design.md`, `manifest unchanged`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 36: A second update after the removal says nothing about `design.md`

**Source:** Interaction Edge Case — Story 3 (Update run twice)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only (the bash test runs a second update only in the modified case)

**Preconditions:**
- Scenario 25 run in this shell (`$W/up-claude` exists).

**Steps:**
1. `upd "$W/up-claude" claude > "$W/again.txt" 2>&1; echo "exit $?"; grep -c 'design' "$W/again.txt"; grep 'Already' "$W/again.txt"`

**Expected Result:**
- `exit 0`, `0`, `✅ Already up to date! (<sha>)`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 37: `--force` still keeps a modified `design.md`

**Source:** Interaction Edge Case — Story 3 (`update.sh --force`)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Setup block pasted.

**Steps:**
1. `p="$W/force-claude"; inst "$p" "$OLD" claude > "$p.log" 2>&1; printf '# local edit\n' >> "$p/.claude/commands/design.md"; H0=$(h "$p/.claude/commands/design.md")`
2. `upd "$p" claude --force > "$W/force.txt" 2>&1; echo "exit $?"; grep -E 'Stale|Removed|New:' "$W/force.txt"`
3. `[ "$(h "$p/.claude/commands/design.md")" = "$H0" ] && echo "byte-identical"; ls "$p/.claude/commands" | grep design`

**Expected Result:**
- Step 2: `exit 0`, `    ✨ New:       commands/writ-design.md`, `  ⚠️  Stale (no longer shipped, locally modified — kept): commands/design.md`. No `Removed` line.
- Step 3: `byte-identical`, `design.md`, `writ-design.md`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 38: The user's own files that say `/design` are not rewritten

**Source:** Interaction Edge Case — Story 3 (User's own files say `/design`)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Install from `$OLD` and add a custom command and a note that use the old name:
   ```bash
   p="$W/own-claude"; inst "$p" "$OLD" claude > "$p.log" 2>&1
   printf -- '---\nname: my-flow\n---\n%s\n' 'Run `/design` first, then open commands/design.md.' > "$p/.claude/commands/my-flow.md"
   mkdir -p "$p/.writ/notes"; echo 'Use /design for mockups.' > "$p/.writ/notes/team.md"
   A=$(h "$p/.claude/commands/my-flow.md"); B=$(h "$p/.writ/notes/team.md")
   ```
2. `upd "$p" claude > "$W/own.txt" 2>&1; echo "exit $?"; grep -E 'my-flow|team\.md|Removed' "$W/own.txt"`
3. `[ "$(h "$p/.claude/commands/my-flow.md")" = "$A" ] && [ "$(h "$p/.writ/notes/team.md")" = "$B" ] && echo "user files unchanged"`

**Expected Result:**
- Step 2: `exit 0` and only `  🗑  Removed: commands/design.md`.
- Step 3: `user files unchanged`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 39: On Claude Code, a kept `design.md` answers `/design` until it is deleted

**Source:** Interaction Edge Case — Story 3 (User kept a modified `design.md` on Claude Code)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Scenario 26 run in this shell (`$W/mod-claude` exists).
- Claude Code CLI on `PATH`.

**Steps:**
1. `cd "$W/mod-claude" && claude`
2. Type `/design` without pressing Enter and read the menu. Press Enter and read the reply. Press Esc, then `/exit`.
3. `rm "$W/mod-claude/.claude/commands/design.md"`, start `claude` in `$W/mod-claude` again, and type `/design`.
4. Exit, then `upd "$W/mod-claude" claude 2>&1 | grep -c Stale`

**Expected Result:**
- Step 2: the menu shows the project's `design` command, and Enter opens Writ's old mode list (wireframe, attach, capture, compare, review).
- Step 3: Writ's mode list no longer appears for `/design`.
- Step 4: `0`. With the file gone, no stale warning prints.

**Status:** [ ] Pass  [ ] Fail

**Notes:** Step 2 is the Upgrade Note's claim ("including on Claude Code"). Nobody has verified whether a project command wins over a native `/design`. Record which one ran and the Claude Code version.

---

### Scenario 40: Upgrading a real `v0.42.0` install removes `design.md` and updates the catalogs

**Source:** Experience Design — Story 3 (Journey step 3, happy path upgrade; State: update, old `design.md` unmodified)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only (the bash test's old source differs from the new one only in the command file)

**Preconditions:**
- Setup block pasted. The Writ repo has the `v0.42.0` tag.

**Steps:**
1. Clone the repo twice: one clone for the new upstream with full history, one checked out at the last release:
   ```bash
   H="$W/hist"; git clone -q "$REPO" "$H"; git -C "$H" ls-files commands/writ-design.md
   RO="$W/rel-src"; git clone -q "$REPO" "$RO" && git -C "$RO" -c advice.detachedHead=false checkout -q v0.42.0
   git -C "$RO" ls-files commands/design.md
   ```
2. Install from the release and update from the clone on each platform:
   ```bash
   for pf in claude cursor codex; do p="$W/rel-$pf"; inst "$p" "$RO" $pf > "$p.log" 2>&1
     UPSTREAM="$H" upd "$p" $pf > "$W/rel-$pf.txt" 2>&1; echo "$pf exit $?"
     grep -E 'design\.md|Writ block' "$W/rel-$pf.txt"; ls "$p/.$pf/commands" | grep design
   done
   ```
3. ``grep -n '`/writ-design`\|`/design`' "$W/rel-claude/CLAUDE.md" "$W/rel-codex/AGENTS.md"``

**Expected Result:**
- Step 1: `commands/writ-design.md`, then `commands/design.md`. (If the clone's checked-out branch predates the rename, the first line is empty; clone with `-b phase/13-subtract-and-repair` or `-b main` after the merge.)
- Step 2, for each platform: `exit 0`, `    ✨ New:       commands/writ-design.md`, `  🗑  Removed: commands/design.md`, then `writ-design.md` only. Claude Code also prints `    🔄 Updated: CLAUDE.md (Writ block)`, and Codex `    🔄 Updated: AGENTS.md (Writ block)`. Other `Removed` lines for files this branch retired may also appear.
- Step 3: one `/writ-design` row in each file and no `/design` row. (The `v0.42.0` block listed `` `/design` `` → `.claude/commands/design.md`.)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 41: When the installed version is not in upstream history, `design.md` stays without a message

**Source:** Experience Design — Story 3 (State: update, old `design.md` unmodified, under the legacy-manifest fallback from `2026-10-20-ci-and-update-integrity`)
**Feature:** none
**Verification:** human — no recipe
**Automated Test:** none — manual only

**Preconditions:**
- Setup block pasted.

**Steps:**
1. Build a `v0.42.0` source that shares no history with `$NEW`, then install from it:
   ```bash
   RA="$W/rel-nohist"; mkdir -p "$RA"; git -C "$REPO" archive v0.42.0 | tar -x -C "$RA"
   git -C "$RA" init -q -b main && gc "$RA" "v0.42.0, no shared history"
   p="$W/nohist-claude"; inst "$p" "$RA" claude > "$p.log" 2>&1
   ```
2. `upd "$p" claude > "$W/nohist-1.txt" 2>&1; echo "exit $?"; grep -E 'predates|design\.md' "$W/nohist-1.txt"`
3. `ls "$p/.claude/commands" | grep design; grep -c ' commands/design.md$' "$p/.claude/.writ-manifest"`
4. `upd "$p" claude 2>&1 | grep -E 'design|Already'`

**Expected Result (current behavior, observed 2026-10-21):**
- Step 2: `exit 0`, `  ⚠️  Manifest predates shipped-only baselines and version <sha> was not found upstream; files that differ from upstream are preserved this run.`, `    ✨ New:       commands/writ-design.md`. No `Removed` or `Stale` line for `design.md`.
- Step 3: `design.md`, `writ-design.md`, `0` (the manifest no longer tracks the old file).
- Step 4: only `✅ Already up to date! (<sha>)`.

**Status:** [ ] Pass  [ ] Fail

**Notes:** Pass means the behavior matches the above. It is a gap against the Upgrade Note, which promises a `Removed` line or a `Stale` warning: the old file stays on disk with no message, and on Claude Code `/design` keeps opening it (Known Gaps 2). Decide whether to accept it or file an issue.

---

## Automated vs. Manual

| Kind | Scenarios | Count |
|---|---|---|
| Asserted by a committed test (CI runs it) | 1, 2, 3, 4, 5, 16, 17, 18, 21, 24, 25, 26, 27, 28, 29 | 15 |
| Partly automated (the test passes in CI; a commit diff, eval's silence, spec text, or the suite run is checked by hand) | 15, 19, 20, 30, 31 | 5 |
| Scripted shell check, no committed test | 32, 33, 34, 35, 36, 37, 38, 40, 41 | 9 |
| Needs a person in a live Cursor, Claude Code, Codex, or OpenClaw session | 6, 7, 8, 9, 10, 11, 12, 13, 14, 22, 23, 39 | 12 |

Scenarios 7, 9, 11, and 13 are the `canvas-preview` degradation line on each platform. Scenarios 22 and 39 are the only checks of what `/design` does in a live Claude Code session.

## Known Gaps

1. **The `canvas-preview` mapping does not reach installed projects.** `install.sh` and `update.sh` never copy `adapters/`. An installed project has `commands/prototype.md`, which says "the adapter maps it", but no adapter file. `codex/AGENTS.md.template` tells Codex to "map tools via `adapters/codex.md`", which is also absent. The agent in a user project has to choose a renderer on its own. Scenarios 6–13 check what users actually get. Observed in temp installs on 2026-10-21: `grep -rl canvas-preview` in an installed project finds only `commands/prototype.md`.
2. **Two upgrade paths leave an unmodified `design.md` with no message.** (a) The manifest does not track it (Scenario 33). (b) The install predates shipped-only baselines and its version is unknown or not in upstream history (Scenario 41); the fallback from `2026-10-20-ci-and-update-integrity` keeps it on purpose. In both cases `/design` keeps opening Writ's old command on Claude Code, and the Upgrade Note says nothing about it. The technical spec's error map says the Upgrade Note tells users to delete an untracked file; it does not.
3. **The bash test's old source is synthetic.** `SRC_OLD` differs from the new tree only in the command file, so the test does not exercise an old `CLAUDE.md` or `AGENTS.md` block that lists `/design`, or a legacy manifest. Scenario 40 covers the real `v0.42.0` path by hand.
4. **Native `/design` precedence is unverified.** Scenarios 22 and 39 are the first live checks.
5. **DEV-004 is flagged for review.** The gate's record list exempts all of `.writ/specs/`, not the named folders the contract listed.

## Not Covered by This Plan

- **`/update-writ`.** It states the same stale rules, but it pulls from the GitHub upstream, which will not have the rename until the release ships. Run it after the release.
- **OpenClaw install and update.** OpenClaw has no install path (`adapters/openclaw.md` § Skills → Install Path).
- **Phase 14's general adapter coverage check** and `/design` Mode A modernization are out of scope in the spec.

## Pending Stories

None. All three stories are Completed ✅.
